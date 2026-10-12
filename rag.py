"""Ollama client + FAISS index + question generation + grounded answering."""

import difflib
import json
import os
import re

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
        r = requests.post(
            url,
            json=payload,
            timeout=config.REQUEST_TIMEOUT
        )
    except requests.exceptions.ConnectionError:
        raise AppError(
            "Ollama is not running.\n\nPlease start Ollama and try again."
        )
    except requests.exceptions.Timeout:
        raise AppError(
            "Ollama took too long to respond.\n\n"
            "Try again, or use a smaller model."
        )
    except requests.exceptions.RequestException as e:
        raise AppError(f"Could not talk to Ollama:\n{e}")

    if r.status_code == 404:
        body = r.text.lower()

        if "model" in body and "not found" in body:
            raise AppError(
                f"Required Ollama model was not found:\n\n{model}\n\n"
                f"Install it with: ollama pull {model}"
            )

        err = AppError(
            "This Ollama endpoint was not found. Please update Ollama."
        )
        err.endpoint_missing = True
        raise err

    if r.status_code != 200:
        raise AppError(
            f"Ollama error ({r.status_code}):\n{r.text[:300]}"
        )

    return r.json()


def strip_think(text):
    """Remove model thinking tags from generated text."""
    return re.sub(
        r"<think>.*?(</think>|$)",
        "",
        text or "",
        flags=re.DOTALL
    ).strip()


def parse_json(text):
    """Extract the first JSON object from model output."""

    text = re.sub(
        r"```(?:json)?",
        "",
        strip_think(text),
        flags=re.IGNORECASE
    )

    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end <= start:
        return None

    try:
        data = json.loads(text[start:end + 1])
        return data if isinstance(data, dict) else None
    except (ValueError, TypeError):
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
    """Single-turn Ollama chat call. Images must be base64 strings."""

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

    options = {
        "temperature": temperature,
        "num_ctx": num_ctx
    }

    if num_predict is not None:
        options["num_predict"] = num_predict

    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "think": False,
        "options": options
    }

    if json_mode:
        payload["format"] = "json"

    data = _post("/api/chat", payload, model)

    message_data = data.get("message", {})
    content = message_data.get("content", "")

    # Avoid printing the entire response and prompt-related information.
    return strip_think(content)


def embed(texts, prefix="search_document: "):
    """
    Generate embeddings with the configured embedding model.

    Vectors are normalised so inner-product search can approximate
    cosine similarity.
    """

    if not texts:
        return np.empty((0, 0), dtype="float32")

    texts = [
        prefix + str(text)[:6000]
        for text in texts
    ]

    try:
        data = _post(
            "/api/embed",
            {
                "model": config.EMBED_MODEL,
                "input": texts
            },
            config.EMBED_MODEL
        )

        vectors = data["embeddings"]

    except AppError as e:
        if not getattr(e, "endpoint_missing", False):
            raise

        # Compatibility with older Ollama versions.
        vectors = [
            _post(
                "/api/embeddings",
                {
                    "model": config.EMBED_MODEL,
                    "prompt": text
                },
                config.EMBED_MODEL
            )["embedding"]
            for text in texts
        ]

    arr = np.array(vectors, dtype="float32")

    if arr.ndim != 2 or arr.shape[0] == 0:
        raise AppError(
            "The embedding model did not return valid embedding vectors."
        )

    faiss.normalize_L2(arr)

    return arr


def test_connection(url=None):
    """Return (success, message) and report missing required models."""

    url = (url or config.OLLAMA_URL).rstrip("/")

    try:
        r = requests.get(
            url + "/api/tags",
            timeout=5
        )
        r.raise_for_status()

        installed = {
            model["name"]
            for model in r.json().get("models", [])
        }

    except requests.exceptions.RequestException:
        return (
            False,
            "Ollama is not running.\n\nPlease start Ollama and try again."
        )

    missing = []

    for name in (
        config.VISION_MODEL,
        config.LLM_MODEL,
        config.EMBED_MODEL
    ):
        if name not in installed and f"{name}:latest" not in installed:
            missing.append(name)

    if missing:
        return (
            False,
            "Ollama is running, but these models were not found:\n\n"
            + "\n".join(missing)
        )

    return True, "Ollama is running and all required models are installed."


# =============================================================================
# FAISS: one index per manual
# =============================================================================

def index_path(manual_id):
    return os.path.join(
        config.FAISS_DIR,
        f"manual_{manual_id}.index"
    )


