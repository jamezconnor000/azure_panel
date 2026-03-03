# Azure Panel - Complete Architecture & Integration Plan

**Version:** 1.0.0
**Date:** March 2026
**Status:** Production Architecture

---

## Executive Summary

The Azure Panel is a comprehensive access control platform built for Azure BLU-IC2 Controllers. It consists of multiple interconnected applications that work together to provide enterprise-grade physical access control with cloud integration capabilities.

---

## Repository Structure

```
azure_panel (GitHub: jamezconnor000/azure_panel)
│
├── main                    # Integration branch - all components merged
│
├── hal-core               # HAL C Library (Hardware Abstraction Layer)
│   └── Core access control engine, OSDP, card database
│
├── python-backend         # Shared Python Services
│   └── FastAPI REST API, database layer, shared utilities
│
├── aether-access          # Aether Access GUI Application
│   └── React frontend + API extensions for GUI
│
└── ambient-integration    # Ambient.ai Cloud Integration
    └── Event forwarding, cloud connectivity, PoC tools
```

---

## Application Domains

### 1. HAL CORE (hal-core branch)
**Language:** C
**Purpose:** Hardware Abstraction Layer - the foundation of the system

```
src/
├── hal_core/              # Core HAL implementation
│   ├── hal.c/h            # Main interface
│   ├── event_manager.c/h  # 100K event buffer
│   ├── event_database.c/h # SQLite persistence
│   ├── card_database.c/h  # 1M+ card capacity
│   ├── access_logic.c/h   # Access decisions
│   ├── osdp_reader.c/h    # OSDP protocol
│   └── osdp_secure_channel.c/h  # AES-128 encryption
│
├── sdk_modules/           # Advanced features
│   ├── permissions/       # Permission rules
│   ├── timezones/         # Schedule management
│   ├── holidays/          # Holiday handling
│   ├── readers/           # Reader config
│   ├── relays/            # Relay control
│   └── events/            # Event structures
│
├── utils/                 # Shared utilities
│   ├── cJSON.c/h          # JSON parsing
│   ├── logging.c          # Unified logging
│   └── queue.c            # Event queue
│
└── include/               # Public headers
    ├── hal_public.h       # Public API
    └── hal_types.h        # Type definitions
```

**Key Features:**
- Event-driven architecture
- OSDP Secure Channel (AES-128)
- Wiegand/DESFire support
- SQLite card database (1M+ capacity)
- 100K event buffer
- Offline operation capability

**Build Output:**
- `libhal_core.a` - Static library
- `libsdk_wrapper.a` - SDK interface
- `libhal_utils.a` - Utilities

---

### 2. PYTHON BACKEND (python-backend branch)
**Language:** Python 3.8+
**Framework:** FastAPI
**Purpose:** Shared REST API and service layer

```
api/
├── hal_api_server.py      # Main REST API server
└── requirements.txt       # Dependencies

python/
├── __init__.py            # Package init
├── hal_interface.py       # HAL C library bindings
├── card_provisioning.py   # Card management
├── event_monitor.py       # Event subscription
└── utils.py               # Utilities

services/
├── database.py            # Shared database layer
├── auth.py                # JWT authentication
├── config.py              # Configuration management
└── event_service.py       # Event processing service
```

**Key Features:**
- FastAPI REST server (port 8080)
- WebSocket real-time events
- JWT authentication
- SQLite database operations
- Python bindings to HAL C library
- Shared service layer for all Python apps

**Dependencies:**
```
fastapi>=0.100.0
uvicorn>=0.23.0
pydantic>=2.0.0
python-jose>=3.3.0
bcrypt>=4.0.0
aiosqlite>=0.19.0
httpx>=0.24.0
```

---

### 3. AETHER ACCESS (aether-access branch)
**Technology:** React 18 + TypeScript + Tailwind CSS
**Purpose:** Enterprise GUI application

