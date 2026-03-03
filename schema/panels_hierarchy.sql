-- AetherAccess v2.1 - Panel Hierarchy Schema
-- Supports master panels and downstream panels (RS-485 connected)

-- Main panels table
CREATE TABLE IF NOT EXISTS panels (
    panel_id INTEGER PRIMARY KEY,
    panel_name TEXT NOT NULL,
    panel_type TEXT NOT NULL CHECK(panel_type IN ('MASTER', 'DOWNSTREAM')),
    parent_panel_id INTEGER DEFAULT NULL,
    rs485_address INTEGER DEFAULT NULL,
    status TEXT NOT NULL DEFAULT 'OFFLINE' CHECK(status IN ('ONLINE', 'OFFLINE', 'FAULT')),
    firmware_version TEXT,
    last_seen INTEGER DEFAULT 0,
    created_at INTEGER DEFAULT (strftime('%s','now')),
    updated_at INTEGER DEFAULT (strftime('%s','now')),
    notes TEXT,
    FOREIGN KEY(parent_panel_id) REFERENCES panels(panel_id) ON DELETE CASCADE,
    UNIQUE(parent_panel_id, rs485_address)
);

-- Index for faster hierarchy queries
CREATE INDEX IF NOT EXISTS idx_panels_parent ON panels(parent_panel_id);
CREATE INDEX IF NOT EXISTS idx_panels_type ON panels(panel_type);

-- Update readers table to associate with panels
-- Note: Existing readers table may need migration
CREATE TABLE IF NOT EXISTS readers_new (
    reader_id INTEGER PRIMARY KEY,
    panel_id INTEGER NOT NULL,
    reader_address INTEGER NOT NULL,
    reader_name TEXT,
    status TEXT NOT NULL DEFAULT 'OFFLINE' CHECK(status IN ('ONLINE', 'OFFLINE', 'FAULT', 'TAMPER')),
    osdp_enabled BOOLEAN DEFAULT 0,
    scbk_key TEXT,
    last_seen INTEGER DEFAULT 0,
    created_at INTEGER DEFAULT (strftime('%s','now')),
    FOREIGN KEY(panel_id) REFERENCES panels(panel_id) ON DELETE CASCADE,
    UNIQUE(panel_id, reader_address)
);

-- Panel inputs (with panel association)
CREATE TABLE IF NOT EXISTS panel_inputs (
    input_id INTEGER PRIMARY KEY AUTOINCREMENT,
    panel_id INTEGER NOT NULL,
    input_number INTEGER NOT NULL,
    input_name TEXT,
    state TEXT NOT NULL DEFAULT 'INACTIVE' CHECK(state IN ('ACTIVE', 'INACTIVE', 'FAULT')),
    last_state_change INTEGER DEFAULT 0,
    FOREIGN KEY(panel_id) REFERENCES panels(panel_id) ON DELETE CASCADE,
    UNIQUE(panel_id, input_number)
);

-- Panel outputs (with panel association)
CREATE TABLE IF NOT EXISTS panel_outputs (
    output_id INTEGER PRIMARY KEY AUTOINCREMENT,
    panel_id INTEGER NOT NULL,
    output_number INTEGER NOT NULL,
    output_name TEXT,
    state TEXT NOT NULL DEFAULT 'INACTIVE' CHECK(state IN ('ACTIVE', 'INACTIVE', 'FAULT')),
    last_state_change INTEGER DEFAULT 0,
    FOREIGN KEY(panel_id) REFERENCES panels(panel_id) ON DELETE CASCADE,
    UNIQUE(panel_id, output_number)
);

-- Panel relays (with panel association)
CREATE TABLE IF NOT EXISTS panel_relays (
    relay_id INTEGER PRIMARY KEY AUTOINCREMENT,
    panel_id INTEGER NOT NULL,
    relay_number INTEGER NOT NULL,
    relay_name TEXT,
    state TEXT NOT NULL DEFAULT 'INACTIVE' CHECK(state IN ('ACTIVE', 'INACTIVE', 'FAULT')),
    last_state_change INTEGER DEFAULT 0,
    FOREIGN KEY(panel_id) REFERENCES panels(panel_id) ON DELETE CASCADE,
    UNIQUE(panel_id, relay_number)
);

-- Create indexes for faster queries
CREATE INDEX IF NOT EXISTS idx_readers_panel ON readers_new(panel_id);
CREATE INDEX IF NOT EXISTS idx_inputs_panel ON panel_inputs(panel_id);
CREATE INDEX IF NOT EXISTS idx_outputs_panel ON panel_outputs(panel_id);
CREATE INDEX IF NOT EXISTS idx_relays_panel ON panel_relays(panel_id);

-- Sample data for testing
INSERT OR IGNORE INTO panels (panel_id, panel_name, panel_type, parent_panel_id, status, firmware_version)
VALUES
    (1, 'Main Panel A', 'MASTER', NULL, 'ONLINE', 'v2.1.0'),
    (2, 'Downstream Panel 1', 'DOWNSTREAM', 1, 'ONLINE', 'v2.1.0'),
    (3, 'Downstream Panel 2', 'DOWNSTREAM', 1, 'ONLINE', 'v2.1.0');

-- Update RS-485 addresses for downstream panels
UPDATE panels SET rs485_address = 1 WHERE panel_id = 2;
UPDATE panels SET rs485_address = 2 WHERE panel_id = 3;
