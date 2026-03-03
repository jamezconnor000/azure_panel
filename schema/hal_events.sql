CREATE TABLE IF NOT EXISTS access_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id TEXT UNIQUE NOT NULL,
    event_type TEXT NOT NULL,
    card_number TEXT,
    door_number INTEGER,
    door_name TEXT,
    cardholder_name TEXT,
    granted BOOLEAN,
    reason TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    sent_to_ambient BOOLEAN DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_event_timestamp ON access_events(timestamp);
CREATE INDEX idx_card_number ON access_events(card_number);
CREATE INDEX idx_event_type ON access_events(event_type);
CREATE INDEX idx_sent_status ON access_events(sent_to_ambient);
