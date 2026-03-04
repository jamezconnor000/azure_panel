# HAL + Aether Access Architecture

## System Overview

The HAL Azure Panel system consists of three major components running on the Azure BLU-IC2 panel:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          AZURE BLU-IC2 PANEL                                │
│                                                                             │
│   ┌─────────────────────┐    ┌─────────────────────────────────────────┐   │
│   │  AETHER ACCESS      │    │  UNIFIED API SERVER                     │   │
│   │  (React Frontend)   │    │  (FastAPI - Python)                     │   │
│   │                     │───→│                                         │   │
│   │  - Dashboard        │    │  /api/v1/  - I/O Control API            │   │
│   │  - Card Management  │    │  /api/v2.1/ - Auth, Users, Doors        │   │
│   │  - Event Viewer     │    │  /api/v2.2/ - HAL Integration           │   │
│   │  - Door Control     │    │  /ws/live  - WebSocket                  │   │
│   │                     │←───│                                         │   │
│   └─────────────────────┘    └─────────────────┬───────────────────────┘   │
│                                                │                            │
│                                                ↓                            │
│                              ┌─────────────────────────────────────────┐   │
│                              │  HAL CORE                               │   │
│                              │  (C Library + Python Bindings)          │   │
│                              │                                         │   │
│                              │  ┌──────────────────────────────────┐   │   │
│                              │  │  HAL Public Interface (hal.h)   │   │   │
│                              │  ├────┬──────┬──────┬──────────────┤   │   │
│                              │  │Event│Card  │Access│SDK          │   │   │
│                              │  │Mgr  │DB    │Logic │Wrapper      │   │   │
│                              │  ├────┴──────┴──────┴──────────────┤   │   │
│                              │  │  Azure Access SDK               │   │   │
│                              │  └──────────────────────────────────┘   │   │
│                              └─────────────────┬───────────────────────┘   │
│                                                │                            │
│                                                ↓                            │
│                              ┌─────────────────────────────────────────┐   │
│                              │  HARDWARE                               │   │
│                              │  - OSDP Readers                         │   │
│                              │  - Relays / Outputs                     │   │
│                              │  - Inputs (REX, Door Contacts)          │   │
│                              │  - RS-485 Bus                           │   │
│                              └─────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Components

### 1. Aether Access (Frontend)
The React-based web interface that users interact with via browser.

**Purpose:** Human-readable management interface
**Technology:** React + TypeScript + Vite
**Location:** `gui/frontend/`

**Features:**
- Dashboard with system health and recent events
- Card holder management
- Door configuration and control
- Access level assignment
- Event search and reporting
- Real-time WebSocket updates

### 2. Unified API Server
Single FastAPI server that provides ALL API endpoints for both the frontend and HAL integration.

**Purpose:** Central API gateway
**Technology:** FastAPI + Python
**Location:** `api/` and `gui/backend/`
**Port:** 8080

**API Versions:**
| Version | Prefix | Purpose |
|---------|--------|---------|
| v1 | `/api/v1/` | Frontend I/O control (panels, readers, doors, outputs) |
| v2.1 | `/api/v2.1/` | Auth, Users, Doors, Access Levels |
| v2.2 | `/api/v2.2/` | HAL Integration (OSDP, Cards, Diagnostics) |

### 3. HAL Core (C Library)
The low-level hardware abstraction layer implemented in C with Python bindings.

**Purpose:** Hardware control and access decisions
**Technology:** C + Python (ctypes/cffi bindings)
**Location:** `src/hal_core/`, `python/`

**Features:**
- Card database (SQLite)
- Access decision engine
- Event buffer (100K capacity)
- OSDP/Wiegand protocol handlers
- Timezone validation
- Hardware I/O control

## Key Files

| File | Purpose |
|------|---------|
| `api/unified_api_server.py` | Main unified API server |
| `api/hal_core_api.py` | HAL-specific endpoints (can be used standalone) |
| `gui/backend/api_v2_1.py` | Auth, Users, Doors, Access Levels |
| `gui/backend/api_v2_2.py` | HAL integration (OSDP, Cards, Diagnostics) |
| `gui/frontend/` | React frontend (Aether Access) |
| `src/hal_core/` | HAL C library source |
| `python/hal_bindings.py` | Python bindings for HAL C library |

## Startup

```bash
# Start the unified API (serves frontend + HAL API)
python api/unified_api_server.py

# Or with uvicorn for development
uvicorn api.unified_api_server:app --host 0.0.0.0 --port 8080 --reload
```

## HAL C Library Structure

```
┌──────────────────────────┐
│  Application             │
├──────────────────────────┤
│  HAL Public Interface    │ (hal_public.h)
├────┬──────┬──────┬───────┤
│Event│Card  │Access│SDK    │
│Mgr  │DB    │Logic │Wrapper│
├────┴──────┴──────┴───────┤
│  Azure Access SDK        │
├──────────────────────────┤
│  BLU-IC2 Controller      │
└──────────────────────────┘
```

## HAL Core Components

### Event Manager
- Manages event buffer (100K capacity)
- Handles subscriptions
- Guaranteed delivery with ACK
- Recovery on disconnect

### Card Database
- SQLite local storage
- Complex queries with AND/OR
- 1M+ card capacity
- Dynamic field updates

### Access Logic
- Permission checking
- Schedule validation
- APB tracking
- Multiple card format support

### SDK Wrapper
- Azure SDK integration
- Command serialization
- Event marshalling

## Event Flow

```
Card Presented at Reader
        ↓
Card Validated Against Local DB
        ↓
Access Decision Made (Grant/Deny)
        ↓
Physical Action (Strike, LED, Buzzer)
        ↓
Event Generated (AccessGrantEvent or AccessDenyEvent)
        ↓
Event Buffered in 100K Buffer
        ↓
Subscribers Notified (with Backpressure)
        ↓
Subscribers Acknowledge Receipt
        ↓
Event Can Be Pruned from Buffer
```

## Threading Model

- Single-threaded by default
- Event queue is thread-safe
- Card database uses SQLite locking
- Application responsible for multi-threaded usage

## Performance

- Access Decision: <250ms
- Event Generation: <1ms
- Event Buffer: 100,000 capacity
- Database: Up to 1,000,000 cards
- Query Performance: <100ms for complex logic

## Data Flow

```
HAL Application
    │
    ├─→ Add Cards to Database
    │
    ├─→ Subscribe to Events
    │
    └─→ Loop:
         ├─ Receive Event (Card Presented)
         ├─ Decide Access (Query DB + Rules)
         ├─ Execute Action (Energize Relay)
         ├─ Generate Event
         └─ Send Acknowledgement
```
