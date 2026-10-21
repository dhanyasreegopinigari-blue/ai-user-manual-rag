"""UI View layer: Styles, Custom Widgets, Dialogs, and Page Layouts."""
import os
import time
import cv2

from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt6.QtGui import QAction, QImage, QPainter, QPixmap
from PyQt6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QDialog, QFileDialog, QFormLayout, QFrame,
    QGridLayout, QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QMenu, QMessageBox, QProgressBar, QPushButton, QScrollArea, QSizePolicy,
    QSpinBox, QSplitter, QStackedWidget, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget
)
import database as db
import services.export as export_mod
try:
    import pymupdf as fitz
except ImportError:
    import fitz

import config

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
QProgressBar#voiceMeter { background:#161a23; border:1px solid #2a3449; border-radius:6px; height:12px; }
QProgressBar#voiceMeter::chunk { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4f8cff, stop:0.8 #45d48b, stop:1 #2fdc71); border-radius:5px; }
QFrame#sidebarFrame { background:#141722; border-right:1px solid #232b3b; }
QFrame#userBubble { background:#1e3250; border:1px solid #2d4873; border-radius:14px; }
QFrame#asstCard { background:#181e2b; border:1px solid #283347; border-radius:16px; }
QFrame#typingCard { background:#151b26; border:1px dashed #34425d; border-radius:12px; }
QTreeWidget { background:#171c26; border:1px solid #283347; border-radius:8px; outline:0; color:#c9d3e8; }
QTreeWidget::item { padding:5px 4px; border-radius:4px; }
QTreeWidget::item:hover { background:#242c3d; }
QTreeWidget::item:selected { background:#304060; color:#ffffff; }
QSpinBox { background:#1b202b; border:1px solid #333b4f; border-radius:8px; padding:6px 8px; color:#ffffff; }
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
        import services.rag as rag
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


class VoiceRecordWorker(QThread):
    level = pyqtSignal(int)
    speech_started = pyqtSignal()
    status = pyqtSignal(str)
    transcription_done = pyqtSignal(str)
    failed = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.recorder = None
        self.should_stop = False
        self.cancelled = False

    def run(self):
        try:
            import services.voice as voice
            self.recorder = voice.AudioRecorder()
            self.recorder.start(level_callback=self.level.emit)
            self.status.emit("Listening... speak now")

            start_t = time.time()
            max_sec = getattr(config, "VOICE_SECONDS", 15)
            speech_announced = False

            while not self.should_stop and not self.cancelled:
                self.msleep(50)
                if self.recorder.speech_detected and not speech_announced:
                    speech_announced = True
                    self.speech_started.emit()

                if self.recorder.should_auto_stop():
                    break
                if time.time() - start_t >= max_sec:
                    break

            if self.cancelled:
                if self.recorder:
                    self.recorder.stop()
                return

            self.status.emit("Transcribing your question...")
            audio = self.recorder.stop() if self.recorder else None

            text = voice.transcribe_audio(audio, progress=self.status.emit)
            self.transcription_done.emit(text)
        except Exception as e:
            if not self.cancelled:
                self.failed.emit(str(e))

    def finish_recording(self):
        self.should_stop = True

    def abort(self):
        self.cancelled = True
        self.should_stop = True
        if self.recorder:
            try:
                self.recorder.stop()
            except Exception:
                pass


class VoiceInputDialog(QDialog):
    """Voice input dialog with live volume meter and Whisper transcription."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Voice Question Input")
        self.setFixedSize(480, 260)
        self.transcribed_text = ""

        lay = QVBoxLayout(self)
        lay.setContentsMargins(28, 24, 28, 20)
        lay.setSpacing(16)

        header_lay = QHBoxLayout()
        mic_icon = QLabel("🎙")
        mic_icon.setStyleSheet("font-size:28px;")
        header_lay.addWidget(mic_icon)

        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        title_lbl = label("Voice Input", "h1", wrap=False)
        self.sub_lbl = label("Listening... Speak your question into the microphone.", "muted")
        title_box.addWidget(title_lbl)
        title_box.addWidget(self.sub_lbl)
        header_lay.addLayout(title_box)
        header_lay.addStretch()
        lay.addLayout(header_lay)

        self.meter = QProgressBar()
        self.meter.setObjectName("voiceMeter")
        self.meter.setRange(0, 100)
        self.meter.setValue(0)
        self.meter.setTextVisible(False)
        self.meter.setFixedHeight(14)
        lay.addWidget(self.meter)

        self.status_box = QLabel("Ready... Speak now. Will auto-transcribe when you pause.")
        self.status_box.setStyleSheet(
            "background:#151a24; border:1px solid #283347; border-radius:10px; "
            "padding:10px 14px; font-size:13.5px; color:#c9d1e3;"
        )
        self.status_box.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self.status_box)

        btn_row = QHBoxLayout()
        self.cancel_btn = button("Cancel", slot=self.reject)
        self.done_btn = button("✓ Done Speaking", "primary", slot=self.on_done_clicked)
        btn_row.addWidget(self.cancel_btn)
        btn_row.addStretch()
        btn_row.addWidget(self.done_btn)
        lay.addLayout(btn_row)

        self.worker = VoiceRecordWorker()
        self.worker.level.connect(self._on_level)
        self.worker.speech_started.connect(self._on_speech_started)
        self.worker.status.connect(self._on_status)
        self.worker.transcription_done.connect(self._on_transcribed)
        self.worker.failed.connect(self._on_failed)
        self.worker.start()

    def _on_level(self, val):
        self.meter.setValue(val)

    def _on_speech_started(self):
        self.status_box.setText("🎙 Hearing speech... (auto-finishing on pause)")
        self.status_box.setStyleSheet(
            "background:#15241b; border:1px solid #2d6a4f; border-radius:10px; "
            "padding:10px 14px; font-size:13.5px; color:#5fd38d; font-weight:600;"
        )

    def _on_status(self, text):
        self.sub_lbl.setText(text)
        if "Transcribing" in text:
            self.meter.setValue(0)
            self.status_box.setText("⏳ Transcribing speech with Whisper AI...")
            self.status_box.setStyleSheet(
                "background:#182033; border:1px solid #3b72db; border-radius:10px; "
                "padding:10px 14px; font-size:13.5px; color:#8ab4f8; font-weight:600;"
            )
            self.done_btn.setEnabled(False)
            self.done_btn.setText("Transcribing...")

    def _on_transcribed(self, text):
        self.transcribed_text = text
        self.accept()

    def _on_failed(self, err_msg):
        QMessageBox.warning(self, "Voice Recognition", err_msg)
        self.reject()

    def on_done_clicked(self):
        self.done_btn.setEnabled(False)
        self.done_btn.setText("Transcribing...")
        self.status_box.setText("Finishing recording & transcribing...")
        self.worker.finish_recording()

    def reject(self):
        if hasattr(self, "worker") and self.worker.isRunning():
            self.worker.abort()
            self.worker.wait(1000)
        super().reject()

    def closeEvent(self, event):
        if hasattr(self, "worker") and self.worker.isRunning():
            self.worker.abort()
            self.worker.wait(1000)
        super().closeEvent(event)


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



class UserManualDialog(QDialog):
    """Full-featured in-app manual viewer: TOC Outline, Full-text Search, and Zoom."""
    def __init__(self, parent=None, manual_id=None, initial_page=1):
        super().__init__(parent)
        self.manual_id = manual_id
        self.current_page = max(1, initial_page)
        self.zoom = 1.25
        self.doc = None
        self.total_pages = 0
        self.manual_info = db.get_manual(manual_id) if manual_id else None

        manual_title = self.manual_info["name"] if self.manual_info else "User Manual"
        self.setWindowTitle(f"📖 User Manual — {manual_title}")
        self.resize(1120, 800)

        main_lay = QVBoxLayout(self)
        main_lay.setContentsMargins(14, 12, 14, 12)
        main_lay.setSpacing(10)

        # Top Control Toolbar
        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)

        self.prev_btn = button("◀ Prev", slot=self.prev_page)
        self.next_btn = button("Next ▶", slot=self.next_page)
        toolbar.addWidget(self.prev_btn)
        toolbar.addWidget(self.next_btn)

        toolbar.addSpacing(10)
        toolbar.addWidget(label("Page:", "muted", wrap=False))
        self.page_spin = QSpinBox()
        self.page_spin.setMinimum(1)
        self.page_spin.setMaximum(1)
        self.page_spin.setValue(self.current_page)
        self.page_spin.valueChanged.connect(self._on_spin_changed)
        toolbar.addWidget(self.page_spin)

        self.total_lbl = label("of 1", "muted", wrap=False)
        toolbar.addWidget(self.total_lbl)

        toolbar.addSpacing(15)
        # Zoom buttons
        self.zoom_out_btn = button("–", slot=self.zoom_out)
        self.zoom_out_btn.setFixedWidth(36)
        self.zoom_lbl = label("125%", "caption", wrap=False)
        self.zoom_in_btn = button("+", slot=self.zoom_in)
        self.zoom_in_btn.setFixedWidth(36)
        self.fit_width_btn = button("Fit Width", slot=self.fit_width)
        toolbar.addWidget(self.zoom_out_btn)
        toolbar.addWidget(self.zoom_lbl)
        toolbar.addWidget(self.zoom_in_btn)
        toolbar.addWidget(self.fit_width_btn)

        toolbar.addStretch()

        # In-document search
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search in manual...")
        self.search_input.setFixedWidth(200)
        self.search_input.returnPressed.connect(self.search_manual)
        self.search_btn = button("Find", slot=self.search_manual)
        toolbar.addWidget(self.search_input)
        toolbar.addWidget(self.search_btn)

        toolbar.addSpacing(10)
        # Open external
        self.ext_btn = button("Open External", slot=self.open_external)
        toolbar.addWidget(self.ext_btn)

        self.close_btn = button("Close", slot=self.accept)
        toolbar.addWidget(self.close_btn)

        main_lay.addLayout(toolbar)

        # Splitter: Left = TOC & Search, Right = Page view
        splitter = QSplitter(Qt.Orientation.Horizontal)

        left_widget = QWidget()
        left_widget.setMinimumWidth(260)
        left_widget.setMaximumWidth(360)
        left_lay = QVBoxLayout(left_widget)
        left_lay.setContentsMargins(0, 0, 0, 0)
        left_lay.setSpacing(6)

        left_lay.addWidget(label("📑 DOCUMENT SECTIONS", "sectionHeader", wrap=False))
        self.toc_tree = QTreeWidget()
        self.toc_tree.setHeaderHidden(True)
        self.toc_tree.itemClicked.connect(self._on_toc_clicked)
        left_lay.addWidget(self.toc_tree, 2)

        self.search_res_header = label("🔍 SEARCH RESULTS", "sectionHeader", wrap=False)
        self.search_res_header.setVisible(False)
        left_lay.addWidget(self.search_res_header)
        self.search_list = QListWidget()
        self.search_list.itemClicked.connect(self._on_search_item_clicked)
        self.search_list.setVisible(False)
        left_lay.addWidget(self.search_list, 1)

        splitter.addWidget(left_widget)

        # Right Document Viewer (Scroll Area)
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("background:#0a0c10; border:1px solid #232b3a; border-radius:10px;")

        self.scroll_content = QWidget()
        self.scroll_content_lay = QVBoxLayout(self.scroll_content)
        self.scroll_content_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.scroll_content_lay.setContentsMargins(12, 12, 12, 12)

        self.page_lbl = QLabel()
        self.page_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.scroll_content_lay.addWidget(self.page_lbl)

        self.scroll_area.setWidget(self.scroll_content)
        splitter.addWidget(self.scroll_area)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 4)

        main_lay.addWidget(splitter, 1)

        self._load_document()

    def _load_document(self):
        if not self.manual_info or not self.manual_info.get("file_path"):
            self.page_lbl.setText("No manual PDF file is associated with this entry.")
            return

        path = self.manual_info["file_path"]
        if not os.path.isfile(path):
            self.page_lbl.setText("Manual PDF not found on disk:\n" + str(path))
            return

        try:
            self.doc = fitz.open(path)
            self.total_pages = len(self.doc)
            self.page_spin.setMaximum(self.total_pages)
            self.total_lbl.setText(f"of {self.total_pages}")
            self._populate_toc()
            self.render_page(self.current_page)
        except Exception as e:
            self.page_lbl.setText("Error reading PDF document:\n" + str(e))

    def _populate_toc(self):
        if not self.doc:
            return
        toc = self.doc.get_toc()
        self.toc_tree.clear()
        if not toc:
            root = QTreeWidgetItem(["Document Pages"])
            for p in range(1, min(self.total_pages + 1, 100)):
                item = QTreeWidgetItem([f"Page {p}"])
                item.setData(0, Qt.ItemDataRole.UserRole, p)
                root.addChild(item)
            self.toc_tree.addTopLevelItem(root)
            root.setExpanded(True)
            return

        stack = [self.toc_tree.invisibleRootItem()]
        for item in toc:
            lvl, title, pno = item
            node = QTreeWidgetItem([f"{title} (p. {pno})"])
            node.setData(0, Qt.ItemDataRole.UserRole, pno)
            node.setToolTip(0, f"Jump to page {pno}: {title}")
            while len(stack) > lvl:
                stack.pop()
            stack[-1].addChild(node)
            stack.append(node)
        self.toc_tree.expandToDepth(1)

    def render_page(self, page_num):
        if not self.doc or self.total_pages == 0:
            return
        self.current_page = max(1, min(page_num, self.total_pages))
        self.page_spin.blockSignals(True)
        self.page_spin.setValue(self.current_page)
        self.page_spin.blockSignals(False)

        self.prev_btn.setEnabled(self.current_page > 1)
        self.next_btn.setEnabled(self.current_page < self.total_pages)
        self.zoom_lbl.setText(f"{int(self.zoom * 100)}%")

        try:
            page = self.doc[self.current_page - 1]
            matrix = fitz.Matrix(self.zoom, self.zoom)
            pix = page.get_pixmap(matrix=matrix)
            qimg = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format.Format_RGB888)
            pm = QPixmap.fromImage(qimg)
            self.page_lbl.setPixmap(pm)
            self.page_lbl.setFixedSize(pm.size())
            self.scroll_area.verticalScrollBar().setValue(0)
        except Exception as e:
            self.page_lbl.setText(f"Error rendering page {self.current_page}:\n{e}")

    def jump_to_page(self, pno):
        self.render_page(pno)

    def prev_page(self):
        if self.current_page > 1:
            self.render_page(self.current_page - 1)

    def next_page(self):
        if self.current_page < self.total_pages:
            self.render_page(self.current_page + 1)

    def _on_spin_changed(self, val):
        self.render_page(val)

    def zoom_in(self):
        self.zoom = min(3.0, self.zoom + 0.25)
        self.render_page(self.current_page)

    def zoom_out(self):
        self.zoom = max(0.5, self.zoom - 0.25)
        self.render_page(self.current_page)

    def fit_width(self):
        avail_w = self.scroll_area.viewport().width() - 36
        if self.doc and avail_w > 100:
            page = self.doc[self.current_page - 1]
            orig_w = page.rect.width
            if orig_w > 0:
                self.zoom = round(avail_w / orig_w, 2)
                self.render_page(self.current_page)

    def _on_toc_clicked(self, item, col):
        pno = item.data(0, Qt.ItemDataRole.UserRole)
        if pno:
            self.render_page(int(pno))

    def search_manual(self):
        query = self.search_input.text().strip()
        if not query or not self.doc:
            return
        self.search_list.clear()
        matches = []
        q_lower = query.lower()
        for pno in range(len(self.doc)):
            page_text = self.doc[pno].get_text("text")
            if q_lower in page_text.lower():
                idx = page_text.lower().find(q_lower)
                start = max(0, idx - 40)
                end = min(len(page_text), idx + 80)
                snippet = page_text[start:end].replace("\n", " ").strip()
                matches.append((pno + 1, snippet))
                if len(matches) >= 30:
                    break

        if matches:
            self.search_res_header.setText(f"🔍 SEARCH RESULTS ({len(matches)} found)")
            self.search_res_header.setVisible(True)
            self.search_list.setVisible(True)
            for pno, snip in matches:
                item = QListWidgetItem(f"Page {pno}: ...{snip}...")
                item.setData(Qt.ItemDataRole.UserRole, pno)
                self.search_list.addItem(item)
            self.render_page(matches[0][0])
        else:
            QMessageBox.information(self, "Search Manual", f"No matches found for '{query}'.")

    def _on_search_item_clicked(self, item):
        pno = item.data(Qt.ItemDataRole.UserRole)
        if pno:
            self.render_page(int(pno))

    def open_external(self):
        if self.manual_info and self.manual_info.get("file_path"):
            path = self.manual_info["file_path"]
            if os.path.isfile(path):
                try:
                    os.startfile(path)
                except Exception as e:
                    QMessageBox.warning(self, "PDF Viewer", f"Could not launch external viewer:\n{e}")


class ChatMessageWidget(QWidget):
    """Visually distinct chat message card (User or Assistant)."""
    def __init__(self, role, content, data=None, created_at=None, parent_win=None):
        super().__init__()
        self.role = role
        self.content = content
        self.data = data
        self.created_at = created_at or time.strftime("%H:%M")
        self.win = parent_win

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 4, 0, 4)

        if self.role == "user":
            row = QHBoxLayout()
            row.addStretch()

            bubble = QFrame()
            bubble.setObjectName("userBubble")
            b_lay = QVBoxLayout(bubble)
            b_lay.setContentsMargins(16, 12, 16, 12)
            b_lay.setSpacing(6)

            head = QHBoxLayout()
            head.addWidget(label("👤 You", "badge"))
            head.addStretch()
            head.addWidget(label(self.created_at, "caption"))
            b_lay.addLayout(head)

            txt_lbl = QLabel(self.content)
            txt_lbl.setWordWrap(True)
            txt_lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            txt_lbl.setStyleSheet("color:#ffffff; font-size:15px; line-height:1.4;")
            b_lay.addWidget(txt_lbl)

            bubble.setMaximumWidth(700)
            row.addWidget(bubble)
            lay.addLayout(row)
        else:
            row = QHBoxLayout()
            card = QFrame()
            card.setObjectName("asstCard")
            c_lay = QVBoxLayout(card)
            c_lay.setContentsMargins(20, 16, 20, 16)
            c_lay.setSpacing(12)

            head = QHBoxLayout()
            head.addWidget(label("🤖 Manual Assistant", "sectionHeader", wrap=False))
            head.addStretch()
            head.addWidget(label(self.created_at, "caption"))
            c_lay.addLayout(head)

            title = (self.data or {}).get("title") if isinstance(self.data, dict) else ""
            if title:
                c_lay.addWidget(label(title.upper(), "h1"))

            summary = (self.data or {}).get("summary") if isinstance(self.data, dict) else ""
            if not summary and self.content:
                summary = self.content
            if summary:
                s_lbl = QLabel(summary)
                s_lbl.setWordWrap(True)
                s_lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
                s_lbl.setStyleSheet("color:#d6dce7; font-size:14.5px; line-height:1.5;")
                c_lay.addWidget(s_lbl)

            warning = (self.data or {}).get("warning") if isinstance(self.data, dict) else ""
            if warning:
                c_lay.addWidget(label(f"⚠️ WARNING: {warning}", "warning"))

            steps = (self.data or {}).get("steps") or [] if isinstance(self.data, dict) else []
            if steps:
                steps_box = QWidget()
                steps_box.setStyleSheet("background:transparent;")
                sb_lay = QVBoxLayout(steps_box)
                sb_lay.setContentsMargins(0, 6, 0, 6)
                sb_lay.setSpacing(10)

                for s in steps:
                    s_row = QHBoxLayout()
                    s_row.setSpacing(10)
                    s_num = label(f" {s.get('number', '')} ", "badge", wrap=False)
                    s_num.setStyleSheet("background:#2a4575; color:#8ab4f8; font-weight:700; border-radius:10px; padding:4px 8px;")
                    s_row.addWidget(s_num, alignment=Qt.AlignmentFlag.AlignTop)

                    s_text = QLabel(s.get("text", ""))
                    s_text.setWordWrap(True)
                    s_text.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
                    s_text.setStyleSheet("color:#ffffff; font-size:14.5px; line-height:1.4;")
                    s_row.addWidget(s_text, 1)

                    pg = s.get("page")
                    if pg and self.win:
                        pg_btn = button(f"📖 Page {pg}", "secondary", slot=lambda p=pg: self.win.open_user_manual(p))
                        pg_btn.setToolTip(f"Open manual at page {pg}")
                        s_row.addWidget(pg_btn, alignment=Qt.AlignmentFlag.AlignTop)

                    sb_lay.addLayout(s_row)
                c_lay.addWidget(steps_box)

            img_path = None
            if isinstance(self.data, dict):
                for s in steps:
                    if s.get("image") and os.path.isfile(s["image"]):
                        img_path = s["image"]
                        break

            if img_path:
                img_box = QFrame()
                img_box.setStyleSheet("background:#0d0f14; border:1px solid #283347; border-radius:10px; padding:10px;")
                ib_lay = QVBoxLayout(img_box)
                ib_lay.setSpacing(6)
                ib_lay.addWidget(label("📷 Matched Illustration from Manual:", "caption"))
                img_lbl = QLabel()
                img_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                pm = QPixmap(img_path)
                if not pm.isNull():
                    img_lbl.setPixmap(pm.scaled(380, 220, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
                ib_lay.addWidget(img_lbl)
                zoom_btn = button("🔍 Click to Zoom Illustration", slot=lambda p=img_path: ImagePreviewDialog(self.win, p).exec())
                ib_lay.addWidget(zoom_btn, alignment=Qt.AlignmentFlag.AlignCenter)
                c_lay.addWidget(img_box)

            actions_row = QHBoxLayout()
            actions_row.setSpacing(8)

            copy_btn = button("📋 Copy", "secondary", slot=self.copy_text)
            actions_row.addWidget(copy_btn)

            export_btn = button("📥 Export Answer ▼", "secondary")
            menu = QMenu(export_btn)
            act_pdf = menu.addAction("Export as PDF (.pdf)")
            act_pdf.triggered.connect(lambda: self.export_answer("pdf"))
            act_md = menu.addAction("Export as Markdown (.md)")
            act_md.triggered.connect(lambda: self.export_answer("md"))
            act_txt = menu.addAction("Export as Plain Text (.txt)")
            act_txt.triggered.connect(lambda: self.export_answer("txt"))
            export_btn.setMenu(menu)
            actions_row.addWidget(export_btn)

            actions_row.addStretch()
            c_lay.addLayout(actions_row)

            card.setMaximumWidth(780)
            row.addWidget(card)
            row.addStretch()
            lay.addLayout(row)

    def copy_text(self):
        text_to_copy = export_mod.format_answer_txt(self.data or {"answer": self.content})
        QApplication.clipboard().setText(text_to_copy)
        if self.win:
            QMessageBox.information(self.win, "Copied", "Answer text copied to clipboard!")

    def export_answer(self, fmt):
        if self.win:
            self.win.export_single_answer(self.data or {"answer": self.content}, fmt=fmt)


class MainView:
    """Pure View builder for MainWindow: creates pages, layouts, and widget hierarchies."""
    def __init__(self, window):
        self.win = window
        self.stack = QStackedWidget()

    def setup_ui(self):
        outer = QVBoxLayout(self.win)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(self.stack)

        self.home_page = self._build_home()
        self.library_page = self._build_library()
        self.busy_page = self._build_busy()
        self.result_page = self._build_result()
        self.ask_page = self._build_ask()
        self.viewer_page = self._build_viewer()
        self.chat_page = self._build_chat()

        for p in (self.home_page, self.library_page, self.busy_page, self.result_page,
                  self.ask_page, self.viewer_page, self.chat_page):
            self.stack.addWidget(p)

    def _page(self, margins=(40, 28, 40, 28)):
        p = QWidget()
        lay = QVBoxLayout(p)
        lay.setContentsMargins(*margins)
        lay.setSpacing(14)
        return p, lay

    def _header(self, title, back_slot):
        row = QHBoxLayout()
        row.addWidget(button("← Back", slot=back_slot))
        row.addStretch()
        row.addWidget(label(title, "h1"))
        row.addStretch()
        spacer = QWidget()
        spacer.setFixedWidth(90)
        row.addWidget(spacer)
        return row

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
        for text, slot in (("📷  Upload Photo", self.win.upload_photo),
                           ("🎥  Live Camera", self.win.open_camera),
                           ("🎬  Upload Video", self.win.upload_video)):
            b = button(text, "primary", slot)
            b.setMinimumSize(180, 52)
            row.addWidget(b)
        row.addStretch()
        lay.addLayout(row)
        row2 = QHBoxLayout()
        row2.addStretch()
        row2.addWidget(button("💬  Chat Assistant", "primary", slot=lambda: self.win.open_chat()))
        row2.addWidget(button("📖  User Manual", slot=lambda: self.win.open_user_manual()))
        row2.addWidget(button("📚  Manual Library", slot=self.win.open_library))
        row2.addWidget(button("⚙  Settings", slot=lambda: SettingsDialog(self.win).exec()))
        row2.addStretch()
        lay.addLayout(row2)
        lay.addStretch(3)
        return p

    def _build_busy(self):
        p, lay = self._page()
        lay.addStretch()
        self.busy_title = label("Working...", "h1", align=Qt.AlignmentFlag.AlignCenter)
        self.busy_detail = label("", "subtitle", align=Qt.AlignmentFlag.AlignCenter)
        self.busy_bar = QProgressBar()
        self.busy_bar.setRange(0, 0)
        self.busy_bar.setTextVisible(False)
        self.busy_bar.setMaximumWidth(420)
        lay.addWidget(self.busy_title)
        lay.addWidget(self.busy_detail)
        row = QHBoxLayout()
        row.addStretch()
        row.addWidget(self.busy_bar)
        row.addStretch()
        lay.addLayout(row)
        lay.addStretch()
        return p

    def _build_library(self):
        p, lay = self._page()
        lay.addLayout(self._header("MANUAL LIBRARY", lambda: self.win.go(self.home_page)))
        self.lib_search = QLineEdit()
        self.lib_search.setPlaceholderText("Search manuals...")
        self.lib_search.textChanged.connect(self.win.refresh_library)
        lay.addWidget(self.lib_search)
        self.lib_list = QListWidget()
        self.lib_list.itemDoubleClicked.connect(lambda _: self.win.use_selected_manual())
        lay.addWidget(self.lib_list, 1)
        self.lib_empty = label("No manuals yet. Click “+ Add Manual” to import a PDF.", "muted",
                               align=Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self.lib_empty)
        row = QHBoxLayout()
        row.addWidget(button("+ Add Manual", "primary", self.win.add_manual))
        row.addWidget(button("📖 View Manual", slot=self.win.view_selected_manual))
        row.addWidget(button("💬 Chat With Manual", "primary", slot=self.win.use_selected_manual))
        row.addStretch()
        row.addWidget(button("Delete", "danger", self.win.delete_selected))
        lay.addLayout(row)
        return p

    def _build_result(self):
        p, lay = self._page()
        lay.addLayout(self._header("HARDWARE FOUND", lambda: self.win.go(self.home_page)))

        # Photo / Frame preview area (supports side-by-side when matched with a manual image)
        self.img_row = QHBoxLayout()
        self.img_row.setSpacing(16)

        self.uploaded_box = QWidget()
        up_lay = QVBoxLayout(self.uploaded_box)
        up_lay.setContentsMargins(0, 0, 0, 0)
        up_lay.setSpacing(4)
        self.uploaded_caption = label("Uploaded Photo / Video Frame", "caption", align=Qt.AlignmentFlag.AlignCenter)
        up_lay.addWidget(self.uploaded_caption)
        self.hw_image = label("", "image", align=Qt.AlignmentFlag.AlignCenter)
        self.hw_image.setFixedHeight(240)
        up_lay.addWidget(self.hw_image)
        self.img_row.addWidget(self.uploaded_box, 1)

        self.matched_box = QWidget()
        mat_lay = QVBoxLayout(self.matched_box)
        mat_lay.setContentsMargins(0, 0, 0, 0)
        mat_lay.setSpacing(4)
        self.matched_caption = label("Matched Manual Illustration", "caption", align=Qt.AlignmentFlag.AlignCenter)
        mat_lay.addWidget(self.matched_caption)
        self.matched_hw_image = label("", "image", align=Qt.AlignmentFlag.AlignCenter)
        self.matched_hw_image.setFixedHeight(240)
        mat_lay.addWidget(self.matched_hw_image)
        self.img_row.addWidget(self.matched_box, 1)
        self.matched_box.setVisible(False)

        lay.addLayout(self.img_row)

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
        self.manual_combo.currentIndexChanged.connect(self.win._update_continue)
        lay.addWidget(self.manual_combo)
        lay.addStretch()
        row = QHBoxLayout()
        row.addWidget(button("📚 Manual Library", slot=self.win.open_library))
        row.addStretch()
        self.continue_btn = button("Continue →", "primary", self.win.continue_from_result)
        row.addWidget(self.continue_btn)
        lay.addLayout(row)
        return p

    def _build_ask(self):
        p, lay = self._page()
        lay.addLayout(self._header("ASK THE MANUAL", lambda: self.win.go(self.win.home_page)))
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
        self.q_input.returnPressed.connect(lambda: self.win.ask(self.q_input.text()))
        lay.addWidget(self.q_input)

        self.full_check = QCheckBox("Full end-to-end guide (reads many pages of the manual)")
        lay.addWidget(self.full_check)

        row = QHBoxLayout()
        self.speak_btn = button("🎤 Speak", slot=self.win.speak)
        row.addWidget(self.speak_btn)
        row.addStretch()
        self.ask_btn = button("ASK", "primary", lambda: self.win.ask(self.q_input.text()))
        row.addWidget(self.ask_btn)
        lay.addLayout(row)
        return p

    def _build_chat(self):
        """Build continuous chat interface with collapsible sidebar history and bottom input bar."""
        p = QWidget()
        main_h_lay = QHBoxLayout(p)
        main_h_lay.setContentsMargins(0, 0, 0, 0)
        main_h_lay.setSpacing(0)

        # -------------------------------------------------------------
        # LEFT: COLLAPSIBLE SIDEBAR
        # -------------------------------------------------------------
        self.chat_sidebar = QFrame()
        self.chat_sidebar.setObjectName("sidebarFrame")
        self.chat_sidebar.setFixedWidth(280)
        s_lay = QVBoxLayout(self.chat_sidebar)
        s_lay.setContentsMargins(14, 16, 14, 16)
        s_lay.setSpacing(10)

        # Sidebar top controls: + New Chat and Collapse button
        s_top = QHBoxLayout()
        self.new_chat_btn = button("＋ New Chat", "primary", slot=self.win.new_chat)
        self.new_chat_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        s_top.addWidget(self.new_chat_btn)

        self.collapse_sidebar_btn = button("◀", slot=self.win.toggle_sidebar)
        self.collapse_sidebar_btn.setFixedWidth(36)
        self.collapse_sidebar_btn.setToolTip("Collapse Sidebar")
        s_top.addWidget(self.collapse_sidebar_btn)
        s_lay.addLayout(s_top)

        # Export recent chats button
        self.export_recent_btn = button("📥 Export Recent Chats ▼", "secondary")
        recent_menu = QMenu(self.export_recent_btn)
        act_p = recent_menu.addAction("Export Recent as PDF (.pdf)")
        act_p.triggered.connect(lambda: self.win.export_recent_chats("pdf"))
        act_m = recent_menu.addAction("Export Recent as Markdown (.md)")
        act_m.triggered.connect(lambda: self.win.export_recent_chats("md"))
        act_t = recent_menu.addAction("Export Recent as Plain Text (.txt)")
        act_t.triggered.connect(lambda: self.win.export_recent_chats("txt"))
        self.export_recent_btn.setMenu(recent_menu)
        s_lay.addWidget(self.export_recent_btn)

        s_lay.addWidget(label("RECENT CHATS", "sectionHeader", wrap=False))

        # Conversations List
        self.chat_history_list = QListWidget()
        self.chat_history_list.setObjectName("historyList")
        self.chat_history_list.itemClicked.connect(self.win._on_history_item_clicked)
        s_lay.addWidget(self.chat_history_list, 1)

        self.sidebar_delete_btn = button("🗑 Delete Selected Chat", "danger", slot=self.win.delete_selected_conversation)
        s_lay.addWidget(self.sidebar_delete_btn)

        main_h_lay.addWidget(self.chat_sidebar)

        # -------------------------------------------------------------
        # RIGHT: MAIN CHAT AREA
        # -------------------------------------------------------------
        chat_area = QWidget()
        c_lay = QVBoxLayout(chat_area)
        c_lay.setContentsMargins(20, 14, 20, 14)
        c_lay.setSpacing(10)

        # Top Navigation Bar
        top_bar = QHBoxLayout()
        top_bar.setSpacing(10)

        self.expand_sidebar_btn = button("☰ Chats", slot=self.win.toggle_sidebar)
        self.expand_sidebar_btn.setVisible(False)
        top_bar.addWidget(self.expand_sidebar_btn)

        self.chat_manual_badge = label("📖 Active Manual: None", "h1", wrap=False)
        top_bar.addWidget(self.chat_manual_badge)
        top_bar.addStretch()

        self.chat_user_manual_btn = button("📖 User Manual", "primary", slot=lambda: self.win.open_user_manual())
        self.chat_user_manual_btn.setStyleSheet("font-weight:700; padding:8px 16px;")
        top_bar.addWidget(self.chat_user_manual_btn)

        self.chat_export_btn = button("📥 Export Chat ▼", "secondary")
        chat_menu = QMenu(self.chat_export_btn)
        c_act_p = chat_menu.addAction("Export Chat as PDF (.pdf)")
        c_act_p.triggered.connect(lambda: self.win.export_current_chat("pdf"))
        c_act_m = chat_menu.addAction("Export Chat as Markdown (.md)")
        c_act_m.triggered.connect(lambda: self.win.export_current_chat("md"))
        c_act_t = chat_menu.addAction("Export Chat as Plain Text (.txt)")
        c_act_t.triggered.connect(lambda: self.win.export_current_chat("txt"))
        self.chat_export_btn.setMenu(chat_menu)
        top_bar.addWidget(self.chat_export_btn)

        self.chat_library_btn = button("📚 Library", slot=self.win.open_library)
        top_bar.addWidget(self.chat_library_btn)

        self.chat_home_btn = button("🏠 Home", slot=lambda: self.win.go(self.home_page))
        top_bar.addWidget(self.chat_home_btn)

        c_lay.addLayout(top_bar)

        # Scrollable Chat Thread
        self.chat_scroll = QScrollArea()
        self.chat_scroll.setWidgetResizable(True)
        self.chat_scroll.setStyleSheet("background:#0f1218; border:1px solid #1f2736; border-radius:12px;")

        self.chat_thread_widget = QWidget()
        self.chat_thread_lay = QVBoxLayout(self.chat_thread_widget)
        self.chat_thread_lay.setContentsMargins(20, 16, 20, 16)
        self.chat_thread_lay.setSpacing(14)
        self.chat_thread_lay.addStretch()

        self.chat_scroll.setWidget(self.chat_thread_widget)
        c_lay.addWidget(self.chat_scroll, 1)

        # Typing Indicator Card
        self.typing_card = QFrame()
        self.typing_card.setObjectName("typingCard")
        t_lay = QHBoxLayout(self.typing_card)
        t_lay.setContentsMargins(16, 10, 16, 10)
        t_lay.setSpacing(10)
        t_icon = label("⏳", wrap=False)
        self.typing_lbl = label("Searching manual & generating answer...", "ok", wrap=False)
        t_lay.addWidget(t_icon)
        t_lay.addWidget(self.typing_lbl)
        t_lay.addStretch()
        self.typing_card.setVisible(False)
        c_lay.addWidget(self.typing_card)

        # Fixed Bottom Input Bar
        bottom_box = QFrame()
        bottom_box.setStyleSheet("background:#171c26; border:1px solid #283347; border-radius:12px; padding:6px;")
        b_lay = QVBoxLayout(bottom_box)
        b_lay.setContentsMargins(10, 8, 10, 8)
        b_lay.setSpacing(8)

        input_row = QHBoxLayout()
        input_row.setSpacing(8)
        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("💬 Type your question about this manual or ask a follow-up...")
        self.chat_input.returnPressed.connect(self.win.send_chat_message)
        input_row.addWidget(self.chat_input, 1)

        self.chat_speak_btn = button("🎤 Speak", slot=self.win.speak_chat)
        input_row.addWidget(self.chat_speak_btn)

        self.chat_send_btn = button("Send", "primary", slot=self.win.send_chat_message)
        self.chat_send_btn.setFixedWidth(80)
        input_row.addWidget(self.chat_send_btn)
        b_lay.addLayout(input_row)

        sub_row = QHBoxLayout()
        self.chat_full_check = QCheckBox("Full end-to-end guide (reads many pages of the manual)")
        sub_row.addWidget(self.chat_full_check)
        sub_row.addStretch()
        sub_hint = label("Press Enter to send • Conversation history is preserved for follow-ups", "caption")
        sub_row.addWidget(sub_hint)
        b_lay.addLayout(sub_row)

        c_lay.addWidget(bottom_box)

        main_h_lay.addWidget(chat_area, 1)
        return p

    def _build_viewer(self):
        p, lay = self._page(margins=(28, 16, 28, 20))
        lay.setSpacing(14)

        # Header row: Back button, Title, Open PDF
        header_row = QHBoxLayout()
        header_row.addWidget(button("← All Questions", slot=self.win.return_to_ask_page))
        header_row.addStretch()
        self.v_title = label("", "h1", wrap=False, align=Qt.AlignmentFlag.AlignCenter)
        header_row.addWidget(self.v_title)
        header_row.addStretch()
        self.open_pdf_btn = button("📖 Open Manual PDF", slot=self.win.open_current_pdf)
        header_row.addWidget(self.open_pdf_btn)
        lay.addLayout(header_row)

        # Quick question bar right on the answer screen
        quick_ask_row = QHBoxLayout()
        self.v_quick_input = QLineEdit()
        self.v_quick_input.setPlaceholderText("💬 Ask another question about this manual...")
        self.v_quick_input.returnPressed.connect(self.win.ask_from_viewer)
        self.v_speak_btn = button("🎤 Speak", slot=self.win.speak_viewer)
        self.v_quick_btn = button("Ask", "primary", slot=self.win.ask_from_viewer)
        quick_ask_row.addWidget(self.v_quick_input, 1)
        quick_ask_row.addWidget(self.v_speak_btn)
        quick_ask_row.addWidget(self.v_quick_btn)
        lay.addLayout(quick_ask_row)

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
        self.prev_btn = button("← Previous Step", slot=self.win.prev_step)
        self.next_btn = button("Next Step →", "primary", slot=self.win.next_step)
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
        self.zoom_btn = button("🔍 View Full Size", "secondary", slot=self.win.zoom_image)
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
