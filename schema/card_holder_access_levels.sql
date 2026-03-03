-- Card Holder Access Levels Junction Table
-- Links card holders to access levels for door access permissions

CREATE TABLE IF NOT EXISTS card_holder_access_levels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    card_holder_id INTEGER NOT NULL,
    level_id INTEGER NOT NULL,
    granted_by INTEGER,                      -- User ID who granted access
    granted_at INTEGER DEFAULT (strftime('%s','now')),
    expires_at INTEGER DEFAULT 0,            -- 0 = never expires
    is_active BOOLEAN DEFAULT 1,
    notes TEXT,
    FOREIGN KEY(card_holder_id) REFERENCES card_holders(id) ON DELETE CASCADE,
    FOREIGN KEY(level_id) REFERENCES access_levels(level_id) ON DELETE CASCADE,
    FOREIGN KEY(granted_by) REFERENCES users(id) ON DELETE SET NULL,
    UNIQUE(card_holder_id, level_id)
);

CREATE INDEX idx_card_holder_access_levels_holder ON card_holder_access_levels(card_holder_id);
CREATE INDEX idx_card_holder_access_levels_level ON card_holder_access_levels(level_id);
CREATE INDEX idx_card_holder_access_levels_active ON card_holder_access_levels(is_active);
