"""
Libusb-1.0 Driverless USB Backend implementation.
Zero external pip dependencies (standard library ctypes binding).
"""

import sys
import ctypes
import ctypes.util
from typing import Optional, List, Tuple
from app.communication.usb_interface import USBInterface
from app.core.exceptions import DeviceNotFoundError, DevicePermissionError, DeviceBusyError, DeviceTimeoutError, CommunicationError
from app.core.logger import get_logger

log = get_logger("app.communication.libusb")

# Find libusb-1.0
_lib_names = ["libusb-1.0.so.0", "libusb-1.0.so", "libusb-1.0.dylib", "libusb-1.0.dll", "usb-1.0.dll"]
_lib = None

for name in _lib_names:
    try:
        _lib = ctypes.CDLL(name)
        break
    except OSError:
        pass

if not _lib:
    found = ctypes.util.find_library("usb-1.0") or ctypes.util.find_library("libusb-1.0")
    if found:
        try:
            _lib = ctypes.CDLL(found)
        except OSError:
            pass

# Types
class _timeval(ctypes.Structure):
    _fields_ = [("tv_sec", ctypes.c_long), ("tv_usec", ctypes.c_long)]

# Setup signatures if library is present
if _lib:
    _lib.libusb_init.argtypes = [ctypes.c_void_p]
    _lib.libusb_init.restype = ctypes.c_int

    _lib.libusb_exit.argtypes = [ctypes.c_void_p]
    _lib.libusb_exit.restype = None

    _lib.libusb_get_device_list.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p))]
    _lib.libusb_get_device_list.restype = ctypes.c_ssize_t

    _lib.libusb_free_device_list.argtypes = [ctypes.POINTER(ctypes.c_void_p), ctypes.c_int]
    _lib.libusb_free_device_list.restype = None

    _lib.libusb_open.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p)]
    _lib.libusb_open.restype = ctypes.c_int

    _lib.libusb_close.argtypes = [ctypes.c_void_p]
    _lib.libusb_close.restype = None

    _lib.libusb_kernel_driver_active.argtypes = [ctypes.c_void_p, ctypes.c_int]
    _lib.libusb_kernel_driver_active.restype = ctypes.c_int

    _lib.libusb_detach_kernel_driver.argtypes = [ctypes.c_void_p, ctypes.c_int]
    _lib.libusb_detach_kernel_driver.restype = ctypes.c_int

    _lib.libusb_attach_kernel_driver.argtypes = [ctypes.c_void_p, ctypes.c_int]
    _lib.libusb_attach_kernel_driver.restype = ctypes.c_int

    _lib.libusb_claim_interface.argtypes = [ctypes.c_void_p, ctypes.c_int]
    _lib.libusb_claim_interface.restype = ctypes.c_int

    _lib.libusb_release_interface.argtypes = [ctypes.c_void_p, ctypes.c_int]
    _lib.libusb_release_interface.restype = ctypes.c_int

    _lib.libusb_bulk_transfer.argtypes = [
        ctypes.c_void_p,
        ctypes.c_uint8,
        ctypes.POINTER(ctypes.c_uint8),
        ctypes.c_int,
        ctypes.POINTER(ctypes.c_int),
        ctypes.c_uint
    ]
    _lib.libusb_bulk_transfer.restype = ctypes.c_int

    _lib.libusb_strerror.argtypes = [ctypes.c_int]
    _lib.libusb_strerror.restype = ctypes.c_char_p


class _DeviceDescriptor(ctypes.Structure):
    _fields_ = [
        ("bLength", ctypes.c_uint8),
        ("bDescriptorType", ctypes.c_uint8),
        ("bcdUSB", ctypes.c_uint16),
        ("bDeviceClass", ctypes.c_uint8),
        ("bDeviceSubClass", ctypes.c_uint8),
        ("bDeviceProtocol", ctypes.c_uint8),
        ("bMaxPacketSize0", ctypes.c_uint8),
        ("idVendor", ctypes.c_uint16),
        ("idProduct", ctypes.c_uint16),
        ("bcdDevice", ctypes.c_uint16),
        ("iManufacturer", ctypes.c_uint8),
        ("iProduct", ctypes.c_uint8),
        ("iSerialNumber", ctypes.c_uint8),
        ("bNumConfigurations", ctypes.c_uint8)
    ]

