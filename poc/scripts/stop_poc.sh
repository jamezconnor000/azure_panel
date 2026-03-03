#!/bin/bash
##############################################################################
# Aether Access PoC - Stop Script
#
# Stops the HAL Engine and Ambient Forwarder components.
#
# Author: FAM-HAL-v1.0-001
# Date: February 10, 2026
##############################################################################

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
POC_DIR="$(dirname "$SCRIPT_DIR")"
DATA_DIR="${POC_DIR}/data"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "[INFO] $1"
}

log_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

# Stop process by PID file
stop_by_pid_file() {
    local NAME="$1"
    local PID_FILE="$2"

    if [ -f "$PID_FILE" ]; then
        local PID=$(cat "$PID_FILE")
        if kill -0 "$PID" 2>/dev/null; then
            log_info "Stopping $NAME (PID: $PID)..."
            kill "$PID"
            sleep 1
            if kill -0 "$PID" 2>/dev/null; then
                log_warn "$NAME didn't stop gracefully, sending SIGKILL..."
                kill -9 "$PID" 2>/dev/null
            fi
            log_success "$NAME stopped"
        else
            log_warn "$NAME not running (stale PID file)"
        fi
        rm -f "$PID_FILE"
    fi
}

# Stop process by name
stop_by_name() {
    local NAME="$1"

    if pgrep -x "$NAME" > /dev/null 2>&1; then
        log_info "Stopping $NAME by name..."
        pkill -x "$NAME"
        sleep 1
        if pgrep -x "$NAME" > /dev/null 2>&1; then
            log_warn "$NAME didn't stop gracefully, sending SIGKILL..."
            pkill -9 -x "$NAME" 2>/dev/null
        fi
        log_success "$NAME stopped"
    fi
}

# Main
main() {
    echo ""
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║          Aether Access PoC - Stop Script                     ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo ""

    # Stop Forwarder first (it depends on HAL Engine)
    stop_by_pid_file "Ambient Forwarder" "${DATA_DIR}/forwarder.pid"
    stop_by_name "ambient_forwarder"

    # Stop HAL Engine
    stop_by_pid_file "HAL Engine" "${DATA_DIR}/hal_engine.pid"
    stop_by_name "hal_engine"

    # Clean up socket
    rm -f /tmp/hal_events.sock
    rm -f /tmp/hal_wiegand.fifo

    echo ""
    log_success "All services stopped"
    echo ""
}

main "$@"
