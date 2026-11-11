"""
EPSON-CTRL High-Level Command Protocol Transport.
"""

import struct
import hashlib
from typing import Dict, Any, Optional, Tuple
from app.communication.dot4_protocol import Dot4Session
from app.core.constants import (
    CMD_VERSION_INFO,
    CMD_DEVICE_ID,
    CMD_STATUS,
    CMD_COUNTER_DATA,
    CMD_RESET,
    CMD_READ_WRITE,
)
from app.core.exceptions import ProtocolError
from app.core.logger import get_logger

log = get_logger("app.communication.epson_ctrl")


class EpsonCtrlTransport:
    def __init__(self, session: Dot4Session):
        self.session = session

    def send_command(self, cmd_name: str, payload: bytes = b"", timeout_s: float = 3.0) -> bytes:
        """Send a 2-char verb with 16-bit little-endian length prefix."""
        header = cmd_name.encode("ascii") + struct.pack("<H", len(payload))
        req = header + payload
        return self.session.send_ctrl(req, timeout_s=timeout_s)

    def get_firmware_version(self) -> str:
        """Query firmware version string via 'vi' command."""
        resp = self.send_command(CMD_VERSION_INFO, b"\x00")
        # Format: b'vi:00:VC15N9;\x0c'
        try:
            text = resp.decode("ascii", errors="replace").strip("\x0c\r\n;")
            parts = text.split(":")
            if len(parts) >= 3:
                return parts[2]
            return text
        except Exception as e:
            log.warning(f"Failed to parse firmware version: {e}")
            return "Unknown"

    def get_device_id(self) -> str:
        """Query IEEE 1284 Device ID via 'di' command."""
        resp = self.send_command(CMD_DEVICE_ID, b"\x01")
        try:
            text = resp.decode("latin1", errors="replace").strip()
            # Often has @EJL ID\r\n prefix
            if "@EJL ID" in text:
                text = text.split("@EJL ID")[-1].strip()
            return text
        except Exception as e:
            log.warning(f"Failed to parse device ID: {e}")
            return ""

    def get_status_tlv(self) -> Dict[int, bytes]:
        """Query status report and parse TLV records from @BDC ST2 response."""
        resp = self.send_command(CMD_STATUS, b"\x01")
        tlvs: Dict[int, bytes] = {}
        header = b"@BDC ST2\r\n"
        if not resp.startswith(header):
            log.warning("Status response missing @BDC ST2 header")
            return tlvs

        raw = resp[len(header):]
        idx = 0
        while idx < len(raw):
            tag = raw[idx]
            if idx + 1 >= len(raw):
                break
            length = raw[idx + 1]
            val = raw[idx + 2 : idx + 2 + length]
            tlvs[tag] = val
            idx += 2 + length
        return tlvs

    def parse_page_counters(self, tlvs: Dict[int, bytes]) -> Dict[str, int]:
        """Extract page production statistics from Tag 0x36."""
        stats = {"total_pages": 0, "color_pages": 0, "monochrome_pages": 0, "scan_count": 0}
        if 0x36 in tlvs and len(tlvs[0x36]) >= 20:
            tag = tlvs[0x36]
            stats["total_pages"] = int.from_bytes(tag[8:12], "little")
            stats["color_pages"] = int.from_bytes(tag[12:16], "little")
            stats["scan_count"] = int.from_bytes(tag[16:20], "little")
            stats["monochrome_pages"] = max(0, stats["total_pages"] - stats["color_pages"])
        return stats

    def get_counter_telemetry(self) -> bytes:
        """Query raw 73-byte counter telemetry structure via 'cd' command."""
        resp = self.send_command(CMD_COUNTER_DATA, b"\x00")
        # Response format: b'@BDC PS\r\ncd:00' + record_len (2B LE) + body + b'/\x16;\x0c'
        header = b"@BDC PS\r\ncd:00"
        if not resp.startswith(header):
            raise ProtocolError("Invalid counter response header")

        raw = resp[len(header):]
        if len(raw) < 2:
            raise ProtocolError("Counter response truncated")

        record_len = int.from_bytes(raw[:2], "little")
        body = raw[2 : 2 + record_len]
        if len(body) != record_len:
            raise ProtocolError(f"Counter body length mismatch (expected {record_len}, got {len(body)})")
        return body

    def execute_waste_pad_reset(self, serial_number: str) -> bool:
        """
        Execute waste ink pad counter reset via 'rw' command using SHA-1 serial token.
        Format: b'\\x01\\x00' + sha1(serial.encode('ascii')).digest()
        Response: b'@BDC PS\\r\\nrw:01:OK;\\x0c'
        """
        code = hashlib.sha1(serial_number.encode("ascii")).digest()
        payload = b"\x01\x00" + code
        resp = self.send_command(CMD_READ_WRITE, payload)
        log.info(f"Executed waste pad reset command ('rw'). Response: {repr(resp)}")
        return b"OK" in resp

    def execute_soft_reset(self) -> bool:
        """Execute device soft reset via 'rs:01'."""
        resp = self.send_command(CMD_RESET, b"\x01")
        # Expected: b'rs:01:OK;\x0c'
        return b"OK" in resp
