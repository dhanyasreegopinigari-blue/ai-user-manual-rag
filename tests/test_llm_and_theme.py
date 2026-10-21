"""Tests for LLM API integration, General Knowledge Chat, and Black & Green Space Theme."""
import os
import sys
import unittest
from PyQt6.QtWidgets import QApplication

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import config
import services.llm as llm_service
from ui.controller import MainWindow
from ui.view import SpaceBackgroundWidget, ChatMessageWidget, DARK_STYLE, LIGHT_STYLE


class TestLLMAndTheme(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication(sys.argv)
        cls.win = MainWindow()

    def test_env_loader(self):
        # Verify load_env does not crash and reads config properly
        config.load_env()
        self.assertIsNotNone(config.LLM_PROVIDER)
        self.assertIsNotNone(config.GEMINI_MODEL)
        self.assertIsNotNone(config.OPENAI_MODEL)
        self.assertIsNotNone(config.ANTHROPIC_MODEL)

    def test_llm_provider_detection(self):
        prov = llm_service.get_active_provider()
        self.assertIn(prov, ["gemini", "openai", "claude", "ollama"])

    def test_format_messages(self):
        history = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"}
        ]
        msgs = llm_service._format_messages_for_llm(history, "What is an IC?")
        self.assertGreater(len(msgs), 2)
        self.assertEqual(msgs[0]["role"], "system")
        self.assertEqual(msgs[-1]["content"], "What is an IC?")

    def test_streaming_chat_widget(self):
        asst_w = ChatMessageWidget("assistant", "", parent_win=self.win)
        self.assertEqual(asst_w.content, "")
        
        # Test appending streaming tokens in real time
        asst_w.append_stream_token("An Integrated Circuit (IC)")
        self.assertEqual(asst_w.content, "An Integrated Circuit (IC)")
        asst_w.append_stream_token(" is a microelectronic semiconductor chip.")
        self.assertIn("semiconductor chip", asst_w.content)

        # Test finalize_stream
        data = {
            "title": "Integrated Circuit Overview",
            "summary": asst_w.content,
            "steps": [{"number": 1, "text": "Silicon wafer fabrication"}],
            "found": True
        }
        asst_w.finalize_stream(data)
        self.assertFalse(asst_w.steps_box.isHidden())

    def test_space_background_widget(self):
        bg = SpaceBackgroundWidget(self.win)
        self.assertTrue(bg.is_dark)
        self.assertGreater(len(bg._stars), 50)

        # Switch to light mode
        bg.set_theme(is_dark=False)
        self.assertFalse(bg.is_dark)

        # Switch back to dark
        bg.set_theme(is_dark=True)
        self.assertTrue(bg.is_dark)

    def test_theme_toggle_applies_styles(self):
        initial = self.win.is_dark_theme
        self.win.toggle_theme()
        self.assertEqual(self.win.is_dark_theme, not initial)
        self.win.toggle_theme()
        self.assertEqual(self.win.is_dark_theme, initial)

    def test_hybrid_answer_general_question(self):
        tokens = []
        def mock_stream(msgs, stream_cb=None):
            text = "An Integrated Circuit (IC) is a miniature electronic circuit composed of semiconductor transistors."
            if stream_cb:
                for word in text.split():
                    stream_cb(word + " ")
            return text

        orig_call = llm_service.call_llm_stream
        llm_service.call_llm_stream = mock_stream
        try:
            ans = llm_service.answer_hybrid(
                manual_id=None,
                question="What is an Integrated Circuit (IC)?",
                history=[],
                progress_cb=None,
                stream_cb=tokens.append
            )
            self.assertIsNotNone(ans)
            self.assertTrue(ans["found"])
            self.assertIn("summary", ans)
            self.assertGreater(len(tokens), 0)
        finally:
            llm_service.call_llm_stream = orig_call


if __name__ == "__main__":
    unittest.main()
