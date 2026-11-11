"""
Core constants for Epson L3110 Resetter Application.
"""

from enum import Enum, auto

APP_NAME = "Epson L3110 Resetter"
APP_VERSION = "1.0.0"
APP_AUTHOR = "Antigravity Engineering"
APP_ORGANIZATION = "OpenPrinterLab"

# USB Identifiers
EPSON_VENDOR_ID = 0x04B8
SUPPORTED_DEVICES = {
    0x1142: "Epson EcoTank L3110 Series",
}

# Target USB Interface & Endpoints
PRINTER_INTERFACE_INDEX = 1
PRINTER_EP_OUT = 0x04
PRINTER_EP_IN = 0x83
PRINTER_PACKET_SIZE = 64

SCANNER_INTERFACE_INDEX = 0
SCANNER_EP_OUT = 0x02
SCANNER_EP_IN = 0x81

# IEEE 1284.4 (Dot4) Protocol Constants
D4_MODE_ENTRY_SEQUENCE = b"\x00\x00\x00\x1b\x01@EJL 1284.4\n@EJL\n@EJL\n"
D4_MODE_EXIT_SEQUENCE = b"\x1b\x01@EJL \n"

D4_CMD_INIT = 0x00
D4_CMD_OPEN_CHANNEL = 0x01
D4_CMD_CLOSE_CHANNEL = 0x02
D4_CMD_CREDIT = 0x03
D4_CMD_CREDIT_REQUEST = 0x04
D4_CMD_EXIT = 0x08
D4_CMD_GET_SOCKET_ID = 0x09

D4_SERVICE_EPSON_CTRL = "EPSON-CTRL"

# EPSON-CTRL Command Verbs
CMD_VERSION_INFO = "vi"
CMD_DEVICE_ID = "di"
CMD_STATUS = "st"
CMD_COUNTER_DATA = "cd"
CMD_RESET = "rs"
CMD_READ_WRITE = "rw"
CMD_PORT_CONFIG = "pc"
CMD_PAPER_MODE = "pm"

# Waste Ink Pad Thresholds
# Empirical calculation: 6346 points / 0.37 = ~17151 points rated full capacity
MAIN_PAD_MAX_POINTS = 17151
PLATEN_PAD_MAX_POINTS = 17151

PAD_WARNING_PERCENT = 80.0
PAD_CRITICAL_PERCENT = 100.0

# Universal Maintenance & Remote Mode Sequences (ESC/P2 & REMOTE1)
# Canonical ESC/P-R control primitives reverse-engineered from Seiko Epson libescpr.so:
ESC_RESET_1284_4 = b"\x00\x00\x00\x1b\x01@EJL 1284.4\n@EJL     \n"  # 27 bytes: Exit IEEE 1284.4 packet mode
ESC_INIT_PRINTER = b"\x1b@\x1b@"                                    # 4 bytes: ESC @ ESC @ reset/init
ESC_ENTER_REMOTE1 = b"\x1b(R\x08\x00\x00REMOTE1"                   # 13 bytes: Enter Remote1 mode
ESC_EXIT_REMOTE1 = b"\x1b\x00\x00\x00"                              # 4 bytes: Exit Remote1 mode
ESC_REMOTE_JE = b"JE\x01\x00\x00"                                   # 5 bytes: Mandatory Job End sequence

# Canonical Pre-assembled Packets:
MAINT_PACKET_HEAD_CLEANING = (
    ESC_RESET_1284_4
    + ESC_INIT_PRINTER
    + ESC_ENTER_REMOTE1
    + b"CH\x02\x00\x00\x00"
    + ESC_EXIT_REMOTE1
    + ESC_INIT_PRINTER
    + ESC_ENTER_REMOTE1
    + ESC_REMOTE_JE
    + ESC_EXIT_REMOTE1
)  # 80 bytes

MAINT_PACKET_POWER_CLEANING = (
    ESC_RESET_1284_4
    + ESC_INIT_PRINTER
    + ESC_ENTER_REMOTE1
    + b"CH\x02\x00\x03\x00"
    + ESC_EXIT_REMOTE1
    + ESC_INIT_PRINTER
    + ESC_ENTER_REMOTE1
    + ESC_REMOTE_JE
    + ESC_EXIT_REMOTE1
)  # 80 bytes

MAINT_PACKET_NOZZLE_CHECK = (
    ESC_RESET_1284_4
    + ESC_INIT_PRINTER
    + ESC_ENTER_REMOTE1
    + b"NC\x02\x00\x00\x00"
    + ESC_EXIT_REMOTE1
    + b"\r\n\r\n"
    + ESC_ENTER_REMOTE1
    + b"VI\x02\x00\x00\x00"
    + b"LD\x00\x00"
    + ESC_EXIT_REMOTE1
    + b"\x0c"
    + ESC_INIT_PRINTER
    + ESC_ENTER_REMOTE1
    + ESC_REMOTE_JE
    + ESC_EXIT_REMOTE1
)  # 112 bytes

