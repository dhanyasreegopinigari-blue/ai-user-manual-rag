"""UI Controller layer: Business logic, worker orchestration, Q&A handling, and event coordination."""
import os
import json
import traceback
import cv2
import re
import threading
from datetime import datetime, timedelta

from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import (
    QInputDialog, QPushButton, QTreeWidgetItem,
    QApplication, QCheckBox, QDialog, QFileDialog, QFrame, QGridLayout,
    QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem, QMessageBox, QVBoxLayout,
    QWidget
)

import config
from ui.icons import get_icon, get_pixmap
import database as db
import services.manual as manual_mod
import services.vision as vision_mod
import services.rag as rag
import services.voice as voice
import services.export as export_mod
import services.components as comp_service
from config import AppError
from ui.view import (
    HelpDrawerDialog, ManualDropZone, ManualItemWidget, InteractiveManualViewer,
    ManualScopeDialog, ManualsManagerDialog, ChatHistoryItemWidget, ChatTextEdit, ImageLightboxDialog,
    MainView, QuestionCard, MetaDialog, CameraDialog, ImagePreviewDialog,
    VoiceInputDialog, UserManualDialog, ChatMessageWidget, ComponentCardWidget,
    DARK_STYLE, LIGHT_STYLE, show_image, label, button
)
try:
    import pymupdf as fitz
except ImportError:
    import fitz


class Worker(QThread):
    """Runs fn(progress_callback) in a background thread so the GUI never freezes."""
    done = pyqtSignal(object)
    failed = pyqtSignal(str)
    progress = pyqtSignal(str)

    def __init__(self, fn):
        super().__init__()
        self.fn = fn

    def run(self):
        try:
            result = self.fn(self.progress.emit)
            self.done.emit(result)
        except AppError as e:
            self.failed.emit(str(e))
        except Exception as e:
            traceback.print_exc()
            self.failed.emit(f"Unexpected error:\n{e}")


