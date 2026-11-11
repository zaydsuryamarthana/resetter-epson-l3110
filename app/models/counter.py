"""
Waste Ink Pad Counter Data Models.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional, Dict, Any
from app.core.constants import (
    PadHealthStatus,
    MAIN_PAD_MAX_POINTS,
    PLATEN_PAD_MAX_POINTS,
    PAD_WARNING_PERCENT,
    PAD_CRITICAL_PERCENT,
)


@dataclass
class CounterReading:
    counter_name: str
    current_points: int
    max_points: int
    percentage: float
    status: PadHealthStatus = PadHealthStatus.UNKNOWN
    last_read_time: datetime = field(default_factory=datetime.now)
    raw_hex: str = ""

    def __post_init__(self):
        if self.max_points > 0:
            calc_pct = (self.current_points / self.max_points) * 100.0
            # If percentage not set or default, use calculated
            if self.percentage <= 0.0 and self.current_points > 0:
                self.percentage = round(calc_pct, 1)

        # Determine status if unknown
        if self.status == PadHealthStatus.UNKNOWN:
            if self.percentage >= PAD_CRITICAL_PERCENT:
                self.status = PadHealthStatus.CRITICAL
            elif self.percentage >= PAD_WARNING_PERCENT:
                self.status = PadHealthStatus.WARNING
            else:
                self.status = PadHealthStatus.NORMAL

    def to_dict(self) -> Dict[str, Any]:
        return {
            "counter_name": self.counter_name,
            "current_points": self.current_points,
            "max_points": self.max_points,
            "percentage": self.percentage,
            "status": self.status.value,
            "last_read_time": self.last_read_time.isoformat(),
            "raw_hex": self.raw_hex,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CounterReading":
        return cls(
            counter_name=data["counter_name"],
            current_points=data["current_points"],
            max_points=data["max_points"],
            percentage=float(data.get("percentage", 0.0)),
            status=PadHealthStatus(data.get("status", PadHealthStatus.UNKNOWN.value)),
            last_read_time=datetime.fromisoformat(data["last_read_time"]) if "last_read_time" in data else datetime.now(),
            raw_hex=data.get("raw_hex", ""),
        )


@dataclass
class WastePadRecord:
    main_pad: CounterReading
    platen_pad: CounterReading
    overall_percentage: float
    overall_status: PadHealthStatus
    timestamp: datetime = field(default_factory=datetime.now)

    @classmethod
    def create_empty(cls) -> "WastePadRecord":
        now = datetime.now()
        main = CounterReading(
            counter_name="Main Waste Ink Pad",
            current_points=0,
            max_points=MAIN_PAD_MAX_POINTS,
            percentage=0.0,
            status=PadHealthStatus.UNKNOWN,
            last_read_time=now,
        )
        platen = CounterReading(
            counter_name="Platen Waste Ink Pad",
            current_points=0,
            max_points=PLATEN_PAD_MAX_POINTS,
            percentage=0.0,
            status=PadHealthStatus.UNKNOWN,
            last_read_time=now,
        )
        return cls(
            main_pad=main,
            platen_pad=platen,
            overall_percentage=0.0,
            overall_status=PadHealthStatus.UNKNOWN,
            timestamp=now,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "main_pad": self.main_pad.to_dict(),
            "platen_pad": self.platen_pad.to_dict(),
            "overall_percentage": self.overall_percentage,
            "overall_status": self.overall_status.value,
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WastePadRecord":
        return cls(
            main_pad=CounterReading.from_dict(data["main_pad"]),
            platen_pad=CounterReading.from_dict(data["platen_pad"]),
            overall_percentage=float(data.get("overall_percentage", 0.0)),
            overall_status=PadHealthStatus(data.get("overall_status", PadHealthStatus.UNKNOWN.value)),
            timestamp=datetime.fromisoformat(data["timestamp"]) if "timestamp" in data else datetime.now(),
        )
