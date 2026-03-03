# Azure Panel - Complete Project Plan
## HAL + Aether Access + Ambient.ai Integration
## Version 2.0 | February 2026

---

## Executive Summary

The Azure Panel project provides a complete physical access control solution built on the Azure BLU-IC2 controller platform. The system consists of three primary components:

1. **HAL Core** - The standalone panel brain (like Mercury panels)
2. **Aether Access** - Local management interface and PACS integration point
3. **Ambient.ai Forwarder** - Real-time event streaming to Ambient.ai cloud

---

## System Architecture

```
                        ┌─────────────────────────────────────┐
                        │         EXTERNAL SYSTEMS            │
                        ├─────────────────┬───────────────────┤
                        │  Enterprise PACS │   Ambient.ai     │
                        │ (Lenel, CCURE,  │   Cloud Portal   │
                        │  Genetec, etc.) │                   │
                        └────────┬────────┴─────────┬─────────┘
                                 │                  ▲
                    Push changes │                  │ Live events
                    via REST API │                  │ via REST API
                                 ▼                  │
┌────────────────────────────────────────────────────────────────────────────┐
│                         AZURE PANEL (On-Premise)                           │
│                                                                            │
│  ┌──────────────────────────────────────────────────────────────────────┐ │
│  │                    AETHER ACCESS (Port 8080)                         │ │
│  │              Local Management Interface + PACS Gateway               │ │
│  │                                                                      │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌────────────┐ │ │
│  │  │  Dashboard  │  │   Event     │  │    Card     │  │    PACS    │ │ │
│  │  │     UI      │  │  Reporting  │  │ Management  │  │ Integration│ │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └────────────┘ │ │
│  └──────────────────────────────────────────────────────────────────────┘ │
│                                   │                                        │
│                          Reads/Writes via REST                             │
│                                   ▼                                        │
│  ┌──────────────────────────────────────────────────────────────────────┐ │
│  │                      HAL CORE (Port 8081)                            │ │
│  │              The Panel Brain - STANDALONE Operation                  │ │
│  │                                                                      │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                  │ │
│  │  │   Cards     │  │   Access    │  │   Events    │                  │ │
│  │  │  (1M+ cap)  │  │   Levels    │  │ (100K RAW)  │                  │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘                  │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                  │ │
│  │  │   Doors     │  │  Timezones  │  │   Audit     │                  │ │
│  │  │  Readers    │  │  Holidays   │  │   Trail     │                  │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘                  │ │
│  │                                                                      │ │
│  │           ACCESS DECISION ENGINE (local, offline-capable)            │ │
│  └──────────────────────────────────────────────────────────────────────┘ │
│                                   │                                        │
│                        Polls live events                                   │
│                                   ▼                                        │
│  ┌──────────────────────────────────────────────────────────────────────┐ │
│  │                 AMBIENT.AI FORWARDER (Daemon)                        │ │
│  │           Streams Live Events to Ambient.ai Cloud                    │ │
│  │                                                                      │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                  │ │
│  │  │   Event     │  │   Retry     │  │   Health    │                  │ │
│  │  │   Poller    │  │   Queue     │  │   Monitor   │                  │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘                  │ │
│  └──────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│  ┌──────────────────────────────────────────────────────────────────────┐ │
│  │                      HARDWARE LAYER                                  │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                  │ │
│  │  │    OSDP     │  │   Wiegand   │  │   Relays    │                  │ │
│  │  │   Readers   │  │   Readers   │  │  (Strikes)  │                  │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘                  │ │
│  │                                                                      │ │
│  │                    Azure BLU-IC2 Controller                          │ │
│  └──────────────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## Component Details

### 1. HAL Core (Port 8081)

**Purpose:** Standalone panel brain that operates like a Mercury panel.

**Key Features:**
- Local SQLite database (all data stored on-panel)
- 1M+ card capacity
- 100K+ event buffer (circular, RAW format)
- Access decision engine (card → permission → timezone → door)
- Complete audit trail of all configuration changes
- Operates without network connectivity
- OSDP Secure Channel support

**API Endpoints:**
```
GET/POST/PUT/DELETE /hal/cards          # Card database
GET/POST/PUT/DELETE /hal/access-levels  # Access level management
GET/POST/PUT/DELETE /hal/doors          # Door configuration
GET                 /hal/events         # Event buffer (RAW)
GET                 /hal/events/stream  # WebSocket real-time
GET                 /hal/config-changes # Audit trail
GET/POST            /hal/timezones      # Timezone definitions
GET/POST/DELETE     /hal/holidays       # Holiday calendar
POST                /hal/sync           # Bulk sync from PACS
GET                 /hal/export         # Full config export
GET                 /hal/health         # System health
```

**Implementation Status:** ✅ Complete (`api/hal_core_api.py`)

---

### 2. Aether Access (Port 8080)

**Purpose:** Local management interface and PACS integration gateway.

**Key Features:**
- Human-readable event reporting with search and export
- Dashboard with real-time statistics
- Cardholder management UI
- Access level configuration with door assignments
- Audit trail viewer (who changed what, when)
- PACS integration endpoints (bidirectional)
- CSV/JSON export capabilities

**API Endpoints:**
```
# Authentication
POST /api/auth/login
GET  /api/auth/me

