"""
Printer Diagnostics View.
"""

from app.ui.qt_compat import QtWidgets, QtCore, Signal, Slot
from app.ui.components.card_widget import CardWidget
from app.ui.components.status_badge import StatusBadge
from app.models.maintenance import DiagnosticResult


class DiagnosticsView(QtWidgets.QWidget):
    run_diagnostics_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header Card
        header_card = CardWidget("Printer Diagnostics", "Automated hardware, communication, and protocol verification")
        btn_layout = QtWidgets.QHBoxLayout()
        self.btn_run = QtWidgets.QPushButton("🩺  Run Full Diagnostics")
        self.btn_run.setObjectName("primary_btn")
        self.btn_run.clicked.connect(self.run_diagnostics_requested.emit)
        btn_layout.addWidget(self.btn_run)

        self.overall_badge = StatusBadge("Pending Test", "disconnected")
        btn_layout.addStretch()
        btn_layout.addWidget(self.overall_badge)
        header_card.add_layout(btn_layout)
        layout.addWidget(header_card)

        # Tests Checklist Card
        self.checklist_card = CardWidget("Diagnostic Test Suite")
        list_layout = QtWidgets.QVBoxLayout()
        list_layout.setSpacing(10)

        self.items = [
            ("USB Physical Connection", "Detect printer hardware on USB controller"),
            ("Device Model Identification", "Verify Vendor ID 0x04B8 and Product ID 0x1142"),
            ("IEEE 1284.4 (Dot4) Protocol Handshake", "Verify multiplexed session negotiation"),
            ("EPSON-CTRL Channel Activation", "Verify Socket ID 2 dynamic credit allocation"),
            ("Waste Counter Telemetry Readability", "Verify 73-byte counter telemetry decoding"),
        ]

        self.status_labels = []
        for title, desc in self.items:
            row = QtWidgets.QHBoxLayout()
            v_box = QtWidgets.QVBoxLayout()
            v_box.setSpacing(2)
            lbl_t = QtWidgets.QLabel(title)
            lbl_t.setStyleSheet("font-weight: 600; color: #f0f6fc;")
            lbl_d = QtWidgets.QLabel(desc)
            lbl_d.setStyleSheet("color: #8b949e; font-size: 11px;")
            v_box.addWidget(lbl_t)
            v_box.addWidget(lbl_d)
            row.addLayout(v_box, 1)

            lbl_stat = QtWidgets.QLabel("⚪ Pending")
            lbl_stat.setStyleSheet("font-weight: 600; color: #8b949e;")
            row.addWidget(lbl_stat)
            self.status_labels.append(lbl_stat)

            list_layout.addLayout(row)
            line = QtWidgets.QFrame()
            line.setFrameShape(QtWidgets.QFrame.Shape.HLine)
            line.setStyleSheet("color: #21262d;")
            list_layout.addWidget(line)

        self.checklist_card.add_layout(list_layout)
        layout.addWidget(self.checklist_card)

        # Technical Output Box
        self.output_card = CardWidget("Technical Diagnostic Output", "Raw protocol responses and register inspection")
        self.txt_output = QtWidgets.QTextEdit()
        self.txt_output.setReadOnly(True)
        self.txt_output.setPlaceholderText("Diagnostic output will appear here after running tests...")
        self.txt_output.setMinimumHeight(120)
        self.output_card.add_widget(self.txt_output)
        layout.addWidget(self.output_card)

        layout.addStretch()

    def set_running(self, running: bool):
        self.btn_run.setEnabled(not running)
        if running:
            self.overall_badge.set_state("Running...", "connecting")
            for lbl in self.status_labels:
                lbl.setText("⏳ Testing...")
                lbl.setStyleSheet("font-weight: 600; color: #e3b341;")
            self.txt_output.setText("Starting hardware diagnostics...\n")

    def display_results(self, res: DiagnosticResult):
        self.set_running(False)
        checks = [
            res.usb_connection_ok,
            res.device_id_match,
            res.d4_handshake_ok,
            res.ctrl_channel_ok,
            res.counter_readable,
        ]

        for i, passed in enumerate(checks):
            lbl = self.status_labels[i]
            if passed:
                lbl.setText("✓ Passed")
                lbl.setStyleSheet("font-weight: 600; color: #3fb950;")
            else:
                lbl.setText("✗ Failed")
                lbl.setStyleSheet("font-weight: 600; color: #f85149;")

        if res.all_passed:
            self.overall_badge.set_state("All Tests Passed", "success")
        else:
            self.overall_badge.set_state("Issues Detected", "critical")

        # Format details
        lines = [
            f"Timestamp: {res.timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
            f"Overall Status: {'PASSED' if res.all_passed else 'FAILED'}",
            "Details:",
        ]
        for k, v in res.details.items():
            lines.append(f"  • {k}: {v}")
        self.txt_output.setText("\n".join(lines))
