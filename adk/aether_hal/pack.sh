#!/bin/bash
#===============================================================================
# Aether HAL - ADK Package Builder
# Creates .app package for Azure BLU-IC2 Controller deployment
#===============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ADK_DIR="/Users/mosley/AXIOM/Projects/Azure_Panel/Relics/adk_1.22.1_20250903-213533"
OUTPUT_DIR="/Users/mosley/AXIOM/Projects/Azure_Panel/Source/deploy"

echo "==============================================================================="
echo "              Building Aether HAL ADK Package"
echo "         Hardware Abstraction Layer for Azure BLU-IC2"
echo "==============================================================================="
echo ""

# Check for developer certificate
if [ ! -f "$ADK_DIR/test-app-dev-sign.crt" ]; then
    echo "ERROR: Developer certificate not found!"
    echo "Please obtain the developer certificate from Azure Access Technology"
    echo "and place it at: $ADK_DIR/test-app-dev-sign.crt"
    exit 1
fi

# Check for base layer
if [ ! -f "$ADK_DIR/layers/base.tar.bz2" ]; then
    echo "ERROR: Base layer not found at $ADK_DIR/layers/base.tar.bz2"
    exit 1
fi

echo "[1/3] Preparing rootfs..."
# Ensure all files are in place
ls -la "$SCRIPT_DIR/rootfs/app/"

echo ""
echo "[2/3] Building .app package..."
cd "$ADK_DIR"

"$ADK_DIR/pack_app.sh" \
    -b "$ADK_DIR/layers/base.tar.bz2" \
    -a "$SCRIPT_DIR/rootfs" \
    -m "$SCRIPT_DIR/manifest" \
    -c "$ADK_DIR/test-app-dev-sign.crt" \
    -o "$OUTPUT_DIR/aether_hal.app"

echo ""
echo "[3/3] Creating checksum..."
cd "$OUTPUT_DIR"
shasum -a 256 aether_hal.app > aether_hal.app.sha256

echo ""
echo "==============================================================================="
echo "                        BUILD COMPLETE"
echo "==============================================================================="
echo ""
echo "Package created:"
echo "  $OUTPUT_DIR/aether_hal.app"
echo ""
echo "Checksum (SHA-256):"
cat "$OUTPUT_DIR/aether_hal.app.sha256"
echo ""
echo "To deploy:"
echo "  1. Open Azure BLU-IC2 web interface"
echo "  2. Navigate to Applications"
echo "  3. Click Upload"
echo "  4. Select: aether_hal.app"
echo ""
