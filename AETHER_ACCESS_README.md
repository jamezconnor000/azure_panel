# Aether Access - Enterprise Access Control GUI

**Version:** 2.1.0
**Status:** Complete Implementation
**Type:** Full-Stack Web Application (React + FastAPI)

---

## Overview

Aether Access is a complete enterprise-grade access control GUI system built for Azure BLU-IC2 Controllers. It provides a modern web interface for managing physical access control systems, surpassing traditional solutions like Lenel OnGuard and Mercury software.

**Key Features:**
- Real-time door monitoring and control
- User and card holder management
- Role-based access control (RBAC)
- OSDP Secure Channel configuration via GUI toggle
- Hardware tree visualization (panels, readers, I/O)
- WebSocket real-time updates
- JWT authentication with session management
- Comprehensive audit logging

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    AETHER ACCESS GUI                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │              FRONTEND (React + TypeScript)                │ │
│  │  Port: 3000                                               │ │
│  │                                                           │ │
│  │  Pages:                                                   │ │
│  │  ├── Login           (Authentication)                     │ │
│  │  ├── Dashboard       (System Overview)                    │ │
│  │  ├── DoorManagement  (OSDP Toggle, Door Config)           │ │
│  │  ├── UserManagement  (User CRUD + Roles)                  │ │
│  │  ├── AccessLevels    (Permission Groups)                  │ │
│  │  ├── CardHolders     (Badge Management)                   │ │
│  │  ├── HardwareTree    (Panel/Reader/IO Hierarchy)          │ │
│  │  ├── Readers         (Reader Health Monitoring)           │ │
│  │  └── IOControl       (Door/Output/Relay Control)          │ │
│  └───────────────────────────────────────────────────────────┘ │
│                              │                                  │
│                              ▼ HTTP/WebSocket                   │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │              BACKEND (FastAPI + Python)                   │ │
│  │  Port: 8080                                               │ │
│  │                                                           │ │
│  │  API Versions:                                            │ │
│  │  ├── /api/v1/*    (I/O Monitoring, Control, Health)       │ │
│  │  └── /api/v2.1/*  (Auth, Users, Doors, Access Levels)     │ │
│  │                                                           │ │
│  │  Modules:                                                 │ │
│  │  ├── aetheraccess_gui_server_v2.py  (Main Server)         │ │
│  │  ├── api_v2_1.py                     (v2.1 Endpoints)     │ │
│  │  ├── auth.py                         (JWT Auth)           │ │
│  │  ├── database.py                     (SQLite)             │ │
│  │  ├── io_monitoring.py                (I/O Status)         │ │
│  │  └── io_control.py                   (I/O Control)        │ │
│  └───────────────────────────────────────────────────────────┘ │
│                              │                                  │
│                              ▼                                  │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │                    SQLite Database                        │ │
│  │                                                           │ │
│  │  Tables:                                                  │ │
│  │  ├── users              (GUI Users)                       │ │
│  │  ├── sessions           (Active Sessions)                 │ │
│  │  ├── door_configs       (Door Configuration)              │ │
│  │  ├── access_levels      (Permission Groups)               │ │
│  │  ├── access_level_doors (Level-Door Mapping)              │ │
│  │  ├── user_access_levels (User-Level Mapping)              │ │
│  │  ├── card_holders       (Badge Holders)                   │ │
│  │  ├── panels             (Azure Panels)                    │ │
│  │  └── audit_log          (Action History)                  │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Directory Structure

```
gui/
├── QUICK_START.md              # Quick start guide
├── backend/
│   ├── aetheraccess_gui_server_v2.py  # Main FastAPI server
│   ├── api_v2_1.py             # v2.1 API endpoints (56 endpoints)
│   ├── auth.py                 # JWT authentication module
│   ├── database.py             # SQLite database operations
│   ├── io_monitoring.py        # Panel/Reader health monitoring
│   ├── io_control.py           # Door/Output/Relay control
│   ├── hal_gui_server.py       # Legacy server (v1)
│   └── requirements.txt        # Python dependencies
├── frontend/
│   ├── package.json            # Node.js dependencies
│   ├── tailwind.config.js      # Tailwind CSS config
│   ├── vite.config.ts          # Vite build config
│   └── src/
│       ├── App.tsx             # Main app with routes
│       ├── main.tsx            # Entry point
│       ├── App.css             # Global styles
│       ├── api/
│       │   ├── client.ts       # v1 API client
│       │   └── clientV2_1.ts   # v2.1 API client
│       ├── components/
│       │   ├── Layout.tsx      # Main layout
│       │   └── ProtectedRoute.tsx  # Auth guard
│       ├── contexts/
│       │   └── AuthContext.tsx # Authentication state
│       ├── pages/
│       │   ├── Login.tsx       # Login page
│       │   ├── Dashboard.tsx   # System overview
│       │   ├── DoorManagement.tsx  # Door + OSDP config
│       │   ├── UserManagement.tsx  # User CRUD
│       │   ├── AccessLevels.tsx    # Access level management
│       │   ├── CardHolders.tsx     # Card holder management
│       │   ├── HardwareTree.tsx    # Panel hierarchy
│       │   ├── Readers.tsx         # Reader health
│       │   └── IOControl.tsx       # I/O control
│       └── types/
│           └── *.ts            # TypeScript type definitions
└── examples/
    ├── python_client_example.py
    ├── bash_examples.sh
    └── monitoring_dashboard.py
```

---

## API Endpoints (56 Total)

### API v1 (I/O Monitoring & Control)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/panels/{id}/io` | GET | Get panel I/O status |
| `/api/v1/panels/{id}/health` | GET | Get panel health metrics |
| `/api/v1/readers/{id}/health` | GET | Get reader health |
| `/api/v1/readers/health/summary` | GET | Get all readers health |
| `/api/v1/doors/{id}/unlock` | POST | Unlock door |
| `/api/v1/doors/{id}/lock` | POST | Lock door |
| `/api/v1/doors/{id}/lockdown` | POST | Lockdown door |
| `/api/v1/doors/{id}/release` | POST | Release door |
| `/api/v1/outputs/{id}/activate` | POST | Activate output |
| `/api/v1/outputs/{id}/deactivate` | POST | Deactivate output |
| `/api/v1/outputs/{id}/pulse` | POST | Pulse output |
| `/api/v1/outputs/{id}/toggle` | POST | Toggle output |
| `/api/v1/relays/{id}/activate` | POST | Activate relay |
| `/api/v1/relays/{id}/deactivate` | POST | Deactivate relay |
| `/api/v1/control/lockdown` | POST | Emergency lockdown |
| `/api/v1/control/unlock-all` | POST | Emergency unlock |
| `/api/v1/control/normal` | POST | Return to normal |
| `/api/v1/macros` | GET | List macros |
| `/api/v1/macros/{id}/execute` | POST | Execute macro |
| `/api/v1/overrides` | GET | Get active overrides |
| `/api/v1/overrides/{id}` | DELETE | Clear override |
| `/ws/live` | WS | Real-time updates |

### API v2.1 (Authentication, Users, Doors, Access)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v2.1/auth/login` | POST | User login |
| `/api/v2.1/auth/logout` | POST | User logout |
| `/api/v2.1/auth/refresh` | POST | Refresh token |
| `/api/v2.1/auth/me` | GET | Current user |
| `/api/v2.1/users` | GET, POST | List/create users |
| `/api/v2.1/users/{id}` | GET, PUT, DELETE | User CRUD |
| `/api/v2.1/users/{id}/change-password` | POST | Change password |
| `/api/v2.1/users/{id}/access-levels` | GET, POST | User access levels |
| `/api/v2.1/users/{id}/access-levels/{lvl}` | DELETE | Revoke level |
| `/api/v2.1/users/{id}/doors` | GET | User's accessible doors |
| `/api/v2.1/doors` | GET, POST | List/create doors |
| `/api/v2.1/doors/{id}` | GET, PUT, DELETE | Door CRUD |
| `/api/v2.1/doors/{id}/osdp/enable` | POST | Enable OSDP |
| `/api/v2.1/doors/{id}/osdp/disable` | POST | Disable OSDP |
| `/api/v2.1/access-levels` | GET, POST | List/create levels |
| `/api/v2.1/access-levels/{id}` | GET, PUT, DELETE | Level CRUD |
| `/api/v2.1/access-levels/{id}/doors` | GET, POST | Level doors |
| `/api/v2.1/access-levels/{id}/doors/{d}` | DELETE | Remove door |
| `/api/v2.1/card-holders` | GET, POST | List/create holders |
| `/api/v2.1/card-holders/{id}` | GET, PUT, DELETE | Holder CRUD |
| `/api/v2.1/card-holders/{id}/access-levels` | GET | Holder levels |
| `/api/v2.1/card-holders/{id}/access-levels/{l}` | POST, DELETE | Grant/revoke |
| `/api/v2.1/card-holders/{id}/doors` | GET | Holder's doors |
| `/api/v2.1/panels` | GET, POST | List/create panels |
| `/api/v2.1/panels/{id}` | GET, PUT, DELETE | Panel CRUD |
| `/api/v2.1/panels/{id}/downstream` | GET | Downstream panels |
| `/api/v2.1/panels/{id}/readers` | GET, POST | Panel readers |
| `/api/v2.1/panels/{id}/inputs` | GET, POST | Panel inputs |
| `/api/v2.1/panels/{id}/outputs` | GET, POST | Panel outputs |
| `/api/v2.1/panels/{id}/relays` | GET, POST | Panel relays |
| `/api/v2.1/hardware-tree` | GET | Full hierarchy |
| `/api/v2.1/audit-logs` | GET | Audit history |

---

## User Roles & Permissions

| Role | Permissions |
|------|-------------|
| **admin** | Full access to all features |
| **operator** | User/door read, card holder management, door control, reports |
| **guard** | Door read, card holder read, door control, audit read |
| **user** | Door read only |

---

## Key Features

### 1. OSDP Secure Channel Toggle
- Enable/disable OSDP per door via GUI
- Configure SCBK (16-byte hex key)
- Set reader address (0-126)
- Real-time status updates

### 2. Hardware Tree
- Hierarchical view: Master Panel → Downstream Panels → Readers/IO
- RS-485 bus visualization
- Real-time device status

### 3. Access Level Management
- Create permission groups
- Assign doors with timezone restrictions
- Grant to users/card holders
- Immediate propagation

### 4. Real-time Monitoring
- WebSocket-based live updates
- Door state changes
- Reader health alerts
- Emergency control events

### 5. Audit Logging
- All actions logged with timestamp
- User attribution
- IP address tracking
- Searchable history

---

## Quick Start

### Start Backend
```bash
cd gui/backend
pip install -r requirements.txt
python3 aetheraccess_gui_server_v2.py
# API: http://localhost:8080
# Docs: http://localhost:8080/docs
```

### Start Frontend
```bash
cd gui/frontend
npm install
npm run dev
# UI: http://localhost:3000
```

### Default Admin Login
- Username: `admin`
- Password: `admin` (change immediately)

---

## Technology Stack

### Frontend
- **React 18** with TypeScript
- **Vite** for build tooling
- **Tailwind CSS** for styling
- **React Router** for navigation
- **Context API** for state management

### Backend
- **FastAPI** (Python 3.8+)
- **Uvicorn** ASGI server
- **SQLite** database
- **JWT** authentication (python-jose)
- **bcrypt** password hashing
- **Pydantic** data validation
- **WebSocket** real-time updates

---

## Relationship to HAL

**Aether Access GUI** is the user-facing interface that sits on top of the **HAL (Hardware Abstraction Layer)**.

```
┌─────────────────────────────────┐
│       Aether Access GUI         │  ← Web Interface (this project)
│   (React + FastAPI + SQLite)    │
└─────────────────────────────────┘
              │
              ▼ REST API / Library Calls
┌─────────────────────────────────┐
│     HAL - Hardware Abstraction  │  ← C Library (main branch)
│   (Event Engine, Card DB, SDK)  │
└─────────────────────────────────┘
              │
              ▼ OSDP / Wiegand / DESFire
┌─────────────────────────────────┐
│    Azure BLU-IC2 Controllers    │  ← Physical Hardware
└─────────────────────────────────┘
```

- **HAL** (main branch): C library for hardware communication
- **Aether Access** (aether-access branch): Full GUI application

---

## Documentation

See `/Documentation/` for:
- `AetherAccess_2.0_Build_Progress_Complete.md`
- `AetherAccess_2.1_COMPLETE_Implementation_Summary.md`
- `HAL_GUI_COMPLETE_IMPLEMENTATION.md`

---

*Aether Access - Where Access Control Meets Modern UX*
