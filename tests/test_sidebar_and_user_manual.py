"""Comprehensive unit tests for Global Left Sidebar Navigation and Redesigned User Manual Page."""
import os
import sys
import unittest
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt, QSettings

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import database as db
import config
from ui.controller import MainWindow
from ui.view import GlobalSidebar, SlimHeader


class TestSidebarAndUserManual(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        db.init_db()
        cls.app = QApplication.instance() or QApplication(sys.argv)
        cls.win = MainWindow()

    def test_01_global_left_sidebar_structure(self):
        """Verify left sidebar presence, logo, items, and bottom utilities."""
        self.assertTrue(hasattr(self.win.view, "sidebar"))
        sidebar = self.win.view.sidebar
        self.assertIsInstance(sidebar, GlobalSidebar)

        # Check logo and brand
        self.assertEqual(sidebar.app_title_lbl.text(), "ElectroLearn AI")
        self.assertIsNotNone(sidebar.brand_icon)
        self.assertIsNotNone(sidebar.collapse_btn)

        # Check the 4 navigation items: Dashboard, AI Assistant, User Manual, Help (Component Library removed)
        btn_labels = [b._orig_text for b in sidebar.all_buttons]
        self.assertEqual(btn_labels, ["Dashboard", "AI Assistant", "User Manual", "Help"])

        # Check bottom utilities
        self.assertTrue(hasattr(sidebar, "ollama_pill"))
        self.assertTrue(hasattr(sidebar, "theme_btn"))
        self.assertTrue(hasattr(sidebar, "settings_btn"))

    def test_02_sidebar_collapsible_and_persistence(self):
        """Test sidebar collapse/expand toggle, tooltips, and QSettings persistence."""
        sidebar = self.win.view.sidebar
        settings = QSettings("ElectroLearn", "ElectroLearnAI")

        # Force expand
        sidebar.set_collapsed(False, save=True)
        self.assertFalse(sidebar.is_collapsed)
        self.assertEqual(sidebar.width(), 230)
        self.assertFalse(sidebar.app_title_lbl.isHidden())
        self.assertEqual(sidebar.btn_dash.text(), "Dashboard")
        self.assertEqual(settings.value("sidebar_collapsed", type=bool), False)

        # Force collapse
        sidebar.set_collapsed(True, save=True)
        self.assertTrue(sidebar.is_collapsed)
        self.assertEqual(sidebar.width(), 68)
        self.assertTrue(sidebar.app_title_lbl.isHidden())
        # Text should be empty, tooltip should have the label
        self.assertEqual(sidebar.btn_dash.text(), "")
        self.assertEqual(sidebar.btn_dash.toolTip(), "Dashboard")
        self.assertEqual(settings.value("sidebar_collapsed", type=bool), True)

        # Toggle back
        sidebar.toggle_collapse()
        self.assertFalse(sidebar.is_collapsed)
        self.assertEqual(sidebar.width(), 230)
        self.assertEqual(sidebar.btn_dash.text(), "Dashboard")

    def test_03_active_page_highlighting_and_slim_header(self):
        """Test active page highlighting and slim header breadcrumb updates."""
        sidebar = self.win.view.sidebar
        slim_header = self.win.view.slim_header
        self.assertIsInstance(slim_header, SlimHeader)

        for idx, expected_title in [
            (0, "Dashboard"),
            (1, "AI Assistant"),
            (2, "User Manual")
        ]:
            self.win.navigate_to(idx)
            self.assertEqual(self.win.stack.currentIndex(), idx)
            # Active button kind property
            active_btn = sidebar.all_buttons[idx]
            self.assertEqual(active_btn.property("kind"), "sidebarNavActive")
            # Slim header breadcrumb
            self.assertEqual(slim_header.title_lbl.text(), expected_title)

    def test_04_user_manual_page_structure_and_toc(self):
        """Verify redesigned User Manual documentation view with 9 sections and Table of Contents."""
        self.win.navigate_to(2)
        self.assertEqual(self.win.stack.currentIndex(), 2)

        self.assertTrue(hasattr(self.win.view, "doc_view"))
        self.assertTrue(hasattr(self.win.view, "doc_search_input"))
        self.assertTrue(hasattr(self.win.view, "doc_sections"))

        # Verify 9 sections
        self.assertEqual(len(self.win.view.doc_sections), 9)
        self.assertEqual(len(self.win.view.toc_buttons), 9)

        # Test scrolling to section
        self.win.view._scroll_to_doc_section(1)
        self.assertEqual(self.win.view.toc_buttons[1].property("kind"), "tocItemActive")
        self.assertEqual(self.win.view.toc_buttons[0].property("kind"), "tocItem")

        # Test scroll spy
        self.win.view._on_doc_scroll(0)
        self.assertEqual(self.win.view.toc_buttons[0].property("kind"), "tocItemActive")

    def test_05_user_manual_search_filtering(self):
        """Test search box live-filtering topics and TOC buttons in documentation."""
        self.win.navigate_to(2)
        doc_search = self.win.view.doc_search_input

        # Search for specific term
        doc_search.setText("whisper")
        # Section 6 (Voice & Live Camera) should be visible
        sec6_widget, sec6_btn = self.win.view.doc_sections[5]
        self.assertFalse(sec6_widget.isHidden())
        self.assertFalse(sec6_btn.isHidden())

        # Clear search - all should be visible
        doc_search.setText("")
        for sec_widget, toc_btn in self.win.view.doc_sections:
            self.assertFalse(sec_widget.isHidden())
            self.assertFalse(toc_btn.isHidden())

    def test_06_manual_segment_switcher_and_hub_integration(self):
        """Test seamless switching between User Manual & Documentation and Hardware PDF Hub."""
        self.win.navigate_to(2)

        # By default loaded manuals hub is visible
        self.assertEqual(self.win.view.manuals_main_stack.currentIndex(), 1)
        self.assertEqual(self.win.view.seg_hw_btn.property("kind"), "chipActive")

        # Switch to App User Guide
        self.win.view.switch_to_user_manual()
        self.assertEqual(self.win.view.manuals_main_stack.currentIndex(), 0)
        self.assertEqual(self.win.view.seg_doc_btn.property("kind"), "chipActive")

        # Switch back to Loaded Manuals Hub
        self.win.view.switch_to_hw_manuals()
        self.assertEqual(self.win.view.manuals_main_stack.currentIndex(), 1)
        self.assertEqual(self.win.view.seg_hw_btn.property("kind"), "chipActive")

    def test_07_mobile_responsive_behavior(self):
        """Test that clicking a nav button on narrow screens (<850px) auto-closes the sidebar."""
        sidebar = self.win.view.sidebar
        sidebar.set_collapsed(False, save=False)

        # Simulate narrow window width
        orig_width = self.win.width
        self.win.width = lambda: 700

        # Click navigation button
        sidebar.btn_dash.click()
        self.assertTrue(sidebar.is_collapsed)

        # Restore
        self.win.width = orig_width
        sidebar.set_collapsed(False, save=True)


if __name__ == "__main__":
    unittest.main()
