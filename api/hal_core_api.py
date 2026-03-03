#!/usr/bin/env python3
"""
HAL Core API Server

The "brain" of the Azure Panel - operates STANDALONE like a Mercury panel.
This is the SINGLE SOURCE OF TRUTH for all access control data.

Port: 8081
Role: Panel's native interface - stores all data locally, makes all decisions locally

Architecture:
- HAL owns ALL data (cards, access levels, events, timezones, holidays)
- HAL makes ALL access decisions locally
- HAL does NOT require network to function
- Aether Access (port 8080) READS from HAL and WRITES through this API

Database: SQLite (local storage)
- 1M+ card capacity
- 100K+ event buffer (circular)
- Complete audit trail
"""

from fastapi import FastAPI, HTTPException, Header, Depends, Query, status, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
from contextlib import asynccontextmanager, contextmanager
from datetime import datetime
from enum import IntEnum
import sqlite3
import json
import time
import os
import asyncio
import uuid


# =============================================================================
# Configuration
# =============================================================================

HAL_VERSION = "2.0.0"
HAL_DB_PATH = os.environ.get("HAL_DB_PATH", "hal_core.db")
HAL_PORT = int(os.environ.get("HAL_PORT", 8081))
MAX_EVENTS = 100000  # Circular buffer capacity
MAX_CARDS = 1000000  # Card database capacity


# =============================================================================
# Enums and Constants
# =============================================================================

class EventType(IntEnum):
    CARD_READ = 1
    ACCESS_GRANTED = 2
    ACCESS_DENIED = 3
    DOOR_FORCED = 4
    DOOR_HELD = 5
    DOOR_OPENED = 6
    DOOR_CLOSED = 7
    RELAY_ACTIVATED = 8
    RELAY_DEACTIVATED = 9
    READER_TAMPER = 10
    SYSTEM_EVENT = 11
    CONFIG_CHANGE = 12
    ALARM = 13
    TROUBLE = 14


class ChangeAction(IntEnum):
    CREATE = 1
    UPDATE = 2
    DELETE = 3


class ChangeSource(IntEnum):
    LOCAL = 1      # Direct HAL change
    AETHER = 2     # Via Aether Access
    PACS = 3       # Via external PACS
    IMPORT = 4     # Bulk import


# =============================================================================
# Database Initialization
# =============================================================================

def init_database(db_path: str):
    """Initialize HAL Core database with complete schema"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Cards (1M+ capacity)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            card_number TEXT UNIQUE NOT NULL,
            facility_code INTEGER DEFAULT 0,
            permission_id INTEGER NOT NULL DEFAULT 1,
            holder_name TEXT DEFAULT '',
            pin_hash TEXT,
            activation_date INTEGER DEFAULT 0,
            expiration_date INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            apb_status INTEGER DEFAULT 0,
            last_access_time INTEGER,
            last_access_door INTEGER,
            created_at INTEGER DEFAULT (strftime('%s','now')),
            updated_at INTEGER DEFAULT (strftime('%s','now'))
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_cards_number ON cards(card_number)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_cards_permission ON cards(permission_id)")

    # Access Levels (Permissions)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS access_levels (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT DEFAULT '',
            priority INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            created_at INTEGER DEFAULT (strftime('%s','now')),
            updated_at INTEGER DEFAULT (strftime('%s','now'))
        )
    """)

    # Access Level -> Door Assignments
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS access_level_doors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            access_level_id INTEGER NOT NULL,
            door_id INTEGER NOT NULL,
            timezone_id INTEGER DEFAULT 2,
            entry_allowed INTEGER DEFAULT 1,
            exit_allowed INTEGER DEFAULT 1,
            UNIQUE(access_level_id, door_id),
            FOREIGN KEY(access_level_id) REFERENCES access_levels(id) ON DELETE CASCADE
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_ald_level ON access_level_doors(access_level_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_ald_door ON access_level_doors(door_id)")

    # Doors
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS doors (
            id INTEGER PRIMARY KEY,
            door_name TEXT NOT NULL,
            location TEXT DEFAULT '',
            reader_address INTEGER DEFAULT 0,
            reader_mode INTEGER DEFAULT 1,
            reader_flags INTEGER DEFAULT 0,
            strike_relay_id INTEGER,
            strike_time_ms INTEGER DEFAULT 3000,
            held_open_time_ms INTEGER DEFAULT 30000,
            pre_alarm_time_ms INTEGER DEFAULT 15000,
            osdp_enabled INTEGER DEFAULT 0,
            scbk TEXT,
            is_online INTEGER DEFAULT 1,
            last_event_time INTEGER,
            created_at INTEGER DEFAULT (strftime('%s','now')),
            updated_at INTEGER DEFAULT (strftime('%s','now'))
        )
    """)

    # Timezones
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS timezones (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT DEFAULT '',
            is_active INTEGER DEFAULT 1,
            created_at INTEGER DEFAULT (strftime('%s','now')),
            updated_at INTEGER DEFAULT (strftime('%s','now'))
        )
    """)

    # Timezone Intervals
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS timezone_intervals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timezone_id INTEGER NOT NULL,
            day_of_week INTEGER DEFAULT 0,
            start_time INTEGER DEFAULT 0,
            end_time INTEGER DEFAULT 86399,
            recurrence_type INTEGER DEFAULT 0,
            holiday_types INTEGER DEFAULT 0,
            FOREIGN KEY(timezone_id) REFERENCES timezones(id) ON DELETE CASCADE
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tz_intervals ON timezone_intervals(timezone_id)")

    # Holidays
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS holidays (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date INTEGER NOT NULL,
            name TEXT DEFAULT '',
            holiday_type INTEGER DEFAULT 1,
            UNIQUE(date)
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_holidays_date ON holidays(date)")

    # Relays
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS relays (
            id INTEGER PRIMARY KEY,
            relay_name TEXT DEFAULT '',
            pulse_duration_ms INTEGER DEFAULT 1000,
            control_timezone INTEGER DEFAULT 2,
            flags INTEGER DEFAULT 0,
            current_state INTEGER DEFAULT 0,
            last_activated INTEGER,
            created_at INTEGER DEFAULT (strftime('%s','now')),
            updated_at INTEGER DEFAULT (strftime('%s','now'))
        )
    """)

    # Events (100K+ capacity, circular buffer)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id TEXT UNIQUE NOT NULL,
            event_type INTEGER NOT NULL,
            timestamp INTEGER NOT NULL,
            card_number TEXT,
            door_id INTEGER,
            granted INTEGER,
            reason TEXT,
            extra_data TEXT,
            exported INTEGER DEFAULT 0,
            acknowledged INTEGER DEFAULT 0
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_ts ON events(timestamp)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_card ON events(card_number)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_door ON events(door_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_exported ON events(exported)")

    # Configuration Changes Audit Trail
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS config_changes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp INTEGER NOT NULL,
            change_type TEXT NOT NULL,
            resource_id TEXT,
            action INTEGER NOT NULL,
            old_value TEXT,
            new_value TEXT,
            source INTEGER DEFAULT 1,
            source_user TEXT,
            source_ip TEXT,
            transaction_id TEXT
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_changes_ts ON config_changes(timestamp)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_changes_type ON config_changes(change_type)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_changes_source ON config_changes(source)")

    # System Status
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS system_status (
            key TEXT PRIMARY KEY,
            value TEXT,
            updated_at INTEGER DEFAULT (strftime('%s','now'))
        )
    """)

    # Insert default timezones
    cursor.execute("INSERT OR IGNORE INTO timezones (id, name, description) VALUES (0, 'Never', 'Never active')")
    cursor.execute("INSERT OR IGNORE INTO timezones (id, name, description) VALUES (1, 'Never', 'Never active (legacy)')")
    cursor.execute("INSERT OR IGNORE INTO timezones (id, name, description) VALUES (2, 'Always', '24/7 access')")

    # Insert default access level
    cursor.execute("INSERT OR IGNORE INTO access_levels (id, name, description) VALUES (1, 'Default', 'Default access level')")

    # Set schema version
    cursor.execute("INSERT OR REPLACE INTO system_status (key, value) VALUES ('schema_version', '2.0')")
    cursor.execute("INSERT OR REPLACE INTO system_status (key, value) VALUES ('hal_version', ?)", (HAL_VERSION,))

    conn.commit()
    conn.close()


