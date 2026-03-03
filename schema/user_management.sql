-- =============================================================================
-- AetherAccess User Management Schema
-- Adds user management, door naming, and access level assignment
-- Version 2.1
-- =============================================================================

-- -----------------------------------------------------------------------------
-- Users Table
-- Stores system users with authentication and profile information
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,      -- bcrypt hash
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    phone VARCHAR(20),
    role VARCHAR(20) DEFAULT 'user',          -- admin, operator, user, guard
    is_active BOOLEAN DEFAULT 1,
    is_locked BOOLEAN DEFAULT 0,
    failed_login_attempts INTEGER DEFAULT 0,
    last_login_at INTEGER,                    -- Unix timestamp
    password_changed_at INTEGER,              -- Unix timestamp
    created_at INTEGER DEFAULT (strftime('%s','now')),
    updated_at INTEGER DEFAULT (strftime('%s','now'))
);

CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_active ON users(is_active);

-- -----------------------------------------------------------------------------
-- Door Configurations
-- Enhanced door management with naming and descriptions
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS door_configs (
    door_id INTEGER PRIMARY KEY,              -- Matches access_point id
    door_name VARCHAR(100) NOT NULL,
    description TEXT,
    location VARCHAR(200),
    door_type VARCHAR(50),                    -- entry, exit, interior, emergency
    osdp_enabled BOOLEAN DEFAULT 0,           -- Enable OSDP Secure Channel
    scbk VARCHAR(32),                         -- Secure Channel Base Key (hex)
    reader_address INTEGER,                   -- OSDP reader address (0-126)
    baud_rate INTEGER DEFAULT 9600,           -- 9600, 19200, 38400, 57600, 115200
    led_control BOOLEAN DEFAULT 1,            -- Allow LED control
    buzzer_control BOOLEAN DEFAULT 1,         -- Allow buzzer control
    biometric_enabled BOOLEAN DEFAULT 0,      -- Biometric reader support
    display_enabled BOOLEAN DEFAULT 0,        -- Has display
    keypad_enabled BOOLEAN DEFAULT 0,         -- Has keypad
    is_monitored BOOLEAN DEFAULT 1,           -- Health monitoring enabled
    alert_on_failure BOOLEAN DEFAULT 1,       -- Alert on comm failure
    notes TEXT,
    created_at INTEGER DEFAULT (strftime('%s','now')),
    updated_at INTEGER DEFAULT (strftime('%s','now'))
);

CREATE INDEX idx_door_configs_name ON door_configs(door_name);
CREATE INDEX idx_door_configs_type ON door_configs(door_type);
CREATE INDEX idx_door_configs_osdp ON door_configs(osdp_enabled);

-- -----------------------------------------------------------------------------
-- Access Levels
-- Groups of doors that can be assigned to users
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS access_levels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    priority INTEGER DEFAULT 0,               -- Higher priority = more access
    is_active BOOLEAN DEFAULT 1,
    created_at INTEGER DEFAULT (strftime('%s','now')),
    updated_at INTEGER DEFAULT (strftime('%s','now'))
);

CREATE INDEX idx_access_levels_name ON access_levels(name);
CREATE INDEX idx_access_levels_active ON access_levels(is_active);

-- -----------------------------------------------------------------------------
-- Access Level Doors
-- Defines which doors belong to each access level
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS access_level_doors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    access_level_id INTEGER NOT NULL,
    door_id INTEGER NOT NULL,
    timezone_id INTEGER DEFAULT 2,            -- 0=Null, 1=Never, 2=Always
    entry_allowed BOOLEAN DEFAULT 1,
    exit_allowed BOOLEAN DEFAULT 1,
    created_at INTEGER DEFAULT (strftime('%s','now')),
    FOREIGN KEY(access_level_id) REFERENCES access_levels(id) ON DELETE CASCADE,
    FOREIGN KEY(door_id) REFERENCES door_configs(door_id) ON DELETE CASCADE,
    UNIQUE(access_level_id, door_id)
);

CREATE INDEX idx_access_level_doors_level ON access_level_doors(access_level_id);
CREATE INDEX idx_access_level_doors_door ON access_level_doors(door_id);

-- -----------------------------------------------------------------------------
-- User Access Levels
-- Assigns access levels to users with activation/expiration dates
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS user_access_levels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    access_level_id INTEGER NOT NULL,
    activation_date INTEGER DEFAULT 0,        -- Unix timestamp, 0 = immediate
    expiration_date INTEGER DEFAULT 0,        -- Unix timestamp, 0 = never
    is_active BOOLEAN DEFAULT 1,
    granted_by INTEGER,                       -- user_id who granted access
    granted_at INTEGER DEFAULT (strftime('%s','now')),
    revoked_by INTEGER,                       -- user_id who revoked access
    revoked_at INTEGER,
    notes TEXT,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY(access_level_id) REFERENCES access_levels(id) ON DELETE CASCADE,
    FOREIGN KEY(granted_by) REFERENCES users(id),
    FOREIGN KEY(revoked_by) REFERENCES users(id),
    UNIQUE(user_id, access_level_id)
);

