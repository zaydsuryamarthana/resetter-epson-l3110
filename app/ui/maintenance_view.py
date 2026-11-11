"""
Modern Minimalist Universal Maintenance View for Epson Inkjet Printers.
Enables Nozzle Check, Head Cleaning, Power Cleaning, and Print Head Alignment.
"""

from typing import Optional, Dict
from app.ui.qt_compat import QtWidgets, QtCore, Signal, Slot
from app.ui.components.card_widget import CardWidget
from app.ui.components.alert_box import AlertBox
from app.ui.components.status_badge import StatusBadge
from app.models.maintenance import MaintenanceRecord
from app.core.constants import OperationResult, POWER_CLEANING_MAX_PAD_PERCENT


class MaintenanceView(QtWidgets.QWidget):
    nozzle_check_requested = Signal()
    head_cleaning_requested = Signal()
    power_cleaning_requested = Signal(bool)  # confirmed_ink_level
    alignment_sheet_requested = Signal()
    apply_alignment_requested = Signal(dict)  # {1: val1, 2: val2, ...}

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(28, 24, 28, 24)
        main_layout.setSpacing(20)

        # Header Title
        hdr_layout = QtWidgets.QVBoxLayout()
        hdr_layout.setSpacing(4)
        title_lbl = QtWidgets.QLabel("🛠️ Universal Printer Maintenance")
        title_lbl.setStyleSheet("font-size: 20px; font-weight: 700; color: #f0f6fc; letter-spacing: -0.3px;")
        desc_lbl = QtWidgets.QLabel(
            "Alat pemeliharaan mandiri untuk menjaga kualitas cetak, mengatasi tinta tersumbat, dan kalibrasi print head."
        )
        desc_lbl.setStyleSheet("font-size: 13px; color: #8b949e;")
        hdr_layout.addWidget(title_lbl)
        hdr_layout.addWidget(desc_lbl)
        main_layout.addLayout(hdr_layout)

        # Scrollable container for cards
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent;")

        container = QtWidgets.QWidget()
        container_layout = QtWidgets.QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 8, 0)
        container_layout.setSpacing(16)

        # -------------------------------------------------------------
        # 1. Nozzle Check Card
        # -------------------------------------------------------------
        self.card_nozzle = CardWidget("1. Nozzle Check (Pemeriksaan Nozel)", "Deteksi kondisi lubang nozel print head")
        nozzle_layout = QtWidgets.QHBoxLayout()
        nozzle_layout.setSpacing(16)

        nozzle_info = QtWidgets.QVBoxLayout()
        nozzle_desc = QtWidgets.QLabel(
            "Mencetak pola uji nozel untuk memastikan seluruh nozel hitam dan warna (Cyan, Magenta, Yellow) "
            "mengeluarkan tinta dengan sempurna tanpa putus atau bergaris."
        )
        nozzle_desc.setWordWrap(True)
        nozzle_desc.setStyleSheet("color: #c9d1d9; font-size: 13px; line-height: 1.4;")
        nozzle_info.addWidget(nozzle_desc)

        # Mini visual guide
        guide_box = QtWidgets.QHBoxLayout()
        guide_box.setSpacing(12)
        lbl_good = QtWidgets.QLabel("✓ Pola Bagus: Garis solid bersambung")
        lbl_good.setStyleSheet("color: #3fb950; font-size: 12px; font-weight: 500;")
        lbl_bad = QtWidgets.QLabel("⚠️ Pola Tersumbat: Garis putus-putus/kosong")
        lbl_bad.setStyleSheet("color: #e3b341; font-size: 12px; font-weight: 500;")
        guide_box.addWidget(lbl_good)
        guide_box.addWidget(lbl_bad)
        guide_box.addStretch()
        nozzle_info.addLayout(guide_box)

        nozzle_layout.addLayout(nozzle_info, 3)

        self.btn_nozzle = QtWidgets.QPushButton("📄 Cetak Pola Uji")
        self.btn_nozzle.setObjectName("primary_btn")
        self.btn_nozzle.setFixedWidth(160)
        self.btn_nozzle.clicked.connect(self.nozzle_check_requested.emit)
        nozzle_layout.addWidget(self.btn_nozzle, 0, QtCore.Qt.AlignmentFlag.AlignVCenter)

        self.card_nozzle.add_layout(nozzle_layout)
        container_layout.addWidget(self.card_nozzle)

        # -------------------------------------------------------------
        # 2. Head Cleaning Card
        # -------------------------------------------------------------
        self.card_cleaning = CardWidget("2. Head Cleaning (Pembersihan Standar)", "Pembersihan pompa hisap nozel otomatis")
        clean_layout = QtWidgets.QHBoxLayout()
        clean_layout.setSpacing(16)

        clean_info = QtWidgets.QVBoxLayout()
        clean_desc = QtWidgets.QLabel(
            "Melakukan siklus pembersihan print head menggunakan hisapan pompa tinta standar. "
            "Gunakan jika hasil Nozzle Check menunjukkan garis putus-putus. "
            "Proses berlangsung sekitar 1-2 menit. Jangan matikan printer!"
        )
        clean_desc.setWordWrap(True)
        clean_desc.setStyleSheet("color: #c9d1d9; font-size: 13px; line-height: 1.4;")
        clean_info.addWidget(clean_desc)
        clean_layout.addLayout(clean_info, 3)

        self.btn_clean = QtWidgets.QPushButton("🧼 Head Cleaning")
        self.btn_clean.setObjectName("accent_btn")
        self.btn_clean.setFixedWidth(160)
        self.btn_clean.clicked.connect(self.head_cleaning_requested.emit)
        clean_layout.addWidget(self.btn_clean, 0, QtCore.Qt.AlignmentFlag.AlignVCenter)

        self.card_cleaning.add_layout(clean_layout)
        container_layout.addWidget(self.card_cleaning)

        # -------------------------------------------------------------
        # 3. Power Cleaning (Ink Flush) Card
        # -------------------------------------------------------------
        self.card_power = CardWidget("3. Power Cleaning (Pembersihan Bertenaga / Ink Flush)", "Pembersihan intensif untuk nozel macet parah")
        power_layout = QtWidgets.QVBoxLayout()
        power_layout.setSpacing(12)

        power_desc = QtWidgets.QLabel(
            "Power Cleaning mengalirkan tinta dengan tekanan tinggi melalui tabung tinta untuk mengatasi "
            "nozel tersumbat membandel atau udara yang terperangkap dalam selang head cetak."
        )
        power_desc.setWordWrap(True)
        power_desc.setStyleSheet("color: #c9d1d9; font-size: 13px; line-height: 1.4;")
        power_layout.addWidget(power_desc)

        # Safety Alert Box
        alert = AlertBox(
            "PERHATIAN: Power Cleaning mengonsumsi banyak tinta (~20-30% tangki) dan menghasilkan limbah tinta cair "
            "dalam jumlah signifikan ke bantalan spon (Waste Ink Pad). Fitur ini otomatis diblokir jika bantalan "
            f"limbah sudah di atas {POWER_CLEANING_MAX_PAD_PERCENT:.0f}%.",
            level="warning"
        )
        power_layout.addWidget(alert)

        # Checkbox for confirmation
        act_row = QtWidgets.QHBoxLayout()
        self.chk_ink_level = QtWidgets.QCheckBox(
            "Saya menyatakan bahwa semua tangki tinta fisik terisi minimal 30% dan siap melakukan Power Cleaning."
        )
        self.chk_ink_level.setStyleSheet("color: #e3b341; font-weight: 500;")
        act_row.addWidget(self.chk_ink_level, 1)

        self.btn_power_clean = QtWidgets.QPushButton("⚡ Power Cleaning")
        self.btn_power_clean.setObjectName("danger_btn")
        self.btn_power_clean.setFixedWidth(160)
        self.btn_power_clean.clicked.connect(self._on_power_cleaning_clicked)
        act_row.addWidget(self.btn_power_clean, 0)

        power_layout.addLayout(act_row)
        self.card_power.add_layout(power_layout)
        container_layout.addWidget(self.card_power)

        # -------------------------------------------------------------
        # 4. Print Head Alignment Card
        # -------------------------------------------------------------
        self.card_align = CardWidget("4. Print Head Alignment (Penyelarasan Head)", "Kalibrasi posisi cetak horizontal dua arah (bidirectional)")
        align_layout = QtWidgets.QVBoxLayout()
        align_layout.setSpacing(12)

        align_desc = QtWidgets.QLabel(
            "Jika hasil cetakan teks berbayang, vertikal tidak lurus, atau cetakan tabel bergeser, "
            "cetak lembar evaluasi alignment dan pilih nomor pola yang paling lurus dan solid tanpa celah."
        )
        align_desc.setWordWrap(True)
        align_desc.setStyleSheet("color: #c9d1d9; font-size: 13px; line-height: 1.4;")
        align_layout.addWidget(align_desc)

        # Step controls
        steps_row = QtWidgets.QHBoxLayout()
        steps_row.setSpacing(16)

        # Print sheet button
        self.btn_align_sheet = QtWidgets.QPushButton("📑 Cetak Lembar Uji")
        self.btn_align_sheet.setFixedWidth(160)
        self.btn_align_sheet.clicked.connect(self.alignment_sheet_requested.emit)
        steps_row.addWidget(self.btn_align_sheet)

        # Alignment Spinboxes for Pattern 1 to 4
        spin_layout = QtWidgets.QHBoxLayout()
        spin_layout.setSpacing(12)
        self.align_spinners: Dict[int, QtWidgets.QSpinBox] = {}

        for p_idx in range(1, 5):
            box = QtWidgets.QHBoxLayout()
            box.setSpacing(6)
            lbl = QtWidgets.QLabel(f"Pola #{p_idx}:")
            lbl.setStyleSheet("color: #8b949e; font-size: 12px;")
            spin = QtWidgets.QSpinBox()
            spin.setRange(1, 9)
            spin.setValue(5)  # Default center value
            spin.setFixedWidth(54)
            self.align_spinners[p_idx] = spin
            box.addWidget(lbl)
            box.addWidget(spin)
            spin_layout.addLayout(box)

        steps_row.addLayout(spin_layout)
        steps_row.addStretch()

        self.btn_apply_align = QtWidgets.QPushButton("💾 Simpan Kalibrasi")
        self.btn_apply_align.setFixedWidth(150)
        self.btn_apply_align.clicked.connect(self._on_apply_alignment_clicked)
        steps_row.addWidget(self.btn_apply_align)

        align_layout.addLayout(steps_row)
        self.card_align.add_layout(align_layout)
        container_layout.addWidget(self.card_align)

        scroll.setWidget(container)
        main_layout.addWidget(scroll, 1)

        # -------------------------------------------------------------
        # Live Progress & Status Footer
        # -------------------------------------------------------------
        self.footer_frame = QtWidgets.QFrame()
        self.footer_frame.setStyleSheet("""
            QFrame {
                background-color: #0e131d;
                border: 1px solid #1f293d;
                border-radius: 10px;
                padding: 6px 12px;
            }
        """)
        footer_layout = QtWidgets.QVBoxLayout(self.footer_frame)
        footer_layout.setSpacing(6)

        status_row = QtWidgets.QHBoxLayout()
        self.lbl_op_status = QtWidgets.QLabel("Status: Siap.")
        self.lbl_op_status.setStyleSheet("font-size: 13px; color: #8b949e; border: none; background: transparent;")
        self.badge_maint = StatusBadge("Idle", "normal")
        status_row.addWidget(self.lbl_op_status, 1)
        status_row.addWidget(self.badge_maint)
        footer_layout.addLayout(status_row)

        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.setTextVisible(False)
        footer_layout.addWidget(self.progress_bar)

        main_layout.addWidget(self.footer_frame)

    def _on_power_cleaning_clicked(self):
        confirmed = self.chk_ink_level.isChecked()
        if not confirmed:
            QtWidgets.QMessageBox.warning(
                self,
                "Konfirmasi Diperlukan",
                "Sebelum menjalankan Power Cleaning, Anda wajib mencentang persetujuan bahwa tangki tinta "
                "fisik terisi minimal 30%.\n\n"
                "Flushing saat tangki tinta kosong dapat menarik udara ke dalam print head dan merusak piezo elektrik.",
                QtWidgets.QMessageBox.StandardButton.Ok
            )
            return

        # Explicit confirmation dialog
        ans = QtWidgets.QMessageBox.question(
            self,
            "Konfirmasi Power Cleaning",
            "Power Cleaning akan mengonsumsi banyak tinta dan memerlukan waktu sekitar 7-10 menit.\n\n"
            "Pastikan:\n"
            "1. Printer terhubung langsung ke listrik stabil.\n"
            "2. Jangan matikan printer atau cabut kabel USB selama proses berlangsung.\n\n"
            "Apakah Anda yakin ingin memulai proses Power Cleaning sekarang?",
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No,
            QtWidgets.QMessageBox.StandardButton.No
        )
        if ans == QtWidgets.QMessageBox.StandardButton.Yes:
            self.power_cleaning_requested.emit(True)

    def _on_apply_alignment_clicked(self):
        offsets = {p: spin.value() for p, spin in self.align_spinners.items()}
        self.apply_alignment_requested.emit(offsets)

    def set_operation_running(self, running: bool, title: str = ""):
        self.btn_nozzle.setEnabled(not running)
        self.btn_clean.setEnabled(not running)
        self.btn_power_clean.setEnabled(not running)
        self.btn_align_sheet.setEnabled(not running)
        self.btn_apply_align.setEnabled(not running)

        if running:
            self.badge_maint.set_state("Running", "warning")
            self.lbl_op_status.setText(f"Sedang memproses: {title}...")
            self.progress_bar.setValue(20)
        else:
            self.badge_maint.set_state("Ready", "normal")
            self.progress_bar.setValue(0)

    def update_progress(self, message: str, percentage: int):
        self.lbl_op_status.setText(f"Status: {message}")
        self.progress_bar.setValue(percentage)

    def display_result(self, record: MaintenanceRecord):
        self.set_operation_running(False)
        self.progress_bar.setValue(100)
        if record.status == OperationResult.SUCCESS:
            self.badge_maint.set_state("Success", "success")
            self.lbl_op_status.setText(f"Sukses: {record.notes or record.operation_type.value}")
            QtWidgets.QMessageBox.information(
                self,
                "Pemeliharaan Selesai",
                f"Operasi {record.operation_type.value} telah berhasil dikirim ke printer.\n\n"
                f"{record.notes or 'Printer sedang menjalankan tugas pemeliharaan.'}",
                QtWidgets.QMessageBox.StandardButton.Ok
            )
        else:
            self.badge_maint.set_state("Failed", "failed")
            self.lbl_op_status.setText(f"Gagal: {record.error_message or 'Error'}")
            QtWidgets.QMessageBox.critical(
                self,
                "Operasi Gagal",
                f"Gagal menjalankan operasi pemeliharaan:\n\n{record.error_message}",
                QtWidgets.QMessageBox.StandardButton.Ok
            )
