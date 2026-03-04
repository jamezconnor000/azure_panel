#!/bin/sh
#===============================================================================
# Aether HAL - Hardware Abstraction Layer for Azure BLU-IC2 Controllers
# Version: 2.0.0
# Entry Point Script
#===============================================================================

logger "Aether HAL: Starting..."

# Create data directories
mkdir -p /app/data
mkdir -p /app/pdata
mkdir -p /app/logs

# Set environment
export HAL_DATABASE_PATH="/app/data/hal_database.db"
export HAL_LOG_PATH="/app/logs/aether_hal.log"
export HAL_API_PORT=8080
export HAL_LOG_LEVEL="INFO"

# Use Azure SDK environment variables if available
if [ -n "$ASP_MASTER_HOSTNAME" ]; then
    export HAL_SDK_HOST=$ASP_MASTER_HOSTNAME
    export HAL_SDK_PORT=$ASP_MASTER_PORT
    logger "Aether HAL: SDK connection configured - $ASP_MASTER_HOSTNAME:$ASP_MASTER_PORT"
fi

# Log startup
logger "Aether HAL: Database path: $HAL_DATABASE_PATH"
logger "Aether HAL: API port: $HAL_API_PORT"

# Start the Python virtual environment if needed
if [ -d "/app/venv" ]; then
    . /app/venv/bin/activate
fi

# Start the unified API server
cd /app
logger "Aether HAL: Starting API server on port $HAL_API_PORT..."

# Run the API server (blocking - will be managed by systemd/supervisor)
exec python3 /app/api/unified_api_server.py
