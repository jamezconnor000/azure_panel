#!/bin/bash
set -e

echo "Running HAL Tests..."

cd build
cmake ..
make -j$(nproc)

ctest --output-on-failure

cd ..

echo "✓ All tests passed"
