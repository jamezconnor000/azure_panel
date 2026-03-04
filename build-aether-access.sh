#!/bin/bash
#===============================================================================
#  ᚨ ᛖ ᚦ ᛖ ᚱ   A C C E S S   3 . 0
#  Complete Build Script for Azure BLU-IC2 Controllers
#
#  Components:
#    - Aether Thrall  (HAL)
#    - Aether Bifrost (API)
#    - Aether Saga    (Web UI)
#===============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VERSION=$(cat "$SCRIPT_DIR/VERSION" 2>/dev/null || echo "3.0.0")
OUTPUT_DIR="$SCRIPT_DIR/deploy"
ADK_TOOLS="/Users/mosley/AXIOM/Projects/Azure_Panel/Relics/adk_1.22.1_20250903-213533"

echo ""
echo "  ᚨ ᛖ ᚦ ᛖ ᚱ   A C C E S S   3 . 0"
echo "  Complete Access Control System"
echo "  Version: $VERSION"
echo ""
echo "==============================================================================="
echo "                     Building Aether Access 3.0 Packages"
echo "==============================================================================="
echo ""
echo "Components:"
echo "  - Aether Thrall  : Hardware Abstraction Layer"
echo "  - Aether Bifrost : API Server (the bridge)"
echo "  - Aether Saga    : Web Management Interface"
echo ""

# Check for ADK tools
if [ ! -f "$ADK_TOOLS/pack_app.sh" ]; then
    echo "ERROR: ADK tools not found at $ADK_TOOLS"
    exit 1
fi

if [ ! -f "$ADK_TOOLS/test-app-dev-sign.crt" ]; then
    echo "ERROR: Developer certificate not found!"
    echo "Place certificate at: $ADK_TOOLS/test-app-dev-sign.crt"
    exit 1
fi

# Create output directory
mkdir -p "$OUTPUT_DIR"

#-------------------------------------------------------------------------------
# Step 1: Build Aether Saga (React frontend)
#-------------------------------------------------------------------------------
echo "[1/4] Building Aether Saga frontend..."

