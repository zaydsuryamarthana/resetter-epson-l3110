"""
Data Repositories for Maintenance Records and Counter Snapshots.
"""

import json
import csv
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
from app.database.connection import DatabaseConnection
from app.models.maintenance import MaintenanceRecord
from app.models.counter import WastePadRecord, CounterReading
from app.core.constants import MaintenanceOperation, OperationResult, PadHealthStatus
from app.core.logger import get_logger
from app.core.exceptions import DatabaseError

log = get_logger("app.database.repository")


class MaintenanceRepository:
    def __init__(self, db_conn: Optional[DatabaseConnection] = None):
        self.db = db_conn or DatabaseConnection.get_instance()

    def add_record(self, record: MaintenanceRecord) -> int:
        """Insert a new maintenance record and return its ID."""
        conn = self.db.get_connection()
        query = """
        INSERT INTO maintenance_records (
            timestamp, printer_model, serial_number, operation_type,
            pre_counter_value, post_counter_value, status, error_message, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
        """
        try:
            with conn:
                cursor = conn.execute(query, (
                    record.timestamp.isoformat(),
                    record.printer_model,
                    record.serial_number,
                    record.operation_type.value,
                    record.pre_counter_value,
                    record.post_counter_value,
                    record.status.value,
                    record.error_message,
                    record.notes,
                ))
                record.id = cursor.lastrowid
                log.info(f"Saved maintenance record id={record.id} [{record.operation_type.value}: {record.status.value}]")
                return record.id
        except Exception as e:
            log.error(f"Failed to insert maintenance record: {e}")
            raise DatabaseError(f"Failed to insert maintenance record: {e}") from e

    def get_records(self, limit: int = 100, offset: int = 0) -> List[MaintenanceRecord]:
        """Fetch maintenance records sorted by timestamp descending."""
        conn = self.db.get_connection()
        query = """
        SELECT id, timestamp, printer_model, serial_number, operation_type,
               pre_counter_value, post_counter_value, status, error_message, notes
        FROM maintenance_records
        ORDER BY timestamp DESC
        LIMIT ? OFFSET ?;
        """
        try:
            cursor = conn.execute(query, (limit, offset))
            rows = cursor.fetchall()
            results = []
            for row in rows:
                results.append(MaintenanceRecord(
                    id=row["id"],
                    timestamp=datetime.fromisoformat(row["timestamp"]),
                    printer_model=row["printer_model"],
                    serial_number=row["serial_number"],
                    operation_type=MaintenanceOperation(row["operation_type"]),
                    pre_counter_value=row["pre_counter_value"],
                    post_counter_value=row["post_counter_value"],
                    status=OperationResult(row["status"]),
                    error_message=row["error_message"],
                    notes=row["notes"],
                ))
            return results
        except Exception as e:
            log.error(f"Failed to query maintenance records: {e}")
            raise DatabaseError(f"Failed to query records: {e}") from e

    def get_latest_reset(self, serial_number: str) -> Optional[MaintenanceRecord]:
        """Fetch the most recent reset record for a given printer serial."""
        conn = self.db.get_connection()
        query = """
        SELECT id, timestamp, printer_model, serial_number, operation_type,
               pre_counter_value, post_counter_value, status, error_message, notes
        FROM maintenance_records
        WHERE serial_number = ? AND operation_type IN ('RESET_MAIN_PAD', 'RESET_PLATEN_PAD', 'RESET_ALL')
        ORDER BY timestamp DESC
        LIMIT 1;
        """
        try:
            cursor = conn.execute(query, (serial_number,))
            row = cursor.fetchone()
            if not row:
                return None
            return MaintenanceRecord(
                id=row["id"],
                timestamp=datetime.fromisoformat(row["timestamp"]),
                printer_model=row["printer_model"],
                serial_number=row["serial_number"],
                operation_type=MaintenanceOperation(row["operation_type"]),
                pre_counter_value=row["pre_counter_value"],
                post_counter_value=row["post_counter_value"],
                status=OperationResult(row["status"]),
                error_message=row["error_message"],
                notes=row["notes"],
            )
        except Exception as e:
            log.error(f"Failed to query latest reset for {serial_number}: {e}")
            return None

    def export_to_json(self, file_path: Path) -> int:
        """Export all maintenance records to a JSON file."""
        records = self.get_records(limit=10000)
        data = [r.to_dict() for r in records]
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return len(data)

    def export_to_csv(self, file_path: Path) -> int:
        """Export all maintenance records to a CSV file."""
        records = self.get_records(limit=10000)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        fieldnames = [
            "id", "timestamp", "printer_model", "serial_number",
            "operation_type", "pre_counter_value", "post_counter_value",
            "status", "error_message", "notes"
        ]
        with open(file_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for r in records:
                writer.writerow(r.to_dict())
        return len(records)

    def clear_history(self) -> int:
        """Clear all records from database."""
        conn = self.db.get_connection()
        with conn:
            cursor = conn.execute("DELETE FROM maintenance_records;")
            return cursor.rowcount


class CounterSnapshotRepository:
    def __init__(self, db_conn: Optional[DatabaseConnection] = None):
        self.db = db_conn or DatabaseConnection.get_instance()

    def save_snapshot(self, serial_number: str, record: WastePadRecord, raw_telemetry: str = "") -> int:
        conn = self.db.get_connection()
        query = """
        INSERT INTO counter_snapshots (
            timestamp, serial_number, main_pad_points, main_pad_pct,
            platen_pad_points, platen_pad_pct, overall_pct, raw_telemetry
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """
        try:
            with conn:
                cursor = conn.execute(query, (
                    record.timestamp.isoformat(),
                    serial_number,
                    record.main_pad.current_points,
                    record.main_pad.percentage,
                    record.platen_pad.current_points,
                    record.platen_pad.percentage,
                    record.overall_percentage,
                    raw_telemetry,
                ))
                return cursor.lastrowid
        except Exception as e:
            log.error(f"Failed to save counter snapshot: {e}")
            raise DatabaseError(f"Failed to save snapshot: {e}") from e