@contextmanager
def get_db():
    """Get database connection with row factory"""
    conn = sqlite3.connect(HAL_DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


# =============================================================================
# Pydantic Models - HAL Data Structures
# =============================================================================

# Cards
class CardCreate(BaseModel):
    card_number: str
    facility_code: int = 0
    permission_id: int = 1
    holder_name: str = ""
    pin: Optional[str] = None
    activation_date: int = 0
    expiration_date: int = 0
    is_active: bool = True

class CardUpdate(BaseModel):
    facility_code: Optional[int] = None
    permission_id: Optional[int] = None
    holder_name: Optional[str] = None
    pin: Optional[str] = None
    activation_date: Optional[int] = None
    expiration_date: Optional[int] = None
    is_active: Optional[bool] = None

class CardResponse(BaseModel):
    id: int
    card_number: str
    facility_code: int
    permission_id: int
    holder_name: str
    activation_date: int
    expiration_date: int
    is_active: bool
    last_access_time: Optional[int]
    last_access_door: Optional[int]
    created_at: int
    updated_at: int

# Access Levels
class AccessLevelCreate(BaseModel):
    id: Optional[int] = None
    name: str
    description: str = ""
    priority: int = 0
    door_ids: List[int] = []

class AccessLevelUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[int] = None
    is_active: Optional[bool] = None
    door_ids: Optional[List[int]] = None

class AccessLevelDoorAssignment(BaseModel):
    door_id: int
    timezone_id: int = 2
    entry_allowed: bool = True
    exit_allowed: bool = True

class AccessLevelResponse(BaseModel):
    id: int
    name: str
    description: str
    priority: int
    is_active: bool
    doors: List[Dict[str, Any]] = []
    created_at: int
    updated_at: int

# Doors
class DoorCreate(BaseModel):
    id: Optional[int] = None
    door_name: str
    location: str = ""
    reader_address: int = 0
    strike_relay_id: Optional[int] = None
    strike_time_ms: int = 3000
    osdp_enabled: bool = False

class DoorUpdate(BaseModel):
    door_name: Optional[str] = None
    location: Optional[str] = None
    reader_address: Optional[int] = None
    reader_mode: Optional[int] = None
    strike_relay_id: Optional[int] = None
    strike_time_ms: Optional[int] = None
    held_open_time_ms: Optional[int] = None
    osdp_enabled: Optional[bool] = None

class DoorResponse(BaseModel):
    id: int
    door_name: str
    location: str
    reader_address: int
    reader_mode: int
    strike_relay_id: Optional[int]
    strike_time_ms: int
    held_open_time_ms: int
    osdp_enabled: bool
    is_online: bool
    last_event_time: Optional[int]
    created_at: int
    updated_at: int

class DoorControl(BaseModel):
    action: str  # "lock", "unlock", "momentary_unlock", "lockdown"
    duration_ms: Optional[int] = None

# Events (RAW format - HAL's native event structure)
class EventRaw(BaseModel):
    """Raw HAL event - kept in native format"""
    id: int
    event_id: str
    event_type: int
    timestamp: int
    card_number: Optional[str]
    door_id: Optional[int]
    granted: Optional[bool]
    reason: Optional[str]
    extra_data: Optional[Dict[str, Any]]
    exported: bool
    acknowledged: bool

class EventQuery(BaseModel):
    """Query parameters for event search"""
    start_time: Optional[int] = None
    end_time: Optional[int] = None
    event_types: Optional[List[int]] = None
    card_numbers: Optional[List[str]] = None
    door_ids: Optional[List[int]] = None
    granted: Optional[bool] = None
    limit: int = 100
    offset: int = 0
    order: str = "desc"  # "asc" or "desc"

# Timezones
class TimezoneIntervalCreate(BaseModel):
    day_of_week: int = 0  # 0-6 or bitmask
    start_time: int = 0   # seconds from midnight
    end_time: int = 86399
    recurrence_type: int = 0
    holiday_types: int = 0

class TimezoneCreate(BaseModel):
    id: Optional[int] = None
    name: str
    description: str = ""
    intervals: List[TimezoneIntervalCreate] = []

class TimezoneResponse(BaseModel):
    id: int
    name: str
    description: str
    is_active: bool
    intervals: List[Dict[str, Any]]
    created_at: int
    updated_at: int

# Holidays
class HolidayCreate(BaseModel):
    date: int  # YYYYMMDD format
    name: str = ""
    holiday_type: int = 1

class HolidayResponse(BaseModel):
    id: int
    date: int
    name: str
    holiday_type: int

# Config Changes (Audit Trail)
class ConfigChangeResponse(BaseModel):
    id: int
    timestamp: int
    change_type: str
    resource_id: Optional[str]
    action: int
    old_value: Optional[Dict[str, Any]]
    new_value: Optional[Dict[str, Any]]
    source: int
    source_user: Optional[str]

# System Health
class SystemHealth(BaseModel):
    status: str
    version: str
    timestamp: int
    uptime_seconds: int
    database: Dict[str, Any]
    statistics: Dict[str, int]
    hardware: Dict[str, Any]


# =============================================================================
# Helper Functions
# =============================================================================

startup_time = int(time.time())

def log_config_change(
    conn: sqlite3.Connection,
    change_type: str,
    resource_id: str,
    action: int,
    old_value: Any = None,
    new_value: Any = None,
    source: int = ChangeSource.LOCAL,
    source_user: str = None,
    source_ip: str = None,
    transaction_id: str = None
):
    """Log a configuration change to the audit trail"""
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO config_changes (
            timestamp, change_type, resource_id, action,
            old_value, new_value, source, source_user, source_ip, transaction_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        int(time.time()),
        change_type,
        resource_id,
        action,
        json.dumps(old_value) if old_value else None,
        json.dumps(new_value) if new_value else None,
        source,
        source_user,
        source_ip,
        transaction_id
    ))


