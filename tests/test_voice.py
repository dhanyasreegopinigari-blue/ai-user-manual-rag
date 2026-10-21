"""Test voice recognition service components and models."""
import os
import sys
import unittest
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import config
from config import AppError
import services.voice as voice


class TestVoice(unittest.TestCase):
    def test_availability(self):
        self.assertTrue(voice.is_available(), "Voice service should be available")

    def test_audio_recorder_stream(self):
        import time
        rec = voice.AudioRecorder()
        levels = []
        rec.start(level_callback=lambda lvl: levels.append(lvl))
        time.sleep(0.4)
        audio = rec.stop()
        self.assertIsInstance(audio, np.ndarray)

    def test_faint_audio_handling(self):
        silent_audio = np.zeros(16000, dtype=np.float32)
        with self.assertRaises(AppError):
            voice.transcribe_audio(silent_audio)

    def test_model_loaded(self):
        model = voice.get_model()
        self.assertIsNotNone(model, "Whisper model should load successfully")


if __name__ == "__main__":
    unittest.main()
