#!/bin/bash
##############################################################################
# Aether Access PoC - Database Seed Script
#
# Seeds the card database with test cards.
#
# Author: FAM-HAL-v1.0-001
# Date: February 10, 2026
##############################################################################

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
POC_DIR="$(dirname "$SCRIPT_DIR")"
DATA_DIR="${POC_DIR}/data"
DB_FILE="${DATA_DIR}/cards.db"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

# Create data directory
mkdir -p "${DATA_DIR}"

# Create or reset database
log_info "Creating database: ${DB_FILE}"

sqlite3 "${DB_FILE}" << 'EOF'
-- Drop existing tables
DROP TABLE IF EXISTS cards;
DROP TABLE IF EXISTS access_schedule;

-- Create cards table
CREATE TABLE cards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    facility_code INTEGER NOT NULL,
    card_number INTEGER NOT NULL,
    person_name TEXT,
    person_uid TEXT,
    access_level INTEGER DEFAULT 1,
    is_active INTEGER DEFAULT 1,
    expires_at INTEGER DEFAULT NULL,
    created_at INTEGER DEFAULT (strftime('%s', 'now')),
    updated_at INTEGER DEFAULT (strftime('%s', 'now')),
    UNIQUE(facility_code, card_number)
);

-- Create indexes
CREATE INDEX idx_cards_lookup ON cards(facility_code, card_number);
CREATE INDEX idx_cards_active ON cards(is_active);

-- Insert test cards
INSERT INTO cards (facility_code, card_number, person_name, access_level, is_active) VALUES
    (100, 12345, 'John Smith', 1, 1),
    (100, 12346, 'Jane Doe', 1, 1),
    (100, 67890, 'Bob Wilson', 2, 1),
    (100, 99999, 'Admin User', 9, 1),
    (100, 55555, 'Visitor Badge', 1, 1),
    (100, 11111, 'Suspended User', 1, 0),
    (100, 22222, 'Expired User', 1, 1);

-- Set expired timestamp for expired user (yesterday)
UPDATE cards SET expires_at = strftime('%s', 'now', '-1 day') WHERE card_number = 22222;

-- Verify
SELECT 'Seeded ' || COUNT(*) || ' cards' as result FROM cards;
EOF

log_success "Database seeded successfully"

# Show contents
echo ""
log_info "Database contents:"
echo ""
sqlite3 -header -column "${DB_FILE}" << 'EOF'
SELECT facility_code as FC, card_number as Card, person_name as Name,
       CASE is_active WHEN 1 THEN 'Active' ELSE 'Suspended' END as Status,
       CASE WHEN expires_at IS NULL THEN 'Never'
            WHEN expires_at < strftime('%s', 'now') THEN 'EXPIRED'
            ELSE datetime(expires_at, 'unixepoch') END as Expires
FROM cards
ORDER BY card_number;
EOF

echo ""
log_success "Done"
echo ""
