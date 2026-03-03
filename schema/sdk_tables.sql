-- =============================================================================
-- Azure Access SDK Database Schema
-- Complete schema for all SDK modules
-- =============================================================================

-- -----------------------------------------------------------------------------
-- Permissions Module
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS permissions (
    id INTEGER PRIMARY KEY,
    activation_datetime INTEGER DEFAULT 0,    -- Unix timestamp, 0 = always active
    deactivation_datetime INTEGER DEFAULT 0,  -- Unix timestamp, 0 = never expires
    created_at INTEGER DEFAULT (strftime('%s','now')),
    updated_at INTEGER DEFAULT (strftime('%s','now'))
);

CREATE TABLE IF NOT EXISTS permission_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    permission_id INTEGER NOT NULL,
    access_object_type INTEGER NOT NULL,    -- LPA type
    access_object_id INTEGER NOT NULL,      -- LPA id
    access_object_node INTEGER NOT NULL,    -- LPA node
    strike_type INTEGER DEFAULT 0,          -- Strike LPA type
    strike_id INTEGER DEFAULT 0,            -- Strike LPA id
    strike_node INTEGER DEFAULT 0,          -- Strike LPA node
    timezone_id INTEGER DEFAULT 0,
    override_mask INTEGER DEFAULT 0,        -- Which flags to override
    override_flags INTEGER DEFAULT 0,       -- Override values
    FOREIGN KEY(permission_id) REFERENCES permissions(id) ON DELETE CASCADE
);

CREATE INDEX idx_permission_entries_perm ON permission_entries(permission_id);
CREATE INDEX idx_permission_entries_obj ON permission_entries(access_object_type, access_object_id);

CREATE TABLE IF NOT EXISTS exclusion_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    permission_id INTEGER NOT NULL,
    access_object_type INTEGER NOT NULL,
    access_object_id INTEGER NOT NULL,
    access_object_node INTEGER NOT NULL,
    strike_type INTEGER DEFAULT 0,
    strike_id INTEGER DEFAULT 0,
    strike_node INTEGER DEFAULT 0,
    FOREIGN KEY(permission_id) REFERENCES permissions(id) ON DELETE CASCADE
);

CREATE INDEX idx_exclusion_entries_perm ON exclusion_entries(permission_id);

-- -----------------------------------------------------------------------------
-- Time Zones Module
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS timezones (
    id INTEGER PRIMARY KEY,
    script_id INTEGER DEFAULT 0,
    created_at INTEGER DEFAULT (strftime('%s','now')),
    updated_at INTEGER DEFAULT (strftime('%s','now'))
);

CREATE TABLE IF NOT EXISTS time_intervals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timezone_id INTEGER NOT NULL,
    start_time INTEGER DEFAULT 0,           -- Seconds since midnight
    end_time INTEGER DEFAULT 0,             -- Seconds since midnight
    cycle_start INTEGER DEFAULT 0,          -- Unix timestamp
    cycle_length INTEGER DEFAULT 0,         -- Days (0-32)
    cycle_days INTEGER DEFAULT 0,           -- Bit field
    holiday_types INTEGER DEFAULT 0,        -- Bit field (32 types)
    begin_datetime INTEGER DEFAULT 0,       -- Unix timestamp
    end_datetime INTEGER DEFAULT 0,         -- Unix timestamp
    cycle_count INTEGER DEFAULT 0,          -- Max cycles
    recurrence_type INTEGER DEFAULT 0,      -- 0=Cyclic, 1=Monthly, 2=Annually, 3=MonthlyAtDay
    FOREIGN KEY(timezone_id) REFERENCES timezones(id) ON DELETE CASCADE
);

CREATE INDEX idx_time_intervals_tz ON time_intervals(timezone_id);

-- -----------------------------------------------------------------------------
-- Holidays Module
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS holidays (
    date INTEGER PRIMARY KEY,               -- YYYYMMDD format (20251225)
    holiday_types INTEGER DEFAULT 0         -- Bit field (32 types)
);

