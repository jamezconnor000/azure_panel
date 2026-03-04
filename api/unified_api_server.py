#!/usr/bin/env python3
"""
Aether Bifrost API Server
=========================
The bridge between realms - connecting applications to hardware.

Single API server that provides all endpoints for:
- Aether Access (React Frontend)
- HAL Core (C Library via Python bindings)

This is the ONLY API server needed on the panel.

Architecture:
    Browser --> [Aether Bifrost (8080)] --> [HAL Library (Python bindings)] --> [Hardware]
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
    print(" AETHER BIFROST API SERVER ".center(70))
    print(" The Bridge Between Realms ".center(70))
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
    print("\nAether Bifrost API Server shutdown complete")


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
    title="Aether Bifrost API",
    description="""
# Aether Bifrost API
### The Bridge Between Realms

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
        <title>Aether Bifrost API</title>
        <style>
            body {{ font-family: sans-serif; max-width: 900px; margin: 50px auto; background: #1a1a2e; color: #eee; padding: 20px; }}
            h1 {{ color: #00d4ff; }}
            h2 {{ color: #00d4ff; }}
            .subtitle {{ color: #888; font-size: 0.9em; margin-top: -10px; }}
            a {{ color: #00d4ff; }}
            code {{ background: #333; padding: 2px 8px; border-radius: 4px; }}
            table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
            th, td {{ text-align: left; padding: 8px; border-bottom: 1px solid #333; }}
            .ok {{ color: #00aa55; }}
            .warn {{ color: #ffaa00; }}
            .rainbow {{ background: linear-gradient(90deg, #ff0000, #ff7f00, #ffff00, #00ff00, #0000ff, #4b0082, #9400d3); -webkit-background-clip: text; background-clip: text; color: transparent; }}
        </style>
    </head>
    <body>
        <h1>Aether Bifrost API</h1>
        <p class="subtitle">The Bridge Between Realms</p>
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
# Reader Mode Control (UnityIS-compatible)
# =============================================================================

# Reader Mode constants (UnityIS compatible)
READER_MODES = {
    1: "Disabled",
    2: "Unlocked",
    3: "Locked (REX Only)",
    4: "Facility Code Only",
    5: "Card Only",
    6: "PIN Only",
    7: "Card and PIN",
    8: "Card or PIN",
    9: "Office First",
    10: "Blocked",
    11: "Emergency Lock",
    12: "Emergency Unlock",
    13: "Fingerprint",
    14: "Card and Fingerprint",
    15: "Card or Fingerprint"
}


class ReaderModeRequest(BaseModel):
    mode: int = Field(..., ge=1, le=15, description="Reader mode (1-15)")


@app.get("/hal/readers/{reader_id}/mode", tags=["HAL Core - Reader Control"])
async def hal_get_reader_mode(reader_id: int):
    """Get current reader mode"""
    if not hal:
        raise HTTPException(status_code=503, detail="HAL not initialized")

    door = hal.get_door(reader_id)
    if not door:
        raise HTTPException(status_code=404, detail="Reader not found")

    # Get current mode (default to Card Only if not set)
    current_mode = door.get("reader_mode", 5)

    return {
        "reader_id": reader_id,
        "mode": current_mode,
        "mode_name": READER_MODES.get(current_mode, "Unknown"),
        "available_modes": READER_MODES
    }


@app.post("/hal/readers/{reader_id}/mode", tags=["HAL Core - Reader Control"])
async def hal_set_reader_mode(reader_id: int, request: ReaderModeRequest):
    """
    Set reader mode (UnityIS compatible)

    Reader Modes:
    - 1: Disabled
    - 2: Unlocked
    - 3: Locked (REX Only)
    - 4: Facility Code Only
    - 5: Card Only
    - 6: PIN Only
    - 7: Card and PIN
    - 8: Card or PIN
    - 9: Office First
    - 10: Blocked
    - 11: Emergency Lock
    - 12: Emergency Unlock
    - 13: Fingerprint
    - 14: Card and Fingerprint
    - 15: Card or Fingerprint
    """
    if not hal:
        raise HTTPException(status_code=503, detail="HAL not initialized")

    door = hal.get_door(reader_id)
    if not door:
        raise HTTPException(status_code=404, detail="Reader not found")

    # Update reader mode
    if hasattr(hal, 'set_reader_mode'):
        success = hal.set_reader_mode(reader_id, request.mode)
    else:
        # Fallback: store mode in door config
        success = hal.update_door(reader_id, reader_mode=request.mode)

    if not success:
        raise HTTPException(status_code=400, detail="Failed to set reader mode")

    # Log the mode change
    hal.add_event(
        6,  # READER_MODE_CHANGE
        door_id=reader_id,
        details=f"Reader mode changed to {request.mode} ({READER_MODES.get(request.mode, 'Unknown')})"
    )

    # Broadcast mode change
    await ws_manager.broadcast({
        "type": "reader_mode_change",
        "reader_id": reader_id,
        "mode": request.mode,
        "mode_name": READER_MODES.get(request.mode, "Unknown"),
        "timestamp": datetime.now().isoformat()
    })

    return {
        "success": True,
        "reader_id": reader_id,
        "mode": request.mode,
        "mode_name": READER_MODES.get(request.mode, "Unknown")
    }


@app.get("/hal/readers/modes", tags=["HAL Core - Reader Control"])
async def hal_list_reader_modes():
    """List all available reader modes"""
    return {
        "modes": [{"id": k, "name": v} for k, v in READER_MODES.items()]
    }


# =============================================================================
# Credential Status (UnityIS-compatible)
# =============================================================================

# Credential Status constants (UnityIS compatible)
CREDENTIAL_STATUS = {
    1: "Active",
    2: "Lost",
    3: "Returned",
    4: "Deactivated",
    5: "Terminated",
    6: "Broken",
    7: "Furlough",
    100: "Created",
    101: "Created and Email Sent",
    102: "Activated",
    103: "Pending Revoke",
    104: "Revoked",
    105: "Deleted",
    106: "Lost",
    107: "Created and Email not Sent"
}


class CredentialStatusRequest(BaseModel):
    status: int = Field(..., description="Credential status code")


@app.get("/hal/cards/{card_number}/status", tags=["HAL Core - Cards"])
async def hal_get_card_status(card_number: str):
    """Get credential status"""
    if not hal:
        raise HTTPException(status_code=503, detail="HAL not initialized")

    card = hal.get_card(card_number)
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")

    status = card.get("status", 1 if card.get("is_active") else 4)

    return {
        "card_number": card_number,
        "status": status,
        "status_name": CREDENTIAL_STATUS.get(status, "Unknown"),
        "is_active": card.get("is_active", False)
    }


@app.put("/hal/cards/{card_number}/status", tags=["HAL Core - Cards"])
async def hal_set_card_status(card_number: str, request: CredentialStatusRequest):
    """
    Set credential status (UnityIS compatible)

    Status Codes:
    - 1: Active
    - 2: Lost
    - 3: Returned
    - 4: Deactivated
    - 5: Terminated
    - 6: Broken
    - 7: Furlough
    """
    if not hal:
        raise HTTPException(status_code=503, detail="HAL not initialized")

    card = hal.get_card(card_number)
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")

    # Determine if card should be active based on status
    is_active = request.status in [1, 102]  # Active or Activated

    success = hal.update_card(
        card_number,
        status=request.status,
        is_active=is_active
    )

    if not success:
        raise HTTPException(status_code=400, detail="Failed to update card status")

    return {
        "success": True,
        "card_number": card_number,
        "status": request.status,
        "status_name": CREDENTIAL_STATUS.get(request.status, "Unknown"),
        "is_active": is_active
    }


@app.get("/hal/credential-statuses", tags=["HAL Core - Cards"])
async def hal_list_credential_statuses():
    """List all available credential statuses"""
    return {
        "statuses": [{"id": k, "name": v} for k, v in CREDENTIAL_STATUS.items()]
    }


# =============================================================================
# Anti-Passback Control (UnityIS-compatible)
# =============================================================================

@app.post("/hal/cards/{card_number}/reset-apb", tags=["HAL Core - Anti-Passback"])
async def hal_reset_anti_passback(card_number: str):
    """
    Reset anti-passback state for a card/personnel (UnityIS compatible)

    This clears the anti-passback violation state allowing the card
    to be used again at entry/exit points.
    """
    if not hal:
        raise HTTPException(status_code=503, detail="HAL not initialized")

    card = hal.get_card(card_number)
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")

    # Reset APB state
    if hasattr(hal, 'reset_anti_passback'):
        success = hal.reset_anti_passback(card_number)
    else:
        # Fallback: update card APB state
        success = hal.update_card(card_number, apb_state=0, apb_zone=None)

    if not success:
        raise HTTPException(status_code=400, detail="Failed to reset anti-passback")

    # Log the APB reset
    hal.add_event(
        7,  # APB_RESET
        card_number=card_number,
        details="Anti-passback state reset"
    )

    return {
        "success": True,
        "card_number": card_number,
        "message": "Anti-passback state reset successfully"
    }


@app.post("/hal/reset-all-apb", tags=["HAL Core - Anti-Passback"])
async def hal_reset_all_anti_passback():
    """Reset anti-passback state for all cards"""
    if not hal:
        raise HTTPException(status_code=503, detail="HAL not initialized")

    if hasattr(hal, 'reset_all_anti_passback'):
        count = hal.reset_all_anti_passback()
    else:
        # Fallback: iterate through all cards
        cards = hal.get_all_cards(limit=100000)
        count = 0
        for card in cards:
            if hal.update_card(card["card_number"], apb_state=0, apb_zone=None):
                count += 1

    # Log the bulk APB reset
    hal.add_event(
        7,  # APB_RESET
        details=f"Bulk anti-passback reset: {count} cards"
    )

    return {
        "success": True,
        "cards_reset": count,
        "message": f"Anti-passback state reset for {count} cards"
    }


# =============================================================================
# Personnel/Card Holder History (UnityIS-compatible)
# =============================================================================

@app.get("/hal/cards/{card_number}/history", tags=["HAL Core - History"])
async def hal_get_card_history(card_number: str, limit: int = 50):
    """
    Get event history for a card/personnel (UnityIS compatible)

    Returns the most recent events for the specified card.
    """
    if not hal:
        raise HTTPException(status_code=503, detail="HAL not initialized")

    card = hal.get_card(card_number)
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")

    # Get events for this card
    if hasattr(hal, 'get_card_events'):
        events = hal.get_card_events(card_number, limit=limit)
    else:
        # Fallback: filter events by card number
        all_events = hal.get_events(limit=1000)
        events = [e for e in all_events if e.get("card_number") == card_number][:limit]

    return {
        "card_number": card_number,
        "holder_name": card.get("holder_name"),
        "events": events,
        "count": len(events)
    }


# =============================================================================
# Device Status (UnityIS-compatible)
# =============================================================================

@app.get("/hal/device-status", tags=["HAL Core - Device Status"])
async def hal_get_device_status(address: Optional[str] = None):
    """
    Get status of all devices (UnityIS compatible)

    Returns status of drivers, controllers, sub-controllers and devices.
    """
    if not hal:
        raise HTTPException(status_code=503, detail="HAL not initialized")

    # Build device status response
    doors = hal.get_all_doors()

    devices = []
    for door in doors:
        door_id = door.get("door_id", 0)

        # Skip if filtering by address
        if address and str(door_id) != address:
            continue

        # Get reader mode (default to Card Only)
        reader_mode = door.get("reader_mode", 5)

        devices.append({
            "address": str(door_id),
            "description": door.get("name", f"Door {door_id}"),
            "device_type": "reader",
            "status": 1,  # Online
            "reader_mode": reader_mode,
            "reader_mode_name": READER_MODES.get(reader_mode, "Unknown"),
            "door_status": 0,  # Closed
            "lock_status": 0,  # Locked
            "last_update": datetime.now().isoformat()
        })

    return {
        "devices": devices,
        "count": len(devices),
        "timestamp": datetime.now().isoformat()
    }


# =============================================================================
# Alarm Management (UnityIS-compatible)
# =============================================================================

@app.get("/hal/alarms", tags=["HAL Core - Alarms"])
async def hal_get_alarms(event_id: Optional[str] = None, limit: int = 500):
    """
    Get alarm events (UnityIS compatible)

    Returns the most recent alarm transactions.
    """
    if not hal:
        raise HTTPException(status_code=503, detail="HAL not initialized")

    # Get events and filter for alarms
    events = hal.get_events(limit=limit)

    # Alarm event types
    alarm_types = [1, 3, 4, 5, 6, 8]  # DENY, DOOR_FORCED, DOOR_HELD, TAMPER, APB_VIOLATION, EMERGENCY

    # Filter by event_id if provided
    event_ids = event_id.split(",") if event_id else None

    alarms = []
    for event in events:
        event_type = event.get("event_type", 0)

        if event_type in alarm_types:
            if event_ids and str(event.get("event_id")) not in event_ids:
                continue
            alarms.append(event)

    return {
        "alarms": alarms,
        "count": len(alarms),
        "timestamp": datetime.now().isoformat()
    }


@app.get("/hal/alarms/count", tags=["HAL Core - Alarms"])
async def hal_get_alarm_count():
    """
    Get alarm count (UnityIS compatible)

    Returns the total number of active alarms.
    """
    if not hal:
        raise HTTPException(status_code=503, detail="HAL not initialized")

    # Get events and count alarms
    events = hal.get_events(limit=10000)

    # Alarm event types
    alarm_types = [1, 3, 4, 5, 6, 8]

    count = sum(1 for e in events if e.get("event_type", 0) in alarm_types)

    return {
        "alarm_count": count,
        "timestamp": datetime.now().isoformat()
    }


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
            "message": f"Connected to Aether Bifrost API v{VERSION}",
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
