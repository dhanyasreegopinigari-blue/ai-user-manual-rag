"""Ollama client + FAISS index + question generation + grounded answering."""
import difflib
from email.mime import message
import json
import os
import re

from cv2 import data
import faiss
import numpy as np
import requests

import config
import database as db
from config import AppError


# =============================================================================
# Ollama HTTP helpers
# =============================================================================
def _post(path, payload, model):
    url = config.OLLAMA_URL.rstrip("/") + path
    try:
        r = requests.post(url, json=payload, timeout=config.REQUEST_TIMEOUT)
    except requests.exceptions.ConnectionError:
        raise AppError("Ollama is not running.\n\nPlease start Ollama and try again.")
    except requests.exceptions.Timeout:
        raise AppError("Ollama took too long to respond.\n\nTry again, or use a smaller model.")
    except requests.exceptions.RequestException as e:
        raise AppError(f"Could not talk to Ollama:\n{e}")
    if r.status_code == 404:
        body = r.text.lower()
        if "model" in body and "not found" in body:
            raise AppError(f"Required Ollama model was not found:\n\n{model}\n\n"
                           f"Install it with:  ollama pull {model}")
        err = AppError("This Ollama endpoint was not found. Please update Ollama.")
        err.endpoint_missing = True
        raise err
    if r.status_code != 200:
        raise AppError(f"Ollama error ({r.status_code}):\n{r.text[:300]}")
    return r.json()


def strip_think(text):
    return re.sub(r"<think>.*?(</think>|$)", "", text or "", flags=re.DOTALL).strip()


def parse_json(text):
    """Extract the first JSON object from model output. Returns None if it can't be parsed."""
    text = re.sub(r"```(?:json)?", "", strip_think(text))
    s, e = text.find("{"), text.rfind("}")
    if s == -1 or e <= s:
        return None
    try:
        data = json.loads(text[s:e + 1])
        return data if isinstance(data, dict) else None
    except ValueError:
        return None

def chat(
    model,
    user,
    system=None,
    images=None,
    json_mode=False,
    temperature=0.2,
    num_ctx=8192,
    num_predict=None
):
    """Single-turn chat call. `images` = list of base64 strings (vision models)."""

    messages = []

    if system:
        messages.append({
            "role": "system",
            "content": system
        })

    msg = {
        "role": "user",
        "content": user
    }

    if images:
        msg["images"] = images

    messages.append(msg)

    # Ollama generation options
    options = {
        "temperature": temperature,
        "num_ctx": num_ctx,
    }

    if num_predict is not None:
        options["num_predict"] = num_predict

    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "think": False,
        "options": options,
    }

    if json_mode:
        payload["format"] = "json"

    data = _post("/api/chat", payload, model)

    print("\n========== FULL OLLAMA RESPONSE ==========")
    print(repr(data))
    print("===========================================\n")

    message = data.get("message", {})

    print("\n========== OLLAMA MESSAGE ==========")
    print(repr(message))
    print("====================================\n")

    content = message.get("content", "")
    thinking = message.get("thinking", "")

    print("[OLLAMA CONTENT]")
    print(repr(content))

    print("[OLLAMA THINKING]")
    print(repr(thinking))

    return strip_think(content)

def embed(texts, prefix="search_document: "):
    """Embed texts with nomic-embed-text -> normalised float32 array (cosine via inner product)."""
    texts = [prefix + t[:6000] for t in texts]
    try:
        data = _post("/api/embed", {"model": config.EMBED_MODEL, "input": texts}, config.EMBED_MODEL)
        vectors = data["embeddings"]
    except AppError as e:
        if not getattr(e, "endpoint_missing", False):
            raise
        # very old Ollama versions: one request per text
        vectors = [_post("/api/embeddings", {"model": config.EMBED_MODEL, "prompt": t},
                         config.EMBED_MODEL)["embedding"] for t in texts]
    arr = np.array(vectors, dtype="float32")
    faiss.normalize_L2(arr)
    return arr