CREATE INDEX idx_holidays_date ON holidays(date);

-- -----------------------------------------------------------------------------
-- Relays Module
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS relays (
    id_type INTEGER NOT NULL,               -- LPA type
    id_id INTEGER NOT NULL,                 -- LPA id
    id_node INTEGER NOT NULL,               -- LPA node
    pulse_duration INTEGER DEFAULT 0,       -- 10ms units
    ctrl_timezone INTEGER DEFAULT 0,        -- TimeZone ID
    flags INTEGER DEFAULT 0,                -- RelayFlags_t bit field
    mode INTEGER DEFAULT 0,                 -- RelayMode_t
    script_id INTEGER DEFAULT 0,
    created_at INTEGER DEFAULT (strftime('%s','now')),
    updated_at INTEGER DEFAULT (strftime('%s','now')),
    PRIMARY KEY(id_type, id_id, id_node)
);

CREATE TABLE IF NOT EXISTS relay_links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    relay_type INTEGER NOT NULL,           -- Relay LPA type
    relay_id INTEGER NOT NULL,             -- Relay LPA id
    relay_node INTEGER NOT NULL,           -- Relay LPA node
    source_type INTEGER NOT NULL,          -- Event source LPA type
    source_id INTEGER NOT NULL,            -- Event source LPA id
    source_node INTEGER NOT NULL,          -- Event source LPA node
    event_type INTEGER NOT NULL,           -- Event type
    event_subtype INTEGER NOT NULL,        -- Event subtype
    new_status INTEGER DEFAULT 0xFF,       -- Status filter (0xFF = any)
    operation INTEGER NOT NULL             -- RelayControlOperation_t (0=OFF, 1=ON, 2=PULSE)
);

CREATE INDEX idx_relay_links_relay ON relay_links(relay_type, relay_id);
CREATE INDEX idx_relay_links_source ON relay_links(source_type, source_id, event_type);

-- -----------------------------------------------------------------------------
-- Readers Module
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS readers (
    id_type INTEGER NOT NULL,               -- LPA type
    id_id INTEGER NOT NULL,                 -- LPA id
    id_node INTEGER NOT NULL,               -- LPA node
    access_point_type INTEGER DEFAULT 0,    -- Access point LPA type
    access_point_id INTEGER DEFAULT 0,      -- Access point LPA id
    access_point_node INTEGER DEFAULT 0,    -- Access point LPA node
    cipher_code INTEGER DEFAULT 0xFFFFFFFF,
    script_id INTEGER DEFAULT 0,
    flags INTEGER DEFAULT 0,                -- ReaderFlags_t bit field
    timed_apb INTEGER DEFAULT 0,            -- Minutes
    timed_apb_ex INTEGER DEFAULT 0,         -- Seconds (overrides timed_apb)
    threat_level INTEGER DEFAULT 0,
    next_to INTEGER DEFAULT 0,              -- Seconds
    signal_type INTEGER DEFAULT 0,
    direction INTEGER DEFAULT 0,            -- 0=IN, 1=OUT
    num_of_cards INTEGER DEFAULT 1,
    init_mode INTEGER DEFAULT 1,            -- ReaderMode_t (default=CardOnly)
    offline_mode INTEGER DEFAULT 1,         -- ReaderMode_t
    use_limit INTEGER DEFAULT 0,
    card_format_list_id INTEGER DEFAULT 0,
    ctrl_timezone INTEGER DEFAULT 0,
    smart_card_format_type INTEGER DEFAULT 0,
    smart_card_format_id INTEGER DEFAULT 0,
    smart_card_format_node INTEGER DEFAULT 0,
    tz_start_mode INTEGER DEFAULT 255,      -- ReaderMode_Unknown
    tz_end_mode INTEGER DEFAULT 255,        -- ReaderMode_Unknown
    diddle_threshold INTEGER DEFAULT 3,
    indication_type INTEGER DEFAULT 0,      -- ReaderIndication LPA type
    indication_id INTEGER DEFAULT 0,        -- ReaderIndication LPA id
    indication_node INTEGER DEFAULT 0,      -- ReaderIndication LPA node
    unlocked_mode INTEGER DEFAULT 4,        -- ReaderMode_Unlocked
    locked_mode INTEGER DEFAULT 0,          -- ReaderMode_Locked
    lock_timeout INTEGER DEFAULT 0,
    disable_reader_toggle_type INTEGER DEFAULT 0,
    disable_reader_toggle_id INTEGER DEFAULT 0,
    disable_reader_toggle_node INTEGER DEFAULT 0,
    command_to INTEGER DEFAULT 3000,        -- Milliseconds
    diddle_lockout_to INTEGER DEFAULT 2,    -- Seconds
    pin_timeout INTEGER DEFAULT 10,         -- Seconds
    created_at INTEGER DEFAULT (strftime('%s','now')),
    updated_at INTEGER DEFAULT (strftime('%s','now')),
    PRIMARY KEY(id_type, id_id, id_node)
);

