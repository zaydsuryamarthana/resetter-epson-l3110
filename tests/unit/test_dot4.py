"""
Unit tests for IEEE 1284.4 (Dot4) Protocol Multiplexing Engine.
Tests header validation, sliding window synchronization, and resilience against unsolicited status text.
"""

import unittest
import struct
from app.communication.dot4_protocol import Dot4Session
from app.core.exceptions import DeviceTimeoutError


class MockUSBForDot4:
    def __init__(self, in_chunks=None):
        self.in_chunks = list(in_chunks or [])
        self.out_packets = []

    def read_bulk(self, ep, length, timeout_ms=1000):
        if self.in_chunks:
            return self.in_chunks.pop(0)
        return b""

    def write_bulk(self, ep, data, timeout_ms=1000):
        self.out_packets.append((ep, bytes(data)))
        return len(data)


class TestDot4Protocol(unittest.TestCase):
    def test_clean_packet_read(self):
        """Valid D4 packet (6B header + 4B payload) is decoded properly."""
        # psid=2, ssid=2, length=10 (6 header + 4 payload), credit=1, control=2
        raw_header = struct.pack(">BBHBB", 2, 2, 10, 1, 2)
        payload = b"TEST"
        usb = MockUSBForDot4([raw_header + payload])
        session = Dot4Session(usb)

        psid, ssid, ret_payload, credit, control = session.read_packet(timeout_s=1.0)
        self.assertEqual(psid, 2)
        self.assertEqual(ssid, 2)
        self.assertEqual(ret_payload, b"TEST")
        self.assertEqual(credit, 1)
        self.assertEqual(control, 2)

    def test_sliding_window_resync_on_ascii_junk(self):
        """
        Simulate unsolicited ASCII status packet (@BDC ST2\r\n...) followed by valid D4 packet.
        The parser must slide the window past the ASCII text and successfully recover the D4 packet.
        """
        ascii_junk = b"@BDC ST2\r\n00:01:04;\r\n"
        # Valid packet: psid=0, ssid=0, length=8 (6 + 2), credit=1, control=0, payload=0x80 0x00
        valid_packet = struct.pack(">BBHBB", 0, 0, 8, 1, 0) + b"\x80\x00"
        usb = MockUSBForDot4([ascii_junk + valid_packet])
        session = Dot4Session(usb)

        psid, ssid, ret_payload, credit, control = session.read_packet(timeout_s=1.0)
        self.assertEqual(psid, 0)
        self.assertEqual(ssid, 0)
        self.assertEqual(ret_payload, b"\x80\x00")

    def test_invalid_length_sliding_window(self):
        """
        Simulate corrupt bytes that would produce huge bogus length (>2048).
        Must be dropped via sliding window without causing 65KB timeout hang.
        """
        # Corrupt 6 bytes: psid=0, ssid=0, length=60000, credit=0, control=0
        corrupt_header = struct.pack(">BBHBB", 0, 0, 60000, 0, 0)
        # Followed by valid packet
        valid_packet = struct.pack(">BBHBB", 1, 1, 6, 1, 0)
        usb = MockUSBForDot4([corrupt_header + valid_packet])
        session = Dot4Session(usb)

        psid, ssid, ret_payload, credit, control = session.read_packet(timeout_s=1.0)
        self.assertEqual(psid, 1)
        self.assertEqual(ssid, 1)
        self.assertEqual(ret_payload, b"")


if __name__ == "__main__":
    unittest.main()
