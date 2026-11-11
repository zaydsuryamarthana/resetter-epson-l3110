"""
USB Device Manager and Hotplug Monitor.
"""

import time
import threading
from typing import Optional, List, Callable
from app.communication.usb_interface import USBInterface
from app.communication.libusb_backend import LibUSBBackend
from app.models.printer import PrinterInfo
from app.core.constants import (
    EPSON_VENDOR_ID,
    SUPPORTED_DEVICES,
    ConnectionStatus,
)
from app.core.config import config
from app.core.logger import get_logger

log = get_logger("app.services.device_manager")


class DeviceManager:
    def __init__(self, usb_backend: Optional[USBInterface] = None):
        self.usb = usb_backend or LibUSBBackend()
        self.current_printer: Optional[PrinterInfo] = None
        self._listeners: List[Callable[[Optional[PrinterInfo], ConnectionStatus], None]] = []
        self._monitor_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()

    def add_connection_listener(self, callback: Callable[[Optional[PrinterInfo], ConnectionStatus], None]):
        """Register a callback for printer connection state changes."""
        with self._lock:
            if callback not in self._listeners:
                self._listeners.append(callback)

    def remove_connection_listener(self, callback: Callable[[Optional[PrinterInfo], ConnectionStatus], None]):
        with self._lock:
            if callback in self._listeners:
                self._listeners.remove(callback)

    def _notify(self, printer: Optional[PrinterInfo], status: ConnectionStatus):
        with self._lock:
            callbacks = list(self._listeners)
        for cb in callbacks:
            try:
                cb(printer, status)
            except Exception as e:
                log.error(f"Error in connection listener callback: {e}")

    def scan_for_printer(self) -> Optional[PrinterInfo]:
        """Scan USB buses for Epson L3110."""
        try:
            devices = self.usb.find_devices(EPSON_VENDOR_ID, 0x1142)
            if devices:
                vid, pid, _ = devices[0]
                model_name = SUPPORTED_DEVICES.get(pid, "Epson L3110 Series")
                printer = PrinterInfo(
                    manufacturer="EPSON",
                    model=model_name,
                    vendor_id=vid,
                    product_id=pid,
                    connection_status=ConnectionStatus.CONNECTED,
                )
                return printer
        except Exception as e:
            log.debug(f"Device scan error: {e}")
        return None

    def check_connection(self) -> ConnectionStatus:
        """Check active connection status and update state."""
        found = self.scan_for_printer()
        with self._lock:
            prev_status = self.current_printer.connection_status if self.current_printer else ConnectionStatus.DISCONNECTED

            if found:
                if self.current_printer is None or prev_status != ConnectionStatus.CONNECTED:
                    self.current_printer = found
                    log.info(f"Printer connected: {found.model} (VID:0x{found.vendor_id:04x} PID:0x{found.product_id:04x})")
                    self._notify(self.current_printer, ConnectionStatus.CONNECTED)
                return ConnectionStatus.CONNECTED
            else:
                if self.current_printer is not None and prev_status != ConnectionStatus.DISCONNECTED:
                    log.info("Printer disconnected")
                    self.current_printer.connection_status = ConnectionStatus.DISCONNECTED
                    self._notify(self.current_printer, ConnectionStatus.DISCONNECTED)
                    self.current_printer = None
                return ConnectionStatus.DISCONNECTED

    def start_monitoring(self, poll_interval_ms: Optional[int] = None):
        """Start background polling thread to detect device connection/disconnection."""
        interval = (poll_interval_ms or config.usb_poll_interval_ms) / 1000.0
        if self._monitor_thread and self._monitor_thread.is_alive():
            return

        self._stop_event.clear()

        def _run():
            while not self._stop_event.is_set():
                try:
                    self.check_connection()
                except Exception as e:
                    log.debug(f"Monitor loop error: {e}")
                self._stop_event.wait(interval)

        self._monitor_thread = threading.Thread(target=_run, name="USBDeviceMonitor", daemon=True)
        self._monitor_thread.start()
        log.debug("USB device monitoring thread started")

    def stop_monitoring(self):
        """Stop background polling thread."""
        self._stop_event.set()
        if self._monitor_thread:
            self._monitor_thread.join(timeout=1.0)
            self._monitor_thread = None
            log.debug("USB device monitoring thread stopped")