def build_index(manual_id, chunk_ids, texts, progress=None):
    """Create and save a FAISS index for the manual's text chunks."""

    cb = progress or (lambda message: None)

    if not texts or not chunk_ids:
        raise AppError(
            "Cannot build the search index because the manual has no text chunks."
        )

    if len(chunk_ids) != len(texts):
        raise AppError(
            "The number of chunk IDs does not match the number of text chunks."
        )

    parts = []

    for i in range(0, len(texts), 8):
        cb(
            f"Creating embeddings... "
            f"{min(i + 8, len(texts))}/{len(texts)}"
        )

        parts.append(
            embed(texts[i:i + 8])
        )

    vectors = np.vstack(parts)

    cb("Building search index...")

    index = faiss.IndexIDMap(
        faiss.IndexFlatIP(vectors.shape[1])
    )

    index.add_with_ids(
        vectors,
        np.array(chunk_ids, dtype="int64")
    )

    config.ensure_dirs()

    faiss.write_index(
        index,
        index_path(manual_id)
    )


def delete_index(manual_id):
    """Delete a manual's FAISS index if it exists."""

    try:
        os.remove(index_path(manual_id))
    except OSError:
        pass


def _search_index(manual_id, qvec, k):
    """Search an existing FAISS index."""

    path = index_path(manual_id)

    if not os.path.isfile(path):
        return []

    index = faiss.read_index(path)

    if index.ntotal == 0:
        return []

    scores, ids = index.search(
        qvec,
        min(k, index.ntotal)
    )

    return [
        (int(chunk_id), float(score))
        for chunk_id, score in zip(ids[0], scores[0])
        if chunk_id != -1
    ]


def search(manual_id, question, k=None):
    """Return the most relevant manual chunks with similarity scores."""

    top_k = k or config.TOP_K

    hits = _search_index(
        manual_id,
        embed([question], "search_query: "),
        top_k
    )

    if not hits:
        return []

    chunks = db.get_chunks([
        chunk_id
        for chunk_id, score in hits
    ])

    scores = dict(hits)

    for chunk in chunks:
        chunk["score"] = scores.get(chunk["id"], 0.0)

    return chunks


def search_all_manuals(query_text, top=3):
    """Find the most relevant manuals for a hardware-matching query."""

    query_vector = embed(
        [query_text],
        "search_query: "
    )

    results = []

    for manual in db.list_manuals():
        hits = _search_index(
            manual["id"],
            query_vector,
            1
        )

        if hits:
            results.append((manual, hits[0][1]))

    results.sort(
        key=lambda item: -item[1]
    )

    return results[:top]


# =============================================================================
# Suggested questions
# =============================================================================

FALLBACK_QUESTIONS = [
    "How do I install this device?",
    "How do I start the device?",
    "How do I stop the device?",
    "How do I perform maintenance?",
    "What safety precautions should I follow?"
]