-- Reader Indication Configurations
CREATE TABLE IF NOT EXISTS reader_indications (
    id_type INTEGER NOT NULL,
    id_id INTEGER NOT NULL,
    id_node INTEGER NOT NULL,
    PRIMARY KEY(id_type, id_id, id_node)
);

CREATE TABLE IF NOT EXISTS indication_configs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    indication_type INTEGER NOT NULL,       -- ReaderIndication LPA type
    indication_id INTEGER NOT NULL,         -- ReaderIndication LPA id
    indication_node INTEGER NOT NULL,       -- ReaderIndication LPA node
    state INTEGER NOT NULL,                 -- ReaderIndicationState_t (0-24)
    position INTEGER NOT NULL,              -- 0-7 (up to 8 configs per state)
    config_type INTEGER NOT NULL,           -- LPA type (LED or Buzzer)
    config_id INTEGER NOT NULL,             -- LPA id
    config_node INTEGER NOT NULL,           -- LPA node
    FOREIGN KEY(indication_type, indication_id, indication_node)
        REFERENCES reader_indications(id_type, id_id, id_node) ON DELETE CASCADE
);

CREATE INDEX idx_indication_configs_ind ON indication_configs(indication_type, indication_id, state);

-- LED Configurations
CREATE TABLE IF NOT EXISTS led_configs (
    id_type INTEGER NOT NULL,
    id_id INTEGER NOT NULL,
    id_node INTEGER NOT NULL,
    led_id INTEGER DEFAULT 2,              -- LEDId_t (Red=0, Yellow=1, Green=2)
    cancel_temp INTEGER DEFAULT 0,
    on_time INTEGER DEFAULT 10,            -- 100ms units
    off_time INTEGER DEFAULT 0,            -- 100ms units (0=solid)
    on_color INTEGER DEFAULT 3,            -- LEDColor_t (Green=3)
    off_color INTEGER DEFAULT 0,           -- LEDColor_t (Off=0)
    PRIMARY KEY(id_type, id_id, id_node)
);

-- Buzzer Configurations
CREATE TABLE IF NOT EXISTS buzzer_configs (
    id_type INTEGER NOT NULL,
    id_id INTEGER NOT NULL,
    id_node INTEGER NOT NULL,
    tone INTEGER DEFAULT 2,                -- 0=no tone, 1=off, 2=default
    on_time INTEGER DEFAULT 2,             -- 100ms units
    off_time INTEGER DEFAULT 0,            -- 100ms units
    count INTEGER DEFAULT 1,               -- Number of beeps (0=continuous)
    PRIMARY KEY(id_type, id_id, id_node)
);

