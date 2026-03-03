#!/bin/bash
#
# Stop HAL + Aether Access System
#

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Stopping HAL + Aether Access System..."

# Stop Aether Access
if [ -f "$SCRIPT_DIR/.pids/aether_access.pid" ]; then
    PID=$(cat "$SCRIPT_DIR/.pids/aether_access.pid")
    if kill -0 "$PID" 2>/dev/null; then
        echo "Stopping Aether Access (PID: $PID)..."
        kill "$PID"
    fi
    rm "$SCRIPT_DIR/.pids/aether_access.pid"
fi

# Stop HAL Core
if [ -f "$SCRIPT_DIR/.pids/hal_core.pid" ]; then
    PID=$(cat "$SCRIPT_DIR/.pids/hal_core.pid")
    if kill -0 "$PID" 2>/dev/null; then
        echo "Stopping HAL Core (PID: $PID)..."
        kill "$PID"
    fi
    rm "$SCRIPT_DIR/.pids/hal_core.pid"
fi

echo "System stopped."
