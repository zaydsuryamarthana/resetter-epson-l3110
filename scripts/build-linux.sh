#!/usr/bin/env bash
# ==============================================================================
# Build & Packaging script for Arch Linux / Linux distributions
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
DIST_DIR="${PROJECT_ROOT}/dist/linux"
APP_NAME="epson-l3110-resetter"

echo "=== Building ${APP_NAME} for Linux ==="
echo "Project root: ${PROJECT_ROOT}"

# Create dist directory
rm -rf "${DIST_DIR}"
mkdir -p "${DIST_DIR}/bin"
mkdir -p "${DIST_DIR}/rules"
mkdir -p "${DIST_DIR}/docs"

# Copy python application code
cp -r "${PROJECT_ROOT}/app" "${DIST_DIR}/"
cp "${PROJECT_ROOT}/scripts/99-epson-l3110.rules" "${DIST_DIR}/rules/"
cp "${PROJECT_ROOT}/README.md" "${DIST_DIR}/docs/"

# Create executable launcher script
cat << 'EOF' > "${DIST_DIR}/bin/epson-resetter"
#!/usr/bin/env bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUNDLE_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
export PYTHONPATH="${BUNDLE_ROOT}:${PYTHONPATH:-}"
exec python3 "${BUNDLE_ROOT}/app/main.py" "$@"
EOF

chmod +x "${DIST_DIR}/bin/epson-resetter"

# Create Desktop Entry
cat << EOF > "${DIST_DIR}/${APP_NAME}.desktop"
[Desktop Entry]
Name=Epson L3110 Resetter
Comment=Cross-Platform Printer Maintenance & Waste Ink Pad Utility
Exec=${DIST_DIR}/bin/epson-resetter
Terminal=false
Type=Application
Categories=Utility;HardwareSettings;Printing;
EOF

chmod +x "${DIST_DIR}/${APP_NAME}.desktop"

echo "=== Linux bundle built successfully at: ${DIST_DIR} ==="
echo "To test run: ${DIST_DIR}/bin/epson-resetter --cli"
