#!/bin/sh
#===============================================================================
# Aether Saga - Web Management Interface for Aether Access 3.0
# Serves the React frontend on port 80
# Entry Point Script
#===============================================================================

logger "Aether Saga: Starting web server..."

# Create directories
mkdir -p /app/data
mkdir -p /app/logs

# Set environment
export SAGA_PORT=80
export SAGA_LOG_PATH="/app/logs/aether_saga.log"

# Log startup
logger "Aether Saga: Serving static files on port $SAGA_PORT"

cd /app/static

# Start simple Python HTTP server to serve the React build
# In production, this could be nginx or another web server
logger "Aether Saga: Starting HTTP server on port $SAGA_PORT..."

exec python3 -m http.server $SAGA_PORT --directory /app/static
