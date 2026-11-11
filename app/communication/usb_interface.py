"""
Abstract USB Communication Interface.
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Tuple


class USBInterface(ABC):
    @abstractmethod
    def find_devices(self, vendor_id: int, product_id: Optional[int] = None) -> List[Tuple[int, int, str]]:
        """List connected devices matching vendor_id (and optional product_id). Returns list of (vid, pid, serial)."""
        pass

    @abstractmethod
    def open_device(self, vendor_id: int, product_id: int, serial_number: Optional[str] = None):
        """Open device handle."""
        pass

    @abstractmethod
    def claim_interface(self, interface_index: int):
        """Claim interface, detaching kernel driver if needed."""
        pass

    @abstractmethod
    def release_interface(self, interface_index: int):
        """Release claimed interface, re-attaching kernel driver if previously detached."""
        pass

    @abstractmethod
    def write_bulk(self, endpoint: int, data: bytes, timeout_ms: int = 2000) -> int:
        """Write data to bulk endpoint. Returns number of bytes transferred."""
        pass

    @abstractmethod
    def read_bulk(self, endpoint: int, length: int = 512, timeout_ms: int = 2000) -> bytes:
        """Read data from bulk endpoint. Returns bytes read."""
        pass

    @abstractmethod
    def close(self):
        """Close device handle and release resources."""
        pass

    @abstractmethod
    def is_open(self) -> bool:
        """Check if device is currently open."""
        pass
