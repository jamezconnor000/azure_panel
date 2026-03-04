#!/usr/bin/env python3
"""
Azure Panel Unified API Server
==============================
Single API server that provides all endpoints for:
- Aether Access (React Frontend)
- HAL Core (C Library via Python bindings)

This is the ONLY API server needed on the panel.

Architecture:
    Browser --> [Unified API (8080)] --> [HAL Library (Python bindings)] --> [Hardware]
                      |
                      +--> /api/v1/     Frontend I/O control
                      +--> /api/v2.1/   Auth, Users, Doors, Access Levels
                      +--> /api/v2.2/   HAL Integration (OSDP, Cards, Diagnostics)
                      +--> /hal/        Direct HAL access
                      +--> /ws/live     WebSocket for real-time

The HAL C library is loaded directly via Python bindings - no separate service needed.

Usage:
    python unified_api_server.py

    Or with uvicorn:
    uvicorn unified_api_server:app --host 0.0.0.0 --port 8080 --reload

Environment Variables:
    API_PORT=8080
    HAL_DATABASE_PATH=/data/hal_database.db
    HAL_LOG_LEVEL=INFO
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import asyncio
import json
import os
import sys
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add paths for imports
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)
sys.path.insert(0, os.path.join(SCRIPT_DIR, '..', 'python'))
sys.path.insert(0, os.path.join(SCRIPT_DIR, '..', 'gui', 'backend'))

# =============================================================================
# HAL Library Integration
# =============================================================================

# Import HAL bindings
try:
    from hal_bindings import HAL
    HAL_AVAILABLE = True
    logger.info("[OK] HAL Python bindings loaded")
except ImportError as e:
    logger.warning(f"[WARN] HAL bindings not available: {e}")
    HAL_AVAILABLE = False
    HAL = None

# Import v2.1 API router (Auth, Users, Doors, Access Levels)
try:
    from api_v2_1 import router as api_v2_1_router
    V2_1_AVAILABLE = True
    logger.info("[OK] v2.1 API router loaded")
except ImportError as e:
    logger.warning(f"[WARN] v2.1 API not available: {e}")
    V2_1_AVAILABLE = False
    api_v2_1_router = None

# Import v2.2 API router (HAL Integration - OSDP, Cards, Diagnostics)
try:
    from api_v2_2 import router as api_v2_2_router
    V2_2_AVAILABLE = True
    logger.info("[OK] v2.2 API router loaded")
except ImportError as e:
    logger.warning(f"[WARN] v2.2 API not available: {e}")
    V2_2_AVAILABLE = False
    api_v2_2_router = None
    HAL = None


# =============================================================================
# Configuration
# =============================================================================

VERSION = "2.0.0"
API_PORT = int(os.environ.get("API_PORT", 8080))
HAL_DATABASE_PATH = os.environ.get("HAL_DATABASE_PATH", "hal_database.db")

# Global HAL instance
hal = None


# =============================================================================
# WebSocket Manager
# =============================================================================

class ConnectionManager:
    def __init__(self):
        self.connections: List[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.connections.append(ws)

    def disconnect(self, ws: WebSocket):
        if ws in self.connections:
            self.connections.remove(ws)

    async def broadcast(self, message: dict):
        for ws in self.connections:
            try:
                await ws.send_json(message)
            except:
                pass

ws_manager = ConnectionManager()


# =============================================================================
# Lifespan
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown"""
    global hal

    # Startup
    print("\n" + "=" * 70)
    print(" AZURE PANEL UNIFIED API SERVER ".center(70))
    print("=" * 70)
    print(f"  Version:  {VERSION}")
    print(f"  Port:     {API_PORT}")
    print(f"  Database: {HAL_DATABASE_PATH}")
    print(f"  HAL Mode: {'Native' if HAL_AVAILABLE else 'Simulation'}")
    print("=" * 70)

    # Initialize HAL
    if HAL_AVAILABLE:
        hal = HAL(HAL_DATABASE_PATH)
        if hal.init():
            logger.info("[OK] HAL initialized")
            # Add default data for testing
            _seed_default_data()
        else:
            logger.warning("[WARN] HAL initialization failed")
    else:
        logger.warning("[WARN] Running without HAL - mock mode only")

    # Start background tasks
    task = asyncio.create_task(event_broadcast_loop())

    yield

    # Shutdown
    task.cancel()
    if hal:
        hal.shutdown()
    print("\nUnified API Server shutdown complete")


