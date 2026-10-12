"""PyQt6 GUI: Home, Manual Library, Hardware Result, Ask the Manual, Step Viewer (+ busy screen)."""
import os
import traceback
from unittest import result

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QDialog, QFileDialog, QFormLayout, QFrame, QGridLayout, QHBoxLayout,
    QLabel, QLineEdit, QListWidget, QListWidgetItem, QMessageBox, QProgressBar, QPushButton,
    QScrollArea, QStackedWidget, QVBoxLayout, QWidget)

import config
import database as db
import manual as manual_mod
import rag
import voice
from config import AppError

STYLE = """
QWidget { background:#12151c; color:#e6e9ef; font-family:'Segoe UI','Inter','Helvetica Neue',Arial; font-size:14px; }
QLabel { background:transparent; }
QPushButton { background:#262c3a; border:1px solid #333b4f; border-radius:10px; padding:10px 18px; }
QPushButton:hover { background:#2f3748; }
QPushButton:disabled { color:#6b7385; background:#1b2029; border-color:#262c3a; }
QPushButton[kind="primary"] { background:#4f8cff; border:none; color:white; font-weight:600; }
QPushButton[kind="primary"]:hover { background:#6aa0ff; }
QPushButton[kind="primary"]:disabled { background:#2a3550; color:#7b86a3; }
QPushButton[kind="danger"] { background:#3a2025; border-color:#6a2f38; color:#ff9aa5; }
QPushButton[kind="card"] { text-align:left; border-radius:14px; background:#1b202b; border:1px solid #2a3142; }
QPushButton[kind="card"]:hover { border-color:#4f8cff; background:#212838; }
QLineEdit, QComboBox { background:#1b202b; border:1px solid #333b4f; border-radius:10px; padding:9px 12px; }
QLineEdit:focus, QComboBox:focus { border-color:#4f8cff; }
QComboBox QAbstractItemView { background:#1b202b; selection-background-color:#2d3a5a; }
QListWidget { background:#1b202b; border:1px solid #2a3142; border-radius:12px; padding:6px; outline:0; }
QListWidget::item { padding:10px; border-radius:8px; }
QListWidget::item:selected { background:#2d3a5a; color:white; }
QFrame#card { background:#1b202b; border:1px solid #2a3142; border-radius:16px; }
QLabel#title { font-size:36px; font-weight:700; letter-spacing:2px; }
QLabel#h1 { font-size:24px; font-weight:700; }
QLabel#subtitle { font-size:17px; color:#9aa4ba; }
QLabel#muted { color:#8791a8; }
QLabel#caption { color:#8791a8; font-size:12px; }
QLabel#stepText { font-size:19px; }
QLabel#ok { color:#5fd38d; font-weight:600; font-size:16px; }
QLabel#bad { color:#ffcf6b; font-weight:600; font-size:16px; }
QLabel#source { background:#1b202b; border-left:4px solid #4f8cff; border-radius:8px; padding:10px 14px; color:#c9d1e3; }
QLabel#answerBox { background:#1b202b; border:1px solid #2a3142; border-radius:12px; padding:12px 16px; font-size:16px; }
QLabel#warning { background:#3a2c12; border:1px solid #8a6a1f; border-radius:10px; padding:10px 14px; color:#ffcf6b; }
QLabel#image { background:#0d0f14; border:1px solid #2a3142; border-radius:12px; color:#8791a8; }
QProgressBar { background:#1b202b; border:none; border-radius:5px; height:10px; }
QProgressBar::chunk { background:#4f8cff; border-radius:5px; }
"""


def button(text, kind=None, slot=None):
    b = QPushButton(text)
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    if kind:
        b.setProperty("kind", kind)
    if slot:
        b.clicked.connect(slot)
    return b


def label(text="", name=None, wrap=True, align=None):
    l = QLabel(text)
    l.setWordWrap(wrap)
    if name:
        l.setObjectName(name)
    if align:
        l.setAlignment(align)
    return l


