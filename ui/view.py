"""UI View layer: Modern Black & Green Cyber/Interstellar Theme, Glass Cards, and 4-Page System."""
import os
import time
import random
import cv2

from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QPointF
from PyQt6.QtGui import (
    QAction, QImage, QPainter, QPixmap, QFont, QColor, QRadialGradient,
    QLinearGradient, QBrush, QPen
)
from PyQt6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QDialog, QFileDialog, QFormLayout, QFrame,
    QGridLayout, QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QMenu, QMessageBox, QProgressBar, QPushButton, QScrollArea, QSizePolicy,
    QSpinBox, QSplitter, QStackedWidget, QTabWidget, QTextEdit, QTreeWidget,
    QTreeWidgetItem, QVBoxLayout, QWidget
)
import database as db
import services.export as export_mod
import services.components as comp_service
try:
    import pymupdf as fitz
except ImportError:
    import fitz

import config


DARK_STYLE = """
/* =========================================================================
   BLACK & GREEN (MATRIX / INTERSTELLAR) DARK THEME
   Deep obsidian space background, cyber green accents, glassmorphic panels
   ========================================================================= */
QWidget {
    background: transparent;
    color: #e6f4ea;
    font-family: 'Segoe UI', 'Inter', -apple-system, system-ui, sans-serif;
    font-size: 14px;
}
QLabel { background: transparent; }

/* Buttons */
QPushButton {
    background: rgba(12, 22, 16, 0.88);
    border: 1px solid #1c3d28;
    border-radius: 10px;
    padding: 9px 18px;
    color: #bbf7d0;
    font-weight: 600;
}
QPushButton:hover {
    background: rgba(18, 36, 25, 0.95);
    border-color: #22c55e;
    color: #ffffff;
}
QPushButton:pressed {
    background: #06180d;
}
QPushButton:disabled {
    color: #4b6353;
    background: rgba(8, 14, 10, 0.6);
    border-color: #122116;
}

/* Primary Green Button (Cyber / Terminal Green) */
QPushButton[kind="primary"] {
    background: #00e65c;
    border: 1px solid #00ff66;
    color: #031407;
    font-weight: 700;
    letter-spacing: 0.3px;
}
QPushButton[kind="primary"]:hover {
    background: #00ff66;
    border-color: #66ff99;
}
QPushButton[kind="primary"]:pressed {
    background: #00b347;
}
QPushButton[kind="primary"]:disabled {
    background: #0d2616;
    border-color: #133a22;
    color: #3b6b4e;
}

QPushButton[kind="secondary"] {
    background: rgba(9, 18, 13, 0.85);
    border: 1px solid #1a3824;
    color: #86efac;
    font-weight: 500;
}
QPushButton[kind="secondary"]:hover {
    background: #142a1c;
    color: #ffffff;
    border-color: #22c55e;
}

QPushButton[kind="danger"] {
    background: rgba(38, 16, 18, 0.85);
    border: 1px solid #572025;
    color: #fca5a5;
}
QPushButton[kind="danger"]:hover {
    background: #451b20;
    border-color: #ef4444;
    color: #fecaca;
}

/* Top Navigation Bar Buttons */
QPushButton[kind="nav"] {
    background: transparent;
    border: none;
    border-radius: 8px;
    padding: 8px 16px;
    color: #86efac;
    font-weight: 600;
    font-size: 14px;
}
QPushButton[kind="nav"]:hover {
    background: rgba(18, 42, 27, 0.6);
    color: #ffffff;
}
QPushButton[kind="navActive"] {
    background: #092916;
    border: 1px solid #22c55e;
    border-radius: 8px;
    padding: 8px 16px;
    color: #4ade80;
    font-weight: 700;
    font-size: 14px;
}

/* Category Filter Chips */
QPushButton[kind="chip"] {
    background: rgba(10, 20, 14, 0.8);
    border: 1px solid #193823;
    border-radius: 16px;
    padding: 6px 14px;
    color: #86efac;
    font-size: 13px;
    font-weight: 500;
}
QPushButton[kind="chip"]:hover {
    background: #152d1d;
    color: #ffffff;
    border-color: #22c55e;
}
QPushButton[kind="chipActive"] {
    background: #064e26;
    border: 1px solid #00ff66;
    border-radius: 16px;
    padding: 6px 14px;
    color: #86efac;
    font-size: 13px;
    font-weight: 700;
}

/* Dashboard Action Cards */
QPushButton[kind="cardAction"] {
    text-align: left;
    border-radius: 14px;
    background: rgba(9, 16, 12, 0.82);
    border: 1px solid #173321;
    padding: 16px;
    color: #e6f4ea;
}
QPushButton[kind="cardAction"]:hover {
    border-color: #00ff66;
    background: rgba(14, 28, 19, 0.92);
}

/* Inputs & Form Elements */
QLineEdit, QComboBox, QSpinBox {
    background: rgba(7, 13, 9, 0.9);
    border: 1px solid #1a3a24;
    border-radius: 10px;
    padding: 9px 12px;
    color: #f0fdf4;
    selection-background-color: #16a34a;
}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus {
    border-color: #00ff66;
    background: #09160e;
}
QComboBox QAbstractItemView {
    background: #07120a;
    border: 1px solid #1b3d26;
    selection-background-color: #15803d;
    selection-color: #ffffff;
}

/* Lists */
QListWidget {
    background: rgba(7, 13, 9, 0.88);
    border: 1px solid #193822;
    border-radius: 12px;
    padding: 6px;
    outline: 0;
}
QListWidget::item {
    padding: 10px 12px;
    border-radius: 8px;
    margin-bottom: 4px;
    color: #e6f4ea;
}
QListWidget::item:hover {
    background: #112618;
}
QListWidget::item:selected {
    background: #0f3d20;
    color: #ffffff;
    border: 1px solid #22c55e;
}

/* Glassmorphic Cards & Containers */
QFrame#card {
    background: rgba(9, 16, 12, 0.85);
    border: 1px solid #183623;
    border-radius: 14px;
}
QFrame#accentCard {
    background: rgba(6, 26, 14, 0.88);
    border: 1px solid #15803d;
    border-radius: 14px;
}
QFrame#tipCard {
    background: rgba(8, 15, 11, 0.85);
    border: 1px solid #163321;
    border-radius: 14px;
    padding: 12px;
}
QFrame#tipCard:hover {
    border-color: #00ff66;
    background: rgba(13, 26, 18, 0.92);
}
QFrame#sidebarFrame {
    background: rgba(6, 11, 8, 0.92);
    border-right: 1px solid #173321;
}

/* Chat Message Bubbles */
QFrame#userBubble {
    background: rgba(9, 36, 19, 0.92);
    border: 1px solid #166534;
    border-radius: 14px;
}
QFrame#asstCard {
    background: rgba(7, 14, 10, 0.94);
    border: 1px solid #1a3d25;
    border-radius: 16px;
}
QFrame#typingCard {
    background: rgba(6, 13, 9, 0.85);
    border: 1px dashed #22c55e;
    border-radius: 12px;
}

/* Typography & Labels */
QLabel#brand {
    font-size: 19px;
    font-weight: 800;
    color: #ffffff;
    letter-spacing: 0.5px;
}
QLabel#title {
    font-size: 26px;
    font-weight: 800;
    color: #ffffff;
    letter-spacing: 0.3px;
}
QLabel#h1 { font-size: 19px; font-weight: 700; color: #ffffff; }
QLabel#h2 { font-size: 15.5px; font-weight: 600; color: #bbf7d0; }
QLabel#subtitle { font-size: 14px; color: #86efac; }
QLabel#muted { color: #86a792; font-size: 13px; }
QLabel#caption { color: #6b8c77; font-size: 12px; }

/* Badges */
QLabel#badge {
    background: #092615;
    border: 1px solid #1b4d2b;
    border-radius: 8px;
    padding: 3px 8px;
    color: #86efac;
    font-size: 11.5px;
    font-weight: 600;
}
QLabel#badgeOk {
    background: #052e16;
    border: 1px solid #00ff66;
    border-radius: 8px;
    padding: 3px 8px;
    color: #00ff66;
    font-size: 11.5px;
    font-weight: 700;
}
QLabel#badgeWarn {
    background: #2b1f07;
    border: 1px solid #854d0e;
    border-radius: 8px;
    padding: 3px 8px;
    color: #fde047;
    font-size: 11.5px;
    font-weight: 600;
}

/* Code Blocks & Schematic Symbols (Phosphor Green Monospace) */
QLabel#codeBlock {
    background: #020503;
    border: 1px solid rgba(0, 255, 102, 0.3);
    border-radius: 8px;
    padding: 10px 14px;
    font-family: 'Cascadia Code', 'Consolas', 'Courier New', monospace;
    font-size: 12.5px;
    color: #00ff66;
    line-height: 1.4;
}

/* Sleek Scrollbars */
QScrollBar:vertical { background: #050a07; width: 10px; margin: 0; }
QScrollBar::handle:vertical { background: #183824; min-height: 24px; border-radius: 5px; margin: 2px; }
QScrollBar::handle:vertical:hover { background: #00ff66; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar:horizontal { background: #050a07; height: 10px; margin: 0; }
QScrollBar::handle:horizontal { background: #183824; min-width: 24px; border-radius: 5px; margin: 2px; }
QScrollBar::handle:horizontal:hover { background: #00ff66; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }

QProgressBar {
    background: #07130b;
    border: 1px solid #1a3824;
    border-radius: 6px;
    text-align: center;
}
QProgressBar::chunk {
    background: #00e65c;
    border-radius: 5px;
}

QTreeWidget {
    background: rgba(7, 13, 9, 0.9);
    border: 1px solid #1a3a24;
    border-radius: 10px;
    outline: 0;
    color: #e6f4ea;
}
QTreeWidget::item { padding: 6px; border-radius: 4px; }
QTreeWidget::item:hover { background: #112618; }
QTreeWidget::item:selected { background: #0f3d20; color: #ffffff; border: 1px solid #22c55e; }

QTabWidget::pane { border: 1px solid #1a3823; border-radius: 12px; background: rgba(7, 13, 9, 0.85); }
QTabBar::tab {
    background: rgba(8, 15, 11, 0.8);
    border: 1px solid #1a3823;
    border-bottom: none;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    padding: 8px 18px;
    margin-right: 4px;
    color: #86efac;
    font-weight: 600;
}
QTabBar::tab:selected { background: #092c18; color: #ffffff; border-color: #22c55e; }
QTabBar::tab:hover:!selected { background: #12281a; color: #e6f4ea; }
"""