if [ -d "$SCRIPT_DIR/aether_saga" ]; then
    cd "$SCRIPT_DIR/aether_saga"

    if [ -f "package.json" ]; then
        echo "  Installing dependencies..."
        npm install --silent 2>/dev/null || true

        echo "  Building React app..."
        npm run build 2>/dev/null || echo "  [WARN] Build failed, using existing dist"
    fi

    if [ -d "dist" ]; then
        echo "  Copying to ADK structure..."
        mkdir -p "$SCRIPT_DIR/adk/aether_saga/rootfs/app/static"
        rm -rf "$SCRIPT_DIR/adk/aether_saga/rootfs/app/static/"*
        cp -r dist/* "$SCRIPT_DIR/adk/aether_saga/rootfs/app/static/"
    else
        echo "  [WARN] Aether Saga dist not found"
    fi

    cd "$SCRIPT_DIR"
else
    echo "  [WARN] Aether Saga source not found"
fi

#-------------------------------------------------------------------------------
# Step 2: Update ADK structures with latest code
#-------------------------------------------------------------------------------
echo ""
echo "[2/4] Updating ADK structures..."

# Aether Thrall (HAL)
echo "  Updating Aether Thrall..."
mkdir -p "$SCRIPT_DIR/adk/aether_thrall/rootfs/app/python"
cp "$SCRIPT_DIR/python/hal_bindings.py" "$SCRIPT_DIR/adk/aether_thrall/rootfs/app/python/"
cp "$SCRIPT_DIR/requirements.txt" "$SCRIPT_DIR/adk/aether_thrall/rootfs/app/"

# Aether Bifrost (API)
echo "  Updating Aether Bifrost..."
mkdir -p "$SCRIPT_DIR/adk/aether_bifrost/rootfs/app/api"
cp "$SCRIPT_DIR/api/aether_bifrost.py" "$SCRIPT_DIR/adk/aether_bifrost/rootfs/app/api/"
cp "$SCRIPT_DIR/api/ambient_integration.py" "$SCRIPT_DIR/adk/aether_bifrost/rootfs/app/api/" 2>/dev/null || true
cp "$SCRIPT_DIR/api/api_v2_1.py" "$SCRIPT_DIR/adk/aether_bifrost/rootfs/app/api/" 2>/dev/null || true
cp "$SCRIPT_DIR/api/api_v2_2.py" "$SCRIPT_DIR/adk/aether_bifrost/rootfs/app/api/" 2>/dev/null || true
cp "$SCRIPT_DIR/api/auth.py" "$SCRIPT_DIR/adk/aether_bifrost/rootfs/app/api/" 2>/dev/null || true
cp "$SCRIPT_DIR/api/database.py" "$SCRIPT_DIR/adk/aether_bifrost/rootfs/app/api/" 2>/dev/null || true
cp "$SCRIPT_DIR/requirements.txt" "$SCRIPT_DIR/adk/aether_bifrost/rootfs/app/"

#-------------------------------------------------------------------------------
# Step 3: Build .app packages
#-------------------------------------------------------------------------------
echo ""
echo "[3/4] Building .app packages..."

cd "$ADK_TOOLS"

# Build Aether Thrall
echo "  Building aether_thrall.app..."
"$ADK_TOOLS/pack_app.sh" \
    -b "$ADK_TOOLS/layers/base.tar.bz2" \
    -a "$SCRIPT_DIR/adk/aether_thrall/rootfs" \
    -m "$SCRIPT_DIR/adk/aether_thrall/manifest" \
    -c "$ADK_TOOLS/test-app-dev-sign.crt" \
    -o "$OUTPUT_DIR/aether_thrall.app"

# Build Aether Bifrost
echo "  Building aether_bifrost.app..."
"$ADK_TOOLS/pack_app.sh" \
    -b "$ADK_TOOLS/layers/base.tar.bz2" \
    -a "$SCRIPT_DIR/adk/aether_bifrost/rootfs" \
    -m "$SCRIPT_DIR/adk/aether_bifrost/manifest" \
    -c "$ADK_TOOLS/test-app-dev-sign.crt" \
    -o "$OUTPUT_DIR/aether_bifrost.app"

# Build Aether Saga
echo "  Building aether_saga.app..."
"$ADK_TOOLS/pack_app.sh" \
    -b "$ADK_TOOLS/layers/base.tar.bz2" \
    -a "$SCRIPT_DIR/adk/aether_saga/rootfs" \
    -m "$SCRIPT_DIR/adk/aether_saga/manifest" \
    -c "$ADK_TOOLS/test-app-dev-sign.crt" \
    -o "$OUTPUT_DIR/aether_saga.app"

#-------------------------------------------------------------------------------
# Step 4: Generate checksums
#-------------------------------------------------------------------------------
echo ""
echo "[4/4] Generating checksums..."

cd "$OUTPUT_DIR"
shasum -a 256 aether_thrall.app > aether_thrall.app.sha256
shasum -a 256 aether_bifrost.app > aether_bifrost.app.sha256
shasum -a 256 aether_saga.app > aether_saga.app.sha256

#-------------------------------------------------------------------------------
# Done
#-------------------------------------------------------------------------------
echo ""
echo "==============================================================================="
echo "                           BUILD COMPLETE"
echo "==============================================================================="
echo ""
echo "Output directory: $OUTPUT_DIR/"
echo ""
echo "Packages created:"
ls -lh "$OUTPUT_DIR/"*.app 2>/dev/null
echo ""
echo "Checksums:"
cat "$OUTPUT_DIR/"*.sha256 2>/dev/null
echo ""
echo "Deployment:"
echo ""
echo "  Upload to Azure BLU-IC2 web interface:"
echo "    1. Open panel web interface"
echo "    2. Navigate to Applications"
echo "    3. Upload each .app file:"
echo "       - aether_thrall.app  (HAL)"
echo "       - aether_bifrost.app (API - port 8080)"
echo "       - aether_saga.app    (Web UI - port 80)"
echo ""
echo "  Or use SCP:"
echo "    scp $OUTPUT_DIR/*.app root@panel-ip:/tmp/"
echo ""