def show_image(lbl, path, w, h):
    """Show an image scaled into lbl. Returns True on success."""
    pm = QPixmap(path) if path else QPixmap()
    if pm.isNull():
        lbl.setPixmap(QPixmap())
        return False
    lbl.setPixmap(pm.scaled(w, h, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
    return True


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


class QuestionCard(QPushButton):
    """A clickable card with word-wrapped text (QPushButton itself cannot wrap)."""
    def __init__(self, text):
        super().__init__()
        self.setProperty("kind", "card")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(58)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 8, 14, 8)
        lbl = QLabel(text)
        lbl.setWordWrap(True)
        lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        lay.addWidget(lbl)


class MetaDialog(QDialog):
    """Asks for manual name / manufacturer / model when adding a PDF."""
    def __init__(self, parent, default_name):
        super().__init__(parent)
        self.setWindowTitle("Add Manual")
        self.setMinimumWidth(440)
        form = QFormLayout(self)
        self.name = QLineEdit(default_name)
        self.maker = QLineEdit()
        self.model = QLineEdit()
        self.model.setPlaceholderText("e.g. P-3000 (used to match hardware photos)")
        form.addRow("Manual name:", self.name)
        form.addRow("Manufacturer:", self.maker)
        form.addRow("Model:", self.model)
        row = QHBoxLayout()
        row.addStretch()
        row.addWidget(button("Cancel", slot=self.reject))
        row.addWidget(button("Import", "primary", self.accept))
        form.addRow(row)


class SettingsDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumWidth(460)
        form = QFormLayout(self)
        self.url = QLineEdit(config.OLLAMA_URL)
        self.vision = QLineEdit(config.VISION_MODEL)
        self.llm = QLineEdit(config.LLM_MODEL)
        self.embed = QLineEdit(config.EMBED_MODEL)
        form.addRow("Ollama URL:", self.url)
        form.addRow("Vision Model:", self.vision)
        form.addRow("LLM Model:", self.llm)
        form.addRow("Embedding Model:", self.embed)
        form.addRow(button("Test Ollama Connection", slot=self.test))
        row = QHBoxLayout()
        row.addStretch()
        row.addWidget(button("Cancel", slot=self.reject))
        row.addWidget(button("Save", "primary", self.save))
        form.addRow(row)

    def _apply(self):
        config.save_settings(self.url.text(), self.vision.text(), self.llm.text(), self.embed.text())

    def test(self):
        self._apply()
        ok, msg = rag.test_connection()
        (QMessageBox.information if ok else QMessageBox.warning)(self, "Ollama", msg)

    def save(self):
        self._apply()
        self.accept()


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI User Manual")
        self.resize(1000, 760)
        self._workers = []
        self.manual_id = None
        self.question_cache = {}
        self.answer = None
        self.step_i = 0
        self.hw_result = None

        self.stack = QStackedWidget()
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(self.stack)

        self.home_page = self._build_home()
        self.library_page = self._build_library()
        self.busy_page = self._build_busy()
        self.result_page = self._build_result()
        self.ask_page = self._build_ask()
        self.viewer_page = self._build_viewer()
        for p in (self.home_page, self.library_page, self.busy_page, self.result_page,
                  self.ask_page, self.viewer_page):
            self.stack.addWidget(p)
        self.go(self.home_page)

    # ---- helpers --------------------------------------------------------------
    def go(self, page):
        self.stack.setCurrentWidget(page)

    def _page(self, margins=(40, 28, 40, 28)):
        p = QWidget()
        lay = QVBoxLayout(p)
        lay.setContentsMargins(*margins)
        lay.setSpacing(14)
        return p, lay

    def _header(self, title, back_page):
        row = QHBoxLayout()
        row.addWidget(button("← Back", slot=lambda: self.go(back_page)))
        row.addStretch()
        row.addWidget(label(title, "h1"))
        row.addStretch()
        spacer = QWidget()
        spacer.setFixedWidth(90)
        row.addWidget(spacer)
        return row

    def run_task(self, fn, on_done, text="Working..."):
        """Run fn(progress_cb) in a background thread."""

        print("\n[RUN_TASK] Starting:", text)

        prev = self.stack.currentWidget()

        self.busy_title.setText(text)
        self.busy_detail.setText("")
        self.go(self.busy_page)

        w = Worker(fn)

        # Keep a strong reference to the worker until it finishes.
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

                QMessageBox.warning(
                    self,
                    "Problem",
                    f"Unexpected error:\n{e}"
                )

            finally:
                # Remove the completed worker.
                if w in self._workers:
                    self._workers.remove(w)

                # Leave the loading screen after the task finishes.
                if self.stack.currentWidget() is self.busy_page:
                    self.go(
                        prev if prev is not self.busy_page
                        else self.home_page
                    )

                print("[RUN_TASK] Loading screen cleanup completed")
        def fail(msg):
            print("\n[RUN_TASK] FAILED:", msg)

            QMessageBox.warning(
                self,
                "Problem",
                msg
            )

            if w in self._workers:
                self._workers.remove(w)

            if self.stack.currentWidget() is self.busy_page:
                self.go(
                    prev if prev is not self.busy_page
                    else self.home_page
                )

        w.done.connect(ok)
        w.failed.connect(fail)

        w.start()

    # ---- Home -----------------------------------------------------------------
    def _build_home(self):
        p, lay = self._page()
        lay.addStretch(2)
        lay.addWidget(label("AI USER MANUAL", "title", align=Qt.AlignmentFlag.AlignCenter))
        lay.addWidget(label("Intelligent Hardware Assistant", "subtitle", align=Qt.AlignmentFlag.AlignCenter))
        lay.addSpacing(18)
        lay.addWidget(label("Upload a photo or video of your hardware", "h1", align=Qt.AlignmentFlag.AlignCenter))
        lay.addWidget(label("Identify your hardware and get easy step-by-step instructions\n"
                            "directly from the manufacturer's manual.", "muted",
                            align=Qt.AlignmentFlag.AlignCenter))
        lay.addSpacing(18)
        row = QHBoxLayout()
        row.addStretch()
        for text, slot in (("📷  Upload Photo", self.upload_photo), ("🎬  Upload Video", self.upload_video)):
            b = button(text, "primary", slot)
            b.setMinimumSize(200, 52)
            row.addWidget(b)
        row.addStretch()
        lay.addLayout(row)
        row2 = QHBoxLayout()
        row2.addStretch()
        row2.addWidget(button("📚  Manual Library", slot=self.open_library))
        row2.addWidget(button("⚙  Settings", slot=lambda: SettingsDialog(self).exec()))
        row2.addStretch()
        lay.addLayout(row2)
        lay.addStretch(3)
        return p

    # ---- Busy -----------------------------------------------------------------
    def _build_busy(self):
        p, lay = self._page()
        lay.addStretch()
        self.busy_title = label("Working...", "h1", align=Qt.AlignmentFlag.AlignCenter)
        self.busy_detail = label("", "subtitle", align=Qt.AlignmentFlag.AlignCenter)
        bar = QProgressBar()
        bar.setRange(0, 0)           # indeterminate
        bar.setTextVisible(False)
        bar.setMaximumWidth(420)
        lay.addWidget(self.busy_title)
        lay.addWidget(self.busy_detail)
        row = QHBoxLayout()
        row.addStretch()
        row.addWidget(bar)
        row.addStretch()
        lay.addLayout(row)
        lay.addStretch()
        return p

    # ---- Upload ---------------------------------------------------------------
    def upload_photo(self):
        path, _ = QFileDialog.getOpenFileName(self, "Choose a photo of your hardware", "",
                                              "Images (*.png *.jpg *.jpeg *.bmp *.webp *.tif *.tiff)")
        if path:
            self.run_task(lambda cb: manual_mod.analyze_photo(path, cb), self.show_hardware,
                          "Identifying hardware...")

    def upload_video(self):
        path, _ = QFileDialog.getOpenFileName(self, "Choose a video of your hardware", "",
                                              "Videos (*.mp4 *.mov *.avi *.mkv *.webm *.m4v)")
        if path:
            self.run_task(lambda cb: manual_mod.analyze_video(path, cb), self.show_hardware,
                          "Analyzing video...")

    # ---- Library --------------------------------------------------------------
    def _build_library(self):
        p, lay = self._page()
        lay.addLayout(self._header("MANUAL LIBRARY", self.home_page))
        self.lib_search = QLineEdit()
        self.lib_search.setPlaceholderText("Search manuals...")
        self.lib_search.textChanged.connect(self.refresh_library)
        lay.addWidget(self.lib_search)
        self.lib_list = QListWidget()
        self.lib_list.itemDoubleClicked.connect(lambda _: self.use_selected_manual())
        lay.addWidget(self.lib_list, 1)
        self.lib_empty = label("No manuals yet. Click “+ Add Manual” to import a PDF.", "muted",
                               align=Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self.lib_empty)
        row = QHBoxLayout()
        row.addWidget(button("+ Add Manual", "primary", self.add_manual))
        row.addWidget(button("Ask This Manual", slot=self.use_selected_manual))
        row.addStretch()
        row.addWidget(button("Delete", "danger", self.delete_selected))
        lay.addLayout(row)
        return p

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

    # ---- Hardware result ------------------------------------------------------
    def _build_result(self):
        p, lay = self._page()
        lay.addLayout(self._header("HARDWARE FOUND", self.home_page))
        self.hw_image = label("", "image", align=Qt.AlignmentFlag.AlignCenter)
        self.hw_image.setFixedHeight(260)
        lay.addWidget(self.hw_image)

        card = QFrame()
        card.setObjectName("card")
        grid = QGridLayout(card)
        grid.setContentsMargins(20, 14, 20, 14)
        self.hw_values = {}
        for r, (key, cap) in enumerate((("manufacturer", "Manufacturer"), ("product_name", "Product"),
                                        ("model", "Model"), ("part_number", "Part number"),
                                        ("hardware_type", "Hardware type"))):
            grid.addWidget(label(cap, "caption"), r, 0)
            v = label("", wrap=False)
            self.hw_values[key] = v
            grid.addWidget(v, r, 1)
        lay.addWidget(card)

        self.match_status = label("", "ok")
        self.match_detail = label("", "muted")
        lay.addWidget(self.match_status)
        lay.addWidget(self.match_detail)
        self.manual_combo = QComboBox()
        self.manual_combo.currentIndexChanged.connect(self._update_continue)
        lay.addWidget(self.manual_combo)
        lay.addStretch()
        row = QHBoxLayout()
        row.addWidget(button("📚 Manual Library", slot=self.open_library))
        row.addStretch()
        self.continue_btn = button("Continue →", "primary", self.continue_from_result)
        row.addWidget(self.continue_btn)
        lay.addLayout(row)
        return p

    def show_hardware(self, res):
        self.hw_result = res
        if not show_image(self.hw_image, res["preview"], 700, 250):
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
        # order: exact matches first, then similar, handled by selecting the best one
        pick = (exact_ids or [None])[0]
        if pick is not None:
            self.manual_combo.setCurrentIndex(self.manual_combo.findData(pick))
        self.manual_combo.blockSignals(False)

        if exact:
            self.match_status.setObjectName("ok")
            self.match_status.setText("✓ Manual Found")
            self.match_detail.setText(f"Matching manual: {exact[0]['name']}")
        else:
            self.match_status.setObjectName("bad")
            self.match_status.setText("⚠ No matching manual found")
            msg = (
                "No verified matching manual was found.\n\n"
                "You can still ask questions about the uploaded image "
                "using General Image AI."
            )
            if similar:
                msg += "\n\nClosest by content (not verified): " + ", ".join(m["name"] for m in similar)
            self.match_detail.setText(msg)
        self.match_status.style().unpolish(self.match_status)
        self.match_status.style().polish(self.match_status)
        self._update_continue()
        self.go(self.result_page)

    def _update_continue(self, *_):
        self.continue_btn.setEnabled(
            self.manual_combo.currentData() is not None
        )

    def continue_from_result(self):
        mid = self.manual_combo.currentData()
        if mid is not None:
            self.open_manual(mid)

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

    # ---- General image AI -------------------------------------------------------


    # ---- Ask the manual -------------------------------------------------------
    def _build_ask(self):
        p, lay = self._page()
        lay.addLayout(self._header("ASK THE MANUAL", self.home_page))
        self.ask_manual_name = label("", "subtitle", align=Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self.ask_manual_name)
        lay.addWidget(label("Suggested Questions", "muted"))
        self.q_grid_host = QWidget()
        self.q_grid = QGridLayout(self.q_grid_host)
        self.q_grid.setContentsMargins(0, 0, 0, 0)
        self.q_grid.setSpacing(10)
        lay.addWidget(self.q_grid_host)
        lay.addStretch()
        lay.addWidget(label("Type your question:", "muted"))
        self.q_input = QLineEdit()
        self.q_input.setPlaceholderText("e.g. How do I replace the filter?")
        self.q_input.returnPressed.connect(lambda: self.ask(self.q_input.text()))
        lay.addWidget(self.q_input)
        self.full_check = QCheckBox("Full end-to-end guide (reads many pages of the manual)")
        lay.addWidget(self.full_check)
        row = QHBoxLayout()
        row.addWidget(button("🎤 Speak", slot=self.speak))
        row.addStretch()
        row.addWidget(button("ASK", "primary", lambda: self.ask(self.q_input.text())))
        lay.addLayout(row)
        return p

    def open_manual(self, manual_id):
        self.manual_id = manual_id

        # If AI-generated questions were already created, use them immediately.
        if manual_id in self.question_cache:
            self.show_ask(self.question_cache[manual_id])
            return

        # Show the Ask page immediately using fast fallback questions.
        fallback = self.default_questions(manual_id)
        self.show_ask(fallback)

        # Generate better AI questions in the background.
        self._generate_questions_background(manual_id)

    def _generate_questions_background(self, manual_id):
        """Generate AI questions without blocking the GUI."""

        def done(questions):
            # Make sure the user is still working with the same manual.
            if self.manual_id != manual_id:
                return

            if questions:
                self.question_cache[manual_id] = questions
                self.show_ask(questions)

        def fail(_msg):
            # AI suggestions are optional.
            # Keep the fallback questions already visible.
            print("AI question generation failed; keeping fallback questions.")

        self._workers = [w for w in self._workers if not w.isFinished()]

        worker = Worker(
            lambda cb: rag.generate_questions(manual_id, cb)
        )

        self._workers.append(worker)

        worker.done.connect(done)
        worker.failed.connect(fail)

        worker.start()

    def show_ask(self, questions):
        m = db.get_manual(self.manual_id)
        self.ask_manual_name.setText(m["name"] if m else "")
        while self.q_grid.count():
            w = self.q_grid.takeAt(0).widget()
            if w:
                w.deleteLater()
        for i, q in enumerate(questions):
            card = QuestionCard(q)
            card.clicked.connect(lambda _=False, q=q: self.ask(q))
            self.q_grid.addWidget(card, i // 2, i % 2)
        self.q_input.clear()
        self.go(self.ask_page)

    def speak(self):
        if not voice.is_available():
            QMessageBox.information(self, "Voice", voice.UNAVAILABLE)
            return

        def done(text):
            self.q_input.setText(text)
            self.go(self.ask_page)

        self.run_task(lambda cb: voice.listen(cb), done, "Listening...")

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
        print("[ASK] Manual:", mid)
        print("[ASK] Mode:", mode)

        self.run_task(
            lambda cb: rag.answer_question(mid, question, cb, mode),
            self.show_answer,
            "Searching the manual..."
        )

    # ---- Step viewer ----------------------------------------------------------
    def _build_viewer(self):
        p, lay = self._page()
        row = QHBoxLayout()
        row.addWidget(button("← Questions", slot=lambda: self.go(self.ask_page)))
        row.addStretch()
        lay.addLayout(row)
        self.v_title = label("", "h1", align=Qt.AlignmentFlag.AlignCenter)
        self.v_step = label("", "muted", align=Qt.AlignmentFlag.AlignCenter)
        self.v_summary = label("", "subtitle", align=Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self.v_title)
        lay.addWidget(self.v_summary)
        lay.addWidget(self.v_step)
        self.v_answer = label("", "answerBox")   # LLM-written sentences from the manual
        lay.addWidget(self.v_answer)
        self.v_image = label("", "image", align=Qt.AlignmentFlag.AlignCenter)
        self.v_image.setMinimumHeight(260)
        lay.addWidget(self.v_image, 1)
        self.v_caption = label("", "caption", align=Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self.v_caption)
        self.v_text = label("", "stepText", align=Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self.v_text)
        self.v_source = label("", "source")
        lay.addWidget(self.v_source)
        self.v_warning = label("", "warning")
        lay.addWidget(self.v_warning)
        row = QHBoxLayout()
        self.prev_btn = button("← Previous", slot=self.prev_step)
        self.next_btn = button("Next →", "primary", self.next_step)
        row.addWidget(self.prev_btn)
        row.addStretch()
        row.addWidget(self.next_btn)
        lay.addLayout(row)
        scroll = QScrollArea()          # long text never gets cut off
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidget(p)
        return scroll

    def show_answer(self, ans):
        print("\n========== SHOW ANSWER ==========")
        print("Answer received:", repr(ans)[:1500])
        print("=================================")

        self.answer = ans
        self.step_i = 0

        print("[SHOW_ANSWER] Calling render_step()...")
        self.render_step()

        print("[SHOW_ANSWER] Going to viewer page...")
        self.go(self.viewer_page)

        print("[SHOW_ANSWER] Viewer page opened")


    def render_step(self):
        ans = self.answer
        steps = ans["steps"]
        self.v_title.setText(ans["title"].upper())
        self.v_answer.setText(ans.get("answer") or ans.get("summary") or "")
        self.v_answer.setVisible(bool(self.v_answer.text()))
        self.v_summary.setText(ans.get("summary", ""))
        self.v_summary.setVisible(bool(ans.get("summary")) and bool(steps))
        self.v_source.hide()
        if not steps:   # manual has no answer / nothing to show
            self.v_step.setText("")
            self.v_image.clear()
            self.v_image.setText("The manual does not contain this information.")
            self.v_caption.setText("")
            self.v_text.setText(ans["summary"])
            self.v_warning.hide()
            self.prev_btn.hide()
            self.next_btn.setText("Done ✓")
            return
        s = steps[self.step_i]
        self.v_step.setText(f"Step {self.step_i + 1} of {len(steps)}")
        if show_image(self.v_image, s["image"], 760, 330):
            self.v_caption.setText(f"Manual page {s['page']}" if s["image_kind"] == "page"
                                   else f"Manual illustration · Page {s['page']}")
        else:
            self.v_image.setText("No illustration available for this step.")
            self.v_caption.setText(f"Page {s['page']}")
        self.v_text.setText(s["text"])
        self.v_source.setVisible(bool(s.get("source")))
        self.v_source.setText(f"From the manual (page {s['page']}):\n“{s.get('source', '')}”")
        warning = s.get("warning") or ans["warning"]
        self.v_warning.setVisible(bool(warning))
        self.v_warning.setText(f"⚠ WARNING\n{warning}")
        self.prev_btn.show()
        self.prev_btn.setEnabled(self.step_i > 0)
        self.next_btn.setText("Done ✓" if self.step_i == len(steps) - 1 else "Next →")

    def prev_step(self):
        if self.step_i > 0:
            self.step_i -= 1
            self.render_step()

    def next_step(self):
        if self.answer["steps"] and self.step_i < len(self.answer["steps"]) - 1:
            self.step_i += 1
            self.render_step()
        else:
            self.go(self.ask_page)   # finished: ask another question without restarting
