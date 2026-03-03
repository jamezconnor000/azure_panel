#!/bin/bash
#
# HAL REST API Server Startup Script
#

cd "$(dirname "$0")"

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                                                              ║"
echo "║         HAL REST API Server                                  ║"
echo "║         Starting...                                          ║"
echo "║                                                              ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv

    echo "Installing dependencies..."
    source venv/bin/activate
    pip install -r api/requirements.txt
else
    source venv/bin/activate
fi

# Check if databases exist
if [ ! -f "hal_sdk.db" ]; then
    echo "WARNING: hal_sdk.db not found"
    echo "Creating empty database..."
    sqlite3 hal_sdk.db < schema/sdk_tables.sql
fi

if [ ! -f "hal_cards.db" ]; then
    echo "WARNING: hal_cards.db not found"
    echo "Creating empty card database..."
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

# Start the API server
echo ""
echo "Starting HAL REST API Server..."
echo ""

python3 api/hal_api_server.py
