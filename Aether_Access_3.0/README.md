# Aether Access 3.0

> Complete Access Control System for Azure BLU-IC2 Controllers

## Components

| App | Purpose | Technology |
|-----|---------|------------|
| **Aether Thrall** | Hardware Abstraction Layer | C / Azure ADK |
| **Aether Bifrost** | API Server (the bridge) | Python / FastAPI |
| **Aether Saga** | Web Management Interface | React / TypeScript |

## Architecture

```
[Aether Saga (80)] --> [Aether Bifrost (8080)] --> [Aether Thrall] --> [Hardware]
       |                         |
       |                         +--> /api/v1/     Frontend I/O control
       |                         +--> /api/v2.1/   Auth, Users, Doors, Access Levels
       |                         +--> /api/v2.2/   HAL Integration (OSDP, Cards, Diagnostics)
       |                         +--> /hal/        Direct HAL access
       |                         +--> /ws/live     WebSocket for real-time
       |
       +--> Cardholder Management
       +--> Access Level Configuration
       +--> Door Management
       +--> Real-time Monitoring
```

## Directory Structure

```
Aether_Access_3.0/
├── api/                    # Aether Bifrost - API Server
│   ├── aether_bifrost.py   # Main API server
│   └── ambient_integration.py  # Ambient.ai cloud integration
├── aether_saga/            # Aether Saga - Web Frontend
│   ├── src/                # React source code
│   └── dist/               # Production build
├── python/                 # HAL Python bindings
├── aether_thrall.app       # Aether Thrall - HAL (Azure ADK format)
├── config/                 # Configuration templates
├── systemd/                # Service files
├── scripts/                # Installation scripts
├── docs/                   # Documentation
├── VERSION                 # Current version (3.0.0)
└── requirements.txt        # Python dependencies
```

## Quick Start

### Development

```bash
# Start Bifrost API
cd api
python aether_bifrost.py

# Start Saga frontend (dev mode)
cd aether_saga
npm run dev
```

### Production Deployment

```bash
# Build Saga frontend
cd aether_saga
npm run build

# Run build script
./scripts/build-package.sh

# Deploy to panel
scp aether-access-3.0.0.tar.gz root@panel-ip:/tmp/
ssh root@panel-ip 'cd /tmp && tar -xzf aether-access-3.0.0.tar.gz && sudo ./scripts/install.sh'
```

## Features

- Event-driven architecture with 100K event buffer
- Local SQLite card database with 1M+ capacity
- OSDP/Wiegand/DESFire protocol support
- Offline operation capability
- Real-time WebSocket updates
- Ambient.ai cloud integration
- UnityIS-compatible API

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `VITE_API_URL` | `http://localhost:8080` | Bifrost API URL |
| `API_PORT` | `8080` | Bifrost port |
| `HAL_DATABASE_PATH` | `/data/hal_database.db` | Card database location |
| `AMBIENT_API_KEY` | - | Ambient.ai API key |
| `AMBIENT_SOURCE_SYSTEM_UID` | - | Ambient.ai system UUID |

## Version

**3.0.0** - March 2026

---

*Part of the Aether Access Control System*
*"The machines answer to US."*