def test_connection(url=None):
    """Returns (ok, message). Lists which required models are missing."""
    url = (url or config.OLLAMA_URL).rstrip("/")
    try:
        r = requests.get(url + "/api/tags", timeout=5)
        r.raise_for_status()
        installed = {m["name"] for m in r.json().get("models", [])}
    except requests.exceptions.RequestException:
        return False, "Ollama is not running.\n\nPlease start Ollama and try again."
    missing = []
    for name in (config.VISION_MODEL, config.LLM_MODEL, config.EMBED_MODEL):
        if name not in installed and f"{name}:latest" not in installed:
            missing.append(name)
    if missing:
        return False, "Ollama is running, but these models were not found:\n\n" + "\n".join(missing)
    return True, "Ollama is running and all required models are installed."


# =============================================================================
# FAISS (one index per manual; vector id == SQLite chunk id via IndexIDMap)
# =============================================================================
def index_path(manual_id):
    return os.path.join(config.FAISS_DIR, f"manual_{manual_id}.index")


def build_index(manual_id, chunk_ids, texts, progress=None):
    cb = progress or (lambda m: None)
    parts = []
    for i in range(0, len(texts), 8):
        cb(f"Creating embeddings... {min(i + 8, len(texts))}/{len(texts)}")
        parts.append(embed(texts[i:i + 8]))
    vectors = np.vstack(parts)
    cb("Building search index...")
    index = faiss.IndexIDMap(faiss.IndexFlatIP(vectors.shape[1]))
    index.add_with_ids(vectors, np.array(chunk_ids, dtype="int64"))
    config.ensure_dirs()
    faiss.write_index(index, index_path(manual_id))


def delete_index(manual_id):
    try:
        os.remove(index_path(manual_id))
    except OSError:
        pass


def _search_index(manual_id, qvec, k):
    path = index_path(manual_id)
    if not os.path.isfile(path):
        return []
    index = faiss.read_index(path)
    scores, ids = index.search(qvec, min(k, index.ntotal))
    return [(int(i), float(s)) for i, s in zip(ids[0], scores[0]) if i != -1]


def search(manual_id, question, k=None):
    """Top-k manual chunks for a question (SQLite rows, each with a 'score')."""
    hits = _search_index(manual_id, embed([question], "search_query: "), k or config.TOP_K)
    chunks = db.get_chunks([i for i, _ in hits])
    scores = dict(hits)
    for c in chunks:
        c["score"] = scores.get(c["id"], 0.0)
    return chunks


def search_all_manuals(query_text, top=3):
    """Semantic fallback for hardware matching: [(manual, best_score)] sorted best first."""
    qvec = embed([query_text], "search_query: ")
    results = []
    for m in db.list_manuals():
        hits = _search_index(m["id"], qvec, 1)
        if hits:
            results.append((m, hits[0][1]))
    results.sort(key=lambda x: -x[1])
    return results[:top]


# =============================================================================
# Suggested questions
# =============================================================================
FALLBACK_QUESTIONS = [
    "How do I install this device?", "How do I start the device?", "How do I stop the device?",
    "How do I perform maintenance?", "What safety precautions should I follow?",
]


