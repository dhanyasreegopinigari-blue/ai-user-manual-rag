"""Comprehensive tests for UI Redesign, 4-Page Architecture, Theme Toggling, and Features."""
import os
import sys
import unittest
from PyQt6.QtWidgets import QApplication

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import database as db
import services.components as comp_service
from ui.controller import MainWindow
from ui.view import ComponentCardWidget, DARK_STYLE, LIGHT_STYLE, CameraDialog


class TestRedesignAndFeatures(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        db.init_db()
        cls.app = QApplication.instance() or QApplication(sys.argv)
        cls.win = MainWindow()

    def test_three_pages_architecture(self):
        # 1. Verify primary pages (Component Library removed)
        self.assertIsNotNone(self.win.dashboard_page)
        self.assertIsNotNone(self.win.chat_page)
        self.assertIsNotNone(self.win.manual_page)

        # 2. Test navigation across primary pages
        for idx in range(3):
            self.win.navigate_to(idx)
            self.assertEqual(self.win.stack.currentIndex(), idx)

    def test_theme_toggle(self):
        # Test toggling from dark to light and back
        initial_theme = self.win.is_dark_theme
        self.win.toggle_theme()
        self.assertEqual(self.win.is_dark_theme, not initial_theme)
        self.win.toggle_theme()
        self.assertEqual(self.win.is_dark_theme, initial_theme)

    def test_component_library_filtering(self):
        # 1. Test get all categories
        cats = comp_service.get_categories()
        self.assertIn("All", cats)
        self.assertIn("ICs", cats)
        self.assertIn("Microcontrollers", cats)
        self.assertIn("Sensors", cats)

        # 2. Test filter by category
        ics = comp_service.filter_components(category="ICs")
        self.assertGreater(len(ics), 0)
        self.assertTrue(all(c["category"] == "ICs" for c in ics))

        # 3. Test filter by search query
        res = comp_service.filter_components(search_query="555")
        self.assertGreater(len(res), 0)
        self.assertIn("555", res[0]["name"])

        # 4. Test find_component_match
        matched = comp_service.find_component_match("NE555P timer circuit")
        self.assertIsNotNone(matched)
        self.assertEqual(matched["id"], "ne555")

        matched_esp = comp_service.find_component_match("ESP32-WROOM-32")
        self.assertIsNotNone(matched_esp)
        self.assertEqual(matched_esp["id"], "esp32")

    def test_component_card_widget(self):
        comp = comp_service.get_all_components()[0]
        card = ComponentCardWidget(comp)
        self.assertTrue(card.details_box.isHidden())
        card.toggle_details()
        self.assertFalse(card.details_box.isHidden())
        card.toggle_details()
        self.assertTrue(card.details_box.isHidden())

    def test_recent_scans_workflow(self):
        # Add test scan
        sid = db.add_component_scan("LM7805", "Voltage Regulators", 0.95, None, '{"specs":{"model":"7805"}}')
        self.assertIsNotNone(sid)

        # Refresh in controller
        self.win.refresh_recent_scans()
        self.assertGreater(self.win.dash_scans_list.count(), 0)

        # Test selecting the item
        item = self.win.dash_scans_list.item(0)
        self.win.on_recent_scan_clicked(item)
        self.assertIn("LM7805", self.win.hw_values["product_name"].text())

        # Cleanup
        db.delete_component_scan(sid)

    def test_embedded_manual_viewer(self):
        manuals = db.list_manuals()
        if manuals:
            mid = manuals[0]["id"]
            self.win.ev_load_manual(mid, page=1)
            self.assertIsNotNone(self.win.ev_doc)
            self.assertGreater(self.win.ev_total_pages, 0)
            self.assertEqual(self.win.ev_current_page, 1)

            # Test page transitions
            self.win.ev_next_page()
            self.assertEqual(self.win.ev_current_page, 2)
            self.win.ev_prev_page()
            self.assertEqual(self.win.ev_current_page, 1)
            self.win.ev_jump_page(5)
            self.assertEqual(self.win.ev_current_page, 5)

            # Test zoom
            z0 = self.win.ev_zoom
            self.win.ev_zoom_in()
            self.assertGreater(self.win.ev_zoom, z0)
            self.win.ev_zoom_out()
            self.assertEqual(self.win.ev_zoom, z0)

    def test_camera_dialog_graceful_handling(self):
        # Even if camera hardware is missing or busy, dialog initializes without crashing
        dlg = CameraDialog(self.win)
        self.assertIsNotNone(dlg.fallback_btn)
        self.assertIsNotNone(dlg.view)
        dlg.reject()


if __name__ == "__main__":
    unittest.main()