def log_event(
    conn: sqlite3.Connection,
    event_type: int,
    card_number: str = None,
    door_id: int = None,
    granted: bool = None,
    reason: str = None,
    extra_data: Dict = None
) -> str:
    """Log an event to the event buffer"""
    event_id = str(uuid.uuid4())
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO events (
            event_id, event_type, timestamp, card_number, door_id,
            granted, reason, extra_data
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        event_id,
        event_type,
        int(time.time()),
        card_number,
        door_id,
        1 if granted else 0 if granted is not None else None,
        reason,
        json.dumps(extra_data) if extra_data else None
    ))

    # Enforce circular buffer - delete oldest if over capacity
    cursor.execute("SELECT COUNT(*) FROM events")
    count = cursor.fetchone()[0]
    if count > MAX_EVENTS:
        delete_count = count - MAX_EVENTS
        cursor.execute(f"DELETE FROM events WHERE id IN (SELECT id FROM events ORDER BY id LIMIT {delete_count})")

    return event_id


def enforce_card_limit(conn: sqlite3.Connection):
    """Enforce maximum card limit"""
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM cards")
    count = cursor.fetchone()[0]
    if count >= MAX_CARDS:
        raise HTTPException(
            status_code=507,
            detail=f"Card database full ({MAX_CARDS} cards maximum)"
        )


def get_source_info(
    x_source: Optional[str] = Header(None, alias="X-HAL-Source"),
    x_user: Optional[str] = Header(None, alias="X-HAL-User"),
    x_transaction: Optional[str] = Header(None, alias="X-HAL-Transaction")
) -> Dict[str, Any]:
    """Extract source information from headers"""
    source = ChangeSource.LOCAL
    if x_source:
        source_map = {"aether": ChangeSource.AETHER, "pacs": ChangeSource.PACS, "import": ChangeSource.IMPORT}
        source = source_map.get(x_source.lower(), ChangeSource.LOCAL)

    return {
        "source": source,
        "source_user": x_user,
        "transaction_id": x_transaction
    }


# =============================================================================
# Lifespan Handler
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown"""
    # Initialize database
    init_database(HAL_DB_PATH)

    print("=" * 70)
    print("HAL CORE API Server")
    print("=" * 70)
    print(f"Version:  {HAL_VERSION}")
    print(f"Port:     {HAL_PORT}")
    print(f"Database: {HAL_DB_PATH}")
    print(f"Mode:     STANDALONE (Mercury-style)")
    print("=" * 70)
    print("HAL is the BRAIN - operates independently of network")
    print("All access decisions made locally from local data")
    print("=" * 70)

    yield

    print("HAL Core API Server stopped")


# =============================================================================
# FastAPI Application
# =============================================================================

app = FastAPI(
    title="HAL Core API",
    description="""
    HAL Core - The Panel's Brain

    This is the SINGLE SOURCE OF TRUTH for all access control data.
    HAL operates STANDALONE like a Mercury panel - it does NOT require
    network connectivity to function.

    All data is stored locally:
    - Cards (1M+ capacity)
    - Access Levels
    - Doors & Readers
    - Events (100K+ buffer)
    - Timezones & Holidays
    - Complete Audit Trail
    """,
    version=HAL_VERSION,
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# Health & Status Endpoints
# =============================================================================

@app.get("/hal/health", response_model=SystemHealth, tags=["Health"])
async def get_health():
    """Get HAL system health and statistics"""
    with get_db() as conn:
        cursor = conn.cursor()

        # Get counts
        cursor.execute("SELECT COUNT(*) FROM cards")
        card_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM cards WHERE is_active = 1")
        active_cards = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM events")
        event_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM access_levels")
        access_level_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM doors")
        door_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM config_changes")
        change_count = cursor.fetchone()[0]

        # Get database size
        db_size = os.path.getsize(HAL_DB_PATH) if os.path.exists(HAL_DB_PATH) else 0

    return {
        "status": "healthy",
        "version": HAL_VERSION,
        "timestamp": int(time.time()),
        "uptime_seconds": int(time.time()) - startup_time,
        "database": {
            "path": HAL_DB_PATH,
            "size_bytes": db_size,
            "size_mb": round(db_size / (1024 * 1024), 2)
        },
        "statistics": {
            "cards_total": card_count,
            "cards_active": active_cards,
            "cards_capacity": MAX_CARDS,
            "events_total": event_count,
            "events_capacity": MAX_EVENTS,
            "access_levels": access_level_count,
            "doors": door_count,
            "config_changes": change_count
        },
        "hardware": {
            "mode": "standalone",
            "network_required": False
        }
    }


# =============================================================================
# Card Endpoints (1M+ capacity)
# =============================================================================

@app.get("/hal/cards", response_model=List[CardResponse], tags=["Cards"])
async def list_cards(
    limit: int = Query(100, le=1000),
    offset: int = 0,
    active_only: bool = False,
    permission_id: Optional[int] = None,
    search: Optional[str] = None
):
    """List cards with pagination and filtering"""
    with get_db() as conn:
        cursor = conn.cursor()

        query = "SELECT * FROM cards WHERE 1=1"
        params = []

        if active_only:
            query += " AND is_active = 1"

        if permission_id is not None:
            query += " AND permission_id = ?"
            params.append(permission_id)

        if search:
            query += " AND (card_number LIKE ? OR holder_name LIKE ?)"
            params.extend([f"%{search}%", f"%{search}%"])

        query += " ORDER BY id LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cursor.execute(query, params)
        rows = cursor.fetchall()

    return [dict(row) for row in rows]


@app.get("/hal/cards/count", tags=["Cards"])
async def count_cards(active_only: bool = False, permission_id: Optional[int] = None):
    """Get total card count"""
    with get_db() as conn:
        cursor = conn.cursor()

        query = "SELECT COUNT(*) FROM cards WHERE 1=1"
        params = []

        if active_only:
            query += " AND is_active = 1"

        if permission_id is not None:
            query += " AND permission_id = ?"
            params.append(permission_id)

        cursor.execute(query, params)
        count = cursor.fetchone()[0]

    return {"count": count, "capacity": MAX_CARDS}


@app.get("/hal/cards/{card_number}", response_model=CardResponse, tags=["Cards"])
async def get_card(card_number: str):
    """Get card by card number"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM cards WHERE card_number = ?", (card_number,))
        row = cursor.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Card not found")

    return dict(row)


