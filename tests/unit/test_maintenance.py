"""
Unit tests for Universal Maintenance Service and Safety Gates.
Canonical packet verification matching Seiko Epson libescpr.so.
"""

import unittest
from unittest.mock import MagicMock
from app.services.maintenance_service import MaintenanceService
from app.services.counter_service import CounterService
from app.models.counter import WastePadRecord, CounterReading
from app.core.exceptions import SafetyGateError, DeviceBusyError
from app.core.constants import (
    EPSON_VENDOR_ID,
    MAINT_PACKET_HEAD_CLEANING,
    MAINT_PACKET_POWER_CLEANING,
    MAINT_PACKET_NOZZLE_CHECK,
    MAINT_PACKET_ALIGNMENT_SHEET,
    build_remote_packet,
    ESC_RESET_1284_4,
    ESC_INIT_PRINTER,
    ESC_ENTER_REMOTE1,
    ESC_EXIT_REMOTE1,
    ESC_REMOTE_JE,
    STATUS_STATE_CLEANING,
    STATUS_STATE_PRINTING,
    STATUS_STATE_IDLE,
    MaintenanceOperation,
    OperationResult,
    PadHealthStatus,
)


class MockUSBForMaintenance:
    def __init__(self):
        self.sent_packets = []
        self._is_open = False

    def open_device(self, vid, pid, serial=None):
        self._is_open = True

    def claim_interface(self, idx):
        pass

    def release_interface(self, idx):
        pass

    def write_bulk(self, ep, data, timeout_ms=5000):
        self.sent_packets.append((ep, bytes(data)))
        return len(data)

    def read_bulk(self, ep, length, timeout_ms=1000):
        return b""

    def close(self):
        self._is_open = False

    def is_open(self):
        return self._is_open


