"""Optional offline voice input (faster-whisper + sounddevice). The app works fine without it."""
import config
from config import AppError

UNAVAILABLE = "Voice input is not available.\nPlease type your question."
_model = None


def is_available():
    try:
        import faster_whisper  # noqa: F401
        import sounddevice     # noqa: F401
        return True
    except Exception:
        return False


def listen(progress=None):
    """Record a few seconds from the microphone and return the transcribed text."""
    cb = progress or (lambda m: None)
    if not is_available():
        raise AppError(UNAVAILABLE)
    global _model
    try:
        import sounddevice as sd
        from faster_whisper import WhisperModel
        if _model is None:
            cb("Loading speech model (first use may download it)...")
            _model = WhisperModel("base", device="cpu", compute_type="int8")
        cb(f"Listening... speak now ({config.VOICE_SECONDS} seconds)")
        audio = sd.rec(int(config.VOICE_SECONDS * 16000), samplerate=16000, channels=1, dtype="float32")
        sd.wait()
        cb("Transcribing...")
        segments, _ = _model.transcribe(audio.flatten())
        text = " ".join(s.text.strip() for s in segments).strip()
    except Exception as e:
        raise AppError(f"Voice input failed:\n{e}\n\nPlease type your question.")
    if not text:
        raise AppError("Nothing was heard. Please try again or type your question.")
    return text
