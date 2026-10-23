"""Comprehensive automated test for Step 4: Manuals Page Redesign & Button Sweep."""
import os
import sys
import shutil
import tempfile
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication

import config
import database as db
import services.manual as manual_service
import services.rag as rag
from ui.controller import MainWindow
from ui.view import InteractiveManualViewer, HelpDrawerDialog, ManualDropZone, ManualItemWidget

try:
    import pymupdf as fitz
except ImportError:
    import fitz

app = QApplication.instance() or QApplication([])


class TestManualsPageRedesign(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp_dir = tempfile.mkdtemp(prefix="test_manuals_")
        cls.orig_db = config.DB_PATH
        cls.orig_manuals = config.MANUALS_DIR
        cls.orig_images = config.IMAGES_DIR
        cls.orig_faiss = config.FAISS_DIR

        config.DB_PATH = os.path.join(cls.tmp_dir, "test.db")
        config.MANUALS_DIR = os.path.join(cls.tmp_dir, "manuals")
        config.IMAGES_DIR = os.path.join(cls.tmp_dir, "images")
        config.FAISS_DIR = os.path.join(cls.tmp_dir, "faiss")
        os.makedirs(config.MANUALS_DIR, exist_ok=True)
        os.makedirs(config.IMAGES_DIR, exist_ok=True)
        os.makedirs(config.FAISS_DIR, exist_ok=True)

        db.init_db()

        # Create dummy PDF
        cls.test_pdf = os.path.join(cls.tmp_dir, "microcontroller_guide.pdf")
        doc = fitz.open()
        p1 = doc.new_page()
        p1.insert_text(fitz.Point(50, 72), "Microcontroller Architecture Guide\nIntroduction to ATmega328P and pinouts.")
        p2 = doc.new_page()
        p2.insert_text(fitz.Point(50, 72), "Power Regulations and LM7805\nAlways use decoupling capacitors on input and output.")
        doc.save(cls.test_pdf)
        doc.close()

        # Import manual
        cls.mid = manual_service.import_pdf(
            cls.test_pdf,
            name="ATmega328P Guide",
            tags="Microcontrollers, Guides"
        )

        cls.win = MainWindow()

    @classmethod
    def tearDownClass(cls):
        cls.win.close()
        config.DB_PATH = cls.orig_db
        config.MANUALS_DIR = cls.orig_manuals
        config.IMAGES_DIR = cls.orig_images
        config.FAISS_DIR = cls.orig_faiss
        shutil.rmtree(cls.tmp_dir, ignore_errors=True)

    def test_01_navigation_tab_and_four_pages(self):
        """Strictly 4 user pages: Dashboard(0), AI Assistant(1), Component Library(2), Manuals(3)."""
        nav = self.win.view.top_bar
        tab_texts = [b.text() for b in nav.nav_buttons]
        self.assertEqual(tab_texts, ["Dashboard", "AI Assistant", "Component Library", "Manuals"])
        self.assertEqual(len(nav.nav_buttons), 4)

        # Navigating to index 3 shows manuals page
        self.win.navigate_to(3)
        self.assertEqual(self.win.view.stack.currentIndex(), 3)

    def test_02_help_drawer_dialog(self):
        """Help icon in top bar opens HelpDrawerDialog and does not consume a page."""
        nav = self.win.view.top_bar
        self.assertTrue(hasattr(nav, "help_btn"))
        drawer = HelpDrawerDialog(self.win)
        self.assertIsNotNone(drawer.search_input)
        self.assertIsNotNone(drawer.tour_btn)
        # Search filter in drawer
        drawer.search_input.setText("chat")
        drawer._filter_topics()
        drawer.close()

    def test_03_summary_stats(self):
        """Summary stats calculation on the manuals hub."""
        stats = db.get_manual_summary_stats()
        self.assertGreaterEqual(stats["total_manuals"], 1)
        self.assertGreaterEqual(stats["total_pages"], 2)
        self.assertTrue(hasattr(self.win.view, "stat_total_val"))
        self.assertIn(str(stats["total_manuals"]), self.win.view.stat_total_val.text())

    def test_04_chat_enabled_toggle_and_rag_filtering(self):
        """Toggle Include in AI search persists in DB and filters RAG search."""
        m = db.get_manual(self.mid)
        self.assertEqual(m["enabled_for_chat"], 1)

        # Toggle to off (0)
        db.update_manual_chat_enabled(self.mid, False)
        m = db.get_manual(self.mid)
        self.assertEqual(m["enabled_for_chat"], 0)

        # Verify rag.search with manual_id=None filters out disabled manuals
        results = rag.search(None, "ATmega328P")
        matching = [r for r in results if r["manual_id"] == self.mid]
        self.assertEqual(len(matching), 0)

        # Toggle back on (1)
        db.update_manual_chat_enabled(self.mid, True)
        m = db.get_manual(self.mid)
        self.assertEqual(m["enabled_for_chat"], 1)

    def test_05_manual_bookmarks(self):
        """Add, retrieve, and delete manual bookmarks."""
        bid = db.add_manual_bookmark(self.mid, 2, "Important decoupling capacitor rule")
        bms = db.get_manual_bookmarks(self.mid)
        self.assertTrue(any(b["id"] == bid for b in bms))

        db.delete_manual_bookmark(bid)
        bms_after = db.get_manual_bookmarks(self.mid)
        self.assertFalse(any(b["id"] == bid for b in bms_after))

    def test_06_interactive_viewer_operations(self):
        """Test interactive PDF viewer controls: page nav, zoom, dark reading mode, search."""
        viewer = self.win.view.viewer_widget
        self.win.load_manual_in_viewer(self.mid, page=1)

        self.assertEqual(viewer.current_page, 1)
        self.assertEqual(viewer.total_pages, 2)
        self.assertIsNotNone(viewer.canvas_lbl.pixmap())

        # Page navigation
        viewer.next_page()
        self.assertEqual(viewer.current_page, 2)
        viewer.prev_page()
        self.assertEqual(viewer.current_page, 1)
        viewer.jump_to_page(2)
        self.assertEqual(viewer.current_page, 2)

        # Zoom controls
        z0 = viewer.zoom
        viewer.zoom_in()
        self.assertGreater(viewer.zoom, z0)
        viewer.zoom_out()
        self.assertEqual(viewer.zoom, z0)

        # Dark Reading Mode
        self.assertFalse(viewer.dark_mode)
        viewer.toggle_dark_reading_mode()
        self.assertTrue(viewer.dark_mode)
        viewer.toggle_dark_reading_mode()
        self.assertFalse(viewer.dark_mode)

        # Rotation
        self.assertEqual(viewer.rotation, 0)
        viewer.rotate_clockwise()
        self.assertEqual(viewer.rotation, 90)
        viewer.rotate_clockwise()
        viewer.rotate_clockwise()
        viewer.rotate_clockwise()
        self.assertEqual(viewer.rotation, 0)

    def test_07_ask_about_manual_and_page_context(self):
        """Ask about manual and Ask about this page fills chat input and navigates to AI Assistant."""
        viewer = self.win.view.viewer_widget
        self.win.load_manual_in_viewer(self.mid, page=2)

        # Test ask about manual
        viewer.ask_manual_btn.click()
        self.assertEqual(self.win.view.stack.currentIndex(), 1)
        self.assertIn("ATmega328P Guide", self.win.view.chat_input.toPlainText())

        # Test ask about this page
        self.win.load_manual_in_viewer(self.mid, page=2)
        viewer.ask_page_btn.click()
        self.assertEqual(self.win.view.stack.currentIndex(), 1)
        prompt_text = self.win.view.chat_input.toPlainText()
        self.assertIn("p.2", prompt_text)

    def test_08_reindexing_and_cascade_delete(self):
        """Re-indexing regenerates chunks, and deleting cascades cleanup."""
        # Reindex
        stats = manual_service.reindex_manual(self.mid)
        self.assertGreaterEqual(stats["chunks"], 1)

        # Create temporary second manual to delete
        doc = fitz.open()
        p = doc.new_page()
        p.insert_text(fitz.Point(50, 70), "Temporary manual for cascade test")
        tpath = os.path.join(self.tmp_dir, "temp_del.pdf")
        doc.save(tpath)
        doc.close()
        tmid = manual_service.import_pdf(tpath, name="Temp Delete Manual")

        self.assertIsNotNone(db.get_manual(tmid))
        self.assertTrue(os.path.isfile(rag.index_path(tmid)))

        # Delete with cascade
        manual_service.delete_manual(tmid)
        self.assertIsNone(db.get_manual(tmid))
        self.assertEqual(len(db.get_all_chunks(tmid)), 0)
        self.assertFalse(os.path.isfile(rag.index_path(tmid)))


if __name__ == "__main__":
    unittest.main()
