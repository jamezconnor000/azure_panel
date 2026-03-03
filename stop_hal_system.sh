#!/bin/bash
#
# HAL System Stop Script
# Stops both REST API Server and Event Export Daemon
#

cd "$(dirname "$0")"

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                                                              ║"
echo "║         HAL SYSTEM - STOPPING SERVICES                       ║"
echo "║                                                              ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

API_PID_FILE=".hal_api.pid"
EXPORT_PID_FILE=".hal_export.pid"

stopped=0

# Stop REST API Server
if [ -f "$API_PID_FILE" ]; then
    API_PID=$(cat "$API_PID_FILE")
    if ps -p $API_PID > /dev/null 2>&1; then
        echo "Stopping REST API Server (PID: $API_PID)..."
        kill $API_PID
        sleep 1

        # Force kill if still running
        if ps -p $API_PID > /dev/null 2>&1; then
            echo "  Force killing..."
            kill -9 $API_PID 2>/dev/null
        fi

        echo "  ✓ REST API Server stopped"
        stopped=$((stopped + 1))
    fi
    rm -f "$API_PID_FILE"
fi

# Stop Event Export Daemon
if [ -f "$EXPORT_PID_FILE" ]; then
    EXPORT_PID=$(cat "$EXPORT_PID_FILE")
    if ps -p $EXPORT_PID > /dev/null 2>&1; then
        echo "Stopping Event Export Daemon (PID: $EXPORT_PID)..."
        kill $EXPORT_PID
        sleep 1

        # Force kill if still running
        if ps -p $EXPORT_PID > /dev/null 2>&1; then
            echo "  Force killing..."
            kill -9 $EXPORT_PID 2>/dev/null
        fi

        echo "  ✓ Event Export Daemon stopped"
        stopped=$((stopped + 1))
    fi
    rm -f "$EXPORT_PID_FILE"
fi

echo ""
if [ $stopped -eq 0 ]; then
    echo "No HAL services were running."
else
    echo "═══════════════════════════════════════════════════════════════"
    echo "  All HAL services stopped ($stopped service(s))"
    echo "═══════════════════════════════════════════════════════════════"
fi
echo ""
