"""
Application Configuration and Path Management.
"""

import os
import sys
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional


def _get_default_app_dir() -> Path:
    env_path = os.environ.get("EPSON_RESETTER_HOME")
    if env_path:
        return Path(env_path)
    home_app = Path.home() / ".epson_resetter"
    try:
        home_app.mkdir(parents=True, exist_ok=True)
        return home_app
    except OSError:
        # Fallback to local workspace or /tmp if home is read-only
        local_app = Path.cwd() / ".app_data"
        return local_app


@dataclass
class AppConfig:
    # Base Directories
    app_dir: Path = field(default_factory=_get_default_app_dir)
    data_dir: Path = field(init=False)
    log_dir: Path = field(init=False)
    db_path: Path = field(init=False)
    log_file: Path = field(init=False)

    # Operational Settings
    usb_poll_interval_ms: int = 1500
    usb_timeout_ms: int = 2000
    theme_mode: str = "dark"  # "dark" or "light"
    strict_safety_gate: bool = True
    auto_refresh_counters_on_connect: bool = True
    debug_mode: bool = False

    def __post_init__(self):
        self.data_dir = self.app_dir / "data"
        self.log_dir = self.app_dir / "logs"
        self.db_path = self.data_dir / "maintenance.db"
        self.log_file = self.log_dir / "app.log"
        self.ensure_directories()

    def ensure_directories(self):
        """Ensure all runtime directories exist."""
        try:
            self.app_dir.mkdir(parents=True, exist_ok=True)
            self.data_dir.mkdir(parents=True, exist_ok=True)
            self.log_dir.mkdir(parents=True, exist_ok=True)
        except OSError:
            pass


# Global singleton configuration
config = AppConfig()
