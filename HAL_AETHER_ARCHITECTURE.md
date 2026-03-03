# HAL + Aether Access Architecture
## Separation of Concerns - Panel Brain vs Management Interface
## v2.0 - Complete Implementation

---

## Core Philosophy

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           THE SEPARATION                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   HAL (Hardware Abstraction Layer)                                          │
│   ═══════════════════════════════                                           │
│   • The "BRAIN" of the panel                                                │
│   • Operates STANDALONE like a Mercury panel                                │
│   • Stores ALL data locally:                                                │
│     - Card database (1M+ cards)                                             │
│     - Access levels & permissions                                           │
│     - Doors, readers, relays configuration                                  │
│     - Timezones & holidays                                                  │
│     - Complete event history                                                │
│   • Makes ALL access decisions locally                                      │
│   • Does NOT require network to function                                    │
│   • Is the SINGLE SOURCE OF TRUTH for this panel                           │
│                                                                             │
│   Aether Access                                                             │
│   ═════════════                                                             │
│   • The "WINDOW" into HAL                                                   │
│   • READS data from HAL, displays in human-readable form                    │
│   • Available on network via browser                                        │
│   • Shows:                                                                  │
│     - Event log & history                                                   │
│     - Configuration changes audit trail                                     │
│     - Current access levels, doors, card holders                            │
│   • Can WRITE changes to HAL (via API)                                      │
│   • Can RECEIVE changes from external PACS (via API)                        │
│   • Provides context and meaning to HAL's data                              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Data Flow

```
                    ┌─────────────────────────────────────────┐
                    │          EXTERNAL PACS                  │
                    │    (Lenel, CCURE, Genetec, etc.)        │
                    └───────────────────┬─────────────────────┘
                                        │
                                        │ API Push (changes to
                                        │ access levels, doors,
                                        │ card holders)
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         AETHER ACCESS                                       │
│                    (Management Interface)                                   │
│                                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   Browser   │  │  API Server │  │  Change     │  │  Audit      │        │
│  │     UI      │  │  (FastAPI)  │  │  Tracker    │  │  Logger     │        │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘        │
│         │                │                │                │               │
│         └────────────────┴────────────────┴────────────────┘               │
│                                   │                                         │
│                                   │ READ data                               │
│                                   │ WRITE changes                           │
│                                   ▼                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                              HAL API                                        │
│                     (HAL's External Interface)                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              HAL CORE                                       │
│                    (The Panel's Brain - STANDALONE)                         │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      LOCAL SQLITE DATABASE                          │   │
│  │                                                                     │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                 │   │
│  │  │    Cards    │  │   Access    │  │    Doors    │                 │   │
│  │  │   1M+ cap   │  │   Levels    │  │  & Readers  │                 │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘                 │   │
│  │                                                                     │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                 │   │
│  │  │  Timezones  │  │  Holidays   │  │   Events    │                 │   │
│  │  │ & Schedules │  │             │  │  (100K+)    │                 │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘                 │   │
│  │                                                                     │   │
│  │  ┌─────────────┐  ┌─────────────┐                                  │   │
│  │  │   Config    │  │   Audit     │                                  │   │
│  │  │  Changes    │  │    Trail    │                                  │   │
│  │  └─────────────┘  └─────────────┘                                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      ACCESS DECISION ENGINE                         │   │
│  │                                                                     │   │
│  │  Card Read → Lookup Card → Check Access Level → Check Timezone     │   │
│  │           → Check Holiday → Evaluate Permission → Grant/Deny        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐             │
│  │  OSDP Readers   │  │  Event Buffer   │  │  Relay Control  │             │
│  │  (Secure Ch.)   │  │   (100K cap)    │  │                 │             │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                    │                               │
                    ▼                               ▼
            ┌───────────────┐               ┌───────────────┐
            │    READERS    │               │    RELAYS     │
            │  (OSDP/Wieg)  │               │   (Strikes)   │
            └───────────────┘               └───────────────┘
```

---

## HAL's Local Database (Single Source of Truth)

HAL maintains ALL access control data locally, just like a Mercury panel:

### Tables

