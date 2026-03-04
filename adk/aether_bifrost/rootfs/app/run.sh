#!/bin/sh
#===============================================================================
# Aether Bifrost - API Server for Aether Access 3.0
# The bridge between Aether Saga and Aether Thrall
# Entry Point Script
#===============================================================================

logger "Aether Bifrost: Starting API server..."

# Create data directories
mkdir -p /app/data
mkdir -p /app/pdata
mkdir -p /app/logs

# Set environment
export HAL_DATABASE_PATH="/app/data/hal_database.db"
export HAL_LOG_PATH="/app/logs/aether_bifrost.log"
export HAL_API_PORT=8080
export HAL_LOG_LEVEL="INFO"

# Ambient.ai configuration (optional)
# export AMBIENT_API_KEY="your-api-key"
# export AMBIENT_SOURCE_SYSTEM_UID="your-system-uuid"

# Use Azure SDK environment variables if available
if [ -n "$ASP_MASTER_HOSTNAME" ]; then
    export HAL_SDK_HOST=$ASP_MASTER_HOSTNAME
    export HAL_SDK_PORT=$ASP_MASTER_PORT
    logger "Aether Bifrost: SDK connection configured - $ASP_MASTER_HOSTNAME:$ASP_MASTER_PORT"
fi

# Log startup
logger "Aether Bifrost: Database path: $HAL_DATABASE_PATH"
logger "Aether Bifrost: API port: $HAL_API_PORT"

# Start the Python virtual environment if needed
if [ -d "/app/venv" ]; then
    . /app/venv/bin/activate
fi

# Start the Bifrost API server
cd /app
logger "Aether Bifrost: Starting on port $HAL_API_PORT..."

# Run the API server (blocking - managed by ADK supervisor)
exec python3 /app/api/aether_bifrost.py
