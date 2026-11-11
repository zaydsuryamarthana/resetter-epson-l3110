"""
Printer Information and Diagnostic Service.
"""

from typing import Optional, Dict, Any
from app.communication.usb_interface import USBInterface
from app.communication.libusb_backend import LibUSBBackend
from app.communication.dot4_protocol import Dot4Session
from app.communication.epson_ctrl_transport import EpsonCtrlTransport
from app.models.printer import PrinterInfo
from app.core.constants import (
    EPSON_VENDOR_ID,
    PRINTER_INTERFACE_INDEX,
    ConnectionStatus,
)
from app.core.exceptions import DeviceNotFoundError, CommunicationError
from app.core.logger import get_logger

log = get_logger("app.services.printer")


class PrinterService:
    def __init__(self, usb_backend: Optional[USBInterface] = None):
        self.usb = usb_backend or LibUSBBackend()

    def get_detailed_printer_info(self, vendor_id: int = EPSON_VENDOR_ID, product_id: int = 0x1142) -> PrinterInfo:
        """Connect to printer and extract full technical identity."""
        info = PrinterInfo(
            manufacturer="EPSON",
            model="Epson EcoTank L3110 Series",
            vendor_id=vendor_id,
            product_id=product_id,
            connection_status=ConnectionStatus.CONNECTING,
        )

        try:
            self.usb.open_device(vendor_id, product_id)
            self.usb.claim_interface(PRINTER_INTERFACE_INDEX)

            with Dot4Session(self.usb) as session:
                transport = EpsonCtrlTransport(session)

                # Query Firmware Version
                try:
                    info.firmware_version = transport.get_firmware_version()
                except Exception as e:
                    log.warning(f"Could not read firmware version: {e}")

                # Query Device ID String
                try:
                    info.device_id_raw = transport.get_device_id()
                except Exception as e:
                    log.warning(f"Could not read device ID: {e}")

                # Query Status TLVs
                try:
                    tlvs = transport.get_status_tlv()
                    # Tag 0x40 = Serial Number
                    if 0x40 in tlvs:
                        info.serial_number = tlvs[0x40].decode("ascii", errors="replace").strip()

                    # Tag 0x36 = Page Counters
                    if 0x36 in tlvs and len(tlvs[0x36]) >= 20:
                        tag36 = tlvs[0x36]
                        info.total_pages_printed = int.from_bytes(tag36[8:12], "little")
                        info.color_pages = int.from_bytes(tag36[12:16], "little")
                        info.scan_count = int.from_bytes(tag36[16:20], "little")
                        if info.total_pages_printed is not None and info.color_pages is not None:
                            info.monochrome_pages = max(0, info.total_pages_printed - info.color_pages)

                except Exception as e:
                    log.warning(f"Could not read status TLVs: {e}")

            info.connection_status = ConnectionStatus.CONNECTED
            log.info(f"Retrieved printer info: S/N={info.serial_number}, FW={info.firmware_version}, TotalPages={info.total_pages_printed}")
            return info

        except Exception as e:
            log.error(f"Error querying printer info: {e}")
            info.connection_status = ConnectionStatus.ERROR
            raise CommunicationError(f"Failed to query printer info: {e}") from e
        finally:
            self.usb.close()