if _lib:
    _lib.libusb_get_device_descriptor.argtypes = [ctypes.c_void_p, ctypes.POINTER(_DeviceDescriptor)]
    _lib.libusb_get_device_descriptor.restype = ctypes.c_int


class LibUSBBackend(USBInterface):
    def __init__(self):
        if not _lib:
            raise CommunicationError("libusb-1.0 library not found on system")
        self._ctx = None
        self._handle = None
        self._claimed_interfaces = []
        self._detached_drivers = []
        self._init_ctx()

    def _init_ctx(self):
        ctx = ctypes.c_void_p()
        ret = _lib.libusb_init(ctypes.byref(ctx))
        if ret != 0:
            raise CommunicationError(f"Failed to init libusb: {_lib.libusb_strerror(ret).decode()}")
        self._ctx = ctx

    def find_devices(self, vendor_id: int, product_id: Optional[int] = None) -> List[Tuple[int, int, str]]:
        if not self._ctx:
            self._init_ctx()

        dev_list = ctypes.POINTER(ctypes.c_void_p)()
        cnt = _lib.libusb_get_device_list(self._ctx, ctypes.byref(dev_list))
        if cnt < 0:
            return []

        results = []
        try:
            for i in range(cnt):
                dev = dev_list[i]
                desc = _DeviceDescriptor()
                if _lib.libusb_get_device_descriptor(dev, ctypes.byref(desc)) == 0:
                    if desc.idVendor == vendor_id:
                        if product_id is None or desc.idProduct == product_id:
                            results.append((desc.idVendor, desc.idProduct, ""))
        finally:
            _lib.libusb_free_device_list(dev_list, 1)

        return results

    def open_device(self, vendor_id: int, product_id: int, serial_number: Optional[str] = None):
        self.close()
        if not self._ctx:
            self._init_ctx()

        dev_list = ctypes.POINTER(ctypes.c_void_p)()
        cnt = _lib.libusb_get_device_list(self._ctx, ctypes.byref(dev_list))
        if cnt < 0:
            raise DeviceNotFoundError(f"Failed to get USB device list (error {cnt})")

        target_dev = None
        try:
            for i in range(cnt):
                dev = dev_list[i]
                desc = _DeviceDescriptor()
                if _lib.libusb_get_device_descriptor(dev, ctypes.byref(desc)) == 0:
                    if desc.idVendor == vendor_id and desc.idProduct == product_id:
                        target_dev = dev
                        break

            if not target_dev:
                raise DeviceNotFoundError(f"No USB device found matching VID:0x{vendor_id:04x} PID:0x{product_id:04x}")

            handle = ctypes.c_void_p()
            ret = _lib.libusb_open(target_dev, ctypes.byref(handle))
            if ret != 0:
                err_msg = _lib.libusb_strerror(ret).decode() if _lib.libusb_strerror else f"error {ret}"
                if ret == -3:  # LIBUSB_ERROR_ACCESS
                    raise DevicePermissionError(f"Access denied opening USB device: {err_msg}")
                elif ret == -6:  # LIBUSB_ERROR_BUSY
                    raise DeviceBusyError(f"USB device busy: {err_msg}")
                else:
                    raise CommunicationError(f"Failed to open USB device: {err_msg}")
            self._handle = handle
            log.info(f"Opened USB device 0x{vendor_id:04x}:0x{product_id:04x}")
        finally:
            _lib.libusb_free_device_list(dev_list, 1)

    def claim_interface(self, interface_index: int):
        if not self._handle:
            raise CommunicationError("Device not opened")

        # Detach kernel driver if active (e.g. usblp on Linux)
        try:
            active = _lib.libusb_kernel_driver_active(self._handle, interface_index)
            if active == 1:
                ret = _lib.libusb_detach_kernel_driver(self._handle, interface_index)
                if ret == 0:
                    self._detached_drivers.append(interface_index)
                    log.debug(f"Detached kernel driver on interface {interface_index}")
        except Exception as e:
            log.debug(f"Kernel driver check/detach exception: {e}")

        ret = _lib.libusb_claim_interface(self._handle, interface_index)
        if ret != 0:
            err_msg = _lib.libusb_strerror(ret).decode() if _lib.libusb_strerror else f"error {ret}"
            raise DeviceBusyError(f"Failed to claim interface {interface_index}: {err_msg}")
        self._claimed_interfaces.append(interface_index)
        log.debug(f"Claimed USB interface {interface_index}")

    def release_interface(self, interface_index: int):
        if self._handle and interface_index in self._claimed_interfaces:
            _lib.libusb_release_interface(self._handle, interface_index)
            self._claimed_interfaces.remove(interface_index)
            log.debug(f"Released USB interface {interface_index}")

        # Re-attach kernel driver if previously detached
        if self._handle and interface_index in self._detached_drivers:
            try:
                _lib.libusb_attach_kernel_driver(self._handle, interface_index)
                self._detached_drivers.remove(interface_index)
                log.debug(f"Re-attached kernel driver on interface {interface_index}")
            except Exception as e:
                log.debug(f"Kernel driver re-attach exception: {e}")

    def write_bulk(self, endpoint: int, data: bytes, timeout_ms: int = 2000) -> int:
        if not self._handle:
            raise CommunicationError("Device not opened")

        data_len = len(data)
        buf = (ctypes.c_uint8 * data_len).from_buffer_copy(data)
        transferred = ctypes.c_int(0)

        ret = _lib.libusb_bulk_transfer(
            self._handle,
            ctypes.c_uint8(endpoint),
            buf,
            ctypes.c_int(data_len),
            ctypes.byref(transferred),
            ctypes.c_uint(timeout_ms)
        )
        if ret != 0:
            if ret == -7:  # LIBUSB_ERROR_TIMEOUT
                raise DeviceTimeoutError(f"Bulk write timeout ({timeout_ms}ms) on EP 0x{endpoint:02x}")
            err_msg = _lib.libusb_strerror(ret).decode() if _lib.libusb_strerror else f"error {ret}"
            raise CommunicationError(f"Bulk write error on EP 0x{endpoint:02x}: {err_msg}")
        return transferred.value

    def read_bulk(self, endpoint: int, length: int = 512, timeout_ms: int = 2000) -> bytes:
        if not self._handle:
            raise CommunicationError("Device not opened")

        buf = (ctypes.c_uint8 * length)()
        transferred = ctypes.c_int(0)

        ret = _lib.libusb_bulk_transfer(
            self._handle,
            ctypes.c_uint8(endpoint),
            buf,
            ctypes.c_int(length),
            ctypes.byref(transferred),
            ctypes.c_uint(timeout_ms)
        )
        if ret != 0:
            if ret == -7:  # LIBUSB_ERROR_TIMEOUT
                return b""  # Clean empty return on timeout
            err_msg = _lib.libusb_strerror(ret).decode() if _lib.libusb_strerror else f"error {ret}"
            raise CommunicationError(f"Bulk read error on EP 0x{endpoint:02x}: {err_msg}")
        return bytes(buf[:transferred.value])

    def close(self):
        if self._handle:
            for iface in list(self._claimed_interfaces):
                self.release_interface(iface)
            _lib.libusb_close(self._handle)
            self._handle = None
            log.info("Closed USB device")

    def is_open(self) -> bool:
        return self._handle is not None

    def __del__(self):
        try:
            self.close()
            if self._ctx:
                _lib.libusb_exit(self._ctx)
                self._ctx = None
        except Exception:
            pass
