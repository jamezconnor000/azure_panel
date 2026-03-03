#!/bin/bash
#
# HAL System Status Script
# Shows status of REST API Server and Event Export Daemon
#

cd "$(dirname "$0")"

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                                                              ║"
echo "║         HAL SYSTEM STATUS                                    ║"
echo "║                                                              ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

API_PID_FILE=".hal_api.pid"
EXPORT_PID_FILE=".hal_export.pid"

running=0

# Check REST API Server
echo "REST API Server:"
if [ -f "$API_PID_FILE" ]; then
    API_PID=$(cat "$API_PID_FILE")
    if ps -p $API_PID > /dev/null 2>&1; then
        echo "  Status:  ✓ RUNNING"
        echo "  PID:     $API_PID"
        echo "  Port:    8080"
        echo "  API:     http://localhost:8080/docs"

        # Check if port is actually listening
        if command -v lsof > /dev/null 2>&1; then
            if lsof -Pi :8080 -sTCP:LISTEN -t > /dev/null 2>&1; then
                echo "  Network: ✓ Listening on port 8080"
            else
                echo "  Network: ⚠ Not listening on port 8080"
            fi
        fi

        running=$((running + 1))
    else
        echo "  Status:  ✗ STOPPED (stale PID file)"
        rm -f "$API_PID_FILE"
    fi
else
    echo "  Status:  ✗ STOPPED"
fi
echo ""

# Check Event Export Daemon
echo "Event Export Daemon:"
if [ -f "$EXPORT_PID_FILE" ]; then
    EXPORT_PID=$(cat "$EXPORT_PID_FILE")
    if ps -p $EXPORT_PID > /dev/null 2>&1; then
        echo "  Status:  ✓ RUNNING"
        echo "  PID:     $EXPORT_PID"

        # Try to read config for destination
        if [ -f "config/hal_config.json" ]; then
            if command -v python3 > /dev/null 2>&1; then
                DEST=$(python3 -c "import json; c=json.load(open('config/hal_config.json')); print(c.get('ambient_ai',{}).get('server_url','N/A'))" 2>/dev/null)
                ENABLED=$(python3 -c "import json; c=json.load(open('config/hal_config.json')); print(c.get('ambient_ai',{}).get('enabled',False))" 2>/dev/null)
                echo "  Export:  → $DEST"
                echo "  Enabled: $ENABLED"
            fi
        fi

        running=$((running + 1))
    else
        echo "  Status:  ✗ STOPPED (stale PID file)"
        rm -f "$EXPORT_PID_FILE"
    fi
else
    echo "  Status:  ✗ STOPPED"
fi
echo ""

# Check log files
echo "Log Files:"
if [ -f "logs/api_server.log" ]; then
    LOG_SIZE=$(du -h logs/api_server.log | cut -f1)
    LOG_LINES=$(wc -l < logs/api_server.log)
    echo "  API Server:     logs/api_server.log ($LOG_SIZE, $LOG_LINES lines)"
else
    echo "  API Server:     No log file"
fi

if [ -f "logs/event_export.log" ]; then
    LOG_SIZE=$(du -h logs/event_export.log | cut -f1)
    LOG_LINES=$(wc -l < logs/event_export.log)
    echo "  Event Export:   logs/event_export.log ($LOG_SIZE, $LOG_LINES lines)"
else
    echo "  Event Export:   No log file"
fi
echo ""

# Check databases
echo "Databases:"
if [ -f "hal_sdk.db" ]; then
    DB_SIZE=$(du -h hal_sdk.db | cut -f1)
    echo "  SDK Database:   hal_sdk.db ($DB_SIZE)"
else
    echo "  SDK Database:   ✗ Not found"
fi

if [ -f "hal_cards.db" ]; then
    DB_SIZE=$(du -h hal_cards.db | cut -f1)

    # Count cards if sqlite3 is available
    if command -v sqlite3 > /dev/null 2>&1; then
        CARD_COUNT=$(sqlite3 hal_cards.db "SELECT COUNT(*) FROM Cards" 2>/dev/null || echo "N/A")
        echo "  Card Database:  hal_cards.db ($DB_SIZE, $CARD_COUNT cards)"
    else
        echo "  Card Database:  hal_cards.db ($DB_SIZE)"
    fi
else
    echo "  Card Database:  ✗ Not found"
fi
echo ""

# Overall status
echo "═══════════════════════════════════════════════════════════════"
if [ $running -eq 2 ]; then
    echo "  System Status: ✓ ALL SERVICES RUNNING ($running/2)"
elif [ $running -eq 1 ]; then
    echo "  System Status: ⚠ PARTIAL ($running/2 services running)"
else
    echo "  System Status: ✗ ALL SERVICES STOPPED"
fi
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Show quick commands
if [ $running -gt 0 ]; then
    echo "Commands:"
    echo "  Stop services:      ./stop_hal_system.sh"
    echo "  View API logs:      tail -f logs/api_server.log"
    echo "  View export logs:   tail -f logs/event_export.log"
else
    echo "Commands:"
    echo "  Start services:     ./start_hal_system.sh"
fi
echo ""
