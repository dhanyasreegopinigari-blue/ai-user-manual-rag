"""Online LLM API Integration & Hybrid General Knowledge Engine.

Supports:
- Google Gemini API (gemini-2.5-flash / gemini-1.5-pro)
- OpenAI API (gpt-4o-mini / gpt-4o)
- Anthropic Claude API (claude-3-5-sonnet / claude-3-5-haiku)
- Local Ollama fallback (qwen, llama, mistral)
"""
import json
import os
import re
import requests

import config
import database as db
import services.rag as rag
import services.visual_ref as visual_ref
import services.components as comp_service


SYSTEM_PROMPT = """You are ElectroLearn AI, an expert, enthusiastic, and sophisticated electronics engineering assistant.
Your goal is to help users learn, understand, and troubleshoot electronic components, circuits, pinouts, and hardware.

Guidelines:
1. Provide well-structured, beginner-friendly yet technically thorough explanations.
2. When explaining components (e.g., NE555, ATmega328P, Transistors, Op-Amps, Diodes, Resistors):
   - Explain what it is and what it does in simple terms.
   - Give typical real-world applications and circuit uses.
   - Mention key specs, precautions, and pinout logic when relevant.
3. If manual reference context is provided, prioritize verified facts and page citations from the manual.
4. If NO manual context is provided or the question is general electronics knowledge (e.g. "What is an IC?", "Explain Ohm's Law", "How do I solder?"), answer directly with your vast engineering knowledge! Never say "this is not in the manual" for general questions.
5. If the user asks for REPAIR, TROUBLESHOOTING, or COMPONENT REPLACEMENT:
   - Provide a structured guide including:
     * ⚠️ SAFETY FIRST: Discharge high-voltage capacitors, disconnect power, ESD precautions.
     * 🛠 REQUIRED TOOLS & PARTS: Multimeter, soldering iron, desoldering pump, components.
     * 📋 STEP-BY-STEP DIAGNOSTIC PROCEDURE: Numbered steps with expected multimeter/scope readings.
     * 🔀 TROUBLESHOOTING BRANCHES: "If reading is X, then do Y; if reading is Z, do W."
6. For standard/general questions (not troubleshooting), keep explanations normal, engaging, and concise.
7. Use clean markdown formatting with clear headings, bullet points, and code blocks for schematics or calculations.
"""


def get_active_provider():
    """Detect which provider to use based on config and available API keys."""
    config.load_env()
    prov = getattr(config, "LLM_PROVIDER", "auto").lower().strip()
    if prov in ("gemini", "openai", "claude", "ollama") and prov != "auto":
        return prov

    # Auto-detection priority
    if getattr(config, "GEMINI_API_KEY", "").strip():
        return "gemini"
    if getattr(config, "OPENAI_API_KEY", "").strip():
        return "openai"
    if getattr(config, "ANTHROPIC_API_KEY", "").strip():
        return "claude"
    return "ollama"


def _format_messages_for_llm(history, user_prompt, system_prompt=SYSTEM_PROMPT):
    """Format conversation history into standardized messages."""
    msgs = []
    if system_prompt:
        msgs.append({"role": "system", "content": system_prompt})
    if history:
        for h in history[-8:]:
            r = h.get("role", "user")
            c = h.get("content", "")
            if r in ("user", "assistant") and c:
                msgs.append({"role": r, "content": c})
    msgs.append({"role": "user", "content": user_prompt})
    return msgs


# ---- Gemini API (Streaming) -------------------------------------------------
def stream_gemini(messages, stream_cb=None):
    """Stream response from Google Gemini API."""
    key = getattr(config, "GEMINI_API_KEY", "").strip()
    if not key:
        raise ValueError("GEMINI_API_KEY is not set in your .env file.")

    model = getattr(config, "GEMINI_MODEL", "gemini-2.5-flash").strip()
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:streamGenerateContent?key={key}&alt=sse"

    # Convert messages to Gemini format
    system_inst = None
    contents = []
    for m in messages:
        if m["role"] == "system":
            system_inst = {"parts": [{"text": m["content"]}]}
        else:
            role = "user" if m["role"] == "user" else "model"
            contents.append({"role": role, "parts": [{"text": m["content"]}]})

    payload = {
        "contents": contents,
        "generationConfig": {
            "temperature": 0.3,
            "maxOutputTokens": 2048,
        }
    }
    if system_inst:
        payload["systemInstruction"] = system_inst

    resp = requests.post(url, json=payload, stream=True, timeout=(5, 60))
    if resp.status_code != 200:
        err_msg = f"Gemini API Error ({resp.status_code}): {resp.text[:300]}"
        raise RuntimeError(err_msg)

    full_text = []
    for line in resp.iter_lines(decode_unicode=True):
        if not line:
            continue
        if line.startswith("data: "):
            data_str = line[6:].strip()
            if data_str == "[DONE]":
                break
            try:
                chunk_json = json.loads(data_str)
                candidates = chunk_json.get("candidates") or []
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    for part in parts:
                        txt = part.get("text", "")
                        if txt:
                            full_text.append(txt)
                            if stream_cb:
                                stream_cb(txt)
            except Exception:
                pass

    return "".join(full_text)


