"""
Alert Notification Box Component.
"""

from app.ui.qt_compat import QtWidgets, QtCore


class AlertBox(QtWidgets.QFrame):
    def __init__(self, message: str, level: str = "warning", parent=None):
        super().__init__(parent)
        self.level = level.lower()
        self._init_ui(message)

    def _init_ui(self, message: str):
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(10)

        # Style based on level
        if self.level == "danger":
            bg = "#491717"
            border = "#f85149"
            color = "#ff7b72"
            icon_char = "⚠️"
        elif self.level == "warning":
            bg = "#4d3800"
            border = "#bb8009"
            color = "#e3b341"
            icon_char = "⚠️"
        elif self.level == "info":
            bg = "#1f2937"
            border = "#38bdf8"
            color = "#7dd3fc"
            icon_char = "ℹ️"
        else:
            bg = "#1b4728"
            border = "#2ea043"
            color = "#3fb950"
            icon_char = "✓"

        self.setStyleSheet(f"""
            QFrame {{
                background-color: {bg};
                border: 1px solid {border};
                border-radius: 6px;
            }}
            QLabel {{
                color: {color};
                font-size: 13px;
                background-color: transparent;
                border: none;
            }}
        """)

        icon_lbl = QtWidgets.QLabel(icon_char)
        icon_lbl.setStyleSheet("font-size: 16px;")
        layout.addWidget(icon_lbl)

        self.msg_lbl = QtWidgets.QLabel(message)
        self.msg_lbl.setWordWrap(True)
        layout.addWidget(self.msg_lbl, 1)

    def set_message(self, message: str):
        self.msg_lbl.setText(message)
