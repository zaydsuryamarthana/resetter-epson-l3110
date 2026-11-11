"""
Unit tests for Database Connection and Repositories.
"""

import unittest
import tempfile
from pathlib import Path
from datetime import datetime

from app.database.connection import DatabaseConnection
from app.database.repository import MaintenanceRepository, CounterSnapshotRepository
from app.models.maintenance import MaintenanceRecord
from app.models.counter import WastePadRecord, CounterReading
from app.core.constants import MaintenanceOperation, OperationResult, PadHealthStatus


class TestDatabaseSubsystem(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_maintenance.db"
        self.db_conn = DatabaseConnection(self.db_path)
        self.repo = MaintenanceRepository(self.db_conn)
        self.snapshot_repo = CounterSnapshotRepository(self.db_conn)

    def tearDown(self):
        self.db_conn.close()
        self.temp_dir.cleanup()

    def test_insert_and_get_records(self):
        rec1 = MaintenanceRecord(
            printer_model="Epson L3110 Series",
            serial_number="TEST123456",
            operation_type=MaintenanceOperation.READ_COUNTER,
            pre_counter_value=6346,
            post_counter_value=6346,
            status=OperationResult.SUCCESS,
        )
        rec2 = MaintenanceRecord(
            printer_model="Epson L3110 Series",
            serial_number="TEST123456",
            operation_type=MaintenanceOperation.RESET_MAIN_PAD,
            pre_counter_value=6346,
            post_counter_value=0,
            status=OperationResult.VERIFIED,
            notes="Reset sponge replaced",
        )

        id1 = self.repo.add_record(rec1)
        id2 = self.repo.add_record(rec2)

        self.assertIsNotNone(id1)
        self.assertIsNotNone(id2)

        records = self.repo.get_records(limit=10)
        self.assertEqual(len(records), 2)
        # Most recent first
        self.assertEqual(records[0].operation_type, MaintenanceOperation.RESET_MAIN_PAD)
        self.assertEqual(records[0].status, OperationResult.VERIFIED)

    def test_get_latest_reset(self):
        rec1 = MaintenanceRecord(
            printer_model="Epson L3110 Series",
            serial_number="TEST123456",
            operation_type=MaintenanceOperation.READ_COUNTER,
            pre_counter_value=6346,
            status=OperationResult.SUCCESS,
        )
        rec2 = MaintenanceRecord(
            printer_model="Epson L3110 Series",
            serial_number="TEST123456",
            operation_type=MaintenanceOperation.RESET_MAIN_PAD,
            pre_counter_value=6346,
            post_counter_value=0,
            status=OperationResult.VERIFIED,
        )
        self.repo.add_record(rec1)
        self.repo.add_record(rec2)

        latest = self.repo.get_latest_reset("TEST123456")
        self.assertIsNotNone(latest)
        self.assertEqual(latest.operation_type, MaintenanceOperation.RESET_MAIN_PAD)
        self.assertEqual(latest.post_counter_value, 0)

    def test_export_json_and_csv(self):
        rec = MaintenanceRecord(
            printer_model="Epson L3110 Series",
            serial_number="TEST123456",
            operation_type=MaintenanceOperation.RESET_ALL,
            pre_counter_value=6346,
            post_counter_value=0,
            status=OperationResult.VERIFIED,
        )
        self.repo.add_record(rec)

        json_file = Path(self.temp_dir.name) / "export.json"
        csv_file = Path(self.temp_dir.name) / "export.csv"

        count_json = self.repo.export_to_json(json_file)
        count_csv = self.repo.export_to_csv(csv_file)

        self.assertEqual(count_json, 1)
        self.assertEqual(count_csv, 1)
        self.assertTrue(json_file.exists())
        self.assertTrue(csv_file.exists())


if __name__ == "__main__":
    unittest.main()
