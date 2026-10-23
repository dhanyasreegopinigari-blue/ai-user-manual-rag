"""UI View layer: Modern Styles, Responsive Widgets, Dialogs, and 4-Page Architecture."""
import os
import re
import time
import cv2

from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QSize, QUrl
from PyQt6.QtGui import QAction, QImage, QPainter, QPixmap, QFont, QColor, QIcon
from PyQt6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QDialog, QFileDialog, QFormLayout, QFrame,
    QGridLayout, QHBoxLayout, QInputDialog, QLabel, QLineEdit, QListWidget, QListWidgetItem,
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
from ui.icons import get_icon, get_pixmap


DARK_STYLE = """
QWidget { background:#0d121a; color:#e6edf6; font-family:'Segoe UI','Inter',system-ui,sans-serif; font-size:14px; }
QLabel { background:transparent; }
QPushButton {
    background: #111a14;
    border: 1px solid rgba(0, 255, 133, 0.16);
    border-radius: 10px;
    padding: 8px 16px;
    min-height: 20px;
    color: #e6edf6;
    font-weight: 500;
}
QPushButton:hover {
    background: #18281d;
    border-color: #00FF85;
}
QPushButton:pressed {
    background: #0d1510;
}
QPushButton:disabled {
    color: #526357;
    background: #0d120f;
    border-color: #1a241e;
}

QPushButton[kind="primary"] {
    background: #00FF85;
    border: 1px solid #00FF85;
    border-radius: 10px;
    color: #060907;
    font-weight: 700;
    padding: 8px 18px;
}
QPushButton[kind="primary"]:hover {
    background: #39FF14;
    border-color: #39FF14;
}
QPushButton[kind="primary"]:pressed {
    background: #00cc6a;
}
QPushButton[kind="primary"]:disabled {
    background: #142419;
    color: #4a6352;
    border-color: #1b3022;
}

QPushButton[kind="secondary"] { background:#161f2c; border:1px solid #2d3b52; color:#cbd5e1; font-weight:500; }
QPushButton[kind="secondary"]:hover { background:#222f42; color:#ffffff; border-color:#475975; }

QPushButton[kind="danger"] { background:#351b20; border:1px solid #632832; color:#fca5a5; }
QPushButton[kind="danger"]:hover { background:#47232a; border-color:#843442; color:#fecaca; }

QPushButton[kind="nav"] { background:transparent; border:none; border-radius:8px; padding:8px 14px; color:#94a3b8; font-weight:600; font-size:14px; }
QPushButton[kind="nav"]:hover { background:#182232; color:#e2e8f0; }
QPushButton[kind="navActive"] { background:#2563eb; border:none; border-radius:8px; padding:8px 14px; color:#ffffff; font-weight:700; font-size:14px; }

QPushButton[kind="chip"] { background:#16202e; border:1px solid #27374e; border-radius:16px; padding:6px 14px; color:#94a3b8; font-size:13px; font-weight:500; }
QPushButton[kind="chip"]:hover { background:#223046; color:#ffffff; border-color:#3d5272; }
QPushButton[kind="chipActive"] { background:#1d4ed8; border:1px solid #3b82f6; border-radius:16px; padding:6px 14px; color:#ffffff; font-size:13px; font-weight:600; }

QPushButton[kind="cardAction"] { text-align:left; border-radius:14px; background:#141b26; border:1px solid #253347; padding:16px; }
QPushButton[kind="cardAction"]:hover { border-color:#3b82f6; background:#1b2434; }

QLineEdit, QComboBox, QSpinBox { background:#131a24; border:1px solid #27364b; border-radius:10px; padding:9px 12px; color:#ffffff; selection-background-color:#2563eb; }
QLineEdit:focus, QComboBox:focus, QSpinBox:focus { border-color:#3b82f6; background:#16202e; }
QComboBox QAbstractItemView { background:#131a24; border:1px solid #27364b; selection-background-color:#2563eb; selection-color:white; }

QListWidget { background:#111722; border:1px solid #222f42; border-radius:12px; padding:6px; outline:0; }
QListWidget::item { padding:10px 12px; border-radius:8px; margin-bottom:4px; }
QListWidget::item:hover { background:#1b2536; }
QListWidget::item:selected { background:#243654; color:#ffffff; }

QFrame#card { background:#131b26; border:1px solid #222f42; border-radius:14px; }
QFrame#accentCard { background:#122038; border:1px solid #214373; border-radius:14px; }
QFrame#tipCard { background:#131a24; border:1px solid #24344a; border-radius:14px; padding:12px; }
QFrame#tipCard:hover { border-color:#3b82f6; background:#172230; }
QFrame#sidebarFrame { background:#0f1520; border-right:1px solid #202b3c; }

QFrame#userBubble { background:#1b3558; border:1px solid #2b4f7e; border-radius:14px; }
QFrame#asstCard { background:#131c28; border:1px solid #233145; border-radius:16px; }

/* Manuals Page & Viewer Styling */
QFrame#dropZone {
    background: #090e0b;
    border: 2px dashed rgba(0, 255, 133, 0.35);
    border-radius: 14px;
}
QFrame#dropZone:hover {
    background: #0e1712;
    border-color: #00FF85;
}
QFrame#manualCard {
    background: #0d1410;
    border: 1px solid rgba(0, 255, 133, 0.14);
    border-radius: 14px;
}
QFrame#manualCard:hover {
    background: #121c16;
    border-color: #00FF85;
}
QFrame#manualRow {
    background: #0d1410;
    border: 1px solid rgba(0, 255, 133, 0.12);
    border-radius: 10px;
    padding: 6px 12px;
}
QFrame#manualRow:hover {
    background: #121c16;
    border-color: #00FF85;
}
QFrame#statCard {
    background: #0b110e;
    border: 1px solid rgba(0, 255, 133, 0.15);
    border-radius: 12px;
    padding: 12px 16px;
}
QCheckBox#toggleChat {
    color: #8ca394;
    font-size: 12px;
    spacing: 6px;
}
QCheckBox#toggleChat::indicator {
    width: 16px;
    height: 16px;
    border-radius: 4px;
    border: 1px solid rgba(0, 255, 133, 0.3);
    background: #090e0b;
}
QCheckBox#toggleChat::indicator:checked {
    background: #00FF85;
    border-color: #00FF85;
}


/* Component Library Cards & Pills */
QFrame#compCard {
    background: #0d1410;
    border: 1px solid rgba(0, 255, 133, 0.14);
    border-radius: 14px;
}
QFrame#compCard:hover {
    background: #121c16;
    border: 1px solid #00FF85;
}
QFrame#imgPanel {
    background: #070c09;
    border-radius: 10px;
}
QPushButton[kind="catPill"] {
    background: #0e1511;
    border: 1px solid rgba(0, 255, 133, 0.16);
    border-radius: 15px;
    padding: 6px 14px;
    color: #8ca394;
    font-size: 13px;
    font-weight: 500;
}
QPushButton[kind="catPill"]:hover {
    background: #142018;
    color: #f3fbf5;
    border-color: rgba(0, 255, 133, 0.4);
}
QPushButton[kind="catPillActive"] {
    background: #00FF85;
    border: 1px solid #00FF85;
    border-radius: 15px;
    padding: 6px 14px;
    color: #060907;
    font-size: 13px;
    font-weight: 700;
}

QFrame#typingCard { background:#101722; border:1px dashed #2f4362; border-radius:12px; }

QLabel#brand { font-size:18px; font-weight:800; color:#ffffff; letter-spacing:0.5px; }
QLabel#title { font-size:28px; font-weight:800; color:#f8fafc; letter-spacing:0.5px; }
QLabel#h1 { font-size:20px; font-weight:700; color:#f1f5f9; }
QLabel#h2 { font-size:16px; font-weight:600; color:#e2e8f0; }
QLabel#subtitle { font-size:14.5px; color:#94a3b8; }
QLabel#muted { color:#8292a8; font-size:13px; }
QLabel#caption { color:#75849a; font-size:12px; }
QLabel#badge { background:#1a273b; border:1px solid #293d5c; border-radius:8px; padding:3px 8px; color:#93c5fd; font-size:11.5px; font-weight:600; }
QLabel#badgeOk { background:#12281e; border:1px solid #1f4f39; border-radius:8px; padding:3px 8px; color:#6ee7b7; font-size:11.5px; font-weight:600; }
QLabel#badgeWarn { background:#302110; border:1px solid #633f17; border-radius:8px; padding:3px 8px; color:#fcd34d; font-size:11.5px; font-weight:600; }
QLabel#codeBlock { background:#090d14; border:1px solid #1e2838; border-radius:8px; padding:10px 12px; font-family:'Cascadia Code','Consolas','Courier New',monospace; font-size:12.5px; color:#67e8f9; }

QScrollBar:vertical { background:#0d121a; width:10px; margin:0; }
QScrollBar::handle:vertical { background:#27364b; min-height:24px; border-radius:5px; margin:2px; }
QScrollBar::handle:vertical:hover { background:#3b82f6; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height:0; }
QScrollBar:horizontal { background:#0d121a; height:10px; margin:0; }
QScrollBar::handle:horizontal { background:#27364b; min-width:24px; border-radius:5px; margin:2px; }
QScrollBar::handle:horizontal:hover { background:#3b82f6; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width:0; }

QProgressBar { background:#111823; border:1px solid #233044; border-radius:6px; text-align:center; }
QProgressBar::chunk { background:#3b82f6; border-radius:5px; }
QTreeWidget { background:#101722; border:1px solid #222f42; border-radius:10px; outline:0; color:#cbd5e1; }
QTreeWidget::item { padding:6px; border-radius:4px; }
QTreeWidget::item:hover { background:#1b2536; }
QTreeWidget::item:selected { background:#2563eb; color:#ffffff; }
QTabWidget::pane { border:1px solid #222f42; border-radius:12px; background:#111722; }
QTabBar::tab { background:#141b26; border:1px solid #222f42; border-bottom:none; border-top-left-radius:8px; border-top-right-radius:8px; padding:8px 18px; margin-right:4px; color:#94a3b8; font-weight:600; }
QTabBar::tab:selected { background:#1d4ed8; color:#ffffff; border-color:#3b82f6; }
QTabBar::tab:hover:!selected { background:#1b2434; color:#e2e8f0; }

/* Quick Action Cards */
QPushButton[kind="qaCardPrimary"] {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #0d2818, stop:1 #081a10);
    border: 1.5px solid #00FF85;
    border-radius: 14px;
    padding: 0px;
    text-align: left;
}
QPushButton[kind="qaCardPrimary"]:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #123822, stop:1 #0b2416);
    border-color: #39FF14;
}
QPushButton[kind="qaCardTeal"] {
    background: #0a1314;
    border: 1px solid rgba(20, 184, 166, 0.28);
    border-radius: 14px;
    padding: 0px;
    text-align: left;
}
QPushButton[kind="qaCardTeal"]:hover {
    background: #0f1c1d;
    border-color: #14B8A6;
}
QPushButton[kind="qaCardMint"] {
    background: #091410;
    border: 1px solid rgba(16, 185, 129, 0.28);
    border-radius: 14px;
    padding: 0px;
    text-align: left;
}
QPushButton[kind="qaCardMint"]:hover {
    background: #0e1e17;
    border-color: #10B981;
}
QPushButton[kind="qaCardLime"] {
    background: #11150a;
    border: 1px solid rgba(132, 204, 22, 0.28);
    border-radius: 14px;
    padding: 0px;
    text-align: left;
}
QPushButton[kind="qaCardLime"]:hover {
    background: #19200f;
    border-color: #84CC16;
}
QLabel#qaTitle { font-size: 15px; font-weight: 700; color: #f3fbf5; }
QLabel#qaDesc { font-size: 12px; color: #8da394; }
QPushButton[kind="qaCardPrimary"] QLabel#qaTitle { color: #00FF85; }

/* Sub-cards and Stat boxes */
QFrame#subCard {
    background: #0a0f0c;
    border: 1px solid rgba(0, 255, 133, 0.12);
    border-radius: 10px;
}
QFrame#subCard:hover {
    background: #101712;
    border-color: rgba(0, 255, 133, 0.28);
}
QLabel#subCardTitle { font-weight: 600; font-size: 13px; color: #f3fbf5; }
QFrame#statBoxGreen {
    background: rgba(0, 255, 133, 0.05);
    border: 1px solid rgba(0, 255, 133, 0.16);
    border-radius: 10px;
}
QFrame#statBoxTeal {
    background: rgba(20, 184, 166, 0.05);
    border: 1px solid rgba(20, 184, 166, 0.16);
    border-radius: 10px;
}
QLabel#statGreenVal { font-size: 20px; font-weight: 700; color: #00FF85; }
QLabel#statTealVal { font-size: 20px; font-weight: 700; color: #14B8A6; }

"""

LIGHT_STYLE = """
QWidget { background:#f8fafc; color:#0f172a; font-family:'Segoe UI','Inter',system-ui,sans-serif; font-size:14px; }
QLabel { background:transparent; }
QPushButton { background:#ffffff; border:1px solid #cbd5e1; border-radius:10px; padding:9px 16px; color:#0f172a; font-weight:500; }
QPushButton:hover { background:#f1f5f9; border-color:#94a3b8; }
QPushButton:pressed { background:#e2e8f0; }
QPushButton:disabled { color:#94a3b8; background:#f1f5f9; border-color:#e2e8f0; }

QPushButton[kind="primary"] { background:#2563eb; border:none; color:#ffffff; font-weight:600; }
QPushButton[kind="primary"]:hover { background:#1d4ed8; }
QPushButton[kind="primary"]:pressed { background:#1e40af; }
QPushButton[kind="primary"]:disabled { background:#e2e8f0; color:#94a3b8; }

QPushButton[kind="secondary"] { background:#ffffff; border:1px solid #cbd5e1; color:#334155; font-weight:500; }
QPushButton[kind="secondary"]:hover { background:#f1f5f9; color:#0f172a; border-color:#94a3b8; }

QPushButton[kind="danger"] { background:#fee2e2; border:1px solid #fca5a5; color:#b91c1c; }
QPushButton[kind="danger"]:hover { background:#fecaca; border-color:#f87171; color:#991b1b; }

QPushButton[kind="nav"] { background:transparent; border:none; border-radius:8px; padding:8px 14px; color:#64748b; font-weight:600; font-size:14px; }
QPushButton[kind="nav"]:hover { background:#e2e8f0; color:#0f172a; }
QPushButton[kind="navActive"] { background:#2563eb; border:none; border-radius:8px; padding:8px 14px; color:#ffffff; font-weight:700; font-size:14px; }

QPushButton[kind="chip"] { background:#ffffff; border:1px solid #cbd5e1; border-radius:16px; padding:6px 14px; color:#475569; font-size:13px; font-weight:500; }
QPushButton[kind="chip"]:hover { background:#f1f5f9; color:#0f172a; border-color:#94a3b8; }
QPushButton[kind="chipActive"] { background:#2563eb; border:1px solid #1d4ed8; border-radius:16px; padding:6px 14px; color:#ffffff; font-size:13px; font-weight:600; }

QPushButton[kind="cardAction"] { text-align:left; border-radius:14px; background:#ffffff; border:1px solid #e2e8f0; padding:16px; }
QPushButton[kind="cardAction"]:hover { border-color:#2563eb; background:#f8fafc; }

QLineEdit, QComboBox, QSpinBox { background:#ffffff; border:1px solid #cbd5e1; border-radius:10px; padding:9px 12px; color:#0f172a; selection-background-color:#2563eb; }
QLineEdit:focus, QComboBox:focus, QSpinBox:focus { border-color:#2563eb; background:#ffffff; }
QComboBox QAbstractItemView { background:#ffffff; border:1px solid #cbd5e1; selection-background-color:#2563eb; selection-color:white; }

QListWidget { background:#ffffff; border:1px solid #e2e8f0; border-radius:12px; padding:6px; outline:0; }
QListWidget::item { padding:10px 12px; border-radius:8px; margin-bottom:4px; }
QListWidget::item:hover { background:#f1f5f9; }
QListWidget::item:selected { background:#e0f2fe; color:#0369a1; }

QFrame#card { background:#ffffff; border:1px solid #e2e8f0; border-radius:14px; }
QFrame#accentCard { background:#eff6ff; border:1px solid #bfdbfe; border-radius:14px; }
QFrame#tipCard { background:#ffffff; border:1px solid #e2e8f0; border-radius:14px; padding:12px; }
QFrame#tipCard:hover { border-color:#2563eb; background:#f8fafc; }
QFrame#sidebarFrame { background:#f1f5f9; border-right:1px solid #e2e8f0; }

QFrame#userBubble { background:#dbeafe; border:1px solid #bfdbfe; border-radius:14px; }
QFrame#asstCard { background:#ffffff; border:1px solid #e2e8f0; border-radius:16px; }

/* Component Library Cards & Pills */
QFrame#compCard {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 14px;
}
QFrame#compCard:hover {
    background: #f8fafc;
    border: 1px solid #10B981;
}
QFrame#imgPanel {
    background: #f1f5f9;
    border-radius: 10px;
}
QPushButton[kind="catPill"] {
    background: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 15px;
    padding: 6px 14px;
    color: #475569;
    font-size: 13px;
    font-weight: 500;
}
QPushButton[kind="catPill"]:hover {
    background: #f1f5f9;
    color: #0f172a;
    border-color: #94a3b8;
}
QPushButton[kind="catPillActive"] {
    background: #10B981;
    border: 1px solid #10B981;
    border-radius: 15px;
    padding: 6px 14px;
    color: #ffffff;
    font-size: 13px;
    font-weight: 700;
}

QFrame#typingCard { background:#f8fafc; border:1px dashed #cbd5e1; border-radius:12px; }

QLabel#brand { font-size:18px; font-weight:800; color:#0f172a; letter-spacing:0.5px; }
QLabel#title { font-size:28px; font-weight:800; color:#0f172a; letter-spacing:0.5px; }
QLabel#h1 { font-size:20px; font-weight:700; color:#0f172a; }
QLabel#h2 { font-size:16px; font-weight:600; color:#1e293b; }
QLabel#subtitle { font-size:14.5px; color:#475569; }
QLabel#muted { color:#64748b; font-size:13px; }
QLabel#caption { color:#64748b; font-size:12px; }
QLabel#badge { background:#eff6ff; border:1px solid #bfdbfe; border-radius:8px; padding:3px 8px; color:#1d4ed8; font-size:11.5px; font-weight:600; }
QLabel#badgeOk { background:#ecfdf5; border:1px solid #a7f3d0; border-radius:8px; padding:3px 8px; color:#047857; font-size:11.5px; font-weight:600; }
QLabel#badgeWarn { background:#fffbeb; border:1px solid #fde68a; border-radius:8px; padding:3px 8px; color:#b45309; font-size:11.5px; font-weight:600; }
QLabel#codeBlock { background:#f1f5f9; border:1px solid #e2e8f0; border-radius:8px; padding:10px 12px; font-family:'Cascadia Code','Consolas','Courier New',monospace; font-size:12.5px; color:#0369a1; }

QScrollBar:vertical { background:#f8fafc; width:10px; margin:0; }
QScrollBar::handle:vertical { background:#cbd5e1; min-height:24px; border-radius:5px; margin:2px; }
QScrollBar::handle:vertical:hover { background:#2563eb; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height:0; }
QScrollBar:horizontal { background:#f8fafc; height:10px; margin:0; }
QScrollBar::handle:horizontal { background:#cbd5e1; min-width:24px; border-radius:5px; margin:2px; }
QScrollBar::handle:horizontal:hover { background:#2563eb; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width:0; }

QProgressBar { background:#f1f5f9; border:1px solid #cbd5e1; border-radius:6px; text-align:center; }
QProgressBar::chunk { background:#2563eb; border-radius:5px; }
QTreeWidget { background:#ffffff; border:1px solid #e2e8f0; border-radius:10px; outline:0; color:#334155; }
QTreeWidget::item { padding:6px; border-radius:4px; }
QTreeWidget::item:hover { background:#f1f5f9; }
QTreeWidget::item:selected { background:#2563eb; color:#ffffff; }
QTabWidget::pane { border:1px solid #e2e8f0; border-radius:12px; background:#ffffff; }
QTabBar::tab { background:#f8fafc; border:1px solid #e2e8f0; border-bottom:none; border-top-left-radius:8px; border-top-right-radius:8px; padding:8px 18px; margin-right:4px; color:#64748b; font-weight:600; }
QTabBar::tab:selected { background:#2563eb; color:#ffffff; border-color:#1d4ed8; }
QTabBar::tab:hover:!selected { background:#e2e8f0; color:#0f172a; }

/* Quick Action Cards */
QPushButton[kind="qaCardPrimary"] {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #e6fcf0, stop:1 #d1fae5);
    border: 1.5px solid #10b981;
    border-radius: 14px;
    padding: 0px;
    text-align: left;
}
QPushButton[kind="qaCardPrimary"]:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #d1fae5, stop:1 #a7f3d0);
    border-color: #059669;
}
QPushButton[kind="qaCardTeal"] {
    background: #f0fdfa;
    border: 1px solid #99f6e4;
    border-radius: 14px;
    padding: 0px;
    text-align: left;
}
QPushButton[kind="qaCardTeal"]:hover {
    background: #ccfbf1;
    border-color: #0d9488;
}
QPushButton[kind="qaCardMint"] {
    background: #f0fdf4;
    border: 1px solid #a7f3d0;
    border-radius: 14px;
    padding: 0px;
    text-align: left;
}
QPushButton[kind="qaCardMint"]:hover {
    background: #dcfce7;
    border-color: #059669;
}
QPushButton[kind="qaCardLime"] {
    background: #f7fee7;
    border: 1px solid #d9f99d;
    border-radius: 14px;
    padding: 0px;
    text-align: left;
}
QPushButton[kind="qaCardLime"]:hover {
    background: #ecfccb;
    border-color: #65a30d;
}
QLabel#qaTitle { font-size: 15px; font-weight: 700; color: #0f172a; }
QLabel#qaDesc { font-size: 12px; color: #64748b; }
QPushButton[kind="qaCardPrimary"] QLabel#qaTitle { color: #047857; }

/* Sub-cards and Stat boxes */
QFrame#subCard {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
}
QFrame#subCard:hover {
    background: #f8fafc;
    border-color: #cbd5e1;
}
QLabel#subCardTitle { font-weight: 600; font-size: 13px; color: #0f172a; }
QFrame#statBoxGreen {
    background: #ecfdf5;
    border: 1px solid #a7f3d0;
    border-radius: 10px;
}
QFrame#statBoxTeal {
    background: #f0fdfa;
    border: 1px solid #99f6e4;
    border-radius: 10px;
}
QLabel#statGreenVal { font-size: 20px; font-weight: 700; color: #047857; }
QLabel#statTealVal { font-size: 20px; font-weight: 700; color: #0d9488; }

"""