# ---- OpenAI API (Streaming) -------------------------------------------------
def stream_openai(messages, stream_cb=None):
    """Stream response from OpenAI API."""
    key = getattr(config, "OPENAI_API_KEY", "").strip()
    if not key:
        raise ValueError("OPENAI_API_KEY is not set in your .env file.")

    model = getattr(config, "OPENAI_MODEL", "gpt-4o-mini").strip()
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.3,
        "stream": True
    }

    resp = requests.post(url, headers=headers, json=payload, stream=True, timeout=(5, 60))
    if resp.status_code != 200:
        raise RuntimeError(f"OpenAI API Error ({resp.status_code}): {resp.text[:300]}")

    full_text = []
    for line in resp.iter_lines(decode_unicode=True):
        if not line:
            continue
        if line.startswith("data: "):
            data_str = line[6:].strip()
            if data_str == "[DONE]":
                break
            try:
                chunk = json.loads(data_str)
                delta = chunk["choices"][0].get("delta", {})
                txt = delta.get("content", "")
                if txt:
                    full_text.append(txt)
                    if stream_cb:
                        stream_cb(txt)
            except Exception:
                pass

    return "".join(full_text)


# ---- Anthropic Claude API (Streaming) ---------------------------------------
def stream_claude(messages, stream_cb=None):
    """Stream response from Anthropic Claude API."""
    key = getattr(config, "ANTHROPIC_API_KEY", "").strip()
    if not key:
        raise ValueError("ANTHROPIC_API_KEY is not set in your .env file.")

    model = getattr(config, "ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022").strip()
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }

    system_text = ""
    claude_msgs = []
    for m in messages:
        if m["role"] == "system":
            system_text = m["content"]
        else:
            claude_msgs.append({"role": m["role"], "content": m["content"]})

    payload = {
        "model": model,
        "messages": claude_msgs,
        "max_tokens": 2048,
        "temperature": 0.3,
        "stream": True
    }
    if system_text:
        payload["system"] = system_text

    resp = requests.post(url, headers=headers, json=payload, stream=True, timeout=(5, 60))
    if resp.status_code != 200:
        raise RuntimeError(f"Claude API Error ({resp.status_code}): {resp.text[:300]}")

    full_text = []
    for line in resp.iter_lines(decode_unicode=True):
        if not line:
            continue
        if line.startswith("data: "):
            data_str = line[6:].strip()
            try:
                ev = json.loads(data_str)
                if ev.get("type") == "content_block_delta":
                    txt = ev.get("delta", {}).get("text", "")
                    if txt:
                        full_text.append(txt)
                        if stream_cb:
                            stream_cb(txt)
            except Exception:
                pass

    return "".join(full_text)


# ---- Ollama (Local Streaming) -----------------------------------------------
def stream_ollama(messages, stream_cb=None):
    """Stream response from local Ollama instance."""
    url = config.OLLAMA_URL.rstrip("/").replace("localhost", "127.0.0.1") + "/api/chat"
    model = config.LLM_MODEL
    payload = {
        "model": model,
        "messages": messages,
        "stream": True,
        "options": {
            "temperature": 0.3,
            "num_ctx": 4096
        }
    }
    resp = requests.post(url, json=payload, stream=True, timeout=(1.5, 30))
    if resp.status_code != 200:
        raise RuntimeError(f"Ollama Error ({resp.status_code}): {resp.text[:300]}")

    full_text = []
    for line in resp.iter_lines(decode_unicode=True):
        if not line:
            continue
        try:
            chunk = json.loads(line)
            txt = chunk.get("message", {}).get("content", "")
            if txt:
                full_text.append(txt)
                if stream_cb:
                    stream_cb(txt)
        except Exception:
            pass

    return rag.strip_think("".join(full_text))


# ---- Universal Dispatcher ---------------------------------------------------
def call_llm_stream(messages, stream_cb=None):
    """Call the active LLM provider with streaming tokens."""
    provider = get_active_provider()
    try:
        if provider == "gemini":
            return stream_gemini(messages, stream_cb=stream_cb)
        elif provider == "openai":
            return stream_openai(messages, stream_cb=stream_cb)
        elif provider == "claude":
            return stream_claude(messages, stream_cb=stream_cb)
        else:
            return stream_ollama(messages, stream_cb=stream_cb)
    except Exception as e:
        # If an online API fails, attempt graceful fallback to local Ollama
        if provider != "ollama":
            print(f"[LLM] Provider {provider} failed ({e}), attempting Ollama fallback...")
            try:
                return stream_ollama(messages, stream_cb=stream_cb)
            except Exception:
                pass
        raise e


