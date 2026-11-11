"""
Live Hardware Integration Tests for Epson EcoTank L3110.
Executes against the connected physical printer.
"""

import unittest
from app.communication.libusb_backend import LibUSBBackend
from app.communication.dot4_protocol import Dot4Session
from app.communication.epson_ctrl_transport import EpsonCtrlTransport
from app.services.device_manager import DeviceManager
from app.services.printer_service import PrinterService
from app.services.counter_service import CounterService
from app.services.diagnostics_service import DiagnosticsService
from app.services.reset_service import ResetService
from app.core.constants import EPSON_VENDOR_ID, PRINTER_INTERFACE_INDEX, MaintenanceOperation
from app.core.exceptions import SafetyGateError


class TestPhysicalHardwareIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.usb = LibUSBBackend()
        # Verify physical device is present
        devs = cls.usb.find_devices(EPSON_VENDOR_ID, 0x1142)
        if not devs:
            raise unittest.SkipTest("No physical Epson L3110 connected to host. Skipping hardware test.")

    def setUp(self):
        self.usb = LibUSBBackend()

    def tearDown(self):
        self.usb.close()

    def test_01_usb_enumeration_and_open(self):
        """Test physical USB open, kernel detach, and claim on Interface 1."""
        self.usb.open_device(EPSON_VENDOR_ID, 0x1142)
        self.assertTrue(self.usb.is_open())
        self.usb.claim_interface(PRINTER_INTERFACE_INDEX)
        self.usb.release_interface(PRINTER_INTERFACE_INDEX)
        self.usb.close()

    def test_02_d4_session_handshake(self):
        """Test IEEE 1284.4 Dot4 session start, channel negotiation, and clean close."""
        self.usb.open_device(EPSON_VENDOR_ID, 0x1142)
        self.usb.claim_interface(PRINTER_INTERFACE_INDEX)

        session = Dot4Session(self.usb)
        session.start()
        self.assertTrue(session.is_active)
        self.assertIsNotNone(session.sid_ctrl)
        self.assertEqual(session.sid_ctrl, 2)  # Socket 2 is EPSON-CTRL
        session.close()
        self.assertFalse(session.is_active)
        self.usb.close()

    def test_03_firmware_and_device_id(self):
        """Test reading firmware version string and IEEE 1284 device descriptor."""
        self.usb.open_device(EPSON_VENDOR_ID, 0x1142)
        self.usb.claim_interface(PRINTER_INTERFACE_INDEX)

        with Dot4Session(self.usb) as session:
            transport = EpsonCtrlTransport(session)
            fw = transport.get_firmware_version()
            dev_id = transport.get_device_id()

            self.assertIsInstance(fw, str)
            self.assertTrue(len(fw) >= 4)
            self.assertEqual(fw, "VC15N9")

            self.assertIn("MFG:EPSON", dev_id)
            self.assertIn("L3110", dev_id)

        self.usb.close()

    def test_04_status_tlv_and_serial_number(self):
        """Test reading status TLVs: Serial Number (Tag 0x40), Page counts (Tag 0x36), and Pad % (Tag 0x4B)."""
        self.usb.open_device(EPSON_VENDOR_ID, 0x1142)
        self.usb.claim_interface(PRINTER_INTERFACE_INDEX)

        with Dot4Session(self.usb) as session:
            transport = EpsonCtrlTransport(session)
            tlvs = transport.get_status_tlv()

            self.assertIn(0x40, tlvs)
            serial = tlvs[0x40].decode("ascii", errors="replace").strip()
            self.assertEqual(len(serial), 10)
            self.assertTrue(serial.isalnum())

            self.assertIn(0x4B, tlvs)
            pad_pct = tlvs[0x4B][0]
            self.assertEqual(pad_pct, 37)

            pages = transport.parse_page_counters(tlvs)
            self.assertGreater(pages["total_pages"], 0)
            self.assertGreaterEqual(pages["total_pages"], 2597)

        self.usb.close()

    def test_05_counter_telemetry(self):
        """Test reading live 73-byte counter telemetry structure."""
        svc = CounterService(self.usb)
        record = svc.read_waste_pad_counters(EPSON_VENDOR_ID, 0x1142)

        self.assertEqual(record.main_pad.counter_name, "Main Waste Ink Pad")
        self.assertGreaterEqual(record.main_pad.current_points, 6346)
        self.assertEqual(record.main_pad.max_points, 17151)
        self.assertAlmostEqual(record.main_pad.percentage, 37.0, delta=2.0)

        self.assertEqual(record.platen_pad.counter_name, "Platen Waste Ink Pad")
        self.assertEqual(record.platen_pad.current_points, 1066)
        self.assertEqual(record.platen_pad.max_points, 17151)
        self.assertEqual(record.platen_pad.percentage, 6.2)

    def test_06_diagnostics_service_pipeline(self):
        """Test complete automated diagnostics pipeline on physical hardware."""
        diag_svc = DiagnosticsService(self.usb)
        result = diag_svc.run_diagnostics(EPSON_VENDOR_ID, 0x1142)

        self.assertTrue(result.usb_connection_ok)
        self.assertTrue(result.device_id_match)
        self.assertTrue(result.d4_handshake_ok)
        self.assertTrue(result.ctrl_channel_ok)
        self.assertTrue(result.counter_readable)
        self.assertTrue(result.all_passed)

    def test_07_safety_gate_blocking_on_hardware(self):
        """Verify that reset cannot be triggered without explicit user confirmation."""
        reset_svc = ResetService(usb_backend=self.usb)
        with self.assertRaises(SafetyGateError):
            reset_svc.execute_reset(
                vendor_id=EPSON_VENDOR_ID,
                product_id=0x1142,
                serial_number="TEST123456",
                operation=MaintenanceOperation.RESET_MAIN_PAD,
                user_confirmed_sponge_serviced=False,  # Should raise SafetyGateError
            )


if __name__ == "__main__":
    unittest.main()
