"""
Maintenance History and Audit Log View.
"""

from pathlib import Path
from app.ui.qt_compat import QtWidgets, QtCore, Signal, Slot
from app.ui.components.card_widget import CardWidget
from app.database.repository import MaintenanceRepository
from app.models.maintenance import MaintenanceRecord


class HistoryView(QtWidgets.QWidget):
    def __init__(self, repo: MaintenanceRepository, parent=None):
        super().__init__(parent)
        self.repo = repo
        self._init_ui()

    def _init_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header card with actions
        header_card = CardWidget("Maintenance History & Audit Log", "Immutable local record of all diagnostic and reset actions")
        btn_row = QtWidgets.QHBoxLayout()

        self.btn_refresh = QtWidgets.QPushButton("🔄  Refresh")
        self.btn_refresh.clicked.connect(self.load_history)
        btn_row.addWidget(self.btn_refresh)

        self.btn_export_json = QtWidgets.QPushButton("📄  Export JSON")
        self.btn_export_json.clicked.connect(self._export_json)
        btn_row.addWidget(self.btn_export_json)

        self.btn_export_csv = QtWidgets.QPushButton("📊  Export CSV")
        self.btn_export_csv.clicked.connect(self._export_csv)
        btn_row.addWidget(self.btn_export_csv)

        btn_row.addStretch()

        self.btn_clear = QtWidgets.QPushButton("🗑️  Clear")
        self.btn_clear.clicked.connect(self._clear_history)
        btn_row.addWidget(self.btn_clear)

        header_card.add_layout(btn_row)
        layout.addWidget(header_card)

        # History Table
        self.table = QtWidgets.QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Timestamp", "Serial Number", "Operation", "Pre Value", "Post Value", "Status", "Notes"
        ])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        layout.addWidget(self.table)

        self.load_history()

    def load_history(self):
        try:
            records = self.repo.get_records(limit=200)
            self.table.setRowCount(len(records))
            for row, r in enumerate(records):
                self.table.setItem(row, 0, QtWidgets.QTableWidgetItem(r.timestamp.strftime("%Y-%m-%d %H:%M:%S")))
                self.table.setItem(row, 1, QtWidgets.QTableWidgetItem(r.serial_number))
                self.table.setItem(row, 2, QtWidgets.QTableWidgetItem(r.operation_type.value))
                self.table.setItem(row, 3, QtWidgets.QTableWidgetItem(f"{r.pre_counter_value:,} pts"))
                post_str = f"{r.post_counter_value:,} pts" if r.post_counter_value is not None else "-"
                self.table.setItem(row, 4, QtWidgets.QTableWidgetItem(post_str))
                self.table.setItem(row, 5, QtWidgets.QTableWidgetItem(r.status.value))
                self.table.setItem(row, 6, QtWidgets.QTableWidgetItem(r.notes or ""))
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Error", f"Failed to load maintenance records: {e}")

    def _export_json(self):
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Export Records to JSON", "maintenance_history.json", "JSON Files (*.json)")
        if path:
            try:
                count = self.repo.export_to_json(Path(path))
                QtWidgets.QMessageBox.information(self, "Exported", f"Successfully exported {count} records to {path}")
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "Export Failed", f"Failed to export JSON: {e}")

    def _export_csv(self):
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Export Records to CSV", "maintenance_history.csv", "CSV Files (*.csv)")
        if path:
            try:
                count = self.repo.export_to_csv(Path(path))
                QtWidgets.QMessageBox.information(self, "Exported", f"Successfully exported {count} records to {path}")
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "Export Failed", f"Failed to export CSV: {e}")

    def _clear_history(self):
        reply = QtWidgets.QMessageBox.question(
            self,
            "Konfirmasi Hapus",
            "Apakah Anda yakin ingin menghapus semua riwayat pemeliharaan?",
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.Cancel
        )
        if reply == QtWidgets.QMessageBox.StandardButton.Yes:
            self.repo.clear_history()
            self.load_history()