@app.post("/hal/cards", response_model=CardResponse, status_code=status.HTTP_201_CREATED, tags=["Cards"])
async def create_card(card: CardCreate, source_info: Dict = Depends(get_source_info)):
    """Add a new card to HAL's local database"""
    with get_db() as conn:
        enforce_card_limit(conn)

        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO cards (
                    card_number, facility_code, permission_id, holder_name,
                    pin_hash, activation_date, expiration_date, is_active
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                card.card_number,
                card.facility_code,
                card.permission_id,
                card.holder_name,
                card.pin,  # In production: hash this
                card.activation_date,
                card.expiration_date,
                1 if card.is_active else 0
            ))

            card_id = cursor.lastrowid

            # Log the change
            log_config_change(
                conn,
                "card",
                card.card_number,
                ChangeAction.CREATE,
                new_value=card.model_dump(),
                **source_info
            )

            conn.commit()

            cursor.execute("SELECT * FROM cards WHERE id = ?", (card_id,))
            return dict(cursor.fetchone())

        except sqlite3.IntegrityError:
            raise HTTPException(status_code=409, detail="Card already exists")


@app.put("/hal/cards/{card_number}", response_model=CardResponse, tags=["Cards"])
async def update_card(card_number: str, update: CardUpdate, source_info: Dict = Depends(get_source_info)):
    """Update an existing card"""
    with get_db() as conn:
        cursor = conn.cursor()

        # Get current values for audit
        cursor.execute("SELECT * FROM cards WHERE card_number = ?", (card_number,))
        old_row = cursor.fetchone()
        if not old_row:
            raise HTTPException(status_code=404, detail="Card not found")

        old_value = dict(old_row)

        # Build update query dynamically
        updates = []
        params = []

        for field, value in update.model_dump(exclude_unset=True).items():
            if value is not None:
                if field == "is_active":
                    updates.append("is_active = ?")
                    params.append(1 if value else 0)
                elif field == "pin":
                    updates.append("pin_hash = ?")
                    params.append(value)  # In production: hash
                else:
                    updates.append(f"{field} = ?")
                    params.append(value)

        if not updates:
            raise HTTPException(status_code=400, detail="No fields to update")

        updates.append("updated_at = ?")
        params.append(int(time.time()))
        params.append(card_number)

        cursor.execute(f"UPDATE cards SET {', '.join(updates)} WHERE card_number = ?", params)

        # Log the change
        log_config_change(
            conn,
            "card",
            card_number,
            ChangeAction.UPDATE,
            old_value=old_value,
            new_value=update.model_dump(exclude_unset=True),
            **source_info
        )

        conn.commit()

        cursor.execute("SELECT * FROM cards WHERE card_number = ?", (card_number,))
        return dict(cursor.fetchone())


@app.delete("/hal/cards/{card_number}", tags=["Cards"])
async def delete_card(card_number: str, source_info: Dict = Depends(get_source_info)):
    """Delete a card from HAL's database"""
    with get_db() as conn:
        cursor = conn.cursor()

        # Get current values for audit
        cursor.execute("SELECT * FROM cards WHERE card_number = ?", (card_number,))
        old_row = cursor.fetchone()
        if not old_row:
            raise HTTPException(status_code=404, detail="Card not found")

        cursor.execute("DELETE FROM cards WHERE card_number = ?", (card_number,))

        # Log the change
        log_config_change(
            conn,
            "card",
            card_number,
            ChangeAction.DELETE,
            old_value=dict(old_row),
            **source_info
        )

        conn.commit()

    return {"status": "deleted", "card_number": card_number}


# =============================================================================
# Access Level Endpoints
# =============================================================================

@app.get("/hal/access-levels", response_model=List[AccessLevelResponse], tags=["Access Levels"])
async def list_access_levels(include_doors: bool = True):
    """List all access levels"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM access_levels ORDER BY id")
        levels = cursor.fetchall()

        result = []
        for level in levels:
            level_dict = dict(level)
            level_dict["doors"] = []

            if include_doors:
                cursor.execute("""
                    SELECT ald.*, d.door_name
                    FROM access_level_doors ald
                    JOIN doors d ON ald.door_id = d.id
                    WHERE ald.access_level_id = ?
                """, (level["id"],))
                level_dict["doors"] = [dict(row) for row in cursor.fetchall()]

            result.append(level_dict)

    return result


@app.get("/hal/access-levels/{level_id}", response_model=AccessLevelResponse, tags=["Access Levels"])
async def get_access_level(level_id: int):
    """Get access level by ID"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM access_levels WHERE id = ?", (level_id,))
        level = cursor.fetchone()

        if not level:
            raise HTTPException(status_code=404, detail="Access level not found")

        level_dict = dict(level)

        cursor.execute("""
            SELECT ald.*, d.door_name
            FROM access_level_doors ald
            JOIN doors d ON ald.door_id = d.id
            WHERE ald.access_level_id = ?
        """, (level_id,))
        level_dict["doors"] = [dict(row) for row in cursor.fetchall()]

    return level_dict


