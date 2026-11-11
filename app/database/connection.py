"""
SQLite Connection Manager and Schema Migrator.
"""

import sqlite3
import threading
from pathlib import Path
from typing import Optional
from app.core.config import config
from app.core.logger import get_logger
from app.core.exceptions import DatabaseError

log = get_logger("app.database.connection")

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS maintenance_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    printer_model TEXT NOT NULL,
    serial_number TEXT NOT NULL,
    operation_type TEXT NOT NULL,
    pre_counter_value INTEGER NOT NULL,
    post_counter_value INTEGER,
    status TEXT NOT NULL,
    error_message TEXT,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS counter_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    serial_number TEXT NOT NULL,
    main_pad_points INTEGER NOT NULL,
    main_pad_pct REAL NOT NULL,
    platen_pad_points INTEGER NOT NULL,
    platen_pad_pct REAL NOT NULL,
    overall_pct REAL NOT NULL,
    raw_telemetry TEXT
);

CREATE INDEX IF NOT EXISTS idx_records_serial ON maintenance_records(serial_number);
CREATE INDEX IF NOT EXISTS idx_records_timestamp ON maintenance_records(timestamp);
CREATE INDEX IF NOT EXISTS idx_snapshots_serial ON counter_snapshots(serial_number);
"""


class DatabaseConnection:
    _instance: Optional["DatabaseConnection"] = None
    _lock = threading.Lock()

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or config.db_path
        self._local = threading.local()
        self.init_schema()

    @classmethod
    def get_instance(cls, db_path: Optional[Path] = None) -> "DatabaseConnection":
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls(db_path)
            return cls._instance

    def get_connection(self) -> sqlite3.Connection:
        """Get thread-local SQLite connection with WAL mode."""
        if not hasattr(self._local, "conn") or self._local.conn is None:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            try:
                conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
                conn.row_factory = sqlite3.Row
                conn.execute("PRAGMA journal_mode=WAL;")
                conn.execute("PRAGMA synchronous=NORMAL;")
                conn.execute("PRAGMA foreign_keys=ON;")
                self._local.conn = conn
            except sqlite3.Error as e:
                log.error(f"Failed to connect to database {self.db_path}: {e}")
                raise DatabaseError(f"Database connection error: {e}") from e
        return self._local.conn

    def init_schema(self):
        """Create tables and indexes if they do not exist."""
        conn = self.get_connection()
        try:
            with conn:
                conn.executescript(SCHEMA_SQL)
            log.debug(f"Database schema initialized at {self.db_path}")
        except sqlite3.Error as e:
            log.error(f"Failed to initialize database schema: {e}")
            raise DatabaseError(f"Failed to initialize schema: {e}") from e

    def close(self):
        """Close thread-local connection."""
        if hasattr(self._local, "conn") and self._local.conn is not None:
            try:
                self._local.conn.close()
            except Exception:
                pass
            self._local.conn = None