def generate_questions(manual_id, progress=None):
    """Generate practical questions from actual manual excerpts."""

    cb = progress or (lambda message: None)

    cb("Reading the manual to suggest questions...")

    chunks = db.get_all_chunks(manual_id)

    if not chunks:
        return FALLBACK_QUESTIONS

    step = max(1, len(chunks) // 8)
    sample = chunks[::step][:8]

    excerpts = "\n\n".join(
        f"[Excerpt {i + 1}]\n{chunk['chunk_text'][:700]}"
        for i, chunk in enumerate(sample)
    )

    prompt = (
        "Below are excerpts from a hardware user manual.\n\n"
        + excerpts
        + "\n\nWrite 6 short, practical questions a user might ask, "
        "such as how to install, start, stop, maintain, or troubleshoot. "
        "Every question MUST be answerable from the excerpts above and "
        "must not mention anything that is not in them.\n"
        'Return ONLY JSON: {"questions": ["...", "..."]}\n'
        "/no_think"
    )

    try:
        data = parse_json(
            chat(
                config.LLM_MODEL,
                prompt,
                json_mode=True,
                temperature=0.3
            )
        )
    except AppError:
        raise

    questions = []

    for question in (data or {}).get("questions", []):
        question = str(question).strip()

        if question and question not in questions:
            questions.append(question)

    return (
        questions[:8]
        if len(questions) >= 3
        else FALLBACK_QUESTIONS
    )


# =============================================================================
# Grounded answering
# =============================================================================

SYSTEM_PROMPT = """You are an AI assistant for a hardware user manual.

Answer the user's question ONLY using the provided manual context.

Do not invent procedures, specifications, warnings, or values.

If the answer cannot be found in the supplied manual context,
clearly say that the manual does not provide enough information.

Give the answer as simple sequential steps.

Use simple language suitable for a normal hardware user.

When possible, associate each step with the relevant manual page.

The page numbers appear in the context as [Page N] markers.
"""


ANSWER_FORMAT = (
    "Return ONLY valid JSON in exactly this format:\n"
    '{"found": true, "title": "short title", '
    '"summary": "one sentence", '
    '"answer": "a clear written answer of 3-5 full sentences in simple '
    'language, based only on the manual", '
    '"warning": "safety warning from the manual, or empty string", '
    '"steps": [{"number": 1, "text": "one simple step", "page": 12}]}\n'
    'If the manual does not contain the answer, return '
    '{"found": false, "title": "Not in manual", '
    '"summary": "The manual does not provide enough information to answer this.", '
    '"answer": "The manual does not provide enough information to answer this.", '
    '"warning": "", "steps": []}'
)


def _to_int(value):
    try:
        return int(str(value).strip())
    except (ValueError, TypeError):
        return None


def _fallback_steps(raw, default_page):
    """Convert plain text into steps when the model returns invalid JSON."""

    lines = [
        re.sub(
            r"^\s*(\d+[.)]|[-*•])\s*",
            "",
            line
        ).strip()
        for line in strip_think(raw).splitlines()
    ]

    lines = [
        line
        for line in lines
        if len(line) > 3
        and not line.startswith(("{", "}", "```"))
    ]

    return [
        {
            "number": i + 1,
            "text": line,
            "page": default_page
        }
        for i, line in enumerate(lines[:10])
    ]


def _page_excerpt(manual_id, page, step_text, max_sentences=2):
    """
    Retrieve actual manual text from the specified page.

    The excerpt is selected using word overlap with the generated step.
    """

    rows = db.query(
        "SELECT text FROM manual_pages "
        "WHERE manual_id=? AND page_number=?",
        (manual_id, page)
    )

    page_text = (
        re.sub(r"\s+", " ", rows[0]["text"]).strip()
        if rows
        else ""
    )

    if not page_text:
        return ""

    sentences = [
        sentence.strip()
        for sentence in re.split(r"(?<=[.!?])\s+", page_text)
        if len(sentence.strip()) > 15
    ]

    if not sentences:
        return page_text[:250]

    wanted_words = set(
        re.findall(
            r"[a-z0-9]{3,}",
            step_text.lower()
        )
    )

    scored = sorted(
        sentences,
        key=lambda sentence: -len(
            wanted_words
            & set(
                re.findall(
                    r"[a-z0-9]{3,}",
                    sentence.lower()
                )
            )
        )
    )

    best = scored[:max_sentences]

    return " ".join(
        sentence
        for sentence in sentences
        if sentence in best
    )[:500]


def _answer_quick(manual_id, question, progress=None):
    """
    Quick RAG pipeline.

    Returns:
        title, summary, answer, warning, found,
        steps containing number, text, page, image, image_kind and source.
    """

    cb = progress or (lambda message: None)

    cb("Searching the manual...")

    chunks = search(manual_id, question)

    print("\n========== RETRIEVAL DEBUG ==========")
    print(f"Question: {question}")
    print(f"Chunks retrieved: {len(chunks)}")

    for i, chunk in enumerate(chunks, start=1):
        print(f"\n--- Chunk {i} ---")
        print(f"Page: {chunk.get('page_number')}")
        print(f"Score: {chunk.get('score')}")
        print(chunk.get('chunk_text', '')[:1000])

    print("========== END RETRIEVAL DEBUG ==========\n")

    if not chunks:
        message = (
            "The manual does not provide enough information to answer this."
        )

        return {
            "title": "Not in manual",
            "found": False,
            "warning": "",
            "steps": [],
            "summary": message,
            "answer": message
        }


    # Use fewer and shorter chunks to reduce LLM processing time.
    selected_chunks = chunks[:3]

    context = "\n\n=====\n\n".join(
        chunk["chunk_text"][:1500]
        for chunk in selected_chunks
    )

    # Collect valid page numbers from the retrieved context.
    allowed = []

    for chunk in selected_chunks:
        allowed += [
            int(page)
            for page in re.findall(
                r"\[Page (\d+)\]",
                chunk["chunk_text"]
            )
        ]

        allowed.append(
            chunk["page_number"]
        )

    # Remove duplicates while preserving order.
    allowed = list(dict.fromkeys(allowed))

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
        # If JSON parsing fails, try to extract simple text steps.
        steps = _fallback_steps(
            raw,
            default_page
        )

        data = {
            "title": question[:60],
            "summary": "",
            "answer": raw.strip(),
            "warning": "",
            "found": bool(steps)
        }

    else:
        steps = []

        for step in data.get("steps") or []:
            if isinstance(step, str):
                step = {"text": step}

            if not isinstance(step, dict):
                continue

            step_text = str(
                step.get("text", "")
            ).strip()

            if not step_text:
                continue

            page = _to_int(
                step.get("page")
            )

            steps.append({
                "text": step_text,
                "page": (
                    page
                    if page in allowed
                    else default_page
                ),
                "warning": str(
                    step.get("warning") or ""
                ).strip()
            })

    # Attach real page images and text excerpts from the manual.
    # Images are retrieved from the database, not generated by the LLM.
    for i, step in enumerate(steps, 1):
        step["number"] = i

        step["image"], step["image_kind"] = db.get_page_visual(
            manual_id,
            step["page"]
        )

        step["source"] = _page_excerpt(
            manual_id,
            step["page"],
            step["text"]
        )

    found = (
        bool(steps)
        and data.get("found", True) is not False
    )

    summary = str(
        data.get("summary") or ""
    )

    if not found and not summary:
        summary = (
            "The manual does not provide enough information to answer this."
        )

    return {
        "title": str(
            data.get("title") or question
        )[:80],

        "summary": summary,

        "answer": str(
            data.get("answer")
            or data.get("summary")
            or ""
        ).strip(),

        "warning": str(
            data.get("warning") or ""
        ).strip(),

        "found": found,

        "steps": steps if found else []
    }


# =============================================================================
# Full guides versus quick answers
# =============================================================================

BROAD_WORDS = (
    "setup",
    "set up",
    "set-up",
    "full",
    "complete",
    "end to end",
    "end-to-end",
    "entire",
    "whole",
    "from scratch",
    "getting started",
    "get started",
    "start to finish",
    "step by step",
    "all steps",
    "install",
    "assemble",
    "first time",
    "configure",
    "running"
)


EXTRACT_FORMAT = (
    'Return ONLY JSON: {"steps": [{"text": "one simple step", '
    '"page": 12}], "warnings": ["..."]}\n'
    "Include ONLY instructions found in the context above that help answer "
    "the question, in the order they appear in the manual. Keep important "
    "details (ports, cables, connectors, switches, software settings, values). "
    'If nothing in this context is relevant return {"steps": [], "warnings": []}.'
)


def is_broad(question):
    question = question.lower()

    return any(
        word in question
        for word in BROAD_WORDS
    )


def _not_found():
    message = (
        "The manual does not provide enough information to answer this."
    )

    return {
        "title": "Not in manual",
        "found": False,
        "warning": "",
        "steps": [],
        "summary": message,
        "answer": message
    }


def _attach_visuals(manual_id, steps):
    """Attach actual manual visuals and excerpts to each step."""

    for i, step in enumerate(steps, 1):
        step["number"] = i

        step["image"], step["image_kind"] = db.get_page_visual(
            manual_id,
            step["page"]
        )

        step["source"] = _page_excerpt(
            manual_id,
            step["page"],
            step["text"]
        )


def _answer_full(manual_id, question, cb):
    """Build a multi-step guide from relevant manual chunks."""

    cb("Searching the whole manual...")

    chunks = search(
        manual_id,
        question,
        config.FULL_TOP_K
    )

    if not chunks:
        return _not_found()

    # Preserve the original manual page order.
    chunks.sort(
        key=lambda chunk: chunk["page_number"]
    )

    size = config.FULL_BATCH

    batches = [
        chunks[i:i + size]
        for i in range(0, len(chunks), size)
    ]

    steps = []
    warnings = []

    for n, batch in enumerate(batches, 1):
        cb(
            f"Reading manual part {n} / {len(batches)}..."
        )

        allowed = []

        for chunk in batch:
            allowed += [
                int(page)
                for page in re.findall(
                    r"\[Page (\d+)\]",
                    chunk["chunk_text"]
                )
            ]

            allowed.append(
                chunk["page_number"]
            )

        allowed = list(dict.fromkeys(allowed))

        context = "\n\n=====\n\n".join(
            chunk["chunk_text"][:4000]
            for chunk in batch
        )

        prompt = (
            f"MANUAL CONTEXT:\n{context}\n\n"
            f"USER QUESTION: {question}\n\n"
            f"{EXTRACT_FORMAT}\n/no_think"
        )

        data = parse_json(
            chat(
                config.LLM_MODEL,
                prompt,
                system=SYSTEM_PROMPT,
                json_mode=True,
                temperature=0.1
            )
        ) or {}

        for step in data.get("steps") or []:
            if isinstance(step, str):
                step = {"text": step}

            if not isinstance(step, dict):
                continue

            step_text = str(
                step.get("text", "")
            ).strip()

            if not step_text:
                continue

            # Avoid adding duplicate instructions.
            duplicate = any(
                difflib.SequenceMatcher(
                    None,
                    step_text.lower(),
                    existing["text"].lower()
                ).ratio() > 0.93
                for existing in steps
            )

            if duplicate:
                continue

            page = _to_int(
                step.get("page")
            )

            steps.append({
                "text": step_text,
                "page": (
                    page
                    if page in allowed
                    else batch[0]["page_number"]
                ),
                "warning": ""
            })

        for warning in data.get("warnings") or []:
            warning = str(warning).strip()

            if warning and warning not in warnings:
                warnings.append(warning)

    steps = steps[:config.MAX_STEPS]

    if not steps:
        return _not_found()

    cb("Writing the final guide...")

    listing = "\n".join(
        f"{i}. (page {step['page']}) {step['text']}"
        for i, step in enumerate(steps, 1)
    )

    prompt = (
        f"USER QUESTION: {question}\n\n"
        f"STEPS EXTRACTED FROM THE MANUAL:\n{listing}\n\n"
        f"MANUAL WARNINGS: {'; '.join(warnings) or 'none'}\n\n"
        "Using ONLY the steps and warnings above, write an overview of "
        "the whole procedure. "
        'Return ONLY JSON: {"title": "short title", '
        '"summary": "one sentence", '
        '"answer": "4-6 full sentences in simple language describing '
        'the whole procedure from start to finish", '
        '"warning": "the most important safety warnings, or empty string"}\n'
        "/no_think"
    )

    data = parse_json(
        chat(
            config.LLM_MODEL,
            prompt,
            system=SYSTEM_PROMPT,
            json_mode=True,
            temperature=0.1
        )
    ) or {}

    _attach_visuals(
        manual_id,
        steps
    )

    return {
        "title": str(
            data.get("title") or question
        )[:80],

        "summary": str(
            data.get("summary")
            or f"Full guide in {len(steps)} steps."
        ),

        "answer": str(
            data.get("answer")
            or data.get("summary")
            or ""
        ).strip(),

        "warning": str(
            data.get("warning")
            or "; ".join(warnings[:3])
        ).strip(),

        "found": True,

        "steps": steps
    }


def answer_question(
    manual_id,
    question,
    progress=None,
    mode="auto"
):
    """
    Answer a manual question.

    mode:
        auto  - choose full or quick mode automatically
        full  - generate an end-to-end guide
        quick - generate a shorter answer
    """

    cb = progress or (lambda message: None)

    if mode == "full" or (
        mode == "auto" and is_broad(question)
    ):
        return _answer_full(
            manual_id,
            question,
            cb
        )

    return _answer_quick(
        manual_id,
        question,
        cb
    )


# =============================================================================
# General image-based answers when no matching manual is found
# =============================================================================

def answer_general_image(hardware, question, progress=None):
    """
    Answer a question about an uploaded image when no matching manual
    was found.

    Uses the visual analysis already produced by the vision model.
    Does not use manual or FAISS context.
    """

    cb = progress or (lambda message: None)

    cb("Analyzing the image...")

    hardware = hardware or {}

    visual_description = hardware.get(
        "visual_description",
        ""
    )

    hardware_type = hardware.get(
        "hardware_type",
        ""
    )

    category = hardware.get(
        "category",
        ""
    )

    visible_components = hardware.get(
        "visible_components",
        []
    )

    visible_text = hardware.get(
        "visible_text",
        []
    )

    likely_use = hardware.get(
        "likely_use",
        ""
    )

    confidence = hardware.get(
        "confidence",
        ""
    )

    components_text = ", ".join(
        str(item)
        for item in visible_components
    )

    text_text = ", ".join(
        str(item)
        for item in visible_text
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
- If the visual analysis does not establish an exact identity, clearly say
  that the exact identity cannot be determined from the image alone.
- Do not pretend that the image belongs to a known manual.
- You may describe visible components, appearance, possible use, and
  clearly readable labels.
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
        "summary": (
            visual_description
            or "The image was analyzed using the vision model."
        ),
        "answer": answer.strip(),
        "warning": (
            "The exact hardware identity could not be verified from a manual."
        ),
        "steps": []
    }