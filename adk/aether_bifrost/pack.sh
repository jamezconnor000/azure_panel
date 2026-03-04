#!/bin/bash
#===============================================================================
# Aether Bifrost - Pack Script
# Creates .app package for Azure ADK deployment
#===============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ADK_TOOLS="/Users/mosley/AXIOM/Projects/Azure_Panel/Relics/adk_1.22.1_20250903-213533"
OUTPUT_DIR="$SCRIPT_DIR/../../deploy"

echo "Packing Aether Bifrost..."

if [ ! -f "$ADK_TOOLS/test-app-dev-sign.crt" ]; then
    echo "ERROR: Developer certificate not found!"
    echo "Place certificate at: $ADK_TOOLS/test-app-dev-sign.crt"
    exit 1
fi

cd "$ADK_TOOLS"

"$ADK_TOOLS/pack_app.sh" \
    -b "$ADK_TOOLS/layers/base.tar.bz2" \
    -a "$SCRIPT_DIR/rootfs" \
    -m "$SCRIPT_DIR/manifest" \
    -c "$ADK_TOOLS/test-app-dev-sign.crt" \
    -o "$OUTPUT_DIR/aether_bifrost.app"

cd "$OUTPUT_DIR"
shasum -a 256 aether_bifrost.app > aether_bifrost.app.sha256

echo "Created: $OUTPUT_DIR/aether_bifrost.app"
