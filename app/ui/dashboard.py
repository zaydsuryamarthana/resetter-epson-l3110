"""
Modern Minimalist Dashboard View for Epson Resetter.
Displays high-level printer telemetry, waste ink pad health, and quick maintenance launchpad.
"""

from typing import Optional
from app.ui.qt_compat import QtWidgets, QtCore, Signal, Slot
from app.ui.components.card_widget import CardWidget
from app.ui.components.status_badge import StatusBadge
from app.ui.components.gauge_bar import GaugeBar
from app.models.printer import PrinterInfo
from app.models.counter import WastePadRecord
from app.core.constants import ConnectionStatus, PadHealthStatus


class DashboardView(QtWidgets.QWidget):
    navigate_to = Signal(int)  # Emit page index to switch tabs
    request_refresh_counters = Signal()
    request_run_diagnostics = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(20)

        # Header Title
        hdr_layout = QtWidgets.QVBoxLayout()
        hdr_layout.setSpacing(4)
        title_lbl = QtWidgets.QLabel("System Overview")
        title_lbl.setStyleSheet("font-size: 20px; font-weight: 700; color: #f0f6fc; letter-spacing: -0.3px;")
        desc_lbl = QtWidgets.QLabel("Status koneksi USB, kesehatan bantalan pembuangan tinta, dan pintasan utilitas.")
        desc_lbl.setStyleSheet("font-size: 13px; color: #8b949e;")
        hdr_layout.addWidget(title_lbl)
        hdr_layout.addWidget(desc_lbl)
        layout.addLayout(hdr_layout)

        # 1. Hero Device Status Card
        self.device_card = CardWidget("Koneksi & Identitas Printer", "Telemetri perangkat keras melalui bus USB")
        dev_layout = QtWidgets.QHBoxLayout()
        dev_layout.setSpacing(24)

        grid = QtWidgets.QGridLayout()
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(10)

        # Row 0
        lbl_m = QtWidgets.QLabel("Model Perangkat:")
        lbl_m.setStyleSheet("color: #8b949e; font-size: 12px;")
        grid.addWidget(lbl_m, 0, 0)
        self.lbl_model = QtWidgets.QLabel("Epson EcoTank L3110")
        self.lbl_model.setStyleSheet("font-weight: 600; color: #f0f6fc; font-size: 13px;")
        grid.addWidget(self.lbl_model, 0, 1)

        lbl_s = QtWidgets.QLabel("Nomor Seri (S/N):")
        lbl_s.setStyleSheet("color: #8b949e; font-size: 12px;")
        grid.addWidget(lbl_s, 0, 2)
        self.lbl_serial = QtWidgets.QLabel("Mencari perangkat...")
        self.lbl_serial.setStyleSheet("font-family: monospace; color: #58a6ff; font-weight: 600;")
        grid.addWidget(self.lbl_serial, 0, 3)

        # Row 1
        lbl_h = QtWidgets.QLabel("USB Hardware ID:")
        lbl_h.setStyleSheet("color: #8b949e; font-size: 12px;")
        grid.addWidget(lbl_h, 1, 0)
        self.lbl_hw_id = QtWidgets.QLabel("VID: 0x04B8 | PID: 0x1142")
        self.lbl_hw_id.setStyleSheet("color: #c9d1d9; font-size: 13px;")
        grid.addWidget(self.lbl_hw_id, 1, 1)

        lbl_fw = QtWidgets.QLabel("Versi Firmware:")
        lbl_fw.setStyleSheet("color: #8b949e; font-size: 12px;")
        grid.addWidget(lbl_fw, 1, 2)
        self.lbl_firmware = QtWidgets.QLabel("Unknown")
        self.lbl_firmware.setStyleSheet("color: #c9d1d9; font-size: 13px;")
        grid.addWidget(self.lbl_firmware, 1, 3)

        # Row 2: Page Counts
        lbl_pages = QtWidgets.QLabel("Total Cetak:")
        lbl_pages.setStyleSheet("color: #8b949e; font-size: 12px;")
        grid.addWidget(lbl_pages, 2, 0)
        self.lbl_page_count = QtWidgets.QLabel("- lembar")
        self.lbl_page_count.setStyleSheet("color: #c9d1d9; font-size: 13px;")
        grid.addWidget(self.lbl_page_count, 2, 1)

        lbl_scanner = QtWidgets.QLabel("Total Scan:")
        lbl_scanner.setStyleSheet("color: #8b949e; font-size: 12px;")
        grid.addWidget(lbl_scanner, 2, 2)
        self.lbl_scan_count = QtWidgets.QLabel("- kali")
        self.lbl_scan_count.setStyleSheet("color: #c9d1d9; font-size: 13px;")
        grid.addWidget(self.lbl_scan_count, 2, 3)

        dev_layout.addLayout(grid, 1)

        # Status badge container
        badge_layout = QtWidgets.QVBoxLayout()
        badge_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.status_badge = StatusBadge("Terputus", "disconnected")
        badge_layout.addWidget(self.status_badge)
        dev_layout.addLayout(badge_layout)

        self.device_card.add_layout(dev_layout)
        layout.addWidget(self.device_card)

        # 2. Dual Column: Counter Summary & Quick Actions
        mid_layout = QtWidgets.QHBoxLayout()
        mid_layout.setSpacing(20)

        # Waste Ink Counter Summary
        self.counter_card = CardWidget("Kapasitas Waste Ink Pad", "Tingkat kejenuhan bantalan spon penyerap tinta buangan")
        self.main_gauge = GaugeBar("Main Waste Ink Pad")
        self.platen_gauge = GaugeBar("Platen (Borderless) Pad")
        self.counter_card.add_widget(self.main_gauge)
        self.counter_card.add_widget(self.platen_gauge)
        mid_layout.addWidget(self.counter_card, 3)

        # Quick Actions Card
        self.action_card = CardWidget("Aksi Cepat", "Pintasan operasional umum")
        act_layout = QtWidgets.QVBoxLayout()
        act_layout.setSpacing(10)

        self.btn_check_counters = QtWidgets.QPushButton("🔄  Baca Ulang Counter")
        self.btn_check_counters.setObjectName("primary_btn")
        self.btn_check_counters.clicked.connect(self.request_refresh_counters.emit)
        act_layout.addWidget(self.btn_check_counters)

        self.btn_run_diag = QtWidgets.QPushButton("🩺  Diagnostik USB & Protokol")
        self.btn_run_diag.clicked.connect(self.request_run_diagnostics.emit)
        act_layout.addWidget(self.btn_run_diag)

        self.btn_open_maint = QtWidgets.QPushButton("🛠️  Alat Pemeliharaan Head")
        self.btn_open_maint.clicked.connect(lambda: self.navigate_to.emit(4))  # Tab 4: Maintenance
        act_layout.addWidget(self.btn_open_maint)

        self.btn_open_reset = QtWidgets.QPushButton("🛡️  Buka Utilitas Reset")
        self.btn_open_reset.clicked.connect(lambda: self.navigate_to.emit(3))  # Tab 3: Reset
        act_layout.addWidget(self.btn_open_reset)

        act_layout.addStretch()
        self.action_card.add_layout(act_layout)
        mid_layout.addWidget(self.action_card, 2)

        layout.addLayout(mid_layout)
        layout.addStretch()

    def update_printer_info(self, info: PrinterInfo):
        if info.connection_status == ConnectionStatus.CONNECTED:
            self.status_badge.set_state("Terhubung", "connected")
            self.lbl_serial.setText(info.serial_number or "Tidak Terdeteksi")
            self.lbl_firmware.setText(info.firmware_version or "Unknown")
            if info.total_pages_printed is not None:
                self.lbl_page_count.setText(f"{info.total_pages_printed:,} lembar")
            if info.scan_count is not None:
                self.lbl_scan_count.setText(f"{info.scan_count:,} kali")
        elif info.connection_status == ConnectionStatus.CONNECTING:
            self.status_badge.set_state("Menghubungkan", "connecting")
            self.lbl_serial.setText("Membaca...")
        else:
            self.status_badge.set_state("Terputus", "disconnected")
            self.lbl_serial.setText("Tidak Terdeteksi")
            self.lbl_firmware.setText("Unknown")
            self.lbl_page_count.setText("- lembar")
            self.lbl_scan_count.setText("- kali")

    def update_counters(self, record: WastePadRecord):
        self.main_gauge.set_values(
            record.main_pad.current_points,
            record.main_pad.max_points,
            record.main_pad.percentage,
        )
        self.platen_gauge.set_values(
            record.platen_pad.current_points,
            record.platen_pad.max_points,
            record.platen_pad.percentage,
        )
