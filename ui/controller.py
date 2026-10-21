"""UI Controller layer: Business logic, worker orchestration, Q&A handling, and event coordination."""
import os
import traceback

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import QDialog, QFileDialog, QMessageBox, QWidget

import config
import database as db
import services.manual as manual_mod
import services.rag as rag
import services.voice as voice
from config import AppError
from ui.view import MainView, QuestionCard, MetaDialog, CameraDialog, ImagePreviewDialog, VoiceInputDialog, show_image


class Worker(QThread):
    """Runs fn(progress_callback) in a background thread so the GUI never freezes."""
    done = pyqtSignal(object)
    failed = pyqtSignal(str)
    progress = pyqtSignal(str)

    def __init__(self, fn):
        super().__init__()
        self.fn = fn

    def run(self):
        print("[WORKER] Started")
        try:
            result = self.fn(self.progress.emit)
            print("[WORKER] Function completed")
            print("[WORKER] Result:", repr(result)[:1000])
            self.done.emit(result)
            print("[WORKER] done signal emitted")
        except AppError as e:
            print("[WORKER] AppError:", str(e))
            self.failed.emit(str(e))
        except Exception as e:
            print("[WORKER] Unexpected exception:")
            traceback.print_exc()
            self.failed.emit(f"Unexpected error:\n{e}")


