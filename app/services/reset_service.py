"""
Safety-Gated Counter Reset Management Service.
"""

from typing import Optional, Callable
from app.communication.usb_interface import USBInterface
from app.communication.libusb_backend import LibUSBBackend
from app.communication.dot4_protocol import Dot4Session
from app.communication.epson_ctrl_transport import EpsonCtrlTransport
from app.services.counter_service import CounterService
from app.services.verification_service import VerificationService
from app.models.maintenance import MaintenanceRecord
from app.models.counter import WastePadRecord
from app.core.constants import (
    EPSON_VENDOR_ID,
    PRINTER_INTERFACE_INDEX,
    MaintenanceOperation,
    OperationResult,
)
from app.core.exceptions import SafetyGateError, CommunicationError
from app.core.logger import get_logger

log = get_logger("app.services.reset")


class ResetService:
    def __init__(
        self,
        usb_backend: Optional[USBInterface] = None,
        counter_service: Optional[CounterService] = None,
        verification_service: Optional[VerificationService] = None,
    ):
        self.usb = usb_backend or LibUSBBackend()
        self.counter_svc = counter_service or CounterService(self.usb)
        self.verify_svc = verification_service or VerificationService()

    def execute_reset(
        self,
        vendor_id: int,
        product_id: int,
        serial_number: str,
        operation: MaintenanceOperation,
        user_confirmed_sponge_serviced: bool,
        progress_callback: Optional[Callable[[str, int], None]] = None,
        power_cycle_callback: Optional[Callable[[], None]] = None,
        notes: Optional[str] = None
    ) -> MaintenanceRecord:
        """
        Execute counter reset with strict multi-layer safety validation.
        """
        def _report(msg: str, pct: int):
            log.info(f"Reset Progress ({pct}%): {msg}")
            if progress_callback:
                try:
                    progress_callback(msg, pct)
                except Exception:
                    pass

        _report("Validating safety requirements...", 10)

        # Safety Gate 1: Physical ink sponge replacement acknowledgment
        if not user_confirmed_sponge_serviced:
            raise SafetyGateError(
                "Reset blocked: User has not confirmed physical inspection or replacement of the waste ink sponge."
            )

        # Safety Gate 2: Device Model Match Verification
        if vendor_id != EPSON_VENDOR_ID or product_id != 0x1142:
            raise SafetyGateError(
                f"Reset blocked: Connected device (VID:0x{vendor_id:04x} PID:0x{product_id:04x}) is not a verified Epson L3110."
            )

        _report("Performing pre-reset counter reading...", 25)

        # Safety Gate 3: Pre-reset counter reading must succeed
        try:
            pre_counters = self.counter_svc.read_waste_pad_counters(vendor_id, product_id)
        except Exception as e:
            raise SafetyGateError(f"Reset blocked: Failed to read pre-reset counter: {e}") from e

        _report(f"Pre-reset Main Pad: {pre_counters.main_pad.current_points} pts. Initiating reset sequence...", 50)

        # Execute Reset over Dot4 EPSON-CTRL channel
        reset_success = False
        try:
            self.usb.open_device(vendor_id, product_id)
            self.usb.claim_interface(PRINTER_INTERFACE_INDEX)

            with Dot4Session(self.usb) as session:
                transport = EpsonCtrlTransport(session)
                _report("Dispatching waste pad reset command ('rw') with SHA-1 serial token...", 65)
                reset_success = transport.execute_waste_pad_reset(serial_number)

        except Exception as e:
            log.error(f"Reset command execution error: {e}")
            raise CommunicationError(f"Failed to execute reset command on printer: {e}") from e
        finally:
            self.usb.close()

        if not reset_success:
            log.warning("Printer firmware returned non-OK status on reset command")

        # Step: Physical Power Cycle requirement
        if power_cycle_callback:
            _report("Printer reset command accepted. Awaiting physical power cycle...", 75)
            try:
                power_cycle_callback()
            except Exception as e:
                log.warning(f"Power cycle callback warning: {e}")

        _report("Performing post-reset verification reading...", 85)

        # Post-reset reading for verification
        try:
            post_counters = self.counter_svc.read_waste_pad_counters(vendor_id, product_id)
        except Exception as e:
            log.warning(f"Failed to read post-reset counter: {e}")
            post_counters = WastePadRecord.create_empty()

        _report("Verifying counter reduction...", 95)

        # Audit and verify
        record = self.verify_svc.verify_reset(
            serial_number=serial_number,
            operation=operation,
            pre_record=pre_counters,
            post_record=post_counters,
            notes=notes,
        )

        if record.status != OperationResult.VERIFIED:
            if record.pre_counter_value == record.post_counter_value:
                record.error_message = (
                    "Nilai counter belum berkurang. Pastikan printer telah dimatikan secara fisik "
                    "menggunakan tombol Power, tunggu 5-10 detik sampai lampu padam total, lalu "
                    "hidupkan kembali agar firmware printer memuat ulang nilai reset dari EEPROM."
                )

        _report(f"Reset finished. Status: {record.status.value}", 100)
        return record
