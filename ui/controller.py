"""UI Controller layer: Business logic, streaming LLM orchestration, Q&A handling, and event coordination."""
import os
import json
import traceback
import cv2

from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtWidgets import (
    QApplication, QCheckBox, QDialog, QFileDialog, QFrame, QGridLayout,
    QHBoxLayout, QLabel, QLineEdit, QListWidgetItem, QMessageBox, QVBoxLayout,
    QWidget
)

import config
import database as db
import services.manual as manual_mod
import services.rag as rag
import services.voice as voice
import services.export as export_mod
import services.components as comp_service
import services.llm as llm_service
from config import AppError
from ui.view import (
    MainView, QuestionCard, MetaDialog, SettingsDialog, CameraDialog,
    ImagePreviewDialog, VoiceInputDialog, UserManualDialog, ChatMessageWidget,
    ComponentCardWidget, DARK_STYLE, LIGHT_STYLE, show_image, label, button
)
try:
    import pymupdf as fitz
except ImportError:
    import fitz


class Worker(QThread):
    """Runs fn(progress_cb, stream_cb) in a background thread with live token streaming."""
    done = pyqtSignal(object)
    failed = pyqtSignal(str)
    progress = pyqtSignal(str)
    stream_token = pyqtSignal(str)

    def __init__(self, fn):
        super().__init__()
        self.fn = fn

    def run(self):
        try:
            # Pass progress and stream callbacks
            import inspect
            sig = inspect.signature(self.fn)
            if len(sig.parameters) >= 2:
                result = self.fn(self.progress.emit, self.stream_token.emit)
            else:
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
        self.is_dark_theme = (getattr(config, "APP_THEME", "dark") != "light")
        self.active_category = "All"

        # Embedded Manual Viewer state (Page 4)
        self.ev_doc = None
        self.ev_total_pages = 0
        self.ev_current_page = 1
        self.ev_zoom = 1.25

        # Build View
        self.view = MainView(self)
        self.view.setup_ui()

        # Keep space background resized
        self.view.space_bg.setGeometry(self.rect())

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
        self.chat_history_list = self.view.chat_history_list
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

        # Library elements
        self.lib_search = self.view.lib_search
        self.lib_list = self.view.lib_list
        self.lib_empty = self.view.lib_empty
        self.cards_lay = self.view.cards_lay

        # Backward compatibility compatibility slots for old viewer/ask tests
        self.ask_manual_name = label("", "subtitle")
        self.q_grid_host = QWidget()
        self.q_grid = QGridLayout(self.q_grid_host)
        self.q_input = QLineEdit()
        self.speak_btn = button("🎤 Speak")
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

        # Initialize Data & Active Manual
        manuals = db.list_manuals()
        if manuals:
            self.manual_id = manuals[0]["id"]
            self.ev_load_manual(self.manual_id)

        self.refresh_recent_scans()
        self.filter_library_cards()
        self.refresh_library()
        self.navigate_to(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "view") and hasattr(self.view, "space_bg"):
            self.view.space_bg.setGeometry(self.rect())

    # ---- Theme Management ----------------------------------------------------
    def toggle_theme(self):
        """Toggle between Agent One Matrix Dark and Clean Mint Light themes."""
        self.is_dark_theme = not self.is_dark_theme
        config.save_theme("dark" if self.is_dark_theme else "light")
        theme = DARK_STYLE if self.is_dark_theme else LIGHT_STYLE
        app = QApplication.instance()
        if app:
            app.setStyleSheet(theme)
        self.view.update_background_theme(self.is_dark_theme)
        self.top_bar.theme_btn.setText("🌓 Dark Theme" if self.is_dark_theme else "☀️ Light Theme")

    # ---- Navigation & Worker execution ----------------------------------------
    def navigate_to(self, page_index):
        """Switch to one of the 4 primary app pages."""
        self.top_bar.set_active_tab(page_index)
        self.stack.setCurrentIndex(page_index)
        if page_index == 0:
            self.refresh_recent_scans()
        elif page_index == 1:
            if not self.active_conv_id:
                convs = db.list_conversations()
                if convs:
                    self.load_conversation(convs[0]["id"])
                else:
                    self.new_chat()
            else:
                self.refresh_history_sidebar()
        elif page_index == 2:
            self.filter_library_cards()
            self.refresh_library()
        elif page_index == 3:
            if self.manual_id and not self.ev_doc:
                self.ev_load_manual(self.manual_id)

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

        if os.path.getsize(path) > 50 * 1024 * 1024:
            QMessageBox.warning(self, "File Too Large", "The selected image exceeds 50MB. Please select a smaller photo.")
            return

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

        for k, lbl in self.hw_values.items():
            lbl.setText(hw.get(k) or "Unknown")

        comp_match = comp_service.find_component_match(
            f"{hw.get('product_name', '')} {hw.get('model', '')} {hw.get('part_number', '')} {hw.get('hardware_type', '')}"
        )

        name = hw.get("product_name") or hw.get("model") or "Electronic Component"
        cat = hw.get("hardware_type") or "Hardware"
        confidence = 0.95 if res.get("exact") else 0.75

        desc_text = f"<b>{name}</b> ({cat})"
        if comp_match:
            desc_text += f"<br>💡 <b>Quick Guide:</b> {comp_match['simple_explanation']}<br>⚡ <b>Key Specs:</b> {comp_match.get('key_specs', 'N/A')}"
        else:
            v_desc = hw.get("visual_description")
            if v_desc:
                desc_text += f"<br>🔍 {v_desc}"

        self.view.dash_desc_lbl.setText(desc_text)
        self.dash_ask_comp_btn.setEnabled(True)

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

        exact, similar = res.get("exact") or [], res.get("similar") or []
        exact_ids = [m["id"] for m in exact]
        similar_ids = [m["id"] for m in similar if m["id"] not in exact_ids]

        self.manual_combo.blockSignals(True)
        self.manual_combo.clear()
        if not exact:
            self.manual_combo.addItem("— choose an indexed manual —", None)
        for m in db.list_manuals():
            mark = "✓ " if m["id"] in exact_ids else ("≈ " if m["id"] in similar_ids else "")
            self.manual_combo.addItem(f"{mark}{m['name']}", m["id"])
        pick = (exact_ids or [None])[0]
        if pick is not None:
            self.manual_combo.setCurrentIndex(self.manual_combo.findData(pick))
        self.manual_combo.blockSignals(False)

        if exact:
            self.dash_match_badge.setText("✓ Verified Match")
            self.dash_match_badge.setProperty("kind", "badgeOk")
            self.match_status.setText(f"✓ Matching Manual: {exact[0]['name']}")
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
            item = QListWidgetItem(f"⚡ {c_name}  ·  {cat}  ·  {conf}% match  ({ts})")
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
                f"💡 {comp_match['simple_explanation']}<br>"
                f"⚡ <b>Key Specs:</b> {comp_match.get('key_specs', '')}"
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

    # ---- Component Library Management ----------------------------------------
    def on_category_chip_clicked(self, category):
        self.active_category = category
        for cat, btn in self.view.chip_buttons:
            is_active = (cat == category)
            btn.setProperty("kind", "chipActive" if is_active else "chip")
            btn.style().unpolish(btn)
            btn.style().polish(btn)

        if category == "Hardware Manuals":
            self.view.lib_stack.setCurrentIndex(1)
            self.refresh_library()
        else:
            self.view.lib_stack.setCurrentIndex(0)
            self.filter_library_cards()

    def filter_library_cards(self):
        """Dynamically render component cards based on category and search query."""
        search_q = self.lib_search.text().strip()
        comps = comp_service.filter_components(self.active_category, search_q)

        while self.cards_lay.count() > 1:
            child = self.cards_lay.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        for c in comps:
            card_widget = ComponentCardWidget(c, on_ask_cb=self.on_ask_component_from_library)
            self.cards_lay.insertWidget(self.cards_lay.count() - 1, card_widget)

    def on_ask_component_from_library(self, comp):
        """Triggered from Component Card 'Ask Assistant' button."""
        prompt = f"Can you explain how to wire the {comp['name']}, its pinout functions, and safety tips?"
        self.open_chat()
        self.send_chat_message(prompt)

    # ---- PDF Manuals Management -----------------------------------------------
    def refresh_library(self):
        self.lib_list.clear()
        manuals = db.list_manuals()
        for m in manuals:
            item = QListWidgetItem(f"📖 {m['name']} — {m.get('manufacturer', '')} {m.get('model', '')}")
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

    # ---- Chat & Conversation System (Streaming Hybrid LLM) -------------------
    def toggle_sidebar(self):
        vis = not self.chat_sidebar.isVisible()
        self.chat_sidebar.setVisible(vis)
        self.expand_sidebar_btn.setVisible(not vis)

    def refresh_history_sidebar(self):
        self.chat_history_list.clear()
        convs = db.list_conversations()
        for c in convs:
            title = c.get("title") or "New Chat"
            date = (c.get("updated_at") or "")[:10]
            item = QListWidgetItem(f"💬 {title}\n  {date}")
            item.setData(Qt.ItemDataRole.UserRole, c["id"])
            if c["id"] == self.active_conv_id:
                item.setSelected(True)
            self.chat_history_list.addItem(item)

    def _on_history_item_clicked(self, item):
        cid = item.data(Qt.ItemDataRole.UserRole)
        if cid:
            self.load_conversation(cid)

    def open_chat(self, manual_id=None, conv_id=None):
        """Open chat page, ensuring active conversation is loaded."""
        if manual_id:
            self.manual_id = manual_id
        elif not self.manual_id:
            manuals = db.list_manuals()
            if manuals:
                self.manual_id = manuals[0]["id"]

        m = db.get_manual(self.manual_id) if self.manual_id else None
        mname = m["name"] if m else "General Electronics Knowledge"
        provider = llm_service.get_active_provider().upper()
        self.chat_manual_badge.setText(f"💬 Assistant ({provider}) · {mname}")

        self.refresh_history_sidebar()

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

        self.top_bar.set_active_tab(1)
        self.stack.setCurrentIndex(1)

    def new_chat(self):
        cid = db.create_conversation(self.manual_id, "New Chat")
        self.active_conv_id = cid
        self.render_empty_chat_welcome()
        self.refresh_history_sidebar()
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

        provider = llm_service.get_active_provider().upper()
        w_lay.addWidget(label(f"👋 ElectroLearn AI Assistant ({provider})", "h1"))
        w_lay.addWidget(label(
            "Ask general electronics questions or inquire about imported hardware manuals. "
            "Get instant explanations, schematic symbols, calculations, and circuit troubleshooting.", "muted"
        ))

        qs = [
            "What is an Integrated Circuit (IC) and how does it work?",
            "How do I determine resistor values from color bands?",
            "What is the difference between NPN and PNP transistors?",
            "How do I wire an NE555 timer in Astable oscillator mode?",
            "What voltage regulator should I use to step down 12V to 5V?",
            "What safety precautions prevent electrostatic discharge (ESD)?"
        ]
        w_lay.addWidget(label("✨ SUGGESTED QUESTIONS:", "caption", wrap=False))

        grid = QGridLayout()
        grid.setSpacing(8)
        for i, q in enumerate(qs):
            card = QuestionCard(q)
            card.clicked.connect(lambda _, qtext=q: self.send_chat_message(qtext))
            grid.addWidget(card, i // 2, i % 2)
        w_lay.addLayout(grid)

        self.chat_thread_lay.insertWidget(0, welcome_card)

    def send_chat_message(self, explicit_question=None):
        question = (explicit_question or self.chat_input.text()).strip()
        if not question:
            return

        if not explicit_question:
            self.chat_input.clear()

        if not self.active_conv_id:
            self.active_conv_id = db.create_conversation(self.manual_id, question[:35])

        # Remove welcome card once real conversation starts
        if self.chat_thread_lay.count() == 2:
            item = self.chat_thread_lay.itemAt(0)
            if item and item.widget() and item.widget().objectName() == "asstCard":
                item.widget().deleteLater()

        # 1. Add User Message to UI & DB
        db.add_chat_message(self.active_conv_id, "user", question)
        user_w = ChatMessageWidget("user", question, parent_win=self)
        self.chat_thread_lay.insertWidget(self.chat_thread_lay.count() - 1, user_w)

        conv = db.get_conversation(self.active_conv_id)
        if conv and conv.get("title") == "New Chat":
            db.update_conversation_title(self.active_conv_id, question[:35])

        # 2. Add Assistant Message Widget ready for streaming tokens
        asst_w = ChatMessageWidget("assistant", "", parent_win=self)
        self.chat_thread_lay.insertWidget(self.chat_thread_lay.count() - 1, asst_w)

        QTimer.singleShot(50, lambda: self.chat_scroll.verticalScrollBar().setValue(
            self.chat_scroll.verticalScrollBar().maximum()))

        provider = llm_service.get_active_provider().upper()
        self.typing_lbl.setText(f"Thinking with {provider}...")
        self.typing_card.setVisible(True)
        self.chat_send_btn.setEnabled(False)
        self.chat_speak_btn.setEnabled(False)

        history = db.get_chat_messages(self.active_conv_id)[-8:]

        # Streaming task worker
        def task_fn(progress_cb, stream_cb):
            return llm_service.answer_hybrid(
                self.manual_id,
                question,
                history=history,
                progress_cb=progress_cb,
                stream_cb=stream_cb
            )

        def on_stream_token(token):
            self.typing_card.setVisible(False)
            asst_w.append_stream_token(token)
            # Smooth auto-scroll during generation
            self.chat_scroll.verticalScrollBar().setValue(
                self.chat_scroll.verticalScrollBar().maximum()
            )

        def on_done(ans):
            self.typing_card.setVisible(False)
            self.chat_send_btn.setEnabled(True)
            self.chat_speak_btn.setEnabled(True)

            summary = ans.get("summary") or ans.get("answer") or "Here is the guidance."
            asst_w.finalize_stream(ans)
            db.add_chat_message(self.active_conv_id, "assistant", summary, data=ans)

            self.refresh_history_sidebar()
            QTimer.singleShot(60, lambda: self.chat_scroll.verticalScrollBar().setValue(
                self.chat_scroll.verticalScrollBar().maximum()))

        worker = Worker(task_fn)
        self._workers.append(worker)
        worker.progress.connect(self.typing_lbl.setText)
        worker.stream_token.connect(on_stream_token)
        worker.done.connect(on_done)
        worker.failed.connect(lambda err: (
            self.typing_card.setVisible(False),
            self.chat_send_btn.setEnabled(True),
            self.chat_speak_btn.setEnabled(True),
            asst_w.append_stream_token(f"\n⚠️ Error: {err}"),
            QMessageBox.warning(self, "Assistant Problem", err)
        ))
        worker.start()

    def load_conversation(self, conv_id):
        self.active_conv_id = conv_id
        conv = db.get_conversation(conv_id)
        if conv and conv.get("manual_id"):
            self.manual_id = conv["manual_id"]
            mname = conv.get("manual_name") or "Manual"
            provider = llm_service.get_active_provider().upper()
            self.chat_manual_badge.setText(f"💬 Assistant ({provider}) · {mname}")

        while self.chat_thread_lay.count() > 1:
            child = self.chat_thread_lay.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        msgs = db.get_chat_messages(conv_id)
        if not msgs:
            self.render_empty_chat_welcome()
        else:
            for m in msgs:
                widget = ChatMessageWidget(
                    m["role"],
                    m["content"],
                    data=m.get("data"),
                    created_at=(m.get("created_at") or "")[-8:],
                    parent_win=self
                )
                self.chat_thread_lay.insertWidget(self.chat_thread_lay.count() - 1, widget)

        self.refresh_history_sidebar()
        QTimer.singleShot(50, lambda: self.chat_scroll.verticalScrollBar().setValue(
            self.chat_scroll.verticalScrollBar().maximum()))

    def delete_selected_conversation(self):
        item = self.chat_history_list.currentItem()
        if not item:
            QMessageBox.information(self, "Delete Chat", "Please select a conversation from the sidebar first.")
            return

        cid = item.data(Qt.ItemDataRole.UserRole)
        if not cid:
            return

        if QMessageBox.question(self, "Delete Chat", "Delete this conversation history?") != QMessageBox.StandardButton.Yes:
            return

        db.delete_conversation(cid)
        if cid == self.active_conv_id:
            self.active_conv_id = None
            convs = db.list_conversations()
            if convs:
                self.load_conversation(convs[0]["id"])
            else:
                self.new_chat()
        else:
            self.refresh_history_sidebar()

    def speak_chat(self):
        if not voice.is_available():
            QMessageBox.information(self, "Voice", voice.UNAVAILABLE)
            return

        dlg = VoiceInputDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted and getattr(dlg, "transcribed_text", None):
            text = dlg.transcribed_text.strip()
            if text:
                self.chat_input.setText(text)
                self.chat_input.setFocus()

    # ---- Embedded PDF Manual Viewer in Page 4 ---------------------------------
    def ev_load_manual(self, manual_id, page=1):
        self.manual_id = manual_id
        minfo = db.get_manual(manual_id)
        if not minfo or not minfo.get("file_path") or not os.path.isfile(minfo["file_path"]):
            self.view.ev_manual_lbl.setText("No manual PDF found")
            return

        self.view.ev_manual_lbl.setText(minfo["name"])
        try:
            self.ev_doc = fitz.open(minfo["file_path"])
            self.ev_total_pages = len(self.ev_doc)
            self.view.ev_page_spin.setMaximum(self.ev_total_pages)
            self.view.ev_total_lbl.setText(f"of {self.ev_total_pages}")
            self.ev_populate_toc()
            self.ev_render_page(page)
        except Exception as e:
            self.view.ev_page_lbl.setText(f"Could not load PDF: {e}")

    def ev_populate_toc(self):
        if not self.ev_doc:
            return
        toc = self.ev_doc.get_toc()
        self.view.ev_toc_tree.clear()
        if not toc:
            root = QTreeWidgetItem(["Document Pages"])
            for p in range(1, min(self.ev_total_pages + 1, 100)):
                item = QTreeWidgetItem([f"Page {p}"])
                item.setData(0, Qt.ItemDataRole.UserRole, p)
                root.addChild(item)
            self.view.ev_toc_tree.addTopLevelItem(root)
            root.setExpanded(True)
            return

        stack = [self.view.ev_toc_tree.invisibleRootItem()]
        for item in toc:
            lvl, title, pno = item
            node = QTreeWidgetItem([f"{title} (p. {pno})"])
            node.setData(0, Qt.ItemDataRole.UserRole, pno)
            while len(stack) > lvl:
                stack.pop()
            stack[-1].addChild(node)
            stack.append(node)
        self.view.ev_toc_tree.expandToDepth(1)

    def ev_render_page(self, page_num):
        if not self.ev_doc or self.ev_total_pages == 0:
            return
        self.ev_current_page = max(1, min(page_num, self.ev_total_pages))
        self.view.ev_page_spin.blockSignals(True)
        self.view.ev_page_spin.setValue(self.ev_current_page)
        self.view.ev_page_spin.blockSignals(False)

        self.view.ev_prev_btn.setEnabled(self.ev_current_page > 1)
        self.view.ev_next_btn.setEnabled(self.ev_current_page < self.ev_total_pages)
        self.view.ev_zoom_lbl.setText(f"{int(self.ev_zoom * 100)}%")

        try:
            page = self.ev_doc[self.ev_current_page - 1]
            matrix = fitz.Matrix(self.ev_zoom, self.ev_zoom)
            pix = page.get_pixmap(matrix=matrix)
            qimg = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format.Format_RGB888)
            pm = QPixmap.fromImage(qimg)
            self.view.ev_page_lbl.setPixmap(pm)
            self.view.ev_page_lbl.setFixedSize(pm.size())
            self.view.ev_scroll.verticalScrollBar().setValue(0)
        except Exception as e:
            self.view.ev_page_lbl.setText(f"Error rendering page: {e}")

    def ev_jump_page(self, pno):
        self.ev_render_page(pno)

    def ev_prev_page(self):
        if self.ev_current_page > 1:
            self.ev_render_page(self.ev_current_page - 1)

    def ev_next_page(self):
        if self.ev_current_page < self.ev_total_pages:
            self.ev_render_page(self.ev_current_page + 1)

    def ev_zoom_in(self):
        self.ev_zoom = min(3.0, round(self.ev_zoom + 0.25, 2))
        self.ev_render_page(self.ev_current_page)

    def ev_zoom_out(self):
        self.ev_zoom = max(0.5, round(self.ev_zoom - 0.25, 2))
        self.ev_render_page(self.ev_current_page)

    def ev_fit_width(self):
        if not self.ev_doc or self.ev_total_pages == 0:
            return
        avail_w = self.view.ev_scroll.viewport().width() - 32
        page = self.ev_doc[self.ev_current_page - 1]
        orig_w = page.rect.width
        if orig_w > 0:
            self.ev_zoom = round(avail_w / orig_w, 2)
            self.ev_render_page(self.ev_current_page)

    def ev_on_toc_clicked(self, item, col):
        pno = item.data(0, Qt.ItemDataRole.UserRole)
        if pno:
            self.ev_render_page(int(pno))

    def ev_search_text(self):
        query = self.view.ev_search_input.text().strip()
        if not query or not self.ev_doc:
            return
        self.view.ev_search_list.clear()
        matches = []
        q_lower = query.lower()
        for pno in range(len(self.ev_doc)):
            txt = self.ev_doc[pno].get_text("text")
            if q_lower in txt.lower():
                idx = txt.lower().find(q_lower)
                start = max(0, idx - 30)
                end = min(len(txt), idx + 70)
                snippet = txt[start:end].replace("\n", " ").strip()
                matches.append((pno + 1, snippet))
                if len(matches) >= 25:
                    break

        if matches:
            for pno, snip in matches:
                item = QListWidgetItem(f"p. {pno}: ...{snip}...")
                item.setData(Qt.ItemDataRole.UserRole, pno)
                self.view.ev_search_list.addItem(item)
            self.ev_render_page(matches[0][0])
        else:
            QMessageBox.information(self, "Search", f"No matches found for '{query}'.")

    def ev_on_search_clicked(self, item):
        pno = item.data(Qt.ItemDataRole.UserRole)
        if pno:
            self.ev_render_page(int(pno))

    def ev_open_external(self):
        if self.manual_id:
            m = db.get_manual(self.manual_id)
            if m and m.get("file_path") and os.path.isfile(m["file_path"]):
                try:
                    os.startfile(m["file_path"])
                except Exception as e:
                    QMessageBox.warning(self, "Viewer", f"Could not launch external viewer:\n{e}")

    def open_user_manual(self, page_number=None):
        """Open User Manual viewer Dialog or navigate to Page 4."""
        if not self.manual_id:
            manuals = db.list_manuals()
            if manuals:
                self.manual_id = manuals[0]["id"]
            else:
                self.navigate_to(3)
                return

        dlg = UserManualDialog(self, manual_id=self.manual_id, initial_page=page_number or 1)
        dlg.exec()

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
        self.navigate_to(1)

    def default_questions(self, mid=None):
        return [
            "What is an Integrated Circuit (IC) and how does it work?",
            "How do I determine resistor values from color bands?",
            "What is the difference between NPN and PNP transistors?",
            "How do I wire an NE555 timer in Astable mode?",
            "What voltage regulator should I use to step down 12V to 5V?",
            "How does an ultrasonic distance sensor measure flight time?",
            "What safety precautions prevent electrostatic discharge (ESD)?"
        ]
