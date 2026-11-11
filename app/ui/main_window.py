"""
Modern Minimalist Application Window with Sidebar Navigation and Asynchronous USB Workers.
Integrates Dashboard, Diagnostics, Counter Telemetry, Reset Utility, Universal Maintenance, and History.
"""

import threading
from typing import Optional, Dict
from app.ui.qt_compat import QtWidgets, QtCore, Signal, Slot, QThread
from app.ui.styles import DARK_THEME
from app.ui.dashboard import DashboardView
from app.ui.diagnostics_view import DiagnosticsView
from app.ui.counter_view import CounterView
from app.ui.reset_view import ResetView
from app.ui.maintenance_view import MaintenanceView
from app.ui.history_view import HistoryView
from app.ui.components.status_badge import StatusBadge
from app.services.device_manager import DeviceManager
from app.services.printer_service import PrinterService
from app.services.counter_service import CounterService
from app.services.diagnostics_service import DiagnosticsService
from app.services.reset_service import ResetService
from app.services.maintenance_service import MaintenanceService
from app.database.repository import MaintenanceRepository
from app.models.printer import PrinterInfo
from app.models.counter import WastePadRecord
from app.models.maintenance import DiagnosticResult, MaintenanceRecord
from app.core.constants import APP_NAME, APP_VERSION, ConnectionStatus, MaintenanceOperation
from app.core.logger import get_logger

log = get_logger("app.ui.main_window")


# --- ASYNCHRONOUS WORKERS ---

class RefreshCountersWorker(QThread):
    finished = Signal(object)
    error = Signal(str)

    def __init__(self, counter_svc: CounterService):
        super().__init__()
        self.counter_svc = counter_svc

    def run(self):
        try:
            record = self.counter_svc.read_waste_pad_counters()
            self.finished.emit(record)
        except Exception as e:
            self.error.emit(str(e))


class RunDiagnosticsWorker(QThread):
    finished = Signal(object)
    error = Signal(str)

    def __init__(self, diag_svc: DiagnosticsService):
        super().__init__()
        self.diag_svc = diag_svc

    def run(self):
        try:
            res = self.diag_svc.run_diagnostics()
            self.finished.emit(res)
        except Exception as e:
            self.error.emit(str(e))


class QueryPrinterInfoWorker(QThread):
    finished = Signal(object)
    error = Signal(str)

    def __init__(self, printer_svc: PrinterService):
        super().__init__()
        self.printer_svc = printer_svc

    def run(self):
        try:
            info = self.printer_svc.get_detailed_printer_info()
            self.finished.emit(info)
        except Exception as e:
            self.error.emit(str(e))


class ExecuteResetWorker(QThread):
    progress = Signal(str, int)
    request_power_cycle = Signal(object)
    finished = Signal(object)
    error = Signal(str)

    def __init__(
        self,
        reset_svc: ResetService,
        serial_number: str,
        operation: MaintenanceOperation,
        confirmed: bool
    ):
        super().__init__()
        self.reset_svc = reset_svc
        self.serial_number = serial_number
        self.operation = operation
        self.confirmed = confirmed

    def run(self):
        def _wait_power_cycle():
            evt = threading.Event()
            self.request_power_cycle.emit(evt)
            evt.wait()

        try:
            rec = self.reset_svc.execute_reset(
                vendor_id=0x04B8,
                product_id=0x1142,
                serial_number=self.serial_number,
                operation=self.operation,
                user_confirmed_sponge_serviced=self.confirmed,
                progress_callback=lambda msg, pct: self.progress.emit(msg, pct),
                power_cycle_callback=_wait_power_cycle,
            )
            self.finished.emit(rec)
        except Exception as e:
            self.error.emit(str(e))


class ExecuteNozzleCheckWorker(QThread):
    progress = Signal(str, int)
    finished = Signal(object)
    error = Signal(str)

    def __init__(self, maint_svc: MaintenanceService, serial_number: str):
        super().__init__()
        self.maint_svc = maint_svc
        self.serial_number = serial_number

    def run(self):
        try:
            rec = self.maint_svc.perform_nozzle_check(
                vendor_id=0x04B8,
                product_id=0x1142,
                serial_number=self.serial_number,
                progress_callback=lambda msg, pct: self.progress.emit(msg, pct),
            )
            self.finished.emit(rec)
        except Exception as e:
            self.error.emit(str(e))


