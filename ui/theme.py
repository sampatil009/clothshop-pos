from PyQt5.QtWidgets import QLabel, QFrame, QHBoxLayout, QVBoxLayout, QSpacerItem, QSizePolicy
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

# ─── DESIGN TOKENS ────────────────────────────────────────────────────────────
PRIMARY       = "#002045"
PRIMARY_DARK  = "#001530"
PRIMARY_CONT  = "#1a365d"
SECONDARY     = "#1b6b51"
SEC_LIGHT     = "#a6f2d1"
SEC_CONTAINER = "#e8f8f1"
TERTIARY      = "#c0392b"
SURFACE       = "#f7f9fb"
SURF_LOW      = "#f2f4f6"
SURF_CARD     = "#ffffff"
SURF_HIGH     = "#e6e8ea"
ON_SURFACE    = "#191c1e"
ON_SURF_VAR   = "#43474e"
OUTLINE       = "#c4c6cf"
ERROR         = "#ba1a1a"
ERROR_BG      = "#ffdad6"
SUCCESS_BG    = "#e8f8f1"
WARN_BG       = "#fff3e0"

# ─── STYLESHEETS ──────────────────────────────────────────────────────────────
APP_STYLE = f"""
QMainWindow, QWidget {{ background: {SURFACE}; color: {ON_SURFACE}; border: none; }}
QLabel {{ background: transparent; border: none; }}
QGroupBox {{ border: 1px solid {OUTLINE}; border-radius: 4px; padding-top: 10px; margin-top: 10px; }}
QGroupBox::title {{ subcontrol-origin: margin; left: 10px; padding: 0 3px; }}
QScrollArea {{ border: none; background: transparent; }}
QScrollBar:vertical {{
    background: {SURF_LOW}; width: 6px; border-radius: 3px;
}}
QScrollBar::handle:vertical {{
    background: {OUTLINE}; border-radius: 3px; min-height: 30px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
QScrollBar:horizontal {{ height: 0px; }}
QLineEdit {{
    background: {SURF_CARD}; border: none;
    border-bottom: 2px solid {OUTLINE};
    border-radius: 0px; padding: 8px 12px;
    color: {ON_SURFACE}; font-size: 13px;
    selection-background-color: {SEC_LIGHT};
}}
QLineEdit:focus {{ border-bottom: 2px solid {SECONDARY}; }}
QLineEdit::placeholder {{ color: {ON_SURF_VAR}; }}
QComboBox {{
    combobox-popup: 0;
    background: {SURF_CARD}; border: none;
    border-bottom: 2px solid {OUTLINE};
    padding: 10px 15px; color: {ON_SURFACE}; font-size: 15px;
    border-radius: 0px;
}}
QComboBox:focus {{ border-bottom: 2px solid {SECONDARY}; }}
QComboBox::drop-down {{ border: none; width: 30px; }}

/* Force the popup list to respect sizing */
QComboBox QAbstractItemView, QComboBox QListView {{
    background-color: #ffffff;
    border: 1px solid {OUTLINE};
    selection-background-color: {SEC_CONTAINER};
    selection-color: {PRIMARY};
    outline: none;
    font-size: 16px;
    min-width: 250px;
}}
QComboBox QAbstractItemView::item, QComboBox QListView::item {{
    min-height: 40px;
    padding: 8px 15px;
    background-color: transparent;
    border-bottom: 1px solid #f1f5f9;
}}
QComboBox QAbstractItemView::item:selected, QComboBox QListView::item:selected {{
    background-color: {SEC_CONTAINER};
    color: {PRIMARY};
    font-weight: bold;
}}
QTableWidget {{
    background: {SURF_CARD}; border: none;
    gridline-color: transparent; font-size: 13px;
    color: {ON_SURFACE}; outline: none;
}}
QTableWidget::item {{
    padding: 12px 16px; border-bottom: 1px solid {SURF_HIGH};
}}
QTableWidget::item:selected {{
    background: {SEC_CONTAINER}; color: {ON_SURFACE};
}}
QTableWidget::item:hover {{
    background: {SURF_LOW};
}}
QHeaderView::section {{
    background: {SURF_LOW}; color: {ON_SURF_VAR};
    font-size: 11px; font-weight: 600; letter-spacing: 0.8px;
    padding: 10px 16px; border: none;
    border-bottom: 1px solid {SURF_HIGH};
    text-transform: uppercase;
}}
QProgressBar {{
    background: {SURF_HIGH}; border-radius: 3px;
    height: 6px; border: none; text-align: center;
}}
QProgressBar::chunk {{
    background: {SECONDARY}; border-radius: 3px;
}}
"""

