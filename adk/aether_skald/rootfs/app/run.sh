#!/bin/sh
#===============================================================================
# Aether Skald - Event Chronicle & Audit Trail
# Part of Aether Access 4.0 "Bifrost's Light"
# The Storyteller - Records all that transpires
#===============================================================================

logger "Aether Skald: The Storyteller awakens..."

# Create data directories
mkdir -p /app/data
mkdir -p /app/pdata
mkdir -p /app/logs
mkdir -p /app/data/chronicles

# Set environment
export SKALD_DATABASE_PATH="/app/data/chronicle.db"
export SKALD_LOG_PATH="/app/logs/aether_skald.log"
export SKALD_CHRONICLE_PATH="/app/data/chronicles"
export SKALD_LOG_LEVEL="INFO"
export SKALD_PORT=8090

# Connection to other Aether components
export THRALL_SOCKET="/var/run/thrall.sock"
export BIFROST_URL="http://localhost:8080"

logger "Aether Skald: Chronicle database: $SKALD_DATABASE_PATH"
logger "Aether Skald: Chronicle storage: $SKALD_CHRONICLE_PATH"

# Start the Python virtual environment if needed
if [ -d "/app/venv" ]; then
    . /app/venv/bin/activate
fi

cd /app

# Run the Skald daemon
logger "Aether Skald: Starting event chronicle service on port $SKALD_PORT..."
exec python3 /app/skald.py