# Default backward compatibility alias
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



class QuickActionCard(QPushButton):
    """Standout card-style action button with icon circle, bold title, and description."""
    def __init__(self, icon_name, title_text, desc_text, accent_color, kind="qaCardTeal", slot=None):
        super().__init__()
        self.setProperty("kind", kind)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.setMinimumHeight(116)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(18, 16, 18, 16)
        lay.setSpacing(10)

        # Icon Circle
        self.icon_circle = QLabel()
        self.icon_circle.setFixedSize(46, 46)
        self.icon_circle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_circle.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.icon_circle.setStyleSheet(
            f"background-color: {accent_color}22; "
            f"border: 1px solid {accent_color}55; "
            f"border-radius: 23px;"
        )
        self.icon_circle.setPixmap(get_pixmap(icon_name, accent_color, 24))
        lay.addWidget(self.icon_circle)

        # Title
        self.title_lbl = QLabel(title_text)
        self.title_lbl.setObjectName("qaTitle")
        self.title_lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        lay.addWidget(self.title_lbl)

        # Description
        self.desc_lbl = QLabel(desc_text)
        self.desc_lbl.setObjectName("qaDesc")
        self.desc_lbl.setWordWrap(True)
        self.desc_lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        lay.addWidget(self.desc_lbl)

        lay.addStretch()

        if slot:
            self.clicked.connect(slot)


class QuestionCard(QPushButton):
    """A clickable card with word-wrapped text."""
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
        row.addWidget(button("Add", "primary", self.accept))
        form.addRow(row)