```sql
-- Cards (1M+ capacity)
CREATE TABLE cards (
    id INTEGER PRIMARY KEY,
    card_number TEXT UNIQUE NOT NULL,
    facility_code INTEGER,
    permission_id INTEGER NOT NULL,
    holder_name TEXT,
    pin_hash TEXT,
    activation_date INTEGER DEFAULT 0,
    expiration_date INTEGER DEFAULT 0,
    is_active INTEGER DEFAULT 1,
    apb_status INTEGER DEFAULT 0,
    last_access_time INTEGER,
    last_access_door INTEGER,
    created_at INTEGER,
    updated_at INTEGER
);

-- Access Levels (Permissions)
CREATE TABLE access_levels (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    priority INTEGER DEFAULT 0,
    is_active INTEGER DEFAULT 1,
    created_at INTEGER,
    updated_at INTEGER
);

-- Access Level → Door Assignments
CREATE TABLE access_level_doors (
    id INTEGER PRIMARY KEY,
    access_level_id INTEGER NOT NULL,
    door_id INTEGER NOT NULL,
    timezone_id INTEGER DEFAULT 2,  -- 2 = Always
    entry_allowed INTEGER DEFAULT 1,
    exit_allowed INTEGER DEFAULT 1,
    UNIQUE(access_level_id, door_id)
);

-- Doors/Readers
CREATE TABLE doors (
    id INTEGER PRIMARY KEY,
    door_name TEXT NOT NULL,
    location TEXT,
    reader_address INTEGER,
    reader_mode INTEGER DEFAULT 1,  -- card_only
    reader_flags INTEGER DEFAULT 0,
    strike_relay_id INTEGER,
    strike_time_ms INTEGER DEFAULT 1000,
    held_open_time_ms INTEGER DEFAULT 30000,
    pre_alarm_time_ms INTEGER DEFAULT 15000,
    osdp_enabled INTEGER DEFAULT 0,
    scbk TEXT,
    is_online INTEGER DEFAULT 1,
    last_event_time INTEGER,
    created_at INTEGER,
    updated_at INTEGER
);

-- Timezones
CREATE TABLE timezones (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    is_active INTEGER DEFAULT 1
);

-- Timezone Intervals
CREATE TABLE timezone_intervals (
    id INTEGER PRIMARY KEY,
    timezone_id INTEGER NOT NULL,
    day_of_week INTEGER,  -- 0-6 or bitmask
    start_time INTEGER,   -- seconds from midnight
    end_time INTEGER,
    recurrence_type INTEGER,
    holiday_types INTEGER DEFAULT 0
);

-- Holidays
CREATE TABLE holidays (
    id INTEGER PRIMARY KEY,
    date INTEGER NOT NULL,  -- YYYYMMDD
    name TEXT,
    holiday_type INTEGER DEFAULT 1
);

-- Events (100K+ capacity, circular)
CREATE TABLE events (
    id INTEGER PRIMARY KEY,
    event_id TEXT UNIQUE,
    event_type INTEGER NOT NULL,
    timestamp INTEGER NOT NULL,
    card_number TEXT,
    door_id INTEGER,
    granted INTEGER,
    reason TEXT,
    extra_data TEXT,  -- JSON
    exported INTEGER DEFAULT 0,
    acknowledged INTEGER DEFAULT 0
);

-- Configuration Change Audit Trail
CREATE TABLE config_changes (
    id INTEGER PRIMARY KEY,
    timestamp INTEGER NOT NULL,
    change_type TEXT NOT NULL,  -- 'card', 'access_level', 'door', 'timezone', etc.
    resource_id INTEGER,
    action TEXT NOT NULL,  -- 'create', 'update', 'delete'
    old_value TEXT,  -- JSON
    new_value TEXT,  -- JSON
    source TEXT,  -- 'aether', 'pacs', 'local'
    source_user TEXT
);

-- Relays
CREATE TABLE relays (
    id INTEGER PRIMARY KEY,
    relay_name TEXT,
    pulse_duration_ms INTEGER DEFAULT 1000,
    control_timezone INTEGER,
    flags INTEGER DEFAULT 0,
    current_state INTEGER DEFAULT 0,
    last_activated INTEGER
);
```

---

## Aether Access Role

Aether Access is a **read-mostly** interface that:

### 1. READS from HAL
- Current card database
- Access levels and door assignments
- Door/reader status
- Event history
- Configuration change audit trail
- System health

### 2. DISPLAYS in Human-Readable Form
- Web dashboard with charts and statistics
- Event log with filtering and search
- Card holder management UI
- Access level configuration UI
- Door status and control
- Audit trail viewer

### 3. LOGS Changes
- Tracks all changes made through Aether Access
- Tracks all changes received from external PACS
- Shows WHO changed WHAT, WHEN, from WHERE
- Maintains history of rule changes pushed to HAL

### 4. WRITES to HAL (when authorized)
- Add/update/delete cards
- Create/modify access levels
- Configure doors and readers
- Update timezones and holidays
- All writes go through HAL's API

### 5. RECEIVES from External PACS
- API endpoint for PACS to push updates
- Validates and forwards to HAL
- Logs all received changes

---

## API Structure

### HAL API (Port 8081) - Panel's Native Interface