class ExecuteHeadCleaningWorker(QThread):
    progress = Signal(str, int)
    finished = Signal(object)
    error = Signal(str)

    def __init__(self, maint_svc: MaintenanceService, serial_number: str):
        super().__init__()
        self.maint_svc = maint_svc
        self.serial_number = serial_number

    def run(self):
        try:
            rec = self.maint_svc.perform_head_cleaning(
                vendor_id=0x04B8,
                product_id=0x1142,
                serial_number=self.serial_number,
                progress_callback=lambda msg, pct: self.progress.emit(msg, pct),
            )
            self.finished.emit(rec)
        except Exception as e:
            self.error.emit(str(e))


class ExecutePowerCleaningWorker(QThread):
    progress = Signal(str, int)
    finished = Signal(object)
    error = Signal(str)

    def __init__(self, maint_svc: MaintenanceService, serial_number: str, confirmed: bool):
        super().__init__()
        self.maint_svc = maint_svc
        self.serial_number = serial_number
        self.confirmed = confirmed

    def run(self):
        try:
            rec = self.maint_svc.perform_power_cleaning(
                vendor_id=0x04B8,
                product_id=0x1142,
                serial_number=self.serial_number,
                confirmed_ink_level=self.confirmed,
                progress_callback=lambda msg, pct: self.progress.emit(msg, pct),
            )
            self.finished.emit(rec)
        except Exception as e:
            self.error.emit(str(e))


class ExecuteAlignmentSheetWorker(QThread):
    progress = Signal(str, int)
    finished = Signal(object)
    error = Signal(str)

    def __init__(self, maint_svc: MaintenanceService, serial_number: str):
        super().__init__()
        self.maint_svc = maint_svc
        self.serial_number = serial_number

    def run(self):
        try:
            rec = self.maint_svc.print_alignment_sheet(
                vendor_id=0x04B8,
                product_id=0x1142,
                serial_number=self.serial_number,
                progress_callback=lambda msg, pct: self.progress.emit(msg, pct),
            )
            self.finished.emit(rec)
        except Exception as e:
            self.error.emit(str(e))


class ExecuteApplyAlignmentWorker(QThread):
    progress = Signal(str, int)
    finished = Signal(object)
    error = Signal(str)

    def __init__(self, maint_svc: MaintenanceService, serial_number: str, offsets: Dict[int, int]):
        super().__init__()
        self.maint_svc = maint_svc
        self.serial_number = serial_number
        self.offsets = offsets

    def run(self):
        try:
            rec = self.maint_svc.apply_alignment_offset(
                vendor_id=0x04B8,
                product_id=0x1142,
                serial_number=self.serial_number,
                offsets=self.offsets,
                progress_callback=lambda msg, pct: self.progress.emit(msg, pct),
            )
            self.finished.emit(rec)
        except Exception as e:
            self.error.emit(str(e))


# --- MAIN APPLICATION WINDOW ---

