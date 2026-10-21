"""High-accuracy voice recognition service (faster-whisper + sounddevice + SpeechRecognition fallback)."""
import os
import sys
import time
import types
import numpy as np

import config
from config import AppError

# Windows AppLocker / WDAC policy workaround:
# faster-whisper imports av.audio.decode_audio on package load. If PyAV C-extensions are
# blocked by Windows security policy, inject a lightweight stub so faster-whisper can load.
# WhisperModel does not use PyAV when transcribing in-memory float32 numpy arrays.
if "av" not in sys.modules:
    try:
        import av  # noqa: F401
    except Exception:
        dummy_av = types.ModuleType("av")
        dummy_av.audio = types.ModuleType("av.audio")
        dummy_av.audio.resampler = types.ModuleType("av.audio.resampler")
        sys.modules["av"] = dummy_av
        sys.modules["av.audio"] = dummy_av.audio
        sys.modules["av.audio.resampler"] = dummy_av.audio.resampler

UNAVAILABLE = (
    "Voice input is not available.\n"
    "Please install the voice requirements:\n"
    "pip install faster-whisper sounddevice SpeechRecognition"
)

_model = None


def is_available():
    """Check if microphone recording and at least one speech-to-text engine are available."""
    try:
        import sounddevice  # noqa: F401
    except Exception:
        return False

    has_whisper = False
    try:
        import faster_whisper  # noqa: F401
        has_whisper = True
    except Exception:
        pass

    has_sr = False
    try:
        import speech_recognition  # noqa: F401
        has_sr = True
    except Exception:
        pass

    return has_whisper or has_sr


def get_model(progress=None):
    """Lazy load and cache the faster-whisper model."""
    global _model
    if _model is not None:
        return _model

    cb = progress or (lambda m: None)
    try:
        from faster_whisper import WhisperModel
        model_name = getattr(config, "VOICE_MODEL", "base")
        cb(f"Loading speech model '{model_name}'...")
        _model = WhisperModel(model_name, device="cpu", compute_type="int8")
        return _model
    except Exception as e:
        print(f"[VOICE] Error loading Whisper model: {e}")
        return None


class AudioRecorder:
    """Streaming microphone recorder with RMS audio levels and Voice Activity Detection (VAD)."""
    def __init__(self, samplerate=16000, speech_threshold=0.015, silence_duration=None):
        self.samplerate = samplerate
        self.speech_threshold = speech_threshold
        self.silence_duration = silence_duration or getattr(config, "VOICE_SILENCE_TIMEOUT", 1.8)
        self.buffer = []
        self.speech_detected = False
        self.silence_seconds = 0.0
        self.current_level = 0.0
        self.stream = None
        self._stopped = False
        self._level_cb = None

    def _audio_callback(self, indata, frames, time_info, status):
        if self._stopped:
            return
        chunk = indata.flatten().copy()
        self.buffer.append(chunk)

        # RMS calculation for UI volume meter
        rms = float(np.sqrt(np.mean(chunk ** 2)))
        self.current_level = rms
        if self._level_cb:
            # Scale to 0-100 range for QProgressBar
            meter_val = int(min(100, max(0, rms * 350)))
            self._level_cb(meter_val)

        chunk_duration = len(chunk) / self.samplerate
        if rms >= self.speech_threshold:
            self.speech_detected = True
            self.silence_seconds = 0.0
        elif self.speech_detected:
            self.silence_seconds += chunk_duration

    def start(self, level_callback=None):
        import sounddevice as sd
        self._level_cb = level_callback
        self.buffer.clear()
        self.speech_detected = False
        self.silence_seconds = 0.0
        self.current_level = 0.0
        self._stopped = False
        self.stream = sd.InputStream(
            samplerate=self.samplerate,
            channels=1,
            dtype="float32",
            callback=self._audio_callback
        )
        self.stream.start()

    def should_auto_stop(self):
        return self.speech_detected and (self.silence_seconds >= self.silence_duration)

    def stop(self):
        self._stopped = True
        if self.stream is not None:
            try:
                self.stream.stop()
                self.stream.close()
            except Exception:
                pass
            self.stream = None
        if not self.buffer:
            return np.zeros(0, dtype=np.float32)
        return np.concatenate(self.buffer).astype(np.float32)


def transcribe_audio(audio, progress=None):
    """Normalize and transcribe audio with Whisper (or fallback to SpeechRecognition)."""
    cb = progress or (lambda m: None)
    if audio is None or len(audio) == 0:
        raise AppError("No audio was recorded. Please check your microphone.")

    audio = audio.flatten().astype(np.float32)
    # DC offset removal
    audio = audio - np.mean(audio)
    peak = float(np.max(np.abs(audio)))

    if peak < 0.005:
        raise AppError("Microphone signal was too faint or silent.\nPlease check your mic volume and try again.")

    # Peak normalization to 0.95 to maximize Whisper acoustic accuracy
    audio = (audio / peak) * 0.95

    text = ""
    whisper_err = None

    # Try faster-whisper first
    model = get_model(cb)
    if model is not None:
        try:
            cb("Transcribing with Whisper AI...")
            lang = getattr(config, "VOICE_LANGUAGE", "en")
            segments, info = model.transcribe(
                audio,
                vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=400),
                language=lang,
                temperature=0.0,
                condition_on_previous_text=False
            )
            text = " ".join(s.text.strip() for s in segments).strip()
        except Exception as e:
            whisper_err = e
            print(f"[VOICE] Whisper transcription failed: {e}")

    # Fallback to SpeechRecognition (Google STT) if Whisper was unavailable or failed
    if not text:
        try:
            import speech_recognition as sr
            cb("Transcribing via speech service...")
            pcm16 = (np.clip(audio, -1.0, 1.0) * 32767).astype(np.int16).tobytes()
            audio_data = sr.AudioData(pcm16, 16000, 2)
            r = sr.Recognizer()
            text = r.recognize_google(audio_data)
        except Exception as sr_err:
            if whisper_err:
                raise AppError(f"Voice recognition failed:\n{whisper_err}\n\nPlease type your question.")
            raise AppError(f"Voice recognition failed:\n{sr_err}\n\nPlease type your question.")

    text = text.strip()
    if not text:
        raise AppError("Nothing was heard or speech could not be recognized. Please try again or type your question.")

    # Formatting cleanup: Capitalize first letter
    if len(text) > 1:
        text = text[0].upper() + text[1:]
    return text


def listen(progress=None):
    """Synchronous recording helper with auto-stop on silence."""
    cb = progress or (lambda m: None)
    if not is_available():
        raise AppError(UNAVAILABLE)

    max_sec = getattr(config, "VOICE_SECONDS", 15)
    cb(f"Listening... speak now (up to {max_sec}s)")
    recorder = AudioRecorder(samplerate=16000)
    recorder.start()

    start_time = time.time()
    try:
        while time.time() - start_time < max_sec:
            time.sleep(0.08)
            if recorder.should_auto_stop():
                break
    finally:
        audio = recorder.stop()

    cb("Transcribing...")
    return transcribe_audio(audio, progress=cb)
