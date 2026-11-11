"""
Application Main Entrypoint.
"""

import sys
import os
import argparse
from pathlib import Path

# Ensure repository root is in sys.path
repo_root = str(Path(__file__).resolve().parent.parent)
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

from app.bootstrap import create_app_container
from app.core.constants import APP_NAME, APP_VERSION, MaintenanceOperation


def run_cli_diagnostics(container):
    print("\n==============================================")
    print(f" {APP_NAME} — Diagnostics Mode")
    print("==============================================")
    res = container.diagnostics_service.run_diagnostics()
    print(f"\n[✓] USB Physical Connection  : {'PASS' if res.usb_connection_ok else 'FAIL'}")
    print(f"[✓] Device Identification    : {'PASS' if res.device_id_match else 'FAIL'}")
    print(f"[✓] IEEE 1284.4 D4 Handshake : {'PASS' if res.d4_handshake_ok else 'FAIL'}")
    print(f"[✓] EPSON-CTRL Channel       : {'PASS' if res.ctrl_channel_ok else 'FAIL'}")
    print(f"[✓] Counter Telemetry        : {'PASS' if res.counter_readable else 'FAIL'}")
    print("\nTechnical Details:")
    for k, v in res.details.items():
        print(f"  • {k}: {v}")
    print(f"\nOverall Result: {'ALL PASSED' if res.all_passed else 'ISSUES DETECTED'}")
    sys.exit(0 if res.all_passed else 1)


def run_cli_counters(container):
    print("\n==============================================")
    print(f" {APP_NAME} — Waste Ink Counter Inspection")
    print("==============================================")
    try:
        record = container.counter_service.read_waste_pad_counters()
        info = container.printer_service.get_detailed_printer_info()
        print(f"Printer Model    : {info.model}")
        print(f"Serial Number    : {info.serial_number}")
        print(f"Firmware Version : {info.firmware_version}")
        print(f"Total Pages Print: {info.total_pages_printed:,}")
        print("\n--- Waste Ink Absorber Pad Status ---")
        print(f"Main Pad Counter   : {record.main_pad.current_points:,} / {record.main_pad.max_points:,} pts ({record.main_pad.percentage:.1f}%)")
        print(f"Platen Pad Counter : {record.platen_pad.current_points:,} / {record.platen_pad.max_points:,} pts ({record.platen_pad.percentage:.1f}%)")
        print(f"Overall Health     : {record.overall_status.value}")
        sys.exit(0)
    except Exception as e:
        print(f"\n[ERROR] Failed to read counters: {e}")
        sys.exit(1)


def run_gui(container):
    from app.ui.qt_compat import QtWidgets
    from app.ui.main_window import MainWindow

    # Check for offscreen mode in env
    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)

    win = MainWindow(
        device_manager=container.device_manager,
        printer_service=container.printer_service,
        counter_service=container.counter_service,
        diagnostics_service=container.diagnostics_service,
        reset_service=container.reset_service,
        repository=container.maintenance_repo,
        maintenance_service=container.maintenance_service,
    )
    win.show()
    sys.exit(app.exec())


def main():
    parser = argparse.ArgumentParser(description=f"{APP_NAME} — Desktop Maintenance & Resetter Utility")
    parser.add_argument("--cli", action="store_true", help="Run without graphical user interface")
    parser.add_argument("--diagnostics", action="store_true", help="Run hardware diagnostics in CLI")
    parser.add_argument("--counters", action="store_true", help="Read waste ink counters in CLI")
    parser.add_argument("--debug", action="store_true", help="Enable verbose debug logging")

    args = parser.parse_args()

    container = create_app_container(debug=args.debug)

    if args.diagnostics:
        run_cli_diagnostics(container)
    elif args.counters:
        run_cli_counters(container)
    elif args.cli:
        print(f"{APP_NAME} CLI Mode. Use --diagnostics or --counters.")
        sys.exit(0)
    else:
        run_gui(container)


if __name__ == "__main__":
    main()