CREATE INDEX idx_user_access_levels_user ON user_access_levels(user_id);
CREATE INDEX idx_user_access_levels_level ON user_access_levels(access_level_id);
CREATE INDEX idx_user_access_levels_active ON user_access_levels(is_active);

-- -----------------------------------------------------------------------------
-- Audit Log
-- Comprehensive audit trail for security and compliance
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp INTEGER DEFAULT (strftime('%s','now')),
    user_id INTEGER,                          -- NULL for system actions
    action_type VARCHAR(50) NOT NULL,         -- login, logout, door_unlock, config_change, etc.
    resource_type VARCHAR(50),                -- user, door, access_level, etc.
    resource_id INTEGER,
    details TEXT,                             -- JSON with additional context
    ip_address VARCHAR(45),                   -- IPv4/IPv6
    user_agent TEXT,
    success BOOLEAN DEFAULT 1,
    error_message TEXT,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE SET NULL
);

CREATE INDEX idx_audit_log_timestamp ON audit_log(timestamp);
CREATE INDEX idx_audit_log_user ON audit_log(user_id);
CREATE INDEX idx_audit_log_action ON audit_log(action_type);
CREATE INDEX idx_audit_log_resource ON audit_log(resource_type, resource_id);

-- -----------------------------------------------------------------------------
-- Session Management
-- Track active user sessions for JWT-based authentication
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    token_hash VARCHAR(255) NOT NULL,         -- SHA-256 of JWT token
    device_info TEXT,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at INTEGER DEFAULT (strftime('%s','now')),
    expires_at INTEGER NOT NULL,
    last_activity INTEGER DEFAULT (strftime('%s','now')),
    is_active BOOLEAN DEFAULT 1,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX idx_sessions_user ON sessions(user_id);
CREATE INDEX idx_sessions_token ON sessions(token_hash);
CREATE INDEX idx_sessions_active ON sessions(is_active);
CREATE INDEX idx_sessions_expires ON sessions(expires_at);

-- -----------------------------------------------------------------------------
-- Card Holder Enhancement
-- Link cards to users and add badge management
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS card_holders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER UNIQUE,                   -- Link to users table (optional)
    card_number VARCHAR(50) UNIQUE NOT NULL,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100),
    phone VARCHAR(20),
    department VARCHAR(100),
    employee_id VARCHAR(50),
    badge_number VARCHAR(50),
    photo_url VARCHAR(500),                   -- Photo storage path/URL
    activation_date INTEGER DEFAULT 0,
    expiration_date INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT 1,
    notes TEXT,
    created_at INTEGER DEFAULT (strftime('%s','now')),
    updated_at INTEGER DEFAULT (strftime('%s','now')),
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE SET NULL
);

CREATE INDEX idx_card_holders_user ON card_holders(user_id);
CREATE INDEX idx_card_holders_card ON card_holders(card_number);
CREATE INDEX idx_card_holders_name ON card_holders(last_name, first_name);
CREATE INDEX idx_card_holders_active ON card_holders(is_active);
CREATE INDEX idx_card_holders_employee ON card_holders(employee_id);

-- -----------------------------------------------------------------------------
-- Initial Data - Create default admin user and access levels
-- -----------------------------------------------------------------------------

