# Python Backend - Shared Services Layer

**Version:** 2.1.0
**Framework:** FastAPI
**Python:** 3.8+
**Status:** Production Ready

---

## Overview

The Python Backend provides a shared service layer for the Azure Panel system. It offers REST APIs, WebSocket real-time updates, and Python bindings to the HAL Core C library. Both Aether Access GUI and Ambient.ai integration can use these shared services.

---

## Features

- **FastAPI REST Server** - High-performance async API
- **WebSocket Support** - Real-time event streaming
- **JWT Authentication** - Secure token-based auth
- **SQLite Database** - Shared data persistence
- **HAL Bindings** - Python interface to C library
- **Modular Design** - Easy to extend and customize

---

## Directory Structure

```
api/
├── hal_api_server.py      # Main REST API server
└── requirements.txt       # API dependencies

python/
├── __init__.py            # Package initialization
├── hal_interface.py       # HAL C library bindings
├── card_provisioning.py   # Card management utilities
├── event_monitor.py       # Event subscription
└── utils.py               # Helper utilities

services/
├── __init__.py
├── database.py            # Shared database layer
├── auth.py                # JWT authentication
├── config.py              # Configuration management
├── event_service.py       # Event processing
└── models.py              # Pydantic models
```

---

## Quick Start

### Installation
```bash
cd Source
pip install -r requirements.txt

# Or install as package
pip install -e .
```

### Run the API Server
```bash
python3 api/hal_api_server.py

# Or with uvicorn directly
uvicorn api.hal_api_server:app --host 0.0.0.0 --port 8080 --reload
```

### API Documentation
- Swagger UI: http://localhost:8080/docs
- ReDoc: http://localhost:8080/redoc

---

## API Endpoints

### Panel Monitoring (v1)
```
GET  /api/v1/panels/{id}/io          Get panel I/O status
GET  /api/v1/panels/{id}/health      Get panel health metrics
GET  /api/v1/readers/{id}/health     Get reader health
GET  /api/v1/readers/health/summary  Get all readers summary
```

### Door Control (v1)
```
POST /api/v1/doors/{id}/unlock       Unlock door
POST /api/v1/doors/{id}/lock         Lock door
POST /api/v1/doors/{id}/lockdown     Lockdown door
POST /api/v1/doors/{id}/release      Release door
```

### Output Control (v1)
```
POST /api/v1/outputs/{id}/activate   Activate output
POST /api/v1/outputs/{id}/deactivate Deactivate output
POST /api/v1/outputs/{id}/pulse      Pulse output
POST /api/v1/outputs/{id}/toggle     Toggle output
```

### Relay Control (v1)
```
POST /api/v1/relays/{id}/activate    Activate relay
POST /api/v1/relays/{id}/deactivate  Deactivate relay
```

### Emergency Operations (v1)
```
POST /api/v1/control/lockdown        Emergency lockdown
POST /api/v1/control/unlock-all      Emergency unlock
POST /api/v1/control/normal          Return to normal
```

### Macros (v1)
```
GET  /api/v1/macros                  List macros
POST /api/v1/macros/{id}/execute     Execute macro
```

### WebSocket
```
WS   /ws/live                        Real-time events
```

---

## HAL Interface (Python Bindings)

### Basic Usage
```python
from python.hal_interface import HAL

# Initialize HAL
hal = HAL()
hal.initialize("/etc/hal/hal_config.json")

# Process card read
result = hal.process_card_read(card_number=12345, door_id=1)
print(f"Access: {'granted' if result.granted else 'denied'}")
print(f"Reason: {result.reason}")

# Shutdown
hal.shutdown()
```

### Card Provisioning
```python
from python.card_provisioning import CardManager

card_mgr = CardManager()

# Add a card
card_mgr.add_card(
    card_number=12345678,
    holder_name="John Doe",
    access_level_id=1,
    activation_date="2026-01-01",
    expiration_date="2027-01-01"
)

# Remove a card
card_mgr.remove_card(12345678)

# List all cards
cards = card_mgr.list_cards()
```

### Event Monitoring
```python
from python.event_monitor import EventMonitor

monitor = EventMonitor()

# Callback-based monitoring
def handle_event(event):
    print(f"Event: {event.type} at door {event.door_id}")

monitor.subscribe(handle_event)
monitor.start()

# Or async iteration
async for event in monitor.stream():
    print(f"Event: {event.type}")
```

---

## Database Layer

### Shared Database Operations
```python
from services.database import Database

db = Database("/var/lib/hal/hal.db")

# Users
user = await db.create_user(
    username="admin",
    email="admin@example.com",
    password_hash=hashed_password,
    role="admin"
)

users = await db.get_all_users()

# Doors
door = await db.create_door_config(
    door_id=1,
    door_name="Front Door",
    osdp_enabled=True,
    reader_address=0
)

# Access Levels
level = await db.create_access_level(
    name="All Doors",
    description="Access to all doors",
    priority=100
)

# Audit Logging
await db.log_audit(
    user_id=1,
    action="door_unlock",
    resource_type="door",
    resource_id=1,
    details={"reason": "Manual unlock"}
)
```