class SettingsDialog(QDialog):
    """Configure Ollama URL and model choices."""
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
    """Live camera viewfinder with robust device fallback and disk picker option."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Live Camera Scanner")
        self.resize(720, 580)
        self.captured_path = None
        self.last_frame = None

        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(14)

        # Header
        top_row = QHBoxLayout()
        cam_icon = QLabel()
        cam_icon.setPixmap(get_pixmap("camera", "#00FF85", 22))
        top_row.addWidget(cam_icon)
        top_row.addWidget(label("Component Camera Scan", "h1"))
        top_row.addStretch()
        top_row.addWidget(label("Align component clearly in frame", "caption"))
        lay.addLayout(top_row)

        self.view = QLabel("Initializing camera...", self)
        self.view.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.view.setStyleSheet("background:#080c12; border:1px solid #1f2a3a; border-radius:12px; color:#94a3b8;")
        self.view.setMinimumSize(660, 420)
        lay.addWidget(self.view, 1)

        btn_row = QHBoxLayout()
        self.fallback_btn = button("Choose Photo from Disk", "secondary", slot=self.choose_disk_photo)
        self.fallback_btn.setIcon(get_icon("upload", "#94a3b8", 16))
        self.cancel_btn = button("Cancel", slot=self.reject)
        self.snap_btn = button("Capture Photo", "primary", slot=self.capture_frame)
        self.snap_btn.setIcon(get_icon("camera", "#ffffff", 16))
        self.snap_btn.setMinimumWidth(160)

        btn_row.addWidget(self.cancel_btn)
        btn_row.addWidget(self.fallback_btn)
        btn_row.addStretch()
        btn_row.addWidget(self.snap_btn)
        lay.addLayout(btn_row)

        # Try opening camera 0, then 1 with DirectShow on Windows
        self.cap = None
        for idx in (0, 1):
            if os.name == 'nt':
                c = cv2.VideoCapture(idx, cv2.CAP_DSHOW)
            else:
                c = cv2.VideoCapture(idx)
            if c.isOpened():
                ret, test_f = c.read()
                if ret and test_f is not None:
                    self.cap = c
                    break
                c.release()

        if self.cap is None or not self.cap.isOpened():
            self.view.setText(
                "No live camera detected or camera permission was denied.\n\n"
                "Please verify your camera is plugged in and permissions are enabled in Windows Settings,\n"
                "or click 'Choose Photo from Disk' below to scan a component image."
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
        self.setWindowTitle("Voice Question Input")
        self.setFixedSize(500, 270)
        self.transcribed_text = ""

        lay = QVBoxLayout(self)
        lay.setContentsMargins(28, 24, 28, 22)
        lay.setSpacing(16)

        header_lay = QHBoxLayout()
        mic_icon = QLabel()
        mic_icon.setPixmap(get_pixmap("mic", "#00FF85", 36))
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
            "background:#121824; border:1px solid #233145; border-radius:10px; "
            "padding:10px 14px; font-size:13.5px; color:#cbd5e1;"
        )
        self.status_box.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self.status_box)

        btn_row = QHBoxLayout()
        self.cancel_btn = button("Cancel", slot=self.reject)
        self.done_btn = button("Done Speaking", "primary", slot=self.on_done_clicked)
        self.done_btn.setIcon(get_icon("check", "#ffffff", 16))
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
        self.status_box.setText("Hearing speech... (auto-finishing on pause)")
        self.status_box.setStyleSheet(
            "background:#10261b; border:1px solid #1e5a3c; border-radius:10px; "
            "padding:10px 14px; font-size:13.5px; color:#6ee7b7; font-weight:600;"
        )

    def _on_status(self, text):
        self.sub_lbl.setText(text)
        if "Transcribing" in text:
            self.meter.setValue(0)
            self.status_box.setText("Transcribing speech with Whisper AI...")
            self.status_box.setStyleSheet(
                "background:#17253d; border:1px solid #2d5599; border-radius:10px; "
                "padding:10px 14px; font-size:13.5px; color:#93c5fd; font-weight:600;"
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
        lbl.setStyleSheet("background:#080c12; border-radius:12px;")
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

        # Controls bar
        ctrl_bar = QHBoxLayout()
        ctrl_bar.setSpacing(10)

        self.prev_btn = button("Prev", "secondary", self.prev_page)
        self.prev_btn.setIcon(get_icon("chevron-left", "#cbd5e1", 14))
        self.next_btn = button("Next", "secondary", self.next_page)
        self.next_btn.setIcon(get_icon("chevron-right", "#cbd5e1", 14))
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

        # Splitter: Left Outline/Search | Right Document Page View
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left panel: Tabs (TOC Outline vs Search)
        left_tabs = QTabWidget()
        left_tabs.setFixedWidth(300)

        # TOC Tab
        toc_widget = QWidget()
        toc_lay = QVBoxLayout(toc_widget)
        toc_lay.setContentsMargins(6, 6, 6, 6)
        self.toc_tree = QTreeWidget()
        self.toc_tree.setHeaderLabel("Table of Contents")
        self.toc_tree.itemClicked.connect(self._on_toc_clicked)
        toc_lay.addWidget(self.toc_tree)
        left_tabs.addTab(toc_widget, "Outline")
        left_tabs.setTabIcon(0, get_icon("book-open", "#10B981", 16))

        # Search Tab
        search_widget = QWidget()
        s_lay = QVBoxLayout(search_widget)
        s_lay.setContentsMargins(6, 6, 6, 6)
        s_lay.setSpacing(6)
        s_input_row = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search in manual...")
        self.search_input.returnPressed.connect(self.search_manual)
        self.search_btn = button("", slot=self.search_manual)
        self.search_btn.setIcon(get_icon("search", "#cbd5e1", 16))
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

        left_tabs.addTab(search_widget, "Search")
        left_tabs.setTabIcon(1, get_icon("search", "#38BDF8", 16))
        splitter.addWidget(left_tabs)

        # Right panel: Page view inside ScrollArea
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
            self.search_res_header.setText(f"SEARCH RESULTS ({len(matches)} found)")
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



def render_markdown_html(text: str, manuals_map=None) -> str:
    """Convert markdown into clean HTML with bold, code blocks, lists, and clickable manual citations."""
    if not text:
        return ""
    import html as html_lib

    code_blocks = []
    def save_code(m):
        code_blocks.append(m.group(2))
        return f"___CODE_BLOCK_{len(code_blocks)-1}___"

    text = re.sub(r"```([a-zA-Z0-9_-]*)\n?(.*?)```", save_code, text, flags=re.DOTALL)

    def make_citation(m):
        m_name = m.group(1).strip()
        p_num = m.group(2).strip()
        mid = "0"
        if manuals_map and m_name in manuals_map:
            mid = str(manuals_map[m_name])
        return f'<a href="manual://{mid}/{p_num}" style="color:#00FF85; text-decoration:none; font-weight:600; background:rgba(0,255,133,0.12); padding:2px 7px; border-radius:5px; border:1px solid rgba(0,255,133,0.25);">[{m_name}, p.{p_num}]</a>'

    text = re.sub(r"\[([^,\]]+),\s*(?:p\.|page|Page)\s*(\d+)\]", make_citation, text)
    text = re.sub(r"\[(?:p\.|page|Page)\s*(\d+)\]", r'<a href="manual://0/\1" style="color:#00FF85; text-decoration:none; font-weight:600; background:rgba(0,255,133,0.12); padding:2px 6px; border-radius:4px; border:1px solid rgba(0,255,133,0.25);">[p. \1]</a>', text)

    text = re.sub(r"^###\s+(.+)$", r'<h3 style="margin:8px 0 4px 0; font-size:15px; color:#f3fbf5;">\1</h3>', text, flags=re.MULTILINE)
    text = re.sub(r"^##\s+(.+)$", r'<h2 style="margin:10px 0 4px 0; font-size:17px; color:#f3fbf5;">\1</h2>', text, flags=re.MULTILINE)
    text = re.sub(r"^#\s+(.+)$", r'<h1 style="margin:12px 0 6px 0; font-size:19px; color:#00FF85;">\1</h1>', text, flags=re.MULTILINE)

    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"\*(.+?)\*", r"<i>\1</i>", text)
    text = re.sub(r"`([^`\n]+)`", r'<code style="background:#090d14; color:#67e8f9; padding:2px 5px; border-radius:4px; font-family:monospace; font-size:12.5px;">\1</code>', text)

    lines = text.split("\n")
    formatted_lines = []
    in_list = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("- ") or stripped.startswith("* ") or stripped.startswith("• "):
            if not in_list:
                formatted_lines.append('<ul style="margin:4px 0; padding-left:20px;">')
                in_list = True
            formatted_lines.append(f'<li style="margin-bottom:3px;">{stripped[2:]}</li>')
        elif re.match(r"^\d+\.\s+", stripped):
            item = re.sub(r"^\d+\.\s+", "", stripped)
            if not in_list:
                formatted_lines.append('<ol style="margin:4px 0; padding-left:20px;">')
                in_list = True
            formatted_lines.append(f'<li style="margin-bottom:3px;">{item}</li>')
        else:
            if in_list:
                formatted_lines.append('</ul>' if formatted_lines[-1].startswith('<li') else '</ol>')
                in_list = False
            formatted_lines.append(line)
    if in_list:
        formatted_lines.append('</ul>')

    text = "<br>".join(formatted_lines)
    text = text.replace("</ul><br>", "</ul>").replace("</ol><br>", "</ol>")

    for idx, code in enumerate(code_blocks):
        escaped_code = html_lib.escape(code.strip())
        block_html = (
            f'<div style="background:#090d14; border:1px solid #1e2838; border-radius:8px; padding:10px 14px; margin:8px 0; font-family:monospace; font-size:12.5px; color:#67e8f9; overflow-x:auto;">'
            f'<pre style="margin:0;">{escaped_code}</pre></div>'
        )
        text = text.replace(f"___CODE_BLOCK_{idx}___", block_html)

    return text


class ImageLightboxDialog(QDialog):
    """Full-screen interactive image lightbox with zoom in/out, pan, reset, and Esc close."""
    def __init__(self, *args, **kwargs):
        parent = kwargs.pop("parent", None)
        title = kwargs.pop("title", "Image Viewer")
        image_path = kwargs.pop("image_path", None)
        if len(args) == 3:
            parent, image_path, title = args
        elif len(args) == 2:
            if isinstance(args[0], str):
                image_path, title = args
            else:
                parent, image_path = args
        elif len(args) == 1:
            if isinstance(args[0], str):
                image_path = args[0]
            else:
                parent = args[0]
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumSize(820, 620)
        self.image_path = image_path
        self.zoom_factor = 1.0
        self.orig_pixmap = QPixmap(image_path) if image_path and os.path.isfile(image_path) else QPixmap()

        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 12, 16, 16)
        lay.setSpacing(10)

        t_bar = QHBoxLayout()
        t_bar.addWidget(label(os.path.basename(image_path) if image_path else "Image", "h2", wrap=False))
        t_bar.addStretch()

        btn_out = button("-", slot=self.zoom_out)
        self.zoom_lbl = label("100%", "caption")
        btn_in = button("+", slot=self.zoom_in)
        btn_reset = button("Reset", slot=self.zoom_reset)
        btn_close = button("Close", slot=self.accept)

        for b in (btn_out, self.zoom_lbl, btn_in, btn_reset, btn_close):
            t_bar.addWidget(b)
        lay.addLayout(t_bar)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("background:#060907; border:1px solid #1f2d24; border-radius:10px;")
        self.img_lbl = QLabel()
        self.img_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.scroll.setWidget(self.img_lbl)
        lay.addWidget(self.scroll, 1)

        self.update_image()

    def zoom_in(self):
        self.zoom_factor = min(4.0, self.zoom_factor + 0.25)
        self.update_image()

    def zoom_out(self):
        self.zoom_factor = max(0.25, self.zoom_factor - 0.25)
        self.update_image()

    def zoom_reset(self):
        self.zoom_factor = 1.0
        self.update_image()

    def update_image(self):
        if self.orig_pixmap.isNull():
            self.img_lbl.setText("No image available")
            return
        w = int(self.orig_pixmap.width() * self.zoom_factor)
        h = int(self.orig_pixmap.height() * self.zoom_factor)
        scaled = self.orig_pixmap.scaled(w, h, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.img_lbl.setPixmap(scaled)
        self.img_lbl.setFixedSize(scaled.size())
        self.zoom_lbl.setText(f"{int(self.zoom_factor * 100)}%")

    def wheelEvent(self, event):
        if event.angleDelta().y() > 0:
            self.zoom_in()
        else:
            self.zoom_out()
        event.accept()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.accept()
        else:
            super().keyPressEvent(event)


class ManualScopeDialog(QDialog):
    """Picker dialog listing all manuals with search box, All manuals option, and checkmarks."""
    def __init__(self, parent, current_manual_id=None):
        super().__init__(parent)
        self.setWindowTitle("Select Manual Search Scope")
        self.setMinimumSize(480, 420)
        self.selected_manual_id = current_manual_id

        lay = QVBoxLayout(self)
        lay.setContentsMargins(18, 16, 18, 16)
        lay.setSpacing(12)

        lay.addWidget(label("MANUAL SEARCH SCOPE", "caption", wrap=False))
        sub = label("Choose whether to search across all uploaded manuals together or focus on a specific manual.", "subtitle")
        lay.addWidget(sub)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search indexed manuals...")
        self.search_input.textChanged.connect(self.filter_items)
        lay.addWidget(self.search_input)

        self.list_widget = QListWidget()
        self.list_widget.itemDoubleClicked.connect(self.on_item_chosen)
        lay.addWidget(self.list_widget, 1)

        self.populate_list()

        b_row = QHBoxLayout()
        b_row.addStretch()
        cancel_b = button("Cancel", slot=self.reject)
        apply_b = button("Apply Scope", "primary", slot=self.apply_selection)
        b_row.addWidget(cancel_b)
        b_row.addWidget(apply_b)
        lay.addLayout(b_row)

    def populate_list(self):
        self.list_widget.clear()
        manuals = db.list_manuals()
        total_p = sum(m.get("page_count", 0) for m in manuals)

        all_item = QListWidgetItem(f"All Manuals ({len(manuals)} manuals · {total_p} pages)")
        all_item.setData(Qt.ItemDataRole.UserRole, None)
        all_item.setIcon(get_icon("layers", "#00FF85", 16))
        if self.selected_manual_id is None:
            all_item.setText(all_item.text() + "  [Active]")
            all_item.setSelected(True)
        self.list_widget.addItem(all_item)

        for m in manuals:
            desc = f"{m['name']} — {m.get('page_count', 0)} pages"
            if m.get('manufacturer'):
                desc += f" ({m['manufacturer']})"
            item = QListWidgetItem(desc)
            item.setData(Qt.ItemDataRole.UserRole, m["id"])
            item.setIcon(get_icon("book-open", "#10B981", 16))
            if self.selected_manual_id == m["id"]:
                item.setText(item.text() + "  [Active]")
                item.setSelected(True)
            self.list_widget.addItem(item)

    def filter_items(self, text):
        query = text.strip().lower()
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            item.setHidden(query not in item.text().lower())

    def on_item_chosen(self, item):
        self.selected_manual_id = item.data(Qt.ItemDataRole.UserRole)
        self.accept()

    def apply_selection(self):
        item = self.list_widget.currentItem()
        if item:
            self.selected_manual_id = item.data(Qt.ItemDataRole.UserRole)
        self.accept()


class ManualsManagerDialog(QDialog):
    """Modal dialog to view and delete indexed hardware manuals."""
    def __init__(self, parent, on_delete_cb=None, on_read_cb=None, on_add_cb=None):
        super().__init__(parent)
        self.setWindowTitle("Hardware Manuals Manager")
        self.setMinimumSize(560, 440)
        self.on_delete_cb = on_delete_cb
        self.on_read_cb = on_read_cb
        self.on_add_cb = on_add_cb

        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 16, 20, 16)
        lay.setSpacing(14)

        head = QHBoxLayout()
        head.addWidget(label("INDEXED HARDWARE MANUALS", "h1", wrap=False))
        head.addStretch()
        add_btn = button("Upload Manuals", "primary", slot=self.add_manuals)
        add_btn.setIcon(get_icon("upload", "#ffffff", 14))
        head.addWidget(add_btn)
        lay.addLayout(head)

        self.list_widget = QListWidget()
        lay.addWidget(self.list_widget, 1)

        self.refresh_list()

        close_b = button("Close", slot=self.accept)
        b_row = QHBoxLayout()
        b_row.addStretch()
        b_row.addWidget(close_b)
        lay.addLayout(b_row)

    def refresh_list(self):
        self.list_widget.clear()
        manuals = db.list_manuals()
        if not manuals:
            item = QListWidgetItem("No manuals indexed yet.")
            self.list_widget.addItem(item)
            return

        for m in manuals:
            item = QListWidgetItem()
            item.setSizeHint(QSize(0, 56))
            self.list_widget.addItem(item)

            row = QFrame()
            row.setObjectName("subCard")
            r_lay = QHBoxLayout(row)
            r_lay.setContentsMargins(10, 6, 10, 6)
            r_lay.setSpacing(10)

            icon_lbl = QLabel()
            icon_lbl.setPixmap(get_pixmap("book-open", "#10B981", 18))
            r_lay.addWidget(icon_lbl)

            col = QVBoxLayout()
            col.setSpacing(2)
            name_lbl = label(m["name"][:36], "subCardTitle", wrap=False)
            extra = f"{m.get('page_count', 0)} pages"
            if m.get("manufacturer"):
                extra += f" · {m['manufacturer']}"
            sub_lbl = label(extra, "caption", wrap=False)
            col.addWidget(name_lbl)
            col.addWidget(sub_lbl)
            r_lay.addLayout(col, 1)

            mid = m["id"]
            read_b = button("Read", slot=lambda _, _id=mid: self.read_manual(_id))
            read_b.setIcon(get_icon("book-open", "#cbd5e1", 12))
            r_lay.addWidget(read_b)

            del_b = button("", "danger", slot=lambda _, _id=mid: self.delete_manual(_id))
            del_b.setIcon(get_icon("trash-2", "#fca5a5", 14))
            del_b.setToolTip("Delete this manual")
            r_lay.addWidget(del_b)

            self.list_widget.setItemWidget(item, row)

    def read_manual(self, mid):
        if self.on_read_cb:
            self.on_read_cb(mid)
        self.accept()

    def delete_manual(self, mid):
        if QMessageBox.question(self, "Delete Manual", "Are you sure you want to delete this manual and its indexed pages?") == QMessageBox.StandardButton.Yes:
            if self.on_delete_cb:
                self.on_delete_cb(mid)
            self.refresh_list()

    def add_manuals(self):
        if self.on_add_cb:
            self.on_add_cb()
        self.refresh_list()


class ChatTextEdit(QTextEdit):
    """Auto-growing multi-line text input with Enter to send and Shift+Enter for new line."""
    submit_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPlaceholderText("Ask about an IC, pinout, circuit problem, or follow-up question...")
        self.setFixedHeight(46)
        self.document().documentLayout().documentSizeChanged.connect(self.adjust_height)

    def adjust_height(self):
        doc_h = int(self.document().size().height()) + 14
        new_h = max(46, min(140, doc_h))
        self.setFixedHeight(new_h)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                super().keyPressEvent(event)
            else:
                self.submit_requested.emit()
        else:
            super().keyPressEvent(event)


class ChatHistoryItemWidget(QFrame):
    """Sidebar chat item with green active highlight, date, and hover actions (pin, rename, delete)."""
    clicked = pyqtSignal(int)
    rename_requested = pyqtSignal(int)
    pin_requested = pyqtSignal(int, bool)
    delete_requested = pyqtSignal(int)

    def __init__(self, conv_id, title, date_str, is_active=False, is_pinned=False, parent=None):
        super().__init__(parent)
        self.conv_id = conv_id
        self.is_active = is_active
        self.is_pinned = is_pinned
        self.setObjectName("chatItem")
        self.setProperty("active", "true" if is_active else "false")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(48)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(10, 4, 8, 4)
        lay.setSpacing(8)

        self.icon_lbl = QLabel()
        icon_name = "pin" if is_pinned else "message-square"
        icon_color = "#00FF85" if (is_pinned or is_active) else "#64748b"
        self.icon_lbl.setPixmap(get_pixmap(icon_name, icon_color, 14))
        self.icon_lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        lay.addWidget(self.icon_lbl)

        text_col = QVBoxLayout()
        text_col.setSpacing(1)
        text_col.setContentsMargins(0, 0, 0, 0)

        display_title = title if len(title) <= 26 else title[:23] + "..."
        self.title_lbl = QLabel(display_title)
        self.title_lbl.setObjectName("chatItemTitle")
        self.title_lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        text_col.addWidget(self.title_lbl)

        self.date_lbl = QLabel(date_str)
        self.date_lbl.setObjectName("caption")
        self.date_lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        text_col.addWidget(self.date_lbl)
        lay.addLayout(text_col, 1)

        self.actions_box = QWidget()
        a_lay = QHBoxLayout(self.actions_box)
        a_lay.setContentsMargins(0, 0, 0, 0)
        a_lay.setSpacing(2)

        self.pin_b = button("", slot=self._on_pin)
        self.pin_b.setIcon(get_icon("pin", "#00FF85" if is_pinned else "#94a3b8", 12))
        self.pin_b.setToolTip("Unpin" if is_pinned else "Pin to top")
        self.pin_b.setFixedSize(24, 24)
        a_lay.addWidget(self.pin_b)

        self.edit_b = button("", slot=self._on_rename)
        self.edit_b.setIcon(get_icon("edit", "#94a3b8", 12))
        self.edit_b.setToolTip("Rename chat")
        self.edit_b.setFixedSize(24, 24)
        a_lay.addWidget(self.edit_b)

        self.del_b = button("", "danger", slot=self._on_delete)
        self.del_b.setIcon(get_icon("trash-2", "#fca5a5", 12))
        self.del_b.setToolTip("Delete chat")
        self.del_b.setFixedSize(24, 24)
        a_lay.addWidget(self.del_b)

        self.actions_box.setVisible(False)
        lay.addWidget(self.actions_box)

    def enterEvent(self, event):
        self.actions_box.setVisible(True)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.actions_box.setVisible(False)
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.conv_id)
        super().mousePressEvent(event)

    def _on_pin(self):
        self.pin_requested.emit(self.conv_id, not self.is_pinned)

    def _on_rename(self):
        self.rename_requested.emit(self.conv_id)

    def _on_delete(self):
        self.delete_requested.emit(self.conv_id)


class ChatMessageWidget(QWidget):
    """Visually distinct chat message card with Markdown, citations, step zoom, and actions."""
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
            head.addWidget(label("You", "badge"))
            head.addStretch()
            head.addWidget(label(self.created_at, "caption"))

            if self.win:
                edit_btn = button("", slot=self.edit_message)
                edit_btn.setIcon(get_icon("edit", "#94a3b8", 12))
                edit_btn.setToolTip("Edit and resend")
                edit_btn.setFixedSize(22, 22)
                head.addWidget(edit_btn)

            b_lay.addLayout(head)

            txt_lbl = QLabel()
            txt_lbl.setTextFormat(Qt.TextFormat.RichText)
            txt_lbl.setText(render_markdown_html(self.content))
            txt_lbl.setWordWrap(True)
            txt_lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            txt_lbl.setStyleSheet("font-size:14.5px; line-height:1.4;")
            b_lay.addWidget(txt_lbl)

            bubble.setMaximumWidth(720)
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
            head.addWidget(label("Assistant", "badgeOk", wrap=False))
            head.addStretch()
            head.addWidget(label(self.created_at, "caption"))
            c_lay.addLayout(head)

            title = (self.data or {}).get("title") if isinstance(self.data, dict) else ""
            if title:
                c_lay.addWidget(label(title.upper(), "h1"))

            summary = (self.data or {}).get("summary") if isinstance(self.data, dict) else ""
            if not summary and self.content:
                summary = self.content

            manuals_map = {m["name"]: m["id"] for m in db.list_manuals()}

            if summary:
                s_lbl = QLabel()
                s_lbl.setTextFormat(Qt.TextFormat.RichText)
                s_lbl.setText(render_markdown_html(summary, manuals_map))
                s_lbl.setWordWrap(True)
                s_lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse | Qt.TextInteractionFlag.LinksAccessibleByMouse)
                s_lbl.linkActivated.connect(self._on_link_clicked)
                s_lbl.setStyleSheet("font-size:14.5px; line-height:1.5;")
                c_lay.addWidget(s_lbl)

            warning = (self.data or {}).get("warning") if isinstance(self.data, dict) else ""
            if warning:
                c_lay.addWidget(label(f"WARNING: {warning}", "badgeWarn"))

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
                    s_row.addWidget(s_num, alignment=Qt.AlignmentFlag.AlignTop)

                    s_text = QLabel()
                    s_text.setTextFormat(Qt.TextFormat.RichText)
                    s_text.setText(render_markdown_html(s.get("text", ""), manuals_map))
                    s_text.setWordWrap(True)
                    s_text.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse | Qt.TextInteractionFlag.LinksAccessibleByMouse)
                    s_text.linkActivated.connect(self._on_link_clicked)
                    s_text.setStyleSheet("font-size:14px; line-height:1.4;")
                    s_row.addWidget(s_text, 1)

                    img_path = s.get("image")
                    if img_path and os.path.isfile(img_path):
                        img_btn = button("", slot=lambda _, p=img_path: self.open_lightbox(p))
                        img_btn.setIcon(get_icon("image", "#00FF85", 14))
                        img_btn.setToolTip("View full diagram / visual")
                        img_btn.setFixedHeight(26)
                        s_row.addWidget(img_btn, alignment=Qt.AlignmentFlag.AlignTop)

                    pno = s.get("page")
                    smid = s.get("manual_id")
                    if pno and self.win:
                        jump_b = button(f"p. {pno} ↗", "chip", slot=lambda _=False, p=pno, m=smid: self.win.open_user_manual(p, m))
                        jump_b.setFixedHeight(26)
                        s_row.addWidget(jump_b, alignment=Qt.AlignmentFlag.AlignTop)

                    sb_lay.addLayout(s_row)
                c_lay.addWidget(steps_box)

            # Footer actions: Copy, Regenerate, Export, Read Aloud, Thumbs Up / Down
            f_row = QHBoxLayout()
            copy_btn = button("Copy", "secondary", slot=self.copy_text)
            copy_btn.setIcon(get_icon("file-text", "#cbd5e1", 14))
            f_row.addWidget(copy_btn)

            if self.win:
                regen_btn = button("Regenerate", "secondary", slot=self.regenerate)
                regen_btn.setIcon(get_icon("refresh-cw", "#cbd5e1", 14))
                f_row.addWidget(regen_btn)

            exp_btn = button("Export Answer", "secondary")
            exp_btn.setIcon(get_icon("download", "#cbd5e1", 14))
            menu = QMenu(exp_btn)
            act_pdf = menu.addAction("Export as PDF (.pdf)")
            act_pdf.triggered.connect(lambda: self.export_answer("pdf"))
            act_md = menu.addAction("Export as Markdown (.md)")
            act_md.triggered.connect(lambda: self.export_answer("md"))
            act_txt = menu.addAction("Export as Plain Text (.txt)")
            act_txt.triggered.connect(lambda: self.export_answer("txt"))
            exp_btn.setMenu(menu)
            f_row.addWidget(exp_btn)

            read_btn = button("", "secondary", slot=self.read_aloud)
            read_btn.setIcon(get_icon("volume-2", "#00FF85", 14))
            read_btn.setToolTip("Read answer aloud")
            read_btn.setFixedSize(32, 32)
            f_row.addWidget(read_btn)

            thumb_up = button("", "secondary", slot=lambda: self.rate_answer(True))
            thumb_up.setIcon(get_icon("thumbs-up", "#10B981", 14))
            thumb_up.setToolTip("Helpful answer")
            thumb_up.setFixedSize(32, 32)
            f_row.addWidget(thumb_up)

            thumb_down = button("", "secondary", slot=lambda: self.rate_answer(False))
            thumb_down.setIcon(get_icon("thumbs-down", "#f87171", 14))
            thumb_down.setToolTip("Not helpful")
            thumb_down.setFixedSize(32, 32)
            f_row.addWidget(thumb_down)

            f_row.addStretch()
            c_lay.addLayout(f_row)

            card.setMaximumWidth(840)
            row.addWidget(card)
            row.addStretch()
            lay.addLayout(row)

    def _on_link_clicked(self, url):
        if url.startswith("manual://"):
            clean = url[len("manual://"):].strip("/")
            parts = clean.split("/")
            mid = None
            pno = 1
            if len(parts) >= 2:
                if parts[0].isdigit() and int(parts[0]) > 0:
                    mid = int(parts[0])
                if parts[1].isdigit():
                    pno = int(parts[1])
            elif len(parts) == 1 and parts[0].isdigit():
                pno = int(parts[0])
            if self.win:
                self.win.open_user_manual(pno, mid)

    def open_lightbox(self, img_path):
        dlg = ImageLightboxDialog(self.win, img_path)
        dlg.exec()

    def edit_message(self):
        if self.win:
            self.win.edit_user_message(self.content)

    def regenerate(self):
        if self.win:
            self.win.regenerate_last_answer()

    def read_aloud(self):
        if self.win:
            text = (self.data or {}).get("answer") or (self.data or {}).get("summary") or self.content
            self.win.read_aloud_answer(text)

    def rate_answer(self, is_positive):
        if self.win:
            msg = "Feedback recorded: Thank you!" if is_positive else "Feedback recorded: We'll improve this."
            QMessageBox.information(self.win, "Feedback", msg)

    def copy_text(self):
        text_to_copy = export_mod.format_answer_txt(self.data or {"answer": self.content})
        QApplication.clipboard().setText(text_to_copy)
        if self.win:
            QMessageBox.information(self.win, "Copied", "Answer text copied to clipboard!")

    def export_answer(self, fmt):
        if self.win:
            self.win.export_single_answer(self.data or {"answer": self.content}, fmt=fmt)


class ComponentCardWidget(QFrame):
    """Clean modern card for electronic components with real photograph, tags, and click-to-open detail."""
    def __init__(self, comp_dict, on_ask_cb=None, parent_win=None):
        super().__init__()
        self.setObjectName("compCard")
        self.comp = comp_dict
        self.on_ask_cb = on_ask_cb
        self.win = parent_win
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 12, 12, 12)
        lay.setSpacing(10)

        # 1. Real photo container panel
        img_panel = QFrame()
        img_panel.setObjectName("imgPanel")
        img_panel.setFixedHeight(150)
        img_lay = QVBoxLayout(img_panel)
        img_lay.setContentsMargins(6, 6, 6, 6)
        img_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)

        photo_path = comp_service.get_component_image_path(comp_dict["id"], "photo")
        img_lbl = QLabel()
        img_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_str = comp_dict.get("display_name") or comp_dict.get("name", "Component")
        img_lbl.setAccessibleName(f"Photograph of {name_str}")

        if photo_path and os.path.exists(photo_path):
            pix = QPixmap(photo_path)
            if not pix.isNull():
                scaled = pix.scaled(
                    QSize(220, 138),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                img_lbl.setPixmap(scaled)
            else:
                img_lbl.setPixmap(get_pixmap("image", "#6B8273", 36))
        else:
            img_lbl.setPixmap(get_pixmap("image", "#6B8273", 36))

        img_lay.addWidget(img_lbl)
        lay.addWidget(img_panel)

        # 2. Text info: Bold Name and Subtitle
        self.name_lbl = QLabel(f"<b>{name_str}</b>")
        self.name_lbl.setStyleSheet("font-size: 15px; font-weight: 700; color: #F3FBF5;")
        lay.addWidget(self.name_lbl)

        sub_str = comp_dict.get("subtitle") or comp_dict.get("function", "")
        self.sub_lbl = QLabel(sub_str)
        self.sub_lbl.setStyleSheet("font-size: 12.5px; color: #6B8273;")
        self.sub_lbl.setWordWrap(False)
        lay.addWidget(self.sub_lbl)

        # 3. Bottom row: Category Tag chip and Chevron arrow
        bot_row = QHBoxLayout()
        bot_row.setContentsMargins(0, 4, 0, 0)
        bot_row.setSpacing(6)

        cat_tag = QLabel(comp_dict.get("category", "Generic"))
        cat_tag.setStyleSheet("""
            background: rgba(0, 255, 133, 0.10);
            color: #00FF85;
            border: 1px solid rgba(0, 255, 133, 0.22);
            border-radius: 6px;
            padding: 2px 7px;
            font-size: 11px;
            font-weight: 600;
        """)
        bot_row.addWidget(cat_tag)
        bot_row.addStretch()

        chevron_lbl = QLabel()
        chevron_lbl.setPixmap(get_pixmap("chevron-right", "#6B8273", 16))
        bot_row.addWidget(chevron_lbl)
        lay.addLayout(bot_row)

        # Retain details_box and toggle_details for tests and programmatic inspection
        self.details_box = QWidget()
        self.details_box.setVisible(False)
        self.details_expanded = False

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.open_details()
        super().mousePressEvent(event)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Space):
            self.open_details()
        super().keyPressEvent(event)

    def toggle_details(self):
        self.details_expanded = not self.details_expanded
        self.details_box.setVisible(self.details_expanded)

    def open_details(self):
        dlg = ComponentDetailDialog(self.comp, on_ask_cb=self.on_ask_cb, parent=self.win or self)
        dlg.exec()


class ComponentDetailDialog(QDialog):
    """Full detail view for a component with real photo, pinout diagram, schematic symbol, and specs."""
    def __init__(self, comp, on_ask_cb=None, parent=None):
        super().__init__(parent)
        self.comp = comp
        self.on_ask_cb = on_ask_cb
        self.setWindowTitle(f"{comp.get('name', 'Component')} - Details")
        self.setMinimumSize(800, 620)
        self.resize(880, 700)

        root_lay = QVBoxLayout(self)
        root_lay.setContentsMargins(0, 0, 0, 0)
        root_lay.setSpacing(0)

        # Header bar
        head = QFrame()
        head.setStyleSheet("background: #0a0f0c; border-bottom: 1px solid rgba(0,255,133,0.15); padding: 16px 20px;")
        h_lay = QHBoxLayout(head)
        h_lay.setContentsMargins(0, 0, 0, 0)
        h_lay.setSpacing(12)

        title_col = QVBoxLayout()
        name_lbl = QLabel(comp.get("name", "Component"))
        name_lbl.setStyleSheet("font-size: 19px; font-weight: 800; color: #F3FBF5;")
        sub_lbl = QLabel(comp.get("subtitle", "") or comp.get("function", ""))
        sub_lbl.setStyleSheet("font-size: 13px; color: #6B8273;")
        title_col.addWidget(name_lbl)
        title_col.addWidget(sub_lbl)
        h_lay.addLayout(title_col, 1)

        cat_badge = QLabel(comp.get("category", "Generic"))
        cat_badge.setStyleSheet("background: rgba(0,255,133,0.12); color: #00FF85; border: 1px solid rgba(0,255,133,0.3); border-radius: 8px; padding: 4px 10px; font-weight: 600; font-size: 12px;")
        h_lay.addWidget(cat_badge)

        pkg_badge = QLabel(comp.get("package", "Standard"))
        pkg_badge.setStyleSheet("background: #141c16; color: #cbd5e1; border: 1px solid #233227; border-radius: 8px; padding: 4px 10px; font-size: 12px;")
        h_lay.addWidget(pkg_badge)

        close_top_btn = QPushButton()
        close_top_btn.setIcon(get_icon("x", "#cbd5e1", 16))
        close_top_btn.setFixedSize(32, 32)
        close_top_btn.clicked.connect(self.accept)
        close_top_btn.setStyleSheet("background: transparent; border: 1px solid rgba(255,255,255,0.1); border-radius: 16px;")
        h_lay.addWidget(close_top_btn)

        root_lay.addWidget(head)

        # Scrollable content area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll_content = QWidget()
        c_lay = QVBoxLayout(scroll_content)
        c_lay.setContentsMargins(24, 20, 24, 20)
        c_lay.setSpacing(18)

        # 1. Component Visual Gallery
        c_lay.addWidget(label("COMPONENT VISUAL GALLERY", "caption"))
        gallery_grid = QHBoxLayout()
        gallery_grid.setSpacing(14)

        cid = comp["id"]
        photo_p = comp_service.get_component_image_path(cid, "photo")
        pinout_p = comp_service.get_component_image_path(cid, "pinout")
        schematic_p = comp_service.get_component_image_path(cid, "schematic")

        def make_gallery_card(title, img_path, default_icon="image"):
            card = QFrame()
            card.setStyleSheet("background: #0d1410; border: 1px solid rgba(0,255,133,0.15); border-radius: 12px;")
            lay_item = QVBoxLayout(card)
            lay_item.setContentsMargins(10, 10, 10, 10)
            lay_item.setSpacing(8)

            h_bar = QHBoxLayout()
            t_lbl = QLabel(title)
            t_lbl.setStyleSheet("font-weight: 700; font-size: 12px; color: #cbd5e1;")
            h_bar.addWidget(t_lbl)
            h_bar.addStretch()

            if img_path and os.path.exists(img_path):
                zoom_btn = QPushButton("Zoom")
                zoom_btn.setIcon(get_icon("zoom-in", "#00FF85", 13))
                zoom_btn.setStyleSheet("background: rgba(0,255,133,0.10); color: #00FF85; border: 1px solid rgba(0,255,133,0.25); border-radius: 6px; padding: 2px 8px; font-size: 11px;")
                zoom_btn.clicked.connect(lambda: ImageLightboxDialog(img_path, f"{comp.get('name')} - {title}", parent=self).exec())
                h_bar.addWidget(zoom_btn)

            lay_item.addLayout(h_bar)

            preview_lbl = QLabel()
            preview_lbl.setFixedHeight(140)
            preview_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            preview_lbl.setStyleSheet("background: #070b09; border-radius: 8px;")

            if img_path and os.path.exists(img_path):
                pix = QPixmap(img_path)
                if not pix.isNull():
                    scaled = pix.scaled(QSize(220, 130), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                    preview_lbl.setPixmap(scaled)
                    preview_lbl.setCursor(Qt.CursorShape.PointingHandCursor)
                    preview_lbl.mousePressEvent = lambda e: ImageLightboxDialog(img_path, f"{comp.get('name')} - {title}", parent=self).exec()
                else:
                    preview_lbl.setPixmap(get_pixmap(default_icon, "#6B8273", 32))
            else:
                preview_lbl.setPixmap(get_pixmap(default_icon, "#6B8273", 32))

            lay_item.addWidget(preview_lbl)
            return card

        gallery_grid.addWidget(make_gallery_card("Actual Component", photo_p, "image"))
        gallery_grid.addWidget(make_gallery_card("Pinout Diagram", pinout_p, "cpu"))
        gallery_grid.addWidget(make_gallery_card("Schematic Symbol", schematic_p, "layers"))
        c_lay.addLayout(gallery_grid)

        # 2. Key Specifications
        if comp.get("key_specs"):
            c_lay.addWidget(label("KEY SPECIFICATIONS", "caption"))
            spec_box = QLabel(comp["key_specs"])
            spec_box.setWordWrap(True)
            spec_box.setStyleSheet("background: #0d1410; border: 1px solid rgba(0,255,133,0.15); border-radius: 10px; padding: 12px; color: #f3fbf5; font-size: 13px; font-weight: 500;")
            c_lay.addWidget(spec_box)

        # 3. Function & Details
        c_lay.addWidget(label("FUNCTION & DETAILS", "caption"))
        exp_box = QFrame()
        exp_box.setStyleSheet("background: #0d1410; border: 1px solid rgba(0,255,133,0.12); border-radius: 10px; padding: 12px;")
        exp_lay = QVBoxLayout(exp_box)
        exp_lay.setSpacing(8)

        if comp.get("simple_explanation"):
            sim_lbl = QLabel(f"<b>Overview:</b> {comp['simple_explanation']}")
            sim_lbl.setWordWrap(True)
            exp_lay.addWidget(sim_lbl)

        if comp.get("detailed_explanation"):
            det_lbl = QLabel(f"<b>Technical Deep Dive:</b> {comp['detailed_explanation']}")
            det_lbl.setWordWrap(True)
            exp_lay.addWidget(det_lbl)

        c_lay.addWidget(exp_box)

        # 4. Pin Connections
        if comp.get("pinout"):
            c_lay.addWidget(label("PINOUT CONNECTIONS", "caption"))
            pin_lbl = QLabel(comp["pinout"])
            pin_lbl.setStyleSheet("background: #080d0a; border: 1px solid #1a2920; border-radius: 8px; padding: 12px; font-family: monospace; font-size: 12.5px; color: #67e8f9;")
            c_lay.addWidget(pin_lbl)

        # 5. Typical Applications
        if comp.get("typical_uses"):
            c_lay.addWidget(label("TYPICAL APPLICATIONS", "caption"))
            app_box = QFrame()
            app_box.setStyleSheet("background: #0d1410; border: 1px solid rgba(0,255,133,0.12); border-radius: 10px; padding: 12px;")
            app_lay = QVBoxLayout(app_box)
            app_lay.setSpacing(6)
            for u in comp["typical_uses"]:
                u_lbl = QLabel(f"• {u}")
                u_lbl.setStyleSheet("color: #cbd5e1; font-size: 13px;")
                app_lay.addWidget(u_lbl)
            c_lay.addWidget(app_box)

        scroll.setWidget(scroll_content)
        root_lay.addWidget(scroll, 1)

        # Footer Actions
        footer = QFrame()
        footer.setStyleSheet("background: #0a0f0c; border-top: 1px solid rgba(0,255,133,0.15); padding: 12px 20px;")
        f_lay = QHBoxLayout(footer)
        f_lay.setContentsMargins(0, 0, 0, 0)

        ask_btn = QPushButton("Ask Assistant About This")
        ask_btn.setProperty("kind", "primary")
        ask_btn.setIcon(get_icon("message-square", "#ffffff", 14))
        ask_btn.clicked.connect(self._on_ask)
        f_lay.addWidget(ask_btn)
        f_lay.addStretch()

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        f_lay.addWidget(close_btn)

        root_lay.addWidget(footer)

    def _on_ask(self):
        self.accept()
        if self.on_ask_cb:
            self.on_ask_cb(self.comp)


class ResponsiveCardGrid(QWidget):
    """Dynamically lays out component cards into 4, 3, 2, or 1 column based on current width."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.grid_layout = QGridLayout(self)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        self.grid_layout.setSpacing(16)
        self.card_widgets = []
        self.current_cols = 4

    def set_cards(self, cards):
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget() and item.widget() not in cards:
                item.widget().deleteLater()
        self.card_widgets = cards
        self._relayout()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._check_columns(event.size().width())

    def _check_columns(self, width):
        if width >= 1150:
            cols = 4
        elif width >= 840:
            cols = 3
        elif width >= 560:
            cols = 2
        else:
            cols = 1

        if cols != self.current_cols:
            self.current_cols = cols
            self._relayout()

    def _relayout(self):
        while self.grid_layout.count():
            self.grid_layout.takeAt(0)

        cols = self.current_cols
        for i, card in enumerate(self.card_widgets):
            r = i // cols
            c = i % cols
            self.grid_layout.addWidget(card, r, c)


