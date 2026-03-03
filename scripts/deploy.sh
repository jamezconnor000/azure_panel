#!/bin/bash
set -e

echo "Deploying HAL..."

# Build
./scripts/build.sh

# Install
cd build
sudo make install
cd ..

# Setup permissions
sudo chmod 644 /usr/local/lib/libhal_core.so
sudo chmod 644 /usr/local/include/hal_public.h

echo "✓ Deployment complete"
echo "HAL installed to /usr/local/lib and /usr/local/include"