-- -----------------------------------------------------------------------------
-- Group Lists Module
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS group_lists (
    id_type INTEGER NOT NULL,
    id_id INTEGER NOT NULL,
    id_node INTEGER NOT NULL,
    created_at INTEGER DEFAULT (strftime('%s','now')),
    updated_at INTEGER DEFAULT (strftime('%s','now')),
    PRIMARY KEY(id_type, id_id, id_node)
);

CREATE TABLE IF NOT EXISTS group_list_groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    group_list_type INTEGER NOT NULL,
    group_list_id INTEGER NOT NULL,
    group_list_node INTEGER NOT NULL,
    position INTEGER NOT NULL,             -- 0-31 (max 32 groups)
    group_id INTEGER NOT NULL,
    FOREIGN KEY(group_list_type, group_list_id, group_list_node)
        REFERENCES group_lists(id_type, id_id, id_node) ON DELETE CASCADE
);

CREATE INDEX idx_group_list_groups_list ON group_list_groups(group_list_type, group_list_id);

-- =============================================================================
-- Update Card Table (add permission link if needed)
-- =============================================================================

-- Uncomment this if your cards table doesn't have permission_id
-- ALTER TABLE cards ADD COLUMN permission_id INTEGER DEFAULT 0;

-- =============================================================================
-- Helper Views
-- =============================================================================

-- View for complete permission entries with activation status
CREATE VIEW IF NOT EXISTS v_permission_entries AS
SELECT
    pe.*,
    p.activation_datetime,
    p.deactivation_datetime,
    CASE
        WHEN p.activation_datetime > 0 AND p.activation_datetime > strftime('%s','now') THEN 0
        WHEN p.deactivation_datetime > 0 AND p.deactivation_datetime <= strftime('%s','now') THEN 0
        ELSE 1
    END AS is_active
FROM permission_entries pe
JOIN permissions p ON pe.permission_id = p.id;

-- View for active timezones (not expired)
CREATE VIEW IF NOT EXISTS v_active_timezones AS
SELECT *
FROM timezones tz
WHERE id = 2  -- TimeZoneConsts_Always
   OR id IN (
       SELECT DISTINCT timezone_id
       FROM time_intervals
       WHERE (begin_datetime = 0 OR begin_datetime <= strftime('%s','now'))
         AND (end_datetime = 0 OR end_datetime >= strftime('%s','now'))
   );

-- View for current holidays
CREATE VIEW IF NOT EXISTS v_current_holidays AS
SELECT *
FROM holidays
WHERE date = CAST(strftime('%Y%m%d', 'now') AS INTEGER);

-- View for reader status summary
CREATE VIEW IF NOT EXISTS v_reader_status AS
SELECT
    r.id_type,
    r.id_id,
    r.id_node,
    r.init_mode AS mode,
    r.flags,
    r.ctrl_timezone,
    CASE
        WHEN r.ctrl_timezone IN (SELECT id FROM v_active_timezones) THEN 1
        ELSE 0
    END AS timezone_active
FROM readers r;

-- =============================================================================
-- Insert default/constant values
-- =============================================================================

-- TimeZone constants
INSERT OR IGNORE INTO timezones (id, script_id) VALUES (0, 0);  -- TimeZoneConsts_Null
INSERT OR IGNORE INTO timezones (id, script_id) VALUES (1, 0);  -- TimeZoneConsts_Never
INSERT OR IGNORE INTO timezones (id, script_id) VALUES (2, 0);  -- TimeZoneConsts_Always

-- =============================================================================
-- Schema Version Tracking
-- =============================================================================