@app.post("/hal/access-levels", response_model=AccessLevelResponse, status_code=status.HTTP_201_CREATED, tags=["Access Levels"])
async def create_access_level(level: AccessLevelCreate, source_info: Dict = Depends(get_source_info)):
    """Create a new access level"""
    with get_db() as conn:
        cursor = conn.cursor()

        if level.id:
            cursor.execute("SELECT id FROM access_levels WHERE id = ?", (level.id,))
            if cursor.fetchone():
                raise HTTPException(status_code=409, detail="Access level ID already exists")
            cursor.execute("""
                INSERT INTO access_levels (id, name, description, priority) VALUES (?, ?, ?, ?)
            """, (level.id, level.name, level.description, level.priority))
            level_id = level.id
        else:
            cursor.execute("""
                INSERT INTO access_levels (name, description, priority) VALUES (?, ?, ?)
            """, (level.name, level.description, level.priority))
            level_id = cursor.lastrowid

        # Add door assignments
        for door_id in level.door_ids:
            cursor.execute("""
                INSERT OR IGNORE INTO access_level_doors (access_level_id, door_id) VALUES (?, ?)
            """, (level_id, door_id))

        # Log the change
        log_config_change(
            conn,
            "access_level",
            str(level_id),
            ChangeAction.CREATE,
            new_value=level.model_dump(),
            **source_info
        )

        conn.commit()

        # Return full response
        cursor.execute("SELECT * FROM access_levels WHERE id = ?", (level_id,))
        level_dict = dict(cursor.fetchone())

        cursor.execute("""
            SELECT ald.*, d.door_name
            FROM access_level_doors ald
            JOIN doors d ON ald.door_id = d.id
            WHERE ald.access_level_id = ?
        """, (level_id,))
        level_dict["doors"] = [dict(row) for row in cursor.fetchall()]

    return level_dict


@app.put("/hal/access-levels/{level_id}", response_model=AccessLevelResponse, tags=["Access Levels"])
async def update_access_level(level_id: int, update: AccessLevelUpdate, source_info: Dict = Depends(get_source_info)):
    """Update an access level"""
    with get_db() as conn:
        cursor = conn.cursor()

        # Get current values
        cursor.execute("SELECT * FROM access_levels WHERE id = ?", (level_id,))
        old_row = cursor.fetchone()
        if not old_row:
            raise HTTPException(status_code=404, detail="Access level not found")

        old_value = dict(old_row)

        # Update fields
        updates = []
        params = []

        for field, value in update.model_dump(exclude_unset=True).items():
            if value is not None and field != "door_ids":
                if field == "is_active":
                    updates.append("is_active = ?")
                    params.append(1 if value else 0)
                else:
                    updates.append(f"{field} = ?")
                    params.append(value)

        if updates:
            updates.append("updated_at = ?")
            params.append(int(time.time()))
            params.append(level_id)
            cursor.execute(f"UPDATE access_levels SET {', '.join(updates)} WHERE id = ?", params)

        # Update door assignments if provided
        if update.door_ids is not None:
            cursor.execute("DELETE FROM access_level_doors WHERE access_level_id = ?", (level_id,))
            for door_id in update.door_ids:
                cursor.execute("""
                    INSERT INTO access_level_doors (access_level_id, door_id) VALUES (?, ?)
                """, (level_id, door_id))

        # Log change
        log_config_change(
            conn,
            "access_level",
            str(level_id),
            ChangeAction.UPDATE,
            old_value=old_value,
            new_value=update.model_dump(exclude_unset=True),
            **source_info
        )

        conn.commit()

        # Return updated
        cursor.execute("SELECT * FROM access_levels WHERE id = ?", (level_id,))
        level_dict = dict(cursor.fetchone())

        cursor.execute("""
            SELECT ald.*, d.door_name
            FROM access_level_doors ald
            JOIN doors d ON ald.door_id = d.id
            WHERE ald.access_level_id = ?
        """, (level_id,))
        level_dict["doors"] = [dict(row) for row in cursor.fetchall()]

    return level_dict


@app.delete("/hal/access-levels/{level_id}", tags=["Access Levels"])
async def delete_access_level(level_id: int, source_info: Dict = Depends(get_source_info)):
    """Delete an access level"""
    if level_id == 1:
        raise HTTPException(status_code=400, detail="Cannot delete default access level")

    with get_db() as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM access_levels WHERE id = ?", (level_id,))
        old_row = cursor.fetchone()
        if not old_row:
            raise HTTPException(status_code=404, detail="Access level not found")

        # Check if any cards use this level
        cursor.execute("SELECT COUNT(*) FROM cards WHERE permission_id = ?", (level_id,))
        card_count = cursor.fetchone()[0]
        if card_count > 0:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot delete: {card_count} cards use this access level"
            )

        cursor.execute("DELETE FROM access_levels WHERE id = ?", (level_id,))

        log_config_change(
            conn,
            "access_level",
            str(level_id),
            ChangeAction.DELETE,
            old_value=dict(old_row),
            **source_info
        )

        conn.commit()

    return {"status": "deleted", "id": level_id}


# =============================================================================
# Door Endpoints
# =============================================================================

@app.get("/hal/doors", response_model=List[DoorResponse], tags=["Doors"])
async def list_doors():
    """List all doors"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM doors ORDER BY id")
        return [dict(row) for row in cursor.fetchall()]


@app.get("/hal/doors/{door_id}", response_model=DoorResponse, tags=["Doors"])
async def get_door(door_id: int):
    """Get door by ID"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM doors WHERE id = ?", (door_id,))
        row = cursor.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Door not found")

    return dict(row)


@app.post("/hal/doors", response_model=DoorResponse, status_code=status.HTTP_201_CREATED, tags=["Doors"])
async def create_door(door: DoorCreate, source_info: Dict = Depends(get_source_info)):
    """Create a new door"""
    with get_db() as conn:
        cursor = conn.cursor()

        if door.id:
            cursor.execute("SELECT id FROM doors WHERE id = ?", (door.id,))
            if cursor.fetchone():
                raise HTTPException(status_code=409, detail="Door ID already exists")
            cursor.execute("""
                INSERT INTO doors (id, door_name, location, reader_address, strike_relay_id, strike_time_ms, osdp_enabled)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (door.id, door.door_name, door.location, door.reader_address, door.strike_relay_id, door.strike_time_ms, 1 if door.osdp_enabled else 0))
            door_id = door.id
        else:
            cursor.execute("""
                INSERT INTO doors (door_name, location, reader_address, strike_relay_id, strike_time_ms, osdp_enabled)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (door.door_name, door.location, door.reader_address, door.strike_relay_id, door.strike_time_ms, 1 if door.osdp_enabled else 0))
            door_id = cursor.lastrowid

        log_config_change(
            conn,
            "door",
            str(door_id),
            ChangeAction.CREATE,
            new_value=door.model_dump(),
            **source_info
        )

        conn.commit()

        cursor.execute("SELECT * FROM doors WHERE id = ?", (door_id,))
        return dict(cursor.fetchone())