```
gui/
├── backend/
│   ├── aetheraccess_gui_server_v2.py  # Extended API server
│   ├── api_v2_1.py                     # v2.1 endpoints
│   ├── io_monitoring.py                # I/O status
│   ├── io_control.py                   # I/O control
│   └── database.py                     # GUI-specific DB
│
├── frontend/
│   └── src/
│       ├── App.tsx                     # Main app
│       ├── api/                        # API clients
│       ├── pages/                      # 8 pages
│       │   ├── Login.tsx
│       │   ├── Dashboard.tsx
│       │   ├── DoorManagement.tsx
│       │   ├── UserManagement.tsx
│       │   ├── AccessLevels.tsx
│       │   ├── CardHolders.tsx
│       │   ├── HardwareTree.tsx
│       │   └── IOControl.tsx
│       ├── components/                 # Shared components
│       ├── contexts/                   # React contexts
│       └── types/                      # TypeScript types
│
└── examples/                           # Client examples
```

**Key Features:**
- 56 REST API endpoints
- Real-time WebSocket updates
- Role-based access control (4 roles)
- OSDP Secure Channel toggle via GUI
- Hardware tree visualization
- User/Card holder management
- Comprehensive audit logging

---

### 4. AMBIENT INTEGRATION (ambient-integration branch)
**Language:** C + Python
**Purpose:** Ambient.ai cloud connectivity

```
poc/
├── app1_hal_engine/       # HAL Access Engine daemon
│   ├── hal_engine.c/h     # Main daemon
│   ├── wiegand_handler.c/h
│   ├── card_database.c/h
│   ├── access_logic.c/h
│   ├── event_producer.c/h
│   └── ipc_publisher.c/h  # Unix socket IPC
│
├── app2_ambient_forwarder/ # Event forwarder daemon
│   ├── forwarder.c/h      # Main daemon
│   ├── ipc_subscriber.c/h
│   ├── ambient_client.c/h # HTTP POST to cloud
│   ├── retry_queue.c/h    # Failed event queue
│   └── uuid_registry.c/h
│
├── shared/                # Shared components
│   ├── event_types.h
│   ├── json_serializer.c/h
│   └── uuid_utils.c/h
│
└── tools/                 # Developer tools
    ├── simulate_badge.c
    ├── monitor_events.c
    ├── test_ambient.c
    ├── hal_logs.c
    └── hal_status.c

integration/
├── ambient_forwarder.py   # Python forwarder (alternative)
├── event_transform.py     # Event format conversion
└── config/
    └── ambient_config.json
```

**Key Features:**
- IPC event bus (Unix sockets)
- HTTP POST to Ambient.ai Generic Cloud API
- Retry queue for failed events
- UUID registry for deduplication
- Real-time event forwarding
- Developer/debug tools

---