-- -----------------------------------------------------------------------------
-- Access Points Module
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS access_points (
    id INTEGER PRIMARY KEY,
    lpa_type INTEGER NOT NULL,
    lpa_id INTEGER NOT NULL,
    lpa_node INTEGER NOT NULL,
    init_mode INTEGER DEFAULT 0,         -- AccessPointMode_t (0=Locked)
    short_strike_time INTEGER DEFAULT 5,
    long_strike_time INTEGER DEFAULT 10,
    short_held_open_time INTEGER DEFAULT 30,
    long_held_open_time INTEGER DEFAULT 60,
    area_a_type INTEGER DEFAULT 0,
    area_a_id INTEGER DEFAULT 0,
    area_a_node INTEGER DEFAULT 0,
    area_b_type INTEGER DEFAULT 0,
    area_b_id INTEGER DEFAULT 0,
    area_b_node INTEGER DEFAULT 0,
    reader_type INTEGER DEFAULT 0,
    reader_id INTEGER DEFAULT 0,
    reader_node INTEGER DEFAULT 0,
    created_at INTEGER DEFAULT (strftime('%s','now')),
    updated_at INTEGER DEFAULT (strftime('%s','now'))
);

CREATE TABLE IF NOT EXISTS access_point_strikes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    access_point_id INTEGER NOT NULL,
    strike_type INTEGER NOT NULL,
    strike_id INTEGER NOT NULL,
    strike_node INTEGER NOT NULL,
    pulse_duration INTEGER DEFAULT 100,   -- 10ms units
    FOREIGN KEY(access_point_id) REFERENCES access_points(id) ON DELETE CASCADE
);

CREATE INDEX idx_access_point_strikes ON access_point_strikes(access_point_id);

-- -----------------------------------------------------------------------------
-- Areas Module
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS areas (
    id INTEGER PRIMARY KEY,
    lpa_type INTEGER NOT NULL,
    lpa_id INTEGER NOT NULL,
    lpa_node INTEGER NOT NULL,
    name TEXT,
    timed_apb INTEGER DEFAULT 0,          -- Minutes (0 = disabled)
    min_occupancy INTEGER DEFAULT 0,
    max_occupancy INTEGER DEFAULT 255,
    occupancy_limit INTEGER DEFAULT 255,
    min_required_occupancy INTEGER DEFAULT 0,
    current_occupancy INTEGER DEFAULT 0,
    created_at INTEGER DEFAULT (strftime('%s','now')),
    updated_at INTEGER DEFAULT (strftime('%s','now'))
);

-- -----------------------------------------------------------------------------
-- Card Formats Module
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS card_formats (
    id INTEGER PRIMARY KEY,
    format_type INTEGER DEFAULT 0,        -- CardFormatType_t (0=Wiegand)
    name TEXT,
    total_bits INTEGER DEFAULT 26,
    facility_start_bit INTEGER DEFAULT 0,
    facility_bit_length INTEGER DEFAULT 0,
    card_start_bit INTEGER DEFAULT 0,
    card_bit_length INTEGER DEFAULT 0,
    parity_type INTEGER DEFAULT 0,
    created_at INTEGER DEFAULT (strftime('%s','now')),
    updated_at INTEGER DEFAULT (strftime('%s','now'))
);

CREATE TABLE IF NOT EXISTS card_format_lists (
    id INTEGER PRIMARY KEY,
    created_at INTEGER DEFAULT (strftime('%s','now')),
    updated_at INTEGER DEFAULT (strftime('%s','now'))
);

CREATE TABLE IF NOT EXISTS card_format_list_formats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    list_id INTEGER NOT NULL,
    format_id INTEGER NOT NULL,
    position INTEGER NOT NULL,
    FOREIGN KEY(list_id) REFERENCES card_format_lists(id) ON DELETE CASCADE,
    FOREIGN KEY(format_id) REFERENCES card_formats(id) ON DELETE CASCADE
);

CREATE INDEX idx_card_format_list_formats ON card_format_list_formats(list_id);

-- =============================================================================
-- Schema Version Tracking
-- =============================================================================

CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at INTEGER DEFAULT (strftime('%s','now')),
    description TEXT
);

INSERT OR REPLACE INTO schema_version (version, description)
VALUES (2, 'Extended SDK schema - Added AccessPoints, Areas, CardFormats');
