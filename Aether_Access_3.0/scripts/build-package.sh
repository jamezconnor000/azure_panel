#!/bin/bash
#===============================================================================
# Aether Access 3.0 - Build Deployment Package
# Complete Access Control System for Azure BLU-IC2 Controllers
# Creates a distributable tar.gz package for Azure Panel deployment
#
# Includes:
#   - Aether Thrall   - Hardware Abstraction Layer
#   - Aether Bifrost  - API Server (the bridge)
#   - Aether Saga     - Web Management Interface
#===============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
BUILD_DIR="/tmp/aether-access-build"
VERSION=$(cat "$SOURCE_DIR/VERSION" 2>/dev/null || echo "2.0.0")
PACKAGE_NAME="aether-access-${VERSION}"
OUTPUT_DIR="${1:-$SOURCE_DIR/deploy}"

echo "==============================================================================="
echo "             Building Aether Access Deployment Package"
echo "        Complete Access Control System for Azure BLU-IC2"
echo "                         Version: $VERSION"
echo "==============================================================================="
echo ""
echo "Components:"
echo "  - Aether Thrall   - Hardware Abstraction Layer"
echo "  - Aether Bifrost  - API Server"
echo "  - Aether Saga     - Web Management Interface"
echo ""

# Clean previous build
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR/$PACKAGE_NAME"

echo "[1/9] Copying Aether Bifrost (API server)..."
mkdir -p "$BUILD_DIR/$PACKAGE_NAME/api"
cp "$SOURCE_DIR/api/aether_bifrost.py" "$BUILD_DIR/$PACKAGE_NAME/api/"
cp "$SOURCE_DIR/api/ambient_integration.py" "$BUILD_DIR/$PACKAGE_NAME/api/"
cp "$SOURCE_DIR/api/api_v2_1.py" "$BUILD_DIR/$PACKAGE_NAME/api/" 2>/dev/null || true
cp "$SOURCE_DIR/api/api_v2_2.py" "$BUILD_DIR/$PACKAGE_NAME/api/" 2>/dev/null || true
cp "$SOURCE_DIR/api/auth.py" "$BUILD_DIR/$PACKAGE_NAME/api/" 2>/dev/null || true
cp "$SOURCE_DIR/api/database.py" "$BUILD_DIR/$PACKAGE_NAME/api/" 2>/dev/null || true
cp "$SOURCE_DIR/api/ambient_export_daemon.py" "$BUILD_DIR/$PACKAGE_NAME/api/" 2>/dev/null || true

echo "[2/9] Copying HAL Python bindings..."
mkdir -p "$BUILD_DIR/$PACKAGE_NAME/python"
cp "$SOURCE_DIR/python/hal_bindings.py" "$BUILD_DIR/$PACKAGE_NAME/python/"

echo "[3/9] Building Aether Saga (React frontend)..."
SAGA_DIR="$SOURCE_DIR/aether_saga"
if [ -d "$SAGA_DIR" ]; then
    cd "$SAGA_DIR"
    if [ -f "package.json" ]; then
        # Build the frontend
        npm run build 2>/dev/null || echo "  [WARN] npm build failed, using existing dist"
    fi

    if [ -d "dist" ]; then
        echo "  Copying Aether Saga build..."
        mkdir -p "$BUILD_DIR/$PACKAGE_NAME/aether_saga"
        cp -r "$SAGA_DIR/dist" "$BUILD_DIR/$PACKAGE_NAME/aether_saga/"
    else
        echo "  [WARN] Aether Saga dist not found"
    fi
    cd "$SOURCE_DIR"
else
    echo "  [WARN] Aether Saga source not found"
fi

echo "[4/9] Copying requirements..."
cp "$SOURCE_DIR/requirements.txt" "$BUILD_DIR/$PACKAGE_NAME/"
# Ensure aiohttp is included for Ambient.ai integration
if ! grep -q "aiohttp" "$BUILD_DIR/$PACKAGE_NAME/requirements.txt" 2>/dev/null; then
    echo "aiohttp>=3.8.0" >> "$BUILD_DIR/$PACKAGE_NAME/requirements.txt"
fi

echo "[5/9] Copying deployment scripts..."
mkdir -p "$BUILD_DIR/$PACKAGE_NAME/scripts"
cp "$SCRIPT_DIR/install.sh" "$BUILD_DIR/$PACKAGE_NAME/scripts/"
cp "$SCRIPT_DIR/uninstall.sh" "$BUILD_DIR/$PACKAGE_NAME/scripts/"
chmod +x "$BUILD_DIR/$PACKAGE_NAME/scripts/"*.sh