def _seed_default_data():
    """Seed default test data if database is empty"""
    global hal
    if not hal:
        return

    try:
        # Add default access level if none exist
        if not hal.get_all_access_levels():
            hal.add_access_level(1, "Full Access", doors=[1, 2, 3])
            hal.add_access_level(2, "Limited Access", doors=[1])
            logger.info("Seeded default access levels")

        # Add default door if none exist
        if not hal.get_all_doors():
            hal.add_door(1, "Main Entrance", strike_time_ms=3000)
            hal.add_door(2, "Back Door", strike_time_ms=5000)
            logger.info("Seeded default doors")

    except Exception as e:
        logger.warning(f"Error seeding default data: {e}")


# =============================================================================
# FastAPI App
# =============================================================================

app = FastAPI(
    title="Azure Panel Unified API",
    description="""
# Azure Panel Unified API

Single API for HAL hardware control and Aether Access management.

## API Versions
- **/api/v1/** - Frontend I/O control (panels, readers, doors)
- **/api/v2.1/** - Auth, Users, Doors, Access Levels
- **/api/v2.2/** - HAL Integration (OSDP, Cards, Diagnostics)
- **/hal/** - Direct HAL access

## WebSocket
- **ws://localhost:8080/ws/live** - Real-time I/O updates
    """,
    version=VERSION,
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =============================================================================
# Include API Routers
# =============================================================================

# Include v2.1 API (Auth, Users, Doors, Access Levels)
if V2_1_AVAILABLE and api_v2_1_router:
    app.include_router(api_v2_1_router)
    logger.info("  [OK] v2.1 API (Auth, Users, Doors, Access Levels)")

# Include v2.2 API (HAL Integration)
if V2_2_AVAILABLE and api_v2_2_router:
    app.include_router(api_v2_2_router)
    logger.info("  [OK] v2.2 API (OSDP, Cards, Diagnostics)")


# =============================================================================
# Pydantic Models
# =============================================================================

class CardCreate(BaseModel):
    card_number: str = Field(..., min_length=1, max_length=20)
    permission_id: int
    holder_name: Optional[str] = None
    facility_code: Optional[int] = 0
    activation_date: Optional[int] = None
    expiration_date: Optional[int] = None
    is_active: bool = True

class CardResponse(BaseModel):
    card_number: str
    permission_id: int
    holder_name: Optional[str] = None
    facility_code: int = 0
    activation_date: int = 0
    expiration_date: int = 0
    is_active: bool = True

class AccessDecisionRequest(BaseModel):
    card_number: str
    door_id: int

class AccessDecisionResponse(BaseModel):
    granted: bool
    reason: str
    card_number: str
    door_id: int
    timestamp: str

class DoorCreate(BaseModel):
    door_id: int
    name: str
    strike_time_ms: int = 3000

class AccessLevelCreate(BaseModel):
    permission_id: int
    name: str
    description: Optional[str] = ""
    doors: Optional[List[int]] = []


# =============================================================================
# Root & Health Endpoints
# =============================================================================

@app.get("/", response_class=HTMLResponse)
async def root():
    """API Root"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Azure Panel API</title>
        <style>
            body {{ font-family: sans-serif; max-width: 900px; margin: 50px auto; background: #1a1a2e; color: #eee; padding: 20px; }}
            h1, h2 {{ color: #00d4ff; }}
            a {{ color: #00d4ff; }}
            code {{ background: #333; padding: 2px 8px; border-radius: 4px; }}
            table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
            th, td {{ text-align: left; padding: 8px; border-bottom: 1px solid #333; }}
            .ok {{ color: #00aa55; }}
            .warn {{ color: #ffaa00; }}
        </style>
    </head>
    <body>
        <h1>Azure Panel Unified API</h1>
        <p>Version {VERSION} | HAL Mode: <span class="{'ok' if HAL_AVAILABLE else 'warn'}">{'Native' if HAL_AVAILABLE else 'Simulation'}</span></p>

        <h2>Documentation</h2>
        <ul>
            <li><a href="/docs">Swagger UI</a></li>
            <li><a href="/redoc">ReDoc</a></li>
        </ul>

        <h2>API Versions</h2>
        <table>
            <tr><th>Version</th><th>Prefix</th><th>Purpose</th><th>Status</th></tr>
            <tr><td>HAL</td><td><code>/hal/</code></td><td>Direct HAL access (cards, doors, events)</td><td><span class="{'ok' if HAL_AVAILABLE else 'warn'}">{'OK' if HAL_AVAILABLE else 'N/A'}</span></td></tr>
            <tr><td>v1</td><td><code>/api/v1/</code></td><td>Frontend I/O control</td><td><span class="ok">OK</span></td></tr>
            <tr><td>v2.1</td><td><code>/api/v2.1/</code></td><td>Auth, Users, Doors, Access Levels</td><td><span class="{'ok' if V2_1_AVAILABLE else 'warn'}">{'OK' if V2_1_AVAILABLE else 'N/A'}</span></td></tr>
            <tr><td>v2.2</td><td><code>/api/v2.2/</code></td><td>OSDP, Cards, Diagnostics</td><td><span class="{'ok' if V2_2_AVAILABLE else 'warn'}">{'OK' if V2_2_AVAILABLE else 'N/A'}</span></td></tr>
        </table>

        <h2>Quick Links</h2>
        <ul>
            <li><a href="/health">Health Check</a></li>
            <li><a href="/hal/stats">HAL Statistics</a></li>
            <li><a href="/hal/cards">Card List</a></li>
            <li><a href="/hal/doors">Door List</a></li>
            <li><a href="/hal/access-levels">Access Levels</a></li>
            <li><a href="/api/v1/dashboard">Dashboard Data</a></li>
        </ul>

        <h2>WebSocket</h2>
        <p><code>ws://localhost:{API_PORT}/ws/live</code></p>
    </body>
    </html>
    """


@app.get("/health")
async def health():
    """Health check"""
    hal_health = hal.get_health() if hal else {"status": "not_loaded"}
    return {
        "status": "healthy",
        "version": VERSION,
        "hal": hal_health,
        "api_versions": {
            "v1": True,
            "v2.1": V2_1_AVAILABLE,
            "v2.2": V2_2_AVAILABLE
        },
        "websocket_clients": len(ws_manager.connections),
        "timestamp": datetime.now().isoformat()
    }


# =============================================================================
# HAL Direct Access Endpoints (/hal/*)
# =============================================================================

@app.get("/hal/health", tags=["HAL Core"])
async def hal_health():
    """Get HAL system health"""
    if not hal:
        raise HTTPException(status_code=503, detail="HAL not initialized")
    return hal.get_health()


@app.get("/hal/stats", tags=["HAL Core"])
async def hal_stats():
    """Get HAL statistics"""
    if not hal:
        raise HTTPException(status_code=503, detail="HAL not initialized")
    return hal.get_stats()


@app.get("/hal/diagnostics", tags=["HAL Core"])
async def hal_diagnostics():
    """Get HAL diagnostics"""
    if not hal:
        raise HTTPException(status_code=503, detail="HAL not initialized")
    return hal.get_diagnostics()


# --- Cards ---

@app.post("/hal/cards", response_model=CardResponse, tags=["HAL Core - Cards"])
async def hal_add_card(card: CardCreate):
    """Add card to HAL database"""
    if not hal:
        raise HTTPException(status_code=503, detail="HAL not initialized")

    success = hal.add_card(
        card.card_number,
        card.permission_id,
        holder_name=card.holder_name,
        facility_code=card.facility_code or 0,
        activation_date=card.activation_date or 0,
        expiration_date=card.expiration_date or 0,
        is_active=card.is_active
    )
    if not success:
        raise HTTPException(status_code=400, detail="Failed to add card (may already exist)")

    result = hal.get_card(card.card_number)
    if not result:
        raise HTTPException(status_code=500, detail="Card added but retrieval failed")
    return result


@app.get("/hal/cards/{card_number}", response_model=CardResponse, tags=["HAL Core - Cards"])
async def hal_get_card(card_number: str):
    """Get card from HAL database"""
    if not hal:
        raise HTTPException(status_code=503, detail="HAL not initialized")

    card = hal.get_card(card_number)
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    return card


@app.get("/hal/cards", tags=["HAL Core - Cards"])
async def hal_list_cards(limit: int = 100, offset: int = 0):
    """List cards from HAL database"""
    if not hal:
        raise HTTPException(status_code=503, detail="HAL not initialized")

    cards = hal.get_all_cards(limit=limit, offset=offset)
    return {"cards": cards, "count": len(cards)}


@app.put("/hal/cards/{card_number}", tags=["HAL Core - Cards"])
async def hal_update_card(card_number: str, card: CardCreate):
    """Update card in HAL database"""
    if not hal:
        raise HTTPException(status_code=503, detail="HAL not initialized")

    existing = hal.get_card(card_number)
    if not existing:
        raise HTTPException(status_code=404, detail="Card not found")

    success = hal.update_card(
        card_number,
        permission_id=card.permission_id,
        holder_name=card.holder_name,
        activation_date=card.activation_date,
        expiration_date=card.expiration_date,
        is_active=card.is_active
    )
    if not success:
        raise HTTPException(status_code=400, detail="Failed to update card")

    return hal.get_card(card_number)


@app.delete("/hal/cards/{card_number}", tags=["HAL Core - Cards"])
async def hal_delete_card(card_number: str):
    """Delete card from HAL database"""
    if not hal:
        raise HTTPException(status_code=503, detail="HAL not initialized")

    success = hal.delete_card(card_number)
    if not success:
        raise HTTPException(status_code=404, detail="Card not found")
    return {"message": "Card deleted", "card_number": card_number}


# --- Doors ---

@app.get("/hal/doors", tags=["HAL Core - Doors"])
async def hal_list_doors():
    """List all doors"""
    if not hal:
        raise HTTPException(status_code=503, detail="HAL not initialized")

    doors = hal.get_all_doors()
    return {"doors": doors, "count": len(doors)}


@app.post("/hal/doors", tags=["HAL Core - Doors"])
async def hal_add_door(door: DoorCreate):
    """Add a door"""
    if not hal:
        raise HTTPException(status_code=503, detail="HAL not initialized")

    success = hal.add_door(door.door_id, door.name, strike_time_ms=door.strike_time_ms)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to add door (may already exist)")

    return hal.get_door(door.door_id)


@app.get("/hal/doors/{door_id}", tags=["HAL Core - Doors"])
async def hal_get_door(door_id: int):
    """Get door by ID"""
    if not hal:
        raise HTTPException(status_code=503, detail="HAL not initialized")

    door = hal.get_door(door_id)
    if not door:
        raise HTTPException(status_code=404, detail="Door not found")
    return door


@app.delete("/hal/doors/{door_id}", tags=["HAL Core - Doors"])
async def hal_delete_door(door_id: int):
    """Delete a door"""
    if not hal:
        raise HTTPException(status_code=503, detail="HAL not initialized")

    success = hal.delete_door(door_id)
    if not success:
        raise HTTPException(status_code=404, detail="Door not found")
    return {"message": "Door deleted", "door_id": door_id}


# --- Access Levels ---

@app.get("/hal/access-levels", tags=["HAL Core - Access Levels"])
async def hal_list_access_levels():
    """List all access levels"""
    if not hal:
        raise HTTPException(status_code=503, detail="HAL not initialized")

    levels = hal.get_all_access_levels()
    return {"access_levels": levels, "count": len(levels)}


@app.post("/hal/access-levels", tags=["HAL Core - Access Levels"])
async def hal_add_access_level(level: AccessLevelCreate):
    """Add an access level"""
    if not hal:
        raise HTTPException(status_code=503, detail="HAL not initialized")

    success = hal.add_access_level(
        level.permission_id,
        level.name,
        description=level.description,
        doors=level.doors
    )
    if not success:
        raise HTTPException(status_code=400, detail="Failed to add access level (may already exist)")

    return hal.get_access_level(level.permission_id)


@app.get("/hal/access-levels/{permission_id}", tags=["HAL Core - Access Levels"])
async def hal_get_access_level(permission_id: int):
    """Get access level by ID"""
    if not hal:
        raise HTTPException(status_code=503, detail="HAL not initialized")

    level = hal.get_access_level(permission_id)
    if not level:
        raise HTTPException(status_code=404, detail="Access level not found")
    return level


@app.delete("/hal/access-levels/{permission_id}", tags=["HAL Core - Access Levels"])
async def hal_delete_access_level(permission_id: int):
    """Delete an access level"""
    if not hal:
        raise HTTPException(status_code=503, detail="HAL not initialized")

    success = hal.delete_access_level(permission_id)
    if not success:
        raise HTTPException(status_code=404, detail="Access level not found")
    return {"message": "Access level deleted", "permission_id": permission_id}


# --- Access Decision ---

@app.post("/hal/access/check", response_model=AccessDecisionResponse, tags=["HAL Core - Access"])
async def hal_check_access(request: AccessDecisionRequest):
    """Check access decision (without generating event)"""
    if not hal:
        raise HTTPException(status_code=503, detail="HAL not initialized")

    result = hal.check_access(request.card_number, request.door_id)
    return AccessDecisionResponse(
        granted=result["granted"],
        reason=result["reason"],
        card_number=request.card_number,
        door_id=request.door_id,
        timestamp=datetime.now().isoformat()
    )


@app.post("/hal/simulate/card-read", tags=["HAL Core - Simulation"])
async def hal_simulate_card_read(card_number: str, door_id: int):
    """Simulate a card read and generate event"""
    if not hal:
        raise HTTPException(status_code=503, detail="HAL not initialized")

    # Check access
    result = hal.check_access(card_number, door_id)

    # Generate event
    event_type = 0 if result["granted"] else 1  # ACCESS_GRANT=0, ACCESS_DENY=1
    event_id = hal.add_event(
        event_type,
        card_number=card_number,
        door_id=door_id,
        decision=0 if result["granted"] else 1,
        details=result["reason"]
    )

    # Broadcast to WebSocket clients
    await ws_manager.broadcast({
        "type": "card_read",
        "event_id": event_id,
        "card_number": card_number,
        "door_id": door_id,
        "granted": result["granted"],
        "reason": result["reason"],
        "timestamp": datetime.now().isoformat()
    })

    return {
        "event_id": event_id,
        "granted": result["granted"],
        "reason": result["reason"],
        "card_number": card_number,
        "door_id": door_id
    }


# --- Events ---

@app.get("/hal/events", tags=["HAL Core - Events"])
async def hal_get_events(limit: int = 100, offset: int = 0):
    """Get events from HAL buffer"""
    if not hal:
        raise HTTPException(status_code=503, detail="HAL not initialized")

    events = hal.get_events(limit=limit, offset=offset)
    return {"events": events, "count": len(events)}


# =============================================================================
# Ambient.ai Entity Sync Endpoints (/hal/ambient/*)
# =============================================================================

@app.get("/hal/ambient/devices", tags=["HAL Core - Ambient.ai Sync"])
async def hal_ambient_devices():
    """Get all devices formatted for Ambient.ai sync"""
    if not hal:
        raise HTTPException(status_code=503, detail="HAL not initialized")

    devices = hal.get_all_devices_for_sync()
    return {"devices": devices, "count": len(devices)}


@app.get("/hal/ambient/persons", tags=["HAL Core - Ambient.ai Sync"])
async def hal_ambient_persons():
    """Get all persons formatted for Ambient.ai sync"""
    if not hal:
        raise HTTPException(status_code=503, detail="HAL not initialized")

    persons = hal.get_all_persons_for_sync()
    return {"persons": persons, "count": len(persons)}


@app.get("/hal/ambient/access-items", tags=["HAL Core - Ambient.ai Sync"])
async def hal_ambient_access_items():
    """Get all access items (cards) formatted for Ambient.ai sync"""
    if not hal:
        raise HTTPException(status_code=503, detail="HAL not initialized")

    items = hal.get_all_access_items_for_sync()
    return {"items": items, "count": len(items)}


@app.get("/hal/ambient/alarms", tags=["HAL Core - Ambient.ai Sync"])
async def hal_ambient_alarms():
    """Get all alarm definitions formatted for Ambient.ai sync"""
    if not hal:
        raise HTTPException(status_code=503, detail="HAL not initialized")

    alarms = hal.get_all_alarms_for_sync()
    return {"alarms": alarms, "count": len(alarms)}


@app.get("/hal/ambient/export-queue", tags=["HAL Core - Ambient.ai Sync"])
async def hal_ambient_export_queue(
    status: Optional[str] = None,
    limit: int = 100
):
    """Get export queue status"""
    if not hal:
        raise HTTPException(status_code=503, detail="HAL not initialized")

    return hal.get_export_queue_status(status=status, limit=limit)


@app.get("/hal/ambient/source-system", tags=["HAL Core - Ambient.ai Sync"])
async def hal_ambient_source_system():
    """Get source system UID for Ambient.ai"""
    if not hal:
        raise HTTPException(status_code=503, detail="HAL not initialized")

    return {"source_system_uid": hal.get_source_system_uid()}


# =============================================================================
# API v1 - Frontend I/O Control
# =============================================================================

@app.get("/api/v1/dashboard", tags=["v1 - Frontend"])
async def v1_dashboard():
    """Dashboard data for frontend"""
    if not hal:
        return {
            "system_status": "hal_not_initialized",
            "hal_version": "N/A",
            "cards": {},
            "doors": {},
            "events": {},
            "recent_events": [],
            "timestamp": datetime.now().isoformat()
        }

    stats = hal.get_stats()
    health = hal.get_health()
    events = hal.get_events(limit=10)

    return {
        "system_status": health.get("status", "unknown"),
        "hal_version": health.get("version", "unknown"),
        "cards": stats.get("cards", {}),
        "doors": stats.get("doors", {}),
        "events": stats.get("events", {}),
        "recent_events": events,
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/v1/panels/{panel_id}/io", tags=["v1 - Frontend"])
async def v1_panel_io(panel_id: int):
    """Panel I/O status"""
    if not hal:
        return {"panel_id": panel_id, "inputs": [], "outputs": [], "relays": []}

    doors = hal.get_all_doors()

    inputs = []
    outputs = []
    relays = []

    for door in doors:
        door_id = door.get("door_id", 0)
        door_name = door.get("name", f"Door {door_id}")

        inputs.append({
            "id": door_id * 10 + 1,
            "name": f"{door_name} - Door Contact",
            "type": "DOOR_CONTACT",
            "state": "inactive"
        })
        inputs.append({
            "id": door_id * 10 + 2,
            "name": f"{door_name} - REX",
            "type": "REX",
            "state": "inactive"
        })
        outputs.append({
            "id": door_id * 10 + 1,
            "name": f"{door_name} - Strike",
            "type": "STRIKE",
            "state": "inactive"
        })
        relays.append({
            "id": door_id,
            "name": f"{door_name} - Relay",
            "state": "inactive"
        })

    return {
        "panel_id": panel_id,
        "panel_name": f"Panel {panel_id}",
        "inputs": inputs,
        "outputs": outputs,
        "relays": relays,
        "last_update": datetime.now().isoformat()
    }


@app.get("/api/v1/panels/{panel_id}/health", tags=["v1 - Frontend"])
async def v1_panel_health(panel_id: int):
    """Panel health metrics"""
    if not hal:
        return {"panel_id": panel_id, "overall_health": "unknown", "online": False}

    health = hal.get_health()
    return {
        "panel_id": panel_id,
        "panel_name": f"Panel {panel_id}",
        "overall_health": "excellent" if health.get("status") == "healthy" else "poor",
        "health_score": 95,
        "online": True,
        "last_health_check": datetime.now().isoformat()
    }


@app.get("/api/v1/readers/health/summary", tags=["v1 - Frontend"])
async def v1_readers_health():
    """All readers health summary"""
    if not hal:
        return {"readers": [], "timestamp": datetime.now().isoformat()}

    doors = hal.get_all_doors()
    readers = []
    for door in doors:
        readers.append({
            "reader_id": door.get("door_id", 0),
            "reader_name": door.get("name", "Unknown"),
            "overall_health": "excellent",
            "health_score": 95,
            "issues": 0
        })

    return {
        "readers": readers,
        "timestamp": datetime.now().isoformat()
    }


@app.post("/api/v1/doors/{door_id}/unlock", tags=["v1 - Frontend"])
async def v1_unlock_door(door_id: int, duration_seconds: int = 5):
    """Unlock a door"""
    if hal:
        hal.add_event(2, door_id=door_id, details=f"Manual unlock for {duration_seconds}s")  # DOOR_UNLOCK=2

    await ws_manager.broadcast({
        "type": "door_control",
        "action": "unlock",
        "door_id": door_id,
        "timestamp": datetime.now().isoformat()
    })

    return {
        "success": True,
        "action": "UNLOCK",
        "target_id": door_id,
        "target_type": "door",
        "message": f"Door {door_id} unlocked",
        "timestamp": datetime.now().isoformat()
    }


@app.post("/api/v1/doors/{door_id}/lock", tags=["v1 - Frontend"])
async def v1_lock_door(door_id: int):
    """Lock a door"""
    if hal:
        hal.add_event(2, door_id=door_id, details="Manual lock")

    return {
        "success": True,
        "action": "LOCK",
        "target_id": door_id,
        "target_type": "door",
        "message": f"Door {door_id} locked",
        "timestamp": datetime.now().isoformat()
    }


@app.post("/api/v1/control/lockdown", tags=["v1 - Frontend"])
async def v1_emergency_lockdown(reason: str = "Emergency"):
    """Emergency lockdown"""
    if hal:
        hal.add_event(8, details=reason)  # EMERGENCY=8

    await ws_manager.broadcast({
        "type": "emergency",
        "action": "LOCKDOWN",
        "reason": reason,
        "timestamp": datetime.now().isoformat()
    })

    return {
        "success": True,
        "action": "LOCKDOWN",
        "target_id": 0,
        "target_type": "system",
        "message": f"Emergency lockdown: {reason}",
        "timestamp": datetime.now().isoformat()
    }


@app.post("/api/v1/control/unlock-all", tags=["v1 - Frontend"])
async def v1_emergency_unlock(reason: str = "Emergency"):
    """Emergency unlock all"""
    if hal:
        hal.add_event(8, details=f"Emergency unlock: {reason}")

    await ws_manager.broadcast({
        "type": "emergency",
        "action": "UNLOCK_ALL",
        "reason": reason,
        "timestamp": datetime.now().isoformat()
    })

    return {
        "success": True,
        "action": "UNLOCK_ALL",
        "target_id": 0,
        "target_type": "system",
        "message": f"Emergency unlock: {reason}",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/v1/macros", tags=["v1 - Frontend"])
async def v1_list_macros():
    """List control macros"""
    return {"macros": [
        {"macro_id": 1, "name": "Evening Lockdown", "description": "Lock all perimeter doors"},
        {"macro_id": 2, "name": "Emergency Egress", "description": "Unlock all exit doors"},
        {"macro_id": 3, "name": "Fire Alarm Mode", "description": "Unlock all doors for evacuation"}
    ]}


@app.get("/api/v1/overrides", tags=["v1 - Frontend"])
async def v1_list_overrides():
    """List active overrides"""
    return []


# =============================================================================
# WebSocket
# =============================================================================

@app.websocket("/ws/live")
async def websocket_endpoint(ws: WebSocket):
    """Real-time WebSocket updates"""
    await ws_manager.connect(ws)

    try:
        await ws.send_json({
            "type": "connected",
            "message": f"Connected to Azure Panel API v{VERSION}",
            "hal_mode": "native" if HAL_AVAILABLE else "simulation",
            "timestamp": datetime.now().isoformat()
        })

        while True:
            data = await ws.receive_text()
            try:
                msg = json.loads(data)
                if msg.get("type") == "ping":
                    await ws.send_json({"type": "pong", "timestamp": datetime.now().isoformat()})
                elif msg.get("action") == "subscribe":
                    await ws.send_json({
                        "type": "subscription_confirmed",
                        "topics": msg.get("topics", []),
                        "timestamp": datetime.now().isoformat()
                    })
            except json.JSONDecodeError:
                pass

    except WebSocketDisconnect:
        ws_manager.disconnect(ws)


# =============================================================================
# Background Tasks
# =============================================================================

async def event_broadcast_loop():
    """Broadcast new events to WebSocket clients"""
    while True:
        await asyncio.sleep(5)

        if ws_manager.connections:
            # Send heartbeat
            await ws_manager.broadcast({
                "type": "heartbeat",
                "timestamp": datetime.now().isoformat()
            })


# =============================================================================
# Main
# =============================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "unified_api_server:app",
        host="0.0.0.0",
        port=API_PORT,
        reload=True,
        log_level="info"
    )
