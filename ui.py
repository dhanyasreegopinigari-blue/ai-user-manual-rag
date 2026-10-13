"""PyQt6 GUI: Home, Manual Library, Hardware Result, Ask the Manual, Step Viewer (+ busy screen)."""
import os
import time
import traceback

import cv2
from PyQt6.QtCore import Qt, QThread, QTimer, pyqtSignal
from PyQt6.QtGui import QImage, QPainter, QPixmap
from PyQt6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QDialog, QFileDialog, QFormLayout, QFrame, QGridLayout, QHBoxLayout,
    QLabel, QLineEdit, QListWidget, QListWidgetItem, QMessageBox, QProgressBar, QPushButton,
    QScrollArea, QSizePolicy, QStackedWidget, QVBoxLayout, QWidget)

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
QPushButton[kind="secondary"] { background:#1f2636; border:1px solid #333f57; color:#c9d3e8; border-radius:8px; padding:7px 14px; font-size:13px; font-weight:600; }
QPushButton[kind="secondary"]:hover { background:#2a354c; color:white; border-color:#4f8cff; }
QPushButton[kind="stepTab"] { background:#1c2331; border:1px solid #2c364b; color:#9aa6bd; border-radius:7px; padding:5px 12px; font-weight:600; font-size:12px; }
QPushButton[kind="stepTab"]:hover { background:#273145; color:#ffffff; border-color:#4f8cff; }
QPushButton[kind="stepTabActive"] { background:#3b72db; border:1px solid #4f8cff; color:#ffffff; border-radius:7px; padding:5px 12px; font-weight:700; font-size:12px; }
QLineEdit, QComboBox { background:#1b202b; border:1px solid #333b4f; border-radius:10px; padding:9px 12px; }
QLineEdit:focus, QComboBox:focus { border-color:#4f8cff; }
QComboBox QAbstractItemView { background:#1b202b; selection-background-color:#2d3a5a; }
QListWidget { background:#1b202b; border:1px solid #2a3142; border-radius:12px; padding:6px; outline:0; }
QListWidget::item { padding:10px; border-radius:8px; }
QListWidget::item:selected { background:#2d3a5a; color:white; }
QFrame#card { background:#1b202b; border:1px solid #2a3142; border-radius:16px; }
QFrame#refCard { background:#151a24; border:1px solid #283347; border-left:5px solid #4f8cff; border-radius:14px; }
QLabel#title { font-size:36px; font-weight:700; letter-spacing:2px; }
QLabel#h1 { font-size:22px; font-weight:700; }
QLabel#subtitle { font-size:16px; color:#9aa4ba; }
QLabel#muted { color:#8791a8; }
QLabel#caption { color:#8791a8; font-size:12px; }
QLabel#stepText { font-size:17px; font-weight:600; color:#ffffff; line-height:1.4; }
QLabel#ok { color:#5fd38d; font-weight:600; font-size:16px; }
QLabel#bad { color:#ffcf6b; font-weight:600; font-size:16px; }
QLabel#source { background:#1b202b; border-left:4px solid #4f8cff; border-radius:8px; padding:10px 14px; color:#c9d1e3; }
QLabel#answerBox { background:#151a24; border:1px solid #283347; border-radius:12px; padding:14px 16px; font-size:14.5px; color:#d6dce7; line-height:1.5; }
QLabel#warning { background:#3a2c12; border:1px solid #8a6a1f; border-radius:10px; padding:10px 14px; color:#ffcf6b; font-size:13.5px; }
QLabel#image { background:#0d0f14; border:1px solid #2a3142; border-radius:12px; color:#8791a8; }
QLabel#imageContainer { background:#0d0f14; border:1px solid #252d3d; border-radius:12px; color:#8791a8; }
QLabel#sectionHeader { font-size:12px; font-weight:700; color:#6ea4ff; letter-spacing:1.2px; }
QLabel#badge { background:#21293b; color:#8ab4f8; border:1px solid #32405d; border-radius:6px; padding:3px 9px; font-size:12px; font-weight:600; }
QLabel#refHeader { font-size:12px; font-weight:700; color:#8ab4f8; letter-spacing:1px; }
QLabel#refText { font-size:13.5px; color:#c4cddb; font-style:italic; line-height:1.5; }
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


class CameraDialog(QDialog):
    """Live camera viewfinder to preview and capture hardware photos."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Live Camera Capture")
        self.resize(700, 560)
        self.captured_path = None
        self.cap = cv2.VideoCapture(0)

        lay = QVBoxLayout(self)
        self.view = QLabel("Starting camera...", self)
        self.view.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.view.setStyleSheet("background:#0d0f14; border-radius:12px;")
        self.view.setMinimumSize(640, 420)
        lay.addWidget(self.view)

        btn_row = QHBoxLayout()
        self.cancel_btn = button("Cancel", slot=self.reject)
        self.snap_btn = button("📸 Capture Photo", "primary", self.capture_frame)
        btn_row.addWidget(self.cancel_btn)
        btn_row.addStretch()
        btn_row.addWidget(self.snap_btn)
        lay.addLayout(btn_row)

        if not self.cap.isOpened():
            self.view.setText("No camera detected or camera is in use by another application.")
            self.snap_btn.setEnabled(False)
            return

        self.last_frame = None
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_frame)
        self.timer.start(33)

    def _update_frame(self):
        ret, frame = self.cap.read()
        if ret and frame is not None:
            self.last_frame = frame
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb.shape
            qimg = QImage(rgb.data, w, h, ch * w, QImage.Format.Format_RGB888)
            self.view.setPixmap(QPixmap.fromImage(qimg).scaled(
                self.view.width(), self.view.height(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation))

    def capture_frame(self):
        if self.last_frame is not None:
            config.ensure_dirs()
            dest = os.path.join(config.IMAGES_DIR, f"camera_snap_{int(time.time())}.jpg")
            cv2.imwrite(dest, self.last_frame)
            self.captured_path = dest
            self.accept()

    def closeEvent(self, event):
        self._cleanup()
        super().closeEvent(event)

    def reject(self):
        self._cleanup()
        super().reject()

    def accept(self):
        self._cleanup()
        super().accept()

    def _cleanup(self):
        if hasattr(self, "timer") and self.timer.isActive():
            self.timer.stop()
        if hasattr(self, "cap") and self.cap.isOpened():
            self.cap.release()


class ImagePreviewDialog(QDialog):
    """Full-size image dialog to inspect diagrams, schematics, and pinouts."""
    def __init__(self, parent, image_path, title="Manual Illustration"):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(960, 720)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(12)

        lbl = QLabel()
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet("background:#0d0f14; border-radius:12px;")
        pm = QPixmap(image_path) if image_path else QPixmap()
        if not pm.isNull():
            lbl.setPixmap(pm.scaled(920, 640, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        else:
            lbl.setText("Image could not be loaded.")

        lay.addWidget(lbl, 1)
        close_btn = button("Close", slot=self.accept)
        close_btn.setFixedWidth(120)
        lay.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignCenter)


class ImageViewerWidget(QLabel):
    """Smooth scaling image widget with aspect-ratio preservation and click-to-zoom."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setObjectName("imageContainer")
        self.setMinimumSize(280, 240)
        self._pixmap = QPixmap()
        self._image_path = None
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip("Click to view full size")

    def set_image(self, path):
        self._image_path = path
        if path and os.path.isfile(path):
            self._pixmap = QPixmap(path)
            self.setText("")
        else:
            self._pixmap = QPixmap()
            self.setText("No illustration available for this step.")
        self.update()

    def get_image_path(self):
        return self._image_path

    def paintEvent(self, event):
        if self._pixmap.isNull():
            super().paintEvent(event)
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        avail_w = max(self.width() - 16, 100)
        avail_h = max(self.height() - 16, 100)
        scaled = self._pixmap.scaled(
            avail_w, avail_h,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        x = (self.width() - scaled.width()) // 2
        y = (self.height() - scaled.height()) // 2
        painter.drawPixmap(x, y, scaled)

    def mousePressEvent(self, event):
        if self._image_path and os.path.isfile(self._image_path):
            ImagePreviewDialog(self.window(), self._image_path).exec()
        super().mousePressEvent(event)


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI User Manual")
        self.resize(1060, 780)
        self.setMinimumSize(880, 640)
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

            # Remove this worker after its result has been handled.
            if w in self._workers:
                self._workers.remove(w)

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
        for text, slot in (("📷  Upload Photo", self.upload_photo),
                           ("🎥  Live Camera", self.open_camera),
                           ("🎬  Upload Video", self.upload_video)):
            b = button(text, "primary", slot)
            b.setMinimumSize(180, 52)
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
        p, lay = self._page(margins=(28, 16, 28, 20))
        lay.setSpacing(14)

        # Header row: Back button, Title, Open PDF
        header_row = QHBoxLayout()
        header_row.addWidget(button("← Questions", slot=lambda: self.go(self.ask_page)))
        header_row.addStretch()
        self.v_title = label("", "h1", wrap=False, align=Qt.AlignmentFlag.AlignCenter)
        header_row.addWidget(self.v_title)
        header_row.addStretch()
        self.open_pdf_btn = button("📖 Open Manual PDF", slot=self.open_current_pdf)
        header_row.addWidget(self.open_pdf_btn)
        lay.addLayout(header_row)

        # Main 2-column layout: Left = Answer, Right = Image
        cols_row = QHBoxLayout()
        cols_row.setSpacing(16)

        # -------------------------------------------------------------
        # LEFT: ANSWER PANEL
        # -------------------------------------------------------------
        left_card = QFrame()
        left_card.setObjectName("card")
        left_lay = QVBoxLayout(left_card)
        left_lay.setContentsMargins(20, 18, 20, 18)
        left_lay.setSpacing(12)

        l_head = QHBoxLayout()
        l_head.addWidget(label("💡 ANSWER & INSTRUCTIONS", "sectionHeader", wrap=False))
        l_head.addStretch()
        self.v_step_badge = label("", "badge")
        l_head.addWidget(self.v_step_badge)
        left_lay.addLayout(l_head)

        # Step tabs / pills for jumping between steps
        self.step_tabs_host = QWidget()
        self.step_tabs_host.setStyleSheet("background:transparent;")
        self.step_tabs_lay = QHBoxLayout(self.step_tabs_host)
        self.step_tabs_lay.setContentsMargins(0, 0, 0, 0)
        self.step_tabs_lay.setSpacing(6)
        left_lay.addWidget(self.step_tabs_host)

        # Step instruction text (prominent)
        self.v_text = label("", "stepText")
        left_lay.addWidget(self.v_text)

        # Detailed answer / explanation text
        self.v_answer = label("", "answerBox")
        left_lay.addWidget(self.v_answer)

        # Warning box
        self.v_warning = label("", "warning")
        left_lay.addWidget(self.v_warning)

        left_lay.addStretch(1)

        # Navigation buttons row in left panel
        nav_row = QHBoxLayout()
        self.prev_btn = button("← Previous Step", slot=self.prev_step)
        self.next_btn = button("Next Step →", "primary", slot=self.next_step)
        nav_row.addWidget(self.prev_btn)
        nav_row.addStretch()
        nav_row.addWidget(self.next_btn)
        left_lay.addLayout(nav_row)

        cols_row.addWidget(left_card, stretch=5)

        # -------------------------------------------------------------
        # RIGHT: IMAGE PANEL
        # -------------------------------------------------------------
        right_card = QFrame()
        right_card.setObjectName("card")
        right_lay = QVBoxLayout(right_card)
        right_lay.setContentsMargins(20, 18, 20, 18)
        right_lay.setSpacing(12)

        r_head = QHBoxLayout()
        r_head.addWidget(label("📷 MANUAL ILLUSTRATION", "sectionHeader", wrap=False))
        r_head.addStretch()
        self.v_img_badge = label("", "badge")
        r_head.addWidget(self.v_img_badge)
        right_lay.addLayout(r_head)

        # High-definition image viewer
        self.v_image = ImageViewerWidget()
        right_lay.addWidget(self.v_image, 1)

        # Caption & zoom button row
        cap_row = QHBoxLayout()
        self.v_caption = label("", "caption")
        cap_row.addWidget(self.v_caption)
        cap_row.addStretch()
        self.zoom_btn = button("🔍 View Full Size", "secondary", slot=self.zoom_image)
        cap_row.addWidget(self.zoom_btn)
        right_lay.addLayout(cap_row)

        cols_row.addWidget(right_card, stretch=5)

        lay.addLayout(cols_row, 1)

        # -------------------------------------------------------------
        # BOTTOM: REFERENCE PANEL
        # -------------------------------------------------------------
        self.ref_card = QFrame()
        self.ref_card.setObjectName("refCard")
        ref_lay = QVBoxLayout(self.ref_card)
        ref_lay.setContentsMargins(18, 14, 18, 14)
        ref_lay.setSpacing(8)

        ref_head = QHBoxLayout()
        ref_head.addWidget(label("📑 REFERENCE FROM MANUAL", "refHeader", wrap=False))
        ref_head.addStretch()
        self.v_ref_badge = label("", "badge")
        ref_head.addWidget(self.v_ref_badge)
        ref_lay.addLayout(ref_head)

        self.v_source = label("", "refText")
        ref_lay.addWidget(self.v_source)

        lay.addWidget(self.ref_card)

        # Backward compatibility aliases
        self.v_step = self.v_step_badge
        self.v_summary = label("", "subtitle")

        scroll = QScrollArea()
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
                tab_btn = QPushButton(f"Step {idx + 1}")
                tab_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                tab_btn.setProperty("kind", "stepTabActive" if idx == self.step_i else "stepTab")
                tab_btn.clicked.connect(lambda _, step_idx=idx: self.go_to_step(step_idx))
                self.step_tabs_lay.addWidget(tab_btn)
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
            self.go(self.ask_page)   # finished: return to questions

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
