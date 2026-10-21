"""Hardware identification from a photo or a video using the Ollama vision model."""
import base64
import io
import os
from collections import Counter

import cv2
import numpy as np
from PIL import Image

import config
from config import AppError
from services.rag import chat, parse_json

FIELDS = (
    "manufacturer",
    "product_name",
    "model",
    "part_number",
    "hardware_type",
    "category",
    "visual_description",
    "visible_components",
    "visible_text",
    "likely_use",
    "confidence",
)

EMPTY_WORDS = {
    "",
    "unknown",
    "n/a",
    "na",
    "none",
    "null",
    "not visible",
    "unidentified",
    "-"
}

PROMPT = """
Analyze only the hardware board in the image.

Return ONLY one valid JSON object.
Do not write markdown or explanations.

RULES:
- Never guess a brand, manufacturer, product name, model, or part number.
- Only report an exact identity if it is clearly printed and readable.
- Do not identify a board from appearance alone.
- If exact identity is uncertain, use "".
- hardware_type must be generic, for example "single-board computer" or "development board".
- category must be generic.
- visible_text must contain only clearly readable text.
- Do not invent text.
- Do not repeat text.
- Maximum 4 visible_text items.
- Maximum 5 visible_components.
- visual_description: maximum 1 short sentence.
- likely_use: maximum 1 short sentence.
- confidence: Low, Medium, or High.

Return exactly:

{
  "manufacturer": "",
  "product_name": "",
  "model": "",
  "part_number": "",
  "hardware_type": "",
  "category": "",
  "visual_description": "",
  "visible_components": [],
  "visible_text": [],
  "likely_use": "",
  "confidence": "Low"
}
"""

def _clean(v):
    v = str(v or "").strip()
    return "" if v.lower() in EMPTY_WORDS else v


def _normalize(data):
    data = data or {}

    out = {}

    # Basic identification fields
    for key in (
        "manufacturer",
        "product_name",
        "model",
        "part_number",
        "hardware_type",
        "category",
        "visual_description",
        "likely_use",
        "confidence",
    ):
        out[key] = _clean(data.get(key))

    # Lists
    components = data.get("visible_components")
    out["visible_components"] = (
        [str(x).strip() for x in components if str(x).strip()][:15]
        if isinstance(components, list)
        else []
    )

    visible_text = data.get("visible_text")

    # Keep compatibility with the old "visible_labels" name
    if not isinstance(visible_text, list):
        visible_text = data.get("visible_labels")

    out["visible_text"] = (
        [str(x).strip() for x in visible_text if str(x).strip()][:10]
        if isinstance(visible_text, list)
        else []
    )

    # Keep old field name too, so existing video/UI code doesn't immediately break
    out["visible_labels"] = out["visible_text"]

    return out


def _to_b64_jpeg(img, max_side=None):
    max_side = max_side or getattr(config, "VISION_MAX_SIDE", 1024)
    img = img.convert("RGB")
    img.thumbnail((max_side, max_side))
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=90)
    return base64.b64encode(buf.getvalue()).decode()

def _identify_b64(b64, progress=None):
    cb = progress or (lambda m: None)

    cb("Running hardware vision model...")

    raw = chat(
        config.VISION_MODEL,
        PROMPT,
        images=[b64],
        json_mode=True,
        temperature=0.0,
        num_ctx=4096,
        num_predict=350
    )

    print("\n========== RAW VISION RESPONSE ==========")
    print(repr(raw))
    print("=========================================\n")

    cb("Processing hardware identification...")

    if not raw or not raw.strip():
        print("[VISION] Model returned an empty response.")

        return {
            "manufacturer": "",
            "product_name": "",
            "model": "",
            "part_number": "",
            "hardware_type": "",
            "category": "",
            "visual_description": "",
            "visible_components": [],
            "visible_text": [],
            "likely_use": "",
            "confidence": "Low",
            "visible_labels": [],
        }

    parsed = parse_json(raw)

    if parsed is None:
        print("[VISION] Could not parse model response as JSON.")
        print("[VISION] Raw response was:")
        print(raw)

        return {
            "manufacturer": "",
            "product_name": "",
            "model": "",
            "part_number": "",
            "hardware_type": "",
            "category": "",
            "visual_description": "",
            "visible_components": [],
            "visible_text": [],
            "likely_use": "",
            "confidence": "Low",
            "visible_labels": [],
        }

    result = _normalize(parsed)

    # Clean duplicated / invalid visible text
    texts = result.get("visible_text", [])

    clean_texts = []
    seen = set()

    for item in texts:
        item = str(item).strip()

        if not item:
            continue

        if item.lower() in {
            "unknown",
            "n/a",
            "none",
        }:
            continue

        key = item.lower()

        if key in seen:
            continue

        seen.add(key)
        clean_texts.append(item)

    result["visible_text"] = clean_texts[:5]
    result["visible_labels"] = clean_texts[:5]

    # Clean duplicated components
    components = result.get("visible_components", [])

    clean_components = []
    seen_components = set()

    for item in components:
        item = str(item).strip()

        if not item:
            continue

        key = item.lower()

        if key in seen_components:
            continue

        seen_components.add(key)
        clean_components.append(item)

    result["visible_components"] = clean_components[:8]

    print("\n========== VISION RESULT ==========")
    print(result)
    print("===================================\n")

    return result