@app.put("/hal/doors/{door_id}", response_model=DoorResponse, tags=["Doors"])
async def update_door(door_id: int, update: DoorUpdate, source_info: Dict = Depends(get_source_info)):
    """Update a door"""
    with get_db() as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM doors WHERE id = ?", (door_id,))
        old_row = cursor.fetchone()
        if not old_row:
            raise HTTPException(status_code=404, detail="Door not found")

        updates = []
        params = []

        for field, value in update.model_dump(exclude_unset=True).items():
            if value is not None:
                if field == "osdp_enabled":
                    updates.append("osdp_enabled = ?")
                    params.append(1 if value else 0)
                else:
                    updates.append(f"{field} = ?")
                    params.append(value)

        if updates:
            updates.append("updated_at = ?")
            params.append(int(time.time()))
            params.append(door_id)
            cursor.execute(f"UPDATE doors SET {', '.join(updates)} WHERE id = ?", params)

        log_config_change(
            conn,
            "door",
            str(door_id),
            ChangeAction.UPDATE,
            old_value=dict(old_row),
            new_value=update.model_dump(exclude_unset=True),
            **source_info
        )

        conn.commit()

        cursor.execute("SELECT * FROM doors WHERE id = ?", (door_id,))
        return dict(cursor.fetchone())


@app.post("/hal/doors/{door_id}/control", tags=["Doors"])
async def control_door(door_id: int, control: DoorControl, source_info: Dict = Depends(get_source_info)):
    """Control door lock state"""
    with get_db() as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM doors WHERE id = ?", (door_id,))
        door = cursor.fetchone()
        if not door:
            raise HTTPException(status_code=404, detail="Door not found")

        # Log the control action as an event
        extra_data = {"action": control.action}
        if control.duration_ms:
            extra_data["duration_ms"] = control.duration_ms

        event_id = log_event(
            conn,
            EventType.SYSTEM_EVENT,
            door_id=door_id,
            reason=f"Door control: {control.action}",
            extra_data=extra_data
        )

        conn.commit()

    # In production, this would send command to hardware
    return {
        "status": "success",
        "door_id": door_id,
        "action": control.action,
        "event_id": event_id
    }


# =============================================================================
# Event Endpoints (RAW FORMAT - 100K+ buffer)
# =============================================================================

@app.get("/hal/events", response_model=List[EventRaw], tags=["Events"])
async def list_events(
    limit: int = Query(100, le=1000),
    offset: int = 0,
    start_time: Optional[int] = None,
    end_time: Optional[int] = None,
    event_type: Optional[int] = None,
    card_number: Optional[str] = None,
    door_id: Optional[int] = None,
    order: str = "desc"
):
    """
    Get events in RAW format from HAL's event buffer.
    Events are kept in their native format - Aether Access handles display formatting.
    """
    with get_db() as conn:
        cursor = conn.cursor()

        query = "SELECT * FROM events WHERE 1=1"
        params = []

        if start_time:
            query += " AND timestamp >= ?"
            params.append(start_time)

        if end_time:
            query += " AND timestamp <= ?"
            params.append(end_time)

        if event_type is not None:
            query += " AND event_type = ?"
            params.append(event_type)

        if card_number:
            query += " AND card_number = ?"
            params.append(card_number)

        if door_id is not None:
            query += " AND door_id = ?"
            params.append(door_id)

        order_dir = "DESC" if order.lower() == "desc" else "ASC"
        query += f" ORDER BY timestamp {order_dir}, id {order_dir} LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cursor.execute(query, params)
        rows = cursor.fetchall()

    result = []
    for row in rows:
        event = dict(row)
        if event.get("extra_data"):
            try:
                event["extra_data"] = json.loads(event["extra_data"])
            except:
                pass
        event["granted"] = bool(event.get("granted")) if event.get("granted") is not None else None
        event["exported"] = bool(event.get("exported"))
        event["acknowledged"] = bool(event.get("acknowledged"))
        result.append(event)

    return result


@app.get("/hal/events/count", tags=["Events"])
async def count_events(
    start_time: Optional[int] = None,
    end_time: Optional[int] = None,
    event_type: Optional[int] = None
):
    """Get event count with optional filtering"""
    with get_db() as conn:
        cursor = conn.cursor()

        query = "SELECT COUNT(*) FROM events WHERE 1=1"
        params = []

        if start_time:
            query += " AND timestamp >= ?"
            params.append(start_time)

        if end_time:
            query += " AND timestamp <= ?"
            params.append(end_time)

        if event_type is not None:
            query += " AND event_type = ?"
            params.append(event_type)

        cursor.execute(query, params)
        count = cursor.fetchone()[0]

    return {"count": count, "capacity": MAX_EVENTS}


@app.get("/hal/events/{event_id}", response_model=EventRaw, tags=["Events"])
async def get_event(event_id: str):
    """Get a specific event by ID"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM events WHERE event_id = ?", (event_id,))
        row = cursor.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Event not found")

    event = dict(row)
    if event.get("extra_data"):
        try:
            event["extra_data"] = json.loads(event["extra_data"])
        except:
            pass
    event["granted"] = bool(event.get("granted")) if event.get("granted") is not None else None
    event["exported"] = bool(event.get("exported"))
    event["acknowledged"] = bool(event.get("acknowledged"))

    return event


@app.post("/hal/events/acknowledge", tags=["Events"])
async def acknowledge_events(event_ids: List[str]):
    """Mark events as acknowledged"""
    with get_db() as conn:
        cursor = conn.cursor()

        placeholders = ",".join(["?" for _ in event_ids])
        cursor.execute(
            f"UPDATE events SET acknowledged = 1 WHERE event_id IN ({placeholders})",
            event_ids
        )
        updated = cursor.rowcount
        conn.commit()

    return {"acknowledged": updated}


@app.post("/hal/events/mark-exported", tags=["Events"])
async def mark_events_exported(event_ids: List[str]):
    """Mark events as exported (for Ambient.ai daemon)"""
    with get_db() as conn:
        cursor = conn.cursor()

        placeholders = ",".join(["?" for _ in event_ids])
        cursor.execute(
            f"UPDATE events SET exported = 1 WHERE event_id IN ({placeholders})",
            event_ids
        )
        updated = cursor.rowcount
        conn.commit()

    return {"marked_exported": updated}


@app.get("/hal/events/unexported", response_model=List[EventRaw], tags=["Events"])
async def get_unexported_events(limit: int = Query(100, le=1000)):
    """Get events not yet exported (for Ambient.ai daemon)"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM events WHERE exported = 0 ORDER BY timestamp ASC LIMIT ?",
            (limit,)
        )
        rows = cursor.fetchall()

    result = []
    for row in rows:
        event = dict(row)
        if event.get("extra_data"):
            try:
                event["extra_data"] = json.loads(event["extra_data"])
            except:
                pass
        event["granted"] = bool(event.get("granted")) if event.get("granted") is not None else None
        event["exported"] = bool(event.get("exported"))
        event["acknowledged"] = bool(event.get("acknowledged"))
        result.append(event)

    return result