class MainWindow(QtWidgets.QMainWindow):
    def __init__(
        self,
        device_manager: DeviceManager,
        printer_service: PrinterService,
        counter_service: CounterService,
        diagnostics_service: DiagnosticsService,
        reset_service: ResetService,
        repository: MaintenanceRepository,
        maintenance_service: Optional[MaintenanceService] = None,
        parent=None
    ):
        super().__init__(parent)
        self.dev_mgr = device_manager
        self.printer_svc = printer_service
        self.counter_svc = counter_service
        self.diag_svc = diagnostics_service
        self.reset_svc = reset_service
        self.repo = repository
        self.maint_svc = maintenance_service or MaintenanceService(
            usb_backend=self.printer_svc.usb,
            counter_service=self.counter_svc,
            repository=self.repo
        )

        self.current_printer_info: Optional[PrinterInfo] = None
        self.current_counters: Optional[WastePadRecord] = None

        self._active_workers = []

        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION} — Cross-Platform Maintenance Suite")
        self.resize(1080, 720)
        self.setMinimumSize(920, 600)
        self.setStyleSheet(DARK_THEME)

        self._init_ui()
        self._setup_device_monitoring()

    def _init_ui(self):
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        main_layout = QtWidgets.QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. Left Sidebar
        sidebar = QtWidgets.QWidget()
        sidebar.setObjectName("sidebar")
        sb_layout = QtWidgets.QVBoxLayout(sidebar)
        sb_layout.setContentsMargins(14, 20, 14, 20)
        sb_layout.setSpacing(6)

        # Brand Header
        brand_lbl = QtWidgets.QLabel("EPSON L3110")
        brand_lbl.setStyleSheet("font-size: 16px; font-weight: 800; color: #58a6ff; padding: 4px 10px;")
        sub_brand = QtWidgets.QLabel("Universal Maintenance Suite")
        sub_brand.setStyleSheet("font-size: 11px; color: #8b949e; padding-left: 10px; margin-bottom: 16px;")
        sb_layout.addWidget(brand_lbl)
        sb_layout.addWidget(sub_brand)

        # Navigation Buttons (6 Tabs)
        self.nav_group = QtWidgets.QButtonGroup(self)
        self.nav_group.setExclusive(True)

        nav_items = [
            ("🏠  Dashboard", 0),
            ("🩺  Diagnostics", 1),
            ("📊  Waste Counter", 2),
            ("🛡️  Reset Utility", 3),
            ("🛠️  Maintenance", 4),
            ("📜  History", 5),
        ]

        self.nav_buttons = []
        for text, idx in nav_items:
            btn = QtWidgets.QPushButton(text)
            btn.setObjectName("nav_btn")
            btn.setCheckable(True)
            if idx == 0:
                btn.setChecked(True)
            btn.clicked.connect(lambda checked, i=idx: self.switch_page(i))
            self.nav_group.addButton(btn, idx)
            sb_layout.addWidget(btn)
            self.nav_buttons.append(btn)

        sb_layout.addStretch()

        # Version stamp
        ver_lbl = QtWidgets.QLabel(f"v{APP_VERSION} (Driverless USB)")
        ver_lbl.setStyleSheet("font-size: 11px; color: #484f58; padding: 10px;")
        sb_layout.addWidget(ver_lbl)

        main_layout.addWidget(sidebar)

        # 2. Right Content Stack
        self.stack = QtWidgets.QStackedWidget()

        # Tab 0: Dashboard
        self.dashboard_view = DashboardView()
        self.dashboard_view.navigate_to.connect(self.switch_page)
        self.dashboard_view.request_refresh_counters.connect(self.trigger_refresh_counters)
        self.dashboard_view.request_run_diagnostics.connect(self.trigger_run_diagnostics)
        self.stack.addWidget(self.dashboard_view)

        # Tab 1: Diagnostics
        self.diagnostics_view = DiagnosticsView()
        self.diagnostics_view.run_diagnostics_requested.connect(self.trigger_run_diagnostics)
        self.stack.addWidget(self.diagnostics_view)

        # Tab 2: Counter Telemetry
        self.counter_view = CounterView()
        self.counter_view.refresh_requested.connect(self.trigger_refresh_counters)
        self.stack.addWidget(self.counter_view)

        # Tab 3: Reset Utility
        self.reset_view = ResetView()
        self.reset_view.execute_reset_requested.connect(self.trigger_execute_reset)
        self.stack.addWidget(self.reset_view)

        # Tab 4: Universal Maintenance
        self.maintenance_view = MaintenanceView()
        self.maintenance_view.nozzle_check_requested.connect(self.trigger_nozzle_check)
        self.maintenance_view.head_cleaning_requested.connect(self.trigger_head_cleaning)
        self.maintenance_view.power_cleaning_requested.connect(self.trigger_power_cleaning)
        self.maintenance_view.alignment_sheet_requested.connect(self.trigger_alignment_sheet)
        self.maintenance_view.apply_alignment_requested.connect(self.trigger_apply_alignment)
        self.stack.addWidget(self.maintenance_view)

        # Tab 5: History
        self.history_view = HistoryView(self.repo)
        self.stack.addWidget(self.history_view)

        main_layout.addWidget(self.stack, 1)

        # Status Bar
        self.status_bar = self.statusBar()
        self.status_conn_badge = StatusBadge("Disconnected", "disconnected")
        self.status_bar.addPermanentWidget(self.status_conn_badge)
        self.status_bar.showMessage("Siap. Menunggu deteksi printer USB...")

    def switch_page(self, index: int):
        self.stack.setCurrentIndex(index)
        for i, btn in enumerate(self.nav_buttons):
            btn.setChecked(i == index)
        if index == 5:
            self.history_view.load_history()

    def _setup_device_monitoring(self):
        self.dev_mgr.add_connection_listener(self._on_connection_change)
        self.dev_mgr.start_monitoring(1500)

    def _on_connection_change(self, printer: Optional[PrinterInfo], status: ConnectionStatus):
        QtCore.QMetaObject.invokeMethod(
            self,
            "_handle_connection_change_gui",
            QtCore.Qt.ConnectionType.QueuedConnection,
            QtCore.Q_ARG(object, printer),
            QtCore.Q_ARG(object, status),
        )

    @Slot(object, object)
    def _handle_connection_change_gui(self, printer: Optional[PrinterInfo], status: ConnectionStatus):
        if status == ConnectionStatus.CONNECTED and printer:
            self.status_conn_badge.set_state("Connected", "connected")
            self.status_bar.showMessage(f"Terhubung ke {printer.model} pada USB")
            self.current_printer_info = printer
            self.dashboard_view.update_printer_info(printer)
            self.trigger_query_printer_info()
            self.trigger_refresh_counters()
        else:
            self.status_conn_badge.set_state("Disconnected", "disconnected")
            self.status_bar.showMessage("Printer USB terputus.")
            self.current_printer_info = None
            empty_info = PrinterInfo(connection_status=ConnectionStatus.DISCONNECTED)
            self.dashboard_view.update_printer_info(empty_info)

    # --- ACTIONS: GENERAL ---

    def trigger_query_printer_info(self):
        worker = QueryPrinterInfoWorker(self.printer_svc)
        worker.finished.connect(self._on_printer_info_received)
        worker.error.connect(lambda err: log.debug(f"Printer info query error: {err}"))
        self._active_workers.append(worker)
        worker.start()

    def _on_printer_info_received(self, info: PrinterInfo):
        self.current_printer_info = info
        self.dashboard_view.update_printer_info(info)
        self.counter_view.update_page_stats(info)

    def trigger_refresh_counters(self):
        self.status_bar.showMessage("Membaca data counter bantalan limbah dari printer...")
        worker = RefreshCountersWorker(self.counter_svc)
        worker.finished.connect(self._on_counters_received)
        worker.error.connect(lambda err: self.status_bar.showMessage(f"Gagal membaca counter: {err}"))
        self._active_workers.append(worker)
        worker.start()

    def _on_counters_received(self, record: WastePadRecord):
        self.current_counters = record
        self.dashboard_view.update_counters(record)
        self.counter_view.update_counters(record)
        self.status_bar.showMessage(
            f"Counter diperbarui: Main Pad={record.main_pad.percentage}% ({record.main_pad.current_points:,} pts)"
        )

    def trigger_run_diagnostics(self):
        self.diagnostics_view.set_running(True)
        self.status_bar.showMessage("Menjalankan diagnostik perangkat keras dan protokol USB...")
        worker = RunDiagnosticsWorker(self.diag_svc)
        worker.finished.connect(self._on_diagnostics_received)
        worker.error.connect(lambda err: self.diagnostics_view.set_running(False))
        self._active_workers.append(worker)
        worker.start()

    def _on_diagnostics_received(self, res: DiagnosticResult):
        self.diagnostics_view.display_results(res)
        self.status_bar.showMessage(f"Diagnostik selesai: {'Semua Lolos' if res.all_passed else 'Ada Masalah'}")

    # --- ACTIONS: RESET UTILITY ---

    def trigger_execute_reset(self, operation_str: str, confirmed: bool):
        self.dev_mgr.stop_monitoring()
        serial = self.current_printer_info.serial_number if self.current_printer_info else "UNKNOWN"
        op = MaintenanceOperation(operation_str)
        self.status_bar.showMessage(f"Menjalankan operasi reset: {op.value}...")
        worker = ExecuteResetWorker(self.reset_svc, serial, op, confirmed)
        worker.progress.connect(self.reset_view.update_progress)
        worker.request_power_cycle.connect(self._on_power_cycle_requested)
        worker.finished.connect(self._on_reset_completed)
        worker.error.connect(self._on_reset_error)
        self._active_workers.append(worker)
        worker.start()

    def _on_reset_error(self, err: str):
        self.dev_mgr.start_monitoring(1500)
        QtWidgets.QMessageBox.critical(self, "Reset Error", err)

    def _on_power_cycle_requested(self, event):
        QtWidgets.QMessageBox.information(
            self,
            "Langkah Wajib: Matikan dan Hidupkan Ulang Printer",
            "Perintah reset counter telah diterima oleh printer (Status: OK).\n\n"
            "Kedua lampu indikator printer menyala/berkedip bersamaan menandakan printer sedang menunggu reboot.\n\n"
            "Langkah yang harus dilakukan:\n"
            "1. Tekan tombol POWER fisik pada printer untuk mematikan printer.\n"
            "2. Tunggu 5-10 detik sampai semua lampu padam total.\n"
            "3. Hidupkan kembali printer menggunakan tombol POWER.\n"
            "4. Setelah printer menyala kembali, klik 'OK' untuk melanjutkan verifikasi.",
            QtWidgets.QMessageBox.StandardButton.Ok
        )
        event.set()

    def _on_reset_completed(self, record: MaintenanceRecord):
        self.dev_mgr.start_monitoring(1500)
        self.reset_view.display_result(record)
        self.trigger_refresh_counters()
        self.history_view.load_history()

    # --- ACTIONS: UNIVERSAL MAINTENANCE ---

    def _get_serial_for_maint(self) -> str:
        return self.current_printer_info.serial_number if self.current_printer_info else "Unknown"

    def trigger_nozzle_check(self):
        self.dev_mgr.stop_monitoring()
        self.maintenance_view.set_operation_running(True, "Nozzle Check")
        self.status_bar.showMessage("Mengirim perintah Nozzle Check...")
        worker = ExecuteNozzleCheckWorker(self.maint_svc, self._get_serial_for_maint())
        worker.progress.connect(self.maintenance_view.update_progress)
        worker.finished.connect(self._on_maintenance_completed)
        worker.error.connect(self._on_maintenance_error)
        self._active_workers.append(worker)
        worker.start()

    def trigger_head_cleaning(self):
        self.dev_mgr.stop_monitoring()
        self.maintenance_view.set_operation_running(True, "Head Cleaning")
        self.status_bar.showMessage("Menjalankan siklus Head Cleaning...")
        worker = ExecuteHeadCleaningWorker(self.maint_svc, self._get_serial_for_maint())
        worker.progress.connect(self.maintenance_view.update_progress)
        worker.finished.connect(self._on_maintenance_completed)
        worker.error.connect(self._on_maintenance_error)
        self._active_workers.append(worker)
        worker.start()

    def trigger_power_cleaning(self, confirmed_ink: bool):
        self.dev_mgr.stop_monitoring()
        self.maintenance_view.set_operation_running(True, "Power Cleaning")
        self.status_bar.showMessage("Memulai proses Power Cleaning...")
        worker = ExecutePowerCleaningWorker(self.maint_svc, self._get_serial_for_maint(), confirmed_ink)
        worker.progress.connect(self.maintenance_view.update_progress)
        worker.finished.connect(self._on_maintenance_completed)
        worker.error.connect(self._on_maintenance_error)
        self._active_workers.append(worker)
        worker.start()

    def trigger_alignment_sheet(self):
        self.dev_mgr.stop_monitoring()
        self.maintenance_view.set_operation_running(True, "Print Alignment Sheet")
        self.status_bar.showMessage("Mencetak lembar uji alignment...")
        worker = ExecuteAlignmentSheetWorker(self.maint_svc, self._get_serial_for_maint())
        worker.progress.connect(self.maintenance_view.update_progress)
        worker.finished.connect(self._on_maintenance_completed)
        worker.error.connect(self._on_maintenance_error)
        self._active_workers.append(worker)
        worker.start()

    def trigger_apply_alignment(self, offsets: Dict[int, int]):
        self.dev_mgr.stop_monitoring()
        self.maintenance_view.set_operation_running(True, "Apply Alignment Offsets")
        self.status_bar.showMessage("Menerapkan nilai offset alignment ke firmware...")
        worker = ExecuteApplyAlignmentWorker(self.maint_svc, self._get_serial_for_maint(), offsets)
        worker.progress.connect(self.maintenance_view.update_progress)
        worker.finished.connect(self._on_maintenance_completed)
        worker.error.connect(self._on_maintenance_error)
        self._active_workers.append(worker)
        worker.start()

    def _on_maintenance_completed(self, record: MaintenanceRecord):
        self.dev_mgr.start_monitoring(1500)
        self.maintenance_view.display_result(record)
        self.status_bar.showMessage(f"Operasi {record.operation_type.value} berhasil diselesaikan.")
        self.history_view.load_history()

    def _on_maintenance_error(self, err_msg: str):
        self.dev_mgr.start_monitoring(1500)
        self.maintenance_view.set_operation_running(False)
        self.status_bar.showMessage(f"Gagal: {err_msg}")
        QtWidgets.QMessageBox.critical(self, "Maintenance Error", err_msg)

    def closeEvent(self, event):
        self.dev_mgr.stop_monitoring()
        for w in self._active_workers:
            if w.isRunning():
                w.wait(500)
        event.accept()
