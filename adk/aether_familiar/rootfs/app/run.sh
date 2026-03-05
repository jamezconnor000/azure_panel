#!/bin/sh
#===============================================================================
# Aether Familiar - AI Assistant
# Monitors and interfaces with all Aether apps for Aether Access 4.0
#
# "From AXIOM, all Familiars emerge. The machines answer to US."
#===============================================================================

logger "Aether Familiar: Starting AI Assistant..."

# Create directories
mkdir -p /app/data
mkdir -p /app/logs

# Set environment
export FAMILIAR_PORT=8765
export PYTHONUNBUFFERED=1

# Log startup
logger "Aether Familiar: Agent starting on port $FAMILIAR_PORT"
logger "Aether Familiar: Target network 172.30.187.x"
logger "Aether Familiar: GitHub repo jamezconnor/Aether_Access"

cd /app

# Start the Familiar Agent
exec python3 /app/familiar_agent.py