# Dashboard
GET  /api/dashboard/stats
GET  /api/dashboard/health

# Events (human-readable)
GET  /api/events                # Search with filtering
GET  /api/events/statistics     # Statistical analysis
GET  /api/events/export/csv     # CSV export
GET  /api/events/export/json    # JSON export

# Audit Trail
GET  /api/audit/changes         # Config change history

# Card Management (UI)
GET/POST/PUT/DELETE /api/cards

# Access Levels (UI)
GET/POST/PUT/DELETE /api/access-levels

# Doors (UI)
GET  /api/doors
POST /api/doors/{id}/control

# PACS Integration
POST /api/pacs/sync             # Bulk sync from PACS
POST /api/pacs/webhook          # Real-time webhook
GET  /api/pacs/events           # Events for PACS consumption

# System
GET  /api/system/info
GET  /api/system/export
```

**Implementation Status:** ✅ Complete (`gui/backend/api_aether.py`)

---

### 3. Ambient.ai Forwarder (Daemon)

**Purpose:** Stream live access events to Ambient.ai cloud for video AI integration.

**Key Features:**
- Polls HAL for new events (or uses WebSocket)
- Transforms events to Ambient.ai format
- Forwards to Ambient.ai REST API endpoint
- Retry queue for failed deliveries
- Marks events as exported in HAL
- Health monitoring and logging
- Configurable destination (cloud portal or local Docker)

**Event Types to Forward:**
- `ACCESS_GRANTED` - Card swipe, access allowed
- `ACCESS_DENIED` - Card swipe, access denied
- `DOOR_FORCED` - Door forced open (alarm)
- `DOOR_HELD` - Door held open too long
- `DOOR_OPENED` - Door opened normally
- `DOOR_CLOSED` - Door closed
- `READER_TAMPER` - Reader tamper detected

**Data Flow:**
```
HAL Event Buffer ──→ Ambient Forwarder ──→ Ambient.ai REST API
       │                    │                      │
  (RAW format)        (Transform)           (Ambient format)
       │                    │                      │
       │              Retry Queue             Cloud Portal
       │              (on failure)             or Docker
       │                    │
       └── Mark Exported ───┘