---

## Authentication

### JWT Configuration
```python
from services.auth import (
    create_access_token,
    create_refresh_token,
    verify_password,
    hash_password,
    get_current_user
)

# Configuration
SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480  # 8 hours
```

### Login Flow
```python
from fastapi import Depends
from services.auth import get_current_user

@app.post("/api/v2.1/auth/login")
async def login(username: str, password: str):
    user = await db.get_user_by_username(username)

    if not verify_password(password, user.password_hash):
        raise HTTPException(status_code=401)

    token = create_access_token({"sub": str(user.id)})
    return {"access_token": token}

@app.get("/api/v2.1/protected")
async def protected_route(user = Depends(get_current_user)):
    return {"user": user.username}
```

### Role-Based Permissions
```python
ROLE_PERMISSIONS = {
    "admin": ["user.*", "door.*", "access_level.*", "audit.*"],
    "operator": ["door.read", "door.control", "card_holder.*"],
    "guard": ["door.read", "door.control", "audit.read"],
    "user": ["door.read"]
}

def check_permission(user, permission):
    role_perms = ROLE_PERMISSIONS.get(user.role, [])
    return permission in role_perms or f"{permission.split('.')[0]}.*" in role_perms
```

---

## WebSocket Real-Time Events

### Server-Side
```python
from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        self.connections: List[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.connections.append(ws)

    async def broadcast(self, message: dict):
        for conn in self.connections:
            await conn.send_json(message)

manager = ConnectionManager()

@app.websocket("/ws/live")
async def websocket_endpoint(ws: WebSocket):
    await manager.connect(ws)
    try:
        while True:
            data = await ws.receive_json()
            # Handle client messages
    except WebSocketDisconnect:
        manager.disconnect(ws)
```

### Client-Side (JavaScript)
```javascript
const ws = new WebSocket('ws://localhost:8080/ws/live');

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('Event:', data);
};

ws.onopen = () => {
    ws.send(JSON.stringify({
        action: 'subscribe',
        topics: ['door_events', 'reader_health']
    }));
};
```

---

## Configuration

### Environment Variables
```bash
# API Server
HAL_API_HOST=0.0.0.0
HAL_API_PORT=8080
HAL_API_WORKERS=4

# Database
HAL_DATABASE_PATH=/var/lib/hal/hal.db

# Authentication
HAL_SECRET_KEY=your-production-secret-key
HAL_TOKEN_EXPIRE_MINUTES=480

# HAL Library
HAL_CONFIG_PATH=/etc/hal/hal_config.json
HAL_LOG_LEVEL=info
```

### requirements.txt
```
fastapi>=0.100.0
uvicorn>=0.23.0
pydantic>=2.0.0
python-jose>=3.3.0
bcrypt>=4.0.0
aiosqlite>=0.19.0
httpx>=0.24.0
websockets>=11.0.0
python-multipart>=0.0.6
```

---

## Integration Points

### With HAL Core (C Library)
```python
# Uses ctypes/CFFI to call C functions
import ctypes

hal_lib = ctypes.CDLL("libhal_core.so")
hal_lib.HAL_Initialize.argtypes = [ctypes.POINTER(HALConfig)]
hal_lib.HAL_Initialize.restype = ctypes.c_int
```

### With Aether Access (Frontend)
```python
# Frontend calls REST API endpoints
# Real-time updates via WebSocket
# CORS configured for frontend origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"]
)
```

### With Ambient.ai Integration
```python
# Event forwarding service
from services.event_service import EventForwarder

forwarder = EventForwarder(
    api_url="https://api.ambient.ai/v1/events",
    api_key=os.environ["AMBIENT_API_KEY"]
)

async def forward_event(event):
    await forwarder.send(event)
```

---

## Testing

```bash
# Run all tests
pytest tests/

# Run specific test
pytest tests/test_api.py -v

# With coverage
pytest --cov=services tests/
```

---

## Deployment

### Docker
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8080
CMD ["uvicorn", "api.hal_api_server:app", "--host", "0.0.0.0", "--port", "8080"]
```

### Systemd Service
```ini
[Unit]
Description=HAL API Server
After=network.target

[Service]
User=hal
WorkingDirectory=/opt/hal
ExecStart=/usr/bin/python3 -m uvicorn api.hal_api_server:app --host 0.0.0.0 --port 8080
Restart=always

[Install]
WantedBy=multi-user.target
```

---

*Python Backend - The shared service layer for Azure Panel*