LIGHT_STYLE = """
/* =========================================================================
   CLEAN WHITE & EMERALD GREEN LIGHT THEME
   Bright soft tech surfaces, matching signature green brand accents
   ========================================================================= */
QWidget {
    background: #f7faf8;
    color: #0f172a;
    font-family: 'Segoe UI', 'Inter', -apple-system, system-ui, sans-serif;
    font-size: 14px;
}
QLabel { background: transparent; }

QPushButton {
    background: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 10px;
    padding: 9px 18px;
    color: #0f172a;
    font-weight: 600;
}
QPushButton:hover {
    background: #f0fdf4;
    border-color: #22c55e;
    color: #15803d;
}
QPushButton:pressed { background: #dcfce7; }
QPushButton:disabled { color: #94a3b8; background: #f1f5f9; border-color: #e2e8f0; }

QPushButton[kind="primary"] {
    background: #16a34a;
    border: 1px solid #15803d;
    color: #ffffff;
    font-weight: 700;
}
QPushButton[kind="primary"]:hover {
    background: #15803d;
    border-color: #166534;
}
QPushButton[kind="primary"]:pressed { background: #14532d; }
QPushButton[kind="primary"]:disabled { background: #cbd5e1; color: #64748b; }

QPushButton[kind="secondary"] {
    background: #ffffff;
    border: 1px solid #bbf7d0;
    color: #15803d;
    font-weight: 600;
}
QPushButton[kind="secondary"]:hover {
    background: #f0fdf4;
    color: #166534;
    border-color: #22c55e;
}

QPushButton[kind="danger"] {
    background: #fee2e2;
    border: 1px solid #fca5a5;
    color: #b91c1c;
}
QPushButton[kind="danger"]:hover {
    background: #fecaca;
    border-color: #ef4444;
}

QPushButton[kind="nav"] {
    background: transparent;
    border: none;
    border-radius: 8px;
    padding: 8px 16px;
    color: #475569;
    font-weight: 600;
    font-size: 14px;
}
QPushButton[kind="nav"]:hover {
    background: #f0fdf4;
    color: #15803d;
}
QPushButton[kind="navActive"] {
    background: #dcfce7;
    border: 1px solid #22c55e;
    border-radius: 8px;
    padding: 8px 16px;
    color: #14532d;
    font-weight: 700;
    font-size: 14px;
}

QPushButton[kind="chip"] {
    background: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 16px;
    padding: 6px 14px;
    color: #475569;
    font-size: 13px;
    font-weight: 500;
}
QPushButton[kind="chip"]:hover {
    background: #f0fdf4;
    color: #16a34a;
    border-color: #86efac;
}
QPushButton[kind="chipActive"] {
    background: #16a34a;
    border: 1px solid #15803d;
    border-radius: 16px;
    padding: 6px 14px;
    color: #ffffff;
    font-size: 13px;
    font-weight: 700;
}

QPushButton[kind="cardAction"] {
    text-align: left;
    border-radius: 14px;
    background: #ffffff;
    border: 1px solid #e2e8f0;
    padding: 16px;
    color: #0f172a;
}
QPushButton[kind="cardAction"]:hover {
    border-color: #22c55e;
    background: #f0fdf4;
}

QLineEdit, QComboBox, QSpinBox {
    background: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 10px;
    padding: 9px 12px;
    color: #0f172a;
    selection-background-color: #22c55e;
}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus {
    border-color: #16a34a;
    background: #ffffff;
}
QComboBox QAbstractItemView {
    background: #ffffff;
    border: 1px solid #cbd5e1;
    selection-background-color: #dcfce7;
    selection-color: #14532d;
}

QListWidget {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 6px;
    outline: 0;
}
QListWidget::item {
    padding: 10px 12px;
    border-radius: 8px;
    margin-bottom: 4px;
    color: #0f172a;
}
QListWidget::item:hover { background: #f0fdf4; }
QListWidget::item:selected { background: #dcfce7; color: #14532d; border: 1px solid #22c55e; }

QFrame#card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 14px;
}
QFrame#accentCard {
    background: #f0fdf4;
    border: 1px solid #bbf7d0;
    border-radius: 14px;
}
QFrame#tipCard {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 14px;
    padding: 12px;
}
QFrame#tipCard:hover {
    border-color: #22c55e;
    background: #f0fdf4;
}
QFrame#sidebarFrame {
    background: #f8fafc;
    border-right: 1px solid #e2e8f0;
}

QFrame#userBubble {
    background: #dcfce7;
    border: 1px solid #86efac;
    border-radius: 14px;
}
QFrame#asstCard {
    background: #ffffff;
    border: 1px solid #bbf7d0;
    border-radius: 16px;
}
QFrame#typingCard {
    background: #f0fdf4;
    border: 1px dashed #22c55e;
    border-radius: 12px;
}

QLabel#brand { font-size: 19px; font-weight: 800; color: #0f172a; letter-spacing: 0.5px; }
QLabel#title { font-size: 26px; font-weight: 800; color: #0f172a; }
QLabel#h1 { font-size: 19px; font-weight: 700; color: #0f172a; }
QLabel#h2 { font-size: 15.5px; font-weight: 600; color: #166534; }
QLabel#subtitle { font-size: 14px; color: #475569; }
QLabel#muted { color: #64748b; font-size: 13px; }
QLabel#caption { color: #64748b; font-size: 12px; }

QLabel#badge {
    background: #f0fdf4;
    border: 1px solid #bbf7d0;
    border-radius: 8px;
    padding: 3px 8px;
    color: #15803d;
    font-size: 11.5px;
    font-weight: 600;
}
QLabel#badgeOk {
    background: #dcfce7;
    border: 1px solid #22c55e;
    border-radius: 8px;
    padding: 3px 8px;
    color: #14532d;
    font-size: 11.5px;
    font-weight: 700;
}
QLabel#badgeWarn {
    background: #fefce8;
    border: 1px solid #fef08a;
    border-radius: 8px;
    padding: 3px 8px;
    color: #854d0e;
    font-size: 11.5px;
    font-weight: 600;
}

QLabel#codeBlock {
    background: #f0fdf4;
    border: 1px solid #bbf7d0;
    border-radius: 8px;
    padding: 10px 14px;
    font-family: 'Cascadia Code', 'Consolas', 'Courier New', monospace;
    font-size: 12.5px;
    color: #15803d;
    line-height: 1.4;
}

QScrollBar:vertical { background: #f8fafc; width: 10px; margin: 0; }
QScrollBar::handle:vertical { background: #cbd5e1; min-height: 24px; border-radius: 5px; margin: 2px; }
QScrollBar::handle:vertical:hover { background: #16a34a; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar:horizontal { background: #f8fafc; height: 10px; margin: 0; }
QScrollBar::handle:horizontal { background: #cbd5e1; min-width: 24px; border-radius: 5px; margin: 2px; }
QScrollBar::handle:horizontal:hover { background: #16a34a; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }

QProgressBar { background: #f1f5f9; border: 1px solid #cbd5e1; border-radius: 6px; text-align: center; }
QProgressBar::chunk { background: #16a34a; border-radius: 5px; }

QTreeWidget { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 10px; outline: 0; color: #334155; }
QTreeWidget::item { padding: 6px; border-radius: 4px; }
QTreeWidget::item:hover { background: #f0fdf4; }
QTreeWidget::item:selected { background: #dcfce7; color: #14532d; border: 1px solid #22c55e; }

QTabWidget::pane { border: 1px solid #e2e8f0; border-radius: 12px; background: #ffffff; }
QTabBar::tab {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-bottom: none;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    padding: 8px 18px;
    margin-right: 4px;
    color: #475569;
    font-weight: 600;
}
QTabBar::tab:selected { background: #16a34a; color: #ffffff; border-color: #15803d; }
QTabBar::tab:hover:!selected { background: #f0fdf4; color: #15803d; }
"""