class TopNavBar(QFrame):
    """Top navigation bar for unified 4-page access and theme toggling."""
    def __init__(self, win):
        super().__init__()
        self.win = win
        self.setObjectName("card")
        self.setFixedHeight(64)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(18, 8, 18, 8)
        lay.setSpacing(8)

        # Brand / Logo
        self.brand_icon = QLabel()
        self.brand_icon.setPixmap(get_pixmap("zap", "#00FF85", 22))
        brand_lbl = label("ElectroLearn AI", "brand", wrap=False)
        lay.addWidget(self.brand_icon)
        lay.addWidget(brand_lbl)
        lay.addSpacing(24)

        # The 4 Main Navigation Buttons
        self.btn_dash = button("Dashboard", "navActive", slot=lambda: self.win.navigate_to(0))
        self.btn_dash.setIcon(get_icon("layout-grid", "#00FF85", 16))

        self.btn_chat = button("AI Assistant", "nav", slot=lambda: self.win.navigate_to(1))
        self.btn_chat.setIcon(get_icon("message-square", "#94a3b8", 16))

        self.btn_lib = button("Component Library", "nav", slot=lambda: self.win.navigate_to(2))
        self.btn_lib.setIcon(get_icon("cpu", "#94a3b8", 16))

        self.btn_manual = button("Manuals", "nav", slot=lambda: self.win.navigate_to(3))
        self.btn_manual.setIcon(get_icon("book-open", "#94a3b8", 16))

        self.nav_buttons = [self.btn_dash, self.btn_chat, self.btn_lib, self.btn_manual]
        for b in self.nav_buttons:
            lay.addWidget(b)

        lay.addStretch()

        # Help drawer button
        self.help_btn = button("Help", "secondary", slot=lambda: self.win.open_help_drawer())
        self.help_btn.setIcon(get_icon("help-circle", "#00FF85", 16))
        self.help_btn.setToolTip("App User Guide & Interactive Tour")
        lay.addWidget(self.help_btn)

        # Theme toggle & Settings
        self.theme_btn = button("Dark Mode", "secondary", slot=self.win.toggle_theme)
        self.theme_btn.setIcon(get_icon("moon", "#00FF85", 16))
        self.theme_btn.setToolTip("Toggle Dark / Light Theme")
        lay.addWidget(self.theme_btn)

        self.settings_btn = button("Settings", "secondary", slot=lambda: SettingsDialog(self.win).exec())
        self.settings_btn.setIcon(get_icon("settings", "#94a3b8", 16))
        lay.addWidget(self.settings_btn)

    def set_active_tab(self, idx):
        buttons = [
            (self.btn_dash, "layout-grid"),
            (self.btn_chat, "message-square"),
            (self.btn_lib, "cpu"),
            (self.btn_manual, "book-open")
        ]
        is_dark = getattr(self.win, "is_dark_theme", True)
        accent = "#00FF85" if is_dark else "#10B981"
        muted = "#94a3b8" if is_dark else "#64748b"
        for i, (b, icon_name) in enumerate(buttons):
            is_active = (i == idx)
            b.setProperty("kind", "navActive" if is_active else "nav")
            b.setIcon(get_icon(icon_name, accent if is_active else muted, 16))
            b.style().unpolish(b)
            b.style().polish(b)


class HelpDrawerDialog(QDialog):
    """Slide-in modal drawer explaining how to use ElectroLearn AI and take the guided tour."""
    def __init__(self, win):
        super().__init__(win)
        self.win = win
        self.setWindowTitle("ElectroLearn AI — Help & User Tour")
        self.setMinimumSize(540, 680)
        self.resize(580, 720)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        # Header
        head = QFrame()
        head.setStyleSheet("background: #0a0f0c; border-bottom: 1px solid rgba(0,255,133,0.15); padding: 16px 20px;")
        h_lay = QHBoxLayout(head)
        h_lay.setContentsMargins(0, 0, 0, 0)

        title_icon = QLabel()
        title_icon.setPixmap(get_pixmap("help-circle", "#00FF85", 22))
        h_lay.addWidget(title_icon)

        t_col = QVBoxLayout()
        t_title = QLabel("Help & User Guide")
        t_title.setStyleSheet("font-size: 18px; font-weight: 800; color: #F3FBF5;")
        t_sub = QLabel("Learn how to capture, identify, search, and troubleshoot")
        t_sub.setStyleSheet("font-size: 12.5px; color: #6B8273;")
        t_col.addWidget(t_title)
        t_col.addWidget(t_sub)
        h_lay.addLayout(t_col, 1)

        close_btn = QPushButton()
        close_btn.setIcon(get_icon("x", "#cbd5e1", 16))
        close_btn.setFixedSize(32, 32)
        close_btn.clicked.connect(self.accept)
        close_btn.setStyleSheet("background: transparent; border: 1px solid rgba(255,255,255,0.1); border-radius: 16px;")
        h_lay.addWidget(close_btn)
        lay.addWidget(head)

        # Body
        body = QWidget()
        b_lay = QVBoxLayout(body)
        b_lay.setContentsMargins(20, 16, 20, 16)
        b_lay.setSpacing(14)

        # Quick Tour Banner
        tour_card = QFrame()
        tour_card.setStyleSheet("background: #0e1a13; border: 1.5px solid #00FF85; border-radius: 12px; padding: 14px;")
        tc_lay = QHBoxLayout(tour_card)
        tc_lay.setContentsMargins(0, 0, 0, 0)

        tc_text = QVBoxLayout()
        tc_t = QLabel("New to the platform?")
        tc_t.setStyleSheet("font-weight: 700; font-size: 14px; color: #00FF85;")
        tc_d = QLabel("Take an interactive guided tour through all 4 primary application screens.")
        tc_d.setStyleSheet("font-size: 12px; color: #cbd5e1;")
        tc_d.setWordWrap(True)
        tc_text.addWidget(tc_t)
        tc_text.addWidget(tc_d)
        tc_lay.addLayout(tc_text, 1)

        self.tour_btn = QPushButton("Take the tour")
        self.tour_btn.setProperty("kind", "primary")
        self.tour_btn.setIcon(get_icon("play", "#060907", 14))
        self.tour_btn.clicked.connect(self._start_tour)
        tc_lay.addWidget(self.tour_btn)
        b_lay.addWidget(tour_card)

        # Search help topics
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search help topics...")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.addAction(get_icon("search", "#6B8273", 16), QLineEdit.ActionPosition.LeadingPosition)
        self.search_input.textChanged.connect(self._filter_topics)
        b_lay.addWidget(self.search_input)

        # Scrollable Topics
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll_content = QWidget()
        self.topics_lay = QVBoxLayout(scroll_content)
        self.topics_lay.setContentsMargins(0, 0, 0, 0)
        self.topics_lay.setSpacing(10)

        self.topic_cards = []
        guides = [
            ("1. Dashboard & Identification",
             "• Click 'Upload Image' or 'Live Cam' on the Dashboard to inspect electronic components.\n"
             "• The system detects markings, part numbers, package formats, and queries datasheets.\n"
             "• Click on matched illustrations to open the high-res zoomable Lightbox."),

            ("2. AI Assistant & Voice Dictation",
             "• Ask repair, pinout, wiring, and replacement questions.\n"
             "• Click the mic button to speak with real-time waveform visualization and automatic silence detection.\n"
             "• Answers automatically cite manuals (e.g. [Manual, p.12])—click any citation to open that exact page in the reader."),

            ("3. Component Library & Pinouts",
             "• Browse curated electronic components across 8 categories (ICs, Diodes, Sensors, etc.).\n"
             "• Click any card to inspect realistic photographs, pin connections, schematic symbols, and key specs."),

            ("4. Hardware Manuals & PDF Reader",
             "• Upload and index manufacturer service manuals and hardware datasheets with drag-and-drop.\n"
             "• Use the interactive PDF reader with page thumbnails, text search, bookmarks, dark reading mode, and extracted figure galleries.\n"
             "• Use the 'Include in AI search' toggle to customize which manuals the AI assistant searches."),

            ("5. Safety & Bench Testing Rules",
             "• Pin 1 Orientation: Pin 1 is always to the left of the U-notch or adjacent to the embossed dot.\n"
             "• Polarity: Rectifier diodes have a silver band at the cathode. Electrolytic capacitors have a negative (-) stripe and must NEVER be wired in reverse.\n"
             "• Always de-energize circuits before measuring component resistance or diode drops.")
        ]

        for title, text_desc in guides:
            card = QFrame()
            card.setObjectName("card")
            card.setStyleSheet("background: #0d1410; border: 1px solid rgba(0,255,133,0.12); border-radius: 10px; padding: 12px;")
            c_lay = QVBoxLayout(card)
            c_lay.setContentsMargins(4, 4, 4, 4)
            c_lay.setSpacing(6)

            t_lbl = QLabel(title)
            t_lbl.setStyleSheet("font-size: 14px; font-weight: 700; color: #F3FBF5;")
            d_lbl = QLabel(text_desc)
            d_lbl.setStyleSheet("font-size: 12.5px; color: #8ca394; line-height: 1.5;")
            d_lbl.setWordWrap(True)

            c_lay.addWidget(t_lbl)
            c_lay.addWidget(d_lbl)
            self.topics_lay.addWidget(card)
            self.topic_cards.append((title.lower() + " " + text_desc.lower(), card))

        self.topics_lay.addStretch()
        scroll.setWidget(scroll_content)
        b_lay.addWidget(scroll, 1)

        lay.addWidget(body, 1)

    def _filter_topics(self, q=None):
        query_text = (q if q is not None else self.search_input.text()).strip().lower()
        for text_corpus, card in self.topic_cards:
            card.setVisible(query_text in text_corpus if query_text else True)

    def _start_tour(self):
        self.accept()
        if hasattr(self.win, "start_guided_tour"):
            self.win.start_guided_tour()