def generate_questions(manual_id, progress=None):
    """5-8 questions generated from real manual excerpts."""
    (progress or (lambda m: None))("Reading the manual to suggest questions...")
    chunks = db.get_all_chunks(manual_id)
    if not chunks:
        return FALLBACK_QUESTIONS
    step = max(1, len(chunks) // 8)
    sample = chunks[::step][:8]
    excerpts = "\n\n".join(f"[Excerpt {i + 1}]\n{c['chunk_text'][:700]}" for i, c in enumerate(sample))
    prompt = (
        "Below are excerpts from a hardware user manual.\n\n" + excerpts +
        "\n\nWrite 6 short, practical questions a user might ask, such as how to install, start, stop, "
        "maintain, or troubleshoot. Every question MUST be answerable from the excerpts above and must not "
        "mention anything that is not in them.\n"
        'Return ONLY JSON: {"questions": ["...", "..."]}  /no_think')
    try:
        data = parse_json(chat(config.LLM_MODEL, prompt, json_mode=True, temperature=0.3))
    except AppError:
        raise
    questions = []
    for q in (data or {}).get("questions", []):
        q = str(q).strip()
        if q and q not in questions:
            questions.append(q)
    return questions[:8] if len(questions) >= 3 else FALLBACK_QUESTIONS


# =============================================================================
# Grounded answer
# =============================================================================
SYSTEM_PROMPT = """You are an AI assistant for a hardware user manual.

Answer the user's question ONLY using the provided manual context.

Do not invent procedures, specifications, warnings, or values.

If the answer cannot be found in the supplied manual context,
clearly say that the manual does not provide enough information.

Give the answer as simple sequential steps.

Use simple language suitable for a normal hardware user.

When possible, associate each step with the relevant manual page.
The page numbers appear in the context as [Page N] markers."""

ANSWER_FORMAT = (
    'Return ONLY valid JSON in exactly this format:\n'
    '{"found": true, "title": "short title", "summary": "one sentence", '
    '"answer": "a clear written answer of 3-5 full sentences in simple language, based only on the manual", '
    '"warning": "safety warning from the manual, or empty string", '
    '"steps": [{"number": 1, "text": "one simple step", "page": 12}]}\n'
    'If the manual does not contain the answer, return {"found": false, "title": "Not in manual", '
    '"summary": "The manual does not provide enough information to answer this.", '
    '"answer": "The manual does not provide enough information to answer this.", '
    '"warning": "", "steps": []}')


def _to_int(v):
    try:
        return int(str(v).strip())
    except (ValueError, TypeError):
        return None


def _fallback_steps(raw, default_page):
    """Used when the model returns malformed JSON: turn plain text into steps."""
    lines = [re.sub(r"^\s*(\d+[.)]|[-*•])\s*", "", ln).strip() for ln in strip_think(raw).splitlines()]
    lines = [ln for ln in lines if len(ln) > 3 and not ln.startswith(("{", "}", "```"))]
    return [{"number": i + 1, "text": ln, "page": default_page} for i, ln in enumerate(lines[:10])]


def _page_excerpt(manual_id, page, step_text, max_sentences=2):
    """The manual's own sentences from `page` that best match the step (real manual text, not generated)."""
    rows = db.query("SELECT text FROM manual_pages WHERE manual_id=? AND page_number=?", (manual_id, page))
    text = re.sub(r"\s+", " ", rows[0]["text"]).strip() if rows else ""
    if not text:
        return ""
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if len(s.strip()) > 15]
    if not sentences:
        return text[:250]
    want = set(re.findall(r"[a-z0-9]{3,}", step_text.lower()))
    scored = sorted(sentences, key=lambda s: -len(want & set(re.findall(r"[a-z0-9]{3,}", s.lower()))))
    best = scored[:max_sentences]
    return " ".join(s for s in sentences if s in best)[:500]

def _answer_quick(manual_id, question, progress=None):
    """Quick RAG pipeline. Returns
    {title, summary, answer, warning, found,
     steps:[{number,text,page,image,image_kind,source}]}
    """

    cb = progress or (lambda m: None)

    cb("Searching the manual...")

    chunks = search(manual_id, question)

    if not chunks:
        return {
            "title": "Not in manual",
            "found": False,
            "warning": "",
            "steps": [],
            "summary": "The manual does not provide enough information to answer this."
        }

    # Use fewer, shorter chunks to reduce LLM processing time.
    # The retrieved chunks are already ranked by relevance.
    selected_chunks = chunks[:3]

    context = "\n\n=====\n\n".join(
        c["chunk_text"][:1500]
        for c in selected_chunks
    )

    allowed = []

    for c in selected_chunks:
        allowed += [
            int(p)
            for p in re.findall(
                r"\[Page (\d+)\]",
                c["chunk_text"]
            )
        ]

        allowed.append(c["page_number"])

    default_page = selected_chunks[0]["page_number"]

    cb("Writing the answer...")

    prompt = (
        f"MANUAL CONTEXT:\n{context}\n\n"
        f"USER QUESTION: {question}\n\n"
        f"{ANSWER_FORMAT}\n/no_think"
    )

    raw = chat(
        config.LLM_MODEL,
        prompt,
        system=SYSTEM_PROMPT,
        json_mode=True,
        temperature=0.1,
        num_ctx=4096,
        num_predict=400
    )

    data = parse_json(raw)

    if data is None:
        # Malformed JSON -> simple text fallback
        steps = _fallback_steps(raw, default_page)

        data = {
            "title": question[:60],
            "summary": "",
            "warning": "",
            "found": bool(steps)
        }

    else:
        steps = []

        for s in data.get("steps") or []:

            if isinstance(s, str):
                s = {"text": s}

            if not isinstance(s, dict):
                continue

            if not str(s.get("text", "")).strip():
                continue

            page = _to_int(s.get("page"))

            steps.append({
                "text": str(s["text"]).strip(),
                "page": page if page in allowed else default_page,
                "warning": str(s.get("warning") or "").strip()
            })

    # Renumber and attach real images from the manual.
    # Images are never generated by the LLM.
    for i, s in enumerate(steps, 1):

        s["number"] = i

        s["image"], s["image_kind"] = db.get_page_visual(
            manual_id,
            s["page"]
        )

        s["source"] = _page_excerpt(
            manual_id,
            s["page"],
            s["text"]
        )

    found = (
        bool(steps)
        and data.get("found", True) is not False
    )

    return {
        "title": str(
            data.get("title") or question
        )[:80],

        "summary": (
            str(data.get("summary") or "")
            if found or data.get("summary")
            else
            "The manual does not provide enough information to answer this."
        ),

        "answer": str(
            data.get("answer")
            or data.get("summary")
            or ""
        ).strip(),

        "warning": str(
            data.get("warning") or ""
        ).strip(),

        "found": found,

        "steps": steps if found else [],
    }

