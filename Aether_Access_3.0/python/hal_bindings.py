#!/usr/bin/env python3
"""
HAL Python Bindings
===================
Python bindings for the HAL C library using ctypes.

This module provides a Pythonic interface to the HAL C library,
allowing the unified API server to interact with hardware through
the compiled HAL shared library.

When the C library is not available, falls back to a SQLite-based
simulation mode that mimics the HAL behavior for development/testing.

Ambient.ai Integration:
-----------------------
This module supports Ambient.ai event ingestion format with:
- UUID-based entity identification (sourceSystemUid, deviceUid, personUid, etc.)
- Standard PACS alarm types (Door Forced Open, Door Held Open, Invalid Badge, etc.)
- Real-time event generation with proper timestamps

Usage:
    from hal_bindings import HAL

    hal = HAL("/path/to/database.db")
    hal.init()

    # Add a card
    hal.add_card("12345", permission_id=1, holder_name="John Doe")

    # Check access
    result = hal.check_access("12345", door_id=1)

    # Get events in Ambient.ai format
    events = hal.get_ambient_events(limit=100)

    hal.shutdown()
"""

import ctypes
import ctypes.util
import sqlite3
import os
import time
import json
import uuid
import logging
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, asdict, field
from enum import IntEnum, Enum
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


# =============================================================================
# Constants and Enums (matching hal_types.h)
# =============================================================================

class ErrorCode(IntEnum):
    OK = 0
    NODE_OFFLINE = 11
    BAD_PARAMS = 21
    OBJECT_NOT_FOUND = 22
    OUT_OF_MEMORY = 23
    DATABASE = 24
    FAILED = 25
    ALREADY_EXISTS = 26
    CRYPTO_ERROR = 27
    NOT_ENABLED = 28
    INVALID_STATE = 29
    AUTH_FAILED = 30


class AccessDecision(IntEnum):
    GRANT = 0
    DENY = 1
    ERROR = 2


class DenyReason(IntEnum):
    CARD_NOT_FOUND = 0
    NO_PERMISSION = 1
    TIME_RESTRICTION = 2
    CARD_BLOCKED = 3
    DOOR_NOT_FOUND = 4
    EXPIRED = 5
    NOT_YET_ACTIVE = 6
    APB_VIOLATION = 7  # Anti-passback
    DURESS = 8
    INVALID_PIN = 9


class EventType(IntEnum):
    """Event types for HAL - mapped to Ambient.ai alarm types"""
    ACCESS_GRANT = 0
    ACCESS_DENY = 1
    DOOR_UNLOCK = 2
    DOOR_LOCK = 3
    DOOR_FORCED_OPEN = 4
    DOOR_HELD_OPEN = 5
    DOOR_CLOSED = 6
    REX_ACTIVATED = 7
    TAMPER = 8
    COMMUNICATION_ERROR = 9
    COMMUNICATION_RESTORED = 10
    READER_OFFLINE = 11
    READER_ONLINE = 12
    INPUT_ACTIVE = 13
    INPUT_INACTIVE = 14
    RELAY_ACTIVATED = 15
    RELAY_DEACTIVATED = 16
    SYSTEM_START = 17
    SYSTEM_STOP = 18
    EMERGENCY_LOCKDOWN = 19
    EMERGENCY_UNLOCK = 20
    APB_VIOLATION = 21
    DURESS = 22
    INVALID_BADGE = 23
    EXPIRED_BADGE = 24


class DeviceType(str, Enum):
    """Device types for Ambient.ai integration"""
    PANEL = "Panel"
    READER = "Reader"
    ALARM_INPUT = "Alarm Input"
    RELAY = "Relay"
    DOOR = "Door"


# =============================================================================
# Ambient.ai Alarm Definitions
# =============================================================================

# Standard PACS alarm types that Ambient.ai expects
AMBIENT_ALARM_DEFINITIONS = {
    EventType.ACCESS_GRANT: {
        "name": "Access Granted",
        "uid": "00000000-0000-0000-0001-000000000001",
        "is_alarm": False,
    },
    EventType.ACCESS_DENY: {
        "name": "Access Denied",
        "uid": "00000000-0000-0000-0001-000000000002",
        "is_alarm": True,
    },
    EventType.DOOR_FORCED_OPEN: {
        "name": "Door Forced Open",
        "uid": "00000000-0000-0000-0001-000000000003",
        "is_alarm": True,
    },
    EventType.DOOR_HELD_OPEN: {
        "name": "Door Held Open",
        "uid": "00000000-0000-0000-0001-000000000004",
        "is_alarm": True,
    },
    EventType.INVALID_BADGE: {
        "name": "Invalid Badge",
        "uid": "00000000-0000-0000-0001-000000000005",
        "is_alarm": True,
    },
    EventType.EXPIRED_BADGE: {
        "name": "Expired Badge",
        "uid": "00000000-0000-0000-0001-000000000006",
        "is_alarm": True,
    },
    EventType.TAMPER: {
        "name": "Tamper Alarm",
        "uid": "00000000-0000-0000-0001-000000000007",
        "is_alarm": True,
    },
    EventType.COMMUNICATION_ERROR: {
        "name": "Communication Failure",
        "uid": "00000000-0000-0000-0001-000000000008",
        "is_alarm": True,
    },
    EventType.APB_VIOLATION: {
        "name": "Anti-Passback Violation",
        "uid": "00000000-0000-0000-0001-000000000009",
        "is_alarm": True,
    },
    EventType.DURESS: {
        "name": "Duress Alarm",
        "uid": "00000000-0000-0000-0001-000000000010",
        "is_alarm": True,
    },
    EventType.EMERGENCY_LOCKDOWN: {
        "name": "Emergency Lockdown",
        "uid": "00000000-0000-0000-0001-000000000011",
        "is_alarm": True,
    },
    EventType.DOOR_UNLOCK: {
        "name": "Door Unlocked",
        "uid": "00000000-0000-0000-0001-000000000012",
        "is_alarm": False,
    },
    EventType.DOOR_LOCK: {
        "name": "Door Locked",
        "uid": "00000000-0000-0000-0001-000000000013",
        "is_alarm": False,
    },
    EventType.REX_ACTIVATED: {
        "name": "Request to Exit",
        "uid": "00000000-0000-0000-0001-000000000014",
        "is_alarm": False,
    },
}


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class Card:
    card_number: str
    permission_id: int
    facility_code: int = 0
    holder_name: str = ""
    person_uid: str = ""  # UUID for Ambient.ai
    activation_date: int = 0
    expiration_date: int = 0
    is_active: bool = True
    is_blocked: bool = False
    use_limit: int = 0
    use_count: int = 0
    pin: str = ""
    created_at: int = 0
    updated_at: int = 0