echo "[6/9] Copying configuration templates..."
mkdir -p "$BUILD_DIR/$PACKAGE_NAME/config"
cp "$SOURCE_DIR/deploy/config/"*.template "$BUILD_DIR/$PACKAGE_NAME/config/" 2>/dev/null || true
mkdir -p "$BUILD_DIR/$PACKAGE_NAME/systemd"
cp "$SOURCE_DIR/deploy/systemd/"*.service "$BUILD_DIR/$PACKAGE_NAME/systemd/" 2>/dev/null || true

echo "[7/9] Copying Aether Thrall app..."
if [ -f "$SOURCE_DIR/deploy/aether_thrall.app" ]; then
    cp "$SOURCE_DIR/deploy/aether_thrall.app" "$BUILD_DIR/$PACKAGE_NAME/"
    echo "  Included aether_thrall.app"
else
    echo "  [WARN] aether_thrall.app not found in deploy/"
fi

echo "[8/9] Copying documentation..."
mkdir -p "$BUILD_DIR/$PACKAGE_NAME/docs"
cp "$SOURCE_DIR/deploy/docs/INSTALLATION_GUIDE.md" "$BUILD_DIR/$PACKAGE_NAME/docs/" 2>/dev/null || true
cp "$SOURCE_DIR/README.md" "$BUILD_DIR/$PACKAGE_NAME/docs/" 2>/dev/null || true

# Create README for package
cat > "$BUILD_DIR/$PACKAGE_NAME/README.txt" << EOF
===============================================================================
                    AETHER ACCESS 3.0 - DEPLOYMENT PACKAGE
         Complete Access Control System for Azure BLU-IC2 Controllers
                           Version: $VERSION
===============================================================================

This package contains the complete Aether Access 3.0 System:

  AETHER THRALL  - Hardware Abstraction Layer
                   Runs as Azure ADK app on the panel

  AETHER BIFROST - API Server (the bridge)
                   REST API connecting frontend to HAL

  AETHER SAGA    - Web Management Interface
                   React-based PACS management UI

Quick Start:
  1. Extract: tar -xzf $PACKAGE_NAME.tar.gz
  2. Install: sudo ./scripts/install.sh
  3. Access:  http://panel-ip (Aether Saga)
              http://panel-ip:8080 (Bifrost API)

Directory Contents:
  - api/              Aether Bifrost API server
    - aether_bifrost.py       Main API server
    - ambient_integration.py  Ambient.ai cloud integration
  - aether_saga/      Web frontend build
    - dist/           Built React application
  - python/           HAL Python bindings
  - scripts/          Installation scripts
  - config/           Configuration templates
  - systemd/          Service files
  - docs/             Documentation
  - aether_thrall.app HAL application (Azure ADK format)

Ambient.ai Integration:
  Set environment variables:
    AMBIENT_API_KEY=your-api-key
    AMBIENT_SOURCE_SYSTEM_UID=your-system-uuid

  Events are automatically forwarded to Ambient.ai cloud.

Features:
  - Event-driven architecture with 100K event buffer
  - Local SQLite card database with 1M+ capacity
  - OSDP/Wiegand/DESFire protocol support
  - Offline operation capability
  - Real-time WebSocket updates
  - Ambient.ai cloud integration
  - UnityIS-compatible API

Generated: $(date)
===============================================================================
EOF

echo "[9/9] Creating deployment archive..."
cd "$BUILD_DIR"
tar -czf "$PACKAGE_NAME.tar.gz" "$PACKAGE_NAME"

# Move to output directory
mkdir -p "$OUTPUT_DIR"
mv "$PACKAGE_NAME.tar.gz" "$OUTPUT_DIR/"

# Calculate checksum
cd "$OUTPUT_DIR"
shasum -a 256 "$PACKAGE_NAME.tar.gz" > "$PACKAGE_NAME.tar.gz.sha256"

# Clean up
rm -rf "$BUILD_DIR"

echo ""
echo "==============================================================================="
echo "                    BUILD COMPLETE"
echo "==============================================================================="
echo ""
echo "Package created:"
echo "  $OUTPUT_DIR/$PACKAGE_NAME.tar.gz"
echo ""
echo "Checksum (SHA-256):"
cat "$OUTPUT_DIR/$PACKAGE_NAME.tar.gz.sha256"
echo ""
echo "Package size:"
ls -lh "$OUTPUT_DIR/$PACKAGE_NAME.tar.gz" | awk '{print "  " $5}'
echo ""
echo "To deploy to an Azure Panel:"
echo "  scp $OUTPUT_DIR/$PACKAGE_NAME.tar.gz root@panel-ip:/tmp/"
echo "  ssh root@panel-ip 'cd /tmp && tar -xzf $PACKAGE_NAME.tar.gz && cd $PACKAGE_NAME && sudo ./scripts/install.sh'"
echo ""
