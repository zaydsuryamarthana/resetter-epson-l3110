"""
Unit tests for Protocol Parsers and Packet Decoding.
"""

import unittest
from app.communication.epson_ctrl_transport import EpsonCtrlTransport
from app.core.constants import MAIN_PAD_MAX_POINTS, PLATEN_PAD_MAX_POINTS
from app.models.counter import CounterReading, WastePadRecord


class MockDot4Session:
    def __init__(self, responses=None):
        self.responses = responses or {}

    def send_ctrl(self, payload: bytes, timeout_s: float = 3.0) -> bytes:
        cmd = payload[:2].decode("ascii", errors="replace")
        return self.responses.get(cmd, b"")


class TestProtocolParser(unittest.TestCase):
    def test_firmware_version_parsing(self):
        mock_session = MockDot4Session({"vi": b"vi:00:VC15N9;\x0c"})
        transport = EpsonCtrlTransport(mock_session)
        fw = transport.get_firmware_version()
        self.assertEqual(fw, "VC15N9")

    def test_device_id_parsing(self):
        raw_id = b"@EJL ID\r\nMFG:EPSON;MDL:L3110 Series;CLS:PRINTER;DES:EPSON L3110 Series;"
        mock_session = MockDot4Session({"di": raw_id})
        transport = EpsonCtrlTransport(mock_session)
        dev_id = transport.get_device_id()
        self.assertIn("MFG:EPSON", dev_id)
        self.assertIn("MDL:L3110 Series", dev_id)

    def test_status_tlv_parsing(self):
        # Real payload from hardware
        hex_st = (
            "40424443205354320d0ac30001010002011006020100"
            "0f0d03010069050369040269030169"
            "400a54455354313233343536"  # Tag 0x40 (Serial: TEST123456)
            "4b0125"                    # Tag 0x4B (0x25 = 37%)
        )
        mock_session = MockDot4Session({"st": bytes.fromhex(hex_st)})
        transport = EpsonCtrlTransport(mock_session)
        tlvs = transport.get_status_tlv()

        self.assertIn(0x40, tlvs)
        self.assertEqual(tlvs[0x40].decode("ascii"), "TEST123456")

        self.assertIn(0x4B, tlvs)
        self.assertEqual(tlvs[0x4B][0], 37)

    def test_counter_telemetry_parsing(self):
        # Real 93-byte cd:00 response from hardware
        hex_cd = (
            "404244432050530d0a63643a3030"  # Header (14 bytes)
            "4900"                          # 73 bytes LE length
            "ffffac2a003801ca180000ac2d0000ffff2fa30200ff102a040000ffffffff"
            "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"
            "ffffffffffffffff2f163b0c"
        )
        mock_session = MockDot4Session({"cd": bytes.fromhex(hex_cd)})
        transport = EpsonCtrlTransport(mock_session)
        body = transport.get_counter_telemetry()
        self.assertEqual(len(body), 73)

        # Main pad offset 7..11: ca 18 00 00 = 6346
        main_pad = int.from_bytes(body[7:11], "little")
        self.assertEqual(main_pad, 6346)

        # Platen pad offset 23..27: 2a 04 00 00 = 1066
        platen_pad = int.from_bytes(body[23:27], "little")
        self.assertEqual(platen_pad, 1066)

    def test_soft_reset_response(self):
        mock_session = MockDot4Session({"rs": b"rs:01:OK;\x0c"})
        transport = EpsonCtrlTransport(mock_session)
        self.assertTrue(transport.execute_soft_reset())

    def test_waste_pad_reset_rw_command(self):
        mock_session = MockDot4Session({"rw": b"@BDC PS\r\nrw:01:OK;\x0c"})
        transport = EpsonCtrlTransport(mock_session)
        self.assertTrue(transport.execute_waste_pad_reset("TEST123456"))


if __name__ == "__main__":
    unittest.main()
