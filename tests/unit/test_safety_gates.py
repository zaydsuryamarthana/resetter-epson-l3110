"""
Unit tests for Safety Gates and Reset Service.
"""

import unittest
from app.services.reset_service import ResetService
from app.core.exceptions import SafetyGateError
from app.core.constants import MaintenanceOperation, EPSON_VENDOR_ID


class MockUSB:
    def find_devices(self, vid, pid=None):
        return [(vid, pid or 0x1142, "TEST123456")]
    def open_device(self, vid, pid, serial=None):
        pass
    def claim_interface(self, idx):
        pass
    def release_interface(self, idx):
        pass
    def close(self):
        pass
    def is_open(self):
        return True


class TestSafetyGates(unittest.TestCase):
    def setUp(self):
        self.reset_svc = ResetService(usb_backend=MockUSB())

    def test_sponge_confirmation_safety_gate(self):
        """Reset must fail if user has not confirmed physical sponge service."""
        with self.assertRaises(SafetyGateError) as ctx:
            self.reset_svc.execute_reset(
                vendor_id=EPSON_VENDOR_ID,
                product_id=0x1142,
                serial_number="TEST123456",
                operation=MaintenanceOperation.RESET_MAIN_PAD,
                user_confirmed_sponge_serviced=False,
            )
        self.assertIn("User has not confirmed physical inspection", str(ctx.exception))

    def test_wrong_device_id_safety_gate(self):
        """Reset must fail if device PID is not 0x1142."""
        with self.assertRaises(SafetyGateError) as ctx:
            self.reset_svc.execute_reset(
                vendor_id=EPSON_VENDOR_ID,
                product_id=0x9999,  # Wrong PID
                serial_number="TEST123456",
                operation=MaintenanceOperation.RESET_MAIN_PAD,
                user_confirmed_sponge_serviced=True,
            )
        self.assertIn("not a verified Epson L3110", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
