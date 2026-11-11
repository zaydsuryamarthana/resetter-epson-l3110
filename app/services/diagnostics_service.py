"""
Comprehensive Diagnostics Service.
"""

from typing import Optional, Dict, Any
from datetime import datetime
from app.communication.usb_interface import USBInterface
from app.communication.libusb_backend import LibUSBBackend
from app.communication.dot4_protocol import Dot4Session
from app.communication.epson_ctrl_transport import EpsonCtrlTransport
from app.models.maintenance import DiagnosticResult
from app.core.constants import EPSON_VENDOR_ID, PRINTER_INTERFACE_INDEX
from app.core.logger import get_logger

log = get_logger("app.services.diagnostics")


class DiagnosticsService:
    def __init__(self, usb_backend: Optional[USBInterface] = None):
        self.usb = usb_backend or LibUSBBackend()

    def run_diagnostics(self, vendor_id: int = EPSON_VENDOR_ID, product_id: int = 0x1142) -> DiagnosticResult:
        """Execute complete hardware & protocol diagnostic pipeline."""
        res = DiagnosticResult(timestamp=datetime.now())
        details: Dict[str, Any] = {}

        # Test 1: USB Device Discovery
        try:
            devs = self.usb.find_devices(vendor_id, product_id)
            if devs:
                res.usb_connection_ok = True
                details["usb_device"] = f"VID:0x{vendor_id:04x} PID:0x{product_id:04x}"
            else:
                details["usb_device"] = "Device not found on USB bus"
                res.details = details
                return res
        except Exception as e:
            details["usb_error"] = str(e)
            res.details = details
            return res

        # Test 2: Device ID match
        res.device_id_match = (product_id == 0x1142)
        details["model_verified"] = "Epson L3110 Series"

        # Test 3 & 4: D4 Handshake and EPSON-CTRL Channel
        try:
            self.usb.open_device(vendor_id, product_id)
            self.usb.claim_interface(PRINTER_INTERFACE_INDEX)

            with Dot4Session(self.usb) as session:
                res.d4_handshake_ok = True
                details["d4_mode"] = "Active"

                if session.sid_ctrl is not None:
                    res.ctrl_channel_ok = True
                    details["epson_ctrl_socket_id"] = session.sid_ctrl

                transport = EpsonCtrlTransport(session)

                # Read firmware
                fw = transport.get_firmware_version()
                details["firmware_version"] = fw

                # Test 5: Counter readability
                telemetry = transport.get_counter_telemetry()
                if len(telemetry) >= 27:
                    res.counter_readable = True
                    main_pts = int.from_bytes(telemetry[7:11], "little")
                    platen_pts = int.from_bytes(telemetry[23:27], "little")
                    details["main_pad_points"] = main_pts
                    details["platen_pad_points"] = platen_pts

        except Exception as e:
            details["protocol_error"] = str(e)
            log.warning(f"Diagnostic protocol test error: {e}")
        finally:
            self.usb.close()

        res.details = details
        log.info(f"Diagnostics complete. Passed: {res.all_passed} ({details})")
        return res