# =============================================================================
# Full / end-to-end guides (many pages) vs. quick answers (one or two pages)
# =============================================================================
BROAD_WORDS = ("setup", "set up", "set-up", "full", "complete", "end to end", "end-to-end", "entire", "whole",
               "from scratch", "getting started", "get started", "start to finish", "step by step",
               "all steps", "install", "assemble", "first time", "configure", "running")

EXTRACT_FORMAT = (
    'Return ONLY JSON: {"steps": [{"text": "one simple step", "page": 12}], "warnings": ["..."]}\n'
    "Include ONLY instructions found in the context above that help answer the question, in the order they "
    "appear in the manual. Keep important details (ports, cables, connectors, switches, software settings, values). "
    'If nothing in this context is relevant return {"steps": [], "warnings": []}.')


def is_broad(question):
    q = question.lower()
    return any(w in q for w in BROAD_WORDS)


def _not_found():
    msg = "The manual does not provide enough information to answer this."
    return {"title": "Not in manual", "found": False, "warning": "", "steps": [], "summary": msg, "answer": msg}


def _attach_visuals(manual_id, steps):
    for i, s in enumerate(steps, 1):
        s["number"] = i
        s["image"], s["image_kind"] = db.get_page_visual(manual_id, s["page"])
        s["source"] = _page_excerpt(manual_id, s["page"], s["text"])


