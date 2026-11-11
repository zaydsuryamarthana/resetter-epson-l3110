"""
Application Bootstrap and Dependency Injection Container.
"""

from typing import Dict, Any
from app.core.config import config
from app.core.logger import setup_logging, get_logger
from app.database.connection import DatabaseConnection
from app.database.repository import MaintenanceRepository, CounterSnapshotRepository
from app.communication.libusb_backend import LibUSBBackend
from app.services.device_manager import DeviceManager
from app.services.printer_service import PrinterService
from app.services.counter_service import CounterService
from app.services.diagnostics_service import DiagnosticsService
from app.services.reset_service import ResetService
from app.services.verification_service import VerificationService
from app.services.maintenance_service import MaintenanceService

log = get_logger("app.bootstrap")


class AppContainer:
    def __init__(self, debug: bool = False):
        self.debug = debug
        setup_logging(log_file=config.log_file)
        log.info("Bootstrapping Epson L3110 Resetter application...")

        # Core & Database
        self.db_conn = DatabaseConnection.get_instance(config.db_path)
        self.maintenance_repo = MaintenanceRepository(self.db_conn)
        self.snapshot_repo = CounterSnapshotRepository(self.db_conn)

        # Communication Backend
        self.usb_backend = LibUSBBackend()

        # Services
        self.device_manager = DeviceManager(self.usb_backend)
        self.printer_service = PrinterService(self.usb_backend)
        self.counter_service = CounterService(self.usb_backend)
        self.diagnostics_service = DiagnosticsService(self.usb_backend)
        self.verification_service = VerificationService(self.maintenance_repo)
        self.reset_service = ResetService(
            usb_backend=self.usb_backend,
            counter_service=self.counter_service,
            verification_service=self.verification_service,
        )
        self.maintenance_service = MaintenanceService(
            usb_backend=self.usb_backend,
            counter_service=self.counter_service,
            repository=self.maintenance_repo,
        )

        log.info("All application services initialized successfully.")


def create_app_container(debug: bool = False) -> AppContainer:
    return AppContainer(debug=debug)
