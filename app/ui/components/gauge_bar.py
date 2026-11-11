"""
Custom Gauge Progress Bar Component with threshold colors and telemetry values.
"""

from app.ui.qt_compat import QtWidgets, QtCore, QtGui, Qt


class GaugeBar(QtWidgets.QWidget):
    def __init__(self, title: str = "Waste Ink Pad", parent=None):
        super().__init__(parent)
        self.title = title
        self._value = 0
        self._max = 17151
        self._percentage = 0.0
        self._init_ui()

    def _init_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        # Top row: Title and Values
        top_row = QtWidgets.QHBoxLayout()
        self.lbl_title = QtWidgets.QLabel(self.title)
        self.lbl_title.setStyleSheet("font-weight: 600; font-size: 13px; color: #f0f6fc;")
        top_row.addWidget(self.lbl_title)

        top_row.addStretch()

        self.lbl_value = QtWidgets.QLabel("0 / 17,151 pts (0.0%)")
        self.lbl_value.setStyleSheet("font-size: 13px; font-weight: bold; color: #58a6ff;")
        top_row.addWidget(self.lbl_value)
        layout.addLayout(top_row)

        # Progress bar
        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(14)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #21262d;
                border: 1px solid #30363d;
                border-radius: 7px;
            }
            QProgressBar::chunk {
                background-color: #238636;
                border-radius: 6px;
            }
        """)
        layout.addWidget(self.progress_bar)

    def set_values(self, current_points: int, max_points: int = 17151, percentage: float = 0.0):
        self._value = current_points
        self._max = max_points
        if percentage > 0.0:
            self._percentage = percentage
        elif max_points > 0:
            self._percentage = round((current_points / max_points) * 100.0, 1)
        else:
            self._percentage = 0.0

        int_pct = int(min(100, max(0, self._percentage)))
        self.progress_bar.setValue(int_pct)
        self.lbl_value.setText(f"{self._value:,} / {self._max:,} pts ({self._percentage:.1f}%)")

        # Threshold coloring
        if self._percentage >= 100.0:
            color = "#da3633"  # Red
            val_color = "#f85149"
        elif self._percentage >= 80.0:
            color = "#d29922"  # Amber/Yellow
            val_color = "#e3b341"
        else:
            color = "#238636"  # Green
            val_color = "#3fb950"

        self.lbl_value.setStyleSheet(f"font-size: 13px; font-weight: bold; color: {val_color};")
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: #21262d;
                border: 1px solid #30363d;
                border-radius: 7px;
            }}
            QProgressBar::chunk {{
                background-color: {color};
                border-radius: 6px;
            }}
        """)
