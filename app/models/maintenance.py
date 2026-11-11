"""
Maintenance, Audit, and Diagnostic Data Models.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional, Dict, Any
from app.core.constants import MaintenanceOperation, OperationResult


@dataclass
class MaintenanceRecord:
    id: Optional[int] = None
    timestamp: datetime = field(default_factory=datetime.now)
    printer_model: str = "Epson L3110 Series"
    serial_number: str = "Unknown"
    operation_type: MaintenanceOperation = MaintenanceOperation.READ_COUNTER
    pre_counter_value: int = 0
    post_counter_value: Optional[int] = None
    status: OperationResult = OperationResult.SUCCESS
    error_message: Optional[str] = None
    notes: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "printer_model": self.printer_model,
            "serial_number": self.serial_number,
            "operation_type": self.operation_type.value,
            "pre_counter_value": self.pre_counter_value,
            "post_counter_value": self.post_counter_value,
            "status": self.status.value,
            "error_message": self.error_message,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MaintenanceRecord":
        return cls(
            id=data.get("id"),
            timestamp=datetime.fromisoformat(data["timestamp"]) if "timestamp" in data else datetime.now(),
            printer_model=data.get("printer_model", "Unknown"),
            serial_number=data.get("serial_number", "Unknown"),
            operation_type=MaintenanceOperation(data["operation_type"]),
            pre_counter_value=int(data.get("pre_counter_value", 0)),
            post_counter_value=int(data["post_counter_value"]) if data.get("post_counter_value") is not None else None,
            status=OperationResult(data.get("status", OperationResult.SUCCESS.value)),
            error_message=data.get("error_message"),
            notes=data.get("notes"),
        )


@dataclass
class DiagnosticResult:
    usb_connection_ok: bool = False
    device_id_match: bool = False
    d4_handshake_ok: bool = False
    ctrl_channel_ok: bool = False
    counter_readable: bool = False
    timestamp: datetime = field(default_factory=datetime.now)
    details: Dict[str, Any] = field(default_factory=dict)

    @property
    def all_passed(self) -> bool:
        return (
            self.usb_connection_ok
            and self.device_id_match
            and self.d4_handshake_ok
            and self.ctrl_channel_ok
            and self.counter_readable
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "usb_connection_ok": self.usb_connection_ok,
            "device_id_match": self.device_id_match,
            "d4_handshake_ok": self.d4_handshake_ok,
            "ctrl_channel_ok": self.ctrl_channel_ok,
            "counter_readable": self.counter_readable,
            "all_passed": self.all_passed,
            "timestamp": self.timestamp.isoformat(),
            "details": self.details,
        }
