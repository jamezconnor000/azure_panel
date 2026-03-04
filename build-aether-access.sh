#!/bin/bash
#===============================================================================
#  ᚨ ᛖ ᚦ ᛖ ᚱ   A C C E S S   4 . 0
#  "BIFROST'S LIGHT"
#  Complete Build Script for Azure BLU-IC2 Controllers
#
#  Components:
#    - Aether Thrall   (HAL - Hardware Abstraction Layer)
#    - Aether Bifrost  (API + Familiar AI Assistant)
#    - Aether Saga     (Web Management Interface)
#    - Aether Skald    (Event Chronicle & Audit Trail)
#
#  "The machines answer to US."
#===============================================================================

set -e

# Add GNU tools to PATH for compatibility
export PATH="$PATH:/opt/homebrew/opt/coreutils/libexec/gnubin:/opt/homebrew/opt/binutils/bin"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VERSION=$(cat "$SCRIPT_DIR/VERSION" 2>/dev/null || echo "4.0.0")
OUTPUT_DIR="$SCRIPT_DIR/deploy"
ADK_TOOLS="/Users/mosley/AXIOM/Projects/Azure_Panel/Relics/adk_1.22.1_20250903-213533"
CERT="$ADK_TOOLS/tiktok-app-dev-sign.crt"

echo ""
echo "  ╔═══════════════════════════════════════════════════════════════════════╗"
echo "  ║           ᚨ ᛖ ᚦ ᛖ ᚱ   A C C E S S   4 . 0                           ║"
echo "  ║                    \"BIFROST'S LIGHT\"                                  ║"
echo "  ║                                                                       ║"
echo "  ║   Complete Access Control System for Azure BLU-IC2                    ║"
echo "  ╚═══════════════════════════════════════════════════════════════════════╝"
echo ""
echo "  Version: $VERSION"
echo "  ADK: 1.22.1"
echo ""
echo "  Components:"
echo "    • Aether Thrall   - Hardware Abstraction Layer (source of truth)"
echo "    • Aether Bifrost  - API Server + Familiar AI Assistant"
echo "    • Aether Saga     - Web Management Interface"
echo "    • Aether Skald    - Event Chronicle & Audit Trail"
echo ""
echo "==============================================================================="
echo ""

# Check for ADK tools
if [ ! -f "$ADK_TOOLS/pack_app.sh" ]; then
    echo "ERROR: ADK tools not found at $ADK_TOOLS"
    echo "Please extract adk_1.23.0_20260115-170502.zip to Relics/"
    exit 1
fi

if [ ! -f "$CERT" ]; then
    echo "ERROR: Developer certificate not found!"
    echo "Place certificate at: $CERT"
    exit 1
fi

# Create output directory
mkdir -p "$OUTPUT_DIR"

#-------------------------------------------------------------------------------
# Step 1: Build Aether Saga (React frontend)
#-------------------------------------------------------------------------------
echo "[1/6] Building Aether Saga frontend..."

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
echo "[2/6] Updating ADK structures..."

# Aether Thrall (HAL)
echo "  Updating Aether Thrall..."
mkdir -p "$SCRIPT_DIR/adk/aether_thrall/rootfs/app/python"
cp "$SCRIPT_DIR/python/hal_bindings.py" "$SCRIPT_DIR/adk/aether_thrall/rootfs/app/python/"
cp "$SCRIPT_DIR/requirements.txt" "$SCRIPT_DIR/adk/aether_thrall/rootfs/app/"

# Aether Bifrost (API + Familiar)
echo "  Updating Aether Bifrost..."
mkdir -p "$SCRIPT_DIR/adk/aether_bifrost/rootfs/app/api"
mkdir -p "$SCRIPT_DIR/adk/aether_bifrost/rootfs/app/api/familiar"
cp "$SCRIPT_DIR/api/aether_bifrost.py" "$SCRIPT_DIR/adk/aether_bifrost/rootfs/app/api/"
cp "$SCRIPT_DIR/api/ambient_integration.py" "$SCRIPT_DIR/adk/aether_bifrost/rootfs/app/api/" 2>/dev/null || true
cp "$SCRIPT_DIR/api/api_v2_1.py" "$SCRIPT_DIR/adk/aether_bifrost/rootfs/app/api/" 2>/dev/null || true
cp "$SCRIPT_DIR/api/api_v2_2.py" "$SCRIPT_DIR/adk/aether_bifrost/rootfs/app/api/" 2>/dev/null || true
cp "$SCRIPT_DIR/api/auth.py" "$SCRIPT_DIR/adk/aether_bifrost/rootfs/app/api/" 2>/dev/null || true
cp "$SCRIPT_DIR/api/database.py" "$SCRIPT_DIR/adk/aether_bifrost/rootfs/app/api/" 2>/dev/null || true

# Copy Familiar module
if [ -d "$SCRIPT_DIR/api/familiar" ]; then
    cp -r "$SCRIPT_DIR/api/familiar/"* "$SCRIPT_DIR/adk/aether_bifrost/rootfs/app/api/familiar/"
    echo "    Familiar AI module included"
fi

cp "$SCRIPT_DIR/requirements.txt" "$SCRIPT_DIR/adk/aether_bifrost/rootfs/app/"

# Aether Skald (Event Chronicle)
echo "  Updating Aether Skald..."
mkdir -p "$SCRIPT_DIR/adk/aether_skald/rootfs/app"
cp "$SCRIPT_DIR/api/aether_skald.py" "$SCRIPT_DIR/adk/aether_skald/rootfs/app/skald.py"
cp "$SCRIPT_DIR/requirements.txt" "$SCRIPT_DIR/adk/aether_skald/rootfs/app/"

