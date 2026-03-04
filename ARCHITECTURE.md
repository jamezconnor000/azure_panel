# Aether Access 3.0 Architecture
## Physical Access Control System for Azure BLU-IC2 Controllers

```
  ᚨ ᛖ ᚦ ᛖ ᚱ   A C C E S S   3 . 0
  Complete Access Control System
```

---

## System Overview

Aether Access 3.0 is a complete Physical Access Control System (PACS) designed for Azure BLU-IC2 controllers. The system consists of three main applications that work together to provide hardware abstraction, API services, and web management.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         AETHER ACCESS 3.0                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│    ┌─────────────────┐         ┌─────────────────┐                         │
│    │  AETHER SAGA    │         │  AETHER BIFROST │                         │
│    │  (Web UI)       │         │  (API/Export)   │                         │
│    │  Port 80        │         │  Port 8080      │                         │
│    │                 │         │                 │                         │
│    │  PostgreSQL     │         │  SQLite +       │                         │
│    │  (Local)        │         │  PostgreSQL     │                         │
│    │                 │         │  (Central)      │                         │
│    └────────┬────────┘         └────────┬────────┘                         │
│             │                           │                                   │
│             │         ┌─────────────────┤                                   │
│             │         │                 │                                   │
│             │         │     LOOM        │                                   │
│             │         │  (Translation)  │                                   │
│             │         │                 │                                   │
│             │         └────────┬────────┘                                   │
│             │                  │                                            │
│             └──────────────────┼──────────────────────────────────────────┐│
│                                │                                          ││
│                       ┌────────▼────────┐                                 ││
│                       │  AETHER THRALL  │                                 ││
│                       │  (HAL)          │                                 ││
│                       │                 │                                 ││
│                       │  AetherDB       │◄── Source of Truth              ││
│                       │  (Binary)       │                                 ││
│                       │                 │                                 ││
│                       └────────┬────────┘                                 ││
│                                │                                          ││
│                       ┌────────▼────────┐                                 ││
│                       │  Azure BLU-IC2  │                                 ││
│                       │  Controller     │                                 ││
│                       └─────────────────┘                                 ││
│                                                                           ││
└───────────────────────────────────────────────────────────────────────────┘│
```

---

## Components

### 1. Aether Thrall (Hardware Abstraction Layer)

**The Source of Truth**

Aether Thrall is the foundation of the system. It directly interfaces with the Azure BLU-IC2 hardware and maintains the authoritative database of all access control data.

| Attribute | Value |
|-----------|-------|
| App ID | `aether_thrall` |
| Port | Internal only |
| Database | AetherDB (Custom Binary) |
| Role | Hardware control, data authority |

**Responsibilities:**
- Direct hardware communication with BLU-IC2
- Stores ALL access control data (cardholders, access levels, doors, events)
- Provides internal API for Saga and Bifrost
- Manages OSDP/Wiegand/DESFire protocols
- Event buffering (100K+ events)
- Offline operation capability

### 2. Aether Bifrost (API Server / Export Daemon)

**The Bridge to External Systems**

Aether Bifrost provides external API access and manages data synchronization with central systems like Lenel OnGuard.

| Attribute | Value |
|-----------|-------|
| App ID | `aether_bifrost` |
| Port | 8080 |
| Database | SQLite (local cache) + PostgreSQL (central) |
| Role | External API, data export |

**Responsibilities:**
- REST API for external integrations
- Event export to Ambient.ai and other systems
- Synchronization with central Lenel/OnGuard servers
- Local SQLite cache for offline resilience
- PostgreSQL connection to central database

### 3. Aether Saga (Web Management Interface)

**The Local Management Portal**

Aether Saga provides a web-based interface for local panel management and monitoring.

| Attribute | Value |
|-----------|-------|
| App ID | `aether_saga` |
| Port | 80 |
| Database | PostgreSQL (local) |
| Role | Web UI, local management |

**Responsibilities:**
- Web-based dashboard for panel status
- Cardholder management interface
- Access level configuration
- Door/reader management
- Event viewing and search
- System diagnostics and health

---

## Loom - Translation Layer

Loom is the translation mechanism that converts data between AetherDB's binary format and the SQL databases used by Bifrost and Saga.

```
                    LOOM TRANSLATION LAYER
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│   AetherDB (Binary)  ◄──────  LOOM  ──────►  SQL Databases     │
│                                                                 │
│   ┌─────────────┐         ┌─────────────┐    ┌─────────────┐   │
│   │ TLV Codec   │◄───────►│   Schema    │───►│ PostgreSQL  │   │
│   │ Binary R/W  │         │  Registry   │    │  Adapter    │   │
│   └─────────────┘         └─────────────┘    └─────────────┘   │
│                                  │                              │
│                                  ▼           ┌─────────────┐   │
│                           ┌─────────────┐    │   SQLite    │   │
│                           │ Translation │───►│   Adapter   │   │
│                           │   Engine    │    └─────────────┘   │
│                           └─────────────┘                       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Loom Components