MAINT_PACKET_ALIGNMENT_SHEET = (
    ESC_RESET_1284_4
    + ESC_INIT_PRINTER
    + ESC_ENTER_REMOTE1
    + b"DT\x03\x00\x00\x00\x00"
    + ESC_EXIT_REMOTE1
    + b"\r\n\r\n"
    + ESC_ENTER_REMOTE1
    + b"VI\x02\x00\x00\x00"
    + b"LD\x00\x00"
    + ESC_EXIT_REMOTE1
    + b"\x0c"
    + ESC_INIT_PRINTER
    + ESC_ENTER_REMOTE1
    + ESC_REMOTE_JE
    + ESC_EXIT_REMOTE1
)  # 113 bytes


def build_remote_packet(cmd_payload: bytes, is_page_print: bool = False) -> bytes:
    """Build a canonical ESC/P-R maintenance packet envelope with Job End termination."""
    if is_page_print:
        return (
            ESC_RESET_1284_4
            + ESC_INIT_PRINTER
            + ESC_ENTER_REMOTE1
            + cmd_payload
            + ESC_EXIT_REMOTE1
            + b"\r\n\r\n"
            + ESC_ENTER_REMOTE1
            + b"VI\x02\x00\x00\x00"
            + b"LD\x00\x00"
            + ESC_EXIT_REMOTE1
            + b"\x0c"
            + ESC_INIT_PRINTER
            + ESC_ENTER_REMOTE1
            + ESC_REMOTE_JE
            + ESC_EXIT_REMOTE1
        )
    else:
        return (
            ESC_RESET_1284_4
            + ESC_INIT_PRINTER
            + ESC_ENTER_REMOTE1
            + cmd_payload
            + ESC_EXIT_REMOTE1
            + ESC_INIT_PRINTER
            + ESC_ENTER_REMOTE1
            + ESC_REMOTE_JE
            + ESC_EXIT_REMOTE1
        )


# Legacy / Primitive aliases for backwards-compatibility
MAINT_ENTRY_REMOTE1 = b"\x1b\x01@EJL \n\x1b@\x1b(R\x08\x00\x00REMOTE1"
MAINT_CMD_NOZZLE_CHECK = b"NC\x02\x00\x00\x00"
MAINT_CMD_HEAD_CLEANING = b"CH\x02\x00\x00\x00"
MAINT_CMD_POWER_CLEANING = b"CH\x02\x00\x03\x00"
MAINT_CMD_ALIGNMENT_SHEET = b"DT\x03\x00\x00\x00\x00"
MAINT_EXIT_REMOTE1 = b"\x1b\x00\x00\x00"
MAINT_PAGE_EJECT = b"\r\n\x0c\x1b@"
MAINT_NON_PAGE_FINISH = b"\x1b@"

# BDC ST2 Status Codes (Tag 0x01)
STATUS_STATE_PRINTING = 0x02
STATUS_STATE_IDLE = 0x04
STATUS_STATE_ERROR = 0x06
STATUS_STATE_CLEANING = 0x07

# Power Cleaning Safety Thresholds
POWER_CLEANING_MAX_PAD_PERCENT = 85.0
POWER_CLEANING_MIN_INK_PERCENT = 30.0
POWER_CLEANING_COOLDOWN_HOURS = 12


class ConnectionStatus(str, Enum):
    DISCONNECTED = "Disconnected"
    CONNECTING = "Connecting"
    CONNECTED = "Connected"
    BUSY = "Busy"
    ERROR = "Error"


class PadHealthStatus(str, Enum):
    NORMAL = "Normal"
    WARNING = "Warning"
    CRITICAL = "Critical (Service Required)"
    UNKNOWN = "Unknown"


class MaintenanceOperation(str, Enum):
    READ_COUNTER = "READ_COUNTER"
    DIAGNOSTICS = "DIAGNOSTICS"
    RESET_MAIN_PAD = "RESET_MAIN_PAD"
    RESET_PLATEN_PAD = "RESET_PLATEN_PAD"
    RESET_ALL = "RESET_ALL"
    NOZZLE_CHECK = "NOZZLE_CHECK"
    HEAD_CLEANING = "HEAD_CLEANING"
    POWER_CLEANING = "POWER_CLEANING"
    HEAD_ALIGNMENT = "HEAD_ALIGNMENT"


class OperationResult(str, Enum):
    SUCCESS = "Success"
    FAILED = "Failed"
    VERIFIED = "Verified"
    CANCELLED = "Cancelled"
