#!/bin/bash
##############################################################################
# Aether Access PoC - Start Script
#
# Starts the HAL Engine and Ambient Forwarder components.
#
# Author: FAM-HAL-v1.0-001
# Date: February 10, 2026
##############################################################################

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
POC_DIR="$(dirname "$SCRIPT_DIR")"
BUILD_DIR="${POC_DIR}/build"
DATA_DIR="${POC_DIR}/data"
LOG_DIR="${POC_DIR}/logs"
CONFIG_DIR="${POC_DIR}/config"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if executables exist
check_build() {
    if [ ! -f "${BUILD_DIR}/hal_engine" ]; then
        log_error "HAL Engine not found. Run 'make' in ${BUILD_DIR} first."
        exit 1
    fi
    if [ ! -f "${BUILD_DIR}/ambient_forwarder" ]; then
        log_error "Ambient Forwarder not found. Run 'make' in ${BUILD_DIR} first."
        exit 1
    fi
    log_success "Build found"
}

# Create required directories
create_dirs() {
    mkdir -p "${DATA_DIR}"
    mkdir -p "${LOG_DIR}"
    log_success "Directories created"
}

# Check if already running
check_running() {
    if pgrep -x "hal_engine" > /dev/null 2>&1; then
        log_warn "HAL Engine is already running"
        return 1
    fi
    if pgrep -x "ambient_forwarder" > /dev/null 2>&1; then
        log_warn "Ambient Forwarder is already running"
        return 1
    fi
    return 0
}

# Start HAL Engine
start_hal_engine() {
    log_info "Starting HAL Engine..."

    local CONFIG="${CONFIG_DIR}/hal_engine.json"
    local OPTS="--simulation"  # Enable simulation mode for testing

    if [ -n "$1" ]; then
        OPTS="$OPTS $1"
    fi

    "${BUILD_DIR}/hal_engine" \
        --config "${CONFIG}" \
        ${OPTS} \
        > "${LOG_DIR}/hal_engine.log" 2>&1 &

    local PID=$!
    echo $PID > "${DATA_DIR}/hal_engine.pid"

    sleep 1
    if kill -0 $PID 2>/dev/null; then
        log_success "HAL Engine started (PID: $PID)"
    else
        log_error "HAL Engine failed to start"
        cat "${LOG_DIR}/hal_engine.log"
        exit 1
    fi
}

# Start Ambient Forwarder
start_forwarder() {
    log_info "Starting Ambient Forwarder..."

    local CONFIG="${CONFIG_DIR}/ambient_forwarder.json"
    local DEVICES="${CONFIG_DIR}/devices.json"
    local OPTS=""

    if [ -n "$1" ]; then
        OPTS="$1"
    fi

    "${BUILD_DIR}/ambient_forwarder" \
        --config "${CONFIG}" \
        --devices "${DEVICES}" \
        ${OPTS} \
        > "${LOG_DIR}/forwarder.log" 2>&1 &

    local PID=$!
    echo $PID > "${DATA_DIR}/forwarder.pid"

    sleep 1
    if kill -0 $PID 2>/dev/null; then
        log_success "Ambient Forwarder started (PID: $PID)"
    else
        log_error "Ambient Forwarder failed to start"
        cat "${LOG_DIR}/forwarder.log"
        exit 1
    fi
}

# Main
main() {
    echo ""
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║          Aether Access PoC - Start Script                    ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo ""

    check_build
    create_dirs

    if ! check_running; then
        log_warn "Use --force to restart running services"
        if [ "$1" != "--force" ]; then
            exit 1
        fi
        log_info "Stopping existing services..."
        "${SCRIPT_DIR}/stop_poc.sh"
        sleep 2
    fi

    start_hal_engine "$2"
    sleep 2
    start_forwarder "$3"

    echo ""
    log_success "All services started!"
    echo ""
    echo "  Monitor events:    ${BUILD_DIR}/monitor_events"
    echo "  Simulate badge:    ${BUILD_DIR}/simulate_badge test john"
    echo "  View HAL logs:     ${BUILD_DIR}/hal_logs -f"
    echo "  Check status:      ${BUILD_DIR}/hal_status"
    echo "  Stop services:     ${SCRIPT_DIR}/stop_poc.sh"
    echo ""
}

main "$@"
