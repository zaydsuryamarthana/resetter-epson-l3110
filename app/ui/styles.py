"""
Modern Minimalist Technical Design System (QSS) for Epson Resetter.
Refined dark theme with high contrast, calm neutral surfaces, and purposeful accent colors.
"""

DARK_THEME = """
/* === BASE APPLICATION WINDOW === */
QMainWindow, QDialog {
    background-color: #0a0d14;
    color: #f0f6fc;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    font-size: 13px;
}

QWidget {
    color: #f0f6fc;
}

/* === SIDEBAR NAVIGATION === */
#sidebar {
    background-color: #0e131d;
    border-right: 1px solid #1f293d;
    min-width: 220px;
    max-width: 250px;
}

#nav_btn {
    text-align: left;
    padding: 11px 16px;
    border-radius: 8px;
    border: none;
    font-weight: 500;
    font-size: 13px;
    color: #8b949e;
    background-color: transparent;
    margin: 3px 10px;
}

#nav_btn:hover {
    background-color: #161f30;
    color: #f0f6fc;
}

#nav_btn:checked {
    background-color: #1f6feb;
    color: #ffffff;
    font-weight: 600;
}

/* === MODERN MINIMALIST CARDS === */
#card {
    background-color: #121824;
    border: 1px solid #1f293d;
    border-radius: 12px;
    padding: 18px 20px;
}

#card:hover {
    border-color: #2b3952;
}

#card_title {
    font-size: 15px;
    font-weight: 600;
    color: #f0f6fc;
    letter-spacing: -0.2px;
}

#card_subtitle {
    font-size: 12px;
    color: #8b949e;
    line-height: 1.4;
}

/* === BUTTONS === */
QPushButton {
    background-color: #161f30;
    color: #c9d1d9;
    border: 1px solid #233148;
    border-radius: 8px;
    padding: 9px 18px;
    font-weight: 500;
    font-size: 13px;
}

QPushButton:hover {
    background-color: #1c283e;
    border-color: #388bfd;
    color: #ffffff;
}

QPushButton:pressed {
    background-color: #121824;
}

QPushButton:disabled {
    background-color: #121824;
    color: #484f58;
    border-color: #192233;
}

QPushButton#primary_btn {
    background-color: #238636;
    color: #ffffff;
    border: 1px solid #2ea043;
    font-weight: 600;
}

QPushButton#primary_btn:hover {
    background-color: #2ea043;
    border-color: #3fb950;
}

QPushButton#primary_btn:pressed {
    background-color: #1e712e;
}

QPushButton#primary_btn:disabled {
    background-color: #132d1c;
    color: #484f58;
    border-color: #132d1c;
}

QPushButton#danger_btn {
    background-color: #da3633;
    color: #ffffff;
    border: 1px solid #f85149;
    font-weight: 600;
}

QPushButton#danger_btn:hover {
    background-color: #f85149;
    border-color: #ff7b72;
}

QPushButton#danger_btn:disabled {
    background-color: #381215;
    color: #6e7681;
    border-color: #381215;
}

QPushButton#warning_btn {
    background-color: #d29922;
    color: #0a0d14;
    border: 1px solid #e3b341;
    font-weight: 600;
}

QPushButton#warning_btn:hover {
    background-color: #e3b341;
}

QPushButton#accent_btn {
    background-color: #1f6feb;
    color: #ffffff;
    border: 1px solid #388bfd;
    font-weight: 600;
}

QPushButton#accent_btn:hover {
    background-color: #388bfd;
}

/* === PROGRESS BARS === */
QProgressBar {
    background-color: #0e131d;
    border: 1px solid #1f293d;
    border-radius: 8px;
    height: 12px;
    text-align: center;
    font-size: 10px;
    color: #8b949e;
}

QProgressBar::chunk {
    background-color: #238636;
    border-radius: 7px;
}

/* === TABLES === */
QTableWidget {
    background-color: #0e131d;
    border: 1px solid #1f293d;
    border-radius: 10px;
    gridline-color: #161f30;
    color: #c9d1d9;
    padding: 4px;
}

QHeaderView::section {
    background-color: #121824;
    color: #8b949e;
    padding: 10px;
    border: none;
    border-bottom: 1px solid #1f293d;
    font-weight: 600;
    font-size: 12px;
}

QTableWidget::item {
    padding: 8px;
    border-radius: 4px;
}

QTableWidget::item:selected {
    background-color: #1f6feb;
    color: #ffffff;
}

/* === STATUS BAR === */
QStatusBar {
    background-color: #0e131d;
    border-top: 1px solid #1f293d;
    color: #8b949e;
    padding: 4px 12px;
    font-size: 12px;
}

/* === SCROLLBARS === */
QScrollBar:vertical {
    background-color: #0a0d14;
    width: 8px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background-color: #233148;
    min-height: 24px;
    border-radius: 4px;
}

QScrollBar::handle:vertical:hover {
    background-color: #388bfd;
}

/* === INPUTS & CONTROLS === */
QCheckBox {
    spacing: 10px;
    color: #c9d1d9;
    font-size: 13px;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border: 1px solid #2b3952;
    border-radius: 5px;
    background-color: #121824;
}

QCheckBox::indicator:hover {
    border-color: #388bfd;
}

QCheckBox::indicator:checked {
    background-color: #1f6feb;
    border-color: #388bfd;
}

QLineEdit, QTextEdit, QSpinBox, QComboBox {
    background-color: #0e131d;
    border: 1px solid #1f293d;
    border-radius: 8px;
    padding: 8px 12px;
    color: #f0f6fc;
    font-size: 13px;
}

QLineEdit:focus, QTextEdit:focus, QSpinBox:focus, QComboBox:focus {
    border-color: #388bfd;
}

QComboBox::drop-down {
    border: none;
    width: 24px;
}

QComboBox QAbstractItemView {
    background-color: #121824;
    border: 1px solid #1f293d;
    border-radius: 8px;
    color: #f0f6fc;
    selection-background-color: #1f6feb;
}
"""