# WebSocket for real-time event streaming
@app.websocket("/hal/events/stream")
async def event_stream(websocket: WebSocket):
    """WebSocket stream for real-time events"""
    await websocket.accept()

    last_id = 0

    try:
        while True:
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM events WHERE id > ? ORDER BY id ASC LIMIT 100",
                    (last_id,)
                )
                rows = cursor.fetchall()

                for row in rows:
                    event = dict(row)
                    if event.get("extra_data"):
                        try:
                            event["extra_data"] = json.loads(event["extra_data"])
                        except:
                            pass
                    event["granted"] = bool(event.get("granted")) if event.get("granted") is not None else None
                    event["exported"] = bool(event.get("exported"))
                    event["acknowledged"] = bool(event.get("acknowledged"))

                    await websocket.send_json(event)
                    last_id = event["id"]

            await asyncio.sleep(0.5)  # Poll every 500ms

    except Exception:
        pass


# =============================================================================
# Config Changes Audit Trail
# =============================================================================

@app.get("/hal/config-changes", response_model=List[ConfigChangeResponse], tags=["Audit Trail"])
async def list_config_changes(
    limit: int = Query(100, le=1000),
    offset: int = 0,
    change_type: Optional[str] = None,
    source: Optional[int] = None,
    start_time: Optional[int] = None,
    end_time: Optional[int] = None
):
    """Get configuration change audit trail"""
    with get_db() as conn:
        cursor = conn.cursor()

        query = "SELECT * FROM config_changes WHERE 1=1"
        params = []

        if change_type:
            query += " AND change_type = ?"
            params.append(change_type)

        if source is not None:
            query += " AND source = ?"
            params.append(source)

        if start_time:
            query += " AND timestamp >= ?"
            params.append(start_time)

        if end_time:
            query += " AND timestamp <= ?"
            params.append(end_time)

        query += " ORDER BY timestamp DESC, id DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cursor.execute(query, params)
        rows = cursor.fetchall()

    result = []
    for row in rows:
        change = dict(row)
        if change.get("old_value"):
            try:
                change["old_value"] = json.loads(change["old_value"])
            except:
                pass
        if change.get("new_value"):
            try:
                change["new_value"] = json.loads(change["new_value"])
            except:
                pass
        result.append(change)

    return result


# =============================================================================
# Timezones
# =============================================================================

@app.get("/hal/timezones", response_model=List[TimezoneResponse], tags=["Timezones"])
async def list_timezones():
    """List all timezones"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM timezones ORDER BY id")
        timezones = cursor.fetchall()

        result = []
        for tz in timezones:
            tz_dict = dict(tz)
            cursor.execute("SELECT * FROM timezone_intervals WHERE timezone_id = ?", (tz["id"],))
            tz_dict["intervals"] = [dict(row) for row in cursor.fetchall()]
            result.append(tz_dict)

    return result


@app.post("/hal/timezones", response_model=TimezoneResponse, status_code=status.HTTP_201_CREATED, tags=["Timezones"])
async def create_timezone(tz: TimezoneCreate, source_info: Dict = Depends(get_source_info)):
    """Create a new timezone"""
    with get_db() as conn:
        cursor = conn.cursor()

        if tz.id:
            cursor.execute("SELECT id FROM timezones WHERE id = ?", (tz.id,))
            if cursor.fetchone():
                raise HTTPException(status_code=409, detail="Timezone ID already exists")
            cursor.execute(
                "INSERT INTO timezones (id, name, description) VALUES (?, ?, ?)",
                (tz.id, tz.name, tz.description)
            )
            tz_id = tz.id
        else:
            cursor.execute(
                "INSERT INTO timezones (name, description) VALUES (?, ?)",
                (tz.name, tz.description)
            )
            tz_id = cursor.lastrowid

        # Add intervals
        for interval in tz.intervals:
            cursor.execute("""
                INSERT INTO timezone_intervals (
                    timezone_id, day_of_week, start_time, end_time,
                    recurrence_type, holiday_types
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                tz_id, interval.day_of_week, interval.start_time, interval.end_time,
                interval.recurrence_type, interval.holiday_types
            ))

        log_config_change(
            conn, "timezone", str(tz_id), ChangeAction.CREATE,
            new_value=tz.model_dump(), **source_info
        )

        conn.commit()

        cursor.execute("SELECT * FROM timezones WHERE id = ?", (tz_id,))
        tz_dict = dict(cursor.fetchone())
        cursor.execute("SELECT * FROM timezone_intervals WHERE timezone_id = ?", (tz_id,))
        tz_dict["intervals"] = [dict(row) for row in cursor.fetchall()]

    return tz_dict


# =============================================================================
# Holidays
# =============================================================================

@app.get("/hal/holidays", response_model=List[HolidayResponse], tags=["Holidays"])
async def list_holidays(year: Optional[int] = None):
    """List holidays"""
    with get_db() as conn:
        cursor = conn.cursor()

        if year:
            start_date = year * 10000 + 101  # YYYYMMDD for Jan 1
            end_date = year * 10000 + 1231   # YYYYMMDD for Dec 31
            cursor.execute(
                "SELECT * FROM holidays WHERE date >= ? AND date <= ? ORDER BY date",
                (start_date, end_date)
            )
        else:
            cursor.execute("SELECT * FROM holidays ORDER BY date")

        return [dict(row) for row in cursor.fetchall()]


@app.post("/hal/holidays", response_model=HolidayResponse, status_code=status.HTTP_201_CREATED, tags=["Holidays"])
async def create_holiday(holiday: HolidayCreate, source_info: Dict = Depends(get_source_info)):
    """Create a holiday"""
    with get_db() as conn:
        cursor = conn.cursor()

        try:
            cursor.execute(
                "INSERT INTO holidays (date, name, holiday_type) VALUES (?, ?, ?)",
                (holiday.date, holiday.name, holiday.holiday_type)
            )
            holiday_id = cursor.lastrowid

            log_config_change(
                conn, "holiday", str(holiday.date), ChangeAction.CREATE,
                new_value=holiday.model_dump(), **source_info
            )

            conn.commit()

            cursor.execute("SELECT * FROM holidays WHERE id = ?", (holiday_id,))
            return dict(cursor.fetchone())

        except sqlite3.IntegrityError:
            raise HTTPException(status_code=409, detail="Holiday already exists for this date")


