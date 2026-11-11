"""
Printer Data Models.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional, Dict, Any
from app.core.constants import ConnectionStatus, EPSON_VENDOR_ID, SUPPORTED_DEVICES


@dataclass
class PrinterInfo:
    manufacturer: str = "Unknown"
    model: str = "Unknown"
    vendor_id: int = 0
    product_id: int = 0
    serial_number: str = "Unknown"
    firmware_version: str = "Unknown"
    device_id_raw: str = ""
    connection_status: ConnectionStatus = ConnectionStatus.DISCONNECTED
    bus_number: Optional[int] = None
    device_address: Optional[int] = None
    total_pages_printed: Optional[int] = None
    color_pages: Optional[int] = None
    monochrome_pages: Optional[int] = None
    scan_count: Optional[int] = None
    ink_levels: Dict[str, Any] = field(default_factory=dict)
    connected_at: Optional[datetime] = None

    @property
    def is_l3110(self) -> bool:
        """Verify whether this device matches Epson L3110 specification."""
        return self.vendor_id == EPSON_VENDOR_ID and self.product_id == 0x1142

    @property
    def is_connected(self) -> bool:
        return self.connection_status == ConnectionStatus.CONNECTED

    def to_dict(self) -> Dict[str, Any]:
        res = asdict(self)
        if self.connected_at:
            res["connected_at"] = self.connected_at.isoformat()
        res["connection_status"] = self.connection_status.value
        return res

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PrinterInfo":
        cleaned = dict(data)
        if "connected_at" in cleaned and cleaned["connected_at"]:
            if isinstance(cleaned["connected_at"], str):
                cleaned["connected_at"] = datetime.fromisoformat(cleaned["connected_at"])
        if "connection_status" in cleaned:
            cleaned["connection_status"] = ConnectionStatus(cleaned["connection_status"])
        return cls(**cleaned)


@dataclass
class DeviceStatus:
    is_connected: bool = False
    status_text: str = "No printer detected"
    error_state: Optional[str] = None
    last_update: datetime = field(default_factory=datetime.now)
