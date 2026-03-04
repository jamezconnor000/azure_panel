#!/bin/bash
#===============================================================================
# Aether HAL - Build Deployment Package
# Hardware Abstraction Layer for Azure BLU-IC2 Controllers
# Creates a distributable tar.gz package for Azure Panel deployment
#===============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
BUILD_DIR="/tmp/aether-hal-build"
VERSION=$(cat "$SOURCE_DIR/VERSION" 2>/dev/null || echo "2.0.0")
PACKAGE_NAME="aether-hal-${VERSION}"
OUTPUT_DIR="${1:-$SOURCE_DIR/deploy}"

echo "==============================================================================="
echo "               Building Aether HAL Deployment Package"
echo "         Hardware Abstraction Layer for Azure BLU-IC2 Controllers"
echo "                         Version: $VERSION"
echo "==============================================================================="
echo ""

# Clean previous build
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR/$PACKAGE_NAME"

echo "[1/7] Copying API server..."
mkdir -p "$BUILD_DIR/$PACKAGE_NAME/api"
cp "$SOURCE_DIR/api/unified_api_server.py" "$BUILD_DIR/$PACKAGE_NAME/api/"
cp "$SOURCE_DIR/api/api_v2_1.py" "$BUILD_DIR/$PACKAGE_NAME/api/"
cp "$SOURCE_DIR/api/api_v2_2.py" "$BUILD_DIR/$PACKAGE_NAME/api/"
cp "$SOURCE_DIR/api/auth.py" "$BUILD_DIR/$PACKAGE_NAME/api/"
cp "$SOURCE_DIR/api/database.py" "$BUILD_DIR/$PACKAGE_NAME/api/"
cp "$SOURCE_DIR/api/ambient_export_daemon.py" "$BUILD_DIR/$PACKAGE_NAME/api/"

echo "[2/7] Copying Python bindings..."
mkdir -p "$BUILD_DIR/$PACKAGE_NAME/python"
cp "$SOURCE_DIR/python/hal_bindings.py" "$BUILD_DIR/$PACKAGE_NAME/python/"

echo "[3/7] Copying requirements..."
cp "$SOURCE_DIR/requirements.txt" "$BUILD_DIR/$PACKAGE_NAME/"

echo "[4/7] Copying deployment scripts..."
mkdir -p "$BUILD_DIR/$PACKAGE_NAME/scripts"
cp "$SCRIPT_DIR/install.sh" "$BUILD_DIR/$PACKAGE_NAME/scripts/"
cp "$SCRIPT_DIR/uninstall.sh" "$BUILD_DIR/$PACKAGE_NAME/scripts/"
chmod +x "$BUILD_DIR/$PACKAGE_NAME/scripts/"*.sh

echo "[5/7] Copying configuration templates..."
mkdir -p "$BUILD_DIR/$PACKAGE_NAME/config"
cp "$SOURCE_DIR/deploy/config/"*.template "$BUILD_DIR/$PACKAGE_NAME/config/" 2>/dev/null || true
mkdir -p "$BUILD_DIR/$PACKAGE_NAME/systemd"
cp "$SOURCE_DIR/deploy/systemd/"*.service "$BUILD_DIR/$PACKAGE_NAME/systemd/" 2>/dev/null || true

echo "[6/7] Adding httpx to requirements..."
# Ensure httpx is in requirements for async HTTP client (needed for Ambient.ai export)
if ! grep -q "httpx" "$SOURCE_DIR/requirements.txt" 2>/dev/null; then
    echo "httpx>=0.24.0" >> "$BUILD_DIR/$PACKAGE_NAME/requirements.txt"
fi

echo "[7/7] Copying documentation..."
mkdir -p "$BUILD_DIR/$PACKAGE_NAME/docs"
cp "$SOURCE_DIR/deploy/docs/INSTALLATION_GUIDE.md" "$BUILD_DIR/$PACKAGE_NAME/docs/"
cp "$SOURCE_DIR/README.md" "$BUILD_DIR/$PACKAGE_NAME/docs/" 2>/dev/null || true

# Create README for package
cat > "$BUILD_DIR/$PACKAGE_NAME/README.txt" << EOF
===============================================================================
                    AETHER HAL - DEPLOYMENT PACKAGE
          Hardware Abstraction Layer for Azure BLU-IC2 Controllers
                           Version: $VERSION
===============================================================================

Quick Start:
  1. Extract this package: tar -xzf $PACKAGE_NAME.tar.gz
  2. Run installer: sudo ./scripts/install.sh
  3. Verify: curl http://localhost:8080/health

For detailed instructions, see: docs/INSTALLATION_GUIDE.md

Directory Contents:
  - api/           API server modules
    - unified_api_server.py      Main API server
    - ambient_export_daemon.py   Ambient.ai event export daemon
  - python/        HAL Python bindings
  - scripts/       Installation scripts
  - config/        Configuration templates
    - aether.env.template        API server config
    - ambient.env.template       Ambient.ai export config
  - systemd/       Service files
    - aether-access.service          API server service
    - aether-ambient-export.service  Ambient.ai export service
  - docs/          Documentation

Ambient.ai Integration:
  To enable Ambient.ai event export:
  1. Copy /etc/aether/ambient.env.template to /etc/aether/ambient.env
  2. Add your AMBIENT_API_KEY
  3. Enable service: sudo systemctl enable aether-ambient-export
  4. Start service: sudo systemctl start aether-ambient-export

Aether HAL Features:
  - Event-driven architecture with 100K event buffer
  - Local SQLite card database with 1M+ capacity
  - OSDP/Wiegand/DESFire protocol support
  - Offline operation capability
  - REST API with real-time WebSocket updates

Generated: $(date)
===============================================================================
EOF

# Create archive
echo ""
echo "Creating deployment archive..."
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
