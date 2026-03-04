# Aether HAL - ADK Deployment Guide

## Overview

Aether HAL (Hardware Abstraction Layer) for Azure BLU-IC2 Controllers uses the official **Azure Access Technology Application Development Kit (ADK)** for deployment.

## ADK Workflow

### Step 1: Obtain Developer Certificate

Contact Azure Access Technology to obtain the developer signing certificate:
- File: `test-app-dev-sign.crt`
- Place in: `/Users/mosley/AXIOM/Projects/Azure_Panel/Relics/adk_1.22.1_20250903-213533/`

### Step 2: Build the .app Package

```bash
cd /Users/mosley/AXIOM/Projects/Azure_Panel/Source/adk/aether_hal
./pack.sh
```

This creates: `deploy/aether_hal.app`

### Step 3: Install on BLU-IC2 Controller

1. Open the Controller's Web Interface in a browser
2. Navigate to **Applications**
3. Click **Upload**
4. Select `aether_hal.app`
5. Application will start automatically after upload

## Package Contents

```
aether_hal/
├── manifest           # ADK manifest (Id, Version, EntryPoint, Ports)
├── pack.sh            # Build script
└── rootfs/
    └── app/
        ├── run.sh         # Entry point script
        ├── requirements.txt
        ├── api/           # REST API server
        │   ├── unified_api_server.py
        │   ├── api_v2_1.py
        │   ├── api_v2_2.py
        │   ├── auth.py
        │   ├── database.py
        │   └── ambient_export_daemon.py
        ├── python/        # HAL Python bindings
        │   └── hal_bindings.py
        ├── config/        # Configuration files
        ├── data/          # Runtime data (database)
        └── logs/          # Application logs
```

## Manifest Configuration

```json
{
  "Id": "aether_hal",
  "Info": "Aether HAL - Hardware Abstraction Layer for Azure BLU-IC2",
  "EntryPoint": "/app/run.sh",
  "Ports": [8080],
  "Data": "/app/data",
  "PFSData": "/app/pdata",
  "ExclusiveMode": 0,
  "Version": "2.0.0",
  "WorkDir": "/app",
  "User": "root"
}
```

## API Endpoints

Once deployed, access the API at: `http://<panel-ip>:8080/`

| Endpoint | Description |
|----------|-------------|
| `/health` | Health check |
| `/docs` | Swagger UI documentation |
| `/hal/*` | HAL Core API |
| `/api/v1/*` | Frontend API |
| `/api/v2.1/*` | Auth & Management API |
| `/ws/live` | WebSocket real-time events |

## Resource Limits

Per ADK specification, applications are limited to:
- **CPU**: 25%
- **RAM**: 50%
- **Flash**: 200 MB
- **Persistent Storage**: 10 MB

## Environment Variables

The BLU-IC2 controller provides these environment variables:

| Variable | Description |
|----------|-------------|
| `ASP_HOSTNAME` | Controller hostname |
| `ASP_MASTER_HOSTNAME` | SDK master hostname |
| `ASP_MASTER_PORT` | SDK master port |
| `ASP_API_HOSTNAME` | API hostname |
| `ASP_API_PORT` | API port (443) |

## Troubleshooting

### SSH Access
1. Click on the application in the web interface
2. Toggle SSH to "On"
3. Get root password
4. Connect: `ssh root@<panel-ip> -p 2222`

### View Logs
```bash
# Via SSH
tail -f /app/logs/aether_hal.log

# Via controller
logger "message" # Goes to system log
```

### Reset Application
Remove via web interface and re-upload the .app file.

---

**Version**: 2.0.0
**ADK Version**: 1.22.2
**Target**: Azure BLU-IC2 (Firmware 1.16.9+)