## System Architecture

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                           AZURE PANEL SYSTEM                                 │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                    AETHER ACCESS GUI (React)                            ││
│  │                    Port 3000 (dev) / Static build                       ││
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐           ││
│  │  │Dashboard│ │  Doors  │ │  Users  │ │ Access  │ │Hardware │           ││
│  │  │         │ │   Mgmt  │ │   Mgmt  │ │ Levels  │ │  Tree   │           ││
│  │  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘           ││
│  └───────┼──────────┼──────────┼──────────┼──────────┼───────────────────┘│
│          │          │          │          │          │                     │
│          └──────────┴──────────┴──────────┴──────────┘                     │
│                                 │                                           │
│                                 ▼ HTTP/WebSocket                            │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                    PYTHON BACKEND (FastAPI)                             ││
│  │                    Port 8080                                            ││
│  │                                                                         ││
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                  ││
│  │  │  REST API    │  │  WebSocket   │  │  Auth/JWT    │                  ││
│  │  │  v1 + v2.1   │  │  Real-time   │  │  Sessions    │                  ││
│  │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘                  ││
│  │         │                 │                 │                           ││
│  │  ┌──────┴─────────────────┴─────────────────┴──────┐                   ││
│  │  │              Database Layer (SQLite)            │                   ││
│  │  │  Users | Sessions | Doors | Access Levels | Audit                   ││
│  │  └──────────────────────┬──────────────────────────┘                   ││
│  └─────────────────────────┼───────────────────────────────────────────────┘│
│                            │                                                │
│                            │ CFFI/Native Calls                              │
│                            ▼                                                │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                    HAL CORE (C Library)                                 ││
│  │                                                                         ││
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐        ││
│  │  │   Event    │  │   Card     │  │  Access    │  │   OSDP     │        ││
│  │  │  Manager   │  │ Database   │  │   Logic    │  │  Secure    │        ││
│  │  │  (100K)    │  │  (1M+)     │  │            │  │  Channel   │        ││
│  │  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘        ││
│  │        │               │               │               │                ││
│  │  ┌─────┴───────────────┴───────────────┴───────────────┴─────┐         ││
│  │  │                   SDK Modules                              │         ││
│  │  │  Permissions | TimeZones | Holidays | Readers | Relays     │         ││
│  │  └────────────────────────┬───────────────────────────────────┘         ││
│  └───────────────────────────┼─────────────────────────────────────────────┘│
│                              │                                              │
│         ┌────────────────────┼────────────────────┐                         │
│         │                    │                    │                         │
│         ▼                    ▼                    ▼                         │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────────────┐           │
│  │   OSDP      │     │  SQLite DB  │     │  AMBIENT INTEGRATION│           │
│  │  Readers    │     │  (Local)    │     │                     │           │
│  │             │     │             │     │  IPC ──► Forwarder  │           │
│  │  Wiegand    │     │  Cards      │     │           │         │           │
│  │  DESFire    │     │  Events     │     │           ▼         │           │
│  │             │     │  Config     │     │      Ambient.ai     │           │
│  └─────────────┘     └─────────────┘     │      Cloud API      │           │
│                                          └─────────────────────┘           │
│                                                                             │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## Integration Points

### HAL Core ↔ Python Backend
```
Method: CFFI / ctypes / Native bindings
Interface: hal_public.h exports
Data Flow:
  - Python calls HAL_Initialize(), HAL_ProcessCard(), etc.
  - HAL returns AccessLogicResult_t structures
  - Events pushed via callbacks or polling
```

### Python Backend ↔ Aether Access
```
Method: HTTP REST API + WebSocket
Interface: /api/v1/* and /api/v2.1/* endpoints
Data Flow:
  - Frontend fetches data via REST
  - Real-time updates via WebSocket
  - Auth via JWT tokens
```

### HAL Core ↔ Ambient Integration
```
Method: Unix Domain Sockets (IPC)
Interface: Event producer/subscriber pattern
Data Flow:
  - HAL publishes events to IPC bus
  - Forwarder subscribes and forwards to cloud
  - Retry queue for failed deliveries
```

### Python Backend ↔ Ambient Integration
```
Method: Shared event service
Interface: Event transformation layer
Data Flow:
  - Python can also forward events
  - Alternative to C forwarder
  - Uses same Ambient.ai API
```

---

## Branch Strategy

### Development Workflow
```
feature/* ───────┬──► hal-core
                 │
feature/* ───────┼──► python-backend
                 │
feature/* ───────┼──► aether-access
                 │
feature/* ───────┼──► ambient-integration
                 │
                 └───────────────────────────► main (integration)
```

### Branch Descriptions

| Branch | Purpose | Primary Language |
|--------|---------|------------------|
| `main` | Integration branch - stable releases | Mixed |
| `hal-core` | HAL C library development | C |
| `python-backend` | Shared Python services | Python |
| `aether-access` | GUI application | TypeScript/React |
| `ambient-integration` | Cloud integration | C/Python |

### Merge Strategy
1. Feature branches merge into respective domain branches
2. Domain branches are tested independently
3. Domain branches merge into `main` for integration testing
4. Releases tagged from `main`

---

## Deployment Configurations

### Development
```yaml
services:
  hal-core:
    build: ./
    volumes:
      - ./config:/app/config
      - ./data:/app/data

  python-api:
    build: ./api
    ports:
      - "8080:8080"
    depends_on:
      - hal-core

  frontend:
    build: ./gui/frontend
    ports:
      - "3000:3000"
    depends_on:
      - python-api

  ambient-forwarder:
    build: ./poc/app2_ambient_forwarder
    depends_on:
      - hal-core
```