def identify_image(path, progress=None):
    cb = progress or (lambda m: None)

    cb("Preparing hardware image...")

    try:
        with Image.open(path) as img:
            img.load()
            b64 = _to_b64_jpeg(img)
    except Exception:
        raise AppError(
            "This file is not a valid image.\n"
            "Please choose a PNG, JPG or similar photo."
        )

    return _identify_b64(b64, cb)

# ---- video ------------------------------------------------------------------
def extract_frames(path, max_frames=None):
    """~1 candidate frame per 1.5 s, keep the sharpest ones. Returns (list_of_jpeg_b64, preview_path)."""
    max_frames = max_frames or config.VIDEO_MAX_FRAMES
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        raise AppError("Could not open this video file.\nPlease choose a valid video (MP4, MOV, AVI...).")
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 25
    if total <= 0:
        cap.release()
        raise AppError("This video appears to be empty or damaged.")

    n_cand = min(max_frames * 3, max(1, int(total / fps / 1.5) + 1))
    positions = [total // 2] if n_cand == 1 else np.linspace(0, total - 1, n_cand, dtype=int)
    candidates = []
    for pos in positions:
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(pos))
        ok, frame = cap.read()
        if ok and frame is not None:
            sharp = cv2.Laplacian(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), cv2.CV_64F).var()
            candidates.append((int(pos), sharp, frame))
    cap.release()
    if not candidates:
        raise AppError("No frames could be read from this video.")

    best = sorted(candidates, key=lambda c: -c[1])[:max_frames]   # sharpest frames
    best.sort(key=lambda c: c[0])                                  # back in time order
    frames_b64 = []
    for _, _, frame in best:
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frames_b64.append(_to_b64_jpeg(Image.fromarray(rgb)))

    config.ensure_dirs()
    preview = os.path.join(config.IMAGES_DIR, "last_video_preview.jpg")
    cv2.imwrite(preview, best[len(best) // 2][2])
    return frames_b64, preview

def _vote(values):
    """Most common non-empty value (case-insensitive); ties -> the longer one."""
    values = [v for v in values if v]
    if not values:
        return ""
    counts = Counter(v.lower() for v in values)
    top = max(counts.values())
    winners = [v for v in values if counts[v.lower()] == top]
    return max(winners, key=len)


def identify_video(path, progress=None):
    """Returns (hardware_dict, preview_image_path)."""
    cb = progress or (lambda m: None)
    cb("Analyzing video...\nExtracting frames")
    frames, preview = extract_frames(path)
    results = []
    for i, b64 in enumerate(frames, 1):
        cb(f"Analyzing video...\nFrame {i} / {len(frames)}")
        results.append(_identify_b64(b64))
    combined = {}

    # Fields where voting makes sense
    for k in (
        "manufacturer",
        "product_name",
        "model",
        "part_number",
        "hardware_type",
        "category",
        "visual_description",
        "likely_use",
        "confidence",
    ):
        combined[k] = _vote([r.get(k, "") for r in results])

    # Combine visible components from all frames
    components = []
    for r in results:
        for item in r.get("visible_components", []):
            if item not in components:
                components.append(item)

    combined["visible_components"] = components[:15]

    # Combine visible text from all frames
    visible_text = []
    for r in results:
        for item in r.get("visible_text", []):
            if item not in visible_text:
                visible_text.append(item)

    combined["visible_text"] = visible_text[:10]

    # Backward compatibility
    combined["visible_labels"] = combined["visible_text"]

    return combined, preview