class ManualDropZone(QFrame):
    """Drag-and-drop file upload target with multi-PDF batch indexing and progress bar."""
    def __init__(self, on_files_dropped=None, on_browse_clicked=None, parent=None):
        super().__init__(parent)
        self.setObjectName("dropZone")
        self.setAcceptDrops(True)
        self.on_files_dropped = on_files_dropped
        self.on_browse_clicked = on_browse_clicked
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 20, 24, 20)
        lay.setSpacing(10)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)

        icon_lbl = QLabel()
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_lbl.setPixmap(get_pixmap("upload", "#00FF85", 34))
        lay.addWidget(icon_lbl)

        title_lbl = QLabel("Drag & drop PDF hardware manuals here, or click to browse")
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_lbl.setStyleSheet("font-size: 15px; font-weight: 700; color: #F3FBF5;")
        lay.addWidget(title_lbl)

        sub_lbl = QLabel("Supports multiple PDF files simultaneously. Automatic text extraction, page snapshots, and FAISS indexing.")
        sub_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub_lbl.setStyleSheet("font-size: 12px; color: #6B8273;")
        lay.addWidget(sub_lbl)

        # Progress widgets (hidden until upload runs)
        self.progress_box = QWidget()
        p_lay = QVBoxLayout(self.progress_box)
        p_lay.setContentsMargins(0, 4, 0, 0)
        p_lay.setSpacing(6)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.setTextVisible(False)
        p_lay.addWidget(self.progress_bar)

        self.status_lbl = QLabel("Uploading and indexing...")
        self.status_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_lbl.setStyleSheet("font-size: 11.5px; color: #00FF85; font-weight: 600;")
        p_lay.addWidget(self.status_lbl)

        self.progress_box.setVisible(False)
        lay.addWidget(self.progress_box)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.on_browse_clicked:
            self.on_browse_clicked()
        super().mousePressEvent(event)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if any(u.toLocalFile().lower().endswith('.pdf') for u in urls):
                event.acceptProposedAction()
                return
        event.ignore()

    def dropEvent(self, event):
        files = []
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if path.lower().endswith('.pdf') and os.path.isfile(path):
                files.append(path)
        if files and self.on_files_dropped:
            self.on_files_dropped(files)
        event.acceptProposedAction()

    def show_progress(self, current, total, msg=""):
        self.progress_box.setVisible(True)
        pct = int((current / max(1, total)) * 100)
        self.progress_bar.setValue(pct)
        self.status_lbl.setText(msg or f"Processing file {current} of {total} ({pct}%)...")

    def hide_progress(self):
        self.progress_box.setVisible(False)


