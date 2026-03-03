#!/bin/bash
#
# HAL Complete System Startup Script
# Starts both REST API Server (inbound) and Event Export Daemon (outbound)
#

cd "$(dirname "$0")"

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                                                              ║"
echo "║         HAL COMPLETE SYSTEM                                  ║"
echo "║         Starting All Services...                             ║"
echo "║                                                              ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Configuration
HAL_HOST="${HAL_HOST:-localhost}"
HAL_PORT="${HAL_PORT:-8080}"
POLL_INTERVAL="${POLL_INTERVAL:-1}"
CONFIG_FILE="${CONFIG_FILE:-config/hal_config.json}"

# PID files
API_PID_FILE=".hal_api.pid"
EXPORT_PID_FILE=".hal_export.pid"

# Function to check if process is running
is_running() {
    local pid_file=$1
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p $pid > /dev/null 2>&1; then
            return 0
        fi
    fi
    return 1
}

# Function to stop services
stop_services() {
    echo ""
    echo "Stopping HAL services..."

    if is_running "$API_PID_FILE"; then
        local pid=$(cat "$API_PID_FILE")
        echo "  Stopping REST API Server (PID: $pid)..."
        kill $pid 2>/dev/null
        rm -f "$API_PID_FILE"
    fi

    if is_running "$EXPORT_PID_FILE"; then
        local pid=$(cat "$EXPORT_PID_FILE")
        echo "  Stopping Event Export Daemon (PID: $pid)..."
        kill $pid 2>/dev/null
        rm -f "$EXPORT_PID_FILE"
    fi

    echo "  All services stopped."
    echo ""
}

# Trap signals for cleanup
trap stop_services EXIT INT TERM

# Check if already running
if is_running "$API_PID_FILE" || is_running "$EXPORT_PID_FILE"; then
    echo "ERROR: HAL services are already running!"
    echo "Run './stop_hal_system.sh' first to stop them."
    exit 1
fi

# Check Python dependencies
echo "Checking dependencies..."
if ! python3 -c "import fastapi, uvicorn" 2>/dev/null; then
    echo "Installing Python dependencies..."
    if [ ! -d "venv" ]; then
        python3 -m venv venv
    fi
    source venv/bin/activate
    pip install -q -r api/requirements.txt
else
    if [ -d "venv" ]; then
        source venv/bin/activate
    fi
fi

# Check databases
if [ ! -f "hal_sdk.db" ]; then
    echo "Creating SDK database..."
    sqlite3 hal_sdk.db < schema/sdk_tables.sql
fi

if [ ! -f "hal_cards.db" ]; then
    echo "Creating card database..."
    sqlite3 hal_cards.db << 'EOF'
CREATE TABLE IF NOT EXISTS Cards (
    card_number INTEGER PRIMARY KEY,
    permission_id INTEGER,
    card_holder_name TEXT,
    activation_date INTEGER,
    expiration_date INTEGER,
    is_active INTEGER,
    pin INTEGER
);
EOF
fi

echo "✓ Dependencies checked"
echo ""

# Start REST API Server
echo "═══════════════════════════════════════════════════════════════"
echo "  Starting REST API Server (Inbound)                           "
echo "═══════════════════════════════════════════════════════════════"
echo "  Port: $HAL_PORT"
echo "  Config: $CONFIG_FILE"
echo ""

python3 api/hal_api_server.py > logs/api_server.log 2>&1 &
API_PID=$!
echo $API_PID > "$API_PID_FILE"

# Wait for API server to start
sleep 2

if ! is_running "$API_PID_FILE"; then
    echo "ERROR: REST API Server failed to start!"
    echo "Check logs/api_server.log for details."
    exit 1
fi

echo "✓ REST API Server started (PID: $API_PID)"
echo "  Access API documentation: http://localhost:$HAL_PORT/docs"
echo ""

# Start Event Export Daemon
echo "═══════════════════════════════════════════════════════════════"
echo "  Starting Event Export Daemon (Outbound)                      "
echo "═══════════════════════════════════════════════════════════════"
echo "  HAL Controller: $HAL_HOST:$HAL_PORT"
echo "  Poll Interval: ${POLL_INTERVAL}s"
echo "  Config: $CONFIG_FILE"
echo ""

./hal_event_export_daemon -c "$CONFIG_FILE" -h "$HAL_HOST" -p "$HAL_PORT" -i "$POLL_INTERVAL" > logs/event_export.log 2>&1 &
EXPORT_PID=$!
echo $EXPORT_PID > "$EXPORT_PID_FILE"

# Wait for export daemon to start
sleep 2

if ! is_running "$EXPORT_PID_FILE"; then
    echo "ERROR: Event Export Daemon failed to start!"
    echo "Check logs/event_export.log for details."
    stop_services
    exit 1
fi

echo "✓ Event Export Daemon started (PID: $EXPORT_PID)"
echo ""

# Display status
echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                                                              ║"
echo "║         HAL SYSTEM RUNNING                                   ║"
echo "║                                                              ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "Services:"
echo "  ✓ REST API Server       (PID: $API_PID)"
echo "    http://localhost:$HAL_PORT"
echo "    http://localhost:$HAL_PORT/docs"
echo ""
echo "  ✓ Event Export Daemon   (PID: $EXPORT_PID)"
echo "    → Ambient.ai integration active"
echo ""
echo "Logs:"
echo "  API Server:      tail -f logs/api_server.log"
echo "  Event Export:    tail -f logs/event_export.log"
echo ""
echo "Management:"
echo "  Stop services:   ./stop_hal_system.sh"
echo "  View status:     ./status_hal_system.sh"
echo ""
echo "Press Ctrl+C to stop all services..."
echo ""

# Keep script running and monitor services
while true; do
    sleep 5

    # Check if API server is still running
    if ! is_running "$API_PID_FILE"; then
        echo "WARNING: REST API Server stopped unexpectedly!"
        echo "Check logs/api_server.log for details."
        stop_services
        exit 1
    fi

    # Check if export daemon is still running
    if ! is_running "$EXPORT_PID_FILE"; then
        echo "WARNING: Event Export Daemon stopped unexpectedly!"
        echo "Check logs/event_export.log for details."
        stop_services
        exit 1
    fi
done
