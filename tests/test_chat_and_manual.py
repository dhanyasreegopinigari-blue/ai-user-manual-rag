"""Test suite for Continuous Chat, Sidebar History, Exports, and User Manual Viewer."""
import os
import sys
import unittest
from PyQt6.QtWidgets import QApplication

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import database as db
import services.export as export_mod
from ui.controller import MainWindow
from ui.view import UserManualDialog, ChatMessageWidget


class TestChatAndManual(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        db.init_db()
        cls.app = QApplication.instance() or QApplication(sys.argv)
        cls.win = MainWindow()

    def test_database_conversations(self):
        # 1. Create conversation
        cid = db.create_conversation(1, "Test Q&A")
        self.assertIsNotNone(cid)

        # 2. Add user message and assistant message
        mid1 = db.add_chat_message(cid, "user", "How do I clean the filter?")
        self.assertIsNotNone(mid1)
        data = {
            "title": "Filter Cleaning",
            "summary": "Remove and wash.",
            "steps": [{"number": 1, "text": "Unplug unit", "page": 9}]
        }
        mid2 = db.add_chat_message(cid, "assistant", "Remove and wash.", data=data)
        self.assertIsNotNone(mid2)

        # 3. Retrieve messages
        msgs = db.get_chat_messages(cid)
        self.assertEqual(len(msgs), 2)
        self.assertEqual(msgs[0]["role"], "user")
        self.assertEqual(msgs[1]["role"], "assistant")
        self.assertEqual(msgs[1]["data"]["title"], "Filter Cleaning")

        # 4. List conversations
        convs = db.list_conversations()
        self.assertTrue(any(c["id"] == cid for c in convs))

        # 5. Delete conversation
        db.delete_conversation(cid)
        msgs_after = db.get_chat_messages(cid)
        self.assertEqual(len(msgs_after), 0)

    def test_exports(self):
        data = {
            "title": "Jumper Settings",
            "summary": "Configure J1 and J2.",
            "steps": [
                {"number": 1, "text": "Locate J1", "page": 14},
                {"number": 2, "text": "Set pins 1-2 for 5V", "page": 15}
            ]
        }
        # Plain text
        txt = export_mod.format_answer_txt(data, "How to set jumpers?")
        self.assertIn("JUMPER SETTINGS", txt)
        self.assertIn("Step 1: Locate J1", txt)

        # Markdown
        md = export_mod.format_answer_md(data, "How to set jumpers?")
        self.assertIn("# Jumper Settings", md)
        self.assertIn("1. Locate J1", md)

        # HTML / PDF
        html = export_mod.format_answer_html(data, "How to set jumpers?", manual_name="Test Manual")
        self.assertIn("Jumper Settings", html)
        pdf_out = os.path.join(os.path.dirname(__file__), "test_temp_out.pdf")
        export_mod.save_as_pdf(html, pdf_out)
        self.assertTrue(os.path.exists(pdf_out))
        self.assertGreater(os.path.getsize(pdf_out), 1000)
        os.remove(pdf_out)

    def test_user_manual_viewer(self):
        manuals = db.list_manuals()
        if manuals:
            mid = manuals[0]["id"]
            dlg = UserManualDialog(self.win, manual_id=mid, initial_page=1)
            self.assertGreater(dlg.total_pages, 0)
            self.assertEqual(dlg.current_page, 1)
            dlg.next_page()
            self.assertEqual(dlg.current_page, 2)
            dlg.prev_page()
            self.assertEqual(dlg.current_page, 1)
            target = min(5, dlg.total_pages)
            dlg.jump_to_page(target)
            self.assertEqual(dlg.current_page, target)
            dlg.close()

    def test_chat_widgets(self):
        user_w = ChatMessageWidget("user", "Hello manual!", parent_win=self.win)
        self.assertIsNotNone(user_w)
        data = {
            "title": "Welcome Answer",
            "steps": [{"number": 1, "text": "Read the manual", "page": 1}]
        }
        asst_w = ChatMessageWidget("assistant", "Read the manual", data=data, parent_win=self.win)
        self.assertIsNotNone(asst_w)


if __name__ == "__main__":
    unittest.main()
