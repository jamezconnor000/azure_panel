#!/usr/bin/env python3
"""
HAL GUI Server v2 - Complete Edition
Modern Web Interface with I/O Control, Reader Health, and Azure Panel Monitoring
Like Lenel OnGuard but BETTER!
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import asyncio
import json

# Import our modules
from io_monitoring import (
    get_panel_io_status, get_reader_health, get_panel_health,
    PanelIOStatus, ReaderHealth, PanelHealth
)
from io_control import (
    control_door, control_output, control_relay, mass_control, execute_macro,
    get_active_overrides, clear_override,
    DoorControl, OutputControl, RelayControl, MassControl,
    ControlResult, IOOverride, EXAMPLE_MACROS
)

# Import v2.1 API router
try:
    from api_v2_1 import router as api_v2_1_router
    v2_1_available = True
except ImportError:
    v2_1_available = False

app = FastAPI(
    title="AetherAccess Control Panel API v2.1",
    description="Professional access control with I/O monitoring & control, user management, authentication, door configuration",
    version="2.1.0"
)

# Include v2.1 API routes
if v2_1_available:
    app.include_router(api_v2_1_router)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Connection manager for WebSocket
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass

manager = ConnectionManager()

# =============================================================================
# AZURE PANEL I/O MONITORING
# =============================================================================

@app.get("/api/v1/panels/{panel_id}/io", response_model=PanelIOStatus)
async def get_panel_io(panel_id: int):
    """
    Get complete I/O status for an Azure panel

    Returns:
    - All inputs (door contacts, REX, tampers, etc.)
    - All outputs (strikes, LEDs, buzzers, etc.)
    - All relays
    - Current states
    - Activation counts
    """
    return get_panel_io_status(panel_id)

@app.get("/api/v1/panels/{panel_id}/health", response_model=PanelHealth)
async def get_panel_health_status(panel_id: int):
    """
    Get comprehensive health metrics for an Azure panel

    Includes:
    - Power status (main + battery)
    - Network health
    - I/O health
    - Database health
    - Recent errors/warnings
    """
    return get_panel_health(panel_id)

# =============================================================================
# READER HEALTH MONITORING
# =============================================================================

@app.get("/api/v1/readers/{reader_id}/health", response_model=ReaderHealth)
async def get_reader_health_status(reader_id: int):
    """
    Get comprehensive health assessment for a reader

    Includes:
    - Communication health
    - Secure channel health
    - Hardware health (power, temp, tamper)
    - Card reader health
    - Firmware status
    - Recommendations
    """
    return get_reader_health(reader_id)

@app.get("/api/v1/readers/health/summary")
async def get_all_readers_health():
    """Get health summary for all readers"""
    # TODO: Get actual reader list
    reader_ids = [1, 2, 3]
    health_data = []

    for reader_id in reader_ids:
        health = get_reader_health(reader_id)
        health_data.append({
            "reader_id": reader_id,
            "reader_name": health.reader_name,
            "overall_health": health.overall_health,
            "health_score": health.health_score,
            "issues": len(health.recent_errors) + len(health.warnings)
        })

    return {"readers": health_data, "timestamp": datetime.now()}

# =============================================================================
# DOOR CONTROL (Lenel-style)
# =============================================================================

@app.post("/api/v1/doors/{door_id}/unlock")
async def unlock_door(door_id: int, duration_seconds: Optional[int] = None, reason: Optional[str] = None):
    """
    Unlock a door

    Parameters:
    - door_id: Door to unlock
    - duration_seconds: If specified, unlock for this duration (momentary unlock)
    - reason: Optional reason for audit log
    """
    door_control = DoorControl(
        door_id=door_id,
        action="UNLOCK_MOMENTARY" if duration_seconds else "UNLOCK",
        duration_seconds=duration_seconds,
        reason=reason,
        initiated_by="API"  # TODO: Get from authentication
    )

    result = await control_door(door_control)

    # Broadcast to WebSocket clients
    await manager.broadcast({
        "type": "door_control",
        "action": "unlock",
        "door_id": door_id,
        "result": result.dict(),
        "timestamp": datetime.now().isoformat()
    })

    return result

@app.post("/api/v1/doors/{door_id}/lock")
async def lock_door(door_id: int, reason: Optional[str] = None):
    """Lock a door"""
    door_control = DoorControl(
        door_id=door_id,
        action="LOCK",
        reason=reason,
        initiated_by="API"
    )

    result = await control_door(door_control)

    await manager.broadcast({
        "type": "door_control",
        "action": "lock",
        "door_id": door_id,
        "result": result.dict(),
        "timestamp": datetime.now().isoformat()
    })

    return result

@app.post("/api/v1/doors/{door_id}/lockdown")
async def lockdown_door(door_id: int, reason: str):
    """
    Put door in LOCKDOWN mode

    Lockdown mode:
    - Door locked
    - All access disabled
    - Manual unlock only
    """
    door_control = DoorControl(
        door_id=door_id,
        action="LOCKDOWN",
        reason=reason,
        initiated_by="API"
    )

    result = await control_door(door_control)

    await manager.broadcast({
        "type": "door_control",
        "action": "lockdown",
        "door_id": door_id,
        "result": result.dict(),
        "timestamp": datetime.now().isoformat()
    })

    return result

@app.post("/api/v1/doors/{door_id}/release")
async def release_door(door_id: int):
    """Release door lockdown/unlock - return to normal operation"""
    door_control = DoorControl(
        door_id=door_id,
        action="RELEASE",
        reason="Release override",
        initiated_by="API"
    )

    result = await control_door(door_control)

    await manager.broadcast({
        "type": "door_control",
        "action": "release",
        "door_id": door_id,
        "result": result.dict(),
        "timestamp": datetime.now().isoformat()
    })

    return result

# =============================================================================
# OUTPUT CONTROL
# =============================================================================

@app.post("/api/v1/outputs/{output_id}/activate")
async def activate_output(output_id: int, duration_ms: Optional[int] = None):
    """
    Activate an output

    Parameters:
    - output_id: Output to activate
    - duration_ms: If specified, activate for this duration (pulse mode)
    """
    from io_control import ControlAction

    output_control = OutputControl(
        output_id=output_id,
        action=ControlAction.PULSE if duration_ms else ControlAction.ACTIVATE,
        duration_ms=duration_ms
    )

    result = await control_output(output_control)

    await manager.broadcast({
        "type": "output_control",
        "action": "activate",
        "output_id": output_id,
        "result": result.dict(),
        "timestamp": datetime.now().isoformat()
    })

    return result

@app.post("/api/v1/outputs/{output_id}/deactivate")
async def deactivate_output(output_id: int):
    """Deactivate an output"""
    from io_control import ControlAction

    output_control = OutputControl(
        output_id=output_id,
        action=ControlAction.DEACTIVATE
    )

    result = await control_output(output_control)

    await manager.broadcast({
        "type": "output_control",
        "action": "deactivate",
        "output_id": output_id,
        "result": result.dict(),
        "timestamp": datetime.now().isoformat()
    })

    return result

@app.post("/api/v1/outputs/{output_id}/pulse")
async def pulse_output(output_id: int, duration_ms: int = 1000):
    """Pulse an output for specified duration"""
    from io_control import ControlAction

    output_control = OutputControl(
        output_id=output_id,
        action=ControlAction.PULSE,
        duration_ms=duration_ms
    )

    result = await control_output(output_control)

    await manager.broadcast({
        "type": "output_control",
        "action": "pulse",
        "output_id": output_id,
        "duration_ms": duration_ms,
        "result": result.dict(),
        "timestamp": datetime.now().isoformat()
    })

    return result

@app.post("/api/v1/outputs/{output_id}/toggle")
async def toggle_output(output_id: int):
    """Toggle output state"""
    from io_control import ControlAction

    output_control = OutputControl(
        output_id=output_id,
        action=ControlAction.TOGGLE
    )

    result = await control_output(output_control)

    await manager.broadcast({
        "type": "output_control",
        "action": "toggle",
        "output_id": output_id,
        "result": result.dict(),
        "timestamp": datetime.now().isoformat()
    })

    return result

# =============================================================================
# RELAY CONTROL
# =============================================================================

@app.post("/api/v1/relays/{relay_id}/activate")
async def activate_relay(relay_id: int, duration_ms: Optional[int] = None):
    """Activate a relay"""
    from io_control import ControlAction

    relay_control = RelayControl(
        relay_id=relay_id,
        action=ControlAction.PULSE if duration_ms else ControlAction.ACTIVATE,
        duration_ms=duration_ms
    )

    result = await control_relay(relay_control)

    await manager.broadcast({
        "type": "relay_control",
        "action": "activate",
        "relay_id": relay_id,
        "result": result.dict(),
        "timestamp": datetime.now().isoformat()
    })

    return result

@app.post("/api/v1/relays/{relay_id}/deactivate")
async def deactivate_relay(relay_id: int):
    """Deactivate a relay"""
    from io_control import ControlAction

    relay_control = RelayControl(
        relay_id=relay_id,
        action=ControlAction.DEACTIVATE
    )

    result = await control_relay(relay_control)

    await manager.broadcast({
        "type": "relay_control",
        "action": "deactivate",
        "relay_id": relay_id,
        "result": result.dict(),
        "timestamp": datetime.now().isoformat()
    })

    return result

# =============================================================================
# MASS CONTROL (Emergency Operations)
# =============================================================================

@app.post("/api/v1/control/lockdown")
async def emergency_lockdown(reason: str, initiated_by: str = "API"):
    """
    EMERGENCY LOCKDOWN

    Actions:
    - Lock ALL doors
    - Disable all outputs
    - Alert all operators
    """
    mass_ctrl = MassControl(
        target_type="ALL_DOORS",
        action="LOCKDOWN",
        reason=reason,
        initiated_by=initiated_by
    )

    result = await mass_control(mass_ctrl)

    await manager.broadcast({
        "type": "mass_control",
        "action": "EMERGENCY_LOCKDOWN",
        "result": result.dict(),
        "timestamp": datetime.now().isoformat(),
        "priority": "CRITICAL"
    })

    return result

@app.post("/api/v1/control/unlock-all")
async def emergency_unlock_all(reason: str, initiated_by: str = "API"):
    """
    EMERGENCY UNLOCK ALL

    Actions:
    - Unlock ALL doors
    - For evacuation scenarios
    """
    mass_ctrl = MassControl(
        target_type="ALL_DOORS",
        action="UNLOCK_ALL",
        reason=reason,
        initiated_by=initiated_by
    )

    result = await mass_control(mass_ctrl)

    await manager.broadcast({
        "type": "mass_control",
        "action": "EMERGENCY_UNLOCK",
        "result": result.dict(),
        "timestamp": datetime.now().isoformat(),
        "priority": "CRITICAL"
    })

    return result

@app.post("/api/v1/control/normal")
async def return_to_normal(initiated_by: str = "API"):
    """Return all systems to normal operation"""
    mass_ctrl = MassControl(
        target_type="PANEL",
        action="NORMAL",
        reason="Return to normal operation",
        initiated_by=initiated_by
    )

    result = await mass_control(mass_ctrl)

    await manager.broadcast({
        "type": "mass_control",
        "action": "NORMAL_OPERATION",
        "result": result.dict(),
        "timestamp": datetime.now().isoformat()
    })

    return result

# =============================================================================
# MACRO CONTROL (Lenel-style)
# =============================================================================

@app.get("/api/v1/macros")
async def list_macros():
    """List all available control macros"""
    return {"macros": EXAMPLE_MACROS}

@app.post("/api/v1/macros/{macro_id}/execute")
async def execute_control_macro(macro_id: int, initiated_by: str = "API"):
    """
    Execute a control macro

    Examples:
    - 1: Emergency Lockdown
    - 2: Fire Evacuation
    - 3: After Hours Mode
    - 4: Morning Unlock
    """
    results = await execute_macro(macro_id, initiated_by)

    await manager.broadcast({
        "type": "macro_executed",
        "macro_id": macro_id,
        "results": [r.dict() for r in results],
        "timestamp": datetime.now().isoformat()
    })

    return {"macro_id": macro_id, "results": results}

# =============================================================================
# OVERRIDE MANAGEMENT
# =============================================================================

@app.get("/api/v1/overrides", response_model=List[IOOverride])
async def get_overrides():
    """Get all active I/O overrides"""
    return await get_active_overrides()

@app.delete("/api/v1/overrides/{override_id}")
async def clear_io_override(override_id: int):
    """Clear an I/O override - return to automatic control"""
    result = await clear_override(override_id)

    await manager.broadcast({
        "type": "override_cleared",
        "override_id": override_id,
        "result": result.dict(),
        "timestamp": datetime.now().isoformat()
    })

    return result

# =============================================================================
# WEBSOCKET
# =============================================================================

@app.websocket("/ws/live")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time I/O updates, control events, health changes"""
    await manager.connect(websocket)

    try:
        await websocket.send_json({
            "type": "connected",
            "message": "Connected to Aether_Access Control Panel v2",
            "features": ["io_monitoring", "io_control", "reader_health", "panel_health"],
            "timestamp": datetime.now().isoformat()
        })

        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            # Handle client requests
            if message.get("action") == "subscribe":
                await websocket.send_json({
                    "type": "subscription_confirmed",
                    "topics": message.get("topics", []),
                    "timestamp": datetime.now().isoformat()
                })

    except WebSocketDisconnect:
        manager.disconnect(websocket)

