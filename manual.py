"""PDF import (text + images + chunks + index), manual deletion, and hardware -> manual matching."""
import os
import re
import shutil
import time

try:
    import pymupdf as fitz          # newer PyMuPDF name
except ImportError:                 # older versions
    import fitz

import config
import database as db
import rag
import vision
from config import AppError

MIN_IMAGE_SIDE = 100   # ignore icons / tiny decorations
MAX_IMAGES_PER_PAGE = 6


# =============================================================================
# Import
# =============================================================================
def import_pdf(pdf_path, name, manufacturer="", model="", progress=None):
    """Import a PDF manual. Returns the new manual id. Raises AppError with a friendly message."""
    cb = progress or (lambda m: None)
    cb("Importing manual...")
    if not os.path.isfile(pdf_path):
        raise AppError("The selected PDF file was not found.")
    config.ensure_dirs()
    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        raise AppError(f"Could not open this PDF:\n{e}")
    if doc.needs_pass:
        doc.close()
        raise AppError("This PDF is password protected. Please remove the password first.")
    if doc.page_count == 0:
        doc.close()
        raise AppError("This PDF has no pages.")

    dest = os.path.join(config.MANUALS_DIR, f"{int(time.time())}_{os.path.basename(pdf_path)}")
    shutil.copy2(pdf_path, dest)
    manual_id = db.add_manual(name.strip() or os.path.splitext(os.path.basename(pdf_path))[0],
                              manufacturer.strip(), model.strip(), dest)
    try:
        _process(doc, manual_id, cb)
    except AppError:
        delete_manual(manual_id)
        raise
    except Exception as e:
        delete_manual(manual_id)
        raise AppError(f"Importing the manual failed:\n{e}")
    finally:
        doc.close()
    cb("Done.")
    return manual_id


def _process(doc, manual_id, cb):
    n = doc.page_count
    # Images used on many pages are usually logos/headers -> skip them.
    counts = {}
    for page in doc:
        for img in page.get_images(full=True):
            counts[img[0]] = counts.get(img[0], 0) + 1
    repeated = {x for x, c in counts.items() if c >= max(3, 0.15 * n)}

    page_rows, image_rows, page_texts, first_image = [], [], [], {}
    for i, page in enumerate(doc):
        pno = i + 1
        cb(f"Extracting pages and images... {pno}/{n}")
        text = page.get_text("text").strip()
        render = os.path.join(config.IMAGES_DIR, f"manual_{manual_id}_page_{pno}_render.jpg")
        try:  # snapshot of the whole page, used when a page has no embedded illustration
            page.get_pixmap(matrix=fitz.Matrix(1.3, 1.3)).save(render)
        except Exception:
            render = None
        page_rows.append((pno, text, render))
        page_texts.append((pno, text))
        for path in _extract_images(doc, page, manual_id, pno, repeated):
            image_rows.append((pno, path))
            first_image.setdefault(pno, path)

    db.add_pages(manual_id, page_rows)
    db.add_images(manual_id, image_rows)

    cb("Creating chunks...")
    chunks = make_chunks(page_texts)
    if not chunks:
        raise AppError("No readable text was found in this PDF.\n"
                       "Scanned (image-only) PDFs are not supported in this prototype.")
    for ch in chunks:
        ch["image_path"] = next((first_image[p] for p in ch["pages"] if p in first_image), None)
    chunk_ids = db.add_chunks(manual_id, chunks)

    rag.build_index(manual_id, chunk_ids, [c["text"] for c in chunks], cb)


def _extract_images(doc, page, manual_id, pno, repeated):
    saved, seen = [], set()
    for img in page.get_images(full=True):
        xref = img[0]
        if xref in repeated or xref in seen or len(saved) >= MAX_IMAGES_PER_PAGE:
            continue
        seen.add(xref)
        try:
            pix = fitz.Pixmap(doc, xref)
            if pix.colorspace is None or pix.width < MIN_IMAGE_SIDE or pix.height < MIN_IMAGE_SIDE:
                continue
            ratio = pix.width / pix.height
            if ratio > 8 or ratio < 1 / 8:      # lines / separators
                continue
            if pix.colorspace.n > 3:            # CMYK -> RGB
                pix = fitz.Pixmap(fitz.csRGB, pix)
            path = os.path.join(config.IMAGES_DIR, f"manual_{manual_id}_page_{pno}_img_{len(saved) + 1}.png")
            pix.save(path)
            saved.append(path)
        except Exception:
            continue  # one broken image must not break the import
    return saved


