"""
Custom Exception Hierarchy for Epson L3110 Resetter.
"""

class AppException(Exception):
    """Base application exception."""
    def __init__(self, message: str, details: str = ""):
        super().__init__(message)
        self.message = message
        self.details = details

    def __str__(self) -> str:
        if self.details:
            return f"{self.message} ({self.details})"
        return self.message


class DeviceError(AppException):
    """Base exception for device-level issues."""
    pass


class DeviceNotFoundError(DeviceError):
    """Raised when no compatible Epson device is detected."""
    pass


class DeviceBusyError(DeviceError):
    """Raised when device interface is claimed or busy."""
    pass


class DevicePermissionError(DeviceError):
    """Raised when USB permissions are insufficient (e.g. udev rules required)."""
    pass


class CommunicationError(AppException):
    """Base exception for USB/protocol transport errors."""
    pass


class DeviceTimeoutError(CommunicationError):
    """Raised when bulk transfer or handshake times out."""
    pass


class ProtocolError(CommunicationError):
    """Raised when protocol framing or response parsing fails."""
    pass


class D4ProtocolError(ProtocolError):
    """Raised when IEEE 1284.4 Dot4 packet errors occur."""
    def __init__(self, message: str, error_code: int = 0):
        super().__init__(message, f"D4 Error Code: 0x{error_code:02x}")
        self.error_code = error_code


class SafetyGateError(AppException):
    """Raised when a pre-condition for counter reset fails safety validation."""
    pass


class VerificationFailedError(AppException):
    """Raised when post-reset counter check does not match expected state."""
    pass


class DatabaseError(AppException):
    """Raised when database query or migration fails."""
    pass
