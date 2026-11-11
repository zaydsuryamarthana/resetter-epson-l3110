"""
Status Badge Chip Component.
"""

from app.ui.qt_compat import QtWidgets, QtCore


class StatusBadge(QtWidgets.QLabel):
    def __init__(self, text: str = "Disconnected", state: str = "disconnected", parent=None):
        super().__init__(parent)
        self.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.setFixedHeight(24)
        self.set_state(text, state)

    def set_state(self, text: str, state: str):
        self.setText(text)
        state = state.lower()
        if state in ("connected", "normal", "success", "verified"):
            bg = "#1b4728"
            border = "#2ea043"
            color = "#3fb950"
        elif state in ("warning", "connecting", "busy"):
            bg = "#4d3800"
            border = "#bb8009"
            color = "#e3b341"
        elif state in ("critical", "disconnected", "error", "failed"):
            bg = "#491717"
            border = "#f85149"
            color = "#ff7b72"
        else:
            bg = "#21262d"
            border = "#30363d"
            color = "#8b949e"

        self.setStyleSheet(f"""
            QLabel {{
                background-color: {bg};
                color: {color};
                border: 1px solid {border};
                border-radius: 12px;
                padding: 2px 10px;
                font-weight: 600;
                font-size: 11px;
            }}
        """)
