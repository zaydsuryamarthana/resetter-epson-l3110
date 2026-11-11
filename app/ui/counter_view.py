"""
Waste Ink Pad Counter Inspection View.
"""

from app.ui.qt_compat import QtWidgets, QtCore, Signal, Slot
from app.ui.components.card_widget import CardWidget
from app.ui.components.gauge_bar import GaugeBar
from app.ui.components.status_badge import StatusBadge
from app.models.counter import WastePadRecord
from app.models.printer import PrinterInfo
from app.core.constants import PadHealthStatus


class CounterView(QtWidgets.QWidget):
    refresh_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header card with refresh button
        header_card = CardWidget("Waste Ink Counter Telemetry", "Firmware EEPROM ink absorber saturation meters")
        top_row = QtWidgets.QHBoxLayout()
        self.btn_refresh = QtWidgets.QPushButton("🔄  Read Counters")
        self.btn_refresh.setObjectName("primary_btn")
        self.btn_refresh.clicked.connect(self.refresh_requested.emit)
        top_row.addWidget(self.btn_refresh)

        self.last_checked_lbl = QtWidgets.QLabel("Last Checked: Not Available")
        self.last_checked_lbl.setStyleSheet("color: #8b949e; font-size: 12px;")
        top_row.addWidget(self.last_checked_lbl)

        top_row.addStretch()
        self.health_badge = StatusBadge("Unknown", "disconnected")
        top_row.addWidget(self.health_badge)
        header_card.add_layout(top_row)
        layout.addWidget(header_card)

        # Main Pad Gauge Card
        self.main_card = CardWidget("Main Waste Ink Pad Counter", "Primary ink collection pad for printhead flushing & maintenance")
        self.main_gauge = GaugeBar("Main Pad Saturation")
        self.main_card.add_widget(self.main_gauge)
        layout.addWidget(self.main_card)

        # Platen Pad Gauge Card
        self.platen_card = CardWidget("Platen (Borderless) Pad Counter", "Secondary absorber pad for borderless over-spray margins")
        self.platen_gauge = GaugeBar("Platen Pad Saturation")
        self.platen_card.add_widget(self.platen_gauge)
        layout.addWidget(self.platen_card)

        # Print Engine Page Statistics Card
        self.stats_card = CardWidget("Print Engine Production Statistics", "Lifetime operational counters from firmware status register")
        grid = QtWidgets.QGridLayout()
        grid.setSpacing(12)

        grid.addWidget(QtWidgets.QLabel("Total Pages Printed:"), 0, 0)
        self.lbl_total_pages = QtWidgets.QLabel("Unknown")
        self.lbl_total_pages.setStyleSheet("font-weight: 600; color: #f0f6fc;")
        grid.addWidget(self.lbl_total_pages, 0, 1)

        grid.addWidget(QtWidgets.QLabel("Color Pages:"), 0, 2)
        self.lbl_color_pages = QtWidgets.QLabel("Unknown")
        grid.addWidget(self.lbl_color_pages, 0, 3)

        grid.addWidget(QtWidgets.QLabel("Monochrome Pages:"), 1, 0)
        self.lbl_mono_pages = QtWidgets.QLabel("Unknown")
        grid.addWidget(self.lbl_mono_pages, 1, 1)

        grid.addWidget(QtWidgets.QLabel("Scan Count:"), 1, 2)
        self.lbl_scans = QtWidgets.QLabel("Unknown")
        grid.addWidget(self.lbl_scans, 1, 3)

        self.stats_card.add_layout(grid)
        layout.addWidget(self.stats_card)

        layout.addStretch()

    def update_counters(self, record: WastePadRecord):
        self.main_gauge.set_values(
            record.main_pad.current_points,
            record.main_pad.max_points,
            record.main_pad.percentage
        )
        self.platen_gauge.set_values(
            record.platen_pad.current_points,
            record.platen_pad.max_points,
            record.platen_pad.percentage
        )
        self.last_checked_lbl.setText(f"Last Checked: {record.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")

        if record.overall_status == PadHealthStatus.NORMAL:
            self.health_badge.set_state("Normal (<80%)", "normal")
        elif record.overall_status == PadHealthStatus.WARNING:
            self.health_badge.set_state("Warning (80-99%)", "warning")
        elif record.overall_status == PadHealthStatus.CRITICAL:
            self.health_badge.set_state("Service Required (100%)", "critical")
        else:
            self.health_badge.set_state("Unknown", "disconnected")

    def update_page_stats(self, info: PrinterInfo):
        if info.total_pages_printed is not None:
            self.lbl_total_pages.setText(f"{info.total_pages_printed:,}")
        if info.color_pages is not None:
            self.lbl_color_pages.setText(f"{info.color_pages:,}")
        if info.monochrome_pages is not None:
            self.lbl_mono_pages.setText(f"{info.monochrome_pages:,}")
        if info.scan_count is not None:
            self.lbl_scans.setText(f"{info.scan_count:,}")
