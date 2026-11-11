"""
Waste Ink Pad Counter Reading Service.
"""

from typing import Optional
from datetime import datetime
from app.communication.usb_interface import USBInterface
from app.communication.libusb_backend import LibUSBBackend
from app.communication.dot4_protocol import Dot4Session
from app.communication.epson_ctrl_transport import EpsonCtrlTransport
from app.models.counter import WastePadRecord, CounterReading
from app.core.constants import (
    EPSON_VENDOR_ID,
    PRINTER_INTERFACE_INDEX,
    MAIN_PAD_MAX_POINTS,
    PLATEN_PAD_MAX_POINTS,
    PadHealthStatus,
)
from app.core.exceptions import CommunicationError, ProtocolError
from app.core.logger import get_logger

log = get_logger("app.services.counter")


class CounterService:
    def __init__(self, usb_backend: Optional[USBInterface] = None):
        self.usb = usb_backend or LibUSBBackend()

    def read_waste_pad_counters(self, vendor_id: int = EPSON_VENDOR_ID, product_id: int = 0x1142) -> WastePadRecord:
        """Connect to printer, read counter telemetry, and return structured record."""
        now = datetime.now()
        try:
            self.usb.open_device(vendor_id, product_id)
            self.usb.claim_interface(PRINTER_INTERFACE_INDEX)

            with Dot4Session(self.usb) as session:
                transport = EpsonCtrlTransport(session)

                # Get telemetry from 'cd' command
                body = transport.get_counter_telemetry()
                if len(body) < 27:
                    raise ProtocolError(f"Counter telemetry truncated ({len(body)} bytes)")

                # Main Pad Counter: bytes 7..11 (uint32 LE)
                main_points = int.from_bytes(body[7:11], "little")

                # Platen Pad Counter: bytes 23..27 (uint32 LE)
                platen_points = int.from_bytes(body[23:27], "little")

                # Status query for overall percentage (Tag 0x4B)
                overall_pct = 0.0
                try:
                    tlvs = transport.get_status_tlv()
                    if 0x4B in tlvs and len(tlvs[0x4B]) >= 1:
                        overall_pct = float(tlvs[0x4B][0])
                except Exception as e:
                    log.debug(f"Tag 0x4B query exception: {e}")

                if overall_pct <= 0.0 and MAIN_PAD_MAX_POINTS > 0:
                    overall_pct = round((main_points / MAIN_PAD_MAX_POINTS) * 100.0, 1)

                main_pct = round((main_points / MAIN_PAD_MAX_POINTS) * 100.0, 1) if MAIN_PAD_MAX_POINTS > 0 else 0.0
                platen_pct = round((platen_points / PLATEN_PAD_MAX_POINTS) * 100.0, 1) if PLATEN_PAD_MAX_POINTS > 0 else 0.0

                main_reading = CounterReading(
                    counter_name="Main Waste Ink Pad",
                    current_points=main_points,
                    max_points=MAIN_PAD_MAX_POINTS,
                    percentage=main_pct,
                    last_read_time=now,
                    raw_hex=body[7:11].hex(),
                )

                platen_reading = CounterReading(
                    counter_name="Platen Waste Ink Pad",
                    current_points=platen_points,
                    max_points=PLATEN_PAD_MAX_POINTS,
                    percentage=platen_pct,
                    last_read_time=now,
                    raw_hex=body[23:27].hex(),
                )

                overall_status = PadHealthStatus.NORMAL
                if overall_pct >= 100.0:
                    overall_status = PadHealthStatus.CRITICAL
                elif overall_pct >= 80.0:
                    overall_status = PadHealthStatus.WARNING

                record = WastePadRecord(
                    main_pad=main_reading,
                    platen_pad=platen_reading,
                    overall_percentage=overall_pct,
                    overall_status=overall_status,
                    timestamp=now,
                )

                log.info(f"Counter reading: Main={main_points} pts ({main_pct}%), Platen={platen_points} pts ({platen_pct}%), Overall={overall_pct}%")
                return record

        except Exception as e:
            log.error(f"Error reading waste pad counters: {e}")
            raise CommunicationError(f"Failed to read waste counters: {e}") from e
        finally:
            self.usb.close()