1. **Schema Registry** - Defines all data structures with versioning
2. **TLV Codec** - Encodes/decodes Tag-Length-Value binary format
3. **Translation Engine** - Bidirectional conversion logic
4. **PostgreSQL Adapter** - Converts to/from PostgreSQL
5. **SQLite Adapter** - Converts to/from SQLite

### Translation Error Tracking

Both Saga and Bifrost include dedicated pages for monitoring Loom translation status:

- **Translation Health Dashboard** - Real-time sync status
- **Error Log** - Detailed translation failures with root cause
- **Suggested Fixes** - Auto-remediation suggestions
- **Manual Intervention Queue** - Items requiring human review

---

## AetherDB - Custom Binary Database

AetherDB is a custom binary database format optimized for embedded access control systems.

### Design Principles

1. **TLV Format** - Tag-Length-Value encoding for schema resilience
2. **WAL Support** - Write-Ahead Logging for crash recovery
3. **Multi-level Checksums** - Data integrity verification
4. **Self-repair** - Automatic corruption detection and recovery
5. **Health Monitoring** - Continuous diagnostics with alerts
6. **Configurable Limits** - No restructuring when capacity changes

### Data Structures

```
AetherDB File Format
┌─────────────────────────────────────────┐
│ Header (Magic, Version, Checksum)       │
├─────────────────────────────────────────┤
│ Table Directory                         │
├─────────────────────────────────────────┤
│ Table: cardholders                      │
│   ├── Index (badge_number)              │
│   └── Records (TLV encoded)             │
├─────────────────────────────────────────┤
│ Table: access_levels                    │
│   ├── Index (id)                        │
│   └── Records (TLV encoded)             │
├─────────────────────────────────────────┤
│ Table: doors                            │
│   ├── Index (id)                        │
│   └── Records (TLV encoded)             │
├─────────────────────────────────────────┤
│ Table: events                           │
│   ├── Index (timestamp)                 │
│   └── Records (TLV encoded)             │
├─────────────────────────────────────────┤
│ WAL (Write-Ahead Log)                   │
└─────────────────────────────────────────┘
```

### TLV Record Format

```
┌─────────┬─────────┬─────────────────────┐
│ Tag     │ Length  │ Value               │
│ (2 bytes)│(2 bytes)│ (variable)          │
├─────────┼─────────┼─────────────────────┤
│ 0x0001  │ 0x0008  │ <8-byte uint64 id>  │
│ 0x0002  │ 0x000A  │ "JOHN.DOE"          │
│ 0x0007  │ 0x0010  │ [1, 2, 3, 4] levels │
└─────────┴─────────┴─────────────────────┘
```

---

## Data Flow

### Access Request Flow

