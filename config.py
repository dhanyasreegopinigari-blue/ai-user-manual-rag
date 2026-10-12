"""Central configuration. Change model names / URL here (or in the Settings dialog).

Other modules always read values as `config.NAME` (never `from config import NAME`)
so that changes made in the Settings dialog take effect immediately.
"""
import json
import os


class AppError(Exception):
    """An error whose message is user-friendly and can be shown in the GUI as-is."""


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
MANUALS_DIR = os.path.join(DATA_DIR, "manuals")   # copies of imported PDFs
IMAGES_DIR = os.path.join(DATA_DIR, "images")     # extracted manual images
FAISS_DIR = os.path.join(DATA_DIR, "faiss")       # one FAISS index per manual
DB_PATH = os.path.join(BASE_DIR, "app.db")
SETTINGS_PATH = os.path.join(BASE_DIR, "settings.json")

# ---- Ollama -----------------------------------------------------------------
OLLAMA_URL = "http://localhost:11434"
VISION_MODEL = "qwen3-vl:2b-instruct"            # photo / video analysis
LLM_MODEL = "qwen3:4b"                  # questions + answers
EMBED_MODEL = "nomic-embed-text:latest" # embeddings for FAISS
REQUEST_TIMEOUT = 600                   # seconds (local models can be slow)

# ---- Tuning -----------------------------------------------------------------
ANSWER_MAX_TOKENS = 1024 # max tokens for LLM answers to prevent JSON truncation
CHUNK_MIN_WORDS = 250    # keep adding pages to a chunk until it has this many words
CHUNK_MAX_WORDS = 800    # never let a chunk grow beyond this
CHUNK_OVERLAP_WORDS = 60 # word overlap between consecutive chunks
FULL_TOP_K = 14          # chunks read for 'full setup / end-to-end' questions
FULL_BATCH = 3           # chunks sent to the LLM per call in full mode
MAX_STEPS = 40           # cap on steps in a full guide
TOP_K = 4                # chunks sent to the LLM per question
VIDEO_MAX_FRAMES = 6     # frames actually sent to the vision model
VISION_MAX_SIDE = 1024   # max resolution dimension for hardware vision input
VOICE_SECONDS = 6        # microphone recording length

_SETTING_KEYS = ("OLLAMA_URL", "VISION_MODEL", "LLM_MODEL", "EMBED_MODEL")


def ensure_dirs():
    for d in (DATA_DIR, MANUALS_DIR, IMAGES_DIR, FAISS_DIR):
        os.makedirs(d, exist_ok=True)


def load_settings():
    """Override defaults with values saved by the Settings dialog."""
    try:
        with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
            saved = json.load(f)
        for k in _SETTING_KEYS:
            if saved.get(k):
                globals()[k] = str(saved[k]).strip()
    except (OSError, ValueError):
        pass


def save_settings(url, vision, llm, embed):
    globals().update(OLLAMA_URL=url.strip(), VISION_MODEL=vision.strip(),
                     LLM_MODEL=llm.strip(), EMBED_MODEL=embed.strip())
    with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
        json.dump({k: globals()[k] for k in _SETTING_KEYS}, f, indent=2)


load_settings()