def _answer_full(manual_id, question, cb):
    cb("Searching the whole manual...")
    chunks = search(manual_id, question, config.FULL_TOP_K)
    if not chunks:
        return _not_found()
    chunks.sort(key=lambda c: c["page_number"])          # keep manual order
    size = config.FULL_BATCH
    batches = [chunks[i:i + size] for i in range(0, len(chunks), size)]

    steps, warnings = [], []
    for n, batch in enumerate(batches, 1):
        cb(f"Reading manual part {n} / {len(batches)}...")
        allowed = []
        for c in batch:
            allowed += [int(p) for p in re.findall(r"\[Page (\d+)\]", c["chunk_text"])] + [c["page_number"]]
        context = "\n\n=====\n\n".join(c["chunk_text"][:4000] for c in batch)
        prompt = f"MANUAL CONTEXT:\n{context}\n\nUSER QUESTION: {question}\n\n{EXTRACT_FORMAT}  /no_think"
        data = parse_json(chat(config.LLM_MODEL, prompt, system=SYSTEM_PROMPT, json_mode=True,
                               temperature=0.1)) or {}
        for s in data.get("steps") or []:
            s = {"text": s} if isinstance(s, str) else s
            text = str(s.get("text", "")).strip() if isinstance(s, dict) else ""
            if not text:
                continue
            if any(difflib.SequenceMatcher(None, text.lower(), o["text"].lower()).ratio() > 0.93 for o in steps):
                continue                                   # duplicate of an earlier step
            page = _to_int(s.get("page"))
            steps.append({"text": text, "page": page if page in allowed else batch[0]["page_number"],
                          "warning": ""})
        for w in data.get("warnings") or []:
            w = str(w).strip()
            if w and w not in warnings:
                warnings.append(w)

    steps = steps[:config.MAX_STEPS]
    if not steps:
        return _not_found()

    cb("Writing the final guide...")
    listing = "\n".join(f"{i}. (page {s['page']}) {s['text']}" for i, s in enumerate(steps, 1))
    prompt = (f"USER QUESTION: {question}\n\nSTEPS EXTRACTED FROM THE MANUAL:\n{listing}\n\n"
              f"MANUAL WARNINGS: {'; '.join(warnings) or 'none'}\n\n"
              "Using ONLY the steps and warnings above, write an overview of the whole procedure. "
              'Return ONLY JSON: {"title": "short title", "summary": "one sentence", '
              '"answer": "4-6 full sentences in simple language describing the whole procedure from start to finish", '
              '"warning": "the most important safety warnings, or empty string"}  /no_think')
    data = parse_json(chat(config.LLM_MODEL, prompt, system=SYSTEM_PROMPT, json_mode=True, temperature=0.1)) or {}
    _attach_visuals(manual_id, steps)
    return {"title": str(data.get("title") or question)[:80],
            "summary": str(data.get("summary") or f"Full guide in {len(steps)} steps."),
            "answer": str(data.get("answer") or data.get("summary") or "").strip(),
            "warning": str(data.get("warning") or "; ".join(warnings[:3])).strip(),
            "found": True, "steps": steps}


def answer_question(manual_id, question, progress=None, mode="auto"):
    """mode: 'auto' (detect broad questions), 'full' (end-to-end guide) or 'quick' (1-2 pages)."""
    cb = progress or (lambda m: None)
    if mode == "full" or (mode == "auto" and is_broad(question)):
        return _answer_full(manual_id, question, cb)
    return _answer_quick(manual_id, question, cb)

def answer_general_image(hardware, question, progress=None):
    """
    Answer a question about an uploaded image when no matching
    user manual was found.

    This mode uses the visual analysis already produced by the
    vision model. It does not use manual/FAISS context.
    """
    cb = progress or (lambda m: None)

    cb("Analyzing the image...")

    hardware = hardware or {}

    visual_description = hardware.get("visual_description", "")
    hardware_type = hardware.get("hardware_type", "")
    category = hardware.get("category", "")
    visible_components = hardware.get("visible_components", [])
    visible_text = hardware.get("visible_text", [])
    likely_use = hardware.get("likely_use", "")
    confidence = hardware.get("confidence", "")

    components_text = ", ".join(
        str(x) for x in visible_components
    )

    text_text = ", ".join(
        str(x) for x in visible_text
    )

    context = f"""
VISUAL ANALYSIS OF THE IMAGE:

Hardware type: {hardware_type}
Category: {category}
Visual description: {visual_description}
Visible components: {components_text}
Visible text: {text_text}
Likely use: {likely_use}
Vision confidence: {confidence}
"""

    system = """
You are an image-understanding assistant.

The user uploaded an image of hardware or an electronic device.

Answer the user's question using ONLY the visual analysis provided below.

IMPORTANT RULES:
- Do not invent an exact manufacturer, product name, model, or part number.
- If the visual analysis does not establish an exact identity, clearly say that the exact identity cannot be determined from the image alone.
- Do not pretend that the image belongs to a known manual.
- You may describe visible components, appearance, possible use, and clearly readable labels.
- If something cannot be determined from the image, say so.
- Keep the answer simple and useful.
"""

    prompt = f"""
{context}

USER QUESTION:
{question}

Give a helpful answer based only on the visual information above.
"""

    cb("Generating image-based answer...")

    answer = chat(
        config.LLM_MODEL,
        prompt,
        system=system,
        temperature=0.2,
        num_ctx=4096,
        num_predict=400
    )

    return {
        "found": True,
        "title": "Image Analysis",
        "summary": visual_description or "The image was analyzed using the vision model.",
        "answer": answer.strip(),
        "warning": (
            "The exact hardware identity could not be verified from a manual."
        ),
        "steps": []
    }