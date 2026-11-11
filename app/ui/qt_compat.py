"""
Qt Binding Compatibility Layer (PyQt6 / PySide6).
"""

import sys

try:
    from PyQt6 import QtCore, QtGui, QtWidgets
    from PyQt6.QtCore import pyqtSignal as Signal, pyqtSlot as Slot, QThread, Qt, QTimer
    IS_PYQT6 = True
    IS_PYSIDE6 = False
except ImportError:
    try:
        from PySide6 import QtCore, QtGui, QtWidgets
        from PySide6.QtCore import Signal, Slot, QThread, Qt, QTimer
        IS_PYQT6 = False
        IS_PYSIDE6 = True
    except ImportError as e:
        raise ImportError("Neither PyQt6 nor PySide6 is installed on the system.") from e