SIDEBAR_STYLE = f"""
QWidget#Sidebar {{
    background: {PRIMARY};
    border-right: none;
}}
"""

NAV_BTN_STYLE = f"""
QPushButton {{
    background: transparent; color: rgba(255,255,255,0.65);
    border: none; border-radius: 8px;
    padding: 10px 16px; text-align: left;
    font-size: 13px; font-weight: 500;
}}
QPushButton:hover {{
    background: rgba(255,255,255,0.08);
    color: rgba(255,255,255,0.9);
}}
QPushButton:checked {{
    background: rgba(255,255,255,0.15);
    color: #ffffff;
    border-left: 3px solid {SEC_LIGHT};
}}
"""

PRIMARY_BTN = f"""
QPushButton {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
        stop:0 {PRIMARY}, stop:1 {PRIMARY_CONT});
    color: #ffffff; border: none; border-radius: 6px;
    padding: 10px 20px; font-size: 13px; font-weight: 600;
}}
QPushButton:hover {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
        stop:0 {PRIMARY_CONT}, stop:1 #243d6b);
}}
QPushButton:pressed {{ background: {PRIMARY_DARK}; }}
"""

SECONDARY_BTN = f"""
QPushButton {{
    background: {SECONDARY}; color: #ffffff;
    border: none; border-radius: 6px;
    padding: 10px 20px; font-size: 13px; font-weight: 600;
}}
QPushButton:hover {{ background: #155c43; }}
"""

GHOST_BTN = f"""
QPushButton {{
    background: transparent; color: {PRIMARY};
    border: 1.5px solid {OUTLINE}; border-radius: 6px;
    padding: 9px 18px; font-size: 13px; font-weight: 500;
}}
QPushButton:hover {{
    background: {SURF_LOW};
    border-color: {ON_SURF_VAR};
}}
"""

CARD_STYLE = f"""
QFrame {{
    background: {SURF_CARD}; border-radius: 8px;
    border: none;
}}
"""

# ─── HELPERS ──────────────────────────────────────────────────────────────────
def make_label(text, size=13, color=ON_SURFACE, bold=False, font_size=None):
    lbl = QLabel(text)
    fs = font_size or size
    w = QFont.Bold if bold else QFont.Normal
    lbl.setFont(QFont("Segoe UI", fs, w))
    lbl.setStyleSheet(f"color: {color}; background: transparent; border: none;")
    return lbl

def divider():
    line = QFrame()
    line.setFrameShape(QFrame.HLine)
    line.setStyleSheet(f"background: {SURF_HIGH}; border: none; max-height: 1px;")
    return line

def card(parent=None):
    f = QFrame(parent)
    f.setStyleSheet(CARD_STYLE)
    f.setObjectName("Card")
    shadow_effect_css = f"background: {SURF_CARD}; border-radius: 8px;"
    f.setStyleSheet(f"QFrame#{f.objectName()} {{ {shadow_effect_css} }}")
    return f

def status_pill(text, color=SECONDARY, bg=SEC_CONTAINER):
    lbl = QLabel(text)
    lbl.setFont(QFont("Segoe UI", 11, QFont.Bold))
    lbl.setStyleSheet(f"""
        color: {color}; background: {bg};
        border-radius: 4px; padding: 3px 10px;
    """)
    lbl.setAlignment(Qt.AlignCenter)
    lbl.setMaximumHeight(26)
    return lbl

def spacer(w=0, h=0, hpol=QSizePolicy.Fixed, vpol=QSizePolicy.Fixed):
    sp = QSpacerItem(w, h, hpol, vpol)
    return sp
