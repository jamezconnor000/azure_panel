#!/bin/sh
#===============================================================================
# Aether Loom - The Weaver of Code
# Interactive code terminal for Aether Access 4.0
#
# "From the Loom, all code is woven."
#===============================================================================

logger "Aether Loom: Starting The Weaver of Code..."

# Create directories
mkdir -p /app/data
mkdir -p /app/logs

# Set environment
export LOOM_PORT=6969
export PYTHONUNBUFFERED=1

# Log startup
logger "Aether Loom: Web terminal starting on port $LOOM_PORT"

cd /app

# Start the Loom
exec python3 /app/aether_loom.py
