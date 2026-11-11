"""
Safety-Gated Reset Utility View.
"""

from app.ui.qt_compat import QtWidgets, QtCore, Signal, Slot
from app.ui.components.card_widget import CardWidget
from app.ui.components.alert_box import AlertBox
from app.ui.components.status_badge import StatusBadge
from app.core.constants import MaintenanceOperation, OperationResult
from app.models.maintenance import MaintenanceRecord


class ResetView(QtWidgets.QWidget):
    execute_reset_requested = Signal(str, bool)  # operation_type, sponge_confirmed

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # 1. Critical Safety Warning Banner
        warning_msg = (
            "PERINGATAN KESELAMATAN: Reset counter firmware hanya mereset pencatatan digital "
            "dan TIDAK membersihkan tinta pada busa penyerap limbah secara fisik. "
            "Pastikan Anda telah memeriksa, mencuci, atau mengganti busa limbah tinta "
            "sebelum melakukan reset agar tinta tidak meluap ke sirkuit printer."
        )
        self.alert_box = AlertBox(warning_msg, level="danger")
        layout.addWidget(self.alert_box)

        # 2. Reset Operation Configuration Card
        self.config_card = CardWidget("Counter Reset Configuration", "Select target counter and confirm safety gates")

        opt_layout = QtWidgets.QVBoxLayout()
        opt_layout.setSpacing(12)

        # Target selection radio buttons
        opt_layout.addWidget(QtWidgets.QLabel("Select Target Counter to Reset:"))
        self.radio_main = QtWidgets.QRadioButton("Reset Main Waste Ink Pad Counter (Recommended)")
        self.radio_main.setChecked(True)
        self.radio_platen = QtWidgets.QRadioButton("Reset Platen (Borderless) Pad Counter")
        self.radio_all = QtWidgets.QRadioButton("Reset All Waste Ink Pad Counters")
        opt_layout.addWidget(self.radio_main)
        opt_layout.addWidget(self.radio_platen)
        opt_layout.addWidget(self.radio_all)

        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        line.setStyleSheet("color: #21262d;")
        opt_layout.addWidget(line)

        # Mandatory Safety Gate Checkbox
        self.chk_confirm_sponge = QtWidgets.QCheckBox(
            "Saya menyatakan telah memeriksa / mengganti busa limbah tinta fisik printer ini."
        )
        self.chk_confirm_sponge.setStyleSheet("font-weight: 600; color: #f0f6fc;")
        self.chk_confirm_sponge.stateChanged.connect(self._on_checkbox_changed)
        opt_layout.addWidget(self.chk_confirm_sponge)

        lbl_hint = QtWidgets.QLabel(
            "💡 Prosedur Firmware: Setelah tombol reset ditekan dan diterima printer, printer akan masuk status 'Reboot Pending' "
            "(kedua lampu indikator menyala bersamaan). Anda HARUS mematikan printer via tombol Power, tunggu 5 detik, dan "
            "menghidupkannya kembali agar firmware memuat nilai counter 0 yang baru."
        )
        lbl_hint.setWordWrap(True)
        lbl_hint.setStyleSheet("color: #8b949e; font-size: 11px; padding: 4px 0px;")
        opt_layout.addWidget(lbl_hint)

        # Action Button Row
        btn_row = QtWidgets.QHBoxLayout()
        self.btn_reset = QtWidgets.QPushButton("🛡️  Execute Counter Reset & Verify")
        self.btn_reset.setObjectName("danger_btn")
        self.btn_reset.setEnabled(False)  # Disabled until user confirms
        self.btn_reset.clicked.connect(self._on_reset_clicked)
        btn_row.addWidget(self.btn_reset)

        btn_row.addStretch()
        self.reset_status_badge = StatusBadge("Ready", "normal")
        btn_row.addWidget(self.reset_status_badge)
        opt_layout.addLayout(btn_row)

        self.config_card.add_layout(opt_layout)
        layout.addWidget(self.config_card)

        # 3. Progress and Verification Card
        self.verify_card = CardWidget("Execution & Verification Audit", "Real-time verification log")
        verify_layout = QtWidgets.QVBoxLayout()
        verify_layout.setSpacing(10)

        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.setTextVisible(False)
        verify_layout.addWidget(self.progress_bar)

        self.txt_log = QtWidgets.QTextEdit()
        self.txt_log.setReadOnly(True)
        self.txt_log.setPlaceholderText("Operation logs and verification details will appear here...")
        self.txt_log.setMinimumHeight(100)
        verify_layout.addWidget(self.txt_log)

        self.verify_card.add_layout(verify_layout)
        layout.addWidget(self.verify_card)

        layout.addStretch()

    def _on_checkbox_changed(self):
        self.btn_reset.setEnabled(self.chk_confirm_sponge.isChecked())

    def _on_reset_clicked(self):
        # Prompt explicit double confirmation dialog
        reply = QtWidgets.QMessageBox.warning(
            self,
            "Konfirmasi Eksekusi Reset",
            "Apakah Anda yakin ingin menjalankan prosedur reset counter firmware pada printer Epson L3110 ini?\n\n"
            "Aplikasi akan membaca nilai awal, mengirimkan perintah reset, dan melakukan verifikasi pembacaan ulang.",
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.Cancel,
            QtWidgets.QMessageBox.StandardButton.Cancel
        )

        if reply != QtWidgets.QMessageBox.StandardButton.Yes:
            return

        op = MaintenanceOperation.RESET_MAIN_PAD.value
        if self.radio_platen.isChecked():
            op = MaintenanceOperation.RESET_PLATEN_PAD.value
        elif self.radio_all.isChecked():
            op = MaintenanceOperation.RESET_ALL.value

        self.btn_reset.setEnabled(False)
        self.reset_status_badge.set_state("Executing...", "connecting")
        self.progress_bar.setValue(10)
        self.txt_log.setText("Initiating reset protocol...\n")
        self.execute_reset_requested.emit(op, self.chk_confirm_sponge.isChecked())

    def update_progress(self, message: str, percent: int):
        self.progress_bar.setValue(percent)
        self.txt_log.append(f"[{percent}%] {message}")

    def display_result(self, record: MaintenanceRecord):
        self.btn_reset.setEnabled(self.chk_confirm_sponge.isChecked())
        if record.status == OperationResult.VERIFIED:
            self.reset_status_badge.set_state("Reset Verified", "verified")
            self.progress_bar.setValue(100)
            self.txt_log.append("\n✅ SUCCESS: Counter reset verified by firmware re-read!")
            self.txt_log.append(f"Pre-reset points: {record.pre_counter_value:,} pts")
            self.txt_log.append(f"Post-reset points: {record.post_counter_value:,} pts")
            QtWidgets.QMessageBox.information(
                self,
                "Reset Berhasil",
                f"Prosedur reset berhasil dan terverifikasi!\nNilai counter berkurang dari {record.pre_counter_value:,} pts menjadi {record.post_counter_value:,} pts."
            )
        else:
            self.reset_status_badge.set_state("Failed", "failed")
            self.txt_log.append(f"\n❌ FAILED: {record.error_message or 'Verification failed'}")
            QtWidgets.QMessageBox.critical(
                self,
                "Reset Gagal",
                f"Prosedur reset tidak berhasil diverifikasi:\n{record.error_message or 'Nilai counter tidak berkurang.'}"
            )