```
HAL API - Direct access to panel data
══════════════════════════════════════

READ Operations (anyone can read):
  GET /hal/cards                    # List cards
  GET /hal/cards/{number}           # Get card
  GET /hal/access-levels            # List access levels
  GET /hal/access-levels/{id}/doors # Get doors for level
  GET /hal/doors                    # List doors
  GET /hal/doors/{id}/status        # Get door status
  GET /hal/events                   # Get events
  GET /hal/events/stream            # WebSocket event stream
  GET /hal/config-changes           # Audit trail
  GET /hal/health                   # System health

WRITE Operations (authenticated):
  POST   /hal/cards                 # Add card
  PUT    /hal/cards/{number}        # Update card
  DELETE /hal/cards/{number}        # Delete card
  POST   /hal/access-levels         # Create access level
  PUT    /hal/access-levels/{id}    # Update access level
  POST   /hal/doors/{id}/control    # Lock/unlock door
  POST   /hal/sync                  # Full sync from PACS
```

### Aether Access API (Port 8080) - Management Interface

```
Aether Access API - Human interface + PACS integration
═══════════════════════════════════════════════════════

Authentication:
  POST /api/auth/login              # Get JWT
  POST /api/auth/logout
  GET  /api/auth/me

Dashboard:
  GET /api/dashboard/stats          # Overview statistics
  GET /api/dashboard/events/recent  # Recent events
  GET /api/dashboard/health         # System health

Cards (proxies to HAL + adds audit):
  GET    /api/cards                 # List with pagination
  POST   /api/cards                 # Add (logs change)
  PUT    /api/cards/{id}            # Update (logs change)
  DELETE /api/cards/{id}            # Delete (logs change)

Access Levels (proxies to HAL + adds audit):
  GET    /api/access-levels
  POST   /api/access-levels         # Create (logs change)
  PUT    /api/access-levels/{id}    # Update (logs change)
  DELETE /api/access-levels/{id}    # Delete (logs change)

Doors:
  GET  /api/doors
  GET  /api/doors/{id}/events       # Events for this door
  POST /api/doors/{id}/control      # Lock/unlock

Events:
  GET /api/events                   # Paginated event history
  GET /api/events/search            # Search events
  GET /api/events/export            # Export to CSV/JSON

Audit Trail:
  GET /api/audit/changes            # All config changes
  GET /api/audit/changes/{type}     # Filter by type

PACS Integration (for external systems):
  POST /api/pacs/sync/cards         # Bulk card sync
  POST /api/pacs/sync/access-levels # Bulk access level sync
  POST /api/pacs/webhook            # Webhook for real-time updates
```

---

## Change Tracking Flow

When a change is made (from any source):

```
1. Change Request Arrives
   ├─ From Aether Access UI
   ├─ From External PACS API
   └─ From Local CLI

2. Aether Access Logs the Intent
   └─ INSERT INTO aether_change_log (
        source, user, resource_type, action, payload, timestamp
      )

3. Aether Access Forwards to HAL
   └─ POST /hal/[resource] with payload

4. HAL Validates and Applies
   ├─ Validates data
   ├─ Updates local database
   └─ Logs to config_changes table

5. HAL Returns Result
   └─ Success or error

6. Aether Access Updates Log
   └─ UPDATE aether_change_log SET
        result = 'success', hal_timestamp = X

7. Event Broadcast (if applicable)
   └─ WebSocket notification to all clients
```

---

## Example: Card Added from PACS

```
1. PACS sends: POST /api/pacs/sync/cards
   {
     "cards": [
       {"card_number": "12345678", "access_level_id": 5, "holder": "John Doe"}
     ],
     "source": "Lenel OnGuard",
     "transaction_id": "abc123"
   }

2. Aether Access logs:
   INSERT INTO change_log (
     source='pacs:Lenel OnGuard',
     transaction_id='abc123',
     resource='card',
     action='create',
     data='{"card_number":"12345678",...}'
   )

3. Aether Access calls HAL:
   POST /hal/cards
   {"card_number": "12345678", "permission_id": 5, "holder_name": "John Doe"}

4. HAL stores in local database:
   INSERT INTO cards (card_number, permission_id, holder_name, ...)

5. HAL logs config change:
   INSERT INTO config_changes (
     change_type='card',
     action='create',
     new_value='{"card_number":"12345678",...}',
     source='pacs'
   )

6. HAL returns success

7. Aether Access updates log and returns to PACS

8. Next card read for 12345678 is processed by HAL locally
```

---

## Offline Operation

When network is down:

```
HAL continues to:
✓ Process card reads
✓ Make access decisions (all data is local)
✓ Control doors and relays
✓ Log events to local buffer
✓ Maintain OSDP secure channels

Aether Access:
✗ Cannot display (no network access)
✗ Cannot receive PACS updates
✗ Changes queue locally (if running on same hardware)

When network returns:
✓ Aether Access reconnects to HAL
✓ Queued events are available
✓ PACS can resume syncing
```

