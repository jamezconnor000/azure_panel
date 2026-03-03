#!/bin/bash
set -e

echo "Building HAL Project..."

mkdir -p build
cd build

cmake ..
make -j$(nproc)
make install

cd ..

echo "✓ Build complete"
echo "Run tests with: ./scripts/test.sh"
echo "Run examples with: ./examples/basic_access"