```
1. Card Presented
   │
   ▼
2. Thrall receives from hardware
   │
   ▼
3. Thrall checks AetherDB for credentials
   │
   ▼
4. Thrall makes access decision
   │
   ▼
5. Thrall controls door hardware
   │
   ▼
6. Event logged to AetherDB
   │
   ├──► 7a. Loom syncs to Saga (PostgreSQL)
   │
   └──► 7b. Loom syncs to Bifrost (SQLite/PostgreSQL)
            │
            ▼
         8. Bifrost exports to central systems
```

### Configuration Change Flow

```
1. Admin makes change in Saga UI
   │
   ▼
2. Saga validates change
   │
   ▼
3. Saga sends to Thrall internal API
   │
   ▼
4. Thrall validates and stores in AetherDB
   │
   ▼
5. Thrall confirms success
   │
   ▼
6. Loom syncs change to Saga PostgreSQL
   │
   └──► 7. Loom syncs to Bifrost if needed
```

---

## API Endpoints

### Thrall Internal API (Unix Socket)

```
/internal/v1/cardholders
/internal/v1/access_levels
/internal/v1/doors
/internal/v1/events
/internal/v1/health
/internal/v1/sync
```

### Bifrost External API (Port 8080)

```
GET  /api/v2/status
GET  /api/v2/cardholders
POST /api/v2/cardholders
GET  /api/v2/events
GET  /api/v2/doors
POST /api/v2/access_decision
GET  /api/v2/health
```

### Saga Web UI (Port 80)

```
/                    - Dashboard
/cardholders         - Cardholder management
/access-levels       - Access level configuration
/doors               - Door/reader management
/events              - Event log viewer
/diagnostics         - System health
/loom                - Translation status
/settings            - System settings
```

---

## Directory Structure

```
aether-access/
├── adk/
│   ├── aether_thrall/
│   │   ├── manifest
│   │   └── rootfs/
│   │       └── app/
│   │           ├── run.sh
│   │           └── python/
│   ├── aether_bifrost/
│   │   ├── manifest
│   │   └── rootfs/
│   │       └── app/
│   │           ├── run.sh
│   │           └── api/
│   └── aether_saga/
│       ├── manifest
│       └── rootfs/
│           └── app/
│               ├── run.sh
│               └── static/
├── src/
│   ├── hal_core/           # Thrall core
│   ├── aetherdb/           # Binary database
│   ├── loom/               # Translation layer
│   └── sdk_modules/        # Azure SDK wrappers
├── api/
│   ├── aether_bifrost.py   # Bifrost server
│   └── database.py         # Database models
├── aether_saga/
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── pages/          # Page components
│   │   └── api/            # API client
│   └── package.json
├── python/
│   └── hal_bindings.py     # Python HAL bindings
├── deploy/
│   ├── aether_thrall.app
│   ├── aether_bifrost.app
│   └── aether_saga.app
└── build-aether-access.sh  # Master build script
```

---

## Deployment

### Building

```bash
./build-aether-access.sh
```

This builds all three .app packages:
- `deploy/aether_thrall.app`
- `deploy/aether_bifrost.app`
- `deploy/aether_saga.app`

### Installation

1. Open Azure BLU-IC2 web interface
2. Navigate to Applications
3. Upload each .app file:
   - `aether_thrall.app` (HAL - install first)
   - `aether_bifrost.app` (API - port 8080)
   - `aether_saga.app` (Web UI - port 80)

### Verification

```bash
# Check Thrall status
curl http://panel-ip:8080/api/v2/health

# Access Saga UI
open http://panel-ip/
```

---

## Version History

| Version | Date | Notes |
|---------|------|-------|
| 3.0.0 | 2026-03 | Initial release with Loom translation layer |
| 2.0.0 | 2026-02 | Renamed to Aether Access, ADK packaging |
| 1.0.0 | 2026-01 | Initial HAL implementation |

---

## License

Proprietary - CST Physical Access Control Systems

---

*Aether Access 3.0 - Where Hardware Meets Abstraction*
*"The machines answer to US."*