@dataclass
class Person:
    """Person entity for Ambient.ai integration"""
    person_uid: str  # UUID
    first_name: str
    last_name: str
    email: str = ""
    department: str = ""
    employee_id: str = ""
    is_active: bool = True
    created_at: int = 0
    updated_at: int = 0


@dataclass
class AccessLevel:
    permission_id: int
    name: str
    description: str = ""
    doors: List[int] = None
    timezones: List[int] = None
    is_active: bool = True

    def __post_init__(self):
        if self.doors is None:
            self.doors = []
        if self.timezones is None:
            self.timezones = []


@dataclass
class Door:
    door_id: int
    name: str
    device_uid: str = ""  # UUID for Ambient.ai
    device_type: str = "Reader"
    reader_id: int = 0
    relay_id: int = 0
    panel_id: int = 1
    strike_time_ms: int = 3000
    held_open_time_s: int = 30
    rex_enabled: bool = True
    osdp_enabled: bool = False
    is_active: bool = True
    created_at: int = 0
    updated_at: int = 0


@dataclass
class AlarmDefinition:
    """Alarm definition for Ambient.ai"""
    alarm_uid: str  # UUID
    name: str
    event_type: int
    is_active: bool = True
    created_at: int = 0
    updated_at: int = 0


@dataclass
class Event:
    event_id: str  # UUID
    event_type: int
    timestamp: int
    card_number: str = ""
    door_id: int = 0
    reader_id: int = 0
    decision: int = 0
    deny_reason: int = 0
    details: str = ""
    # Ambient.ai fields
    device_uid: str = ""
    device_name: str = ""
    device_type: str = "Reader"
    alarm_uid: str = ""
    alarm_name: str = ""
    person_uid: str = ""
    person_first_name: str = ""
    person_last_name: str = ""
    access_item_key: str = ""
    exported: bool = False
    export_timestamp: int = 0


@dataclass
class AccessResult:
    granted: bool
    reason: str
    decision: AccessDecision
    deny_reason: Optional[DenyReason] = None
    strike_time_ms: int = 3000
    relay_id: int = 0


# =============================================================================
# HAL C Library Bindings (ctypes)
# =============================================================================

class HALCBindings:
    """Direct ctypes bindings to HAL C library"""

    def __init__(self, lib_path: str = None):
        self._lib = None
        self._hal = None

        if lib_path is None:
            lib_path = self._find_library()

        if lib_path and os.path.exists(lib_path):
            try:
                self._lib = ctypes.CDLL(lib_path)
                self._setup_bindings()
                logger.info(f"Loaded HAL C library from {lib_path}")
            except OSError as e:
                logger.warning(f"Failed to load HAL C library: {e}")
                self._lib = None
        else:
            logger.info("HAL C library not found, will use simulation mode")

    def _find_library(self) -> Optional[str]:
        """Find the HAL shared library"""
        search_paths = [
            "./lib/libhal.so",
            "./lib/libhal.dylib",
            "../lib/libhal.so",
            "../lib/libhal.dylib",
            "/usr/local/lib/libhal.so",
            "/usr/local/lib/libhal.dylib",
            "/opt/aether-access/lib/libhal.so",
        ]

        base_dir = Path(__file__).parent.parent
        search_paths.extend([
            str(base_dir / "lib" / "libhal.so"),
            str(base_dir / "lib" / "libhal.dylib"),
            str(base_dir / "build" / "libhal.so"),
            str(base_dir / "build" / "libhal.dylib"),
        ])

        for path in search_paths:
            if os.path.exists(path):
                return path

        lib_name = ctypes.util.find_library("hal")
        if lib_name:
            return lib_name

        return None

    def _setup_bindings(self):
        """Setup ctypes function signatures"""
        if not self._lib:
            return

        # HAL_Create
        self._lib.HAL_Create.argtypes = [ctypes.c_void_p]
        self._lib.HAL_Create.restype = ctypes.c_void_p

        # HAL_Destroy
        self._lib.HAL_Destroy.argtypes = [ctypes.c_void_p]
        self._lib.HAL_Destroy.restype = None

        # HAL_Connect
        self._lib.HAL_Connect.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_uint16]
        self._lib.HAL_Connect.restype = ctypes.c_int

        # HAL_Disconnect
        self._lib.HAL_Disconnect.argtypes = [ctypes.c_void_p]
        self._lib.HAL_Disconnect.restype = ctypes.c_int

        # HAL_IsConnected
        self._lib.HAL_IsConnected.argtypes = [ctypes.c_void_p]
        self._lib.HAL_IsConnected.restype = ctypes.c_uint8

    @property
    def is_available(self) -> bool:
        return self._lib is not None


# =============================================================================
# HAL Simulation (SQLite-based) with Ambient.ai Support
# =============================================================================

