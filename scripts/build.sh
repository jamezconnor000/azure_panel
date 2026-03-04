#!/bin/bash
set -e

echo "==============================================================================="
echo "              Building Aether HAL - Hardware Abstraction Layer"
echo "==============================================================================="

# Detect platform
if [[ "$(uname)" == "Darwin" ]]; then
    NPROC=$(sysctl -n hw.ncpu)
else
    NPROC=$(nproc)
fi

# Build directory
mkdir -p build
cd build

# Configure with CMake
echo "[1/3] Configuring Aether HAL..."
cmake -DCMAKE_BUILD_TYPE=Release ..

# Build
echo "[2/3] Building Aether HAL..."
make -j$NPROC

# Install locally
echo "[3/3] Installing libraries..."
make install DESTDIR=../dist 2>/dev/null || true

cd ..

echo ""
echo "==============================================================================="
echo "                        Aether HAL Build Complete"
echo "==============================================================================="
echo ""
echo "Binaries available in: ./build/"
echo "  - libhal_core.a           HAL Core Library"
echo "  - libsdk_wrapper.a        SDK Wrapper"
echo "  - libhal_utils.a          Utility Library"
echo ""
echo "Test with:  ./scripts/test.sh"
echo "Examples:   ./build/example_basic"
echo ""
