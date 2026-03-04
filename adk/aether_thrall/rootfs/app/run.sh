#!/bin/sh
#===============================================================================
# Aether Thrall - Hardware Abstraction Layer for Azure BLU-IC2 Controllers
# Part of Aether Access 3.0
# Entry Point Script
#===============================================================================

logger "Aether Thrall: Starting HAL..."

# Create data directories
mkdir -p /app/data
mkdir -p /app/pdata
mkdir -p /app/logs

# Set environment
export HAL_DATABASE_PATH="/app/data/hal_database.db"
export HAL_LOG_PATH="/app/logs/aether_thrall.log"
export HAL_LOG_LEVEL="INFO"

# Use Azure SDK environment variables if available
if [ -n "$ASP_MASTER_HOSTNAME" ]; then
    export HAL_SDK_HOST=$ASP_MASTER_HOSTNAME
    export HAL_SDK_PORT=$ASP_MASTER_PORT
    logger "Aether Thrall: SDK connection configured - $ASP_MASTER_HOSTNAME:$ASP_MASTER_PORT"
fi

# Log startup
logger "Aether Thrall: Database path: $HAL_DATABASE_PATH"
logger "Aether Thrall: HAL initialized"

# Start the Python virtual environment if needed
if [ -d "/app/venv" ]; then
    . /app/venv/bin/activate
fi

# The HAL runs as a daemon, connecting to hardware
cd /app

# Run HAL bindings daemon (monitoring mode)
logger "Aether Thrall: Starting HAL bindings daemon..."
exec python3 -c "
import sys
sys.path.insert(0, '/app/python')
from hal_bindings import HAL
import time

hal = HAL()
hal.initialize()
print('Aether Thrall: HAL running...')

# Keep running until terminated
while True:
    time.sleep(60)
    # HAL handles events internally
"