class HALSimulation:
    """
    SQLite-based HAL simulation for development/testing.
    Includes full Ambient.ai integration support with UUID-based entity tracking.
    """

    def __init__(self, db_path: str = ":memory:", source_system_uid: str = None):
        self.db_path = db_path
        self._conn: Optional[sqlite3.Connection] = None
        self._initialized = False
        self._event_counter = 0

        # Source system UUID - identifies this PACS system to Ambient.ai
        # This should be configured per-installation
        self._source_system_uid = source_system_uid or self._generate_or_load_system_uid()

    def _generate_or_load_system_uid(self) -> str:
        """Generate or load the source system UUID"""
        # Try to load from config file
        config_path = Path(self.db_path).parent / "system_uid.txt"
        if config_path.exists():
            return config_path.read_text().strip()

        # Generate new UUID
        system_uid = str(uuid.uuid4())

        # Try to save it
        try:
            config_path.write_text(system_uid)
        except:
            pass

        return system_uid

    @property
    def source_system_uid(self) -> str:
        """Get the source system UUID for Ambient.ai"""
        return self._source_system_uid

    def init(self) -> bool:
        """Initialize the HAL simulation"""
        try:
            self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
            self._create_tables()
            self._seed_alarm_definitions()
            self._initialized = True
            logger.info(f"HAL Simulation initialized with database: {self.db_path}")
            logger.info(f"Source System UID: {self._source_system_uid}")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize HAL simulation: {e}")
            return False

    def shutdown(self):
        """Shutdown the HAL simulation"""
        if self._conn:
            self._conn.close()
            self._conn = None
        self._initialized = False
        logger.info("HAL Simulation shutdown")

    def _create_tables(self):
        """Create database tables with Ambient.ai UUID support"""
        cursor = self._conn.cursor()

        # System configuration
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_config (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at INTEGER DEFAULT 0
            )
        """)

        # Store source system UID
        cursor.execute("""
            INSERT OR REPLACE INTO system_config (key, value, updated_at)
            VALUES ('source_system_uid', ?, ?)
        """, (self._source_system_uid, int(time.time())))

        # Persons table (for Ambient.ai)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS persons (
                person_uid TEXT PRIMARY KEY,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                email TEXT DEFAULT '',
                department TEXT DEFAULT '',
                employee_id TEXT DEFAULT '',
                is_active INTEGER DEFAULT 1,
                created_at INTEGER DEFAULT 0,
                updated_at INTEGER DEFAULT 0
            )
        """)

        # Cards table with person_uid link
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cards (
                card_number TEXT PRIMARY KEY,
                permission_id INTEGER NOT NULL,
                facility_code INTEGER DEFAULT 0,
                holder_name TEXT DEFAULT '',
                person_uid TEXT DEFAULT '',
                activation_date INTEGER DEFAULT 0,
                expiration_date INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1,
                is_blocked INTEGER DEFAULT 0,
                use_limit INTEGER DEFAULT 0,
                use_count INTEGER DEFAULT 0,
                pin TEXT DEFAULT '',
                created_at INTEGER DEFAULT 0,
                updated_at INTEGER DEFAULT 0,
                FOREIGN KEY (person_uid) REFERENCES persons(person_uid)
            )
        """)

        # Access levels (permissions)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS access_levels (
                permission_id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT DEFAULT '',
                doors TEXT DEFAULT '[]',
                timezones TEXT DEFAULT '[]',
                is_active INTEGER DEFAULT 1,
                created_at INTEGER DEFAULT 0,
                updated_at INTEGER DEFAULT 0
            )
        """)

        # Doors with device_uid for Ambient.ai
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS doors (
                door_id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                device_uid TEXT NOT NULL,
                device_type TEXT DEFAULT 'Reader',
                panel_id INTEGER DEFAULT 1,
                reader_id INTEGER DEFAULT 0,
                relay_id INTEGER DEFAULT 0,
                strike_time_ms INTEGER DEFAULT 3000,
                held_open_time_s INTEGER DEFAULT 30,
                rex_enabled INTEGER DEFAULT 1,
                osdp_enabled INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1,
                created_at INTEGER DEFAULT 0,
                updated_at INTEGER DEFAULT 0
            )
        """)

        # Alarm definitions for Ambient.ai
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alarm_definitions (
                alarm_uid TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                event_type INTEGER NOT NULL,
                description TEXT DEFAULT '',
                is_active INTEGER DEFAULT 1,
                created_at INTEGER DEFAULT 0,
                updated_at INTEGER DEFAULT 0
            )
        """)

        # Timezones
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS timezones (
                timezone_id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                intervals TEXT DEFAULT '[]',
                is_active INTEGER DEFAULT 1
            )
        """)

        # Events with full Ambient.ai support
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS events (
                event_id TEXT PRIMARY KEY,
                event_type INTEGER NOT NULL,
                timestamp INTEGER NOT NULL,
                card_number TEXT DEFAULT '',
                door_id INTEGER DEFAULT 0,
                reader_id INTEGER DEFAULT 0,
                decision INTEGER DEFAULT 0,
                deny_reason INTEGER DEFAULT 0,
                details TEXT DEFAULT '',
                device_uid TEXT DEFAULT '',
                device_name TEXT DEFAULT '',
                device_type TEXT DEFAULT 'Reader',
                alarm_uid TEXT DEFAULT '',
                alarm_name TEXT DEFAULT '',
                person_uid TEXT DEFAULT '',
                person_first_name TEXT DEFAULT '',
                person_last_name TEXT DEFAULT '',
                access_item_key TEXT DEFAULT '',
                exported INTEGER DEFAULT 0,
                export_timestamp INTEGER DEFAULT 0,
                acknowledged INTEGER DEFAULT 0
            )
        """)

        # Export queue for Ambient.ai
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS export_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id TEXT NOT NULL,
                payload TEXT NOT NULL,
                created_at INTEGER NOT NULL,
                attempts INTEGER DEFAULT 0,
                last_attempt INTEGER DEFAULT 0,
                status TEXT DEFAULT 'pending',
                error_message TEXT DEFAULT '',
                FOREIGN KEY (event_id) REFERENCES events(event_id)
            )
        """)

        # Holidays
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS holidays (
                holiday_id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                date TEXT NOT NULL,
                recurring INTEGER DEFAULT 0
            )
        """)

        # Create indexes for performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_exported ON events(exported)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_event_type ON events(event_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_cards_person ON cards(person_uid)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_export_queue_status ON export_queue(status)")

        self._conn.commit()

    def _seed_alarm_definitions(self):
        """Seed standard alarm definitions for Ambient.ai"""
        cursor = self._conn.cursor()
        now = int(time.time())

        for event_type, alarm_def in AMBIENT_ALARM_DEFINITIONS.items():
            cursor.execute("""
                INSERT OR IGNORE INTO alarm_definitions (alarm_uid, name, event_type, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
            """, (alarm_def["uid"], alarm_def["name"], int(event_type), now, now))

        self._conn.commit()

    # -------------------------------------------------------------------------
    # Person Operations (for Ambient.ai)
    # -------------------------------------------------------------------------

    def add_person(self, first_name: str, last_name: str, **kwargs) -> Optional[str]:
        """Add a person and return their UUID"""
        try:
            now = int(time.time())
            person_uid = kwargs.get('person_uid') or str(uuid.uuid4())

            cursor = self._conn.cursor()
            cursor.execute("""
                INSERT INTO persons (
                    person_uid, first_name, last_name, email, department,
                    employee_id, is_active, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                person_uid,
                first_name,
                last_name,
                kwargs.get('email', ''),
                kwargs.get('department', ''),
                kwargs.get('employee_id', ''),
                1 if kwargs.get('is_active', True) else 0,
                now,
                now
            ))
            self._conn.commit()
            return person_uid
        except sqlite3.IntegrityError:
            logger.warning(f"Person with UID already exists")
            return None
        except Exception as e:
            logger.error(f"Failed to add person: {e}")
            return None

    def get_person(self, person_uid: str) -> Optional[Dict]:
        """Get a person by UUID"""
        cursor = self._conn.cursor()
        cursor.execute("SELECT * FROM persons WHERE person_uid = ?", (person_uid,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_all_persons(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """Get all persons"""
        cursor = self._conn.cursor()
        cursor.execute(
            "SELECT * FROM persons ORDER BY last_name, first_name LIMIT ? OFFSET ?",
            (limit, offset)
        )
        return [dict(row) for row in cursor.fetchall()]

    def update_person(self, person_uid: str, **kwargs) -> bool:
        """Update a person"""
        try:
            updates = []
            values = []
            for key, value in kwargs.items():
                if key in ['first_name', 'last_name', 'email', 'department',
                          'employee_id', 'is_active']:
                    updates.append(f"{key} = ?")
                    values.append(value)

            if not updates:
                return False

            updates.append("updated_at = ?")
            values.append(int(time.time()))
            values.append(person_uid)

            cursor = self._conn.cursor()
            cursor.execute(
                f"UPDATE persons SET {', '.join(updates)} WHERE person_uid = ?",
                values
            )
            self._conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Failed to update person: {e}")
            return False

    # -------------------------------------------------------------------------
    # Card Operations
    # -------------------------------------------------------------------------

    def add_card(self, card_number: str, permission_id: int, **kwargs) -> bool:
        """Add a card to the database"""
        try:
            now = int(time.time())

            # If holder_name provided but no person_uid, create a person
            person_uid = kwargs.get('person_uid', '')
            if not person_uid and kwargs.get('holder_name'):
                names = kwargs['holder_name'].split(' ', 1)
                first_name = names[0]
                last_name = names[1] if len(names) > 1 else ''
                person_uid = self.add_person(first_name, last_name) or ''

            cursor = self._conn.cursor()
            cursor.execute("""
                INSERT INTO cards (
                    card_number, permission_id, facility_code, holder_name,
                    person_uid, activation_date, expiration_date, is_active, is_blocked,
                    use_limit, use_count, pin, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                card_number,
                permission_id,
                kwargs.get('facility_code', 0),
                kwargs.get('holder_name', ''),
                person_uid,
                kwargs.get('activation_date', 0),
                kwargs.get('expiration_date', 0),
                1 if kwargs.get('is_active', True) else 0,
                1 if kwargs.get('is_blocked', False) else 0,
                kwargs.get('use_limit', 0),
                kwargs.get('use_count', 0),
                kwargs.get('pin', ''),
                now,
                now
            ))
            self._conn.commit()
            return True
        except sqlite3.IntegrityError:
            logger.warning(f"Card {card_number} already exists")
            return False
        except Exception as e:
            logger.error(f"Failed to add card: {e}")
            return False

    def get_card(self, card_number: str) -> Optional[Dict]:
        """Get a card from the database"""
        cursor = self._conn.cursor()
        cursor.execute("SELECT * FROM cards WHERE card_number = ?", (card_number,))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None

    def get_card_with_person(self, card_number: str) -> Optional[Dict]:
        """Get a card with person details for Ambient.ai events"""
        cursor = self._conn.cursor()
        cursor.execute("""
            SELECT c.*, p.first_name, p.last_name, p.email
            FROM cards c
            LEFT JOIN persons p ON c.person_uid = p.person_uid
            WHERE c.card_number = ?
        """, (card_number,))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None

    def get_all_cards(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """Get all cards from the database"""
        cursor = self._conn.cursor()
        cursor.execute(
            "SELECT * FROM cards ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (limit, offset)
        )
        return [dict(row) for row in cursor.fetchall()]

    def update_card(self, card_number: str, **kwargs) -> bool:
        """Update a card in the database"""
        try:
            updates = []
            values = []
            for key, value in kwargs.items():
                if key in ['permission_id', 'facility_code', 'holder_name', 'person_uid',
                          'activation_date', 'expiration_date', 'is_active',
                          'is_blocked', 'use_limit', 'pin']:
                    updates.append(f"{key} = ?")
                    values.append(value)

            if not updates:
                return False

            updates.append("updated_at = ?")
            values.append(int(time.time()))
            values.append(card_number)

            cursor = self._conn.cursor()
            cursor.execute(
                f"UPDATE cards SET {', '.join(updates)} WHERE card_number = ?",
                values
            )
            self._conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Failed to update card: {e}")
            return False

    def delete_card(self, card_number: str) -> bool:
        """Delete a card from the database"""
        try:
            cursor = self._conn.cursor()
            cursor.execute("DELETE FROM cards WHERE card_number = ?", (card_number,))
            self._conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Failed to delete card: {e}")
            return False

    def count_cards(self) -> int:
        """Count total cards"""
        cursor = self._conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM cards")
        return cursor.fetchone()[0]

    # -------------------------------------------------------------------------
    # Access Level Operations
    # -------------------------------------------------------------------------

    def add_access_level(self, permission_id: int, name: str, **kwargs) -> bool:
        """Add an access level"""
        try:
            now = int(time.time())
            cursor = self._conn.cursor()
            cursor.execute("""
                INSERT INTO access_levels (permission_id, name, description, doors, timezones, is_active, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                permission_id,
                name,
                kwargs.get('description', ''),
                json.dumps(kwargs.get('doors', [])),
                json.dumps(kwargs.get('timezones', [])),
                1 if kwargs.get('is_active', True) else 0,
                now,
                now
            ))
            self._conn.commit()
            return True
        except sqlite3.IntegrityError:
            logger.warning(f"Access level {permission_id} already exists")
            return False
        except Exception as e:
            logger.error(f"Failed to add access level: {e}")
            return False

    def get_access_level(self, permission_id: int) -> Optional[Dict]:
        """Get an access level"""
        cursor = self._conn.cursor()
        cursor.execute("SELECT * FROM access_levels WHERE permission_id = ?", (permission_id,))
        row = cursor.fetchone()
        if row:
            result = dict(row)
            result['doors'] = json.loads(result.get('doors', '[]'))
            result['timezones'] = json.loads(result.get('timezones', '[]'))
            return result
        return None

    def get_all_access_levels(self) -> List[Dict]:
        """Get all access levels"""
        cursor = self._conn.cursor()
        cursor.execute("SELECT * FROM access_levels ORDER BY permission_id")
        results = []
        for row in cursor.fetchall():
            result = dict(row)
            result['doors'] = json.loads(result.get('doors', '[]'))
            result['timezones'] = json.loads(result.get('timezones', '[]'))
            results.append(result)
        return results

    def delete_access_level(self, permission_id: int) -> bool:
        """Delete an access level"""
        try:
            cursor = self._conn.cursor()
            cursor.execute("DELETE FROM access_levels WHERE permission_id = ?", (permission_id,))
            self._conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Failed to delete access level: {e}")
            return False

    # -------------------------------------------------------------------------
    # Door Operations
    # -------------------------------------------------------------------------

    def add_door(self, door_id: int, name: str, **kwargs) -> bool:
        """Add a door with Ambient.ai UUID"""
        try:
            now = int(time.time())
            device_uid = kwargs.get('device_uid') or str(uuid.uuid4())

            cursor = self._conn.cursor()
            cursor.execute("""
                INSERT INTO doors (
                    door_id, name, device_uid, device_type, panel_id,
                    reader_id, relay_id, strike_time_ms, held_open_time_s,
                    rex_enabled, osdp_enabled, is_active, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                door_id,
                name,
                device_uid,
                kwargs.get('device_type', 'Reader'),
                kwargs.get('panel_id', 1),
                kwargs.get('reader_id', door_id),
                kwargs.get('relay_id', door_id),
                kwargs.get('strike_time_ms', 3000),
                kwargs.get('held_open_time_s', 30),
                1 if kwargs.get('rex_enabled', True) else 0,
                1 if kwargs.get('osdp_enabled', False) else 0,
                1 if kwargs.get('is_active', True) else 0,
                now,
                now
            ))
            self._conn.commit()
            return True
        except sqlite3.IntegrityError:
            logger.warning(f"Door {door_id} already exists")
            return False
        except Exception as e:
            logger.error(f"Failed to add door: {e}")
            return False

    def get_door(self, door_id: int) -> Optional[Dict]:
        """Get a door"""
        cursor = self._conn.cursor()
        cursor.execute("SELECT * FROM doors WHERE door_id = ?", (door_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_all_doors(self) -> List[Dict]:
        """Get all doors"""
        cursor = self._conn.cursor()
        cursor.execute("SELECT * FROM doors ORDER BY door_id")
        return [dict(row) for row in cursor.fetchall()]

    def update_door(self, door_id: int, **kwargs) -> bool:
        """Update a door"""
        try:
            updates = []
            values = []
            for key, value in kwargs.items():
                if key in ['name', 'device_type', 'panel_id', 'reader_id', 'relay_id',
                          'strike_time_ms', 'held_open_time_s', 'rex_enabled',
                          'osdp_enabled', 'is_active']:
                    updates.append(f"{key} = ?")
                    values.append(value)

            if not updates:
                return False

            updates.append("updated_at = ?")
            values.append(int(time.time()))
            values.append(door_id)

            cursor = self._conn.cursor()
            cursor.execute(
                f"UPDATE doors SET {', '.join(updates)} WHERE door_id = ?",
                values
            )
            self._conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Failed to update door: {e}")
            return False

    def delete_door(self, door_id: int) -> bool:
        """Delete a door"""
        try:
            cursor = self._conn.cursor()
            cursor.execute("DELETE FROM doors WHERE door_id = ?", (door_id,))
            self._conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Failed to delete door: {e}")
            return False

    # -------------------------------------------------------------------------
    # Alarm Definition Operations
    # -------------------------------------------------------------------------

    def get_alarm_definition(self, event_type: int) -> Optional[Dict]:
        """Get alarm definition by event type"""
        cursor = self._conn.cursor()
        cursor.execute("SELECT * FROM alarm_definitions WHERE event_type = ?", (event_type,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_all_alarm_definitions(self) -> List[Dict]:
        """Get all alarm definitions"""
        cursor = self._conn.cursor()
        cursor.execute("SELECT * FROM alarm_definitions ORDER BY event_type")
        return [dict(row) for row in cursor.fetchall()]

    # -------------------------------------------------------------------------
    # Access Decision
    # -------------------------------------------------------------------------

    def check_access(self, card_number: str, door_id: int) -> Dict:
        """Check if a card has access to a door"""
        card = self.get_card_with_person(card_number)
        door = self.get_door(door_id)

        result = {
            "granted": False,
            "reason": "",
            "decision": AccessDecision.DENY,
            "deny_reason": None,
            "event_type": EventType.ACCESS_DENY,
            "card": card,
            "door": door
        }

        # Card not found
        if not card:
            result["reason"] = "Card not found"
            result["deny_reason"] = DenyReason.CARD_NOT_FOUND
            result["event_type"] = EventType.INVALID_BADGE
            return result

        # Door not found
        if not door:
            result["reason"] = "Door not found"
            result["deny_reason"] = DenyReason.DOOR_NOT_FOUND
            return result

        # Card blocked
        if card.get('is_blocked'):
            result["reason"] = "Card blocked"
            result["deny_reason"] = DenyReason.CARD_BLOCKED
            return result

        # Card inactive
        if not card.get('is_active'):
            result["reason"] = "Card inactive"
            result["deny_reason"] = DenyReason.CARD_BLOCKED
            return result

        # Check expiration
        now = int(time.time())
        if card.get('expiration_date', 0) > 0 and card['expiration_date'] < now:
            result["reason"] = "Card expired"
            result["deny_reason"] = DenyReason.EXPIRED
            result["event_type"] = EventType.EXPIRED_BADGE
            return result

        # Check activation
        if card.get('activation_date', 0) > 0 and card['activation_date'] > now:
            result["reason"] = "Card not yet active"
            result["deny_reason"] = DenyReason.NOT_YET_ACTIVE
            return result

        # Get access level
        access_level = self.get_access_level(card['permission_id'])
        if not access_level:
            result["reason"] = "No access level assigned"
            result["deny_reason"] = DenyReason.NO_PERMISSION
            return result

        # Check if door is in access level
        allowed_doors = access_level.get('doors', [])
        if door_id not in allowed_doors:
            result["reason"] = f"Door {door_id} not in access level"
            result["deny_reason"] = DenyReason.NO_PERMISSION
            return result

        # TODO: Add timezone checking

        # Access granted!
        result["granted"] = True
        result["reason"] = "Access granted"
        result["decision"] = AccessDecision.GRANT
        result["deny_reason"] = None
        result["event_type"] = EventType.ACCESS_GRANT
        result["strike_time_ms"] = door.get('strike_time_ms', 3000)
        result["relay_id"] = door.get('relay_id', door_id)

        return result

    # -------------------------------------------------------------------------
    # Event Operations with Ambient.ai Support
    # -------------------------------------------------------------------------

    def add_event(self, event_type: int, **kwargs) -> str:
        """
        Add an event with full Ambient.ai support.
        Returns the event UUID.
        """
        try:
            now = int(time.time())
            event_id = str(uuid.uuid4())

            # Get alarm definition
            alarm_def = self.get_alarm_definition(event_type)
            alarm_uid = alarm_def['alarm_uid'] if alarm_def else ""
            alarm_name = alarm_def['name'] if alarm_def else f"Event Type {event_type}"

            # Get door info
            door_id = kwargs.get('door_id', 0)
            door = self.get_door(door_id) if door_id else None
            device_uid = door['device_uid'] if door else ""
            device_name = door['name'] if door else kwargs.get('device_name', '')
            device_type = door['device_type'] if door else kwargs.get('device_type', 'Reader')

            # Get card/person info
            card_number = kwargs.get('card_number', '')
            person_uid = ""
            person_first_name = ""
            person_last_name = ""

            if card_number:
                card = self.get_card_with_person(card_number)
                if card:
                    person_uid = card.get('person_uid', '')
                    person_first_name = card.get('first_name', '')
                    person_last_name = card.get('last_name', '')

            cursor = self._conn.cursor()
            cursor.execute("""
                INSERT INTO events (
                    event_id, event_type, timestamp, card_number, door_id,
                    reader_id, decision, deny_reason, details,
                    device_uid, device_name, device_type,
                    alarm_uid, alarm_name,
                    person_uid, person_first_name, person_last_name,
                    access_item_key, exported
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
            """, (
                event_id,
                event_type,
                now,
                card_number,
                door_id,
                kwargs.get('reader_id', door_id),
                kwargs.get('decision', 0),
                kwargs.get('deny_reason', 0),
                kwargs.get('details', ''),
                device_uid,
                device_name,
                device_type,
                alarm_uid,
                alarm_name,
                person_uid,
                person_first_name,
                person_last_name,
                card_number  # accessItemKey is the card number
            ))
            self._conn.commit()

            # Queue for Ambient.ai export
            self._queue_event_for_export(event_id)

            return event_id
        except Exception as e:
            logger.error(f"Failed to add event: {e}")
            return ""

    def _queue_event_for_export(self, event_id: str):
        """Queue an event for Ambient.ai export"""
        try:
            event = self.get_event(event_id)
            if not event:
                return

            payload = self.format_ambient_event(event)

            cursor = self._conn.cursor()
            cursor.execute("""
                INSERT INTO export_queue (event_id, payload, created_at, status)
                VALUES (?, ?, ?, 'pending')
            """, (event_id, json.dumps(payload), int(time.time())))
            self._conn.commit()
        except Exception as e:
            logger.error(f"Failed to queue event for export: {e}")

    def format_ambient_event(self, event: Dict) -> Dict:
        """Format an event for Ambient.ai API"""
        return {
            "sourceSystemUid": self._source_system_uid,
            "deviceUid": event.get('device_uid', ''),
            "deviceName": event.get('device_name', ''),
            "deviceType": event.get('device_type', 'Reader'),
            "eventUid": event.get('event_id', ''),
            "alarmName": event.get('alarm_name', ''),
            "alarmUid": event.get('alarm_uid', ''),
            "eventOccuredAtTimestamp": event.get('timestamp', 0),
            "eventPublishedAtTimestamp": int(time.time()),
            "personUid": event.get('person_uid', '') or None,
            "personFirstName": event.get('person_first_name', '') or None,
            "personLastName": event.get('person_last_name', '') or None,
            "accessItemKey": event.get('access_item_key', '') or None
        }

    def get_event(self, event_id: str) -> Optional[Dict]:
        """Get an event by ID"""
        cursor = self._conn.cursor()
        cursor.execute("SELECT * FROM events WHERE event_id = ?", (event_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_events(self, limit: int = 100, offset: int = 0, **filters) -> List[Dict]:
        """Get events with optional filters"""
        query = "SELECT * FROM events WHERE 1=1"
        params = []

        if 'event_type' in filters:
            query += " AND event_type = ?"
            params.append(filters['event_type'])

        if 'door_id' in filters:
            query += " AND door_id = ?"
            params.append(filters['door_id'])

        if 'card_number' in filters:
            query += " AND card_number = ?"
            params.append(filters['card_number'])

        if 'exported' in filters:
            query += " AND exported = ?"
            params.append(1 if filters['exported'] else 0)

        if 'since' in filters:
            query += " AND timestamp >= ?"
            params.append(filters['since'])

        query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cursor = self._conn.cursor()
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

    def get_unexported_events(self, limit: int = 100) -> List[Dict]:
        """Get events that haven't been exported to Ambient.ai"""
        cursor = self._conn.cursor()
        cursor.execute("""
            SELECT * FROM events
            WHERE exported = 0
            ORDER BY timestamp ASC
            LIMIT ?
        """, (limit,))
        return [dict(row) for row in cursor.fetchall()]

    def mark_events_exported(self, event_ids: List[str]) -> bool:
        """Mark events as exported"""
        try:
            now = int(time.time())
            cursor = self._conn.cursor()
            placeholders = ','.join(['?' for _ in event_ids])
            cursor.execute(f"""
                UPDATE events
                SET exported = 1, export_timestamp = ?
                WHERE event_id IN ({placeholders})
            """, [now] + event_ids)
            self._conn.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to mark events as exported: {e}")
            return False

    def get_pending_exports(self, limit: int = 100) -> List[Dict]:
        """Get pending export queue items"""
        cursor = self._conn.cursor()
        cursor.execute("""
            SELECT * FROM export_queue
            WHERE status = 'pending'
            ORDER BY created_at ASC
            LIMIT ?
        """, (limit,))
        return [dict(row) for row in cursor.fetchall()]

    def update_export_status(self, export_id: int, status: str, error_message: str = "") -> bool:
        """Update export queue item status"""
        try:
            cursor = self._conn.cursor()
            cursor.execute("""
                UPDATE export_queue
                SET status = ?, error_message = ?, last_attempt = ?, attempts = attempts + 1
                WHERE id = ?
            """, (status, error_message, int(time.time()), export_id))
            self._conn.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to update export status: {e}")
            return False

    def count_events(self) -> int:
        """Count total events"""
        cursor = self._conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM events")
        return cursor.fetchone()[0]

    def count_unexported_events(self) -> int:
        """Count unexported events"""
        cursor = self._conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM events WHERE exported = 0")
        return cursor.fetchone()[0]

    # -------------------------------------------------------------------------
    # Entity Sync for Ambient.ai Initial Full Sync
    # -------------------------------------------------------------------------

    def get_all_devices_for_sync(self) -> List[Dict]:
        """Get all devices formatted for Ambient.ai sync"""
        doors = self.get_all_doors()
        devices = []

        for door in doors:
            devices.append({
                "sourceSystemUid": self._source_system_uid,
                "uid": door['device_uid'],
                "name": door['name'],
                "type": door.get('device_type', 'Reader'),
                "lastChangedTimestamp": door.get('updated_at', 0),
                "operation": "Create"
            })

        return devices

    def get_all_persons_for_sync(self) -> List[Dict]:
        """Get all persons formatted for Ambient.ai sync"""
        persons = self.get_all_persons(limit=10000)
        result = []

        for person in persons:
            result.append({
                "sourceSystemUid": self._source_system_uid,
                "uid": person['person_uid'],
                "first_name": person['first_name'],
                "last_name": person['last_name'],
                "lastChangedTimestamp": person.get('updated_at', 0),
                "operation": "Create"
            })

        return result

    def get_all_access_items_for_sync(self) -> List[Dict]:
        """Get all access items (cards) formatted for Ambient.ai sync"""
        cards = self.get_all_cards(limit=100000)
        result = []

        for card in cards:
            result.append({
                "sourceSystemUid": self._source_system_uid,
                "uid": str(uuid.uuid5(uuid.NAMESPACE_DNS, card['card_number'])),
                "personUid": card.get('person_uid', ''),
                "key": card['card_number'],
                "lastChangedTimestamp": card.get('updated_at', 0),
                "operation": "Create"
            })

        return result

    def get_all_alarms_for_sync(self) -> List[Dict]:
        """Get all alarm definitions formatted for Ambient.ai sync"""
        alarms = self.get_all_alarm_definitions()
        result = []

        for alarm in alarms:
            result.append({
                "sourceSystemUid": self._source_system_uid,
                "uid": alarm['alarm_uid'],
                "name": alarm['name'],
                "lastChangedTimestamp": alarm.get('updated_at', 0),
                "operation": "Create"
            })

        return result

    # -------------------------------------------------------------------------
    # Health & Statistics
    # -------------------------------------------------------------------------

    def get_health(self) -> Dict:
        """Get HAL health status"""
        return {
            "status": "healthy" if self._initialized else "not_initialized",
            "version": "2.0.0",
            "mode": "simulation",
            "database": {
                "connected": self._conn is not None,
                "path": self.db_path
            },
            "source_system_uid": self._source_system_uid,
            "uptime_seconds": 0
        }

    def get_stats(self) -> Dict:
        """Get HAL statistics"""
        return {
            "cards": {
                "total": self.count_cards(),
                "active": self._count_active_cards()
            },
            "events": {
                "total": self.count_events(),
                "pending": self.count_unexported_events()
            },
            "doors": {
                "total": len(self.get_all_doors())
            },
            "access_levels": {
                "total": len(self.get_all_access_levels())
            },
            "persons": {
                "total": len(self.get_all_persons(limit=100000))
            }
        }

    def _count_active_cards(self) -> int:
        """Count active cards"""
        cursor = self._conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM cards WHERE is_active = 1")
        return cursor.fetchone()[0]

    def get_diagnostics(self) -> Dict:
        """Get HAL diagnostics"""
        return {
            "database": {
                "path": self.db_path,
                "size_bytes": os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0
            },
            "source_system_uid": self._source_system_uid,
            "tables": self._get_table_counts()
        }

    def _get_table_counts(self) -> Dict:
        """Get row counts for all tables"""
        tables = ['cards', 'persons', 'doors', 'access_levels', 'events', 'alarm_definitions', 'export_queue']
        counts = {}

        cursor = self._conn.cursor()
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                counts[table] = cursor.fetchone()[0]
            except:
                counts[table] = 0

        return counts

    def get_source_system_uid(self) -> str:
        """Get the source system UID for Ambient.ai"""
        return self._source_system_uid

    def get_export_queue_status(self, status: str = None, limit: int = 100) -> Dict:
        """
        Get export queue status and items

        Args:
            status: Filter by status (pending, processing, completed, failed, retry)
            limit: Maximum items to return

        Returns:
            Dictionary with queue statistics and items
        """
        cursor = self._conn.cursor()

        # Get counts by status
        cursor.execute("""
            SELECT status, COUNT(*) as count
            FROM export_queue
            GROUP BY status
        """)
        status_counts = {row[0]: row[1] for row in cursor.fetchall()}

        # Get items
        if status:
            cursor.execute("""
                SELECT id, event_id, payload, created_at, attempts, last_attempt, status, error_message
                FROM export_queue
                WHERE status = ?
                ORDER BY created_at DESC
                LIMIT ?
            """, (status, limit))
        else:
            cursor.execute("""
                SELECT id, event_id, payload, created_at, attempts, last_attempt, status, error_message
                FROM export_queue
                ORDER BY created_at DESC
                LIMIT ?
            """, (limit,))

        items = []
        for row in cursor.fetchall():
            items.append({
                "id": row[0],
                "event_id": row[1],
                "payload": json.loads(row[2]) if row[2] else {},
                "created_at": row[3],
                "attempts": row[4],
                "last_attempt": row[5],
                "status": row[6],
                "error_message": row[7]
            })

        return {
            "total": sum(status_counts.values()),
            "by_status": status_counts,
            "items": items,
            "limit": limit
        }


# =============================================================================
# Main HAL Class
# =============================================================================

class HAL:
    """
    Main HAL class that wraps either C library or simulation.
    This is the primary interface for the API server.
    """

    def __init__(self, db_path: str = "hal_database.db", source_system_uid: str = None):
        self._c_bindings = HALCBindings()
        self._simulation = HALSimulation(db_path, source_system_uid)
        self._use_c_library = self._c_bindings.is_available
        self._initialized = False

    def init(self) -> bool:
        """Initialize HAL"""
        if self._use_c_library:
            # TODO: Initialize C library
            logger.info("Using HAL C library")
            self._initialized = True
        else:
            logger.info("Using HAL simulation mode")
            self._initialized = self._simulation.init()

        return self._initialized

    def shutdown(self):
        """Shutdown HAL"""
        if not self._use_c_library:
            self._simulation.shutdown()
        self._initialized = False

    @property
    def source_system_uid(self) -> str:
        """Get the source system UUID for Ambient.ai"""
        return self._simulation.source_system_uid

    # Delegate all methods to simulation for now
    # TODO: Add C library implementations

    def add_person(self, first_name: str, last_name: str, **kwargs) -> Optional[str]:
        return self._simulation.add_person(first_name, last_name, **kwargs)

    def get_person(self, person_uid: str) -> Optional[Dict]:
        return self._simulation.get_person(person_uid)

    def get_all_persons(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        return self._simulation.get_all_persons(limit, offset)

    def update_person(self, person_uid: str, **kwargs) -> bool:
        return self._simulation.update_person(person_uid, **kwargs)

    def add_card(self, card_number: str, permission_id: int, **kwargs) -> bool:
        return self._simulation.add_card(card_number, permission_id, **kwargs)

    def get_card(self, card_number: str) -> Optional[Dict]:
        return self._simulation.get_card(card_number)

    def get_card_with_person(self, card_number: str) -> Optional[Dict]:
        return self._simulation.get_card_with_person(card_number)

    def get_all_cards(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        return self._simulation.get_all_cards(limit, offset)

    def update_card(self, card_number: str, **kwargs) -> bool:
        return self._simulation.update_card(card_number, **kwargs)

    def delete_card(self, card_number: str) -> bool:
        return self._simulation.delete_card(card_number)

    def add_access_level(self, permission_id: int, name: str, **kwargs) -> bool:
        return self._simulation.add_access_level(permission_id, name, **kwargs)

    def get_access_level(self, permission_id: int) -> Optional[Dict]:
        return self._simulation.get_access_level(permission_id)

    def get_all_access_levels(self) -> List[Dict]:
        return self._simulation.get_all_access_levels()

    def delete_access_level(self, permission_id: int) -> bool:
        return self._simulation.delete_access_level(permission_id)

    def add_door(self, door_id: int, name: str, **kwargs) -> bool:
        return self._simulation.add_door(door_id, name, **kwargs)

    def get_door(self, door_id: int) -> Optional[Dict]:
        return self._simulation.get_door(door_id)

    def get_all_doors(self) -> List[Dict]:
        return self._simulation.get_all_doors()

    def update_door(self, door_id: int, **kwargs) -> bool:
        return self._simulation.update_door(door_id, **kwargs)

    def delete_door(self, door_id: int) -> bool:
        return self._simulation.delete_door(door_id)

    def get_alarm_definition(self, event_type: int) -> Optional[Dict]:
        return self._simulation.get_alarm_definition(event_type)

    def get_all_alarm_definitions(self) -> List[Dict]:
        return self._simulation.get_all_alarm_definitions()

    def check_access(self, card_number: str, door_id: int) -> Dict:
        return self._simulation.check_access(card_number, door_id)

    def add_event(self, event_type: int, **kwargs) -> str:
        return self._simulation.add_event(event_type, **kwargs)

    def get_event(self, event_id: str) -> Optional[Dict]:
        return self._simulation.get_event(event_id)

    def get_events(self, limit: int = 100, offset: int = 0, **filters) -> List[Dict]:
        return self._simulation.get_events(limit, offset, **filters)

    def get_unexported_events(self, limit: int = 100) -> List[Dict]:
        return self._simulation.get_unexported_events(limit)

    def mark_events_exported(self, event_ids: List[str]) -> bool:
        return self._simulation.mark_events_exported(event_ids)

    def format_ambient_event(self, event: Dict) -> Dict:
        return self._simulation.format_ambient_event(event)

    def get_pending_exports(self, limit: int = 100) -> List[Dict]:
        return self._simulation.get_pending_exports(limit)

    def update_export_status(self, export_id: int, status: str, error_message: str = "") -> bool:
        return self._simulation.update_export_status(export_id, status, error_message)

    # Entity sync for Ambient.ai
    def get_all_devices_for_sync(self) -> List[Dict]:
        return self._simulation.get_all_devices_for_sync()

    def get_all_persons_for_sync(self) -> List[Dict]:
        return self._simulation.get_all_persons_for_sync()

    def get_all_access_items_for_sync(self) -> List[Dict]:
        return self._simulation.get_all_access_items_for_sync()

    def get_all_alarms_for_sync(self) -> List[Dict]:
        return self._simulation.get_all_alarms_for_sync()

    def get_source_system_uid(self) -> str:
        return self._simulation.get_source_system_uid()

    def get_export_queue_status(self, status: str = None, limit: int = 100) -> Dict:
        return self._simulation.get_export_queue_status(status, limit)

    def get_health(self) -> Dict:
        return self._simulation.get_health()

    def get_stats(self) -> Dict:
        return self._simulation.get_stats()

    def get_diagnostics(self) -> Dict:
        return self._simulation.get_diagnostics()


# =============================================================================
# Export Helper
# =============================================================================

if __name__ == "__main__":
    # Test the HAL bindings
    logging.basicConfig(level=logging.INFO)

    hal = HAL("test_hal.db")
    hal.init()

    print(f"Source System UID: {hal.source_system_uid}")
    print(f"Health: {hal.get_health()}")

    # Add test person
    person_uid = hal.add_person("John", "Doe", email="john@example.com")
    print(f"Added person: {person_uid}")

    # Add test door
    hal.add_door(1, "Main Entrance")
    print(f"Doors: {hal.get_all_doors()}")

    # Add test access level
    hal.add_access_level(1, "Full Access", doors=[1])

    # Add test card
    hal.add_card("12345678", 1, holder_name="John Doe", person_uid=person_uid)

    # Check access
    result = hal.check_access("12345678", 1)
    print(f"Access check: {result}")

    # Add event
    event_id = hal.add_event(
        EventType.ACCESS_GRANT,
        card_number="12345678",
        door_id=1
    )
    print(f"Event ID: {event_id}")

    # Get Ambient.ai formatted event
    event = hal.get_event(event_id)
    ambient_event = hal.format_ambient_event(event)
    print(f"Ambient.ai event: {json.dumps(ambient_event, indent=2)}")

    # Get alarm definitions
    print(f"Alarm definitions: {hal.get_all_alarm_definitions()}")

    # Stats
    print(f"Stats: {hal.get_stats()}")

    hal.shutdown()