class ManualItemWidget(QFrame):
    """Modern manual entry card supporting Grid and List view, AI toggle, and instant actions."""
    def __init__(self, manual, view_mode="grid", on_view_cb=None, on_ask_cb=None, on_toggle_cb=None, on_delete_cb=None, on_rename_cb=None, on_download_cb=None, parent=None):
        super().__init__(parent)
        self.manual = manual
        self.mid = manual["id"]
        self.view_mode = view_mode
        self.on_view_cb = on_view_cb
        self.on_ask_cb = on_ask_cb
        self.on_toggle_cb = on_toggle_cb
        self.on_delete_cb = on_delete_cb
        self.on_rename_cb = on_rename_cb
        self.on_download_cb = on_download_cb

        self.setObjectName("manualCard" if view_mode == "grid" else "manualRow")
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        if view_mode == "grid":
            self._build_grid_layout()
        else:
            self._build_list_layout()

    def _build_grid_layout(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 14, 14, 14)
        lay.setSpacing(10)

        # Top row: Checkbox, status badge, and AI Search Toggle
        top_row = QHBoxLayout()
        top_row.setSpacing(8)

        self.select_check = QCheckBox()
        self.select_check.setToolTip("Select for bulk action")
        top_row.addWidget(self.select_check)

        # Status badge
        status_lbl = QLabel("Indexed")
        status_lbl.setStyleSheet("background: rgba(0,255,133,0.12); color: #00FF85; border: 1px solid rgba(0,255,133,0.25); border-radius: 6px; padding: 2px 7px; font-size: 11px; font-weight: 600;")
        top_row.addWidget(status_lbl)
        top_row.addStretch()

        # AI Chat Search Toggle
        self.chat_toggle = QCheckBox("AI Search")
        self.chat_toggle.setObjectName("toggleChat")
        self.chat_toggle.setChecked(bool(self.manual.get("enabled_for_chat", 1)))
        self.chat_toggle.setToolTip("Include this manual in AI Assistant search queries")
        self.chat_toggle.toggled.connect(lambda val: self.on_toggle_cb(self.mid, val) if self.on_toggle_cb else None)
        top_row.addWidget(self.chat_toggle)
        lay.addLayout(top_row)

        # Preview Thumbnail / Icon Box
        preview_box = QFrame()
        preview_box.setFixedHeight(120)
        preview_box.setStyleSheet("background: #070b09; border-radius: 8px;")
        pb_lay = QVBoxLayout(preview_box)
        pb_lay.setContentsMargins(4, 4, 4, 4)
        pb_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)

        thumb_lbl = QLabel()
        thumb_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        page_img = self.manual.get("page_image")
        if page_img and os.path.isfile(page_img):
            pix = QPixmap(page_img)
            if not pix.isNull():
                thumb_lbl.setPixmap(pix.scaled(QSize(180, 110), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            else:
                thumb_lbl.setPixmap(get_pixmap("book-open", "#00FF85", 36))
        else:
            thumb_lbl.setPixmap(get_pixmap("book-open", "#00FF85", 36))
        pb_lay.addWidget(thumb_lbl)
        preview_box.mousePressEvent = lambda e: self.on_view_cb(self.mid) if self.on_view_cb else None
        lay.addWidget(preview_box)

        # Title & Subtitle
        name_str = self.manual.get("name") or "Hardware Manual"
        title_lbl = QLabel(f"<b>{name_str}</b>")
        title_lbl.setStyleSheet("font-size: 14.5px; font-weight: 700; color: #F3FBF5;")
        title_lbl.setWordWrap(True)
        lay.addWidget(title_lbl)

        sub_parts = []
        if self.manual.get("manufacturer"):
            sub_parts.append(self.manual["manufacturer"])
        if self.manual.get("model"):
            sub_parts.append(self.manual["model"])
        if sub_parts:
            sub_lbl = QLabel(" • ".join(sub_parts))
            sub_lbl.setStyleSheet("font-size: 12px; color: #6B8273;")
            lay.addWidget(sub_lbl)

        # Metadata badges row: Pages, Size, Date
        meta_row = QHBoxLayout()
        meta_row.setSpacing(6)

        p_count = self.manual.get("page_count", 0)
        meta_row.addWidget(QLabel(f'<span style="background:rgba(255,255,255,0.05); color:#cbd5e1; padding:2px 6px; border-radius:4px; font-size:11px;">{p_count} pgs</span>'))

        sz_bytes = self.manual.get("file_size", 0)
        sz_mb = f"{sz_bytes / (1024*1024):.1f} MB" if sz_bytes else "—"
        meta_row.addWidget(QLabel(f'<span style="background:rgba(255,255,255,0.05); color:#cbd5e1; padding:2px 6px; border-radius:4px; font-size:11px;">{sz_mb}</span>'))

        meta_row.addStretch()
        lay.addLayout(meta_row)

        # Tags row if any
        tags = self.manual.get("tags")
        if tags:
            tag_row = QHBoxLayout()
            tag_row.setSpacing(4)
            for t in tags.split(",")[:3]:
                if t.strip():
                    t_badge = QLabel(t.strip())
                    t_badge.setStyleSheet("background: rgba(0,255,133,0.08); color: #00FF85; border: 1px solid rgba(0,255,133,0.18); border-radius: 4px; padding: 1px 5px; font-size: 10px;")
                    tag_row.addWidget(t_badge)
            tag_row.addStretch()
            lay.addLayout(tag_row)

        # Action Buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(6)

        view_b = QPushButton("View")
        view_b.setIcon(get_icon("book-open", "#060907", 13))
        view_b.setProperty("kind", "primary")
        view_b.clicked.connect(lambda: self.on_view_cb(self.mid) if self.on_view_cb else None)
        btn_row.addWidget(view_b, 1)

        ask_b = QPushButton("Ask")
        ask_b.setIcon(get_icon("message-square", "#cbd5e1", 13))
        ask_b.setProperty("kind", "secondary")
        ask_b.clicked.connect(lambda: self.on_ask_cb(self.mid) if self.on_ask_cb else None)
        btn_row.addWidget(ask_b)

        # More menu (Rename, Download, Delete)
        more_b = QPushButton()
        more_b.setIcon(get_icon("settings", "#6B8273", 14))
        more_b.setFixedSize(34, 34)
        more_b.setProperty("kind", "secondary")
        menu = QMenu(more_b)
        act_ren = menu.addAction("Rename Manual")
        act_ren.triggered.connect(lambda: self.on_rename_cb(self.manual) if self.on_rename_cb else None)
        act_down = menu.addAction("Download PDF Copy")
        act_down.triggered.connect(lambda: self.on_download_cb(self.manual) if self.on_download_cb else None)
        menu.addSeparator()
        act_del = menu.addAction("Delete Manual")
        act_del.triggered.connect(lambda: self.on_delete_cb(self.mid) if self.on_delete_cb else None)
        more_b.setMenu(menu)
        btn_row.addWidget(more_b)

        lay.addLayout(btn_row)

    def _build_list_layout(self):
        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 10, 14, 10)
        lay.setSpacing(14)

        self.select_check = QCheckBox()
        lay.addWidget(self.select_check)

        icon_lbl = QLabel()
        icon_lbl.setPixmap(get_pixmap("book-open", "#00FF85", 22))
        lay.addWidget(icon_lbl)

        # Name and maker
        text_col = QVBoxLayout()
        text_col.setSpacing(2)
        name_str = self.manual.get("name") or "Hardware Manual"
        t_lbl = QLabel(f"<b>{name_str}</b>")
        t_lbl.setStyleSheet("font-size: 14px; color: #F3FBF5;")
        text_col.addWidget(t_lbl)

        sub_parts = []
        if self.manual.get("manufacturer"):
            sub_parts.append(self.manual["manufacturer"])
        if self.manual.get("model"):
            sub_parts.append(self.manual["model"])
        p_count = self.manual.get("page_count", 0)
        sz_bytes = self.manual.get("file_size", 0)
        sz_mb = f"{sz_bytes / (1024*1024):.1f} MB" if sz_bytes else "—"
        sub_parts.append(f"{p_count} pages")
        sub_parts.append(sz_mb)

        s_lbl = QLabel(" • ".join(sub_parts))
        s_lbl.setStyleSheet("font-size: 12px; color: #6B8273;")
        text_col.addWidget(s_lbl)
        lay.addLayout(text_col, 2)

        # AI Search Toggle
        self.chat_toggle = QCheckBox("AI Search")
        self.chat_toggle.setObjectName("toggleChat")
        self.chat_toggle.setChecked(bool(self.manual.get("enabled_for_chat", 1)))
        self.chat_toggle.toggled.connect(lambda val: self.on_toggle_cb(self.mid, val) if self.on_toggle_cb else None)
        lay.addWidget(self.chat_toggle)

        # Actions
        view_b = QPushButton("View")
        view_b.setIcon(get_icon("book-open", "#060907", 13))
        view_b.setProperty("kind", "primary")
        view_b.clicked.connect(lambda: self.on_view_cb(self.mid) if self.on_view_cb else None)
        lay.addWidget(view_b)

        ask_b = QPushButton("Ask")
        ask_b.setIcon(get_icon("message-square", "#cbd5e1", 13))
        ask_b.setProperty("kind", "secondary")
        ask_b.clicked.connect(lambda: self.on_ask_cb(self.mid) if self.on_ask_cb else None)
        lay.addWidget(ask_b)

        more_b = QPushButton()
        more_b.setIcon(get_icon("settings", "#6B8273", 14))
        more_b.setFixedSize(34, 34)
        more_b.setProperty("kind", "secondary")
        menu = QMenu(more_b)
        act_ren = menu.addAction("Rename Manual")
        act_ren.triggered.connect(lambda: self.on_rename_cb(self.manual) if self.on_rename_cb else None)
        act_down = menu.addAction("Download PDF Copy")
        act_down.triggered.connect(lambda: self.on_download_cb(self.manual) if self.on_download_cb else None)
        menu.addSeparator()
        act_del = menu.addAction("Delete Manual")
        act_del.triggered.connect(lambda: self.on_delete_cb(self.mid) if self.on_delete_cb else None)
        more_b.setMenu(menu)
        lay.addWidget(more_b)

class InteractiveManualViewer(QWidget):
    """Full-featured interactive PDF manual reader with PyMuPDF rendering, dark mode, thumbnails, search, and notes."""
    def __init__(self, win, on_back_cb=None, parent=None):
        super().__init__(parent)
        self.win = win
        self.on_back_cb = on_back_cb

        # State
        self.manual_id = None
        self.manual_info = None
        self.doc = None
        self.total_pages = 0
        self.current_page = 1
        self.zoom = 1.25
        self.rotation = 0
        self.dark_mode = False
        self.search_matches = []
        self.current_match_idx = -1
        self.search_query = ""
        self.thumbnail_buttons = {}

        self._build_ui()

    def _build_ui(self):
        root_lay = QVBoxLayout(self)
        root_lay.setContentsMargins(0, 0, 0, 0)
        root_lay.setSpacing(0)

        # 1. Top Control Bar
        ctrl_bar = QFrame()
        ctrl_bar.setStyleSheet("background: #0a0f0c; border-bottom: 1px solid rgba(0,255,133,0.15); padding: 8px 16px;")
        cb_lay = QHBoxLayout(ctrl_bar)
        cb_lay.setContentsMargins(0, 0, 0, 0)
        cb_lay.setSpacing(8)

        # Back button
        self.back_btn = QPushButton("All Manuals")
        self.back_btn.setIcon(get_icon("chevron-left", "#00FF85", 14))
        self.back_btn.setProperty("kind", "secondary")
        self.back_btn.clicked.connect(self._go_back)
        cb_lay.addWidget(self.back_btn)

        # Manual Title Label
        self.title_lbl = QLabel("Manual Viewer")
        self.title_lbl.setStyleSheet("font-size: 14px; font-weight: 700; color: #F3FBF5; margin-left: 6px;")
        cb_lay.addWidget(self.title_lbl)
        cb_lay.addStretch()

        # Page Navigation
        self.prev_btn = QPushButton()
        self.prev_btn.setIcon(get_icon("chevron-left", "#cbd5e1", 14))
        self.prev_btn.setFixedSize(32, 32)
        self.prev_btn.setToolTip("Previous Page (Left Arrow)")
        self.prev_btn.clicked.connect(self.prev_page)
        cb_lay.addWidget(self.prev_btn)

        self.next_btn = QPushButton()
        self.next_btn.setIcon(get_icon("chevron-right", "#cbd5e1", 14))
        self.next_btn.setFixedSize(32, 32)
        self.next_btn.setToolTip("Next Page (Right Arrow)")
        self.next_btn.clicked.connect(self.next_page)
        cb_lay.addWidget(self.next_btn)

        cb_lay.addWidget(QLabel('<span style="color:#6B8273; font-size:12px;">Page</span>'))
        self.page_spin = QSpinBox()
        self.page_spin.setRange(1, 1)
        self.page_spin.setValue(1)
        self.page_spin.setFixedWidth(64)
        self.page_spin.valueChanged.connect(self.jump_to_page)
        cb_lay.addWidget(self.page_spin)

        self.total_lbl = QLabel("of 0")
        self.total_lbl.setStyleSheet("color:#6B8273; font-size:12px;")
        cb_lay.addWidget(self.total_lbl)

        cb_lay.addSpacing(8)

        # Zoom Controls
        self.zoom_out_btn = QPushButton()
        self.zoom_out_btn.setIcon(get_icon("zoom-out", "#cbd5e1", 14))
        self.zoom_out_btn.setFixedSize(32, 32)
        self.zoom_out_btn.setToolTip("Zoom Out")
        self.zoom_out_btn.clicked.connect(self.zoom_out)
        cb_lay.addWidget(self.zoom_out_btn)

        self.zoom_lbl = QLabel("125%")
        self.zoom_lbl.setStyleSheet("color:#cbd5e1; font-size:12px; font-weight:600;")
        cb_lay.addWidget(self.zoom_lbl)

        self.zoom_in_btn = QPushButton()
        self.zoom_in_btn.setIcon(get_icon("zoom-in", "#cbd5e1", 14))
        self.zoom_in_btn.setFixedSize(32, 32)
        self.zoom_in_btn.setToolTip("Zoom In")
        self.zoom_in_btn.clicked.connect(self.zoom_in)
        cb_lay.addWidget(self.zoom_in_btn)

        self.fit_width_btn = QPushButton("Fit Width")
        self.fit_width_btn.setProperty("kind", "secondary")
        self.fit_width_btn.clicked.connect(self.fit_width)
        cb_lay.addWidget(self.fit_width_btn)

        cb_lay.addSpacing(8)

        # Page Tools: Dark Reading Mode, Rotate, Fullscreen, Bookmark
        self.dark_mode_btn = QPushButton()
        self.dark_mode_btn.setIcon(get_icon("moon", "#00FF85", 14))
        self.dark_mode_btn.setFixedSize(32, 32)
        self.dark_mode_btn.setToolTip("Toggle Dark Reading Mode")
        self.dark_mode_btn.clicked.connect(self.toggle_dark_reading_mode)
        cb_lay.addWidget(self.dark_mode_btn)

        self.rotate_btn = QPushButton()
        self.rotate_btn.setIcon(get_icon("rotate-cw", "#cbd5e1", 14))
        self.rotate_btn.setFixedSize(32, 32)
        self.rotate_btn.setToolTip("Rotate Page 90°")
        self.rotate_btn.clicked.connect(self.rotate_clockwise)
        cb_lay.addWidget(self.rotate_btn)

        self.bookmark_btn = QPushButton()
        self.bookmark_btn.setIcon(get_icon("bookmark", "#cbd5e1", 14))
        self.bookmark_btn.setFixedSize(32, 32)
        self.bookmark_btn.setToolTip("Bookmark Current Page")
        self.bookmark_btn.clicked.connect(self.add_bookmark_prompt)
        cb_lay.addWidget(self.bookmark_btn)

        self.ext_btn = QPushButton()
        self.ext_btn.setIcon(get_icon("external-link", "#cbd5e1", 14))
        self.ext_btn.setFixedSize(32, 32)
        self.ext_btn.setToolTip("Open in External PDF Viewer")
        self.ext_btn.clicked.connect(self.open_external)
        cb_lay.addWidget(self.ext_btn)

        cb_lay.addSpacing(12)

        # AI Assistant Actions
        self.ask_manual_btn = QPushButton("Ask About Manual")
        self.ask_manual_btn.setIcon(get_icon("message-square", "#cbd5e1", 13))
        self.ask_manual_btn.setProperty("kind", "secondary")
        self.ask_manual_btn.clicked.connect(self.ask_about_this_manual)
        cb_lay.addWidget(self.ask_manual_btn)

        self.ask_page_btn = QPushButton("Ask About Page")
        self.ask_page_btn.setIcon(get_icon("message-square", "#ffffff", 13))
        self.ask_page_btn.setProperty("kind", "primary")
        self.ask_page_btn.clicked.connect(self.ask_about_this_page)
        cb_lay.addWidget(self.ask_page_btn)

        root_lay.addWidget(ctrl_bar)

        # 2. Main Horizontal Splitter: Left Sidebar Tabs | Document Canvas
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setHandleWidth(4)

        # Left Sidebar Tabs
        self.tabs = QTabWidget()
        self.tabs.setFixedWidth(310)

        # Tab 1: Thumbnails
        thumb_widget = QWidget()
        t_lay = QVBoxLayout(thumb_widget)
        t_lay.setContentsMargins(6, 6, 6, 6)
        self.thumb_scroll = QScrollArea()
        self.thumb_scroll.setWidgetResizable(True)
        self.thumb_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.thumb_container = QWidget()
        self.thumb_lay = QVBoxLayout(self.thumb_container)
        self.thumb_lay.setContentsMargins(4, 4, 4, 4)
        self.thumb_lay.setSpacing(8)
        self.thumb_lay.addStretch()
        self.thumb_scroll.setWidget(self.thumb_container)
        t_lay.addWidget(self.thumb_scroll)
        self.tabs.addTab(thumb_widget, "Pages")

        # Tab 2: Outline
        toc_widget = QWidget()
        toc_lay = QVBoxLayout(toc_widget)
        toc_lay.setContentsMargins(4, 4, 4, 4)
        self.toc_tree = QTreeWidget()
        self.toc_tree.setHeaderLabel("Table of Contents")
        self.toc_tree.itemClicked.connect(self._on_toc_clicked)
        toc_lay.addWidget(self.toc_tree)
        self.tabs.addTab(toc_widget, "Outline")

        # Tab 3: Search
        search_widget = QWidget()
        s_lay = QVBoxLayout(search_widget)
        s_lay.setContentsMargins(6, 6, 6, 6)
        s_lay.setSpacing(8)

        s_bar = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search inside PDF...")
        self.search_input.returnPressed.connect(self._do_search)
        s_bar.addWidget(self.search_input)

        s_btn = QPushButton()
        s_btn.setIcon(get_icon("search", "#00FF85", 14))
        s_btn.setFixedSize(32, 32)
        s_btn.clicked.connect(self._do_search)
        s_bar.addWidget(s_btn)
        s_lay.addLayout(s_bar)

        # Match navigation bar
        match_bar = QHBoxLayout()
        self.match_lbl = QLabel("0 matches")
        self.match_lbl.setStyleSheet("font-size: 11.5px; color: #6B8273;")
        match_bar.addWidget(self.match_lbl)
        match_bar.addStretch()

        self.prev_match_btn = QPushButton("Prev")
        self.prev_match_btn.setFixedHeight(26)
        self.prev_match_btn.clicked.connect(self._prev_match)
        match_bar.addWidget(self.prev_match_btn)

        self.next_match_btn = QPushButton("Next")
        self.next_match_btn.setFixedHeight(26)
        self.next_match_btn.clicked.connect(self._next_match)
        match_bar.addWidget(self.next_match_btn)
        s_lay.addLayout(match_bar)

        self.search_list = QListWidget()
        self.search_list.itemClicked.connect(self._on_search_item_clicked)
        s_lay.addWidget(self.search_list, 1)
        self.tabs.addTab(search_widget, "Search")

        # Tab 4: Figures Gallery
        fig_widget = QWidget()
        f_lay = QVBoxLayout(fig_widget)
        f_lay.setContentsMargins(4, 4, 4, 4)
        self.fig_scroll = QScrollArea()
        self.fig_scroll.setWidgetResizable(True)
        self.fig_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.fig_container = QWidget()
        self.fig_lay = QVBoxLayout(self.fig_container)
        self.fig_lay.setContentsMargins(4, 4, 4, 4)
        self.fig_lay.setSpacing(10)
        self.fig_lay.addStretch()
        self.fig_scroll.setWidget(self.fig_container)
        f_lay.addWidget(self.fig_scroll)
        self.tabs.addTab(fig_widget, "Figures")

        # Tab 5: Bookmarks & Notes
        bm_widget = QWidget()
        bm_lay = QVBoxLayout(bm_widget)
        bm_lay.setContentsMargins(6, 6, 6, 6)
        bm_lay.setSpacing(8)

        add_bm_b = QPushButton("Add Note On This Page")
        add_bm_b.setIcon(get_icon("bookmark", "#00FF85", 13))
        add_bm_b.setProperty("kind", "secondary")
        add_bm_b.clicked.connect(self.add_bookmark_prompt)
        bm_lay.addWidget(add_bm_b)

        self.bm_list = QListWidget()
        self.bm_list.itemClicked.connect(self._on_bookmark_clicked)
        bm_lay.addWidget(self.bm_list, 1)
        self.tabs.addTab(bm_widget, "Notes")

        # Tab 6: Details & Components
        det_widget = QWidget()
        d_lay = QVBoxLayout(det_widget)
        d_lay.setContentsMargins(10, 10, 10, 10)
        d_lay.setSpacing(10)

        self.det_summary_lbl = QLabel()
        self.det_summary_lbl.setWordWrap(True)
        self.det_summary_lbl.setStyleSheet("font-size: 12px; color: #cbd5e1; line-height: 1.4;")
        d_lay.addWidget(self.det_summary_lbl)

        d_lay.addWidget(QLabel("<b>MENTIONED COMPONENTS:</b>"))
        self.comp_chips_box = QWidget()
        self.comp_chips_lay = QVBoxLayout(self.comp_chips_box)
        self.comp_chips_lay.setContentsMargins(0, 0, 0, 0)
        self.comp_chips_lay.setSpacing(6)
        d_lay.addWidget(self.comp_chips_box)
        d_lay.addStretch()
        self.tabs.addTab(det_widget, "Details")

        self.splitter.addWidget(self.tabs)

        # Right Document Canvas
        self.doc_scroll = QScrollArea()
        self.doc_scroll.setWidgetResizable(False)
        self.doc_scroll.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.doc_scroll.setStyleSheet("background: #080d0a;")

        self.canvas_lbl = QLabel("No manual loaded")
        self.canvas_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.canvas_lbl.setStyleSheet("background: #ffffff; border-radius: 4px;")
        self.doc_scroll.setWidget(self.canvas_lbl)

        self.splitter.addWidget(self.doc_scroll)
        self.splitter.setStretchFactor(1, 4)

        root_lay.addWidget(self.splitter, 1)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Left, Qt.Key.Key_PageUp):
            self.prev_page()
            event.accept()
        elif event.key() in (Qt.Key.Key_Right, Qt.Key.Key_PageDown):
            self.next_page()
            event.accept()
        else:
            super().keyPressEvent(event)

    def load_manual(self, manual_id, page=1, highlight_query=""):
        self.manual_id = manual_id
        self.manual_info = db.get_manual(manual_id)
        if not self.manual_info:
            return

        db.update_manual_last_viewed(manual_id)
        path = self.manual_info.get("file_path", "")
        if not path or not os.path.isfile(path):
            self.canvas_lbl.setText(f"<p style='color:#f87171; font-size:15px; font-weight:700;'>PDF File Not Found</p><p style='color:#94a3b8; font-size:12.5px;'>Could not locate PDF file on disk at:<br><b>{path}</b></p>")
            self.canvas_lbl.setFixedSize(560, 200)
            return

        try:
            if self.doc:
                self.doc.close()
            self.doc = fitz.open(path)
            self.total_pages = self.doc.page_count
        except Exception as e:
            self.canvas_lbl.setText(f"<p style='color:#f87171; font-size:15px; font-weight:700;'>PDF Read Error</p><p style='color:#94a3b8; font-size:12.5px;'>Failed to open PDF document:<br>{e}</p>")
            self.canvas_lbl.setFixedSize(560, 200)
            return

        self.title_lbl.setText(self.manual_info.get("name", "Manual"))
        self.page_spin.blockSignals(True)
        self.page_spin.setRange(1, self.total_pages)
        self.page_spin.setValue(max(1, min(page, self.total_pages)))
        self.page_spin.blockSignals(False)
        self.total_lbl.setText(f"of {self.total_pages}")
        self.current_page = max(1, min(page, self.total_pages))

        # Populate sidebar tabs
        self._populate_outline()
        self._populate_thumbnails()
        self._populate_figures()
        self._populate_bookmarks()
        self._populate_details()

        # Render page
        self.search_query = highlight_query or ""
        self.render_page()

    def render_page(self):
        if not self.doc or self.current_page < 1 or self.current_page > self.total_pages:
            return

        page_obj = self.doc[self.current_page - 1]
        mat = fitz.Matrix(self.zoom, self.zoom).prerotate(self.rotation)
        pix = page_obj.get_pixmap(matrix=mat, alpha=False)

        qimg = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format.Format_RGB888)

        # Dark Reading Mode: Invert pixels for comfortable viewing
        if self.dark_mode:
            qimg.invertPixels(QImage.InvertMode.InvertRgb)

        # Highlight search query matches
        if self.search_query.strip():
            matches = page_obj.search_for(self.search_query.strip())
            if matches:
                painter = QPainter(qimg)
                color = QColor(0, 255, 133, 110) if self.dark_mode else QColor(16, 185, 129, 90)
                painter.setBrush(color)
                painter.setPen(Qt.PenStyle.NoPen)
                for r in matches:
                    rx = int(r.x0 * self.zoom)
                    ry = int(r.y0 * self.zoom)
                    rw = int((r.x1 - r.x0) * self.zoom)
                    rh = int((r.y1 - r.y0) * self.zoom)
                    painter.drawRect(rx, ry, rw, rh)
                painter.end()

        pm = QPixmap.fromImage(qimg)
        self.canvas_lbl.setPixmap(pm)
        self.canvas_lbl.setFixedSize(pm.size())
        self.zoom_lbl.setText(f"{int(self.zoom * 100)}%")

        # Update active thumbnail border
        for pno, btn in self.thumbnail_buttons.items():
            is_cur = (pno == self.current_page)
            btn.setStyleSheet(
                "border: 2px solid #00FF85; border-radius: 6px; background: #142018;"
                if is_cur else
                "border: 1px solid rgba(255,255,255,0.1); border-radius: 6px; background: #070b09;"
            )

    def prev_page(self):
        if self.current_page > 1:
            self.jump_to_page(self.current_page - 1)

    def next_page(self):
        if self.current_page < self.total_pages:
            self.jump_to_page(self.current_page + 1)

    def jump_to_page(self, pno):
        pno = max(1, min(pno, self.total_pages))
        self.current_page = pno
        self.page_spin.blockSignals(True)
        self.page_spin.setValue(pno)
        self.page_spin.blockSignals(False)
        self.render_page()

    def zoom_in(self):
        self.zoom = min(4.0, self.zoom + 0.25)
        self.render_page()

    def zoom_out(self):
        self.zoom = max(0.5, self.zoom - 0.25)
        self.render_page()

    def fit_width(self):
        if not self.doc:
            return
        w = self.doc_scroll.viewport().width() - 30
        page_w = self.doc[self.current_page - 1].rect.width
        self.zoom = max(0.5, min(3.5, w / page_w))
        self.render_page()

    def toggle_dark_reading_mode(self):
        self.dark_mode = not self.dark_mode
        self.dark_mode_btn.setIcon(get_icon("sun" if self.dark_mode else "moon", "#00FF85", 14))
        self.dark_mode_btn.setToolTip("Switch to Standard View" if self.dark_mode else "Toggle Dark Reading Mode")
        self.render_page()

    def rotate_clockwise(self):
        self.rotation = (self.rotation + 90) % 360
        self.render_page()

    def open_external(self):
        if self.manual_info and self.manual_info.get("file_path"):
            path = self.manual_info["file_path"]
            if os.path.isfile(path):
                try:
                    os.startfile(path)
                except Exception as e:
                    QMessageBox.warning(self, "External Viewer", f"Could not launch viewer:\n{e}")

    def add_bookmark_prompt(self):
        if not self.manual_id:
            return
        note, ok = QInputDialog.getText(self, "Add Bookmark", f"Add note for Page {self.current_page}:")
        if ok:
            db.add_manual_bookmark(self.manual_id, self.current_page, note)
            self._populate_bookmarks()

    def ask_about_this_manual(self):
        if not self.manual_info:
            return
        name = self.manual_info.get("name", "Manual")
        prompt = f"Can you summarize the key specifications, precautions, and operating instructions for the {name} manual?"
        self.win.navigate_to(1)
        if hasattr(self.win.view, "chat_input"):
            self.win.view.chat_input.setPlainText(prompt)
            self.win.view.chat_input.setFocus()

    def ask_about_this_page(self):
        if not self.manual_info or not self.doc:
            return
        page_txt = self.doc[self.current_page - 1].get_text("text").strip()
        name = self.manual_info.get("name", "Manual")
        excerpt = page_txt[:400].replace("\n", " ")
        prompt = f'In [{name}, p.{self.current_page}], can you explain the procedure or diagram shown here: "{excerpt}"?'
        self.win.navigate_to(1)
        if hasattr(self.win.view, "chat_input"):
            self.win.view.chat_input.setPlainText(prompt)
            self.win.view.chat_input.setFocus()

    def _go_back(self):
        if self.on_back_cb:
            self.on_back_cb()

    def _populate_thumbnails(self):
        # Clear existing
        while self.thumb_lay.count() > 1:
            item = self.thumb_lay.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.thumbnail_buttons.clear()

        # Generate lazy thumbnails up to 50 pages or all
        limit = min(self.total_pages, 60)
        for i in range(limit):
            pno = i + 1
            btn = QPushButton()
            btn.setFixedHeight(95)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            p_obj = self.doc[i]
            pix = p_obj.get_pixmap(matrix=fitz.Matrix(0.2, 0.2), alpha=False)
            qimg = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format.Format_RGB888)
            btn.setIcon(QIcon(QPixmap.fromImage(qimg)))
            btn.setIconSize(QSize(70, 85))
            btn.setToolTip(f"Page {pno}")
            btn.clicked.connect(lambda _=False, p=pno: self.jump_to_page(p))
            self.thumb_lay.insertWidget(self.thumb_lay.count() - 1, btn)
            self.thumbnail_buttons[pno] = btn

    def _populate_outline(self):
        self.toc_tree.clear()
        if not self.doc:
            return
        toc = self.doc.get_toc()
        if not toc:
            item = QTreeWidgetItem(self.toc_tree, ["(No bookmarks in this document)"])
            return

        node_stack = [(0, self.toc_tree.invisibleRootItem())]
        for lvl, title, page in toc:
            while node_stack and node_stack[-1][0] >= lvl:
                node_stack.pop()
            parent_item = node_stack[-1][1] if node_stack else self.toc_tree.invisibleRootItem()
            item = QTreeWidgetItem(parent_item, [f"{title} (p.{page})"])
            item.setData(0, Qt.ItemDataRole.UserRole, page)
            node_stack.append((lvl, item))
        self.toc_tree.expandAll()

    def _on_toc_clicked(self, item):
        pno = item.data(0, Qt.ItemDataRole.UserRole)
        if pno:
            self.jump_to_page(int(pno))

    def _do_search(self):
        query_text = self.search_input.text().strip()
        if not query_text or not self.doc:
            return
        self.search_query = query_text
        self.search_matches.clear()
        self.search_list.clear()

        for idx, page in enumerate(self.doc):
            pno = idx + 1
            rects = page.search_for(query_text)
            if rects:
                t = page.get_text("text").strip().replace("\n", " ")
                snippet = t[:80] + "..." if len(t) > 80 else t
                item = QListWidgetItem(f"Page {pno}: {snippet}")
                item.setData(Qt.ItemDataRole.UserRole, pno)
                self.search_list.addItem(item)
                for r in rects:
                    self.search_matches.append((pno, r))

        cnt = len(self.search_matches)
        self.match_lbl.setText(f"{cnt} match{'es' if cnt != 1 else ''}")
        self.current_match_idx = 0 if cnt > 0 else -1
        if cnt > 0:
            self.jump_to_page(self.search_matches[0][0])
        else:
            self.render_page()

    def _next_match(self):
        if not self.search_matches:
            return
        self.current_match_idx = (self.current_match_idx + 1) % len(self.search_matches)
        pno, _ = self.search_matches[self.current_match_idx]
        self.match_lbl.setText(f"Match {self.current_match_idx + 1} of {len(self.search_matches)}")
        self.jump_to_page(pno)

    def _prev_match(self):
        if not self.search_matches:
            return
        self.current_match_idx = (self.current_match_idx - 1) % len(self.search_matches)
        pno, _ = self.search_matches[self.current_match_idx]
        self.match_lbl.setText(f"Match {self.current_match_idx + 1} of {len(self.search_matches)}")
        self.jump_to_page(pno)

    def _on_search_item_clicked(self, item):
        pno = item.data(Qt.ItemDataRole.UserRole)
        if pno:
            self.jump_to_page(int(pno))

    def _populate_figures(self):
        while self.fig_lay.count() > 1:
            w = self.fig_lay.takeAt(0)
            if w.widget():
                w.widget().deleteLater()

        if not self.manual_id:
            return
        rows = db.query("SELECT page_number, image_path FROM manual_images WHERE manual_id=? ORDER BY page_number ASC", (self.manual_id,))
        for r in rows:
            pno = r["page_number"]
            ipath = r["image_path"]
            if not os.path.isfile(ipath):
                continue
            card = QFrame()
            card.setStyleSheet("background: #0d1410; border: 1px solid rgba(0,255,133,0.15); border-radius: 8px; padding: 6px;")
            c_l = QVBoxLayout(card)
            c_l.setContentsMargins(4, 4, 4, 4)

            h_bar = QHBoxLayout()
            h_bar.addWidget(QLabel(f'<span style="background:rgba(0,255,133,0.12); color:#00FF85; padding:2px 6px; border-radius:4px; font-size:11px; font-weight:600;">Page {pno}</span>'))
            h_bar.addStretch()
            c_l.addLayout(h_bar)

            lbl = QLabel()
            lbl.setFixedHeight(110)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet("background: #070b09; border-radius: 6px;")
            pix = QPixmap(ipath)
            if not pix.isNull():
                lbl.setPixmap(pix.scaled(QSize(180, 105), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
                lbl.setCursor(Qt.CursorShape.PointingHandCursor)
                lbl.mousePressEvent = lambda e, p=ipath, pn=pno: ImageLightboxDialog(p, f"{self.manual_info.get('name')} - Page {pn} Figure", parent=self).exec()
            c_l.addWidget(lbl)
            self.fig_lay.insertWidget(self.fig_lay.count() - 1, card)

    def _populate_bookmarks(self):
        self.bm_list.clear()
        if not self.manual_id:
            return
        bms = db.get_manual_bookmarks(self.manual_id)
        for b in bms:
            note_str = f": {b['note']}" if b.get("note") else ""
            item = QListWidgetItem(f"Page {b['page_number']}{note_str}")
            item.setData(Qt.ItemDataRole.UserRole, b["page_number"])
            self.bm_list.addItem(item)

    def _on_bookmark_clicked(self, item):
        pno = item.data(Qt.ItemDataRole.UserRole)
        if pno:
            self.jump_to_page(int(pno))

    def _populate_details(self):
        if not self.manual_info:
            return
        sz = self.manual_info.get("file_size", 0)
        sz_mb = f"{sz / (1024*1024):.1f} MB" if sz else "—"
        summary_txt = self.manual_info.get("summary") or "Technical hardware documentation."
        self.det_summary_lbl.setText(
            f"<b>File Size:</b> {sz_mb}<br>"
            f"<b>Total Pages:</b> {self.total_pages}<br>"
            f"<b>Added:</b> {self.manual_info.get('created_at', '—')}<br><br>"
            f"<b>Summary:</b><br>{summary_txt}"
        )

        # Scan for mentioned electronic components
        while self.comp_chips_lay.count():
            w = self.comp_chips_lay.takeAt(0)
            if w.widget():
                w.widget().deleteLater()

        all_comps = comp_service.get_all_components()
        all_text = ""
        if self.doc:
            for p in self.doc[:10]:
                all_text += " " + p.get_text("text").lower()

        found = []
        for c in all_comps:
            token = c.get("display_name", "").lower()
            if token and len(token) >= 3 and token in all_text:
                found.append(c)

        if not found:
            found = all_comps[:3]

        for c in found:
            btn = QPushButton(f"{c.get('display_name')} — {c.get('category')}")
            btn.setIcon(get_icon("cpu", "#00FF85", 13))
            btn.setProperty("kind", "secondary")
            btn.clicked.connect(lambda _=False, comp=c: self._open_component(comp))
            self.comp_chips_lay.addWidget(btn)

    def _open_component(self, comp):
        self.win.navigate_to(2)
        if hasattr(self.win.view, "lib_search"):
            self.win.view.lib_search.setText(comp.get("display_name", ""))

class MainView:
    """Builder for the modern 4-page electronic components learning interface."""
    def __init__(self, window):
        self.win = window
        self.stack = QStackedWidget()

    def setup_ui(self):
        outer = QVBoxLayout(self.win)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Persistent Top Navigation Bar
        self.top_bar = TopNavBar(self.win)
        outer.addWidget(self.top_bar)
        outer.addWidget(self.stack, 1)

        # Build the exact 4 pages requested
        self.dashboard_page = self._build_dashboard()   # Page 0
        self.chat_page = self._build_chat()             # Page 1
        self.library_page = self._build_library()       # Page 2
        self.manual_page = self._build_manuals_page()    # Page 3

        # Auxiliary background transition page (for long processing operations)
        self.busy_page = self._build_busy()

        # Add to stack in order
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

    def _page_scroll(self, max_width=1160):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        outer_content = QWidget()
        outer_lay = QHBoxLayout(outer_content)
        outer_lay.setContentsMargins(28, 20, 28, 24)
        outer_lay.setSpacing(0)

        inner_content = QWidget()
        if max_width:
            inner_content.setMaximumWidth(max_width)
        lay = QVBoxLayout(inner_content)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(18)

        outer_lay.addStretch(1)
        outer_lay.addWidget(inner_content, 12)
        outer_lay.addStretch(1)

        scroll.setWidget(outer_content)
        return scroll, lay

    # =========================================================================
    # PAGE 1: DASHBOARD / HOME
    # =========================================================================
    def _build_dashboard(self):
        page, lay = self._page_scroll(max_width=1180)

        # Compact Header
        dash_header = QHBoxLayout()
        dash_header.setContentsMargins(0, 0, 0, 4)
        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        title_box.addWidget(label("Dashboard", "h1", wrap=False))
        title_box.addWidget(label("Identify electronic components, inspect pinouts, and explore manuals", "subtitle", wrap=False))
        dash_header.addLayout(title_box)
        dash_header.addStretch()
        lay.addLayout(dash_header)

        # Quick Actions Grid (4 Standout Cards)
        lay.addWidget(label("QUICK ACTIONS", "h2", wrap=False))
        actions_grid = QGridLayout()
        actions_grid.setSpacing(14)

        act1 = QuickActionCard(
            "upload",
            "Upload Image",
            "Select photo from disk",
            accent_color="#00FF85",
            kind="qaCardPrimary",
            slot=self.win.upload_photo
        )
        actions_grid.addWidget(act1, 0, 0)

        act2 = QuickActionCard(
            "camera",
            "Live Camera Scan",
            "Point camera at board",
            accent_color="#14B8A6",
            kind="qaCardTeal",
            slot=self.win.open_camera
        )
        actions_grid.addWidget(act2, 0, 1)

        act3 = QuickActionCard(
            "video",
            "Upload Video",
            "Analyze video frames",
            accent_color="#10B981",
            kind="qaCardMint",
            slot=self.win.upload_video
        )
        actions_grid.addWidget(act3, 0, 2)

        act4 = QuickActionCard(
            "message-square",
            "Ask AI Question",
            "Chat about components",
            accent_color="#84CC16",
            kind="qaCardLime",
            slot=lambda: self.win.open_chat()
        )
        actions_grid.addWidget(act4, 0, 3)

        lay.addLayout(actions_grid)

        # Component Identification Result Card
        self.dash_result_card = QFrame()
        self.dash_result_card.setObjectName("card")
        res_lay = QVBoxLayout(self.dash_result_card)
        res_lay.setContentsMargins(22, 18, 22, 18)
        res_lay.setSpacing(14)

        r_head = QHBoxLayout()
        r_head.addWidget(label("COMPONENT IDENTIFICATION RESULT", "h1", wrap=False))
        r_head.addStretch()
        self.dash_match_badge = label("Ready to Scan", "badgeOk", wrap=False)
        r_head.addWidget(self.dash_match_badge)
        res_lay.addLayout(r_head)

        # Side-by-side images (Uploaded Photo vs Matched Reference)
        self.img_row = QHBoxLayout()
        self.img_row.setSpacing(16)

        self.uploaded_box = QWidget()
        up_lay = QVBoxLayout(self.uploaded_box)
        up_lay.setContentsMargins(0, 0, 0, 0)
        up_lay.setSpacing(4)
        self.uploaded_caption = label("Uploaded Photo / Frame", "caption", align=Qt.AlignmentFlag.AlignCenter)
        up_lay.addWidget(self.uploaded_caption)
        self.hw_image = label("", align=Qt.AlignmentFlag.AlignCenter)
        self.hw_image.setStyleSheet("background:#080c12; border:1px solid #1f2a3a; border-radius:12px;")
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
        self.matched_hw_image.setStyleSheet("background:#080c12; border:1px solid #1f2a3a; border-radius:12px;")
        self.matched_hw_image.setFixedHeight(220)
        mat_lay.addWidget(self.matched_hw_image)
        self.img_row.addWidget(self.matched_box, 1)
        self.matched_box.setVisible(False)

        res_lay.addLayout(self.img_row)

        # Specs grid
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

        # Description / Learning Note
        self.dash_desc_lbl = label("Upload an image or use the live camera to identify your electronic component.", "muted")
        res_lay.addWidget(self.dash_desc_lbl)

        # Manual selector / Match status
        self.match_status = label("", "badgeOk")
        self.match_detail = label("", "muted")
        res_lay.addWidget(self.match_status)
        res_lay.addWidget(self.match_detail)

        self.manual_combo = QComboBox()
        self.manual_combo.currentIndexChanged.connect(self.win._update_continue)
        res_lay.addWidget(self.manual_combo)

        # Result Action buttons
        res_btn_row = QHBoxLayout()
        self.dash_ask_comp_btn = button("Ask Assistant About This Component", "primary", slot=self.win.ask_about_scanned_component)
        self.dash_ask_comp_btn.setIcon(get_icon("message-square", "#ffffff", 14))
        self.dash_ask_comp_btn.setEnabled(False)
        res_btn_row.addWidget(self.dash_ask_comp_btn)

        self.continue_btn = button("Open Manual Instructions", "secondary", self.win.continue_from_result)
        self.continue_btn.setIcon(get_icon("book-open", "#10B981", 14))
        res_btn_row.addWidget(self.continue_btn)
        res_btn_row.addStretch()

        res_lay.addLayout(res_btn_row)
        lay.addWidget(self.dash_result_card)

        # Recent Scans & Activity Section
        lay.addWidget(label("RECENT SCANS & IDENTIFICATIONS", "h2", wrap=False))
        self.dash_scans_list = QListWidget()
        self.dash_scans_list.setFixedHeight(150)
        self.dash_scans_list.itemClicked.connect(self.win.on_recent_scan_clicked)
        lay.addWidget(self.dash_scans_list)

        scans_btn_row = QHBoxLayout()
        scans_btn_row.addStretch()
        self.dash_clear_scans_btn = button("Clear Recent Scans", "danger", slot=self.win.clear_recent_scans)
        self.dash_clear_scans_btn.setIcon(get_icon("trash-2", "#fca5a5", 14))
        scans_btn_row.addWidget(self.dash_clear_scans_btn)
        lay.addLayout(scans_btn_row)

        # Dynamic Overview Section replacing static beginner tips
        overview_grid = QGridLayout()
        overview_grid.setSpacing(16)

        # Card A: Continue Where You Left Off
        self.dash_continue_card = QFrame()
        self.dash_continue_card.setObjectName("card")
        c_lay = QVBoxLayout(self.dash_continue_card)
        c_lay.setContentsMargins(18, 16, 18, 16)
        c_lay.setSpacing(12)

        c_head = QHBoxLayout()
        c_head.addWidget(label("Continue Where You Left Off", "h2", wrap=False))
        c_head.addStretch()
        c_lay.addLayout(c_head)

        self.dash_chats_container = QVBoxLayout()
        self.dash_chats_container.setSpacing(8)
        c_lay.addLayout(self.dash_chats_container)
        c_lay.addStretch()

        overview_grid.addWidget(self.dash_continue_card, 0, 0)

        # Card B: Hardware Manuals Overview
        self.dash_manuals_card = QFrame()
        self.dash_manuals_card.setObjectName("card")
        m_lay = QVBoxLayout(self.dash_manuals_card)
        m_lay.setContentsMargins(18, 16, 18, 16)
        m_lay.setSpacing(12)

        m_head = QHBoxLayout()
        m_head.addWidget(label("Hardware Manuals Overview", "h2", wrap=False))
        m_head.addStretch()
        self.dash_manage_manuals_btn = button("Manage Manuals", "secondary", slot=lambda: self.win.navigate_to(3))
        self.dash_manage_manuals_btn.setIcon(get_icon("book-open", "#10B981", 14))
        m_head.addWidget(self.dash_manage_manuals_btn)
        m_lay.addLayout(m_head)

        self.dash_manuals_container = QVBoxLayout()
        self.dash_manuals_container.setSpacing(8)
        m_lay.addLayout(self.dash_manuals_container)
        m_lay.addStretch()

        overview_grid.addWidget(self.dash_manuals_card, 0, 1)

        lay.addLayout(overview_grid)
        return page

    # =========================================================================
    # PAGE 2: CHAT / ASSISTANT
    # =========================================================================
    def _build_chat(self):
        p = QWidget()
        main_h_lay = QHBoxLayout(p)
        main_h_lay.setContentsMargins(0, 0, 0, 0)
        main_h_lay.setSpacing(0)

        # ---------------------------------------------------------------------
        # Redesigned Chat History Sidebar (Grouped, Searchable, Sleek)
        # ---------------------------------------------------------------------
        self.chat_sidebar = QFrame()
        self.chat_sidebar.setObjectName("sidebarFrame")
        self.chat_sidebar.setFixedWidth(290)
        s_lay = QVBoxLayout(self.chat_sidebar)
        s_lay.setContentsMargins(14, 16, 14, 16)
        s_lay.setSpacing(10)

        # Header row: New Chat + Collapse Button
        s_top = QHBoxLayout()
        self.new_chat_btn = button("New Chat", "primary", slot=self.win.new_chat)
        self.new_chat_btn.setIcon(get_icon("plus", "#ffffff", 14))
        self.new_chat_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        s_top.addWidget(self.new_chat_btn)

        self.collapse_sidebar_btn = button("", slot=self.win.toggle_sidebar)
        self.collapse_sidebar_btn.setIcon(get_icon("panel-left-close", "#94a3b8", 16))
        self.collapse_sidebar_btn.setFixedWidth(36)
        self.collapse_sidebar_btn.setToolTip("Collapse Sidebar")
        s_top.addWidget(self.collapse_sidebar_btn)
        s_lay.addLayout(s_top)

        # Search box to filter chats dynamically
        self.chat_search = QLineEdit()
        self.chat_search.setPlaceholderText("Search chats...")
        self.chat_search.textChanged.connect(self.win.filter_chat_history)
        s_lay.addWidget(self.chat_search)

        # Scrollable area for categorized chats with custom slim scrollbar
        self.sidebar_scroll = QScrollArea()
        self.sidebar_scroll.setWidgetResizable(True)
        self.sidebar_scroll.setStyleSheet("background:transparent; border:none;")
        self.sidebar_container = QWidget()
        self.sidebar_groups_lay = QVBoxLayout(self.sidebar_container)
        self.sidebar_groups_lay.setContentsMargins(0, 4, 0, 4)
        self.sidebar_groups_lay.setSpacing(6)
        self.sidebar_groups_lay.addStretch()

        self.sidebar_scroll.setWidget(self.sidebar_container)
        s_lay.addWidget(self.sidebar_scroll, 1)

        # Footer info
        s_footer = QHBoxLayout()
        self.chat_count_lbl = label("0 conversations", "caption", wrap=False)
        self.chat_history_list = self.sidebar_scroll
        self.sidebar_delete_btn = None
        self.export_recent_btn = None
        s_footer.addWidget(self.chat_count_lbl)
        s_footer.addStretch()
        s_lay.addLayout(s_footer)

        main_h_lay.addWidget(self.chat_sidebar)

        # ---------------------------------------------------------------------
        # Main Chat Area (Centered Column, Interactive Controls)
        # ---------------------------------------------------------------------
        chat_area = QWidget()
        outer_chat_lay = QHBoxLayout(chat_area)
        outer_chat_lay.setContentsMargins(0, 0, 0, 0)
        outer_chat_lay.setSpacing(0)

        # Centered container column
        chat_col = QWidget()
        chat_col.setMaximumWidth(920)
        c_lay = QVBoxLayout(chat_col)
        c_lay.setContentsMargins(20, 16, 20, 16)
        c_lay.setSpacing(10)

        # Header bar
        top_bar = QHBoxLayout()
        top_bar.setSpacing(10)

        self.expand_sidebar_btn = button("Chats", slot=self.win.toggle_sidebar)
        self.expand_sidebar_btn.setIcon(get_icon("panel-left-open", "#94a3b8", 16))
        self.expand_sidebar_btn.setVisible(False)
        top_bar.addWidget(self.expand_sidebar_btn)

        self.chat_manual_badge = label("Scope: All Manuals", "h1", wrap=False)
        top_bar.addWidget(self.chat_manual_badge)
        top_bar.addStretch()

        self.chat_export_btn = button("Export Chat", "secondary")
        self.chat_export_btn.setIcon(get_icon("download", "#94a3b8", 14))
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

        # Scrollable Thread Container
        self.chat_scroll = QScrollArea()
        self.chat_scroll.setWidgetResizable(True)
        self.chat_scroll.setStyleSheet("background:transparent; border:none;")

        self.chat_thread_widget = QWidget()
        self.chat_thread_lay = QVBoxLayout(self.chat_thread_widget)
        self.chat_thread_lay.setContentsMargins(10, 10, 10, 10)
        self.chat_thread_lay.setSpacing(14)
        self.chat_thread_lay.addStretch()

        self.chat_scroll.setWidget(self.chat_thread_widget)

        # Floating 'Scroll to bottom' button
        self.scroll_bottom_btn = QPushButton(self.chat_scroll)
        self.scroll_bottom_btn.setObjectName("scrollBottomBtn")
        self.scroll_bottom_btn.setIcon(get_icon("arrow-down", "#00FF85", 16))
        self.scroll_bottom_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.scroll_bottom_btn.setToolTip("Scroll to bottom")
        self.scroll_bottom_btn.clicked.connect(self.win.scroll_chat_to_bottom)
        self.scroll_bottom_btn.hide()
        self.chat_scroll.verticalScrollBar().valueChanged.connect(self.win._on_chat_scroll_moved)

        c_lay.addWidget(self.chat_scroll, 1)

        # Typing & Streaming Indicator Card with Stop Button
        self.typing_card = QFrame()
        self.typing_card.setObjectName("typingCard")
        t_lay = QHBoxLayout(self.typing_card)
        t_lay.setContentsMargins(16, 10, 16, 10)
        t_lay.setSpacing(10)

        t_icon = QLabel()
        t_icon.setPixmap(get_pixmap("clock", "#00FF85", 16))
        t_lay.addWidget(t_icon)

        self.typing_lbl = label("Searching manual excerpts & reasoning...", "badgeOk", wrap=False)
        t_lay.addWidget(self.typing_lbl, 1)

        self.stop_btn = button("Stop Generating", "danger", slot=self.win.stop_generating)
        self.stop_btn.setIcon(get_icon("square", "#ffffff", 12))
        self.stop_btn.setProperty("kind", "stopBtn")
        t_lay.addWidget(self.stop_btn)

        self.typing_card.setVisible(False)
        c_lay.addWidget(self.typing_card)

        # ---------------------------------------------------------------------
        # Bottom Input Area (Tidy Scope Toolbar + Voice Overlay + Text Input)
        # ---------------------------------------------------------------------
        bottom_box = QFrame()
        bottom_box.setObjectName("card")
        b_lay = QVBoxLayout(bottom_box)
        b_lay.setContentsMargins(14, 12, 14, 12)
        b_lay.setSpacing(10)

        # Voice Input Overlay Bar (Active during recording)
        self.voice_bar = QFrame()
        self.voice_bar.setObjectName("voiceBar")
        vb_lay = QHBoxLayout(self.voice_bar)
        vb_lay.setContentsMargins(12, 8, 12, 8)
        vb_lay.setSpacing(12)

        mic_rec_icon = QLabel()
        mic_rec_icon.setPixmap(get_pixmap("mic", "#00FF85", 20))
        vb_lay.addWidget(mic_rec_icon)

        self.voice_timer_lbl = label("0:00", "boldText", wrap=False)
        self.voice_timer_lbl.setStyleSheet("color:#00FF85; font-weight:700; font-size:14px;")
        vb_lay.addWidget(self.voice_timer_lbl)

        self.voice_level_bar = QProgressBar()
        self.voice_level_bar.setRange(0, 100)
        self.voice_level_bar.setValue(0)
        self.voice_level_bar.setTextVisible(False)
        self.voice_level_bar.setFixedHeight(8)
        self.voice_level_bar.setStyleSheet("QProgressBar::chunk { background: #00FF85; border-radius: 4px; }")
        vb_lay.addWidget(self.voice_level_bar, 1)

        self.voice_lang_combo = QComboBox()
        self.voice_lang_combo.addItem("English (Auto)", "en")
        self.voice_lang_combo.addItem("English (India)", "en-IN")
        self.voice_lang_combo.addItem("Hindi (हिन्दी)", "hi")
        self.voice_lang_combo.setFixedHeight(28)
        vb_lay.addWidget(self.voice_lang_combo)

        self.voice_done_btn = button("Done", "primary", slot=self.win.stop_voice_input)
        self.voice_done_btn.setIcon(get_icon("check", "#ffffff", 14))
        self.voice_done_btn.setFixedHeight(28)
        vb_lay.addWidget(self.voice_done_btn)

        self.voice_cancel_btn = button("Cancel", "secondary", slot=self.win.cancel_voice_input)
        self.voice_cancel_btn.setIcon(get_icon("x", "#94a3b8", 12))
        self.voice_cancel_btn.setFixedHeight(28)
        vb_lay.addWidget(self.voice_cancel_btn)

        self.voice_bar.setVisible(False)
        b_lay.addWidget(self.voice_bar)

        # Text input row
        input_row = QHBoxLayout()
        input_row.setSpacing(8)

        self.chat_input = ChatTextEdit()
        self.chat_input.submit_requested.connect(self.win.send_chat_message)
        input_row.addWidget(self.chat_input, 1)

        self.chat_send_btn = button("Send", "primary", slot=self.win.send_chat_message)
        self.chat_send_btn.setIcon(get_icon("send", "#ffffff", 14))
        self.chat_send_btn.setFixedSize(80, 46)
        input_row.addWidget(self.chat_send_btn)

        b_lay.addLayout(input_row)

        # Manual Scope Controls & Quick Actions Toolbar
        scope_row = QHBoxLayout()
        scope_row.setSpacing(8)

        # Scope Chip
        self.scope_chip_btn = button("All manuals", "chipActive", slot=self.win.open_scope_picker)
        self.scope_chip_btn.setIcon(get_icon("book-open", "#00FF85", 14))
        self.scope_chip_btn.setToolTip("Click to change manual scope")
        scope_row.addWidget(self.scope_chip_btn)

        self.scope_add_btn = button("Add Manual", "secondary", slot=self.win.add_manual_multi)
        self.scope_add_btn.setIcon(get_icon("upload", "#94a3b8", 13))
        self.scope_add_btn.setStyleSheet("padding: 5px 10px; font-size: 12.5px;")
        scope_row.addWidget(self.scope_add_btn)

        self.scope_manage_btn = button("Manage", "secondary", slot=self.win.manage_manuals_modal)
        self.scope_manage_btn.setIcon(get_icon("settings", "#94a3b8", 13))
        self.scope_manage_btn.setStyleSheet("padding: 5px 10px; font-size: 12.5px;")
        scope_row.addWidget(self.scope_manage_btn)

        self.scope_clear_btn = button("Reset Scope", "secondary", slot=self.win.reset_scope_to_all)
        self.scope_clear_btn.setStyleSheet("padding: 5px 10px; font-size: 12.5px;")
        self.scope_clear_btn.setVisible(False)
        scope_row.addWidget(self.scope_clear_btn)

        scope_row.addSpacing(6)

        # Deep-dive toggle
        self.chat_full_check = QCheckBox("Deep-dive")
        self.chat_full_check.setToolTip("Checks all indexed manual pages thoroughly")
        scope_row.addWidget(self.chat_full_check)

        scope_row.addStretch()

        # Attach Photo button
        self.chat_attach_btn = button("Attach Photo", "secondary", slot=self.win.attach_photo_to_chat)
        self.chat_attach_btn.setIcon(get_icon("camera", "#94a3b8", 13))
        self.chat_attach_btn.setStyleSheet("padding: 5px 10px; font-size: 12.5px;")
        scope_row.addWidget(self.chat_attach_btn)

        # Voice input button
        self.chat_speak_btn = button("Voice", "secondary", slot=self.win.toggle_voice_input)
        self.chat_speak_btn.setIcon(get_icon("mic", "#00FF85", 13))
        self.chat_speak_btn.setStyleSheet("padding: 5px 10px; font-size: 12.5px;")
        scope_row.addWidget(self.chat_speak_btn)

        b_lay.addLayout(scope_row)

        c_lay.addWidget(bottom_box)

        # Add centered chat column with flex spacing
        outer_chat_lay.addStretch(1)
        outer_chat_lay.addWidget(chat_col, 10)
        outer_chat_lay.addStretch(1)

        main_h_lay.addWidget(chat_area, 1)
        return p

    # =========================================================================
    # PAGE 3: COMPONENT LIBRARY / LEARN
    # =========================================================================
        # =========================================================================
    # PAGE 3: COMPONENT LIBRARY / LEARN
    # =========================================================================
    def _build_library(self):
        page = QWidget()
        outer_lay = QVBoxLayout(page)
        outer_lay.setContentsMargins(0, 0, 0, 0)
        outer_lay.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setObjectName("libScroll")

        content = QWidget()
        c_lay = QVBoxLayout(content)
        c_lay.setContentsMargins(28, 24, 28, 28)
        c_lay.setSpacing(16)
        c_lay.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Centered container with max-width 1320px
        centered_box = QWidget()
        centered_box.setMaximumWidth(1320)
        box_lay = QVBoxLayout(centered_box)
        box_lay.setContentsMargins(0, 0, 0, 0)
        box_lay.setSpacing(16)

        # 1. Page Header: Title and subtitle
        head_box = QVBoxLayout()
        head_box.setSpacing(4)
        title_lbl = QLabel("Component Library")
        title_lbl.setStyleSheet("font-size: 24px; font-weight: 800; color: #F3FBF5; letter-spacing: -0.3px;")
        sub_lbl = QLabel("Explore electronic components, view pinouts, specs and more")
        sub_lbl.setStyleSheet("font-size: 13.5px; color: #6B8273;")
        head_box.addWidget(title_lbl)
        head_box.addWidget(sub_lbl)
        box_lay.addLayout(head_box)

        # 2. Search & Filter Bar
        search_row = QHBoxLayout()
        search_row.setSpacing(10)

        self.lib_search = QLineEdit()
        self.lib_search.setPlaceholderText("Search components...")
        self.lib_search.setClearButtonEnabled(True)
        self.lib_search.addAction(get_icon("search", "#6B8273", 16), QLineEdit.ActionPosition.LeadingPosition)
        self.lib_search.textChanged.connect(self.win.filter_library_cards)
        search_row.addWidget(self.lib_search, 1)

        self.lib_filter_btn = QPushButton("Filter")
        self.lib_filter_btn.setIcon(get_icon("sliders", "#00FF85", 14))
        self.lib_filter_btn.setProperty("kind", "secondary")
        self.lib_filter_btn.setStyleSheet("padding: 9px 16px; font-weight: 600; border-radius: 10px;")
        self.lib_filter_menu = QMenu(self.lib_filter_btn)
        self.lib_filter_btn.setMenu(self.lib_filter_menu)
        search_row.addWidget(self.lib_filter_btn)

        box_lay.addLayout(search_row)

        # 3. Category Pills Bar (Horizontal Scroll Area)
        pills_scroll = QScrollArea()
        pills_scroll.setWidgetResizable(True)
        pills_scroll.setFixedHeight(46)
        pills_scroll.setFrameShape(QFrame.Shape.NoFrame)
        pills_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        pills_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        pills_scroll.setStyleSheet("background: transparent; border: none;")

        pills_content = QWidget()
        self.chip_bar = QHBoxLayout(pills_content)
        self.chip_bar.setContentsMargins(0, 2, 0, 2)
        self.chip_bar.setSpacing(8)
        self.chip_buttons = []

        for cat in comp_service.get_categories():
            btn = QPushButton(cat)
            btn.setProperty("kind", "catPillActive" if cat == "All" else "catPill")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _=False, c=cat: self.win.on_category_chip_clicked(c))
            self.chip_bar.addWidget(btn)
            self.chip_buttons.append((cat, btn))

        self.chip_bar.addStretch()
        pills_scroll.setWidget(pills_content)
        box_lay.addWidget(pills_scroll)

        # 4. Status summary row
        status_row = QHBoxLayout()
        self.lib_status_lbl = QLabel()
        self.lib_status_lbl.setStyleSheet("font-size: 12px; color: #6B8273;")
        status_row.addWidget(self.lib_status_lbl)
        status_row.addStretch()
        box_lay.addLayout(status_row)

        # 5. Responsive Card Grid
        self.lib_grid = ResponsiveCardGrid()
        box_lay.addWidget(self.lib_grid)

        # Empty State
        self.lib_no_results = QWidget()
        no_res_lay = QVBoxLayout(self.lib_no_results)
        no_res_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        no_res_lay.setContentsMargins(20, 40, 20, 40)
        no_res_icon = QLabel()
        no_res_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        no_res_icon.setPixmap(get_pixmap("search", "#6B8273", 42))
        no_res_lay.addWidget(no_res_icon)
        no_res_title = QLabel("No components found")
        no_res_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        no_res_title.setStyleSheet("font-size: 16px; font-weight: 700; color: #cbd5e1; margin-top: 10px;")
        no_res_lay.addWidget(no_res_title)
        no_res_sub = QLabel("Try adjusting your search query or selecting a different category pill.")
        no_res_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        no_res_sub.setStyleSheet("font-size: 13px; color: #6B8273;")
        no_res_lay.addWidget(no_res_sub)
        self.lib_no_results.setVisible(False)
        box_lay.addWidget(self.lib_no_results)

        c_lay.addWidget(centered_box, alignment=Qt.AlignmentFlag.AlignHCenter)
        scroll.setWidget(content)
        outer_lay.addWidget(scroll, 1)

        # Backward compatibility properties
        self.cards_lay = self.lib_grid.grid_layout

        return page

    # =========================================================================
    # PAGE 4: HARDWARE MANUALS & INTERACTIVE PDF VIEWER
    # =========================================================================
    def _build_manuals_page(self):
        page = QWidget()
        outer = QVBoxLayout(page)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self.manuals_stack = QStackedWidget()

        # VIEW 0: Manuals Hub & Management
        hub = QWidget()
        hub_scroll = QScrollArea()
        hub_scroll.setWidgetResizable(True)
        hub_scroll.setFrameShape(QFrame.Shape.NoFrame)
        hub_content = QWidget()
        hc_lay = QVBoxLayout(hub_content)
        hc_lay.setContentsMargins(28, 24, 28, 28)
        hc_lay.setSpacing(16)
        hc_lay.setAlignment(Qt.AlignmentFlag.AlignTop)

        centered = QWidget()
        centered.setMaximumWidth(1320)
        c_lay = QVBoxLayout(centered)
        c_lay.setContentsMargins(0, 0, 0, 0)
        c_lay.setSpacing(16)

        # 1. Header Bar: Title + Subtitle + Action buttons
        head_row = QHBoxLayout()
        h_col = QVBoxLayout()
        h_col.setSpacing(4)
        t_lbl = QLabel("Hardware Manuals")
        t_lbl.setStyleSheet("font-size: 24px; font-weight: 800; color: #F3FBF5;")
        s_lbl = QLabel("Upload, index, inspect and search PDF hardware documentation and datasheets")
        s_lbl.setStyleSheet("font-size: 13.5px; color: #6B8273;")
        h_col.addWidget(t_lbl)
        h_col.addWidget(s_lbl)
        head_row.addLayout(h_col, 1)

        self.man_add_btn = QPushButton("Add Manuals")
        self.man_add_btn.setIcon(get_icon("plus", "#060907", 14))
        self.man_add_btn.setProperty("kind", "primary")
        self.man_add_btn.clicked.connect(self.win.add_manual_multi)
        head_row.addWidget(self.man_add_btn)

        self.man_reindex_all_btn = QPushButton("Re-index All")
        self.man_reindex_all_btn.setIcon(get_icon("refresh-cw", "#00FF85", 14))
        self.man_reindex_all_btn.setProperty("kind", "secondary")
        self.man_reindex_all_btn.clicked.connect(self.win.reindex_all_manuals)
        head_row.addWidget(self.man_reindex_all_btn)

        c_lay.addLayout(head_row)

        # 2. Summary Statistics Panel (4 cards)
        stats_row = QHBoxLayout()
        stats_row.setSpacing(12)

        def make_stat_card(title, value, icon_name):
            card = QFrame()
            card.setObjectName("statCard")
            sc_l = QHBoxLayout(card)
            sc_l.setContentsMargins(12, 10, 12, 10)
            sc_l.setSpacing(10)

            ic = QLabel()
            ic.setPixmap(get_pixmap(icon_name, "#00FF85", 22))
            sc_l.addWidget(ic)

            tc = QVBoxLayout()
            tc.setSpacing(1)
            v_l = QLabel(value)
            v_l.setStyleSheet("font-size: 16px; font-weight: 800; color: #F3FBF5;")
            t_l = QLabel(title)
            t_l.setStyleSheet("font-size: 11.5px; color: #6B8273;")
            tc.addWidget(v_l)
            tc.addWidget(t_l)
            sc_l.addLayout(tc, 1)
            return card, v_l

        self.stat_card_total, self.stat_total_val = make_stat_card("Total Manuals", "0", "book-open")
        self.stat_card_pages, self.stat_pages_val = make_stat_card("Pages Indexed", "0", "file-text")
        self.stat_card_chat, self.stat_chat_val = make_stat_card("AI Search Enabled", "0", "message-square")
        self.stat_card_storage, self.stat_storage_val = make_stat_card("Storage Used", "0 MB", "hard-drive")

        for sc in (self.stat_card_total, self.stat_card_pages, self.stat_card_chat, self.stat_card_storage):
            stats_row.addWidget(sc)
        c_lay.addLayout(stats_row)

        # 3. Recently Viewed Row (horizontal list of cards)
        self.recent_box = QWidget()
        rec_lay = QVBoxLayout(self.recent_box)
        rec_lay.setContentsMargins(0, 0, 0, 0)
        rec_lay.setSpacing(8)
        rec_title = QLabel("RECENTLY VIEWED")
        rec_title.setStyleSheet("font-size: 11.5px; font-weight: 700; color: #6B8273; letter-spacing: 0.5px;")
        rec_lay.addWidget(rec_title)

        self.recent_cards_lay = QHBoxLayout()
        self.recent_cards_lay.setSpacing(10)
        rec_lay.addLayout(self.recent_cards_lay)
        c_lay.addWidget(self.recent_box)

        # 4. Drag-and-Drop Zone
        self.drop_zone = ManualDropZone(
            on_files_dropped=self.win.import_manual_files,
            on_browse_clicked=self.win.add_manual_multi
        )
        c_lay.addWidget(self.drop_zone)

        # 5. Filter & Search Toolbar
        filter_bar = QHBoxLayout()
        filter_bar.setSpacing(10)

        self.man_search = QLineEdit()
        self.man_search.setPlaceholderText("Search manuals by name, manufacturer, or model...")
        self.man_search.setClearButtonEnabled(True)
        self.man_search.addAction(get_icon("search", "#6B8273", 16), QLineEdit.ActionPosition.LeadingPosition)
        self.man_search.textChanged.connect(self.win.filter_manuals_list)
        filter_bar.addWidget(self.man_search, 1)

        self.man_sort_combo = QComboBox()
        self.man_sort_combo.addItems(["Newest Added", "Name (A-Z)", "Size (Largest)", "Pages (Most)", "Recently Viewed"])
        self.man_sort_combo.currentTextChanged.connect(self.win.filter_manuals_list)
        filter_bar.addWidget(self.man_sort_combo)

        # Grid / List Toggle
        self.view_grid_btn = QPushButton()
        self.view_grid_btn.setIcon(get_icon("grid", "#00FF85", 15))
        self.view_grid_btn.setFixedSize(36, 36)
        self.view_grid_btn.setToolTip("Grid View")
        self.view_grid_btn.clicked.connect(lambda: self.win.set_manuals_view_mode("grid"))
        filter_bar.addWidget(self.view_grid_btn)

        self.view_list_btn = QPushButton()
        self.view_list_btn.setIcon(get_icon("list", "#6B8273", 15))
        self.view_list_btn.setFixedSize(36, 36)
        self.view_list_btn.setToolTip("List View")
        self.view_list_btn.clicked.connect(lambda: self.win.set_manuals_view_mode("list"))
        filter_bar.addWidget(self.view_list_btn)

        # Bulk Delete Button
        self.bulk_delete_btn = QPushButton("Delete Selected")
        self.bulk_delete_btn.setIcon(get_icon("trash-2", "#fca5a5", 13))
        self.bulk_delete_btn.setProperty("kind", "danger")
        self.bulk_delete_btn.clicked.connect(self.win.bulk_delete_manuals)
        self.bulk_delete_btn.setVisible(False)
        filter_bar.addWidget(self.bulk_delete_btn)

        c_lay.addLayout(filter_bar)

        # Collections / Tag Filter Pills
        self.tags_scroll = QScrollArea()
        self.tags_scroll.setWidgetResizable(True)
        self.tags_scroll.setFixedHeight(42)
        self.tags_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.tags_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.tags_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.tags_scroll.setStyleSheet("background:transparent; border:none;")

        self.tags_content = QWidget()
        self.tags_lay = QHBoxLayout(self.tags_content)
        self.tags_lay.setContentsMargins(0, 0, 0, 0)
        self.tags_lay.setSpacing(6)
        self.tags_lay.addStretch()
        self.tags_scroll.setWidget(self.tags_content)
        c_lay.addWidget(self.tags_scroll)

        # 6. Manuals Container: Grid & List host
        self.manuals_container = QWidget()
        self.manuals_lay = QVBoxLayout(self.manuals_container)
        self.manuals_lay.setContentsMargins(0, 0, 0, 0)
        self.manuals_lay.setSpacing(14)
        c_lay.addWidget(self.manuals_container)

        # Empty State
        self.man_empty = QWidget()
        me_lay = QVBoxLayout(self.man_empty)
        me_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        me_lay.setContentsMargins(20, 40, 20, 40)
        me_lay.setSpacing(12)

        e_icon = QLabel()
        e_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        e_icon.setPixmap(get_pixmap("book-open", "#6B8273", 44))
        me_lay.addWidget(e_icon)

        e_title = QLabel("No manuals indexed yet")
        e_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        e_title.setStyleSheet("font-size: 16px; font-weight: 700; color: #cbd5e1;")
        me_lay.addWidget(e_title)

        e_sub = QLabel("Drag and drop manufacturer hardware PDF manuals above to extract schematics, pinouts, and knowledge.")
        e_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        e_sub.setStyleSheet("font-size: 13px; color: #6B8273;")
        me_lay.addWidget(e_sub)

        first_btn = QPushButton("Add your first manual")
        first_btn.setProperty("kind", "primary")
        first_btn.setIcon(get_icon("plus", "#060907", 14))
        first_btn.clicked.connect(self.win.add_manual_multi)
        me_lay.addWidget(first_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        c_lay.addWidget(self.man_empty)
        self.man_empty.setVisible(False)

        hc_lay.addWidget(centered, alignment=Qt.AlignmentFlag.AlignHCenter)
        hub_scroll.setWidget(hub_content)
        outer_hub_lay = QVBoxLayout(hub)
        outer_hub_lay.setContentsMargins(0, 0, 0, 0)
        outer_hub_lay.addWidget(hub_scroll)
        self.manuals_stack.addWidget(hub)

        # VIEW 1: Interactive PDF Viewer
        self.viewer_widget = InteractiveManualViewer(self.win, on_back_cb=lambda: self.manuals_stack.setCurrentIndex(0))
        self.manuals_stack.addWidget(self.viewer_widget)

        outer.addWidget(self.manuals_stack)

        # Backward compatibility aliases
        self.embedded_viewer_widget = self.viewer_widget
        self.ev_scroll = self.viewer_widget.doc_scroll
        self.ev_page_lbl = self.viewer_widget.canvas_lbl
        self.ev_manual_lbl = self.viewer_widget.title_lbl
        self.ev_total_lbl = self.viewer_widget.total_lbl
        self.ev_page_spin = self.viewer_widget.page_spin
        self.ev_zoom_lbl = self.viewer_widget.zoom_lbl
        self.ev_toc_tree = self.viewer_widget.toc_tree
        self.ev_search_input = self.viewer_widget.search_input
        self.ev_search_list = self.viewer_widget.search_list

        return page


    def _build_busy(self):
        p = QWidget()
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
