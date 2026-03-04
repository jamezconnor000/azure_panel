#!/bin/bash
#===============================================================================
#  ᚨ ᛖ ᚦ ᛖ ᚱ  HAL - Complete Build Script
#  Hardware Abstraction Layer for Azure BLU-IC2 Controllers
#  Version: 2.0.0
#===============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VERSION=$(cat "$SCRIPT_DIR/VERSION" 2>/dev/null || echo "2.0.0")
OUTPUT_DIR="$SCRIPT_DIR/deploy"
ADK_DIR="$SCRIPT_DIR/adk/aether_hal"

echo ""
echo "  ᚨ ᛖ ᚦ ᛖ ᚱ   H A L"
echo "  Hardware Abstraction Layer"
echo "  Version: $VERSION"
echo ""
echo "==============================================================================="
echo "                     Building Aether HAL Deployment Packages"
echo "==============================================================================="
echo ""

# Create output directory
mkdir -p "$OUTPUT_DIR"

#-------------------------------------------------------------------------------
# Package 1: Traditional tar.gz deployment
#-------------------------------------------------------------------------------
echo "[1/2] Building traditional deployment package..."

BUILD_DIR="/tmp/aether-hal-build"
PACKAGE_NAME="aether-hal-${VERSION}"

rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR/$PACKAGE_NAME"

# Copy API server
mkdir -p "$BUILD_DIR/$PACKAGE_NAME/api"
cp "$SCRIPT_DIR/api/unified_api_server.py" "$BUILD_DIR/$PACKAGE_NAME/api/"
cp "$SCRIPT_DIR/api/api_v2_1.py" "$BUILD_DIR/$PACKAGE_NAME/api/"
cp "$SCRIPT_DIR/api/api_v2_2.py" "$BUILD_DIR/$PACKAGE_NAME/api/"
cp "$SCRIPT_DIR/api/auth.py" "$BUILD_DIR/$PACKAGE_NAME/api/"
cp "$SCRIPT_DIR/api/database.py" "$BUILD_DIR/$PACKAGE_NAME/api/"
cp "$SCRIPT_DIR/api/ambient_export_daemon.py" "$BUILD_DIR/$PACKAGE_NAME/api/" 2>/dev/null || true

# Copy Python bindings
mkdir -p "$BUILD_DIR/$PACKAGE_NAME/python"
cp "$SCRIPT_DIR/python/hal_bindings.py" "$BUILD_DIR/$PACKAGE_NAME/python/"

# Copy requirements
cp "$SCRIPT_DIR/requirements.txt" "$BUILD_DIR/$PACKAGE_NAME/"

# Copy deployment scripts
mkdir -p "$BUILD_DIR/$PACKAGE_NAME/scripts"
cp "$SCRIPT_DIR/deploy/scripts/install.sh" "$BUILD_DIR/$PACKAGE_NAME/scripts/" 2>/dev/null || true
cp "$SCRIPT_DIR/deploy/scripts/uninstall.sh" "$BUILD_DIR/$PACKAGE_NAME/scripts/" 2>/dev/null || true
chmod +x "$BUILD_DIR/$PACKAGE_NAME/scripts/"*.sh 2>/dev/null || true

# Copy config templates
mkdir -p "$BUILD_DIR/$PACKAGE_NAME/config"
cp "$SCRIPT_DIR/deploy/config/"*.template "$BUILD_DIR/$PACKAGE_NAME/config/" 2>/dev/null || true

# Copy systemd services
mkdir -p "$BUILD_DIR/$PACKAGE_NAME/systemd"
cp "$SCRIPT_DIR/deploy/systemd/"*.service "$BUILD_DIR/$PACKAGE_NAME/systemd/" 2>/dev/null || true

# Copy documentation
mkdir -p "$BUILD_DIR/$PACKAGE_NAME/docs"
cp "$SCRIPT_DIR/deploy/docs/INSTALLATION_GUIDE.md" "$BUILD_DIR/$PACKAGE_NAME/docs/" 2>/dev/null || true
cp "$SCRIPT_DIR/README.md" "$BUILD_DIR/$PACKAGE_NAME/docs/" 2>/dev/null || true

