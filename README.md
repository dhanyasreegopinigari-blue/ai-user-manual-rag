# AI User Manual (offline prototype)

Upload a photo or video of a hardware product → a local vision model identifies it → the matching
PDF manual is found → ask a question (click, type or speak) → you get **simple step-by-step
instructions with the real images/pages from the manual**. Everything runs locally through Ollama.

## Requirements
- Python 3.10+
- [Ollama](https://ollama.com) running locally
- Models:
```text
ollama pull nomic-embed-text
ollama pull qwen3-vl:2b
ollama pull qwen3:4b
```

## Installation
```text
python -m venv venv
venv\Scripts\activate          (Linux/macOS: source venv/bin/activate)
pip install -r requirements.txt
```
Optional offline voice input: `pip install -r requirements-voice.txt`
(faster-whisper downloads its small "base" speech model the first time you use the microphone).

## Run
```text
python main.py
```
Check your setup first with `python test_setup.py` (uses a temporary database, does not touch your library).

## Usage
1. Start Ollama.
2. Start the application.
3. **Manual Library → + Add Manual**: choose a PDF, enter name / manufacturer / **model** (the model is what
   hardware photos are matched against). Wait for indexing.
4. On Home, **Upload Photo** (or Video).
5. Check the result. "✓ Manual Found" appears only for a real model match; otherwise pick a manual yourself.
6. Pick a suggested question, type one, or press 🎤 Speak.
7. Step through the answer with Previous / Next. **Done** returns to the questions – no restart needed.

## How it works
| Part | File |
|---|---|
| Settings, model names, paths | `config.py` (also editable in the Settings dialog → `settings.json`) |
| SQLite tables (manuals, manual_pages, manual_images, manual_chunks) | `database.py` |
| PDF import, chunking, hardware→manual matching | `manual.py` |
| Ollama client, FAISS, suggested questions, grounded answers | `rag.py` |
| Photo/video identification (OpenCV frames) | `vision.py` |
| Optional speech-to-text | `voice.py` |
| GUI (PyQt6, background threads) | `ui.py` |

- One FAISS index per manual (`data/faiss/manual_<id>.index`). The FAISS vector id **is** the SQLite chunk id
  (`IndexIDMap`), which is the vector→chunk mapping. Deleting a manual removes its rows, images and index.
- Chunks are 250–800 words and carry `[Page N]` markers so each step can cite a page.
- The LLM only sees the top 4 retrieved chunks and is told to answer **only** from them; if the manual lacks
  the answer, the app says so. Malformed JSON from the model falls back to plain-text steps.
- Videos: ~1 candidate frame per 1.5 s, the sharpest 6 frames are analysed, and the results are voted per field.

## Images
Only images from the real manual are shown. For each step the largest illustration embedded on that
page is used. If the page has no embedded illustration, a **snapshot of the manual page itself** is shown
(captioned "Manual page N"). Nothing is ever generated. If neither exists: "No illustration available for this step."

## Limitations / graceful fallbacks
- Scanned (image-only) PDFs have no text and are rejected with a message (no OCR in this prototype).
- Repeated images (logos on many pages) and tiny icons are skipped.
- Semantic "similar manual" suggestions are labelled *not verified*; they never count as a found manual.
- Small local models can mis-read labels or occasionally cite a wrong page; always check the shown manual page.
- Voice is optional; without the voice packages the app shows "Voice input is not available."

## Common errors
| Message | Fix |
|---|---|
| Ollama is not running | Start Ollama (`ollama serve`) and check the URL in Settings |
| Required Ollama model was not found | `ollama pull <model>` or change the model name in Settings |
| No matching manual was found | Add the PDF in Manual Library; make sure its *Model* field matches the product |
| No readable text in PDF | The PDF is scanned; use a text-based PDF |
| Slow first answer | Ollama is loading the model into memory; later answers are faster |