# =============================================================================
# Chunking
# =============================================================================
def make_chunks(page_texts):
    """Group page text into chunks of ~CHUNK_MIN..CHUNK_MAX words with overlap.
    Every page's text is prefixed with a [Page N] marker so answers can cite pages."""
    segments = []   # (page, text); very long pages are split along paragraph/sentence boundaries
    for pno, text in page_texts:
        words = text.split()
        if not words:
            continue
        if len(words) <= config.CHUNK_MAX_WORDS:
            segments.append((pno, text))
        else:
            paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
            part_words = []
            for para in paragraphs:
                pw = para.split()
                if len(part_words) + len(pw) > config.CHUNK_MAX_WORDS and part_words:
                    segments.append((pno, " ".join(part_words)))
                    part_words = []
                if len(pw) > config.CHUNK_MAX_WORDS:
                    for i in range(0, len(pw), config.CHUNK_MAX_WORDS):
                        slice_w = pw[i:i + config.CHUNK_MAX_WORDS]
                        if slice_w:
                            segments.append((pno, " ".join(slice_w)))
                else:
                    part_words.extend(pw)
            if part_words:
                segments.append((pno, " ".join(part_words)))

    chunks, cur, count = [], [], 0
    has_new = False
    overlap_words = getattr(config, "CHUNK_OVERLAP_WORDS", 60)

    def flush():
        nonlocal cur, count, has_new
        if cur and has_new:
            body = "\n".join(f"[Page {p}]\n{t}" for p, t in cur)
            first_line = next((ln.strip() for ln in cur[0][1].splitlines() if ln.strip()), "")
            chunks.append({"page_number": cur[0][0], "pages": sorted({p for p, _ in cur}),
                           "text": body, "section": first_line[:80]})
            overlap_cur = []
            overlap_count = 0
            if overlap_words > 0:
                for pno, txt in reversed(cur):
                    w_list = txt.split()
                    if overlap_count + len(w_list) <= overlap_words:
                        overlap_cur.insert(0, (pno, txt))
                        overlap_count += len(w_list)
                    else:
                        needed = overlap_words - overlap_count
                        if needed > 10:
                            overlap_cur.insert(0, (pno, " ".join(w_list[-needed:])))
                            overlap_count += needed
                        break
            cur = overlap_cur
            count = overlap_count
            has_new = False

    for pno, text in segments:
        w = len(text.split())
        if cur and count + w > config.CHUNK_MAX_WORDS:
            flush()
        cur.append((pno, text))
        count += w
        has_new = True
        if count >= config.CHUNK_MIN_WORDS:
            flush()
    flush()
    return chunks


# =============================================================================
# Delete
# =============================================================================
def delete_manual(manual_id):
    """Remove DB rows, extracted images, the PDF copy and the FAISS index."""
    for path in db.delete_manual_rows(manual_id):
        try:
            os.remove(path)
        except OSError:
            pass
    rag.delete_index(manual_id)


# =============================================================================
# Hardware analysis + manual matching
# =============================================================================
def match_manual(hw):

    # First try exact database matching
    exact = db.find_manuals_by_hardware(hw)

    similar = []

    if not exact:
        parts = [
            hw.get("manufacturer", ""),
            hw.get("product_name", ""),
            hw.get("model", ""),
            hw.get("part_number", ""),
            hw.get("hardware_type", ""),
            hw.get("category", ""),
            hw.get("visual_description", ""),
            hw.get("likely_use", ""),
            " ".join(hw.get("visible_text", [])),
            " ".join(hw.get("visible_components", [])),
        ]

        text = " ".join(
            str(x).strip()
            for x in parts
            if str(x).strip()
        )

        if text:
            try:
                similar = [
                    m for m, score in rag.search_all_manuals(text)
                ]
            except AppError:
                similar = []

    return exact, similar

# Cache vision/manual analysis by image path.
# This prevents running the expensive vision model repeatedly
# for the same image during the current application session.
_photo_analysis_cache = {}


def analyze_photo(path, progress=None):
    cb = progress or (lambda m: None)

    # Reuse previous result for the same image.
    if path in _photo_analysis_cache:
        cb("Using cached hardware analysis...")
        print(f"[CACHE] Reusing photo analysis: {path}")
        return _photo_analysis_cache[path]

    start = time.time()

    cb("Preparing hardware image...")
    hw = vision.identify_image(path, cb)

    vision_time = time.time() - start
    print(f"[TIMING] Vision identification: {vision_time:.2f} seconds")

    cb("Finding matching manuals...")

    match_start = time.time()
    exact, similar = match_manual(hw)

    match_time = time.time() - match_start
    print(f"[TIMING] Manual matching: {match_time:.2f} seconds")

    print(f"[TIMING] Total photo analysis: {time.time() - start:.2f} seconds")

    cb("Preparing hardware result...")

    result = {
        "hardware": hw,
        "preview": path,
        "exact": exact,
        "similar": similar
    }

    # Save the complete result for reuse.
    _photo_analysis_cache[path] = result

    print(f"[CACHE] Saved photo analysis: {path}")

    return result

def analyze_video(path, progress=None):
    cb = progress or (lambda m: None)
    hw, preview = vision.identify_video(path, cb)
    exact, similar = match_manual(hw)
    return {"hardware": hw, "preview": preview, "exact": exact, "similar": similar}