# =============================================================================
# BACKGROUND TASKS
# =============================================================================

async def io_monitoring_loop():
    """Background task to monitor I/O and push updates"""
    while True:
        await asyncio.sleep(2)  # Every 2 seconds

        # Simulate I/O change event
        await manager.broadcast({
            "type": "io_change",
            "event": {
                "panel_id": 1,
                "input_id": 1,
                "name": "Main Door Contact",
                "new_state": "ACTIVE",
                "timestamp": datetime.now().isoformat()
            }
        })

@app.on_event("startup")
async def startup_event():
    """Start background tasks"""
    asyncio.create_task(io_monitoring_loop())

    print("="*80)
    print(" Aether_Access Control Panel v2 - Complete Edition".center(80))
    print("="*80)
    print(" API Documentation: http://localhost:8080/docs")
    print(" WebSocket: ws://localhost:8080/ws/live")
    print("")
    print(" Features:")
    print("   ✓ Azure Panel I/O Monitoring")
    print("   ✓ Reader Health Monitoring")
    print("   ✓ I/O Control (Doors, Outputs, Relays)")
    print("   ✓ Mass Control Operations")
    print("   ✓ Control Macros")
    print("   ✓ Override Management")
    print("   ✓ Real-time WebSocket Updates")
    print("="*80)

# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8080,
        log_level="info"
    )