---

## Summary

| Component | Role | Data Ownership | Network Required |
|-----------|------|----------------|------------------|
| **HAL** | Panel brain | OWNS all data | NO (standalone) |
| **Aether Access** | Management UI | VIEWS HAL data | YES (browser access) |
| **External PACS** | Enterprise system | Syncs TO HAL | YES (API calls) |

The key insight: **HAL is a Mercury-style intelligent panel that happens to have a web interface (Aether Access) and PACS integration capabilities.** It doesn't depend on either to function.

---

## Implementation Files

### HAL Core (Port 8081)
```
api/hal_core_api.py          # HAL Core REST API Server
├── /hal/health              # System health and statistics
├── /hal/cards               # Card database (1M+ capacity)
├── /hal/access-levels       # Access level management
├── /hal/doors               # Door configuration and control
├── /hal/events              # Event buffer (100K+, RAW format)
├── /hal/config-changes      # Audit trail
├── /hal/timezones           # Timezone definitions
├── /hal/holidays            # Holiday calendar
├── /hal/sync                # Bulk sync endpoint for PACS
└── /hal/export              # Full configuration export
```

### Aether Access (Port 8080)
```
gui/backend/api_aether.py    # Aether Access REST API Server
├── /api/auth                # Authentication
├── /api/dashboard           # Dashboard statistics
├── /api/events              # Human-readable event search/export
├── /api/audit               # Config change audit trail
├── /api/cards               # Cardholder management UI
├── /api/access-levels       # Access level management UI
├── /api/doors               # Door management UI
├── /api/pacs/sync           # PACS bulk sync endpoint
├── /api/pacs/webhook        # PACS real-time webhook
├── /api/pacs/events         # Events for PACS consumption
├── /api/timezones           # Timezone viewing
├── /api/holidays            # Holiday viewing
└── /api/system              # System info and export

gui/backend/hal_client.py    # HAL API Client
gui/backend/event_reporting.py  # Event formatting & statistics
```

---

## Data Flow - Bidirectional PACS Integration

```
                    ┌─────────────────────────────────────────┐
                    │          EXTERNAL PACS                  │
                    │    (Lenel, CCURE, Genetec, etc.)        │
                    └───────────────────┬─────────────────────┘
                                        │
                    ┌───────────────────┼───────────────────┐
                    │                   │                   │
                    │ POST /api/pacs/sync                   │ GET /api/pacs/events
                    │ POST /api/pacs/webhook                │ (poll for events)
                    │ (push changes)                        │
                    ▼                                       │
┌─────────────────────────────────────────────────────────────────────────────┐
│                         AETHER ACCESS (Port 8080)                           │
│                    (Management Interface - Local Panel)                     │
│                                                                             │
│  Receives PACS updates ─────────┬─────────────── Provides events to PACS   │
│                                 │                                           │
│         ┌───────────────────────┴───────────────────────┐                  │
│         │           HAL Client (hal_client.py)          │                  │
│         └───────────────────────┬───────────────────────┘                  │
│                                 │                                           │
│  Event Reporting ◄──────────────┴──────────────► Audit Trail              │
│  (human-readable)                                (who changed what)         │
│                                                                             │
│  Browser UI ◄──────────────────────────────────► Card/Access Management   │
└─────────────────────────────────────────────────────────────────────────────┘
                                   │
                                   │ READ/WRITE via REST API
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         HAL CORE (Port 8081)                                │
│                    (The Panel's Brain - STANDALONE)                         │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      LOCAL SQLITE DATABASE                          │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                 │   │
│  │  │    Cards    │  │   Access    │  │    Doors    │                 │   │
│  │  │   1M+ cap   │  │   Levels    │  │  & Readers  │                 │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘                 │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                 │   │
│  │  │   Events    │  │   Config    │  │  Timezones  │                 │   │
│  │  │ 100K+ (RAW) │  │  Changes    │  │ & Holidays  │                 │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ACCESS DECISION ENGINE: Card → Permission → Timezone → Door → Grant/Deny  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Starting the System

```bash
# Start HAL Core (the panel brain)
cd api
python3 hal_core_api.py
# Runs on port 8081

# Start Aether Access (management interface)
cd gui/backend
python3 api_aether.py
# Runs on port 8080

# Access Aether Access UI
open http://localhost:8080
```

---

## Environment Variables

```bash
# HAL Core
HAL_DB_PATH=/path/to/hal_core.db   # SQLite database location
HAL_PORT=8081                       # API port

# Aether Access
AETHER_PORT=8080                    # API port
HAL_CORE_URL=http://localhost:8081  # HAL Core API URL
```