#-------------------------------------------------------------------------------
# Step 3: Build .app packages
#-------------------------------------------------------------------------------
echo ""
echo "[3/6] Building .app packages..."

cd "$ADK_TOOLS"

# Build Aether Thrall
echo "  Building aether_thrall.app..."
"$ADK_TOOLS/pack_app.sh" \
    -b "$ADK_TOOLS/layers/base.tar.bz2" \
    -a "$SCRIPT_DIR/adk/aether_thrall/rootfs" \
    -m "$SCRIPT_DIR/adk/aether_thrall/manifest" \
    -c "$CERT" \
    -o "$OUTPUT_DIR/aether_thrall.app"

# Build Aether Bifrost
echo "  Building aether_bifrost.app..."
"$ADK_TOOLS/pack_app.sh" \
    -b "$ADK_TOOLS/layers/base.tar.bz2" \
    -a "$SCRIPT_DIR/adk/aether_bifrost/rootfs" \
    -m "$SCRIPT_DIR/adk/aether_bifrost/manifest" \
    -c "$CERT" \
    -o "$OUTPUT_DIR/aether_bifrost.app"

# Build Aether Saga
echo "  Building aether_saga.app..."
"$ADK_TOOLS/pack_app.sh" \
    -b "$ADK_TOOLS/layers/base.tar.bz2" \
    -a "$SCRIPT_DIR/adk/aether_saga/rootfs" \
    -m "$SCRIPT_DIR/adk/aether_saga/manifest" \
    -c "$CERT" \
    -o "$OUTPUT_DIR/aether_saga.app"

# Build Aether Skald
echo "  Building aether_skald.app..."
"$ADK_TOOLS/pack_app.sh" \
    -b "$ADK_TOOLS/layers/base.tar.bz2" \
    -a "$SCRIPT_DIR/adk/aether_skald/rootfs" \
    -m "$SCRIPT_DIR/adk/aether_skald/manifest" \
    -c "$CERT" \
    -o "$OUTPUT_DIR/aether_skald.app"

#-------------------------------------------------------------------------------
# Step 4: Generate checksums
#-------------------------------------------------------------------------------
echo ""
echo "[4/6] Generating checksums..."

cd "$OUTPUT_DIR"
shasum -a 256 aether_thrall.app > aether_thrall.app.sha256
shasum -a 256 aether_bifrost.app > aether_bifrost.app.sha256
shasum -a 256 aether_saga.app > aether_saga.app.sha256
shasum -a 256 aether_skald.app > aether_skald.app.sha256

#-------------------------------------------------------------------------------
# Step 5: Create release manifest
#-------------------------------------------------------------------------------
echo ""
echo "[5/6] Creating release manifest..."

cat > "$OUTPUT_DIR/RELEASE.json" << EOF
{
  "name": "Aether Access",
  "codename": "Bifrost's Light",
  "version": "$VERSION",
  "adk_version": "1.22.1",
  "build_date": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "components": [
    {
      "id": "aether_thrall",
      "name": "Aether Thrall",
      "description": "Hardware Abstraction Layer - Source of Truth",
      "version": "$VERSION",
      "ports": []
    },
    {
      "id": "aether_bifrost",
      "name": "Aether Bifrost",
      "description": "API Server with Familiar AI Assistant",
      "version": "$VERSION",
      "ports": [8080]
    },
    {
      "id": "aether_saga",
      "name": "Aether Saga",
      "description": "Web Management Interface",
      "version": "$VERSION",
      "ports": [80]
    },
    {
      "id": "aether_skald",
      "name": "Aether Skald",
      "description": "Event Chronicle & Audit Trail",
      "version": "$VERSION",
      "ports": [8090]
    }
  ],
  "motto": "The machines answer to US."
}
EOF

#-------------------------------------------------------------------------------
# Step 6: Summary
#-------------------------------------------------------------------------------
echo ""
echo "[6/6] Finalizing..."

echo ""
echo "  ╔═══════════════════════════════════════════════════════════════════════╗"
echo "  ║                       BUILD COMPLETE                                  ║"
echo "  ║                  AETHER ACCESS 4.0 - BIFROST'S LIGHT                  ║"
echo "  ╚═══════════════════════════════════════════════════════════════════════╝"
echo ""
echo "  Output directory: $OUTPUT_DIR/"
echo ""
echo "  Packages created:"
ls -lh "$OUTPUT_DIR/"*.app 2>/dev/null
echo ""
echo "  Checksums:"
cat "$OUTPUT_DIR/"*.sha256 2>/dev/null
echo ""
echo "  ┌─────────────────────────────────────────────────────────────────────┐"
echo "  │                        DEPLOYMENT                                   │"
echo "  ├─────────────────────────────────────────────────────────────────────┤"
echo "  │                                                                     │"
echo "  │  Upload to Azure BLU-IC2 web interface:                            │"
echo "  │    1. Open panel web interface                                     │"
echo "  │    2. Navigate to Applications                                     │"
echo "  │    3. Upload each .app file:                                       │"
echo "  │       • aether_thrall.app  (HAL - no port)                        │"
echo "  │       • aether_bifrost.app (API + Familiar - port 8080)           │"
echo "  │       • aether_saga.app    (Web UI - port 80)                     │"
echo "  │       • aether_skald.app   (Chronicle - port 8090)                │"
echo "  │                                                                     │"
echo "  │  Or use SCP:                                                        │"
echo "  │    scp $OUTPUT_DIR/*.app root@panel-ip:/tmp/                       │"
echo "  │                                                                     │"
echo "  └─────────────────────────────────────────────────────────────────────┘"
echo ""
echo "  \"The Skald remembers all. The machines answer to US.\""
echo ""
