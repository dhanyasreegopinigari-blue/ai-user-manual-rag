"""High-quality offline Text-To-Speech (TTS) service using pyttsx3."""
import re
import threading
from typing import Callable, Optional

try:
    import pythoncom
except ImportError:
    pythoncom = None


def clean_text_for_speech(text: str) -> str:
    """Strip HTML, markdown formatting, code fences, and bracketed citations for natural speech."""
    if not text:
        return ""
    # Remove HTML tags
    clean = re.sub(r"<[^>]+>", " ", text)
    # Remove code blocks
    clean = re.sub(r"```.*?```", " Code snippet omitted. ", clean, flags=re.DOTALL)
    # Turn [Manual Name, p. 12] into "Manual Name, page 12"
    clean = re.sub(r"\[([^,\]]+),\s*(?:p\.|page)\s*(\d+)\]", r"\1, page \2", clean, flags=re.IGNORECASE)
    # Remove standalone [p. 12]
    clean = re.sub(r"\[(?:p\.|page)\s*(\d+)\]", r"page \1", clean, flags=re.IGNORECASE)
    # Remove markdown formatting characters
    clean = re.sub(r"[*_#`~>|]", " ", clean)
    # Collapse multiple spaces and newlines
    clean = re.sub(r"\s+", " ", clean).strip()
    return clean


class TTSService:
    """Thread-safe background Text-To-Speech engine using pyttsx3."""
    def __init__(self):
        self._lock = threading.Lock()
        self._thread: Optional[threading.Thread] = None
        self._is_speaking = False
        self._current_engine = None
        self._active_id: Optional[str] = None

    def speak(self, text: str, speech_id: Optional[str] = None, on_start: Optional[Callable] = None, on_finish: Optional[Callable] = None):
        """Speak the given text asynchronously in a background thread."""
        self.stop()

        clean_text = clean_text_for_speech(text)
        if not clean_text:
            if on_finish:
                try:
                    on_finish()
                except Exception:
                    pass
            return

        def _worker():
            try:
                if pythoncom:
                    pythoncom.CoInitialize()

                import pyttsx3
                engine = pyttsx3.init()
                with self._lock:
                    self._current_engine = engine
                    self._is_speaking = True
                    self._active_id = speech_id

                if on_start:
                    try:
                        on_start()
                    except Exception as e:
                        print(f"[TTS] on_start callback error: {e}")

                try:
                    engine.setProperty("rate", 175)
                except Exception:
                    pass

                engine.say(clean_text)
                engine.runAndWait()
            except Exception as e:
                print(f"[TTS] Playback error: {e}")
            finally:
                with self._lock:
                    self._is_speaking = False
                    self._current_engine = None
                    self._active_id = None

                if on_finish:
                    try:
                        on_finish()
                    except Exception as e:
                        print(f"[TTS] on_finish callback error: {e}")

        self._thread = threading.Thread(target=_worker, daemon=True)
        self._thread.start()

    def stop(self):
        """Immediately stop any current speech playback."""
        with self._lock:
            if self._current_engine:
                try:
                    self._current_engine.stop()
                except Exception:
                    pass
            self._is_speaking = False
            self._active_id = None

    def is_speaking(self, speech_id: Optional[str] = None) -> bool:
        """Check if TTS is currently active (optionally for a specific speech ID)."""
        with self._lock:
            if speech_id is not None:
                return self._is_speaking and self._active_id == speech_id
            return self._is_speaking

    def get_active_id(self) -> Optional[str]:
        with self._lock:
            return self._active_id


# Global singleton instance
tts = TTSService()