```

**Event Format (to Ambient.ai):**
```json
{
  "event_type": "access_granted",
  "timestamp": "2026-02-10T14:30:25Z",
  "panel_id": "azure-panel-001",
  "door": {
    "id": 1,
    "name": "Main Entrance"
  },
  "credential": {
    "card_number": "12345678",
    "holder_name": "John Doe"
  },
  "decision": "granted",
  "reason": "Valid card, active permission"
}
```

**Configuration:**
```json
{
  "hal_url": "http://localhost:8081",
  "ambient_api_url": "https://api.ambient.ai/v1/events",
  "ambient_api_key": "your-api-key",
  "poll_interval_ms": 500,
  "retry_max_attempts": 5,
  "retry_backoff_ms": 1000,
  "batch_size": 100
}
```

**Implementation Status:** 🔲 Planned

---

## Implementation Roadmap

### Phase 1: Core Infrastructure ✅ Complete
- [x] HAL C Library (event buffer, card DB, access logic)
- [x] SDK Module Integration (permissions, timezones, readers, relays)
- [x] Python Bindings
- [x] Basic REST API Server

### Phase 2: HAL Core API ✅ Complete
- [x] HAL Core REST API (port 8081)
- [x] Local SQLite database with complete schema
- [x] Card management (1M+ capacity)
- [x] Access level management
- [x] Event buffer (100K+, RAW format)
- [x] Audit trail logging
- [x] Bulk sync endpoint for PACS

### Phase 3: Aether Access ✅ Complete
- [x] Aether Access REST API (port 8080)
- [x] HAL Client module
- [x] Event reporting with human-readable formatting
- [x] Event search and statistics
- [x] CSV/JSON export
- [x] PACS integration endpoints
- [x] Dashboard statistics

### Phase 4: Ambient.ai Integration 🔲 Planned
- [ ] Ambient.ai Forwarder daemon
- [ ] Event transformation to Ambient format
- [ ] REST API client for Ambient.ai
- [ ] Retry queue with backoff
- [ ] Event export tracking in HAL
- [ ] Health monitoring
- [ ] Configuration management

### Phase 5: React Frontend 🔲 Planned
- [ ] Dashboard page (statistics, recent events)
- [ ] Event log page (search, filter, export)
- [ ] Cardholder management page
- [ ] Access level configuration page
- [ ] Door status and control page
- [ ] Audit trail viewer
- [ ] System settings page

### Phase 6: Production Hardening 🔲 Planned
- [ ] Authentication with JWT
- [ ] Role-based access control
- [ ] HTTPS/TLS support
- [ ] Rate limiting
- [ ] Logging and monitoring
- [ ] Backup/restore procedures
- [ ] Documentation and deployment guides

---

## File Structure

```
Azure_Panel/Source/
├── api/
│   ├── hal_core_api.py         # HAL Core REST API (port 8081)
│   └── hal_api_server.py       # Legacy API server
│
├── gui/
│   ├── backend/
│   │   ├── api_aether.py       # Aether Access API (port 8080)
│   │   ├── hal_client.py       # HAL API client
│   │   ├── event_reporting.py  # Event formatting & stats
│   │   └── api_v2_2.py         # Extended API endpoints
│   │
│   └── frontend/               # React application
│       └── src/
│
├── ambient/                    # [PLANNED] Ambient.ai integration
│   ├── forwarder.py            # Event forwarder daemon
│   ├── ambient_client.py       # Ambient.ai API client
│   └── config.json             # Forwarder configuration
│
├── src/
│   ├── hal_core/               # HAL C library
│   └── sdk_modules/            # SDK module wrappers
│
├── include/                    # C headers
├── python/                     # Python bindings
├── schema/                     # Database schemas
├── config/                     # Configuration files
├── docs/                       # Documentation
│
├── HAL_AETHER_ARCHITECTURE.md  # Architecture documentation
├── AZURE_PANEL_PROJECT_PLAN.md # This file
│
├── start_aether_system.sh      # Start HAL + Aether
└── stop_aether_system.sh       # Stop HAL + Aether
```

---

## Network Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          BUILDING NETWORK                               │
│                                                                         │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐              │
│  │   Browser   │     │  Enterprise │     │  Ambient.ai │              │
│  │     UI      │     │    PACS     │     │   Server    │              │
│  └──────┬──────┘     └──────┬──────┘     └──────┬──────┘              │
│         │                   │                   │                      │
│         └───────────────────┼───────────────────┘                      │
│                             │                                          │
│                      ┌──────┴──────┐                                   │
│                      │   Switch    │                                   │
│                      └──────┬──────┘                                   │
│                             │                                          │
│  ┌──────────────────────────┴──────────────────────────┐              │
│  │                    AZURE PANEL                       │              │
│  │                                                      │              │
│  │  Port 8080: Aether Access (browser UI, PACS API)    │              │
│  │  Port 8081: HAL Core (internal, panel data)         │              │
│  │                                                      │              │
│  │  Ambient Forwarder ──────────────────────────────────┼──→ Ambient  │
│  │  (outbound REST)                                     │      API    │
│  └──────────────────────────────────────────────────────┘              │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Security Considerations

1. **HAL Core (Port 8081)**
   - Internal only, not exposed to network by default
   - Source tracking headers for audit trail
   - All changes logged

2. **Aether Access (Port 8080)**
   - JWT authentication (planned)
   - Role-based access control (planned)
   - HTTPS/TLS support (planned)
   - Rate limiting (planned)

3. **Ambient.ai Forwarder**
   - API key authentication to Ambient.ai
   - Outbound connections only
   - No inbound API surface

4. **PACS Integration**
   - API key or certificate authentication (planned)
   - Transaction ID tracking
   - Complete audit trail

---

## Summary

| Component | Port | Purpose | Status |
|-----------|------|---------|--------|
| **HAL Core** | 8081 | Panel brain, standalone operation | ✅ Complete |
| **Aether Access** | 8080 | Management UI, PACS gateway | ✅ Complete |
| **Ambient Forwarder** | N/A | Event streaming to Ambient.ai | 🔲 Planned |
| **React Frontend** | (via 8080) | Browser UI | 🔲 Planned |

The Azure Panel provides a complete, modern access control solution that:
- Operates **standalone** like traditional Mercury panels
- Provides a **web-based management interface** (Aether Access)
- Integrates with **enterprise PACS** systems bidirectionally
- Streams **live events to Ambient.ai** for video AI integration
