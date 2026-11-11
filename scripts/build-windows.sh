#!/usr/bin/env bash
# ==============================================================================
# Build & Packaging script for Windows 10/11 (PyInstaller)
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
DIST_DIR="${PROJECT_ROOT}/dist/windows"
APP_NAME="EpsonL3110Resetter"

echo "=== Packaging ${APP_NAME} for Windows 10/11 ==="

if command -v pyinstaller &> /dev/null; then
    pyinstaller \
        --name="${APP_NAME}" \
        --noconfirm \
        --onedir \
        --windowed \
        --add-data="${PROJECT_ROOT}/app:app" \
        --distpath="${DIST_DIR}" \
        "${PROJECT_ROOT}/app/main.py"
    echo "Windows build complete at: ${DIST_DIR}/${APP_NAME}"
else
    echo "[INFO] PyInstaller not detected in current Linux host environment."
    echo "To build on Windows, run:"
    echo "    pip install pyinstaller"
    echo "    pyinstaller --name=${APP_NAME} --windowed app/main.py"
fi