class MainWindow(QWidget):
    """Main window controller: connects user actions to business logic and background services."""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI User Manual")
        self.resize(1060, 780)
        self.setMinimumSize(880, 640)

        # State
        self._workers = []
        self.manual_id = None
        self.question_cache = {}
        self.answer = None
        self.step_i = 0
        self.hw_result = None

        # Build View
        self.view = MainView(self)
        self.view.setup_ui()

        # Expose view attributes for direct access and backward compatibility
        self.stack = self.view.stack
        self.home_page = self.view.home_page
        self.busy_page = self.view.busy_page
        self.library_page = self.view.library_page
        self.result_page = self.view.result_page
        self.ask_page = self.view.ask_page
        self.viewer_page = self.view.viewer_page

        self.busy_title = self.view.busy_title
        self.busy_detail = self.view.busy_detail
        self.busy_bar = self.view.busy_bar

        self.lib_search = self.view.lib_search
        self.lib_list = self.view.lib_list
        self.lib_empty = self.view.lib_empty

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

        self.ask_manual_name = self.view.ask_manual_name
        self.q_grid_host = self.view.q_grid_host
        self.q_grid = self.view.q_grid
        self.q_input = self.view.q_input
        self.speak_btn = getattr(self.view, "speak_btn", None)
        self.full_check = self.view.full_check

        self.v_title = self.view.v_title
        self.v_quick_input = self.view.v_quick_input
        self.v_speak_btn = getattr(self.view, "v_speak_btn", None)
        self.v_quick_btn = self.view.v_quick_btn
        self.v_step_badge = self.view.v_step_badge
        self.step_tabs_host = self.view.step_tabs_host
        self.step_tabs_lay = self.view.step_tabs_lay
        self.v_text = self.view.v_text
        self.v_answer = self.view.v_answer
        self.v_warning = self.view.v_warning
        self.prev_btn = self.view.prev_btn
        self.next_btn = self.view.next_btn
        self.v_img_badge = self.view.v_img_badge
        self.v_image = self.view.v_image
        self.v_caption = self.view.v_caption
        self.zoom_btn = self.view.zoom_btn
        self.ref_card = self.view.ref_card
        self.v_ref_badge = self.view.v_ref_badge
        self.v_source = self.view.v_source
        self.open_pdf_btn = self.view.open_pdf_btn
        self.v_step = self.view.v_step
        self.v_summary = self.view.v_summary

        self.go(self.home_page)

    # ---- Navigation & Worker execution ----------------------------------------
    def go(self, page):
        self.stack.setCurrentWidget(page)

    def run_task(self, fn, on_done, text="Working..."):
        """Run fn(progress_cb) in a background thread without freezing the GUI."""
        print("\n[RUN_TASK] Starting:", text)
        prev = self.stack.currentWidget()

        self.busy_title.setText(text)
        self.busy_detail.setText("")
        self.go(self.busy_page)

        w = Worker(fn)
        self._workers.append(w)
        w.progress.connect(self.busy_detail.setText)

        def ok(result):
            print("\n[RUN_TASK] DONE CALLBACK")
            print("[RUN_TASK] Result received:", repr(result)[:1000])
            try:
                on_done(result)
                print("[RUN_TASK] on_done completed")
            except Exception as e:
                print("[RUN_TASK] on_done FAILED")
                traceback.print_exc()
                QMessageBox.warning(self, "Problem", f"Unexpected error:\n{e}")
            if w in self._workers:
                self._workers.remove(w)

        def fail(msg):
            print("\n[RUN_TASK] FAILED:", msg)
            QMessageBox.warning(self, "Problem", msg)
            if w in self._workers:
                self._workers.remove(w)
            if self.stack.currentWidget() is self.busy_page:
                self.go(prev if prev is not self.busy_page else self.home_page)

        w.done.connect(ok)
        w.failed.connect(fail)
        w.start()

    # ---- Uploads --------------------------------------------------------------
    def upload_photo(self):
        path, _ = QFileDialog.getOpenFileName(self, "Choose a photo of your hardware", "",
                                              "Images (*.png *.jpg *.jpeg *.bmp *.webp *.tif *.tiff)")
        if path:
            self.run_task(lambda cb: manual_mod.analyze_photo(path, cb), self.show_hardware,
                          "Identifying hardware...")

    def open_camera(self):
        dlg = CameraDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted and dlg.captured_path:
            self.run_task(lambda cb: manual_mod.analyze_photo(dlg.captured_path, cb), self.show_hardware,
                          "Identifying hardware...")

    def upload_video(self):
        path, _ = QFileDialog.getOpenFileName(self, "Choose a video of your hardware", "",
                                              "Videos (*.mp4 *.mov *.avi *.mkv *.webm *.m4v)")
        if path:
            self.run_task(lambda cb: manual_mod.analyze_video(path, cb), self.show_hardware,
                          "Analyzing video...")

    # ---- Hardware Result ------------------------------------------------------
    def show_hardware(self, res):
        self.hw_result = res
        match_info = res.get("match_info") or {}
        source = match_info.get("source")
        matched_img = match_info.get("matched_image_path")

        # Handle visual match image comparison preview
        if source in ("visual_image", "visual_image_similar") and matched_img and os.path.isfile(matched_img):
            pno = match_info.get("page", "")
            pct = match_info.get("score_pct", 0)
            self.uploaded_caption.setVisible(True)
            self.matched_caption.setText(f"Matched Manual Image (Page {pno} · {pct}% Visual Match)")
            self.matched_box.setVisible(True)
            show_image(self.hw_image, res["preview"], 360, 240)
            show_image(self.matched_hw_image, matched_img, 360, 240)
        else:
            self.matched_box.setVisible(False)
            self.uploaded_caption.setVisible(False)
            if not show_image(self.hw_image, res["preview"], 700, 240):
                self.hw_image.setText("(image preview unavailable)")

        for k, lbl in self.hw_values.items():
            lbl.setText(res["hardware"].get(k) or "Unknown")

        exact, similar = res["exact"], res["similar"]
        exact_ids = [m["id"] for m in exact]
        similar_ids = [m["id"] for m in similar if m["id"] not in exact_ids]
        self.manual_combo.blockSignals(True)
        self.manual_combo.clear()
        if not exact:
            self.manual_combo.addItem("— choose a manual —", None)
        for m in db.list_manuals():
            mark = "✓ " if m["id"] in exact_ids else ("≈ " if m["id"] in similar_ids else "")
            self.manual_combo.addItem(f"{mark}{m['name']}", m["id"])
        pick = (exact_ids or [None])[0]
        if pick is not None:
            self.manual_combo.setCurrentIndex(self.manual_combo.findData(pick))
        self.manual_combo.blockSignals(False)

        if exact:
            self.match_status.setObjectName("ok")
            if source == "visual_image":
                self.match_status.setText("✓ Visual Match Found in Manual Images")
                pno = match_info.get("page")
                score = match_info.get("score_pct", 0)
                detail = f"Matching manual: {exact[0]['name']}"
                if pno:
                    detail += f"\nMatched illustration from manual on Page {pno} (Visual match: {score}%)"
                self.match_detail.setText(detail)
            else:
                self.match_status.setText("✓ Manual Found")
                self.match_detail.setText(f"Matching manual: {exact[0]['name']}")
        else:
            self.match_status.setObjectName("bad")
            self.match_status.setText("⚠ No matching manual found")
            msg = "No verified matching manual was found."
            if similar:
                if source == "visual_image_similar":
                    pno = match_info.get("page")
                    score = match_info.get("score_pct", 0)
                    msg += f"\n\nClosest visual manual image: {similar[0]['name']} (Page {pno}, ~{score}%)"
                else:
                    msg += "\n\nClosest by content (not verified): " + ", ".join(m["name"] for m in similar)
            self.match_detail.setText(msg)

        self.match_status.style().unpolish(self.match_status)
        self.match_status.style().polish(self.match_status)
        self._update_continue()
        self.go(self.result_page)

    def _update_continue(self, *_):
        self.continue_btn.setEnabled(self.manual_combo.currentData() is not None)

    def continue_from_result(self):
        mid = self.manual_combo.currentData()
        if mid is not None:
            self.open_manual(mid)

    # ---- Manual Library -------------------------------------------------------
    def open_library(self):
        self.refresh_library()
        self.go(self.library_page)

    def refresh_library(self, *_):
        self.lib_list.clear()
        manuals = db.list_manuals(self.lib_search.text())
        for m in manuals:
            item = QListWidgetItem(f"{m['name']}\n{m['manufacturer'] or '—'}  ·  "
                                   f"Model {m['model'] or '—'}  ·  {m['page_count']} pages")
            item.setData(Qt.ItemDataRole.UserRole, m["id"])
            self.lib_list.addItem(item)
        self.lib_empty.setVisible(not manuals)

    def _selected_id(self):
        item = self.lib_list.currentItem()
        if not item:
            QMessageBox.information(self, "Manual Library", "Please select a manual first.")
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
                      lambda _id: self.refresh_library(), "Importing manual...")

    def delete_selected(self):
        mid = self._selected_id()
        if mid is None:
            return
        if QMessageBox.question(self, "Delete manual",
                                "Delete this manual, its images and its search index?") \
                != QMessageBox.StandardButton.Yes:
            return
        manual_mod.delete_manual(mid)
        self.question_cache.pop(mid, None)
        self.refresh_library()

    def use_selected_manual(self):
        mid = self._selected_id()
        if mid is not None:
            self.open_manual(mid)

    # ---- Q&A / Ask the Manual -------------------------------------------------
    def default_questions(self, manual_id):
        """Fast fallback questions shown immediately while AI suggestions load."""
        m = db.get_manual(manual_id)
        manual_name = m["name"] if m else "this manual"
        return [
            f"What are the main features of {manual_name}?",
            "How do I install or set up this hardware?",
            "What are the important safety precautions?",
            "What are the specifications of this hardware?",
            "How do I troubleshoot common problems?",
            "How do I maintain this hardware?"
        ]

    def open_manual(self, manual_id):
        self.manual_id = manual_id

        # If AI-generated questions were already created, show them immediately.
        if manual_id in self.question_cache:
            self.show_ask(self.question_cache[manual_id])
            self.go(self.ask_page)
            return

        # Show the Ask page immediately using fast fallback questions.
        fallback = self.default_questions(manual_id)
        self.show_ask(fallback)
        self.go(self.ask_page)

        # Generate better AI questions in the background without blocking.
        self._generate_questions_background(manual_id)

    def _generate_questions_background(self, manual_id):
        """Generate AI questions without blocking the GUI."""
        def done(questions):
            # Make sure user is still working with the same manual
            if self.manual_id != manual_id:
                return

            if questions:
                self.question_cache[manual_id] = questions
                # If user is currently on the ask page, refresh the cards immediately
                if self.stack.currentWidget() is self.ask_page:
                    self.show_ask(questions)
                else:
                    # Silently update the grid in background without stealing active view
                    self._update_ask_grid(questions)

        def fail(_msg):
            print("AI question generation failed; keeping fallback questions.")

        self._workers = [w for w in self._workers if not w.isFinished()]
        worker = Worker(lambda cb: rag.generate_questions(manual_id, cb))
        self._workers.append(worker)
        worker.done.connect(done)
        worker.failed.connect(fail)
        worker.start()

    def _update_ask_grid(self, questions):
        """Safely populate suggested question cards and ensure they are visible."""
        m = db.get_manual(self.manual_id)
        self.ask_manual_name.setText(m["name"] if m else "")

        # Remove existing widgets from layout
        while self.q_grid.count():
            item = self.q_grid.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        # Add new cards and explicitly call show() on each
        for i, q in enumerate(questions):
            card = QuestionCard(q)
            card.clicked.connect(lambda _=False, q=q: self.ask(q))
            self.q_grid.addWidget(card, i // 2, i % 2)
            card.show()

    def show_ask(self, questions):
        """Populate questions on the ask page."""
        self._update_ask_grid(questions)
        self.q_input.clear()

    def return_to_ask_page(self):
        """Return to the Ask page, ensuring questions are always populated and visible."""
        if self.manual_id:
            qs = self.question_cache.get(self.manual_id) or self.default_questions(self.manual_id)
            self.show_ask(qs)
            self.go(self.ask_page)
        else:
            self.go(self.home_page)

    def speak(self):
        if not voice.is_available():
            QMessageBox.information(self, "Voice", voice.UNAVAILABLE)
            return

        dlg = VoiceInputDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted and getattr(dlg, "transcribed_text", None):
            text = dlg.transcribed_text.strip()
            if text:
                self.q_input.setText(text)
                self.q_input.setFocus()
                if self.manual_id:
                    self.go(self.ask_page)

    def speak_viewer(self):
        if not voice.is_available():
            QMessageBox.information(self, "Voice", voice.UNAVAILABLE)
            return

        dlg = VoiceInputDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted and getattr(dlg, "transcribed_text", None):
            text = dlg.transcribed_text.strip()
            if text:
                self.v_quick_input.setText(text)
                self.v_quick_input.setFocus()

    def ask(self, question):
        question = (question or "").strip()
        print("\n========== ASK DEBUG ==========")
        print("Question:", repr(question))
        print("Manual ID:", repr(self.manual_id))
        print("Full mode:", self.full_check.isChecked())
        print("================================")

        if not question:
            print("[ASK] Empty question - returning")
            return

        if self.manual_id is None:
            print("[ASK] ERROR: manual_id is None")
            QMessageBox.warning(
                self,
                "Manual not selected",
                "No manual is currently selected. Please go back and select the manual again."
            )
            return

        self.q_input.setText(question)
        mid = self.manual_id
        mode = "full" if self.full_check.isChecked() else "auto"

        print("[ASK] Starting answer task...")
        self.run_task(
            lambda cb: rag.answer_question(mid, question, cb, mode),
            self.show_answer,
            "Searching the manual..."
        )

    def ask_from_viewer(self):
        """Allow asking another question directly from the viewer page."""
        q = self.v_quick_input.text().strip()
        if q:
            self.v_quick_input.clear()
            self.ask(q)

    # ---- Answer / Step Viewer -------------------------------------------------
    def show_answer(self, ans):
        print("\n========== SHOW ANSWER ==========")
        print("Answer received:", repr(ans)[:1500])
        print("=================================")

        self.answer = ans
        self.step_i = 0
        self.render_step()
        self.go(self.viewer_page)

    def render_step(self):
        ans = self.answer or {}
        steps = ans.get("steps") or []
        self.v_title.setText((ans.get("title") or "ANSWER").upper())

        # When manual has no answer / nothing to show
        if not steps:
            self.v_step_badge.setText("Not in manual" if not ans.get("found") else "Overview")
            self.step_tabs_host.hide()
            self.v_text.setText(ans.get("summary") or "The manual does not contain this information.")
            ans_text = (ans.get("answer") or "").strip()
            if ans_text and ans_text != self.v_text.text():
                self.v_answer.setText(ans_text)
                self.v_answer.show()
            else:
                self.v_answer.hide()
            self.v_warning.hide()
            self.prev_btn.hide()
            self.next_btn.show()
            self.next_btn.setText("Back to Questions")
            self.v_image.set_image(None)
            self.v_img_badge.hide()
            self.v_caption.setText("")
            self.zoom_btn.hide()
            self.ref_card.hide()
            return

        total_steps = len(steps)
        self.step_i = max(0, min(self.step_i, total_steps - 1))
        s = steps[self.step_i]

        # 1. Update Step Badge
        self.v_step_badge.setText(f"Step {self.step_i + 1} of {total_steps}")
        self.v_step_badge.show()

        # 2. Update Step Tabs (Pills)
        while self.step_tabs_lay.count():
            item = self.step_tabs_lay.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        if total_steps > 1:
            self.step_tabs_host.show()
            for idx in range(total_steps):
                tab_btn = QuestionCard(f"Step {idx + 1}")
                tab_btn.setProperty("kind", "stepTabActive" if idx == self.step_i else "stepTab")
                tab_btn.clicked.connect(lambda _, step_idx=idx: self.go_to_step(step_idx))
                self.step_tabs_lay.addWidget(tab_btn)
                tab_btn.show()
            self.step_tabs_lay.addStretch()
        else:
            self.step_tabs_host.hide()

        # 3. Update Step Action / Instruction Text
        step_text = str(s.get("text") or "").strip()
        self.v_text.setText(f"Step {self.step_i + 1}: {step_text}" if total_steps > 1 else step_text)
        self.v_text.show()

        # 4. Update Answer Explanation Text
        ans_text = str(ans.get("answer") or ans.get("summary") or "").strip()
        if ans_text and ans_text.lower() != step_text.lower():
            self.v_answer.setText(ans_text)
            self.v_answer.show()
        else:
            self.v_answer.hide()

        # 5. Warning
        warning = str(s.get("warning") or ans.get("warning") or "").strip()
        if warning:
            self.v_warning.setText(f"⚠ WARNING\n{warning}")
            self.v_warning.show()
        else:
            self.v_warning.hide()

        # 6. Previous / Next buttons
        self.prev_btn.show()
        self.prev_btn.setEnabled(self.step_i > 0)
        self.next_btn.setText("Done ✓" if self.step_i == total_steps - 1 else "Next Step →")

        # 7. Update Image Panel (Right)
        image_path = s.get("image")
        page_num = s.get("page", "")
        image_kind = s.get("image_kind", "illustration")

        self.v_image.set_image(image_path)
        if page_num:
            kind_label = "Illustration" if image_kind == "illustration" else "Page Render"
            self.v_img_badge.setText(f"Page {page_num} · {kind_label}")
            self.v_img_badge.show()
            self.v_caption.setText(f"Manual Page {page_num} ({kind_label})")
        else:
            self.v_img_badge.hide()
            self.v_caption.setText("")

        self.zoom_btn.setVisible(bool(image_path and os.path.isfile(image_path)))

        # 8. Update Reference Panel (Bottom)
        source_text = str(s.get("source") or "").strip()
        m_name = ""
        if self.manual_id:
            m = db.get_manual(self.manual_id)
            if m:
                m_name = m.get("name") or ""

        ref_parts = []
        if page_num:
            ref_parts.append(f"Page {page_num}")
        if m_name:
            ref_parts.append(m_name[:40] + ("..." if len(m_name) > 40 else ""))
        self.v_ref_badge.setText(" · ".join(ref_parts))

        if source_text:
            self.v_source.setText(f"“{source_text}”")
            self.ref_card.show()
        elif page_num:
            self.v_source.setText(f"Reference from manual page {page_num}.")
            self.ref_card.show()
        else:
            self.ref_card.hide()

    def go_to_step(self, idx):
        steps = (self.answer or {}).get("steps") or []
        if 0 <= idx < len(steps):
            self.step_i = idx
            self.render_step()

    def zoom_image(self):
        img_path = self.v_image.get_image_path()
        if img_path and os.path.isfile(img_path):
            title = self.v_caption.text() or "Manual Illustration"
            ImagePreviewDialog(self, img_path, title).exec()

    def prev_step(self):
        if self.step_i > 0:
            self.step_i -= 1
            self.render_step()

    def next_step(self):
        steps = (self.answer or {}).get("steps") or []
        if steps and self.step_i < len(steps) - 1:
            self.step_i += 1
            self.render_step()
        else:
            self.return_to_ask_page()

    def open_current_pdf(self):
        if not self.manual_id:
            return
        m = db.get_manual(self.manual_id)
        if m and m.get("file_path") and os.path.isfile(m["file_path"]):
            try:
                os.startfile(m["file_path"])
            except Exception as e:
                QMessageBox.warning(self, "PDF Viewer", f"Could not open PDF file:\n{e}")
        else:
            QMessageBox.information(self, "PDF Viewer", "Original PDF file could not be found.")