@app.delete("/hal/holidays/{date}", tags=["Holidays"])
async def delete_holiday(date: int, source_info: Dict = Depends(get_source_info)):
    """Delete a holiday by date (YYYYMMDD format)"""
    with get_db() as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM holidays WHERE date = ?", (date,))
        old_row = cursor.fetchone()
        if not old_row:
            raise HTTPException(status_code=404, detail="Holiday not found")

        cursor.execute("DELETE FROM holidays WHERE date = ?", (date,))

        log_config_change(
            conn, "holiday", str(date), ChangeAction.DELETE,
            old_value=dict(old_row), **source_info
        )

        conn.commit()

    return {"status": "deleted", "date": date}


# =============================================================================
# Bulk Sync Endpoint (for PACS integration)
# =============================================================================

@app.post("/hal/sync", tags=["Sync"])
async def bulk_sync(
    cards: Optional[List[CardCreate]] = None,
    access_levels: Optional[List[AccessLevelCreate]] = None,
    transaction_id: Optional[str] = None,
    source_info: Dict = Depends(get_source_info)
):
    """
    Bulk sync from external PACS.
    Accepts cards and/or access levels in a single transaction.
    """
    results = {
        "cards": {"created": 0, "updated": 0, "errors": []},
        "access_levels": {"created": 0, "updated": 0, "errors": []},
        "transaction_id": transaction_id or str(uuid.uuid4())
    }

    source_info["transaction_id"] = results["transaction_id"]

    with get_db() as conn:
        cursor = conn.cursor()

        # Sync cards
        if cards:
            for card in cards:
                try:
                    cursor.execute("SELECT id FROM cards WHERE card_number = ?", (card.card_number,))
                    existing = cursor.fetchone()

                    if existing:
                        # Update
                        cursor.execute("""
                            UPDATE cards SET
                                facility_code = ?, permission_id = ?, holder_name = ?,
                                activation_date = ?, expiration_date = ?, is_active = ?,
                                updated_at = ?
                            WHERE card_number = ?
                        """, (
                            card.facility_code, card.permission_id, card.holder_name,
                            card.activation_date, card.expiration_date, 1 if card.is_active else 0,
                            int(time.time()), card.card_number
                        ))
                        results["cards"]["updated"] += 1
                    else:
                        # Create
                        cursor.execute("""
                            INSERT INTO cards (
                                card_number, facility_code, permission_id, holder_name,
                                activation_date, expiration_date, is_active
                            ) VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, (
                            card.card_number, card.facility_code, card.permission_id,
                            card.holder_name, card.activation_date, card.expiration_date,
                            1 if card.is_active else 0
                        ))
                        results["cards"]["created"] += 1

                except Exception as e:
                    results["cards"]["errors"].append({
                        "card_number": card.card_number,
                        "error": str(e)
                    })

        # Sync access levels
        if access_levels:
            for level in access_levels:
                try:
                    if level.id:
                        cursor.execute("SELECT id FROM access_levels WHERE id = ?", (level.id,))
                        existing = cursor.fetchone()

                        if existing:
                            cursor.execute("""
                                UPDATE access_levels SET name = ?, description = ?, priority = ?, updated_at = ?
                                WHERE id = ?
                            """, (level.name, level.description, level.priority, int(time.time()), level.id))
                            results["access_levels"]["updated"] += 1
                        else:
                            cursor.execute("""
                                INSERT INTO access_levels (id, name, description, priority) VALUES (?, ?, ?, ?)
                            """, (level.id, level.name, level.description, level.priority))
                            results["access_levels"]["created"] += 1

                        # Update door assignments
                        cursor.execute("DELETE FROM access_level_doors WHERE access_level_id = ?", (level.id,))
                        for door_id in level.door_ids:
                            cursor.execute(
                                "INSERT INTO access_level_doors (access_level_id, door_id) VALUES (?, ?)",
                                (level.id, door_id)
                            )
                    else:
                        cursor.execute("""
                            INSERT INTO access_levels (name, description, priority) VALUES (?, ?, ?)
                        """, (level.name, level.description, level.priority))
                        results["access_levels"]["created"] += 1

                except Exception as e:
                    results["access_levels"]["errors"].append({
                        "name": level.name,
                        "error": str(e)
                    })

        # Log bulk sync
        log_config_change(
            conn, "bulk_sync", results["transaction_id"], ChangeAction.UPDATE,
            new_value={
                "cards": len(cards) if cards else 0,
                "access_levels": len(access_levels) if access_levels else 0
            },
            **source_info
        )

        conn.commit()

    return results


# =============================================================================
# Export Configuration (Full dump for backup/migration)
# =============================================================================

@app.get("/hal/export", tags=["Export"])
async def export_configuration():
    """Export full HAL configuration as JSON"""
    with get_db() as conn:
        cursor = conn.cursor()

        export = {
            "version": HAL_VERSION,
            "exported_at": int(time.time()),
            "cards": [],
            "access_levels": [],
            "doors": [],
            "timezones": [],
            "holidays": [],
            "relays": []
        }

        # Export cards
        cursor.execute("SELECT * FROM cards")
        export["cards"] = [dict(row) for row in cursor.fetchall()]

        # Export access levels with door assignments
        cursor.execute("SELECT * FROM access_levels")
        for level in cursor.fetchall():
            level_dict = dict(level)
            cursor.execute(
                "SELECT door_id, timezone_id FROM access_level_doors WHERE access_level_id = ?",
                (level["id"],)
            )
            level_dict["doors"] = [dict(row) for row in cursor.fetchall()]
            export["access_levels"].append(level_dict)

        # Export doors
        cursor.execute("SELECT * FROM doors")
        export["doors"] = [dict(row) for row in cursor.fetchall()]

        # Export timezones with intervals
        cursor.execute("SELECT * FROM timezones")
        for tz in cursor.fetchall():
            tz_dict = dict(tz)
            cursor.execute("SELECT * FROM timezone_intervals WHERE timezone_id = ?", (tz["id"],))
            tz_dict["intervals"] = [dict(row) for row in cursor.fetchall()]
            export["timezones"].append(tz_dict)

        # Export holidays
        cursor.execute("SELECT * FROM holidays")
        export["holidays"] = [dict(row) for row in cursor.fetchall()]

        # Export relays
        cursor.execute("SELECT * FROM relays")
        export["relays"] = [dict(row) for row in cursor.fetchall()]

    return export


# =============================================================================
# Main Entry Point
# =============================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=HAL_PORT,
        log_level="info"
    )
