"""
Headless UI instantiation test for MainWindow and Modern Minimalist views.
"""

import os
import unittest

# Configure headless offscreen platform for Qt
os.environ["QT_QPA_PLATFORM"] = "offscreen"

from app.ui.qt_compat import QtWidgets
from app.ui.main_window import MainWindow
from app.bootstrap import create_app_container


class TestGuiInstantiation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Create QApplication instance if not present
        cls.app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

    def test_main_window_loads_with_six_tabs(self):
        container = create_app_container(debug=True)
        win = MainWindow(
            device_manager=container.device_manager,
            printer_service=container.printer_service,
            counter_service=container.counter_service,
            diagnostics_service=container.diagnostics_service,
            reset_service=container.reset_service,
            repository=container.maintenance_repo,
            maintenance_service=container.maintenance_service,
        )

        self.assertIsNotNone(win)
        self.assertEqual(win.stack.count(), 6)

        # Tab index verification:
        # 0: Dashboard, 1: Diagnostics, 2: Waste Counter, 3: Reset, 4: Maintenance, 5: History
        self.assertEqual(win.stack.widget(0), win.dashboard_view)
        self.assertEqual(win.stack.widget(1), win.diagnostics_view)
        self.assertEqual(win.stack.widget(2), win.counter_view)
        self.assertEqual(win.stack.widget(3), win.reset_view)
        self.assertEqual(win.stack.widget(4), win.maintenance_view)
        self.assertEqual(win.stack.widget(5), win.history_view)

        # Test switching across all tabs
        for idx in range(6):
            win.switch_page(idx)
            self.assertEqual(win.stack.currentIndex(), idx)

        # Cleanup
        win.close()


if __name__ == "__main__":
    unittest.main()
