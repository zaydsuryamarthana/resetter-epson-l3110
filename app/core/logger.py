"""
Structured Logging Subsystem.
"""

import sys
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional, List, Callable
from app.core.config import config

LOG_FORMAT = "[%(asctime)s] [%(levelname)-7s] [%(name)s]: %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

_initialized = False
_gui_log_listeners: List[Callable[[str, int], None]] = []


class GuiLogHandler(logging.Handler):
    """Custom logging handler that forwards messages to GUI listeners."""
    def emit(self, record):
        msg = self.format(record)
        for listener in _gui_log_listeners:
            try:
                listener(msg, record.levelno)
            except Exception:
                pass


def add_gui_log_listener(callback: Callable[[str, int], None]):
    """Register a callback for live GUI log streaming."""
    if callback not in _gui_log_listeners:
        _gui_log_listeners.append(callback)


def remove_gui_log_listener(callback: Callable[[str, int], None]):
    """Remove a callback from live GUI log streaming."""
    if callback in _gui_log_listeners:
        _gui_log_listeners.remove(callback)


def setup_logging(level: int = logging.INFO, log_file: Optional[Path] = None):
    """Initialize root and application loggers."""
    global _initialized
    if _initialized:
        return

    target_log_file = log_file or config.log_file
    target_log_file.parent.mkdir(parents=True, exist_ok=True)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # File Handler (Rotating: 5MB max, 3 backups)
    file_handler = RotatingFileHandler(
        str(target_log_file),
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)

    # GUI Handler
    gui_handler = GuiLogHandler()
    gui_handler.setLevel(level)
    gui_handler.setFormatter(console_formatter)
    root_logger.addHandler(gui_handler)

    _initialized = True
    logging.getLogger("app.logger").info(f"Logging initialized. Log file: {target_log_file}")


def get_logger(name: str) -> logging.Logger:
    """Get a named application logger."""
    if not _initialized:
        setup_logging()
    return logging.getLogger(name)