REPAIR_KEYWORDS = {
    "repair", "fix", "troubleshoot", "troubleshooting", "diagnose", "diagnosis",
    "replacement", "replace", "not working", "broken", "blown", "test", "fault",
    "short", "shorted", "burn", "burned", "multimeter", "defective", "fail",
    "failed", "dead", "smoke", "overheating", "overheat", "damage"
}


# ---- Hybrid RAG + General Knowledge ----------------------------------------
def answer_hybrid(manual_id, question, history=None, progress_cb=None, stream_cb=None, photo_path=None):
    """Intelligently combine manual context with general LLM knowledge.

    - If the question relates to an indexed manual, extracts relevant chunks as context.
    - If no manual context is found or it's a general electronics question, answers
      from the LLM's comprehensive general knowledge.
    - If troubleshooting/repair is requested, provides structured safety, tools,
      diagnostic steps with expected multimeter readings, and repair branches.
    - Automatically collects relevant inline images (manual figures, pinout diagrams,
      or user-scanned photos).
    - Supports real-time streaming tokens.
    """
    cb = progress_cb or (lambda _: None)
    provider = get_active_provider()
    cb(f"Connecting to {provider.upper()} Assistant...")

    manual_context = ""
    has_manual_match = False
    matched_pages = []
    chunks = []

    # 1. Search manual chunks if a manual is active
    if manual_id:
        try:
            cb("Checking manual for relevant topics...")
            chunks = rag.search(manual_id, question, top_k=3)
            q_words = set(re.findall(r"[a-z0-9]{3,}", question.lower()))
            for ch in chunks:
                ch_words = set(re.findall(r"[a-z0-9]{3,}", ch.get("chunk_text", "").lower()))
                overlap = len(q_words & ch_words)
                if overlap >= 2:
                    has_manual_match = True
                pno = ch.get("page_number")
                if pno and pno not in matched_pages:
                    matched_pages.append(pno)

            if has_manual_match and chunks:
                manual_context = "\n\n==== VERIFIED MANUAL CONTEXT ====\n" + "\n\n".join(
                    f"[Page {c.get('page_number', '?')}]: {c.get('chunk_text', '')[:1200]}"
                    for c in chunks[:3]
                ) + "\n=================================\n"
        except Exception as e:
            print(f"[HYBRID] Manual search note: {e}")

    # Check for repair / troubleshooting query
    q_lower = question.lower()
    is_repair = any(kw in q_lower for kw in REPAIR_KEYWORDS)

    # 2. Construct the prompt
    repair_instruction = ""
    if is_repair:
        repair_instruction = (
            "\n\nCRITICAL - STRUCTURE AS A STEP-BY-STEP REPAIR & TROUBLESHOOTING GUIDE:\n"
            "1. ⚠️ SAFETY FIRST: Discharge bulk filter capacitors, disconnect power/mains, ESD safety wristband/mat.\n"
            "2. 🛠 REQUIRED TOOLS & PARTS: Digital Multimeter, Soldering Station, Desoldering pump/wick, and specific replacement components.\n"
            "3. 📋 STEP-BY-STEP DIAGNOSTIC PROCEDURE: Numbered steps with specific test points and EXPECTED MULTIMETER/SCOPE READINGS (e.g. 'Measure DC voltage at pin 8: should read +5.0V ± 0.25V. If 0V, inspect diode D1').\n"
            "4. 🔀 TROUBLESHOOTING BRANCHES: 'If reading is X, do Y; if reading is Z, do W.'\n"
        )

    if manual_context:
        user_prompt = (
            f"The user is asking about a specific hardware manual.\n"
            f"{manual_context}\n\n"
            f"USER QUESTION: {question}\n\n"
            f"Instructions: Use the verified manual context above to provide guidance. "
            f"Include relevant page citations. If the manual lacks some details, supplement with your engineering knowledge."
            f"{repair_instruction}"
        )
    else:
        user_prompt = (
            f"USER QUESTION: {question}\n\n"
            f"Instructions: Answer thoroughly using your comprehensive electronics engineering and hardware knowledge. "
            f"Provide a clear, engaging, and beginner-friendly explanation with formatting, bullet points, pinout details, "
            f"and practical circuit examples where applicable."
            f"{repair_instruction}"
        )

    cb(f"Generating answer with {provider.upper()}...")
    messages = _format_messages_for_llm(history, user_prompt)

    try:
        full_text = call_llm_stream(messages, stream_cb=stream_cb)
    except Exception as e:
        err_msg = str(e)
        if "API_KEY" in err_msg or "401" in err_msg or "not set" in err_msg:
            full_text = (
                f"⚠️ **LLM API Key Required**\n\n"
                f"To enable general-knowledge answers like ChatGPT and Claude:\n"
                f"1. Open the `.env` file in the project folder: `{config.ENV_PATH}`\n"
                f"2. Add your **Google Gemini**, **OpenAI**, or **Anthropic** API key:\n"
                f"   ```env\n"
                f"   GEMINI_API_KEY=your_gemini_key_here\n"
                f"   ```\n"
                f"   *(Get a free Gemini key in seconds at: https://aistudio.google.com/app/apikey)*\n\n"
                f"Alternatively, make sure **Ollama** is running locally for offline answering."
            )
        elif "Connection" in err_msg or "Failed to establish" in err_msg:
            full_text = (
                f"⚠️ **Network Connection Issue**\n\n"
                f"Could not connect to the {provider.upper()} AI service. Please check your internet connection "
                f"or start local Ollama (`ollama serve`).\n\nDetails: {err_msg[:180]}"
            )
        else:
            full_text = f"⚠️ **Assistant Error**: {err_msg}"

        if stream_cb:
            stream_cb(full_text)

    # 3. Retrieve relevant inline images
    images = []
    # If user provided or captured a photo
    if photo_path and os.path.isfile(photo_path):
        images.append({
            "path": photo_path,
            "caption": "Scanned Hardware Photo",
            "kind": "user_photo"
        })

    # If manual context has matched pages, retrieve manual diagrams
    if manual_id and matched_pages:
        manual_figs = visual_ref.get_manual_images_for_pages(manual_id, matched_pages, max_images=2)
        for mf in manual_figs:
            if not any(img["path"] == mf["path"] for img in images):
                images.append(mf)

    # If no manual images attached, check for general component reference visual
    if not any(img.get("kind") in ("illustration", "page") for img in images):
        comp_ref = visual_ref.get_component_reference_image(question)
        if comp_ref and not any(img["path"] == comp_ref["path"] for img in images):
            images.append(comp_ref)

    # 4. Check if user asked about a specific manual without selecting one
    manual_suggestion = ""
    if not manual_id:
        # Check if question seems to ask for manual/datasheet info
        manual_mentions = ["manual", "datasheet", "schematic", "page", "user guide"]
        all_manuals = db.list_manuals()
        has_manual_kw = any(mkw in q_lower for mkw in manual_mentions)
        matching_manual_name = next((m["name"] for m in all_manuals if m["name"].lower() in q_lower), None)

        if matching_manual_name:
            manual_suggestion = f"\n\n💡 *Note: I noticed you mentioned '{matching_manual_name}'. You can select it directly from the **📚 Manual** selector below for exact page-referenced schematics!*"
        elif has_manual_kw and all_manuals:
            manual_suggestion = "\n\n💡 *Tip: If you're referencing an uploaded device manual, select it using the **📚 Manual** button below to query its specific pages and circuit diagrams.*"

    if manual_suggestion:
        full_text += manual_suggestion

    # 5. Extract structured repair data: safety, tools, and steps
    safety_text = ""
    tools_list = []
    safety_match = re.search(r"(?:SAFETY FIRST|SAFETY PRECAUTIONS?|SAFETY WARNINGS?)[:\*\s]*\n*([^\n#]+(?:\n[^\n#]+)?)", full_text, re.IGNORECASE)
    if safety_match:
        safety_text = safety_match.group(1).strip()

    tools_match = re.search(r"(?:REQUIRED TOOLS|TOOLS & PARTS|REQUIRED PARTS)[:\*\s]*\n*([^\n#]+(?:\n[^\n#]+)?)", full_text, re.IGNORECASE)
    if tools_match:
        t_raw = tools_match.group(1).strip()
        tools_list = [t.strip(" *-\t") for t in re.split(r"[,;•\n]", t_raw) if len(t.strip(" *-\t")) > 2][:6]

    steps = []
    lines = full_text.splitlines()
    step_num = 1
    for line in lines:
        match = re.match(r"^\s*(?:Step\s*)?(\d+)[:\.)]\s*(.+)", line)
        if match:
            s_text = match.group(2).strip()
            # Try to associate page number if mentioned in line or from matched_pages
            p_match = re.search(r"[Pp]age\s*(\d+)", s_text)
            pno = int(p_match.group(1)) if p_match else (matched_pages[0] if matched_pages else None)
            steps.append({
                "number": step_num,
                "text": s_text,
                "page": pno
            })
            step_num += 1

    return {
        "title": question[:50],
        "summary": full_text,
        "answer": full_text,
        "steps": steps[:8] if len(steps) >= 2 else [],
        "images": images,
        "safety": safety_text,
        "tools": tools_list,
        "is_repair": is_repair,
        "found": True,
        "provider": provider
    }