### Production
```yaml
# Single container with all components
hal-azure-panel:
  image: azure-panel:latest
  ports:
    - "8080:8080"
  environment:
    - HAL_CONFIG=/config/hal_config.json
    - AMBIENT_ENABLED=true
    - AMBIENT_API_KEY=${AMBIENT_API_KEY}
  volumes:
    - /data/hal:/app/data
    - /config/hal:/app/config
```

---

## API Summary

### HAL Core (C API)
```c
// Initialization
ErrorCode_t HAL_Initialize(HAL_RuntimeConfig_t* config);
void HAL_Shutdown(void);

// Access Control
AccessLogicResult_t HAL_ProcessCardRead(uint32_t card, uint8_t door);
ErrorCode_t HAL_SetReaderMode(LPA_t reader, ReaderMode_t mode);

// Events
ErrorCode_t HAL_SubscribeEvents(EventCallback callback);
AccessEvent_t* HAL_GetNextEvent(void);

// Card Database
ErrorCode_t HAL_AddCard(uint32_t card_number, uint32_t permissions);
ErrorCode_t HAL_RemoveCard(uint32_t card_number);
```

### Python Backend REST API
```
GET  /api/v1/panels/{id}/io          Panel I/O status
GET  /api/v1/readers/{id}/health     Reader health
POST /api/v1/doors/{id}/unlock       Unlock door
POST /api/v2.1/auth/login            User login
GET  /api/v2.1/users                 List users
GET  /api/v2.1/doors                 List doors
GET  /api/v2.1/access-levels         List access levels
WS   /ws/live                        Real-time events
```

### Ambient.ai Integration
```
POST https://api.ambient.ai/v1/events
Content-Type: application/json

{
  "event_type": "access_granted",
  "timestamp": "2026-03-03T10:30:00Z",
  "card_number": "12345678",
  "door_id": 1,
  "door_name": "Front Door",
  "granted": true
}
```

---

## Build Instructions

### HAL Core
```bash
cd Source
mkdir build && cd build
cmake ..
make
# Output: libhal_core.a, test executables
```

### Python Backend
```bash
cd Source/api
pip install -r requirements.txt
python3 hal_api_server.py
```

### Aether Access Frontend
```bash
cd Source/gui/frontend
npm install
npm run dev      # Development
npm run build    # Production
```

### Ambient Integration
```bash
cd Source/poc
make all
./app1_hal_engine &
./app2_ambient_forwarder &
```

---

## Testing Strategy

| Component | Test Type | Location |
|-----------|-----------|----------|
| HAL Core | Unit + Integration | `tests/test_*.c` |
| Python Backend | API tests | `tests/test_api.py` |
| Aether Access | E2E + Component | `gui/frontend/tests/` |
| Ambient Integration | Integration | `poc/tools/test_ambient.c` |

---

## Configuration Files

| File | Purpose |
|------|---------|
| `config/hal_config.json` | HAL system configuration |
| `config/ambient_config.json` | Ambient.ai API settings |
| `gui/frontend/.env` | Frontend environment |
| `.env` | Shared environment variables |

---

## Security Considerations

1. **OSDP Secure Channel:** AES-128 encryption for reader communication
2. **JWT Authentication:** Token-based auth with session management
3. **Role-Based Access:** Admin, Operator, Guard, User roles
4. **Audit Logging:** All actions logged with timestamps
5. **API Security:** CORS, rate limiting, input validation
6. **Database:** SQLite with parameterized queries

---

## Next Steps

1. [ ] Create and push all domain branches
2. [ ] Set up CI/CD for each branch
3. [ ] Create integration tests for cross-component communication
4. [ ] Document deployment procedures for each environment
5. [ ] Set up branch protection rules on GitHub

---

*Azure Panel Architecture v1.0.0 - March 2026*