class MainWindow(QWidget):
    """Main window controller: connects user actions to business logic and background services."""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ElectroLearn AI — Electronic Components Hub")
        self.resize(1140, 840)
        self.setMinimumSize(920, 680)

        # State
        self._workers = []
        self.manual_id = None
        self.active_conv_id = None
        self.question_cache = {}
        self.answer = None
        self.step_i = 0
        self.hw_result = None
        self.is_dark_theme = True
        self.active_category = "All"
        self.manuals_view_mode = "grid"
        self.active_manual_tag = "All"
        self.selected_manual_ids = set()
        self.active_package_filter = "All Packages"
        self.active_pin_filter = "All Pins"
        self.active_sort = "Name (A-Z)" 

        # Embedded Manual Viewer state (Page 4)
        self._ev_doc = None
        self._ev_total_pages = 0
        self._ev_current_page = 1
        self._ev_zoom = 1.25

        # Build View
        self.view = MainView(self)
        self.view.setup_ui()

        # Expose view attributes for direct access and backward compatibility
        self.top_bar = self.view.top_bar
        self.stack = self.view.stack
        self.dashboard_page = self.view.dashboard_page
        self.home_page = self.view.home_page
        self.chat_page = self.view.chat_page
        self.library_page = self.view.library_page
        self.manual_page = self.view.manual_page
        self.busy_page = self.view.busy_page
        self.result_page = self.view.result_page
        self.viewer_page = self.view.viewer_page
        self.ask_page = self.view.ask_page

        self.busy_title = self.view.busy_title
        self.busy_detail = self.view.busy_detail
        self.busy_bar = self.view.busy_bar

        # Dashboard elements
        self.dash_result_card = self.view.dash_result_card
        self.dash_match_badge = self.view.dash_match_badge
        self.dash_scans_list = self.view.dash_scans_list
        self.dash_ask_comp_btn = self.view.dash_ask_comp_btn
        self.hw_image = self.view.hw_image
        self.hw_values = self.view.hw_values
        self.match_status = self.view.match_status
        self.match_detail = self.view.match_detail
        self.manual_combo = self.view.manual_combo
        self.continue_btn = self.view.continue_btn
        self.uploaded_caption = self.view.uploaded_caption
        self.matched_box = self.view.matched_box
        self.matched_caption = self.view.matched_caption
        self.matched_hw_image = self.view.matched_hw_image

        # Chat elements
        self.chat_sidebar = self.view.chat_sidebar
        self.chat_history_list = getattr(self.view, "chat_history_list", None)
        self.chat_scroll = self.view.chat_scroll
        self.chat_thread_widget = self.view.chat_thread_widget
        self.chat_thread_lay = self.view.chat_thread_lay
        self.chat_input = self.view.chat_input
        self.chat_send_btn = self.view.chat_send_btn
        self.chat_speak_btn = self.view.chat_speak_btn
        self.chat_full_check = self.view.chat_full_check
        self.typing_card = self.view.typing_card
        self.typing_lbl = self.view.typing_lbl
        self.chat_manual_badge = self.view.chat_manual_badge
        self.expand_sidebar_btn = self.view.expand_sidebar_btn
        self.chat_manual_combo = getattr(self.view, "chat_manual_combo", None)
        self.chat_view_manual_btn = getattr(self.view, "chat_view_manual_btn", None)

        # Library elements (retained safely for backward compatibility)
        self.lib_search = getattr(self.view, 'lib_search', None)
        self.lib_list = getattr(self.view, 'lib_list', None) or QListWidget()
        self.lib_empty = getattr(self.view, 'lib_empty', None) or QLabel()
        self.cards_lay = getattr(self.view, 'cards_lay', None)

        # Backward compatibility compatibility slots for old viewer/ask tests
        self.ask_manual_name = label("", "subtitle")
        self.q_grid_host = QWidget()
        self.q_grid = QGridLayout(self.q_grid_host)
        self.q_input = QLineEdit()
        self.speak_btn = button("Speak")
        self.speak_btn.setIcon(get_icon("mic", "#cbd5e1", 16))
        self.full_check = QCheckBox()
        self.v_title = label()
        self.v_quick_input = QLineEdit()
        self.v_quick_btn = button("Ask")
        self.v_step_badge = label()
        self.step_tabs_host = QWidget()
        self.step_tabs_lay = QHBoxLayout(self.step_tabs_host)
        self.v_text = label()
        self.v_answer = label()
        self.v_warning = label()
        self.prev_btn = button("Prev")
        self.next_btn = button("Next")
        self.v_img_badge = label()
        self.v_image = label()
        self.v_caption = label()
        self.zoom_btn = button("Zoom")
        self.ref_card = QFrame()
        self.v_ref_badge = label()
        self.v_source = label()
        self.open_pdf_btn = button("PDF")
        self.v_step = self.v_step_badge
        self.v_summary = label()

        # Initialize Default Data & Active Manual
        self.manual_id = None  # Default scope is ALL manuals
        manuals = db.list_manuals()
        if manuals:
            self.manual_id = manuals[0]["id"]

        self.refresh_recent_scans()
        if hasattr(self, 'refresh_manuals_page'):
            self.refresh_manuals_page()
        if hasattr(self.view, 'cards_lay') and self.view.cards_lay:
            self.filter_library_cards()
        self.refresh_dashboard_overview()
        self.navigate_to(0)

    # ---- Theme Management ----------------------------------------------------
    def toggle_theme(self):
        """Toggle between modern Dark and Light themes across the entire app."""
        self.is_dark_theme = not self.is_dark_theme
        theme = DARK_STYLE if self.is_dark_theme else LIGHT_STYLE
        app = QApplication.instance()
        if app:
            app.setStyleSheet(theme)
        if self.is_dark_theme:
            self.top_bar.theme_btn.setText("Dark Mode")
            self.top_bar.theme_btn.setIcon(get_icon("moon", "#00FF85", 16))
        else:
            self.top_bar.theme_btn.setText("Light Mode")
            self.top_bar.theme_btn.setIcon(get_icon("sun", "#10B981", 16))
        self.top_bar.set_active_tab(self.stack.currentIndex())
        self.refresh_dashboard_overview()

    # ---- Navigation & Worker execution ----------------------------------------
    def navigate_to(self, page_index):
        """Switch to one of the primary app pages (Dashboard, AI Assistant, User Manual)."""
        # Backward compatibility: redirect old page 3 (Manuals) to page 2 (User Manual)
        if page_index == 3:
            page_index = 2
        elif page_index not in (0, 1, 2):
            page_index = 0

        self.top_bar.set_active_tab(page_index)
        self.stack.setCurrentIndex(page_index)
        if page_index == 0:
            self.refresh_recent_scans()
            self.refresh_dashboard_overview()
        elif page_index == 1:
            if not self.active_conv_id:
                convs = db.list_conversations()
                if convs:
                    self.load_conversation(convs[0]["id"])
                else:
                    self.new_chat()
            else:
                self.refresh_history_sidebar()
            self.update_scope_ui()
        elif page_index == 2:
            if hasattr(self.view, "switch_to_hw_manuals"):
                self.view.switch_to_hw_manuals()
            if hasattr(self.view, "manuals_stack"):
                self.view.manuals_stack.setCurrentIndex(0)
            self.refresh_manuals_page()

    def go(self, page):
        """Navigate to a specific page widget (supports backward compatibility)."""
        idx = self.stack.indexOf(page)
        if 0 <= idx <= 3:
            self.navigate_to(idx)
        else:
            self.stack.setCurrentWidget(page)

    def run_task(self, fn, on_done, text="Working..."):
        """Run fn(progress_cb) in a background thread without freezing the GUI."""
        prev_idx = self.stack.currentIndex()
        self.busy_title.setText(text)
        self.busy_detail.setText("")
        self.stack.setCurrentWidget(self.busy_page)

        w = Worker(fn)
        self._workers.append(w)
        w.progress.connect(self.busy_detail.setText)

        def ok(result):
            try:
                on_done(result)
            except Exception as e:
                traceback.print_exc()
                QMessageBox.warning(self, "Problem", f"Unexpected error:\n{e}")
            if w in self._workers:
                self._workers.remove(w)
            if self.stack.currentWidget() is self.busy_page:
                self.navigate_to(prev_idx if 0 <= prev_idx <= 3 else 0)

        def fail(msg):
            QMessageBox.warning(self, "Problem", msg)
            if w in self._workers:
                self._workers.remove(w)
            if self.stack.currentWidget() is self.busy_page:
                self.navigate_to(prev_idx if 0 <= prev_idx <= 3 else 0)

        w.done.connect(ok)
        w.failed.connect(fail)
        w.start()

    # ---- Uploads & Camera -----------------------------------------------------
    def upload_photo(self):
        """Validate and analyze an uploaded electronic component image."""
        path, _ = QFileDialog.getOpenFileName(
            self, "Choose an image of your electronic component", "",
            "Images (*.png *.jpg *.jpeg *.bmp *.webp *.tif *.tiff)"
        )
        if not path:
            return

        if not os.path.isfile(path) or os.path.getsize(path) == 0:
            QMessageBox.warning(self, "Invalid File", "The selected file is empty or cannot be accessed.")
            return

        # Check maximum file size (50MB)
        if os.path.getsize(path) > 50 * 1024 * 1024:
            QMessageBox.warning(self, "File Too Large", "The selected image exceeds 50MB. Please select a smaller photo.")
            return

        # Verify image integrity with OpenCV
        test_img = cv2.imread(path)
        if test_img is None:
            QMessageBox.warning(self, "Corrupted Image", "The selected file is not a valid or readable image format.")
            return

        self.run_task(lambda cb: manual_mod.analyze_photo(path, cb), self.show_hardware,
                      "Identifying electronic component...")

    def open_camera(self):
        """Open live camera viewfinder for circuit & component capture."""
        dlg = CameraDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted and dlg.captured_path:
            self.run_task(lambda cb: manual_mod.analyze_photo(dlg.captured_path, cb), self.show_hardware,
                          "Identifying electronic component...")

    def upload_video(self):
        """Analyze a video clip of hardware or component markings."""
        path, _ = QFileDialog.getOpenFileName(
            self, "Choose a video of your component/circuit", "",
            "Videos (*.mp4 *.mov *.avi *.mkv *.webm *.m4v)"
        )
        if not path:
            return

        if not os.path.isfile(path) or os.path.getsize(path) == 0:
            QMessageBox.warning(self, "Invalid Video", "The selected video file is empty or cannot be opened.")
            return

        self.run_task(lambda cb: manual_mod.analyze_video(path, cb), self.show_hardware,
                      "Analyzing video frames...")

    # ---- Hardware & Component Result -----------------------------------------
    def show_hardware(self, res):
        """Display component identification findings and save to recent activity."""
        self.hw_result = res
        hw = res.get("hardware") or {}
        match_info = res.get("match_info") or {}
        source = match_info.get("source")
        matched_img = match_info.get("matched_image_path")

        # Side-by-side comparison if visual match found
        if source in ("visual_image", "visual_image_similar") and matched_img and os.path.isfile(matched_img):
            pno = match_info.get("page", "")
            pct = match_info.get("score_pct", 0)
            self.uploaded_caption.setVisible(True)
            self.matched_caption.setText(f"Matched Manual Illustration (Page {pno} · {pct}% Match)")
            self.matched_box.setVisible(True)
            show_image(self.hw_image, res["preview"], 380, 220)
            show_image(self.matched_hw_image, matched_img, 380, 220)
        else:
            self.matched_box.setVisible(False)
            self.uploaded_caption.setVisible(False)
            if not show_image(self.hw_image, res["preview"], 760, 220):
                self.hw_image.setText("(image preview unavailable)")

        # Populate specs fields
        for k, lbl in self.hw_values.items():
            lbl.setText(hw.get(k) or "Unknown")

        # Check for matching electronic component reference in components library
        comp_match = comp_service.find_component_match(
            f"{hw.get('product_name', '')} {hw.get('model', '')} {hw.get('part_number', '')} {hw.get('hardware_type', '')}"
        )

        name = hw.get("product_name") or hw.get("model") or "Electronic Component"
        cat = hw.get("hardware_type") or "Hardware"
        confidence = 0.95 if res.get("exact") else 0.75

        desc_text = f"<b>{name}</b> ({cat})"
        if comp_match:
            desc_text += f"<br><b>Quick Guide:</b> {comp_match['simple_explanation']}<br><b>Key Specs:</b> {comp_match.get('key_specs', 'N/A')}"
        else:
            v_desc = hw.get("visual_description")
            if v_desc:
                desc_text += f"<br><b>Vision Notes:</b> {v_desc}"

        self.view.dash_desc_lbl.setText(desc_text)
        self.dash_ask_comp_btn.setEnabled(True)

        # Save to persistent component scans table
        try:
            details_json = json.dumps({
                "specs": hw,
                "comp_match_id": comp_match.get("id") if comp_match else None,
                "preview": res.get("preview")
            })
            db.add_component_scan(name, cat, confidence, res.get("preview"), details_json)
            self.refresh_recent_scans()
        except Exception as e:
            print(f"[SCAN_DB] Failed to record scan: {e}")

        # Update manual combobox & status
        exact, similar = res.get("exact") or [], res.get("similar") or []
        exact_ids = [m["id"] for m in exact]
        similar_ids = [m["id"] for m in similar if m["id"] not in exact_ids]

        self.manual_combo.blockSignals(True)
        self.manual_combo.clear()
        if not exact:
            self.manual_combo.addItem("— choose an indexed manual —", None)
        for m in db.list_manuals():
            mark = "[Match] " if m["id"] in exact_ids else ("[Similar] " if m["id"] in similar_ids else "")
            self.manual_combo.addItem(f"{mark}{m['name']}", m["id"])
        pick = (exact_ids or [None])[0]
        if pick is not None:
            self.manual_combo.setCurrentIndex(self.manual_combo.findData(pick))
        self.manual_combo.blockSignals(False)

        if exact:
            self.dash_match_badge.setText("Verified Match")
            self.dash_match_badge.setProperty("kind", "badgeOk")
            self.match_status.setText(f"Matching Manual: {exact[0]['name']}")
            self.match_detail.setText("Step-by-step instructions available in assistant.")
        else:
            self.dash_match_badge.setText("Component Identified")
            self.match_status.setText("General Component Knowledge")
            self.match_detail.setText("Ask questions below or view component pinout.")

        self._update_continue()
        self.navigate_to(0)

    def _update_continue(self):
        mid = self.manual_combo.currentData()
        self.continue_btn.setEnabled(mid is not None)
        if mid:
            self.manual_id = mid

    def continue_from_result(self):
        mid = self.manual_combo.currentData()
        if mid:
            self.manual_id = mid
            self.open_chat(manual_id=mid)
        else:
            self.open_chat()

    def ask_about_scanned_component(self):
        """Jump from Dashboard result directly into AI Assistant with prompt preloaded."""
        if not self.hw_result:
            self.navigate_to(1)
            return
        hw = self.hw_result.get("hardware") or {}
        name = hw.get("product_name") or hw.get("model") or "this component"
        prompt = f"Can you explain the function, pinout connections, and typical circuit applications for {name}?"
        self.open_chat()
        self.send_chat_message(prompt)


    # ---- Dynamic Dashboard Overview (Real DB Data) ---------------------------
    def refresh_dashboard_overview(self):
        """Populate 'Continue Where You Left Off' and 'Hardware Manuals Overview' with real DB data."""
        if not hasattr(self.view, 'dash_chats_container') or not hasattr(self.view, 'dash_manuals_container'):
            return

        is_dark = getattr(self, 'is_dark_theme', True)

        # 1. Continue Where You Left Off
        while self.view.dash_chats_container.count():
            item = self.view.dash_chats_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                sub = item.layout()
                while sub.count():
                    si = sub.takeAt(0)
                    if si.widget():
                        si.widget().deleteLater()

        convs = db.list_conversations()
        recent_convs = convs[:3]
        if not recent_convs:
            empty_box = QWidget()
            e_lay = QVBoxLayout(empty_box)
            e_lay.setContentsMargins(8, 12, 8, 12)
            e_lay.setSpacing(8)
            e_lbl = label("No recent conversations yet. Start a chat with the assistant!", "muted", align=Qt.AlignmentFlag.AlignCenter)
            e_lay.addWidget(e_lbl)
            new_btn = button("Start New Chat", "primary", slot=lambda: (self.new_chat(), self.navigate_to(1)))
            new_btn.setIcon(get_icon("plus", "#ffffff", 14))
            e_lay.addWidget(new_btn, alignment=Qt.AlignmentFlag.AlignCenter)
            self.view.dash_chats_container.addWidget(empty_box)
        else:
            for c in recent_convs:
                row_frame = QFrame()
                row_frame.setObjectName("subCard")
                rf_lay = QHBoxLayout(row_frame)
                rf_lay.setContentsMargins(12, 10, 12, 10)
                rf_lay.setSpacing(10)

                icon_lbl = QLabel()
                icon_lbl.setPixmap(get_pixmap("message-square", "#38BDF8", 16))
                rf_lay.addWidget(icon_lbl)

                info_col = QVBoxLayout()
                info_col.setSpacing(2)
                title = c.get("title") or "Conversation"
                if len(title) > 36:
                    title = title[:33] + "..."
                t_lbl = label(title, "subCardTitle", wrap=False)
                info_col.addWidget(t_lbl)

                dt = (c.get("updated_at") or c.get("created_at") or "")[:16].replace("T", " ")
                m_ref = c.get("manual_name")
                caption_text = dt
                if m_ref:
                    caption_text += f" · {m_ref[:20]}"
                d_lbl = label(caption_text, "caption", wrap=False)
                info_col.addWidget(d_lbl)
                rf_lay.addLayout(info_col, 1)

                cid = c["id"]
                resume_btn = button("Resume", "secondary", slot=lambda checked=False, cid=cid: (self.load_conversation(cid), self.navigate_to(1)))
                resume_btn.setIcon(get_icon("arrow-right", "#00FF85" if is_dark else "#10B981", 14))
                resume_btn.setStyleSheet("padding: 5px 12px; font-size: 12px; border-radius: 8px;")
                rf_lay.addWidget(resume_btn)

                self.view.dash_chats_container.addWidget(row_frame)

        # 2. Hardware Manuals Overview
        while self.view.dash_manuals_container.count():
            item = self.view.dash_manuals_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                sub = item.layout()
                while sub.count():
                    si = sub.takeAt(0)
                    if si.widget():
                        si.widget().deleteLater()

        manuals = db.list_manuals()
        if not manuals:
            empty_box = QWidget()
            e_lay = QVBoxLayout(empty_box)
            e_lay.setContentsMargins(8, 12, 8, 12)
            e_lay.setSpacing(8)
            e_lbl = label("No hardware manuals indexed yet. Upload a PDF manual to enable grounded AI troubleshooting.", "muted", align=Qt.AlignmentFlag.AlignCenter)
            e_lay.addWidget(e_lbl)
            add_btn = button("Add Manual PDF", "primary", slot=self.add_manual)
            add_btn.setIcon(get_icon("upload", "#ffffff", 14))
            e_lay.addWidget(add_btn, alignment=Qt.AlignmentFlag.AlignCenter)
            self.view.dash_manuals_container.addWidget(empty_box)
        else:
            stats_row = QHBoxLayout()
            stats_row.setSpacing(10)

            total_pages = sum(m.get("page_count", 0) for m in manuals)

            box_man = QFrame()
            box_man.setObjectName("statBoxGreen")
            bmlay = QVBoxLayout(box_man)
            bmlay.setContentsMargins(10, 8, 10, 8)
            bmlay.setSpacing(2)
            bmlay.addWidget(label("INDEXED MANUALS", "caption", wrap=False))
            num_mans_lbl = label(str(len(manuals)), "statGreenVal", wrap=False)
            bmlay.addWidget(num_mans_lbl)
            stats_row.addWidget(box_man, 1)

            box_pages = QFrame()
            box_pages.setObjectName("statBoxTeal")
            bplay = QVBoxLayout(box_pages)
            bplay.setContentsMargins(10, 8, 10, 8)
            bplay.setSpacing(2)
            bplay.addWidget(label("TOTAL PAGES", "caption", wrap=False))
            num_pgs_lbl = label(str(total_pages), "statTealVal", wrap=False)
            bplay.addWidget(num_pgs_lbl)
            stats_row.addWidget(box_pages, 1)

            self.view.dash_manuals_container.addLayout(stats_row)

            for m in manuals[:2]:
                m_row = QFrame()
                m_row.setObjectName("subCard")
                m_lay = QHBoxLayout(m_row)
                m_lay.setContentsMargins(12, 10, 12, 10)
                m_lay.setSpacing(10)

                m_icon = QLabel()
                m_icon.setPixmap(get_pixmap("book-open", "#10B981", 16))
                m_lay.addWidget(m_icon)

                m_info = QVBoxLayout()
                m_info.setSpacing(2)
                m_name = m.get("name") or "Manual"
                if len(m_name) > 36:
                    m_name = m_name[:33] + "..."
                m_lbl = label(m_name, "subCardTitle", wrap=False)
                m_info.addWidget(m_lbl)

                extra = f"{m.get('page_count', 0)} pages"
                if m.get('manufacturer'):
                    extra += f" · {m.get('manufacturer')}"
                e_lbl = label(extra, "caption", wrap=False)
                m_info.addWidget(e_lbl)
                m_lay.addLayout(m_info, 1)

                mid = m["id"]
                open_btn = button("Read", "secondary", slot=lambda checked=False, mid=mid: (self.ev_load_manual(mid), self.navigate_to(3)))
                open_btn.setIcon(get_icon("book-open", "#10B981", 14))
                open_btn.setStyleSheet("padding: 5px 12px; font-size: 12px; border-radius: 8px;")
                m_lay.addWidget(open_btn)

                self.view.dash_manuals_container.addWidget(m_row)

    # ---- Recent Scans Management ---------------------------------------------
    def refresh_recent_scans(self):
        """Populate recent scans list on the Dashboard."""
        self.dash_scans_list.clear()
        scans = db.list_component_scans(limit=15)
        for s in scans:
            ts = (s.get("scanned_at") or "")[:16]
            c_name = s.get("component_name") or "Component"
            cat = s.get("category") or "General"
            try:
                conf = int(float(s.get("confidence") or 0.8) * 100)
            except Exception:
                conf = 85
            item = QListWidgetItem(f"{c_name}  ·  {cat}  ·  {conf}% match  ({ts})")
            item.setIcon(get_icon("zap", "#00FF85", 16))
            item.setData(Qt.ItemDataRole.UserRole, s)
            self.dash_scans_list.addItem(item)

    def on_recent_scan_clicked(self, item):
        """Inspect a saved recent scan."""
        s = item.data(Qt.ItemDataRole.UserRole)
        if not s:
            return
        name = s.get("component_name", "Component")
        cat = s.get("category", "")
        img_path = s.get("image_path")
        self.hw_values["product_name"].setText(name)
        self.hw_values["hardware_type"].setText(cat)
        if img_path and os.path.isfile(img_path):
            show_image(self.hw_image, img_path, 760, 220)

        comp_match = comp_service.find_component_match(name)
        if comp_match:
            self.view.dash_desc_lbl.setText(
                f"<b>{comp_match['name']}</b> ({comp_match['category']})<br>"
                f"<b>Guide:</b> {comp_match['simple_explanation']}<br>"
                f"<b>Key Specs:</b> {comp_match.get('key_specs', '')}"
            )
        else:
            self.view.dash_desc_lbl.setText(f"Identified component: <b>{name}</b> ({cat})")
        self.dash_ask_comp_btn.setEnabled(True)

    def clear_recent_scans(self):
        scans = db.list_component_scans()
        if not scans:
            return
        if QMessageBox.question(self, "Clear Scans", "Clear all recent component scans from history?") == QMessageBox.StandardButton.Yes:
            for s in scans:
                db.delete_component_scan(s["id"])
            self.refresh_recent_scans()
        if hasattr(self, 'refresh_manuals_page'):
            self.refresh_manuals_page()
        self.setup_library_filters()
        self.filter_library_cards()

    # ---- Component Library Management ----------------------------------------
    def setup_library_filters(self):
        menu = getattr(self.view, 'lib_filter_menu', None)
        if not menu:
            return
        menu.clear()

        # Sort Submenu
        sort_menu = menu.addMenu("Sort By")
        for s in ["Name (A-Z)", "Name (Z-A)", "Category"]:
            act = sort_menu.addAction(s)
            act.setCheckable(True)
            act.setChecked(getattr(self, 'active_sort', 'Name (A-Z)') == s)
            act.triggered.connect(lambda _=False, val=s: self.set_sort_filter(val))

        menu.addSeparator()

        # Package Submenu
        pkg_menu = menu.addMenu("Package Type")
        for p in comp_service.get_package_types():
            act = pkg_menu.addAction(p)
            act.setCheckable(True)
            act.setChecked(getattr(self, 'active_package_filter', 'All Packages') == p)
            act.triggered.connect(lambda _=False, val=p: self.set_package_filter(val))

        # Pin Count Submenu
        pins_menu = menu.addMenu("Pin Count")
        for pc in ["All Pins", "2-3 Pins", "4-8 Pins", "14+ Pins"]:
            act = pins_menu.addAction(pc)
            act.setCheckable(True)
            act.setChecked(getattr(self, 'active_pin_filter', 'All Pins') == pc)
            act.triggered.connect(lambda _=False, val=pc: self.set_pin_filter(val))

        menu.addSeparator()
        reset_act = menu.addAction("Reset All Filters")
        reset_act.triggered.connect(self.reset_all_library_filters)

    def set_sort_filter(self, val):
        self.active_sort = val
        self.setup_library_filters()
        self.filter_library_cards()

    def set_package_filter(self, val):
        self.active_package_filter = val
        self.setup_library_filters()
        self.filter_library_cards()

    def set_pin_filter(self, val):
        self.active_pin_filter = val
        self.setup_library_filters()
        self.filter_library_cards()

    def reset_all_library_filters(self):
        self.active_category = "All"
        self.manuals_view_mode = "grid"
        self.active_manual_tag = "All"
        self.selected_manual_ids = set()
        self.active_package_filter = "All Packages"
        self.active_pin_filter = "All Pins"
        self.active_sort = "Name (A-Z)"
        if hasattr(self.view, 'lib_search'):
            self.view.lib_search.clear()
        for cat, btn in getattr(self.view, 'chip_buttons', []):
            is_active = (cat == "All")
            btn.setProperty("kind", "catPillActive" if is_active else "catPill")
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        self.setup_library_filters()
        self.filter_library_cards()

    def on_category_chip_clicked(self, category):
        self.active_category = category
        for cat, btn in getattr(self.view, 'chip_buttons', []):
            is_active = (cat == category)
            btn.setProperty("kind", "catPillActive" if is_active else "catPill")
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        self.filter_library_cards()

    def filter_library_cards(self):
        """Dynamically render component cards based on category, search query, package, and pins."""
        search_q = self.lib_search.text().strip() if hasattr(self, 'lib_search') and self.lib_search else ""
        pkg_f = getattr(self, 'active_package_filter', 'All Packages')
        pin_f = getattr(self, 'active_pin_filter', 'All Pins')
        sort_f = getattr(self, 'active_sort', 'Name (A-Z)')

        comps = comp_service.filter_components(
            category=self.active_category,
            search_query=search_q,
            package=pkg_f,
            pin_filter=pin_f,
            sort_by=sort_f
        )

        cards = [
            ComponentCardWidget(c, on_ask_cb=self.on_ask_component_from_library, parent_win=self)
            for c in comps
        ]

        if hasattr(self.view, 'lib_grid'):
            self.view.lib_grid.set_cards(cards)

        if hasattr(self.view, 'lib_status_lbl'):
            count = len(cards)
            filter_note = []
            if self.active_category != "All":
                filter_note.append(self.active_category)
            if pkg_f != "All Packages":
                filter_note.append(pkg_f)
            if pin_f != "All Pins":
                filter_note.append(pin_f)
            note_str = f" in {', '.join(filter_note)}" if filter_note else ""
            self.view.lib_status_lbl.setText(f"Showing {count} component{'s' if count != 1 else ''}{note_str}")

        if hasattr(self.view, 'lib_no_results'):
            self.view.lib_no_results.setVisible(len(cards) == 0)

    def on_ask_component_from_library(self, comp):
        """Triggered from Component Card 'Ask Assistant' button."""
        name = comp.get('display_name') or comp.get('name', 'Component')
        prompt = f"Can you explain how to wire the {name}, its pinout functions, and safety tips?"
        self.navigate_to(1)
        if hasattr(self.view, 'chat_input'):
            self.view.chat_input.setPlainText(prompt)
            self.view.chat_input.setFocus()

    # ---- PDF Manuals Management -----------------------------------------------
    def refresh_library(self):
        self.lib_list.clear()
        manuals = db.list_manuals()
        for m in manuals:
            item = QListWidgetItem(f"{m['name']} — {m.get('manufacturer', '')} {m.get('model', '')}")
            item.setIcon(get_icon("book-open", "#10B981", 16))
            item.setData(Qt.ItemDataRole.UserRole, m["id"])
            self.lib_list.addItem(item)
        self.lib_empty.setVisible(not manuals)

    def _selected_id(self):
        item = self.lib_list.currentItem()
        if not item:
            QMessageBox.information(self, "Manual Library", "Please select a manual from the list first.")
            return None
        return item.data(Qt.ItemDataRole.UserRole)

    def add_manual(self):
        path, _ = QFileDialog.getOpenFileName(self, "Choose a PDF manual", "", "PDF files (*.pdf)")
        if not path:
            return
        dlg = MetaDialog(self, os.path.splitext(os.path.basename(path))[0])
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        name, maker, model = dlg.name.text(), dlg.maker.text(), dlg.model.text()
        self.run_task(lambda cb: manual_mod.import_pdf(path, name, maker, model, cb),
                      lambda _id: (self.refresh_library(), self.ev_load_manual(_id)), "Importing manual...")

    def delete_selected(self):
        mid = self._selected_id()
        if mid is None:
            return
        if QMessageBox.question(self, "Delete Manual", "Delete this manual and its indexed pages?") != QMessageBox.StandardButton.Yes:
            return
        manual_mod.delete_manual(mid)
        self.refresh_library()

    def use_selected_manual(self):
        mid = self._selected_id()
        if mid is not None:
            self.manual_id = mid
            self.open_chat(manual_id=mid)

    def view_selected_manual(self):
        mid = self._selected_id()
        if mid:
            self.manual_id = mid
            self.ev_load_manual(mid)
            self.navigate_to(3)

    # ---- Chat & Conversation System -------------------------------------------
    def toggle_sidebar(self):
        vis = not self.chat_sidebar.isVisible()
        self.chat_sidebar.setVisible(vis)
        self.expand_sidebar_btn.setVisible(not vis)

    def filter_chat_history(self, text):
        self.refresh_history_sidebar()

    def refresh_history_sidebar(self):
        """Group chats by date categories (PINNED, TODAY, YESTERDAY, 7 DAYS, OLDER) with slim styling."""
        if not hasattr(self.view, 'sidebar_groups_lay'):
            return

        while self.view.sidebar_groups_lay.count():
            child = self.view.sidebar_groups_lay.takeAt(0)
            w = child.widget()
            if w:
                w.hide()
                w.setParent(None)
                w.deleteLater()
            elif child.layout():
                sub = child.layout()
                while sub.count():
                    si = sub.takeAt(0)
                    sw = si.widget()
                    if sw:
                        sw.hide()
                        sw.setParent(None)
                        sw.deleteLater()

        convs = db.list_conversations()
        filter_text = self.view.chat_search.text().strip().lower() if hasattr(self.view, 'chat_search') else ""

        if filter_text:
            convs = [c for c in convs if filter_text in (c.get("title") or "").lower()]

        self.view.chat_count_lbl.setText(f"{len(convs)} conversation{'s' if len(convs) != 1 else ''}")

        now = datetime.now()
        today = now.date()
        yesterday = today - timedelta(days=1)
        seven_days_ago = today - timedelta(days=7)

        groups = {
            "PINNED": [],
            "TODAY": [],
            "YESTERDAY": [],
            "PREVIOUS 7 DAYS": [],
            "OLDER": []
        }

        for c in convs:
            if c.get("is_pinned"):
                groups["PINNED"].append(c)
                continue

            dt_str = c.get("updated_at") or c.get("created_at") or ""
            try:
                c_date = datetime.fromisoformat(dt_str).date()
            except Exception:
                c_date = today

            if c_date == today:
                groups["TODAY"].append(c)
            elif c_date == yesterday:
                groups["YESTERDAY"].append(c)
            elif c_date >= seven_days_ago:
                groups["PREVIOUS 7 DAYS"].append(c)
            else:
                groups["OLDER"].append(c)

        for group_name, items in groups.items():
            if not items:
                continue

            hdr = label(group_name, "caption", wrap=False)
            hdr.setObjectName("chatDateHeader")
            self.view.sidebar_groups_lay.addWidget(hdr)

            for c in items:
                is_active = (c["id"] == self.active_conv_id)
                dt_str = (c.get("updated_at") or c.get("created_at") or "")[:16].replace("T", " ")
                item_widget = ChatHistoryItemWidget(
                    c["id"],
                    c.get("title") or "New Chat",
                    dt_str,
                    is_active=is_active,
                    is_pinned=bool(c.get("is_pinned")),
                    parent=self.view.sidebar_container
                )
                item_widget.clicked.connect(self.load_conversation)
                item_widget.pin_requested.connect(self.pin_chat)
                item_widget.rename_requested.connect(self.rename_chat)
                item_widget.delete_requested.connect(self.delete_chat)
                self.view.sidebar_groups_lay.addWidget(item_widget)

        self.view.sidebar_groups_lay.addStretch(1)

    def pin_chat(self, conv_id, is_pinned):
        db.pin_conversation(conv_id, is_pinned)
        self.refresh_history_sidebar()

    def rename_chat(self, conv_id):
        conv = db.get_conversation(conv_id)
        current = conv.get("title", "") if conv else ""
        new_title, ok = QInputDialog.getText(self, "Rename Chat", "Enter new conversation title:", text=current)
        if ok and new_title.strip():
            db.update_conversation_title(conv_id, new_title.strip())
            self.refresh_history_sidebar()
            self.refresh_dashboard_overview()

    def delete_chat(self, conv_id):
        if QMessageBox.question(self, "Delete Chat", "Are you sure you want to delete this chat?") == QMessageBox.StandardButton.Yes:
            db.delete_conversation(conv_id)
            if self.active_conv_id == conv_id:
                convs = db.list_conversations()
                if convs:
                    self.load_conversation(convs[0]["id"])
                else:
                    self.new_chat()
            else:
                self.refresh_history_sidebar()
            self.refresh_dashboard_overview()

    # ---- Scope Controls & Multi-Manual Management ----------------------------
    def update_scope_ui(self):
        manuals = db.list_manuals()
        total = len(manuals)

        # Update chat manual combo selector
        combo = getattr(self.view, "chat_manual_combo", None)
        if combo is not None:
            combo.blockSignals(True)
            combo.clear()
            combo.addItem(f"📚 All Loaded Manuals ({total})", None)
            sel_idx = 0
            for idx, m in enumerate(manuals, start=1):
                mname = m.get("name") or "Manual"
                pages = m.get("page_count", 0)
                mfr = m.get("manufacturer", "")
                label_txt = f"📄 {mname}"
                if mfr:
                    label_txt += f" — {mfr}"
                if pages:
                    label_txt += f" ({pages}p)"
                combo.addItem(label_txt, m["id"])
                if self.manual_id == m["id"]:
                    sel_idx = idx
            combo.setCurrentIndex(sel_idx)
            combo.blockSignals(False)

        if self.manual_id is None:
            if hasattr(self.view, "scope_chip_btn"):
                self.view.scope_chip_btn.setText(f"All manuals ({total})")
                self.view.scope_chip_btn.setProperty("kind", "chipActive")
            self.chat_manual_badge.setText(f"Scope: All Manuals ({total})")
            if hasattr(self.view, "scope_clear_btn"):
                self.view.scope_clear_btn.setVisible(False)
            if hasattr(self.view, "chat_view_manual_btn"):
                self.view.chat_view_manual_btn.setVisible(False)
        else:
            m = db.get_manual(self.manual_id)
            mname = m["name"] if m else "Manual"
            if hasattr(self.view, "scope_chip_btn"):
                self.view.scope_chip_btn.setText(f"{mname[:20]}")
                self.view.scope_chip_btn.setProperty("kind", "chip")
            self.chat_manual_badge.setText(f"Scope: {mname}")
            if hasattr(self.view, "scope_clear_btn"):
                self.view.scope_clear_btn.setVisible(True)
            if hasattr(self.view, "chat_view_manual_btn"):
                self.view.chat_view_manual_btn.setVisible(True)

        if hasattr(self.view, "scope_chip_btn"):
            self.view.scope_chip_btn.style().unpolish(self.view.scope_chip_btn)
            self.view.scope_chip_btn.style().polish(self.view.scope_chip_btn)

    def on_chat_manual_combo_changed(self, index):
        combo = getattr(self.view, "chat_manual_combo", None)
        if combo is None:
            return
        mid = combo.currentData()
        self.manual_id = mid
        if self.active_conv_id:
            db.update_conversation_manual(self.active_conv_id, self.manual_id)
        self.update_scope_ui()

    def on_chat_view_manual_clicked(self):
        if self.manual_id:
            self.load_manual_in_viewer(self.manual_id)

    def open_scope_picker(self):
        dlg = ManualScopeDialog(self, current_manual_id=self.manual_id)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.manual_id = dlg.selected_manual_id
            if self.active_conv_id:
                db.update_conversation_manual(self.active_conv_id, self.manual_id)
            self.update_scope_ui()

    def reset_scope_to_all(self):
        self.manual_id = None
        if self.active_conv_id:
            db.update_conversation_manual(self.active_conv_id, None)
        self.update_scope_ui()

    def add_manual_multi(self):
        paths, _ = QFileDialog.getOpenFileNames(self, "Choose PDF Manuals", "", "PDF files (*.pdf)")
        if not paths:
            return
        def task_fn(progress_cb):
            imported = []
            for i, p in enumerate(paths, 1):
                base = os.path.splitext(os.path.basename(p))[0]
                progress_cb(f"Indexing manual {i}/{len(paths)}: {base[:30]}...")
                mid = manual_mod.import_pdf(p, base, "", "", progress_cb)
                imported.append(mid)
            return imported
        def on_done(ids):
            self.refresh_library()
            self.refresh_dashboard_overview()
            self.update_scope_ui()
            QMessageBox.information(self, "Manuals Added", f"Successfully indexed {len(ids)} manual(s)!")
        self.run_task(task_fn, on_done, text="Importing manuals...")

    def manage_manuals_modal(self):
        dlg = ManualsManagerDialog(
            self,
            on_delete_cb=lambda mid: (manual_mod.delete_manual(mid), self.refresh_library(), self.refresh_dashboard_overview(), self.update_scope_ui()),
            on_read_cb=lambda mid: (self.ev_load_manual(mid), self.navigate_to(3)),
            on_add_cb=self.add_manual_multi
        )
        dlg.exec()

    def open_chat(self, manual_id=None, conv_id=None):
        """Open chat page, ensuring active conversation and scope are set."""
        if manual_id is not None:
            self.manual_id = manual_id

        if conv_id:
            self.load_conversation(conv_id)
        elif self.active_conv_id:
            self.load_conversation(self.active_conv_id)
        else:
            convs = db.list_conversations()
            if convs:
                self.load_conversation(convs[0]["id"])
            else:
                self.new_chat()

        self.update_scope_ui()
        self.top_bar.set_active_tab(1)
        self.stack.setCurrentIndex(1)

    def new_chat(self):
        cid = db.create_conversation(self.manual_id, "New Chat")
        self.active_conv_id = cid
        self.render_empty_chat_welcome()
        self.refresh_history_sidebar()
        self.refresh_dashboard_overview()
        self.update_scope_ui()
        self.chat_input.setFocus()

    def render_empty_chat_welcome(self):
        while self.chat_thread_lay.count() > 1:
            child = self.chat_thread_lay.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        welcome_card = QFrame()
        welcome_card.setObjectName("asstCard")
        w_lay = QVBoxLayout(welcome_card)
        w_lay.setContentsMargins(24, 20, 24, 20)
        w_lay.setSpacing(12)

        m = db.get_manual(self.manual_id) if self.manual_id else None
        mtitle = m["name"] if m else "ElectroLearn AI Hardware Assistant"
        w_lay.addWidget(label(f"Welcome to {mtitle}", "h1"))
        w_lay.addWidget(label("Ask any question across your hardware manuals, troubleshoot circuits, identify ICs, or click a suggested prompt below.", "muted"))

        qs = [
            "Explain this pinout and connections",
            "Help me troubleshoot my circuit problem",
            "What safety precautions prevent damage to ICs?",
            "How do I determine resistor values from color bands?",
            "What is an NE555 timer and how does Astable mode work?",
            "How does an ultrasonic distance sensor measure flight time?"
        ]
        w_lay.addWidget(label("SUGGESTED QUESTIONS", "caption", wrap=False))

        grid = QGridLayout()
        grid.setSpacing(8)
        for i, q in enumerate(qs):
            card = QuestionCard(q)
            card.clicked.connect(lambda _, qtext=q: self.send_chat_message(qtext))
            grid.addWidget(card, i // 2, i % 2)
        w_lay.addLayout(grid)

        self.chat_thread_lay.insertWidget(0, welcome_card)

    def send_chat_message(self, explicit_question=None):
        raw_text = explicit_question or self.chat_input.toPlainText()
        question = raw_text.strip()
        if not question:
            return

        if not explicit_question:
            self.chat_input.clear()

        if not self.active_conv_id:
            self.active_conv_id = db.create_conversation(self.manual_id, question[:35])

        if self.chat_thread_lay.count() == 2:
            item = self.chat_thread_lay.itemAt(0)
            if item and item.widget() and item.widget().objectName() == "asstCard":
                item.widget().deleteLater()

        db.add_chat_message(self.active_conv_id, "user", question)
        user_w = ChatMessageWidget("user", question, parent_win=self)
        self.chat_thread_lay.insertWidget(self.chat_thread_lay.count() - 1, user_w)

        conv = db.get_conversation(self.active_conv_id)
        if conv and conv.get("title") == "New Chat":
            db.update_conversation_title(self.active_conv_id, question[:35])

        self.scroll_chat_to_bottom()

        self.typing_lbl.setText("Searching manuals & synthesizing answer...")
        self.typing_card.setVisible(True)
        self.chat_send_btn.setEnabled(False)
        self.chat_speak_btn.setEnabled(False)

        history = db.get_chat_messages(self.active_conv_id)[-6:]
        mode = "full" if self.chat_full_check.isChecked() else "auto"

        self._chat_cancel_event = threading.Event()

        def task_fn(progress_cb):
            return rag.answer_question(
                self.manual_id,
                question,
                progress=progress_cb,
                mode=mode,
                history=history,
                cancel_event=self._chat_cancel_event
            )

        def on_done(ans):
            self.typing_card.setVisible(False)
            self.chat_send_btn.setEnabled(True)
            self.chat_speak_btn.setEnabled(True)

            summary = ans.get("summary") or ans.get("answer") or "Here is the guidance for your question."
            db.add_chat_message(self.active_conv_id, "assistant", summary, data=ans)

            asst_w = ChatMessageWidget("assistant", summary, data=ans, parent_win=self)
            self.chat_thread_lay.insertWidget(self.chat_thread_lay.count() - 1, asst_w)

            self.refresh_history_sidebar()
            self.scroll_chat_to_bottom()

        worker = Worker(task_fn)
        self._workers.append(worker)
        worker.progress.connect(self.typing_lbl.setText)
        worker.done.connect(on_done)
        worker.failed.connect(lambda err: (
            self.typing_card.setVisible(False),
            self.chat_send_btn.setEnabled(True),
            self.chat_speak_btn.setEnabled(True),
            QMessageBox.warning(self, "Assistant Response", err)
        ))
        worker.start()

    def stop_generating(self):
        if hasattr(self, "_chat_cancel_event"):
            self._chat_cancel_event.set()
        self.view.typing_card.setVisible(False)
        self.chat_send_btn.setEnabled(True)
        self.chat_speak_btn.setEnabled(True)

    def load_conversation(self, conv_id):
        self.active_conv_id = conv_id
        conv = db.get_conversation(conv_id)
        if conv:
            self.manual_id = conv.get("manual_id")

        self.update_scope_ui()

        while self.chat_thread_lay.count() > 1:
            child = self.chat_thread_lay.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        msgs = db.get_chat_messages(conv_id)
        if not msgs:
            self.render_empty_chat_welcome()
        else:
            for m in msgs:
                role = m["role"]
                content = m["content"]
                data = None
                if m.get("data_json"):
                    try:
                        data = json.loads(m["data_json"])
                    except Exception:
                        pass
                w = ChatMessageWidget(role, content, data=data, parent_win=self)
                self.chat_thread_lay.insertWidget(self.chat_thread_lay.count() - 1, w)

        self.refresh_history_sidebar()
        self.scroll_chat_to_bottom()

    # ---- Voice Input Handling (ChatGPT-Style) ---------------------------------
    def toggle_voice_input(self):
        if getattr(self, "_is_recording_voice", False):
            self.stop_voice_input()
        else:
            self.start_voice_input()

    def start_voice_input(self):
        if not voice.is_available():
            QMessageBox.warning(self, "Voice Input", "Microphone recording is unavailable.\nPlease check your microphone settings.")
            return

        self._is_recording_voice = True
        self._voice_seconds = 0
        self.view.voice_timer_lbl.setText("0:00")
        self.view.voice_level_bar.setValue(0)
        self.view.voice_bar.setVisible(True)

        self.voice_recorder = voice.AudioRecorder(samplerate=16000)
        self.voice_recorder.start(level_callback=self._on_voice_level)

        if not hasattr(self, "_voice_qtimer"):
            self._voice_qtimer = QTimer(self)
            self._voice_qtimer.timeout.connect(self._on_voice_timer_tick)
        self._voice_qtimer.start(100)

    def _on_voice_level(self, level):
        self.view.voice_level_bar.setValue(int(level))

    def _on_voice_timer_tick(self):
        if not getattr(self, "_is_recording_voice", False):
            return
        self._voice_seconds += 0.1
        sec = int(self._voice_seconds)
        self.view.voice_timer_lbl.setText(f"{sec // 60}:{sec % 60:02d}")

        if self.voice_recorder and self.voice_recorder.should_auto_stop():
            self.stop_voice_input()

    def stop_voice_input(self):
        if not getattr(self, "_is_recording_voice", False):
            return
        self._is_recording_voice = False
        if hasattr(self, "_voice_qtimer"):
            self._voice_qtimer.stop()

        self.view.voice_bar.setVisible(False)
        audio = self.voice_recorder.stop() if self.voice_recorder else None
        if audio is None or len(audio) == 0:
            return

        lang_idx = self.view.voice_lang_combo.currentIndex()
        lang_code = self.view.voice_lang_combo.itemData(lang_idx) or "en"

        def task_fn(progress_cb):
            progress_cb("Transcribing voice audio with Whisper...")
            return voice.transcribe_audio(audio, progress=progress_cb)

        def on_done(text):
            current = self.view.chat_input.toPlainText()
            separator = " " if current and not current.endswith(" ") else ""
            self.view.chat_input.setText(current + separator + text)
            self.view.chat_input.setFocus()

        self.run_task(task_fn, on_done, text="Transcribing speech...")

    def cancel_voice_input(self):
        self._is_recording_voice = False
        if hasattr(self, "_voice_qtimer"):
            self._voice_qtimer.stop()
        if self.voice_recorder:
            self.voice_recorder.stop()
        self.view.voice_bar.setVisible(False)

    # ---- Chat Polish: Scroll, TTS, Citations & Photo Attach -------------------
    def _on_chat_scroll_moved(self, val):
        bar = self.view.chat_scroll.verticalScrollBar()
        if bar.maximum() - val > 120:
            self.view.scroll_bottom_btn.show()
            self.view.scroll_bottom_btn.move(
                self.view.chat_scroll.width() - 56,
                self.view.chat_scroll.height() - 56
            )
        else:
            self.view.scroll_bottom_btn.hide()

    def scroll_chat_to_bottom(self):
        QTimer.singleShot(60, lambda: (
            self.view.chat_scroll.verticalScrollBar().setValue(
                self.view.chat_scroll.verticalScrollBar().maximum()
            ),
            self.view.scroll_bottom_btn.hide()
        ))

    def edit_user_message(self, content):
        self.view.chat_input.setText(content)
        self.view.chat_input.setFocus()

    def regenerate_last_answer(self):
        if not self.active_conv_id:
            return
        msgs = db.get_chat_messages(self.active_conv_id)
        user_msgs = [m for m in msgs if m["role"] == "user"]
        if user_msgs:
            last_q = user_msgs[-1]["content"]
            self.send_chat_message(last_q)

    def read_aloud_answer(self, text):
        try:
            from PyQt6.QtTextToSpeech import QTextToSpeech
            if not hasattr(self, "_tts"):
                self._tts = QTextToSpeech(self)
            clean_text = re.sub(r"<[^>]+>", "", text)
            clean_text = re.sub(r"\\[[^\\]]+\\]", "", clean_text)
            self._tts.say(clean_text)
        except Exception as e:
            print(f"[TTS] Read aloud error: {e}")

    def attach_photo_to_chat(self):
        path, _ = QFileDialog.getOpenFileName(self, "Choose component photo", "", "Images (*.png *.jpg *.jpeg *.webp)")
        if not path:
            return
        self.run_task(
            lambda cb: vision_mod.identify_hardware(path, cb),
            lambda res: self._on_photo_attached_to_chat(path, res),
            text="Analyzing component photo..."
        )

    def _on_photo_attached_to_chat(self, path, res):
        hw = res.get("hardware") or {}
        name = hw.get("product_name") or "Electronic Component"
        desc = hw.get("visual_description") or ""
        prompt = f"I uploaded an image of a {name}. {desc}. How do I wire, use, or troubleshoot it?"
        self.view.chat_input.setText(prompt)
        self.view.chat_input.setFocus()



    # ---- Hardware Manuals Hub & Interactive Reader (Page 4) ------------------
    def open_help_drawer(self):
        """Open the slide-out Help & Guided Tour modal drawer."""
        dlg = HelpDrawerDialog(self)
        dlg.exec()

    def start_guided_tour(self):
        """Interactive walkthrough of the 4 primary application screens."""
        steps = [
            (0, "Dashboard: Here you can scan electronic components with your camera, upload photos, and view AI matches with datasheet illustrations."),
            (1, "AI Assistant: Chat with our electronics troubleshooting model, dictate questions with real-time waveform voice input, and inspect citations."),
            (2, "Component Library: Explore real photographs, pinout diagrams, schematic symbols, and key specs across 8 component categories."),
            (3, "Hardware Manuals: Upload and manage PDF service manuals, inspect schematics in our high-res interactive reader, and toggle AI chat search.")
        ]
        for tab_idx, msg in steps:
            self.navigate_to(tab_idx)
            QMessageBox.information(self, f"Tour Step {tab_idx + 1} of 4", msg)

    def refresh_manuals_page(self):
        """Refresh summary cards, recently viewed row, tag chips, and manuals list."""
        if not hasattr(self.view, "stat_total_val"):
            return

        # 1. Summary Statistics
        stats = db.get_manual_summary_stats()
        self.view.stat_total_val.setText(str(stats.get("total_manuals", 0)))
        self.view.stat_pages_val.setText(str(stats.get("total_pages", 0)))
        self.view.stat_chat_val.setText(f"{stats.get('chat_enabled', 0)} of {stats.get('total_manuals', 0)}")
        sz_mb = stats.get("total_bytes", 0) / (1024 * 1024)
        self.view.stat_storage_val.setText(f"{sz_mb:.1f} MB")

        # 2. Recently Viewed Row
        while self.view.recent_cards_lay.count():
            item = self.view.recent_cards_lay.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        recent_manuals = db.list_manuals(sort_by="Recently Viewed")[:4]
        has_recent = any(m.get("last_viewed_at") for m in recent_manuals)
        self.view.recent_box.setVisible(has_recent)

        for m in recent_manuals:
            if not m.get("last_viewed_at"):
                continue
            rc = QFrame()
            rc.setStyleSheet("background: #0d1410; border: 1px solid rgba(0,255,133,0.15); border-radius: 8px; padding: 6px 12px;")
            rc_l = QHBoxLayout(rc)
            rc_l.setContentsMargins(4, 4, 4, 4)
            rc_l.setSpacing(8)

            ic = QLabel()
            ic.setPixmap(get_pixmap("book-open", "#00FF85", 16))
            rc_l.addWidget(ic)

            name_lbl = QLabel(f"<b>{m['name'][:24]}...</b>" if len(m['name']) > 26 else f"<b>{m['name']}</b>")
            name_lbl.setStyleSheet("font-size: 12px; color: #F3FBF5;")
            rc_l.addWidget(name_lbl)

            open_b = QPushButton("Open")
            open_b.setIcon(get_icon("chevron-right", "#00FF85", 12))
            open_b.setProperty("kind", "secondary")
            open_b.setFixedHeight(26)
            open_b.clicked.connect(lambda _=False, mid=m['id']: self.load_manual_in_viewer(mid))
            rc_l.addWidget(open_b)

            self.view.recent_cards_lay.addWidget(rc)

        self.view.recent_cards_lay.addStretch()

        # 3. Collections / Tag Filter Pills
        while self.view.tags_lay.count() > 1:
            item = self.view.tags_lay.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        tags = ["All"] + db.get_all_manual_tags()
        for t in tags:
            btn = QPushButton(t)
            is_act = (t == getattr(self, "active_manual_tag", "All"))
            btn.setProperty("kind", "catPillActive" if is_act else "catPill")
            btn.clicked.connect(lambda _=False, tag=t: self._on_manual_tag_clicked(tag))
            self.view.tags_lay.insertWidget(self.view.tags_lay.count() - 1, btn)

        # 4. Refresh List
        self.filter_manuals_list()

    def _on_manual_tag_clicked(self, tag):
        self.active_manual_tag = tag
        self.refresh_manuals_page()

    def filter_manuals_list(self):
        """Query and populate manuals into the grid or list container."""
        if not hasattr(self.view, "manuals_lay"):
            return

        search_q = self.view.man_search.text().strip() if hasattr(self.view, "man_search") else ""
        sort_by = self.view.man_sort_combo.currentText() if hasattr(self.view, "man_sort_combo") else "Newest Added"
        tag = getattr(self, "active_manual_tag", "All")

        manuals = db.list_manuals(search=search_q, tag=tag, sort_by=sort_by)

        while self.view.manuals_lay.count():
            item = self.view.manuals_lay.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.view.man_empty.setVisible(len(manuals) == 0)

        mode = getattr(self, "manuals_view_mode", "grid")

        if mode == "grid":
            grid_w = QWidget()
            grid_l = QGridLayout(grid_w)
            grid_l.setContentsMargins(0, 0, 0, 0)
            grid_l.setSpacing(14)
            cols = 3
            for i, m in enumerate(manuals):
                w = ManualItemWidget(
                    m, view_mode="grid",
                    on_view_cb=self.load_manual_in_viewer,
                    on_ask_cb=lambda mid: (setattr(self, "manual_id", mid), self.open_chat(manual_id=mid)),
                    on_toggle_cb=self.on_manual_chat_toggled,
                    on_delete_cb=self.delete_manual_confirmed,
                    on_rename_cb=self.rename_manual_modal,
                    on_download_cb=self.download_manual_pdf,
                    parent=self
                )
                w.select_check.toggled.connect(lambda val, mid=m['id']: self._on_manual_selected(mid, val))
                grid_l.addWidget(w, i // cols, i % cols)
            self.view.manuals_lay.addWidget(grid_w)
        else:
            for m in manuals:
                w = ManualItemWidget(
                    m, view_mode="list",
                    on_view_cb=self.load_manual_in_viewer,
                    on_ask_cb=lambda mid: (setattr(self, "manual_id", mid), self.open_chat(manual_id=mid)),
                    on_toggle_cb=self.on_manual_chat_toggled,
                    on_delete_cb=self.delete_manual_confirmed,
                    on_rename_cb=self.rename_manual_modal,
                    on_download_cb=self.download_manual_pdf,
                    parent=self
                )
                w.select_check.toggled.connect(lambda val, mid=m['id']: self._on_manual_selected(mid, val))
                self.view.manuals_lay.addWidget(w)

    def set_manuals_view_mode(self, mode):
        self.manuals_view_mode = mode
        is_dark = getattr(self, "is_dark_theme", True)
        acc = "#00FF85" if is_dark else "#10B981"
        mut = "#6B8273" if is_dark else "#94a3b8"
        self.view.view_grid_btn.setIcon(get_icon("grid", acc if mode == "grid" else mut, 15))
        self.view.view_list_btn.setIcon(get_icon("list", acc if mode == "list" else mut, 15))
        self.filter_manuals_list()

    def _on_manual_selected(self, mid, val):
        if val:
            self.selected_manual_ids.add(mid)
        else:
            self.selected_manual_ids.discard(mid)
        has_sel = len(self.selected_manual_ids) > 0
        self.view.bulk_delete_btn.setVisible(has_sel)
        if has_sel:
            self.view.bulk_delete_btn.setText(f"Delete Selected ({len(self.selected_manual_ids)})")

    def add_manual_multi(self):
        """Open multi-PDF file dialog and batch import."""
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Choose hardware manuals to index", "", "PDF Files (*.pdf)"
        )
        if paths:
            self.import_manual_files(paths)

    def import_manual_files(self, paths):
        """Import multiple PDF files with per-file progress tracking."""
        if not paths:
            return

        total = len(paths)
        self.view.drop_zone.show_progress(0, total, "Starting import...")

        def run_import(progress_cb):
            results = []
            for idx, p in enumerate(paths):
                name = os.path.splitext(os.path.basename(p))[0]
                def sub_cb(msg):
                    progress_cb(f"[{idx+1}/{total}] {name}: {msg}")
                try:
                    mid = manual_mod.import_pdf(p, name, progress=sub_cb)
                    results.append((p, mid, None))
                except Exception as e:
                    results.append((p, None, str(e)))
            return results

        def on_done(results):
            self.view.drop_zone.hide_progress()
            successes = [r for r in results if r[1] is not None]
            failures = [r for r in results if r[2] is not None]
            self.refresh_manuals_page()
            self.refresh_library()
            self.refresh_dashboard_overview()
            self.update_scope_ui()
            if hasattr(self.view, "manuals_stack"):
                self.view.manuals_stack.setCurrentIndex(0)
            if successes:
                QMessageBox.information(
                    self, "Manuals Added",
                    f"Successfully indexed {len(successes)} manual(s)! They are now available in your manuals list and AI Assistant."
                )
            if failures:
                err_text = "\n".join(f"• {os.path.basename(f[0])}: {f[2]}" for f in failures)
                QMessageBox.warning(self, "Some Manuals Failed", f"The following files could not be indexed:\n{err_text}")

        self.run_task(run_import, on_done, text=f"Indexing {total} Manual(s)...")

    def reindex_all_manuals(self):
        if QMessageBox.question(self, "Re-index All", "Rebuild chunks and vector embeddings for all indexed manuals?") != QMessageBox.StandardButton.Yes:
            return
        self.run_task(
            lambda cb: manual_mod.reindex_all_manuals(progress=cb),
            lambda _: (self.refresh_manuals_page(), QMessageBox.information(self, "Re-indexed", "All manuals re-indexed successfully.")),
            "Re-indexing manuals..."
        )

    def on_manual_chat_toggled(self, mid, val):
        db.update_manual_chat_enabled(mid, val)
        stats = db.get_manual_summary_stats()
        self.view.stat_chat_val.setText(f"{stats.get('chat_enabled', 0)} of {stats.get('total_manuals', 0)}")

    def delete_manual_confirmed(self, mid):
        m = db.get_manual(mid)
        name = m.get("name", "this manual") if m else "this manual"
        if QMessageBox.question(
            self, "Delete Manual",
            f"Are you sure you want to delete '{name}'?\n\nThis will remove all indexed chunks, extracted images, and FAISS vectors so it will never appear in AI search answers.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) != QMessageBox.StandardButton.Yes:
            return
        manual_mod.delete_manual(mid)
        if self.manual_id == mid:
            self.manual_id = None
        self.refresh_manuals_page()
        self.refresh_library()
        self.refresh_dashboard_overview()
        self.update_scope_ui()

    def bulk_delete_manuals(self):
        if not self.selected_manual_ids:
            return
        count = len(self.selected_manual_ids)
        if QMessageBox.question(
            self, "Bulk Delete",
            f"Delete {count} selected manual(s) and remove their vector indexes and images?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) != QMessageBox.StandardButton.Yes:
            return

        for mid in list(self.selected_manual_ids):
            manual_mod.delete_manual(mid)
        if self.manual_id in self.selected_manual_ids:
            self.manual_id = None
        self.selected_manual_ids.clear()
        self.view.bulk_delete_btn.setVisible(False)
        self.refresh_manuals_page()
        self.refresh_library()
        self.refresh_dashboard_overview()
        self.update_scope_ui()

    def rename_manual_modal(self, manual):
        new_name, ok = QInputDialog.getText(self, "Rename Manual", "Manual Title:", text=manual.get("name", ""))
        if ok and new_name.strip():
            db.update_manual_metadata(manual["id"], new_name.strip(), manual.get("manufacturer", ""), manual.get("model", ""), manual.get("tags", ""))
            self.refresh_manuals_page()
            self.refresh_library()
            self.refresh_dashboard_overview()
            self.update_scope_ui()

    def download_manual_pdf(self, manual):
        src = manual.get("file_path")
        if not src or not os.path.isfile(src):
            QMessageBox.warning(self, "Download Error", "Source file not found on disk.")
            return
        dst, _ = QFileDialog.getSaveFileName(self, "Save Copy of PDF Manual", os.path.basename(src), "PDF Files (*.pdf)")
        if dst:
            import shutil
            shutil.copy2(src, dst)
            QMessageBox.information(self, "Saved", f"Manual PDF saved to {dst}")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        w = event.size().width()
        if hasattr(self, "view") and hasattr(self.view, "sidebar"):
            if w < 850:
                if not self.view.sidebar.is_collapsed:
                    self.view.sidebar.set_collapsed(True, save=False)
            else:
                saved = self.view.sidebar.settings.value("sidebar_collapsed", False, type=bool)
                if self.view.sidebar.is_collapsed != saved:
                    self.view.sidebar.set_collapsed(saved, save=False)

    def load_manual_in_viewer(self, manual_id, page=1, highlight_query=""):
        """Display the interactive PDF viewer for the given manual."""
        self.manual_id = manual_id
        self.navigate_to(2)
        if hasattr(self.view, "switch_to_hw_manuals"):
            self.view.switch_to_hw_manuals()
        if hasattr(self.view, "manuals_stack"):
            self.view.manuals_stack.setCurrentIndex(1)
        if hasattr(self.view, "viewer_widget"):
            self.view.viewer_widget.load_manual(manual_id, page=page, highlight_query=highlight_query)
            self.ev_doc = self.view.viewer_widget.doc
            self.ev_total_pages = self.view.viewer_widget.total_pages
            self.ev_current_page = self.view.viewer_widget.current_page

    def open_user_manual(self, pno=1, mid=None, highlight=""):
        """Navigates to the Manuals page, opens the viewer at the exact cited page, and highlights terms."""
        target_mid = mid or self.manual_id
        if not target_mid:
            manuals = db.list_manuals()
            if manuals:
                target_mid = manuals[0]["id"]
        if target_mid:
            self.load_manual_in_viewer(target_mid, page=int(pno) if pno else 1, highlight_query=highlight)


    # ---- Embedded PDF Manual Viewer Compatibility Layer ----------------------
    @property
    def ev_doc(self):
        w = getattr(self.view, "viewer_widget", None)
        return getattr(w, "doc", None) or self._ev_doc

    @ev_doc.setter
    def ev_doc(self, val):
        self._ev_doc = val

    @property
    def ev_total_pages(self):
        w = getattr(self.view, "viewer_widget", None)
        return getattr(w, "total_pages", 0) or self._ev_total_pages

    @ev_total_pages.setter
    def ev_total_pages(self, val):
        self._ev_total_pages = val

    @property
    def ev_current_page(self):
        w = getattr(self.view, "viewer_widget", None)
        return getattr(w, "current_page", 1) if w and hasattr(w, "current_page") else self._ev_current_page

    @ev_current_page.setter
    def ev_current_page(self, val):
        self._ev_current_page = val
        if hasattr(self.view, "viewer_widget"):
            self.view.viewer_widget.current_page = val

    @property
    def ev_zoom(self):
        w = getattr(self.view, "viewer_widget", None)
        return getattr(w, "zoom", 1.0) if w and hasattr(w, "zoom") else self._ev_zoom

    @ev_zoom.setter
    def ev_zoom(self, val):
        self._ev_zoom = val
        if hasattr(self.view, "viewer_widget"):
            self.view.viewer_widget.zoom = val

    def ev_load_manual(self, manual_id, page=1):
        self.load_manual_in_viewer(manual_id, page=page)

    def ev_render_page(self, page_num):
        if hasattr(self.view, "viewer_widget"):
            self.view.viewer_widget.jump_to_page(page_num)

    def ev_jump_page(self, pno):
        if hasattr(self.view, "viewer_widget"):
            self.view.viewer_widget.jump_to_page(pno)

    def ev_prev_page(self):
        if hasattr(self.view, "viewer_widget"):
            self.view.viewer_widget.prev_page()

    def ev_next_page(self):
        if hasattr(self.view, "viewer_widget"):
            self.view.viewer_widget.next_page()

    def ev_zoom_in(self):
        if hasattr(self.view, "viewer_widget"):
            self.view.viewer_widget.zoom_in()

    def ev_zoom_out(self):
        if hasattr(self.view, "viewer_widget"):
            self.view.viewer_widget.zoom_out()

    def ev_fit_width(self):
        if hasattr(self.view, "viewer_widget"):
            self.view.viewer_widget.fit_width()


    def ev_open_external(self):
        if self.manual_id:
            m = db.get_manual(self.manual_id)
            if m and m.get("file_path") and os.path.isfile(m["file_path"]):
                try:
                    os.startfile(m["file_path"])
                except Exception as e:
                    QMessageBox.warning(self, "Viewer", f"Could not launch external viewer:\n{e}")

    # ---- Exporting -----------------------------------------------------------
    def export_current_chat(self, fmt="txt"):
        if not self.active_conv_id:
            QMessageBox.information(self, "Export", "No active conversation to export.")
            return

        conv = db.get_conversation(self.active_conv_id)
        msgs = db.get_chat_messages(self.active_conv_id)
        if not msgs:
            QMessageBox.information(self, "Export", "The conversation is empty.")
            return

        title = conv.get("title") or "Conversation"
        mname = conv.get("manual_name") or "Electronics Assistant"
        ext = f".{fmt}"
        filter_str = f"{fmt.upper()} files (*{ext})"
        dest, _ = QFileDialog.getSaveFileName(self, f"Export Conversation as {fmt.upper()}", f"{title}{ext}", filter_str)
        if not dest:
            return

        try:
            if fmt == "pdf":
                html = export_mod.format_conversation_html(msgs, title=title, manual_name=mname)
                export_mod.save_as_pdf(html, dest)
            elif fmt == "md":
                content = export_mod.format_conversation_md(msgs, title=title, manual_name=mname)
                with open(dest, "w", encoding="utf-8") as f:
                    f.write(content)
            else:
                content = export_mod.format_conversation_txt(msgs, title=title, manual_name=mname)
                with open(dest, "w", encoding="utf-8") as f:
                    f.write(content)
            QMessageBox.information(self, "Export Complete", f"Conversation exported successfully to:\n{dest}")
        except Exception as e:
            QMessageBox.warning(self, "Export Failed", f"Could not export conversation:\n{e}")

    def export_recent_chats(self, fmt="txt"):
        convs = db.list_conversations()
        if not convs:
            QMessageBox.information(self, "Export", "No recent chats found to export.")
            return

        all_msgs = []
        for c in convs[:15]:
            all_msgs.append({"role": "user", "content": f"--- CHAT: {c.get('title')} ---"})
            all_msgs.extend(db.get_chat_messages(c["id"]))

        ext = f".{fmt}"
        dest, _ = QFileDialog.getSaveFileName(self, f"Export Recent Chats as {fmt.upper()}", f"Recent_Chats_Export{ext}", f"{fmt.upper()} files (*{ext})")
        if not dest:
            return

        try:
            if fmt == "pdf":
                html = export_mod.format_conversation_html(all_msgs, title="Recent Chats Export", manual_name="ElectroLearn AI")
                export_mod.save_as_pdf(html, dest)
            elif fmt == "md":
                content = export_mod.format_conversation_md(all_msgs, title="Recent Chats Export", manual_name="ElectroLearn AI")
                with open(dest, "w", encoding="utf-8") as f:
                    f.write(content)
            else:
                content = export_mod.format_conversation_txt(all_msgs, title="Recent Chats Export", manual_name="ElectroLearn AI")
                with open(dest, "w", encoding="utf-8") as f:
                    f.write(content)
            QMessageBox.information(self, "Export Complete", f"Recent chats exported successfully to:\n{dest}")
        except Exception as e:
            QMessageBox.warning(self, "Export Failed", f"Could not export recent chats:\n{e}")

    def export_single_answer(self, answer_data, question="", fmt="txt"):
        title = answer_data.get("title") or "Component_Answer"
        safe_title = "".join(c for c in title if c.isalnum() or c in (" ", "_", "-")).strip()[:40]
        ext = f".{fmt}"
        dest, _ = QFileDialog.getSaveFileName(self, f"Export Answer as {fmt.upper()}", f"{safe_title}{ext}", f"{fmt.upper()} files (*{ext})")
        if not dest:
            return

        m = db.get_manual(self.manual_id) if self.manual_id else None
        mname = m["name"] if m else "Electronics Assistant"
        try:
            if fmt == "pdf":
                html = export_mod.format_answer_html(answer_data, question=question, manual_name=mname)
                export_mod.save_as_pdf(html, dest)
            elif fmt == "md":
                content = export_mod.format_answer_md(answer_data, question=question)
                with open(dest, "w", encoding="utf-8") as f:
                    f.write(content)
            else:
                content = export_mod.format_answer_txt(answer_data, question=question)
                with open(dest, "w", encoding="utf-8") as f:
                    f.write(content)
            QMessageBox.information(self, "Export Complete", f"Answer exported successfully to:\n{dest}")
        except Exception as e:
            QMessageBox.warning(self, "Export Failed", f"Could not export answer:\n{e}")

    # Backward compatibility helpers
    def open_library(self):
        self.navigate_to(2)

    def speak(self):
        self.speak_chat()

    def speak_viewer(self):
        self.speak_chat()

    def ask(self, q):
        self.open_chat()
        self.send_chat_message(q)

    def ask_from_viewer(self):
        self.open_chat()

    def return_to_ask_page(self):
        self.top_bar.set_active_tab(1)
        self.stack.setCurrentIndex(1)

    def default_questions(self, mid=None):
        return [
            "How do I determine resistor values from color bands?",
            "What is the difference between NPN and PNP transistors?",
            "How do I wire an NE555 timer in Astable mode?",
            "What voltage regulator should I use to step down 12V to 5V?",
            "How does an ultrasonic distance sensor measure flight time?",
            "What safety precautions prevent electrostatic discharge (ESD)?"
        ]