STYLE = DARK_STYLE


def button(text, kind=None, slot=None):
    b = QPushButton(text)
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    if kind:
        b.setProperty("kind", kind)
    if slot:
        b.clicked.connect(slot)
    return b


def label(text="", name=None, wrap=True, align=None):
    l = QLabel(str(text))
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


class SpaceBackgroundWidget(QWidget):
    """Subtle interstellar space background with soft nebulae and starfield for dark mode."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.is_dark = True
        self._cached_pixmap = None
        self._stars = self._generate_stars(130)

    def _generate_stars(self, count):
        rnd = random.Random(42)  # Stable deterministic seed
        stars = []
        for _ in range(count):
            x = rnd.random()
            y = rnd.random()
            sz = rnd.choice([1.0, 1.2, 1.5, 2.0, 2.5])
            bright = rnd.randint(70, 220)
            stars.append((x, y, sz, bright))
        return stars

    def set_theme(self, is_dark):
        self.is_dark = is_dark
        self._cached_pixmap = None
        self.update()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._cached_pixmap = None

    def paintEvent(self, event):
        painter = QPainter(self)
        if not self.is_dark:
            painter.fillRect(self.rect(), QColor("#f7faf8"))
            return

        w, h = self.width(), self.height()
        if self._cached_pixmap is None or self._cached_pixmap.size() != self.size():
            pm = QPixmap(self.size())
            p = QPainter(pm)
            p.setRenderHint(QPainter.RenderHint.Antialiasing)

            # 1. Base obsidian void
            p.fillRect(0, 0, w, h, QColor("#040705"))

            # 2. Soft Emerald Nebula 1 (Top Left)
            rad1 = max(w, h) * 0.65
            grad1 = QRadialGradient(w * 0.18, h * 0.18, rad1)
            grad1.setColorAt(0.0, QColor(0, 255, 102, 22))
            grad1.setColorAt(0.4, QColor(16, 185, 129, 12))
            grad1.setColorAt(1.0, QColor(4, 7, 5, 0))
            p.fillRect(0, 0, w, h, grad1)

            # 3. Soft Galaxy Nebula 2 (Bottom Right)
            rad2 = max(w, h) * 0.55
            grad2 = QRadialGradient(w * 0.82, h * 0.82, rad2)
            grad2.setColorAt(0.0, QColor(34, 197, 94, 18))
            grad2.setColorAt(0.5, QColor(6, 40, 20, 10))
            grad2.setColorAt(1.0, QColor(4, 7, 5, 0))
            p.fillRect(0, 0, w, h, grad2)

            # 4. Starfield
            for rx, ry, sz, br in self._stars:
                sx = int(rx * w)
                sy = int(ry * h)
                col = QColor(190, 255, 210, br) if br > 150 else QColor(220, 235, 225, br)
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(col)
                p.drawEllipse(sx, sy, int(sz), int(sz))

            p.end()
            self._cached_pixmap = pm

        painter.drawPixmap(0, 0, self._cached_pixmap)


class QuestionCard(QPushButton):
    """Clickable suggested question card."""
    def __init__(self, text):
        super().__init__()
        self.setProperty("kind", "secondary")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(54)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 8, 14, 8)
        lbl = QLabel(text)
        lbl.setWordWrap(True)
        lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        lay.addWidget(lbl)


class MetaDialog(QDialog):
    """Asks for manual metadata when importing a PDF."""
    def __init__(self, parent, default_name):
        super().__init__(parent)
        self.setWindowTitle("Import PDF Manual")
        self.setMinimumWidth(440)
        form = QFormLayout(self)
        self.name = QLineEdit(default_name)
        self.maker = QLineEdit()
        self.model = QLineEdit()
        self.model.setPlaceholderText("e.g. ESP32-WROOM / NE555 / MIO-2364")
        form.addRow("Manual name:", self.name)
        form.addRow("Manufacturer:", self.maker)
        form.addRow("Model:", self.model)
        row = QHBoxLayout()
        row.addStretch()
        row.addWidget(button("Cancel", slot=self.reject))
        row.addWidget(button("Import", "primary", self.accept))
        form.addRow(row)


class SettingsDialog(QDialog):
    """Settings dialog for Ollama, LLM provider, and model configurations."""
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("AI & Hardware Settings")
        self.setMinimumWidth(480)
        form = QFormLayout(self)
        form.setSpacing(12)

        self.provider_combo = QComboBox()
        self.provider_combo.addItems(["auto (Auto-detect from .env)", "gemini", "openai", "claude", "ollama"])
        idx = self.provider_combo.findText(config.LLM_PROVIDER, Qt.MatchFlag.MatchContains)
        if idx >= 0:
            self.provider_combo.setCurrentIndex(idx)

        self.url = QLineEdit(config.OLLAMA_URL)
        self.vision = QLineEdit(config.VISION_MODEL)
        self.llm = QLineEdit(config.LLM_MODEL)
        self.embed = QLineEdit(config.EMBED_MODEL)

        form.addRow("LLM Provider:", self.provider_combo)
        form.addRow("Local Ollama URL:", self.url)
        form.addRow("Vision Model:", self.vision)
        form.addRow("Local LLM Model:", self.llm)
        form.addRow("Embedding Model:", self.embed)
        form.addRow(button("⚡ Test Local Ollama Connection", slot=self.test))

        env_hint = label("💡 <i>To configure online Gemini, OpenAI, or Claude API keys, edit <b>.env</b> in the app folder.</i>", "caption")
        form.addRow(env_hint)

        row = QHBoxLayout()
        row.addStretch()
        row.addWidget(button("Cancel", slot=self.reject))
        row.addWidget(button("Save Settings", "primary", self.save))
        form.addRow(row)

    def _apply(self):
        sel_text = self.provider_combo.currentText().split()[0].lower()
        config.save_settings(self.url.text(), self.vision.text(), self.llm.text(), self.embed.text(), provider=sel_text)

    def test(self):
        self._apply()
        import services.rag as rag
        ok, msg = rag.test_connection()
        (QMessageBox.information if ok else QMessageBox.warning)(self, "Ollama Test", msg)

    def save(self):
        self._apply()
        self.accept()


class CameraDialog(QDialog):
    """Live camera viewfinder with device probe and fallback disk selector."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Live Camera Scanner")
        self.resize(720, 580)
        self.captured_path = None
        self.last_frame = None

        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(14)

        top_row = QHBoxLayout()
        top_row.addWidget(label("📷 Component Camera Scan", "h1"))
        top_row.addStretch()
        top_row.addWidget(label("Align IC or circuit board in frame", "caption"))
        lay.addLayout(top_row)

        self.view = QLabel("Initializing camera...", self)
        self.view.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.view.setStyleSheet("background:#040705; border:1px solid #173822; border-radius:12px; color:#86efac;")
        self.view.setMinimumSize(660, 420)
        lay.addWidget(self.view, 1)

        btn_row = QHBoxLayout()
        self.fallback_btn = button("📁 Choose Photo from Disk", "secondary", slot=self.choose_disk_photo)
        self.cancel_btn = button("Cancel", slot=self.reject)
        self.snap_btn = button("📸 Capture Photo", "primary", slot=self.capture_frame)
        self.snap_btn.setMinimumWidth(160)

        btn_row.addWidget(self.cancel_btn)
        btn_row.addWidget(self.fallback_btn)
        btn_row.addStretch()
        btn_row.addWidget(self.snap_btn)
        lay.addLayout(btn_row)

        self.cap = None
        for idx in (0, 1):
            c = cv2.VideoCapture(idx, cv2.CAP_DSHOW) if os.name == 'nt' else cv2.VideoCapture(idx)
            if c.isOpened():
                ret, test_f = c.read()
                if ret and test_f is not None:
                    self.cap = c
                    break
                c.release()

        if self.cap is None or not self.cap.isOpened():
            self.view.setText(
                "⚠️ No live camera detected or permission was denied.\n\n"
                "You can click 'Choose Photo from Disk' below to scan a component image directly."
            )
            self.snap_btn.setEnabled(False)
            return

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_frame)
        self.timer.start(33)

    def _update_frame(self):
        if not self.cap or not self.cap.isOpened():
            return
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
            self._cleanup()
            self.accept()

    def choose_disk_photo(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Choose component photo", "",
            "Images (*.png *.jpg *.jpeg *.bmp *.webp *.tif *.tiff)"
        )
        if path and os.path.isfile(path):
            self.captured_path = path
            self._cleanup()
            self.accept()

    def closeEvent(self, event):
        self._cleanup()
        super().closeEvent(event)

    def reject(self):
        self._cleanup()
        super().reject()

    def _cleanup(self):
        if hasattr(self, "timer") and self.timer.isActive():
            self.timer.stop()
        if hasattr(self, "cap") and self.cap and self.cap.isOpened():
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
        self.setWindowTitle("Voice Assistant Input")
        self.setFixedSize(500, 270)
        self.transcribed_text = ""

        lay = QVBoxLayout(self)
        lay.setContentsMargins(28, 24, 28, 22)
        lay.setSpacing(16)

        header_lay = QHBoxLayout()
        mic_icon = QLabel("🎙")
        mic_icon.setStyleSheet("font-size:28px;")
        header_lay.addWidget(mic_icon)

        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        title_lbl = label("Voice Assistant Input", "h1", wrap=False)
        self.sub_lbl = label("Listening... Speak your electronic question into the microphone.", "muted")
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
        self.meter.setFixedHeight(12)
        lay.addWidget(self.meter)

        self.status_box = QLabel("Ready... Speak now. Transcription will automatically start when you pause.")
        self.status_box.setStyleSheet(
            "background:rgba(9, 20, 13, 0.9); border:1px solid #1a4227; border-radius:10px; "
            "padding:10px 14px; font-size:13.5px; color:#bbf7d0;"
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
            "background:#052e16; border:1px solid #00ff66; border-radius:10px; "
            "padding:10px 14px; font-size:13.5px; color:#00ff66; font-weight:700;"
        )

    def _on_status(self, text):
        self.sub_lbl.setText(text)
        if "Transcribing" in text:
            self.meter.setValue(0)
            self.status_box.setText("⏳ Transcribing speech with Whisper AI...")
            self.status_box.setStyleSheet(
                "background:#082414; border:1px solid #22c55e; border-radius:10px; "
                "padding:10px 14px; font-size:13.5px; color:#86efac; font-weight:600;"
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
        lbl.setStyleSheet("background:#040705; border-radius:12px;")
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
    """Image display with smooth scaling and path storage."""
    def __init__(self):
        super().__init__()
        self.setObjectName("imageContainer")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumSize(320, 240)
        self._image_path = None

    def set_image(self, path):
        self._image_path = path
        if not path or not os.path.isfile(path):
            self.setText("No illustration available")
            self.setPixmap(QPixmap())
            return
        pm = QPixmap(path)
        if pm.isNull():
            self.setText("Failed to load image")
            return
        self.setPixmap(pm.scaled(
            self.width() if self.width() > 100 else 460,
            self.height() if self.height() > 100 else 320,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        ))

    def get_image_path(self):
        return self._image_path


class UserManualDialog(QDialog):
    """Comprehensive PDF viewer with Table of Contents, in-doc search, and zoom controls."""
    def __init__(self, parent=None, manual_id=None, initial_page=1):
        super().__init__(parent)
        self.manual_id = manual_id
        self.manual_info = db.get_manual(manual_id) if manual_id else None
        self.doc = None
        self.total_pages = 0
        self.current_page = initial_page
        self.zoom = 1.25

        title = f"User Manual: {self.manual_info['name']}" if self.manual_info else "User Manual Viewer"
        self.setWindowTitle(title)
        self.resize(1120, 800)

        main_lay = QVBoxLayout(self)
        main_lay.setContentsMargins(14, 12, 14, 14)
        main_lay.setSpacing(10)

        ctrl_bar = QHBoxLayout()
        ctrl_bar.setSpacing(10)

        self.prev_btn = button("◀ Prev", "secondary", self.prev_page)
        self.next_btn = button("Next ▶", "secondary", self.next_page)
        ctrl_bar.addWidget(self.prev_btn)
        ctrl_bar.addWidget(self.next_btn)

        ctrl_bar.addWidget(label("Page:", "caption"))
        self.page_spin = QSpinBox()
        self.page_spin.setRange(1, 1)
        self.page_spin.setValue(self.current_page)
        self.page_spin.valueChanged.connect(self.jump_to_page)
        ctrl_bar.addWidget(self.page_spin)

        self.total_lbl = label("of 0", "caption")
        ctrl_bar.addWidget(self.total_lbl)

        ctrl_bar.addSpacing(16)
        ctrl_bar.addWidget(label("Zoom:", "caption"))
        self.zoom_out_btn = button("－", slot=self.zoom_out)
        self.zoom_in_btn = button("＋", slot=self.zoom_in)
        self.fit_btn = button("Fit Width", slot=self.fit_width)
        self.zoom_lbl = label("125%", "caption")
        ctrl_bar.addWidget(self.zoom_out_btn)
        ctrl_bar.addWidget(self.zoom_lbl)
        ctrl_bar.addWidget(self.zoom_in_btn)
        ctrl_bar.addWidget(self.fit_btn)

        ctrl_bar.addStretch()

        self.ext_btn = button("↗ Open External Viewer", slot=self.open_external)
        ctrl_bar.addWidget(self.ext_btn)
        self.close_btn = button("Close", slot=self.accept)
        ctrl_bar.addWidget(self.close_btn)

        main_lay.addLayout(ctrl_bar)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        left_tabs = QTabWidget()
        left_tabs.setFixedWidth(300)

        toc_widget = QWidget()
        toc_lay = QVBoxLayout(toc_widget)
        toc_lay.setContentsMargins(6, 6, 6, 6)
        self.toc_tree = QTreeWidget()
        self.toc_tree.setHeaderLabel("Table of Contents")
        self.toc_tree.itemClicked.connect(self._on_toc_clicked)
        toc_lay.addWidget(self.toc_tree)
        left_tabs.addTab(toc_widget, "📖 Outline")

        search_widget = QWidget()
        s_lay = QVBoxLayout(search_widget)
        s_lay.setContentsMargins(6, 6, 6, 6)
        s_lay.setSpacing(6)
        s_input_row = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search in manual...")
        self.search_input.returnPressed.connect(self.search_manual)
        self.search_btn = button("🔍", slot=self.search_manual)
        s_input_row.addWidget(self.search_input, 1)
        s_input_row.addWidget(self.search_btn)
        s_lay.addLayout(s_input_row)

        self.search_res_header = label("", "caption")
        self.search_res_header.setVisible(False)
        s_lay.addWidget(self.search_res_header)

        self.search_list = QListWidget()
        self.search_list.itemClicked.connect(self._on_search_item_clicked)
        self.search_list.setVisible(False)
        s_lay.addWidget(self.search_list, 1)

        left_tabs.addTab(search_widget, "🔍 Search")
        splitter.addWidget(left_tabs)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.page_lbl = QLabel("Loading manual...", self)
        self.page_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.scroll_area.setWidget(self.page_lbl)
        splitter.addWidget(self.scroll_area)
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

    def zoom_in(self):
        self.zoom = min(3.0, round(self.zoom + 0.25, 2))
        self.render_page(self.current_page)

    def zoom_out(self):
        self.zoom = max(0.5, round(self.zoom - 0.25, 2))
        self.render_page(self.current_page)

    def fit_width(self):
        if not self.doc or self.total_pages == 0:
            return
        avail_w = self.scroll_area.viewport().width() - 32
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
    """Visually distinct chat message card (User or Assistant) with live streaming support."""
    def __init__(self, role, content, data=None, created_at=None, parent_win=None):
        super().__init__()
        self.role = role
        self.content = content
        self.data = data
        self.created_at = created_at or time.strftime("%H:%M")
        self.win = parent_win

        self.main_lay = QVBoxLayout(self)
        self.main_lay.setContentsMargins(0, 4, 0, 4)

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

            self.txt_lbl = QLabel(self.content)
            self.txt_lbl.setWordWrap(True)
            self.txt_lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            self.txt_lbl.setStyleSheet("font-size:14.5px; line-height:1.45;")
            b_lay.addWidget(self.txt_lbl)

            bubble.setMaximumWidth(720)
            row.addWidget(bubble)
            self.main_lay.addLayout(row)
        else:
            row = QHBoxLayout()
            self.card = QFrame()
            self.card.setObjectName("asstCard")
            self.c_lay = QVBoxLayout(self.card)
            self.c_lay.setContentsMargins(20, 16, 20, 16)
            self.c_lay.setSpacing(12)

            head = QHBoxLayout()
            self.asst_badge = label("🤖 ElectroLearn AI", "badgeOk", wrap=False)
            head.addWidget(self.asst_badge)
            head.addStretch()
            head.addWidget(label(self.created_at, "caption"))
            self.c_lay.addLayout(head)

            title = (self.data or {}).get("title") if isinstance(self.data, dict) else ""
            if title:
                self.c_lay.addWidget(label(title.upper(), "h1"))

            summary = (self.data or {}).get("summary") if isinstance(self.data, dict) else ""
            if not summary and self.content:
                summary = self.content

            self.summary_lbl = QLabel(summary)
            self.summary_lbl.setWordWrap(True)
            self.summary_lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            self.summary_lbl.setStyleSheet("font-size:14.5px; line-height:1.55;")
            self.c_lay.addWidget(self.summary_lbl)

            self.steps_box = QWidget()
            self.steps_box.setStyleSheet("background:transparent;")
            self.sb_lay = QVBoxLayout(self.steps_box)
            self.sb_lay.setContentsMargins(0, 4, 0, 4)
            self.sb_lay.setSpacing(8)
            self.c_lay.addWidget(self.steps_box)

            steps = (self.data or {}).get("steps") or [] if isinstance(self.data, dict) else []
            self._render_steps(steps)

            # Footer actions: Copy, Export
            self.f_row = QHBoxLayout()
            copy_btn = button("📋 Copy", "secondary", slot=self.copy_text)
            self.f_row.addWidget(copy_btn)

            exp_btn = button("📥 Export Answer ▼", "secondary")
            menu = QMenu(exp_btn)
            act_pdf = menu.addAction("Export as PDF (.pdf)")
            act_pdf.triggered.connect(lambda: self.export_answer("pdf"))
            act_md = menu.addAction("Export as Markdown (.md)")
            act_md.triggered.connect(lambda: self.export_answer("md"))
            act_txt = menu.addAction("Export as Plain Text (.txt)")
            act_txt.triggered.connect(lambda: self.export_answer("txt"))
            exp_btn.setMenu(menu)
            self.f_row.addWidget(exp_btn)

            self.f_row.addStretch()
            self.c_lay.addLayout(self.f_row)

            self.card.setMaximumWidth(860)
            row.addWidget(self.card)
            row.addStretch()
            self.main_lay.addLayout(row)

    def append_stream_token(self, token):
        """Append streamed token in real-time."""
        self.content += token
        self.summary_lbl.setText(self.content)

    def finalize_stream(self, data):
        """Called when streaming finishes to attach steps and metadata."""
        self.data = data
        self.content = data.get("summary") or data.get("answer") or self.content
        self.summary_lbl.setText(self.content)
        steps = data.get("steps") or []
        self._render_steps(steps)

    def _render_steps(self, steps):
        while self.sb_lay.count():
            item = self.sb_lay.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not steps:
            self.steps_box.setVisible(False)
            return

        self.steps_box.setVisible(True)
        for s in steps:
            s_row = QHBoxLayout()
            s_row.setSpacing(10)
            s_num = label(f" {s.get('number', '')} ", "badge", wrap=False)
            s_row.addWidget(s_num, alignment=Qt.AlignmentFlag.AlignTop)

            s_text = QLabel(s.get("text", ""))
            s_text.setWordWrap(True)
            s_text.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            s_text.setStyleSheet("font-size:14px; line-height:1.4;")
            s_row.addWidget(s_text, 1)

            pno = s.get("page")
            if pno and self.win:
                jump_b = button(f"p. {pno} ↗", "chip", slot=lambda _=False, p=pno: self.win.open_user_manual(p))
                jump_b.setFixedHeight(26)
                s_row.addWidget(jump_b, alignment=Qt.AlignmentFlag.AlignTop)

            self.sb_lay.addLayout(s_row)

    def copy_text(self):
        text_to_copy = export_mod.format_answer_txt(self.data or {"answer": self.content})
        QApplication.clipboard().setText(text_to_copy)
        if self.win:
            QMessageBox.information(self.win, "Copied", "Answer text copied to clipboard!")

    def export_answer(self, fmt):
        if self.win:
            self.win.export_single_answer(self.data or {"answer": self.content}, fmt=fmt)


class ComponentCardWidget(QFrame):
    """Rich interactive card for electronic component info & pinouts."""
    def __init__(self, comp_dict, on_ask_cb=None):
        super().__init__()
        self.setObjectName("card")
        self.comp = comp_dict
        self.on_ask_cb = on_ask_cb
        self.details_expanded = False

        lay = QVBoxLayout(self)
        lay.setContentsMargins(18, 16, 18, 16)
        lay.setSpacing(10)

        head = QHBoxLayout()
        name_lbl = label(comp_dict.get("name", "Component"), "h1", wrap=False)
        head.addWidget(name_lbl)
        head.addStretch()

        cat_badge = label(f"🏷 {comp_dict.get('category', 'Generic')}", "badge", wrap=False)
        head.addWidget(cat_badge)
        lay.addLayout(head)

        pkg_lbl = label(f"Package: {comp_dict.get('package', 'Standard')}", "caption")
        lay.addWidget(pkg_lbl)

        func_lbl = label(f"<b>Function:</b> {comp_dict.get('function', '')}")
        lay.addWidget(func_lbl)

        simple_lbl = label(f"💡 <i>{comp_dict.get('simple_explanation', '')}</i>")
        lay.addWidget(simple_lbl)

        sym = comp_dict.get("symbol", "").strip()
        if sym:
            sym_box = label(sym, "codeBlock")
            lay.addWidget(sym_box)

        self.details_box = QWidget()
        d_lay = QVBoxLayout(self.details_box)
        d_lay.setContentsMargins(0, 6, 0, 6)
        d_lay.setSpacing(8)

        if comp_dict.get("pinout"):
            d_lay.addWidget(label("📍 PIN DIAGRAM & CONNECTIONS:", "h2", wrap=False))
            pin_lbl = label(comp_dict["pinout"], "codeBlock")
            d_lay.addWidget(pin_lbl)

        if comp_dict.get("key_specs"):
            d_lay.addWidget(label(f"⚡ <b>Key Specs:</b> {comp_dict['key_specs']}"))

        uses = comp_dict.get("typical_uses") or []
        if uses:
            d_lay.addWidget(label("🛠 <b>Typical Applications:</b> " + ", ".join(uses)))

        if comp_dict.get("detailed_explanation"):
            d_lay.addWidget(label(f"🔬 <b>Technical Deep Dive:</b> {comp_dict['detailed_explanation']}"))

        self.details_box.setVisible(False)
        lay.addWidget(self.details_box)

        btn_row = QHBoxLayout()
        self.toggle_btn = button("▼ View Pinout & Details", "secondary", slot=self.toggle_details)
        btn_row.addWidget(self.toggle_btn)

        btn_row.addStretch()
        ask_b = button("💬 Ask Assistant About This", "primary", slot=self.ask_about)
        btn_row.addWidget(ask_b)

        lay.addLayout(btn_row)

    def toggle_details(self):
        self.details_expanded = not self.details_expanded
        self.details_box.setVisible(self.details_expanded)
        self.toggle_btn.setText("▲ Hide Details" if self.details_expanded else "▼ View Pinout & Details")

    def ask_about(self):
        if self.on_ask_cb:
            self.on_ask_cb(self.comp)


class TopNavBar(QFrame):
    """Top navigation bar with Cyber Green branding, page routing, and theme toggle."""
    def __init__(self, win):
        super().__init__()
        self.win = win
        self.setObjectName("card")
        self.setFixedHeight(64)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(18, 8, 18, 8)
        lay.setSpacing(8)

        brand_icon = label("⚡", wrap=False)
        brand_icon.setStyleSheet("font-size:22px; color:#00ff66;")
        brand_lbl = label("ElectroLearn AI", "brand", wrap=False)
        lay.addWidget(brand_icon)
        lay.addWidget(brand_lbl)
        lay.addSpacing(20)

        self.btn_dash = button("🏠 Dashboard", "navActive", slot=lambda: self.win.navigate_to(0))
        self.btn_chat = button("💬 AI Assistant", "nav", slot=lambda: self.win.navigate_to(1))
        self.btn_lib = button("📚 Component Library", "nav", slot=lambda: self.win.navigate_to(2))
        self.btn_manual = button("📖 User Manual & Help", "nav", slot=lambda: self.win.navigate_to(3))

        for b in (self.btn_dash, self.btn_chat, self.btn_lib, self.btn_manual):
            lay.addWidget(b)

        lay.addStretch()

        self.theme_btn = button("🌓 Theme", "secondary", slot=self.win.toggle_theme)
        self.theme_btn.setToolTip("Toggle Matrix Dark / Clean Light Theme")
        lay.addWidget(self.theme_btn)

        self.settings_btn = button("⚙ Settings", "secondary", slot=lambda: SettingsDialog(self.win).exec())
        lay.addWidget(self.settings_btn)

    def set_active_tab(self, idx):
        buttons = [self.btn_dash, self.btn_chat, self.btn_lib, self.btn_manual]
        for i, b in enumerate(buttons):
            b.setProperty("kind", "navActive" if i == idx else "nav")
            b.style().unpolish(b)
            b.style().polish(b)


class MainView:
    """Builder for the modern 4-page electronic components learning interface with space background."""
    def __init__(self, window):
        self.win = window
        self.stack = QStackedWidget()

    def setup_ui(self):
        # Window base layout
        root_lay = QVBoxLayout(self.win)
        root_lay.setContentsMargins(0, 0, 0, 0)
        root_lay.setSpacing(0)

        # Space background canvas behind everything
        self.space_bg = SpaceBackgroundWidget(self.win)
        self.space_bg.lower()

        # Persistent Top Navigation Bar
        self.top_bar = TopNavBar(self.win)
        root_lay.addWidget(self.top_bar)
        root_lay.addWidget(self.stack, 1)

        # Build the 4 primary pages
        self.dashboard_page = self._build_dashboard()   # Page 0
        self.chat_page = self._build_chat()             # Page 1
        self.library_page = self._build_library()       # Page 2
        self.manual_page = self._build_manual_help()    # Page 3

        # Auxiliary background transition page
        self.busy_page = self._build_busy()

        self.stack.addWidget(self.dashboard_page)
        self.stack.addWidget(self.chat_page)
        self.stack.addWidget(self.library_page)
        self.stack.addWidget(self.manual_page)
        self.stack.addWidget(self.busy_page)

        # Aliases for backward compatibility
        self.home_page = self.dashboard_page
        self.result_page = self.dashboard_page
        self.viewer_page = self.manual_page
        self.ask_page = self.chat_page

    def update_background_theme(self, is_dark):
        if hasattr(self, "space_bg"):
            self.space_bg.set_theme(is_dark)

    def _page_scroll(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background:transparent;")
        content = QWidget()
        content.setStyleSheet("background:transparent;")
        lay = QVBoxLayout(content)
        lay.setContentsMargins(32, 24, 32, 28)
        lay.setSpacing(20)
        scroll.setWidget(content)
        return scroll, lay

    # =========================================================================
    # PAGE 1: DASHBOARD / HOME
    # =========================================================================
    def _build_dashboard(self):
        page, lay = self._page_scroll()

        # Top Banner
        banner_box = QFrame()
        banner_box.setObjectName("accentCard")
        b_lay = QVBoxLayout(banner_box)
        b_lay.setContentsMargins(24, 20, 24, 20)
        b_lay.setSpacing(8)

        b_head = QHBoxLayout()
        b_title = label("Electronic Components Learning & Identification Hub", "title")
        b_head.addWidget(b_title)
        b_head.addStretch()
        b_badge = label("⚡ AI Vision & General Assistant", "badgeOk", wrap=False)
        b_head.addWidget(b_badge)
        b_lay.addLayout(b_head)

        b_sub = label(
            "Scan circuit boards, identify mystery ICs, review pinout schematics, "
            "and ask general electronics knowledge questions powered by hybrid AI.", "subtitle"
        )
        b_lay.addWidget(b_sub)
        lay.addWidget(banner_box)

        # Quick Actions Grid (4 Cards)
        lay.addWidget(label("QUICK ACTIONS", "h2", wrap=False))
        actions_grid = QGridLayout()
        actions_grid.setSpacing(14)

        act1 = QPushButton("📷  Upload Image\nSelect circuit photo from disk")
        act1.setProperty("kind", "cardAction")
        act1.setCursor(Qt.CursorShape.PointingHandCursor)
        act1.clicked.connect(self.win.upload_photo)
        actions_grid.addWidget(act1, 0, 0)

        act2 = QPushButton("🎥  Live Camera Scan\nPoint webcam at component")
        act2.setProperty("kind", "cardAction")
        act2.setCursor(Qt.CursorShape.PointingHandCursor)
        act2.clicked.connect(self.win.open_camera)
        actions_grid.addWidget(act2, 0, 1)

        act3 = QPushButton("🎬  Upload Video\nAnalyze hardware recording")
        act3.setProperty("kind", "cardAction")
        act3.setCursor(Qt.CursorShape.PointingHandCursor)
        act3.clicked.connect(self.win.upload_video)
        actions_grid.addWidget(act3, 0, 2)

        act4 = QPushButton("💬  Ask AI Assistant\nGeneral electronics or manuals")
        act4.setProperty("kind", "cardAction")
        act4.setCursor(Qt.CursorShape.PointingHandCursor)
        act4.clicked.connect(lambda: self.win.open_chat())
        actions_grid.addWidget(act4, 0, 3)

        lay.addLayout(actions_grid)

        # Component Identification Result Card
        self.dash_result_card = QFrame()
        self.dash_result_card.setObjectName("card")
        res_lay = QVBoxLayout(self.dash_result_card)
        res_lay.setContentsMargins(22, 18, 22, 18)
        res_lay.setSpacing(14)

        r_head = QHBoxLayout()
        r_head.addWidget(label("🔍 COMPONENT IDENTIFICATION RESULT", "h1", wrap=False))
        r_head.addStretch()
        self.dash_match_badge = label("Ready to Scan", "badgeOk", wrap=False)
        r_head.addWidget(self.dash_match_badge)
        res_lay.addLayout(r_head)

        self.img_row = QHBoxLayout()
        self.img_row.setSpacing(16)

        self.uploaded_box = QWidget()
        up_lay = QVBoxLayout(self.uploaded_box)
        up_lay.setContentsMargins(0, 0, 0, 0)
        up_lay.setSpacing(4)
        self.uploaded_caption = label("Uploaded Photo / Frame", "caption", align=Qt.AlignmentFlag.AlignCenter)
        up_lay.addWidget(self.uploaded_caption)
        self.hw_image = label("", align=Qt.AlignmentFlag.AlignCenter)
        self.hw_image.setStyleSheet("background:#040705; border:1px solid #173822; border-radius:12px;")
        self.hw_image.setFixedHeight(220)
        up_lay.addWidget(self.hw_image)
        self.img_row.addWidget(self.uploaded_box, 1)

        self.matched_box = QWidget()
        mat_lay = QVBoxLayout(self.matched_box)
        mat_lay.setContentsMargins(0, 0, 0, 0)
        mat_lay.setSpacing(4)
        self.matched_caption = label("Matched Manual / Component Reference", "caption", align=Qt.AlignmentFlag.AlignCenter)
        mat_lay.addWidget(self.matched_caption)
        self.matched_hw_image = label("", align=Qt.AlignmentFlag.AlignCenter)
        self.matched_hw_image.setStyleSheet("background:#040705; border:1px solid #173822; border-radius:12px;")
        self.matched_hw_image.setFixedHeight(220)
        mat_lay.addWidget(self.matched_hw_image)
        self.img_row.addWidget(self.matched_box, 1)
        self.matched_box.setVisible(False)

        res_lay.addLayout(self.img_row)

        specs_box = QWidget()
        specs_grid = QGridLayout(specs_box)
        specs_grid.setContentsMargins(0, 4, 0, 4)
        specs_grid.setSpacing(8)
        self.hw_values = {}
        for r, (key, cap) in enumerate((
            ("product_name", "Component / Product"),
            ("manufacturer", "Manufacturer"),
            ("model", "Model / Marking"),
            ("part_number", "Part Number"),
            ("hardware_type", "Category / Type")
        )):
            specs_grid.addWidget(label(cap, "caption"), r, 0)
            val = label("—", wrap=False)
            self.hw_values[key] = val
            specs_grid.addWidget(val, r, 1)
        res_lay.addWidget(specs_box)

        self.dash_desc_lbl = label("Upload an image or use the live camera to identify your electronic component.", "muted")
        res_lay.addWidget(self.dash_desc_lbl)

        self.match_status = label("", "badgeOk")
        self.match_detail = label("", "muted")
        res_lay.addWidget(self.match_status)
        res_lay.addWidget(self.match_detail)

        self.manual_combo = QComboBox()
        self.manual_combo.currentIndexChanged.connect(self.win._update_continue)
        res_lay.addWidget(self.manual_combo)

        res_btn_row = QHBoxLayout()
        self.dash_ask_comp_btn = button("💬 Ask Assistant About This Component", "primary", slot=self.win.ask_about_scanned_component)
        self.dash_ask_comp_btn.setEnabled(False)
        res_btn_row.addWidget(self.dash_ask_comp_btn)

        self.continue_btn = button("📖 Open Manual Instructions →", "secondary", self.win.continue_from_result)
        res_btn_row.addWidget(self.continue_btn)
        res_btn_row.addStretch()

        res_lay.addLayout(res_btn_row)
        lay.addWidget(self.dash_result_card)

        # Recent Scans & Activity
        lay.addWidget(label("RECENT SCANS & IDENTIFICATIONS", "h2", wrap=False))
        self.dash_scans_list = QListWidget()
        self.dash_scans_list.setFixedHeight(160)
        self.dash_scans_list.itemClicked.connect(self.win.on_recent_scan_clicked)
        lay.addWidget(self.dash_scans_list)

        scans_btn_row = QHBoxLayout()
        scans_btn_row.addStretch()
        self.dash_clear_scans_btn = button("🗑 Clear Recent Scans", "danger", slot=self.win.clear_recent_scans)
        scans_btn_row.addWidget(self.dash_clear_scans_btn)
        lay.addLayout(scans_btn_row)

        # Beginner Electronics Tips
        lay.addWidget(label("BEGINNER ELECTRONICS QUICK TIPS", "h2", wrap=False))
        tips_grid = QGridLayout()
        tips_grid.setSpacing(14)

        tips_data = [
            ("🎨 Resistor Color Bands", "Black=0, Brown=1, Red=2, Orange=3, Yellow=4, Green=5, Blue=6, Violet=7, Grey=8, White=9. Gold tolerance is ±5%. First two bands are digits, third is multiplier."),
            ("📌 Finding Pin 1 on ICs", "Look for the half-circle notch at one end. With the notch facing UP, Pin 1 is immediately at the top-left! Alternatively, look for a small circular indentation dot next to Pin 1."),
            ("⚡ Capacitor Polarity Care", "Electrolytic capacitors have polarity! The side marked with a minus (-) stripe is NEGATIVE. Connecting an electrolytic backwards will cause it to overheat and fail!"),
            ("🔬 Safe Multimeter Testing", "Never measure resistance (ohms) or continuity on a powered circuit! Always disconnect power before probing component leads to prevent blowing the meter's fuse.")
        ]

        for i, (ttitle, ttext) in enumerate(tips_data):
            card = QFrame()
            card.setObjectName("tipCard")
            c_lay = QVBoxLayout(card)
            c_lay.setContentsMargins(14, 12, 14, 12)
            c_lay.setSpacing(6)
            c_lay.addWidget(label(ttitle, "h2"))
            c_lay.addWidget(label(ttext, "muted"))
            tips_grid.addWidget(card, i // 2, i % 2)

        lay.addLayout(tips_grid)
        return page

    # =========================================================================
    # PAGE 2: CHAT / ASSISTANT
    # =========================================================================
    def _build_chat(self):
        p = QWidget()
        p.setStyleSheet("background:transparent;")
        main_h_lay = QHBoxLayout(p)
        main_h_lay.setContentsMargins(0, 0, 0, 0)
        main_h_lay.setSpacing(0)

        # Collapsible Left Sidebar
        self.chat_sidebar = QFrame()
        self.chat_sidebar.setObjectName("sidebarFrame")
        self.chat_sidebar.setFixedWidth(290)
        s_lay = QVBoxLayout(self.chat_sidebar)
        s_lay.setContentsMargins(14, 16, 14, 16)
        s_lay.setSpacing(10)

        s_top = QHBoxLayout()
        self.new_chat_btn = button("＋ New Chat", "primary", slot=self.win.new_chat)
        self.new_chat_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        s_top.addWidget(self.new_chat_btn)

        self.collapse_sidebar_btn = button("◀", slot=self.win.toggle_sidebar)
        self.collapse_sidebar_btn.setFixedWidth(36)
        self.collapse_sidebar_btn.setToolTip("Collapse Sidebar")
        s_top.addWidget(self.collapse_sidebar_btn)
        s_lay.addLayout(s_top)

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

        s_lay.addWidget(label("SAVED CONVERSATIONS", "caption", wrap=False))

        self.chat_history_list = QListWidget()
        self.chat_history_list.itemClicked.connect(self.win._on_history_item_clicked)
        s_lay.addWidget(self.chat_history_list, 1)

        self.sidebar_delete_btn = button("🗑 Delete Selected Chat", "danger", slot=self.win.delete_selected_conversation)
        s_lay.addWidget(self.sidebar_delete_btn)

        main_h_lay.addWidget(self.chat_sidebar)

        # Main Chat Area
        chat_area = QWidget()
        chat_area.setStyleSheet("background:transparent;")
        c_lay = QVBoxLayout(chat_area)
        c_lay.setContentsMargins(24, 16, 24, 16)
        c_lay.setSpacing(10)

        top_bar = QHBoxLayout()
        top_bar.setSpacing(10)

        self.expand_sidebar_btn = button("☰ Chats", slot=self.win.toggle_sidebar)
        self.expand_sidebar_btn.setVisible(False)
        top_bar.addWidget(self.expand_sidebar_btn)

        self.chat_manual_badge = label("💬 Electronics & Manuals Assistant", "h1", wrap=False)
        top_bar.addWidget(self.chat_manual_badge)
        top_bar.addStretch()

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

        c_lay.addLayout(top_bar)

        self.chat_scroll = QScrollArea()
        self.chat_scroll.setWidgetResizable(True)
        self.chat_scroll.setStyleSheet("background:transparent; border:none;")

        self.chat_thread_widget = QWidget()
        self.chat_thread_widget.setStyleSheet("background:transparent;")
        self.chat_thread_lay = QVBoxLayout(self.chat_thread_widget)
        self.chat_thread_lay.setContentsMargins(10, 10, 10, 10)
        self.chat_thread_lay.setSpacing(14)
        self.chat_thread_lay.addStretch()

        self.chat_scroll.setWidget(self.chat_thread_widget)
        c_lay.addWidget(self.chat_scroll, 1)

        self.typing_card = QFrame()
        self.typing_card.setObjectName("typingCard")
        t_lay = QHBoxLayout(self.typing_card)
        t_lay.setContentsMargins(16, 10, 16, 10)
        t_lay.setSpacing(10)
        t_icon = label("⏳", wrap=False)
        self.typing_lbl = label("Reasoning answer...", "badgeOk", wrap=False)
        t_lay.addWidget(t_icon)
        t_lay.addWidget(self.typing_lbl)
        t_lay.addStretch()
        self.typing_card.setVisible(False)
        c_lay.addWidget(self.typing_card)

        # Fixed Bottom Input Bar
        bottom_box = QFrame()
        bottom_box.setObjectName("card")
        b_lay = QVBoxLayout(bottom_box)
        b_lay.setContentsMargins(12, 10, 12, 10)
        b_lay.setSpacing(8)

        input_row = QHBoxLayout()
        input_row.setSpacing(8)
        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("💬 Ask anything! (e.g. 'What is an IC?', 'How do 555 timers oscillate?', or questions about manuals)...")
        self.chat_input.returnPressed.connect(self.win.send_chat_message)
        input_row.addWidget(self.chat_input, 1)

        self.chat_speak_btn = button("🎤 Speak", slot=self.win.speak_chat)
        input_row.addWidget(self.chat_speak_btn)

        self.chat_send_btn = button("Send", "primary", slot=self.win.send_chat_message)
        self.chat_send_btn.setFixedWidth(80)
        input_row.addWidget(self.chat_send_btn)
        b_lay.addLayout(input_row)

        sub_row = QHBoxLayout()
        self.chat_full_check = QCheckBox("Deep-dive mode (searches all manual pages + engineering theory)")
        sub_row.addWidget(self.chat_full_check)
        sub_row.addStretch()
        sub_hint = label("Press Enter to send • Supports live streaming & general electronics questions", "caption")
        sub_row.addWidget(sub_hint)
        b_lay.addLayout(sub_row)

        c_lay.addWidget(bottom_box)

        main_h_lay.addWidget(chat_area, 1)
        return p

    # =========================================================================
    # PAGE 3: COMPONENT LIBRARY / LEARN
    # =========================================================================
    def _build_library(self):
        page = QWidget()
        page.setStyleSheet("background:transparent;")
        lay = QVBoxLayout(page)
        lay.setContentsMargins(28, 20, 28, 24)
        lay.setSpacing(14)

        head_row = QHBoxLayout()
        head_row.addWidget(label("ELECTRONIC COMPONENT LIBRARY & PINOUTS", "h1"))
        head_row.addStretch()
        self.lib_add_btn = button("+ Add Manual PDF", "primary", slot=self.win.add_manual)
        head_row.addWidget(self.lib_add_btn)
        lay.addLayout(head_row)

        self.lib_search = QLineEdit()
        self.lib_search.setPlaceholderText("🔍 Search components by name, pin, package, or function (e.g. 555, timer, esp32, ultrasonic, diode)...")
        self.lib_search.textChanged.connect(self.win.filter_library_cards)
        lay.addWidget(self.lib_search)

        self.chip_bar = QHBoxLayout()
        self.chip_bar.setSpacing(8)
        self.chip_buttons = []
        categories = comp_service.get_categories() + ["Hardware Manuals"]
        for cat in categories:
            btn = button(cat, "chipActive" if cat == "All" else "chip")
            btn.clicked.connect(lambda _=False, c=cat: self.win.on_category_chip_clicked(c))
            self.chip_bar.addWidget(btn)
            self.chip_buttons.append((cat, btn))
        self.chip_bar.addStretch()
        lay.addLayout(self.chip_bar)

        self.lib_stack = QStackedWidget()
        self.lib_stack.setStyleSheet("background:transparent;")

        self.cards_scroll = QScrollArea()
        self.cards_scroll.setWidgetResizable(True)
        self.cards_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.cards_scroll.setStyleSheet("background:transparent;")
        self.cards_container = QWidget()
        self.cards_container.setStyleSheet("background:transparent;")
        self.cards_lay = QVBoxLayout(self.cards_container)
        self.cards_lay.setContentsMargins(0, 0, 0, 0)
        self.cards_lay.setSpacing(14)
        self.cards_lay.addStretch()
        self.cards_scroll.setWidget(self.cards_container)
        self.lib_stack.addWidget(self.cards_scroll)

        manuals_view = QWidget()
        manuals_view.setStyleSheet("background:transparent;")
        m_lay = QVBoxLayout(manuals_view)
        m_lay.setContentsMargins(0, 0, 0, 0)
        m_lay.setSpacing(10)

        self.lib_list = QListWidget()
        self.lib_list.itemDoubleClicked.connect(lambda _: self.win.use_selected_manual())
        m_lay.addWidget(self.lib_list, 1)

        self.lib_empty = label("No imported PDF manuals found. Click '+ Add Manual PDF' above to index hardware manuals.", "muted", align=Qt.AlignmentFlag.AlignCenter)
        m_lay.addWidget(self.lib_empty)

        m_btn_row = QHBoxLayout()
        m_btn_row.addWidget(button("📖 View In Manual Reader", slot=self.win.view_selected_manual))
        m_btn_row.addWidget(button("💬 Chat With This Manual", "primary", slot=self.win.use_selected_manual))
        m_btn_row.addStretch()
        m_btn_row.addWidget(button("Delete", "danger", slot=self.win.delete_selected))
        m_lay.addLayout(m_btn_row)

        self.lib_stack.addWidget(manuals_view)
        lay.addWidget(self.lib_stack, 1)

        return page

    # =========================================================================
    # PAGE 4: USER MANUAL & APP HELP
    # =========================================================================
    def _build_manual_help(self):
        page = QWidget()
        page.setStyleSheet("background:transparent;")
        lay = QVBoxLayout(page)
        lay.setContentsMargins(28, 20, 28, 24)
        lay.setSpacing(14)

        tabs = QTabWidget()

        guide_widget = QWidget()
        guide_widget.setStyleSheet("background:transparent;")
        g_scroll = QScrollArea()
        g_scroll.setWidgetResizable(True)
        g_scroll.setFrameShape(QFrame.Shape.NoFrame)
        g_scroll.setStyleSheet("background:transparent;")
        g_content = QWidget()
        g_content.setStyleSheet("background:transparent;")
        g_lay = QVBoxLayout(g_content)
        g_lay.setContentsMargins(20, 16, 20, 20)
        g_lay.setSpacing(16)

        g_lay.addWidget(label("📖 How to Use ElectroLearn AI & Hardware Assistant", "title"))
        g_lay.addWidget(label("A complete beginner-to-advanced guide on how to capture, identify, learn, and troubleshoot electronics with hybrid AI.", "subtitle"))

        guides = [
            ("1. Live Camera & Photo Scanning",
             "• Click 'Live Camera Scan' on the Dashboard to start your webcam or external USB microscope.\n"
             "• Align the chip or circuit board in good lighting. Click 'Capture Photo' to run vision identification.\n"
             "• Alternatively, click 'Upload Image' to choose a photo from disk. Common formats (.png, .jpg, .webp) are supported up to 50MB."),

            ("2. Hybrid AI & General Knowledge Chat",
             "• Ask general electronics questions like 'What is an IC?' or 'How does a diode work?'.\n"
             "• The assistant uses online LLM APIs (Gemini, OpenAI, Claude) or local Ollama to answer comprehensively.\n"
             "• When a question relates to an active manual, the assistant automatically retrieves manual context and cites page numbers."),

            ("3. Voice Recognition",
             "• Click the '🎤 Speak' button in the chat input bar or on any screen.\n"
             "• Dictate your question. Transcription starts automatically when you pause speaking."),

            ("4. Component Library & Pinouts",
             "• Browse standard components like the 555 timer, ATmega328P, ESP32, transistors, and diodes.\n"
             "• Click '▼ View Pinout & Details' on any card to see ASCII schematics and pin connection tables.\n"
             "• Click '💬 Ask Assistant About This' to jump directly into a detailed Q&A session."),

            ("5. Exporting Answers & Manual Viewing",
             "• Export answers or chat logs to PDF, Markdown (.md), or Plain Text (.txt).\n"
             "• Read full indexed PDF manuals in the embedded viewer tab with Table of Contents and search.")
        ]

        for g_title, g_body in guides:
            card = QFrame()
            card.setObjectName("card")
            c_lay = QVBoxLayout(card)
            c_lay.setContentsMargins(18, 14, 18, 14)
            c_lay.setSpacing(6)
            c_lay.addWidget(label(g_title, "h2"))
            body_lbl = label(g_body)
            body_lbl.setStyleSheet("line-height:1.55;")
            c_lay.addWidget(body_lbl)
            g_lay.addWidget(card)

        g_lay.addStretch()
        g_scroll.setWidget(g_content)

        g_main_lay = QVBoxLayout(guide_widget)
        g_main_lay.setContentsMargins(0, 0, 0, 0)
        g_main_lay.addWidget(g_scroll)
        tabs.addTab(guide_widget, "📘 App User Guide & Tutorials")

        # Embedded Interactive PDF Manual Reader
        self.embedded_viewer_widget = QWidget()
        self.embedded_viewer_widget.setStyleSheet("background:transparent;")
        ev_lay = QVBoxLayout(self.embedded_viewer_widget)
        ev_lay.setContentsMargins(10, 10, 10, 10)
        ev_lay.setSpacing(10)

        ev_ctrl = QHBoxLayout()
        ev_ctrl.addWidget(label("Active Manual:", "caption"))
        self.ev_manual_lbl = label("No manual selected", "h2")
        ev_ctrl.addWidget(self.ev_manual_lbl)
        ev_ctrl.addStretch()

        self.ev_prev_btn = button("◀ Prev", "secondary", slot=self.win.ev_prev_page)
        self.ev_next_btn = button("Next ▶", "secondary", slot=self.win.ev_next_page)
        ev_ctrl.addWidget(self.ev_prev_btn)
        ev_ctrl.addWidget(self.ev_next_btn)

        self.ev_page_spin = QSpinBox()
        self.ev_page_spin.setRange(1, 1)
        self.ev_page_spin.valueChanged.connect(self.win.ev_jump_page)
        ev_ctrl.addWidget(self.ev_page_spin)

        self.ev_total_lbl = label("of 0", "caption")
        ev_ctrl.addWidget(self.ev_total_lbl)

        ev_ctrl.addSpacing(12)
        self.ev_zoom_lbl = label("125%", "caption")
        ev_ctrl.addWidget(button("－", slot=self.win.ev_zoom_out))
        ev_ctrl.addWidget(self.ev_zoom_lbl)
        ev_ctrl.addWidget(button("＋", slot=self.win.ev_zoom_in))
        ev_ctrl.addWidget(button("Fit", slot=self.win.ev_fit_width))

        self.ev_ext_btn = button("↗ External", "secondary", slot=self.win.ev_open_external)
        ev_ctrl.addWidget(self.ev_ext_btn)

        ev_lay.addLayout(ev_ctrl)

        ev_splitter = QSplitter(Qt.Orientation.Horizontal)

        ev_left_tabs = QTabWidget()
        ev_left_tabs.setFixedWidth(280)

        ev_toc_w = QWidget()
        ev_toc_l = QVBoxLayout(ev_toc_w)
        ev_toc_l.setContentsMargins(4, 4, 4, 4)
        self.ev_toc_tree = QTreeWidget()
        self.ev_toc_tree.setHeaderLabel("Manual Outline")
        self.ev_toc_tree.itemClicked.connect(self.win.ev_on_toc_clicked)
        ev_toc_l.addWidget(self.ev_toc_tree)
        ev_left_tabs.addTab(ev_toc_w, "Outline")

        ev_search_w = QWidget()
        ev_s_l = QVBoxLayout(ev_search_w)
        ev_s_l.setContentsMargins(4, 4, 4, 4)
        ev_s_row = QHBoxLayout()
        self.ev_search_input = QLineEdit()
        self.ev_search_input.setPlaceholderText("Search manual text...")
        self.ev_search_input.returnPressed.connect(self.win.ev_search_text)
        ev_s_btn = button("🔍", slot=self.win.ev_search_text)
        ev_s_row.addWidget(self.ev_search_input)
        ev_s_row.addWidget(ev_s_btn)
        ev_s_l.addLayout(ev_s_row)

        self.ev_search_list = QListWidget()
        self.ev_search_list.itemClicked.connect(self.win.ev_on_search_clicked)
        ev_s_l.addWidget(self.ev_search_list, 1)
        ev_left_tabs.addTab(ev_search_w, "Search")

        ev_splitter.addWidget(ev_left_tabs)

        self.ev_scroll = QScrollArea()
        self.ev_scroll.setWidgetResizable(True)
        self.ev_scroll.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.ev_page_lbl = QLabel("Select a manual to view its pages", self.ev_scroll)
        self.ev_page_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.ev_scroll.setWidget(self.ev_page_lbl)
        ev_splitter.addWidget(self.ev_scroll)
        ev_splitter.setStretchFactor(1, 4)

        ev_lay.addWidget(ev_splitter, 1)

        tabs.addTab(self.embedded_viewer_widget, "📑 Interactive Manual PDF Viewer")
        lay.addWidget(tabs, 1)
        return page

    # =========================================================================
    # AUXILIARY / PROGRESS TRANSITION
    # =========================================================================
    def _build_busy(self):
        p = QWidget()
        p.setStyleSheet("background:transparent;")
        lay = QVBoxLayout(p)
        lay.setContentsMargins(40, 40, 40, 40)
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