# Create README
cat > "$BUILD_DIR/$PACKAGE_NAME/README.txt" << EOF
===============================================================================
                        AETHER HAL - DEPLOYMENT PACKAGE
              Hardware Abstraction Layer for Azure BLU-IC2 Controllers
                               Version: $VERSION
===============================================================================

Quick Start:
  1. Extract: tar -xzf $PACKAGE_NAME.tar.gz
  2. Install: sudo ./scripts/install.sh
  3. Verify:  curl http://localhost:8080/health

For detailed instructions, see: docs/INSTALLATION_GUIDE.md

API Documentation: http://<panel-ip>:8080/docs

Features:
  - Event-driven architecture with 100K event buffer
  - Local SQLite card database with 1M+ capacity
  - OSDP/Wiegand/DESFire protocol support
  - Ambient.ai event export integration
  - REST API with real-time WebSocket updates
  - Offline operation capability

Generated: $(date)
===============================================================================
EOF

# Create archive
cd "$BUILD_DIR"
tar -czf "$PACKAGE_NAME.tar.gz" "$PACKAGE_NAME"
mv "$PACKAGE_NAME.tar.gz" "$OUTPUT_DIR/"

# Checksum
cd "$OUTPUT_DIR"
shasum -a 256 "$PACKAGE_NAME.tar.gz" > "$PACKAGE_NAME.tar.gz.sha256"

echo "  Created: $OUTPUT_DIR/$PACKAGE_NAME.tar.gz"

#-------------------------------------------------------------------------------
# Package 2: ADK .app package (requires developer certificate)
#-------------------------------------------------------------------------------
echo ""
echo "[2/2] Preparing ADK package..."

ADK_TOOLS="/Users/mosley/AXIOM/Projects/Azure_Panel/Relics/adk_1.22.1_20250903-213533"

if [ -f "$ADK_TOOLS/test-app-dev-sign.crt" ]; then
    echo "  Developer certificate found. Building .app package..."

    cd "$ADK_TOOLS"
    "$ADK_TOOLS/pack_app.sh" \
        -b "$ADK_TOOLS/layers/base.tar.bz2" \
        -a "$ADK_DIR/rootfs" \
        -m "$ADK_DIR/manifest" \
        -c "$ADK_TOOLS/test-app-dev-sign.crt" \
        -o "$OUTPUT_DIR/aether_hal.app"

    cd "$OUTPUT_DIR"
    shasum -a 256 aether_hal.app > aether_hal.app.sha256

    echo "  Created: $OUTPUT_DIR/aether_hal.app"
else
    echo "  WARNING: Developer certificate not found!"
    echo "  To build .app package:"
    echo "    1. Obtain certificate from Azure Access Technology"
    echo "    2. Place at: $ADK_TOOLS/test-app-dev-sign.crt"
    echo "    3. Run: ./adk/aether_hal/pack.sh"
    echo ""
    echo "  ADK structure prepared at: $ADK_DIR/"
fi

# Cleanup
rm -rf "$BUILD_DIR"

echo ""
echo "==============================================================================="
echo "                           BUILD COMPLETE"
echo "==============================================================================="
echo ""
echo "Output directory: $OUTPUT_DIR/"
echo ""
ls -lh "$OUTPUT_DIR/"*.tar.gz "$OUTPUT_DIR/"*.app 2>/dev/null || true
echo ""
echo "Deployment Options:"
echo ""
echo "  Option 1 - Traditional (SSH/SCP):"
echo "    scp $OUTPUT_DIR/$PACKAGE_NAME.tar.gz root@panel-ip:/tmp/"
echo "    ssh root@panel-ip 'cd /tmp && tar -xzf $PACKAGE_NAME.tar.gz && cd $PACKAGE_NAME && sudo ./scripts/install.sh'"
echo ""
echo "  Option 2 - ADK (Web Interface):"
echo "    1. Open Azure BLU-IC2 web interface"
echo "    2. Navigate to Applications"
echo "    3. Click Upload"
echo "    4. Select: aether_hal.app"
echo ""
