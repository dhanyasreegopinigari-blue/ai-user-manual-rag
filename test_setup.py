"""Quick end-to-end check:  python test_setup.py
Uses a temporary database/data folder, so your real library is not touched."""
import os
import shutil
import sys
import tempfile
import traceback

import config

TMP = tempfile.mkdtemp(prefix="aum_test_")
config.DB_PATH = os.path.join(TMP, "test.db")
config.DATA_DIR = TMP
config.MANUALS_DIR = os.path.join(TMP, "manuals")
config.IMAGES_DIR = os.path.join(TMP, "images")
config.FAISS_DIR = os.path.join(TMP, "faiss")

import database as db          # noqa: E402
import manual                  # noqa: E402
import rag                     # noqa: E402
import vision                  # noqa: E402

try:
    import pymupdf as fitz
except ImportError:
    import fitz

MANUAL_TEXT = (
    "ABC Industrial Pump P-3000 - User Manual. SAFETY: Always switch off the pump and disconnect power "
    "before servicing. REPLACING THE FILTER: 1. Switch off the pump and unplug the power cable. "
    "2. Remove the four screws of the front cover and lift the cover off. 3. Pull out the old filter "
    "cartridge. 4. Insert the new filter cartridge with the arrow pointing up. 5. Refit the front cover "
    "and tighten the screws. 6. Reconnect power and switch the pump on. STARTING THE PUMP: Press the green "
    "START button. ERROR E03 means the filter is clogged; replace the filter. ") * 3

results, state = [], {}


def check(name, fn):
    try:
        info = fn()
        print(f"[PASS] {name}" + (f" - {info}" if info else ""))
        results.append(True)
    except Exception as e:
        print(f"[FAIL] {name}: {getattr(e, 'args', [e])[0]}")
        if not isinstance(e, config.AppError):
            traceback.print_exc()
        results.append(False)


def t_db():
    db.init_db()
    assert db.list_manuals() == []


def t_ollama():
    ok, msg = rag.test_connection()
    if not ok:
        raise config.AppError(msg)


def t_embed():
    v = rag.embed(["hello world"])
    return f"vector size {v.shape[1]}"


def t_pdf():
    pdf = os.path.join(TMP, "test_manual.pdf")
    doc = fitz.open()
    for _ in range(2):
        page = doc.new_page()
        page.insert_textbox(fitz.Rect(40, 40, 550, 800), MANUAL_TEXT, fontsize=9)
    doc.save(pdf)
    doc.close()
    state["mid"] = manual.import_pdf(pdf, "ABC P-3000 User Manual", "ABC", "P-3000")
    m = db.list_manuals()[0]
    assert m["page_count"] == 2 and os.path.isfile(rag.index_path(state["mid"]))
    return f"{len(db.get_all_chunks(state['mid']))} chunks, index created"


def t_retrieve():
    chunks = rag.search(state["mid"], "How do I replace the filter?")
    assert chunks, "no chunks returned"
    return f"top chunk page {chunks[0]['page_number']}"


def t_match():
    assert db.find_manuals_by_hardware({"model": "p 3000"}), "model match failed"


def t_vision():
    from PIL import Image, ImageDraw
    path = os.path.join(TMP, "label.png")
    img = Image.new("RGB", (800, 400), "white")
    ImageDraw.Draw(img).text((40, 150), "ABC Corporation  Industrial Pump  Model P-3000", fill="black")
    img.save(path)
    hw = vision.identify_image(path)
    return str({k: v for k, v in hw.items() if v and k != "visible_labels"})


def t_answer():
    ans = rag.answer_question(state["mid"], "How do I replace the filter?")
    assert ans["found"] and ans["steps"], "no steps returned"
    return f"{len(ans['steps'])} steps, first: {ans['steps'][0]['text'][:60]}"


check("1. SQLite database can be created", t_db)
check("2. Ollama connection / models installed", t_ollama)
if results[-1]:
    check("3. Embedding model works", t_embed)
    check("4+5. PDF processed, FAISS index created", t_pdf)
    if results[-1]:
        check("6. Manual chunks can be retrieved", t_retrieve)
        check("   Hardware -> manual matching", t_match)
        check("8. LLM answers from retrieved context", t_answer)
    check("7. Vision model can analyze an image", t_vision)
else:
    print("Skipping the remaining checks because Ollama is not ready.")

shutil.rmtree(TMP, ignore_errors=True)
print(f"\n{sum(results)}/{len(results)} checks passed")
sys.exit(0 if all(results) else 1)