class TestMaintenanceService(unittest.TestCase):
    def setUp(self):
        self.mock_usb = MockUSBForMaintenance()
        self.mock_counter_svc = MagicMock(spec=CounterService)
        # Default mock counter: healthy (20% pad)
        self.mock_counter_svc.read_waste_pad_counters.return_value = WastePadRecord(
            main_pad=CounterReading("Main Pad", 3400, 17151, 19.8),
            platen_pad=CounterReading("Platen Pad", 500, 17151, 2.9),
            overall_percentage=19.8,
            overall_status=PadHealthStatus.NORMAL,
        )
        self.maintenance_svc = MaintenanceService(
            usb_backend=self.mock_usb,
            counter_service=self.mock_counter_svc,
        )

    def test_nozzle_check_packet(self):
        """Nozzle check must package canonical 112-byte packet and dispatch to EP 0x04."""
        record = self.maintenance_svc.perform_nozzle_check(
            vendor_id=EPSON_VENDOR_ID,
            product_id=0x1142,
            serial_number="TEST12345",
        )
        self.assertEqual(record.status, OperationResult.SUCCESS)
        self.assertEqual(record.operation_type, MaintenanceOperation.NOZZLE_CHECK)
        self.assertEqual(len(self.mock_usb.sent_packets), 1)

        ep, packet = self.mock_usb.sent_packets[0]
        self.assertEqual(ep, 0x04)
        self.assertEqual(len(packet), 112)
        self.assertEqual(packet, MAINT_PACKET_NOZZLE_CHECK)

    def test_head_cleaning_packet(self):
        """Head cleaning must send canonical 80-byte packet with RemoteJE."""
        record = self.maintenance_svc.perform_head_cleaning(
            vendor_id=EPSON_VENDOR_ID,
            product_id=0x1142,
            serial_number="TEST12345",
        )
        self.assertEqual(record.status, OperationResult.SUCCESS)
        self.assertEqual(record.operation_type, MaintenanceOperation.HEAD_CLEANING)
        self.assertEqual(len(self.mock_usb.sent_packets), 1)

        ep, packet = self.mock_usb.sent_packets[0]
        self.assertEqual(ep, 0x04)
        self.assertEqual(len(packet), 80)
        self.assertEqual(packet, MAINT_PACKET_HEAD_CLEANING)

    def test_power_cleaning_safety_gate_ink_unconfirmed(self):
        """Power cleaning must fail if ink level confirmation is not given."""
        with self.assertRaises(SafetyGateError) as ctx:
            self.maintenance_svc.perform_power_cleaning(
                vendor_id=EPSON_VENDOR_ID,
                product_id=0x1142,
                serial_number="TEST12345",
                confirmed_ink_level=False,
            )
        self.assertIn("tangki tinta terisi minimal", str(ctx.exception))
        self.assertEqual(len(self.mock_usb.sent_packets), 0)

    def test_power_cleaning_safety_gate_pad_overflow_risk(self):
        """Power cleaning must be blocked if waste pad level >= 85%."""
        # Simulate near-full pad (88.5%)
        self.mock_counter_svc.read_waste_pad_counters.return_value = WastePadRecord(
            main_pad=CounterReading("Main Pad", 15180, 17151, 88.5),
            platen_pad=CounterReading("Platen Pad", 1200, 17151, 7.0),
            overall_percentage=88.5,
            overall_status=PadHealthStatus.WARNING,
        )

        with self.assertRaises(SafetyGateError) as ctx:
            self.maintenance_svc.perform_power_cleaning(
                vendor_id=EPSON_VENDOR_ID,
                product_id=0x1142,
                serial_number="TEST12345",
                confirmed_ink_level=True,
            )
        self.assertIn("Kapasitas Waste Ink Pad saat ini 88.5%", str(ctx.exception))
        self.assertEqual(len(self.mock_usb.sent_packets), 0)

    def test_power_cleaning_success_when_safe(self):
        """Power cleaning proceeds when ink is confirmed and pad < 85%."""
        record = self.maintenance_svc.perform_power_cleaning(
            vendor_id=EPSON_VENDOR_ID,
            product_id=0x1142,
            serial_number="TEST12345",
            confirmed_ink_level=True,
        )
        self.assertEqual(record.status, OperationResult.SUCCESS)
        self.assertEqual(record.operation_type, MaintenanceOperation.POWER_CLEANING)
        self.assertEqual(len(self.mock_usb.sent_packets), 1)

        ep, packet = self.mock_usb.sent_packets[0]
        self.assertEqual(ep, 0x04)
        self.assertEqual(len(packet), 80)
        self.assertEqual(packet, MAINT_PACKET_POWER_CLEANING)

    def test_print_alignment_sheet(self):
        """Print alignment sheet sends canonical 113-byte evaluation packet."""
        record = self.maintenance_svc.print_alignment_sheet(
            vendor_id=EPSON_VENDOR_ID,
            product_id=0x1142,
            serial_number="TEST12345",
        )
        self.assertEqual(record.status, OperationResult.SUCCESS)
        self.assertEqual(record.operation_type, MaintenanceOperation.HEAD_ALIGNMENT)
        self.assertEqual(len(self.mock_usb.sent_packets), 1)

        ep, packet = self.mock_usb.sent_packets[0]
        self.assertEqual(ep, 0x04)
        self.assertEqual(len(packet), 113)
        self.assertEqual(packet, MAINT_PACKET_ALIGNMENT_SHEET)

    def test_apply_alignment_offset(self):
        """Apply alignment offset formats pattern pairs correctly with canonical envelope."""
        offsets = {1: 5, 2: 4, 3: 6}
        record = self.maintenance_svc.apply_alignment_offset(
            vendor_id=EPSON_VENDOR_ID,
            product_id=0x1142,
            serial_number="TEST12345",
            offsets=offsets,
        )
        self.assertEqual(record.status, OperationResult.SUCCESS)
        self.assertEqual(len(self.mock_usb.sent_packets), 1)

        ep, packet = self.mock_usb.sent_packets[0]
        self.assertTrue(packet.startswith(ESC_RESET_1284_4 + ESC_INIT_PRINTER + ESC_ENTER_REMOTE1 + b"AL"))
        self.assertTrue(packet.endswith(ESC_REMOTE_JE + ESC_EXIT_REMOTE1))


if __name__ == "__main__":
    unittest.main()