-- Default admin user (password: admin123 - CHANGE IN PRODUCTION!)
-- Password hash: bcrypt of 'admin123'
INSERT OR IGNORE INTO users (id, username, email, password_hash, first_name, last_name, role, is_active)
VALUES (1, 'admin', 'admin@aetheraccess.local', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYvVq/cG7dK', 'System', 'Administrator', 'admin', 1);

-- Default access levels
INSERT OR IGNORE INTO access_levels (id, name, description, priority)
VALUES
    (1, 'Full Access', 'Access to all doors at all times', 100),
    (2, 'Business Hours', 'Access to common areas during business hours', 50),
    (3, 'Restricted', 'Limited access to specific areas', 10),
    (4, 'Visitor', 'Escort required, temporary access', 1);

-- Grant admin full access
INSERT OR IGNORE INTO user_access_levels (user_id, access_level_id, activation_date, expiration_date, granted_by)
VALUES (1, 1, 0, 0, 1);

-- =============================================================================
-- Views for easier querying
-- =============================================================================

-- User with access levels
CREATE VIEW IF NOT EXISTS v_user_access AS
SELECT
    u.id as user_id,
    u.username,
    u.email,
    u.first_name,
    u.last_name,
    u.role,
    u.is_active as user_active,
    al.id as access_level_id,
    al.name as access_level_name,
    al.priority as access_priority,
    ual.activation_date,
    ual.expiration_date,
    ual.is_active as assignment_active
FROM users u
LEFT JOIN user_access_levels ual ON u.id = ual.user_id
LEFT JOIN access_levels al ON ual.access_level_id = al.id;

-- Access level with doors
CREATE VIEW IF NOT EXISTS v_access_level_details AS
SELECT
    al.id as access_level_id,
    al.name as access_level_name,
    al.description,
    al.priority,
    dc.door_id,
    dc.door_name,
    dc.location,
    dc.door_type,
    ald.timezone_id,
    ald.entry_allowed,
    ald.exit_allowed
FROM access_levels al
LEFT JOIN access_level_doors ald ON al.id = ald.access_level_id
LEFT JOIN door_configs dc ON ald.door_id = dc.door_id;

-- User effective access (which doors can they access)
CREATE VIEW IF NOT EXISTS v_user_door_access AS
SELECT DISTINCT
    u.id as user_id,
    u.username,
    dc.door_id,
    dc.door_name,
    dc.location,
    al.name as access_level_name,
    ald.entry_allowed,
    ald.exit_allowed,
    ald.timezone_id,
    ual.activation_date,
    ual.expiration_date
FROM users u
INNER JOIN user_access_levels ual ON u.id = ual.user_id AND ual.is_active = 1
INNER JOIN access_levels al ON ual.access_level_id = al.id AND al.is_active = 1
INNER JOIN access_level_doors ald ON al.id = ald.access_level_id
INNER JOIN door_configs dc ON ald.door_id = dc.door_id
WHERE u.is_active = 1
    AND (ual.activation_date = 0 OR ual.activation_date <= strftime('%s','now'))
    AND (ual.expiration_date = 0 OR ual.expiration_date >= strftime('%s','now'));

-- =============================================================================
-- Triggers for automatic timestamp updates
-- =============================================================================

CREATE TRIGGER IF NOT EXISTS update_users_timestamp
AFTER UPDATE ON users
BEGIN
    UPDATE users SET updated_at = strftime('%s','now') WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_door_configs_timestamp
AFTER UPDATE ON door_configs
BEGIN
    UPDATE door_configs SET updated_at = strftime('%s','now') WHERE door_id = NEW.door_id;
END;

CREATE TRIGGER IF NOT EXISTS update_access_levels_timestamp
AFTER UPDATE ON access_levels
BEGIN
    UPDATE access_levels SET updated_at = strftime('%s','now') WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_card_holders_timestamp
AFTER UPDATE ON card_holders
BEGIN
    UPDATE card_holders SET updated_at = strftime('%s','now') WHERE id = NEW.id;
END;

-- =============================================================================
-- Sample data for testing (optional)
-- =============================================================================

-- Sample doors (customize for your installation)
INSERT OR IGNORE INTO door_configs (door_id, door_name, description, location, door_type, osdp_enabled)
VALUES
    (1, 'Main Entrance', 'Primary building entrance', 'Building A - Front', 'entry', 1),
    (2, 'Server Room', 'Data center access', 'Building A - 2nd Floor', 'interior', 1),
    (3, 'Executive Office', 'C-level office area', 'Building A - 5th Floor', 'interior', 0),
    (4, 'Loading Dock', 'Receiving and shipping', 'Building B - Ground', 'entry', 1),
    (5, 'Emergency Exit', 'Emergency egress only', 'Building A - East Side', 'emergency', 0);

-- Assign doors to access levels
INSERT OR IGNORE INTO access_level_doors (access_level_id, door_id, timezone_id, entry_allowed, exit_allowed)
VALUES
    -- Full Access: all doors
    (1, 1, 2, 1, 1),
    (1, 2, 2, 1, 1),
    (1, 3, 2, 1, 1),
    (1, 4, 2, 1, 1),
    (1, 5, 2, 1, 1),
    -- Business Hours: main entrance and loading dock
    (2, 1, 2, 1, 1),
    (2, 4, 2, 1, 1),
    -- Restricted: only main entrance
    (3, 1, 2, 1, 1),
    -- Visitor: main entrance only, exit only
    (4, 1, 2, 0, 1);

-- =============================================================================
-- Migration Notes
-- =============================================================================
-- This schema extends the existing AetherAccess database
-- It should be applied alongside the existing sdk_tables.sql and hal_events.sql
--
-- Key Integration Points:
-- 1. door_configs.door_id links to access_points.id in sdk_tables.sql
-- 2. door_configs.reader_address links to readers configuration
-- 3. timezone_id references timezones table from sdk_tables.sql
-- 4. audit_log complements access_events from hal_events.sql
--
-- To apply:
-- sqlite3 hal_sdk.db < schema/user_management.sql
-- =============================================================================
