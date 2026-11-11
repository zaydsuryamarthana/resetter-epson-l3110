"""
IEEE 1284.4 (Dot4) Protocol Multiplexing Engine.
"""

import time
import struct
from typing import Optional, Tuple
from app.communication.usb_interface import USBInterface
from app.core.constants import (
    PRINTER_EP_OUT,
    PRINTER_EP_IN,
    D4_MODE_ENTRY_SEQUENCE,
    D4_MODE_EXIT_SEQUENCE,
    D4_CMD_INIT,
    D4_CMD_OPEN_CHANNEL,
    D4_CMD_CLOSE_CHANNEL,
    D4_CMD_CREDIT,
    D4_CMD_CREDIT_REQUEST,
    D4_CMD_EXIT,
    D4_CMD_GET_SOCKET_ID,
    D4_SERVICE_EPSON_CTRL,
)
from app.core.exceptions import D4ProtocolError, DeviceTimeoutError
from app.core.logger import get_logger

log = get_logger("app.communication.dot4")


class Dot4Session:
    def __init__(self, usb: USBInterface, ep_out: int = PRINTER_EP_OUT, ep_in: int = PRINTER_EP_IN):
        self.usb = usb
        self.ep_out = ep_out
        self.ep_in = ep_in
        self.buffer = bytearray()
        self.sid_ctrl: Optional[int] = None
        self.ctrl_credits: int = 0
        self.is_active: bool = False

    def _flush_in(self):
        """Drain any residual bytes from input buffer and USB bulk IN endpoint."""
        self.buffer.clear()
        start = time.time()
        while time.time() - start < 0.5:
            try:
                chunk = self.usb.read_bulk(self.ep_in, 1024, timeout_ms=30)
                if not chunk:
                    break
            except Exception:
                break

    def _read_exact(self, length: int, timeout_s: float = 3.0) -> bytes:
        start = time.time()
        while len(self.buffer) < length:
            if time.time() - start > timeout_s:
                raise DeviceTimeoutError(f"Timeout waiting for {length} bytes (buffer: {len(self.buffer)})")
            try:
                chunk = self.usb.read_bulk(self.ep_in, 512, timeout_ms=100)
                if chunk:
                    self.buffer.extend(chunk)
                else:
                    time.sleep(0.01)
            except Exception:
                time.sleep(0.01)
        res = bytes(self.buffer[:length])
        del self.buffer[:length]
        return res

    def read_packet(self, timeout_s: float = 3.0) -> Tuple[int, int, bytes, int, int]:
        """
        Read a single D4 packet (6-byte header + payload) with sliding window sync validation.
        Prevents desynchronization caused by unsolicited ASCII status packets (@BDC ST2).
        """
        start = time.time()
        while time.time() - start < timeout_s:
            if len(self.buffer) < 6:
                try:
                    chunk = self.usb.read_bulk(self.ep_in, 512, timeout_ms=100)
                    if chunk:
                        self.buffer.extend(chunk)
                    else:
                        time.sleep(0.01)
                except Exception:
                    time.sleep(0.01)
                continue

            # Peek at potential D4 header
            psid, ssid, length, credit, control = struct.unpack(">BBHBB", self.buffer[:6])

            # IEEE 1284.4 Header Validation:
            # - Point-to-point socket connections always have psid == ssid (and <= 32)
            # - Control flags only use bits 0 and 1 in standard 1284.4 (control <= 3)
            # - Length must be at least header size (6 bytes) and <= max USB packet size (1024 bytes)
            if psid > 32 or ssid > 32 or psid != ssid or control > 3 or length < 6 or length > 1024:
                # Corrupted, desynchronized, or ASCII text in buffer; slide window forward by 1 byte
                del self.buffer[0]
                continue

            # Valid header shape found; ensure entire payload is read
            payload_timed_out = False
            while len(self.buffer) < length:
                if time.time() - start > timeout_s:
                    payload_timed_out = True
                    break
                try:
                    chunk = self.usb.read_bulk(self.ep_in, 512, timeout_ms=50)
                    if chunk:
                        self.buffer.extend(chunk)
                    else:
                        time.sleep(0.01)
                except Exception:
                    time.sleep(0.01)

            if payload_timed_out:
                # False positive header match; slide window forward by 1 byte and continue
                del self.buffer[0]
                continue

            # Consume the validated packet
            packet_data = bytes(self.buffer[:length])
            del self.buffer[:length]

            psid, ssid, length, credit, control = struct.unpack(">BBHBB", packet_data[:6])
            payload = packet_data[6:length]
            return psid, ssid, payload, credit, control

        raise DeviceTimeoutError(f"Timeout waiting for valid D4 packet (buffer len: {len(self.buffer)})")

    def write_packet(self, psid: int, ssid: Optional[int] = None, payload: bytes = b"", credit: int = 1, control: int = 0):
        """Send a single D4 packet."""
        if ssid is None:
            ssid = psid
        length = 6 + len(payload)
        hdr = struct.pack(">BBHBB", psid, ssid, length, credit, control)
        self.usb.write_bulk(self.ep_out, hdr + payload, timeout_ms=2000)

    def d4_command(self, cmd_byte: int, payload: bytes = b"") -> bytes:
        """Send a command on Channel 0 and receive response."""
        self.write_packet(0, 0, bytes([cmd_byte]) + payload, credit=1, control=0)
        psid, ssid, resp_payload, credit, control = self.read_packet(timeout_s=3.0)
        if len(resp_payload) < 2:
            raise D4ProtocolError("D4 command response too short")
        if resp_payload[0] == 0x7F:
            err_code = resp_payload[1]
            raise D4ProtocolError(f"D4 command 0x{cmd_byte:02x} rejected with error", err_code)
        if resp_payload[0] != (cmd_byte | 0x80):
            raise D4ProtocolError(f"Unexpected D4 response byte 0x{resp_payload[0]:02x} for cmd 0x{cmd_byte:02x}")
        return resp_payload[2:]

    def start(self):
        """Initiate Dot4 multiplexed session and negotiate EPSON-CTRL channel."""
        self._flush_in()

        # Step 1: Mode switch to 1284.4
        self.usb.write_bulk(self.ep_out, D4_MODE_ENTRY_SEQUENCE, timeout_ms=1000)
        # Drain switch event and any residual status text
        start_t = time.time()
        while time.time() - start_t < 0.6:
            try:
                chunk = self.usb.read_bulk(self.ep_in, 512, timeout_ms=50)
                if chunk:
                    self.buffer.extend(chunk)
                    idx = self.buffer.find(b"\x00\x00\x00\x08")
                    if idx >= 0:
                        del self.buffer[: idx + 8]
                        break
            except Exception:
                break
        self.buffer.clear()

        # Step 2: D4 Init (0x00)
        self.d4_command(D4_CMD_INIT, b"\x10")

        # Step 3: GetSocketID for EPSON-CTRL
        resp = self.d4_command(D4_CMD_GET_SOCKET_ID, D4_SERVICE_EPSON_CTRL.encode("ascii"))
        self.sid_ctrl = resp[0]
        log.debug(f"Resolved {D4_SERVICE_EPSON_CTRL} to Socket ID {self.sid_ctrl}")

        # Step 4: OpenChannel
        open_req = struct.pack(">BBHHHH", self.sid_ctrl, self.sid_ctrl, 0xFFFF, 0xFFFF, 0xFFFF, 0xFFFF)
        resp = self.d4_command(D4_CMD_OPEN_CHANNEL, open_req)
        psid, ssid, mtu, max_cred, initial_cred = struct.unpack(">BBHHH", resp)
        self.ctrl_credits = initial_cred
        self.is_active = True
        log.info(f"Dot4 session active. Channel {self.sid_ctrl} opened (MTU: {mtu})")

    def ensure_ctrl_credits(self):
        """Request credits from printer if exhausted."""
        if self.ctrl_credits < 1:
            req = struct.pack(">BBH", self.sid_ctrl, self.sid_ctrl, 0x0100)
            resp = self.d4_command(D4_CMD_CREDIT_REQUEST, req)
            _, _, granted = struct.unpack(">BBH", resp)
            self.ctrl_credits += granted

    def send_ctrl(self, payload: bytes, timeout_s: float = 3.0, max_retries: int = 2) -> bytes:
        """Send command on EPSON-CTRL channel and receive reply with resilient retries."""
        if not self.is_active or self.sid_ctrl is None:
            raise D4ProtocolError("Dot4 session is not active")

        last_error = None
        for attempt in range(max_retries + 1):
            try:
                self.ensure_ctrl_credits()
                # Control=2 indicates End of Message (EOM)
                self.write_packet(self.sid_ctrl, self.sid_ctrl, payload, credit=1, control=2)
                self.ctrl_credits -= 1

                # Grant credit to printer so it can send reply
                credit_req = struct.pack(">BBH", self.sid_ctrl, self.sid_ctrl, 1)
                self.d4_command(D4_CMD_CREDIT, credit_req)

                # Read reply packet on ctrl channel
                psid, ssid, resp_payload, credit, control = self.read_packet(timeout_s=timeout_s)
                return resp_payload
            except Exception as e:
                last_error = e
                log.warning(f"send_ctrl attempt {attempt + 1}/{max_retries + 1} failed: {e}")
                self._flush_in()
                if attempt < max_retries:
                    time.sleep(0.05)
                    try:
                        self.ctrl_credits = 0
                        self.ensure_ctrl_credits()
                    except Exception:
                        pass

        raise D4ProtocolError(f"Failed to execute EPSON-CTRL command after {max_retries + 1} attempts: {last_error}") from last_error

    def close(self):
        """Cleanly close D4 channel and exit D4 mode."""
        if self.is_active:
            try:
                if self.sid_ctrl is not None:
                    req = struct.pack(">BB", self.sid_ctrl, self.sid_ctrl)
                    self.d4_command(D4_CMD_CLOSE_CHANNEL, req)
            except Exception:
                pass
            try:
                self.d4_command(D4_CMD_EXIT, b"")
            except Exception:
                pass
            try:
                self.usb.write_bulk(self.ep_out, D4_MODE_EXIT_SEQUENCE, timeout_ms=500)
            except Exception:
                pass
            self.is_active = False
            self.sid_ctrl = None
            log.info("Dot4 session closed cleanly")

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
