"""Tests for the 5 new upgrades:
1. Softer, slightly curved buttons (12px / 10px radius and focus states)
2. Inline image answers (manual figures, pinouts, user photos, clean fallback)
3. Manual selector button below composer input (scoping, persistence, view/clear)
4. Step-by-step repair guidance (safety warning cards, required tools, diagnostic steps)
5. Dashboard active scanner preview area (replaces blank box, graceful camera handling)
"""
import os
import re
import sys
import unittest
from PyQt6.QtWidgets import QApplication

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import config
import database as db
import services.llm as llm_service
import services.visual_ref as visual_ref
from ui.controller import MainWindow
from ui.view import ChatMessageWidget, DARK_STYLE, LIGHT_STYLE


class TestNewUpgrades(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication(sys.argv)
        cls.win = MainWindow()

    # 1. Softer buttons
    def test_softer_button_radii_and_focus(self):
        # Verify QPushButton styles do not use 9999px pill shapes
        for style_name, style_qss in [("Dark", DARK_STYLE), ("Light", LIGHT_STYLE)]:
            # Match any QPushButton block with border-radius: 9999px
            btn_matches = re.findall(r"QPushButton[^{]*\{[^}]*border-radius:\s*9999px", style_qss)
            self.assertEqual(len(btn_matches), 0, f"{style_name} still has QPushButton with 9999px")

            # Check 12px button radius and focus states exist
            self.assertIn("border-radius: 12px", style_qss)
            self.assertIn("QPushButton#primaryBtn:focus", style_qss)
            self.assertIn("QPushButton#secondaryBtn:focus", style_qss)

    # 2. Inline images & component reference visuals
    def test_component_reference_image_generation(self):
        res = visual_ref.get_component_reference_image("ne555")
        self.assertIsNotNone(res)
        self.assertTrue(os.path.isfile(res["path"]))
        self.assertIn("NE555", res["caption"])

    def test_chat_widget_renders_inline_images_and_fallback(self):
        # 1. With image: images_box should not be hidden
        ref = visual_ref.get_component_reference_image("atmega328p")
        self.assertIsNotNone(ref)
        asst_with_img = ChatMessageWidget("assistant", "Here is the ATmega328P pinout.", data={
            "summary": "Here is the ATmega328P pinout.",
            "images": [ref]
        }, parent_win=self.win)
        self.assertFalse(asst_with_img.images_box.isHidden())

        # 2. Without image: images_box should be cleanly hidden (graceful fallback)
        asst_text_only = ChatMessageWidget("assistant", "Simple Ohm's Law explanation.", data={
            "summary": "Simple Ohm's Law explanation.",
            "images": []
        }, parent_win=self.win)
        self.assertTrue(asst_text_only.images_box.isHidden())

    # 3. Manual selector button below composer input
    def test_manual_selector_below_composer(self):
        btn = self.win.chat_manual_selector_btn
        self.assertIsNotNone(btn)

        # Clear back to general knowledge (no manual selected)
        self.win.clear_chat_manual()
        self.assertIsNone(self.win.manual_id)
        self.assertIn("Select a manual", btn.text())
        self.assertTrue(self.win.chat_view_manual_btn.isHidden())
        self.assertTrue(self.win.chat_clear_manual_btn.isHidden())

        # Select manual 1
        self.win.set_chat_manual(1)
        self.assertEqual(self.win.manual_id, 1)
        self.assertIn("▼", btn.text())
        self.assertFalse(self.win.chat_view_manual_btn.isHidden())
        self.assertFalse(self.win.chat_clear_manual_btn.isHidden())

        # Clear again
        self.win.clear_chat_manual()
        self.assertIsNone(self.win.manual_id)
        self.assertIn("Select a manual", btn.text())

    def test_manual_selector_persists_to_conversation(self):
        cid = db.create_conversation(manual_id=None, title="Test Scoped Chat")
        self.win.load_conversation(cid)
        self.assertIsNone(self.win.manual_id)

        # User chooses manual 1 for this conversation
        self.win.set_chat_manual(1)
        conv = db.get_conversation(cid)
        self.assertEqual(conv["manual_id"], 1)

        # Switch to another chat without manual
        cid2 = db.create_conversation(manual_id=None, title="General Chat")
        self.win.load_conversation(cid2)
        self.assertIsNone(self.win.manual_id)

        # Switch back: manual 1 must be remembered
        self.win.load_conversation(cid)
        self.assertEqual(self.win.manual_id, 1)

    # 4. Step-by-step repair guidance
    def test_repair_query_detection_and_prompt_formatting(self):
        # Repair keywords trigger structured repair guidance
        repair_q = "How do I troubleshoot and repair an overheating voltage regulator?"
        self.assertTrue(any(kw in repair_q.lower() for kw in llm_service.REPAIR_KEYWORDS))

        # Regular question does not trigger repair
        normal_q = "What is the history of microprocessors?"
        self.assertFalse(any(kw in normal_q.lower() for kw in llm_service.REPAIR_KEYWORDS))

    def test_repair_widget_renders_safety_and_tools(self):
        repair_data = {
            "summary": "Step-by-step diagnostic guide for power supply rail.",
            "safety": "Disconnect AC mains power and discharge bulk 400V electrolytic capacitors before touching leads.",
            "tools": ["Digital Multimeter", "Soldering Iron", "10k 5W Bleeder Resistor"],
            "steps": [
                {"number": 1, "text": "Measure DC rail: expected 12.0V ± 0.5V. If 0V, inspect fuse F1.", "page": None},
                {"number": 2, "text": "Check diode bridge forward drop: expected 0.6V.", "page": None}
            ]
        }
        w = ChatMessageWidget("assistant", "", data=repair_data, parent_win=self.win)
        self.assertFalse(w.safety_card.isHidden())
        self.assertIn("SAFETY PRECAUTION", w.safety_lbl.text())
        self.assertFalse(w.tools_box.isHidden())
        self.assertFalse(w.steps_box.isHidden())

    # 5. Dashboard active scanner preview area
    def test_dashboard_active_scanner_preview(self):
        # Scanner placeholder is present and not hidden initially
        self.assertTrue(hasattr(self.win.view, "scanner_placeholder"))
        
        # When show_hardware is called, placeholder is hidden and uploaded box shown
        mock_res = {
            "preview": None,
            "hardware": {"product_name": "NE555 Timer", "hardware_type": "IC"}
        }
        self.win.show_hardware(mock_res)
        self.assertTrue(self.win.view.scanner_placeholder.isHidden())
        self.assertFalse(self.win.uploaded_box.isHidden())
        self.assertEqual(self.win.dash_match_badge.text(), "Component Identified")

    # 6. Dashboard Zoom & Stacking
    def test_dashboard_large_images_and_layout_toggle(self):
        # Images must have minimum height >= 380px
        self.assertGreaterEqual(self.win.hw_image.minimumHeight(), 380)
        self.assertGreaterEqual(self.win.matched_hw_image.minimumHeight(), 380)

        # Stacking toggle
        initial_stacked = getattr(self.win, "is_dash_stacked", False)
        self.win.toggle_dash_images_layout()
        self.assertNotEqual(initial_stacked, self.win.is_dash_stacked)
        # Toggle back
        self.win.toggle_dash_images_layout()
        self.assertEqual(initial_stacked, self.win.is_dash_stacked)

    # 7. ManualPickerDialog
    def test_manual_picker_dialog(self):
        from ui.view import ManualPickerDialog
        dlg = ManualPickerDialog(self.win, active_manual_id=None)
        self.assertGreater(dlg.list_widget.count(), 0)
        # First item is General Knowledge
        first_item = dlg.list_widget.item(0)
        self.assertIn("General", first_item.text())
        # Filter test
        dlg.search_box.setText("NonExistentXYZManualFilter")
        visible_count = sum(not dlg.list_widget.isRowHidden(i) for i in range(dlg.list_widget.count()))
        self.assertEqual(visible_count, 0)
        dlg.search_box.clear()
        visible_count = sum(not dlg.list_widget.isRowHidden(i) for i in range(dlg.list_widget.count()))
        self.assertGreater(visible_count, 0)
        dlg.close()

    # 8. Component Library Gallery & Images
    def test_component_library_gallery_assets(self):
        import services.component_images as comp_img_service
        from ui.view import ComponentCardWidget
        import services.components as comp_service
        comps = comp_service.get_all_components()
        self.assertGreater(len(comps), 0)
        first_comp = comps[0]

        # Ensure assets are generated
        gallery = comp_img_service.get_component_gallery_images(first_comp["id"])
        self.assertGreaterEqual(len(gallery), 3)
        for item in gallery:
            self.assertTrue(os.path.isfile(item["path"]), f"Missing asset at {item['path']}")

        # Widget should render gallery items
        card = ComponentCardWidget(first_comp)
        self.assertIsNotNone(card.gallery_box)
        self.assertFalse(card.gallery_box.isHidden())

    # 9. Clear and visible sidebar toggle button (Item 2)
    def test_sidebar_toggle_visibility_and_states(self):
        col_btn = self.win.collapse_sidebar_btn
        exp_btn = self.win.expand_sidebar_btn
        self.assertIsNotNone(col_btn)
        self.assertIsNotNone(exp_btn)
        self.assertEqual(col_btn.width(), 38)
        self.assertEqual(col_btn.height(), 38)
        self.assertEqual(col_btn.objectName(), "sidebarToggleBtn")
        self.assertIn("Collapse", col_btn.toolTip())

        # Toggle to collapse
        self.win.toggle_sidebar()
        self.assertTrue(self.win.chat_sidebar.isHidden())
        self.assertFalse(exp_btn.isHidden())
        self.assertEqual(exp_btn.objectName(), "sidebarExpandBtn")
        self.assertIn("Expand", exp_btn.toolTip())

        # Toggle back to expand
        self.win.toggle_sidebar()
        self.assertFalse(self.win.chat_sidebar.isHidden())
        self.assertTrue(exp_btn.isHidden())

    # 10. Compact toolbar and realistic component images (Item 1 & 3)
    def test_compact_library_toolbar_and_credits(self):
        import services.component_images as comp_img_service
        # Search bar is compact (not full screen)
        self.assertLessEqual(self.win.lib_search.maximumWidth(), 520)
        self.assertGreaterEqual(self.win.lib_search.minimumWidth(), 300)

        # Credits exist with authentic license metadata
        credits_map = comp_img_service.load_component_credits()
        self.assertIn("ne555", credits_map)
        self.assertIn("atmega328p", credits_map)
        for cid in ("ne555", "atmega328p", "esp32", "1n4007", "2n2222", "lm7805", "lm358"):
            self.assertIn(cid, credits_map)
            item = credits_map[cid]
            self.assertIn("photo", item)
            self.assertTrue(len(item["photo"].get("author", "")) > 0)
            self.assertTrue(len(item["photo"].get("license", "")) > 0)


if __name__ == "__main__":
    unittest.main()
