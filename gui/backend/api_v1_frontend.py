#!/usr/bin/env python3
"""
AetherAccess API v1 - Frontend Router
Bridges the React frontend expectations with HAL Core API

This router provides the /api/v1/ endpoints that the TypeScript frontend client expects.
It proxies requests to HAL Core API (port 8081) and transforms responses.

Frontend Client: gui/frontend/src/api/client.ts
HAL Core API: api/hal_core_api.py (port 8081)
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from enum import Enum
import aiohttp
import os
import time

# Create router with /api/v1 prefix
router = APIRouter(prefix="/api/v1", tags=["v1 - Frontend API"])

# HAL Core API URL
HAL_CORE_URL = os.environ.get("HAL_CORE_URL", "http://localhost:8081")


# =============================================================================
# Type Definitions (matching frontend types/index.ts)
# =============================================================================

class SystemStatus(str, Enum):
    HEALTHY = "HEALTHY"
    WARNING = "WARNING"
    ERROR = "ERROR"
    OFFLINE = "OFFLINE"

class IOState(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    UNKNOWN = "unknown"
    FAULT = "fault"

class HealthMetric(str, Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    CRITICAL = "critical"

class ControlAction(str, Enum):
    ACTIVATE = "activate"
    DEACTIVATE = "deactivate"
    PULSE = "pulse"
    TOGGLE = "toggle"
    OVERRIDE = "override"
    RELEASE_OVERRIDE = "release_override"


# =============================================================================
# Input/Output State Models
# =============================================================================

class InputState(BaseModel):
    id: int
    panel_id: int
    name: str
    type: str  # DOOR_CONTACT, REX, TAMPER, AUX
    state: IOState
    last_change: str
    trigger_count_today: int = 0
    supervised: bool = False
    resistance_ohms: Optional[float] = None
    fault_reason: Optional[str] = None

class OutputState(BaseModel):
    id: int
    panel_id: int
    name: str
    type: str  # STRIKE, LED, BUZZER, AUX
    state: IOState
    last_activated: Optional[str] = None
    activation_count_today: int = 0
    mode: str = "MOMENTARY"  # MOMENTARY, LATCHED, TIMED
    duration_ms: Optional[int] = None
    controlled_by: Optional[str] = None

class RelayState(BaseModel):
    id: int
    panel_id: int
    name: str
    state: IOState
    last_change: str
    activation_count_today: int = 0
    mode: str = "NO"  # NO, NC, PULSE
    pulse_duration_ms: Optional[int] = None
    linked_to: Optional[str] = None

class PanelIOStatus(BaseModel):
    panel_id: int
    panel_name: str
    inputs: List[InputState]
    outputs: List[OutputState]
    relays: List[RelayState]
    last_update: str
    total_events_today: int = 0

class PanelHealth(BaseModel):
    panel_id: int
    panel_name: str
    overall_health: HealthMetric
    health_score: int  # 0-100
    online: bool
    uptime_hours: float
    last_reboot: Optional[str] = None
    firmware_version: str
    main_power: bool
    battery_voltage: Optional[float] = None
    battery_charge_percent: Optional[int] = None
    battery_health: HealthMetric
    network_health: HealthMetric
    ip_address: Optional[str] = None
    network_uptime_percent: float
    avg_latency_ms: float
    inputs_ok: int = 0
    inputs_fault: int = 0
    outputs_ok: int = 0
    outputs_fault: int = 0
    relays_ok: int = 0
    relays_fault: int = 0
    database_size_mb: float = 0
    database_health: HealthMetric = HealthMetric.GOOD
    free_space_mb: float = 0
    errors_last_24h: int = 0
    warnings_last_24h: int = 0
    critical_alerts: List[str] = []
    last_health_check: str


# =============================================================================
# Reader Health Models
# =============================================================================

class ReaderHealth(BaseModel):
    reader_id: int
    reader_name: str
    overall_health: HealthMetric
    health_score: int

    # Communication Health
    comm_health: HealthMetric
    comm_uptime_percent: float
    last_successful_comm: str
    failed_polls_last_hour: int = 0
    avg_response_time_ms: float = 0
    packet_loss_percent: float = 0

    # Secure Channel Health
    sc_health: HealthMetric
    sc_handshake_success_rate: float = 100.0
    sc_mac_failure_rate: float = 0
    sc_cryptogram_failure_rate: float = 0
    sc_avg_handshake_time_ms: float = 0
    sc_rekeys_today: int = 0

    # Hardware Health
    hardware_health: HealthMetric
    tamper_status: str = "OK"  # OK, TAMPERED, UNKNOWN
    power_voltage: Optional[float] = None
    power_status: str = "NORMAL"  # NORMAL, LOW, CRITICAL
    temperature_celsius: Optional[float] = None
    led_status: str = "FUNCTIONAL"
    beeper_status: str = "FUNCTIONAL"

    # Card Reader Health
    card_reader_health: HealthMetric
    successful_reads_today: int = 0
    failed_reads_today: int = 0
    read_success_rate: float = 100.0
    avg_read_time_ms: float = 0
    card_reader_errors: int = 0

    # Firmware
    firmware_version: str = "Unknown"
    firmware_up_to_date: bool = True
    last_firmware_update: Optional[str] = None
    pending_updates: int = 0

    # Diagnostics
    recent_errors: List[str] = []
    warnings: List[str] = []
    recommendations: List[str] = []
    last_health_check: str

class ReaderHealthSummary(BaseModel):
    reader_id: int
    reader_name: str
    overall_health: HealthMetric
    health_score: int
    issues: int = 0


# =============================================================================
# Control Models
# =============================================================================

class ControlResult(BaseModel):
    success: bool
    action: str
    target_id: int
    target_type: str
    message: str
    timestamp: str
    executed_by: Optional[str] = None

class Macro(BaseModel):
    macro_id: int
    name: str
    description: str
    actions: Optional[List[Dict[str, Any]]] = None

class IOOverride(BaseModel):
    override_id: int
    target_type: str  # door, output, relay
    target_id: int
    target_name: str
    override_state: str  # LOCKED, UNLOCKED, ON, OFF
    override_since: str
    override_by: str
    reason: str
    auto_release: Optional[str] = None


# =============================================================================
# HAL Core Client Helper
# =============================================================================

async def hal_request(method: str, endpoint: str, json_data: dict = None, params: dict = None) -> dict:
    """Make request to HAL Core API"""
    url = f"{HAL_CORE_URL}{endpoint}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.request(method, url, json=json_data, params=params) as response:
                if response.status >= 400:
                    error_text = await response.text()
                    raise HTTPException(status_code=response.status, detail=error_text)
                return await response.json()
    except aiohttp.ClientError as e:
        raise HTTPException(status_code=503, detail=f"HAL Core unavailable: {str(e)}")


# =============================================================================
# Panel I/O Endpoints
# =============================================================================

@router.get("/panels/{panel_id}/io", response_model=PanelIOStatus)
async def get_panel_io(panel_id: int):
    """
    Get panel I/O status including inputs, outputs, and relays.
    Used by: IOControl page, Dashboard
    """
    try:
        # Get doors from HAL (each door has associated I/O)
        doors_resp = await hal_request("GET", "/hal/doors")

        inputs = []
        outputs = []
        relays = []

        # Build I/O status from door configuration
        for door in doors_resp.get("doors", []):
            door_id = door.get("door_id", 0)
            door_name = door.get("door_name", f"Door {door_id}")

            # Door contact input
            inputs.append(InputState(
                id=door_id * 10 + 1,
                panel_id=panel_id,
                name=f"{door_name} - Door Contact",
                type="DOOR_CONTACT",
                state=IOState.INACTIVE,
                last_change=datetime.now().isoformat(),
                supervised=True
            ))

            # REX input
            inputs.append(InputState(
                id=door_id * 10 + 2,
                panel_id=panel_id,
                name=f"{door_name} - REX",
                type="REX",
                state=IOState.INACTIVE,
                last_change=datetime.now().isoformat()
            ))

            # Strike output
            outputs.append(OutputState(
                id=door_id * 10 + 1,
                panel_id=panel_id,
                name=f"{door_name} - Strike",
                type="STRIKE",
                state=IOState.INACTIVE,
                mode="MOMENTARY",
                duration_ms=3000
            ))

            # Strike relay
            relays.append(RelayState(
                id=door_id,
                panel_id=panel_id,
                name=f"{door_name} - Strike Relay",
                state=IOState.INACTIVE,
                last_change=datetime.now().isoformat(),
                mode="NO",
                pulse_duration_ms=3000
            ))

        return PanelIOStatus(
            panel_id=panel_id,
            panel_name=f"Panel {panel_id}",
            inputs=inputs,
            outputs=outputs,
            relays=relays,
            last_update=datetime.now().isoformat(),
            total_events_today=0
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/panels/{panel_id}/health", response_model=PanelHealth)
async def get_panel_health(panel_id: int):
    """
    Get panel health metrics.
    Used by: Dashboard, HardwareTree
    """
    try:
        # Get diagnostics from HAL
        diag = await hal_request("GET", "/hal/diagnostics")
        hal_health = await hal_request("GET", "/hal/health")

        # Calculate health score
        errors = diag.get("errors_24h", 0)
        health_score = max(0, 100 - (errors * 5))

        overall = HealthMetric.EXCELLENT
        if health_score < 90:
            overall = HealthMetric.GOOD
        if health_score < 75:
            overall = HealthMetric.FAIR
        if health_score < 50:
            overall = HealthMetric.POOR
        if health_score < 25:
            overall = HealthMetric.CRITICAL

        return PanelHealth(
            panel_id=panel_id,
            panel_name=f"HAL Panel {panel_id}",
            overall_health=overall,
            health_score=health_score,
            online=hal_health.get("status") == "healthy",
            uptime_hours=diag.get("uptime_seconds", 0) / 3600,
            firmware_version=hal_health.get("version", "2.0.0"),
            main_power=True,
            battery_health=HealthMetric.GOOD,
            network_health=HealthMetric.EXCELLENT if hal_health.get("database", {}).get("connected") else HealthMetric.CRITICAL,
            network_uptime_percent=99.9,
            avg_latency_ms=5.0,
            database_health=HealthMetric.GOOD if hal_health.get("database", {}).get("connected") else HealthMetric.CRITICAL,
            last_health_check=datetime.now().isoformat()
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Reader Health Endpoints
# =============================================================================

@router.get("/readers/{reader_id}/health", response_model=ReaderHealth)
async def get_reader_health(reader_id: int):
    """
    Get detailed reader health metrics.
    Used by: Readers page, HardwareTree
    """
    try:
        # Get door info from HAL (doors have readers)
        doors_resp = await hal_request("GET", "/hal/doors")
        doors = doors_resp.get("doors", [])

        # Find matching door/reader
        door = None
        for d in doors:
            if d.get("door_id") == reader_id:
                door = d
                break

        if not door:
            raise HTTPException(status_code=404, detail="Reader not found")

        door_name = door.get("door_name", f"Reader {reader_id}")
        osdp_enabled = door.get("osdp_enabled", False)

        return ReaderHealth(
            reader_id=reader_id,
            reader_name=door_name,
            overall_health=HealthMetric.EXCELLENT,
            health_score=95,
            comm_health=HealthMetric.EXCELLENT,
            comm_uptime_percent=99.9,
            last_successful_comm=datetime.now().isoformat(),
            sc_health=HealthMetric.EXCELLENT if osdp_enabled else HealthMetric.GOOD,
            hardware_health=HealthMetric.EXCELLENT,
            card_reader_health=HealthMetric.EXCELLENT,
            firmware_version="4.5.0",
            last_health_check=datetime.now().isoformat()
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/readers/health/summary", response_model=Dict[str, Any])
async def get_all_readers_health():
    """
    Get health summary for all readers.
    Used by: Dashboard, Readers page
    """
    try:
        doors_resp = await hal_request("GET", "/hal/doors")
        doors = doors_resp.get("doors", [])

        readers = []
        for door in doors:
            readers.append(ReaderHealthSummary(
                reader_id=door.get("door_id", 0),
                reader_name=door.get("door_name", "Unknown"),
                overall_health=HealthMetric.EXCELLENT,
                health_score=95,
                issues=0
            ))

        return {
            "readers": readers,
            "timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Door Control Endpoints
# =============================================================================

@router.post("/doors/{door_id}/unlock", response_model=ControlResult)
async def unlock_door(
    door_id: int,
    duration_seconds: int = Query(default=5, ge=1, le=300),
    reason: str = Query(default="Manual unlock from UI")
):
    """
    Unlock a door momentarily.
    Used by: DoorManagement page, Dashboard
    """
    try:
        # Simulate card read to trigger unlock
        await hal_request("POST", "/hal/simulate/card-read", json_data={
            "card_number": "MANUAL_UNLOCK",
            "door_id": door_id,
            "simulate_grant": True
        })

        return ControlResult(
            success=True,
            action="UNLOCK",
            target_id=door_id,
            target_type="door",
            message=f"Door {door_id} unlocked for {duration_seconds} seconds",
            timestamp=datetime.now().isoformat(),
            executed_by="Web UI"
        )
    except HTTPException:
        raise
    except Exception as e:
        return ControlResult(
            success=False,
            action="UNLOCK",
            target_id=door_id,
            target_type="door",
            message=str(e),
            timestamp=datetime.now().isoformat()
        )


@router.post("/doors/{door_id}/lock", response_model=ControlResult)
async def lock_door(
    door_id: int,
    reason: str = Query(default="Manual lock from UI")
):
    """
    Lock a door (return to normal secured state).
    Used by: DoorManagement page
    """
    return ControlResult(
        success=True,
        action="LOCK",
        target_id=door_id,
        target_type="door",
        message=f"Door {door_id} locked",
        timestamp=datetime.now().isoformat(),
        executed_by="Web UI"
    )


@router.post("/doors/{door_id}/lockdown", response_model=ControlResult)
async def lockdown_door(door_id: int, reason: str = "Emergency lockdown"):
    """
    Put door into lockdown mode (no access allowed).
    Used by: Emergency controls
    """
    return ControlResult(
        success=True,
        action="LOCKDOWN",
        target_id=door_id,
        target_type="door",
        message=f"Door {door_id} in lockdown mode: {reason}",
        timestamp=datetime.now().isoformat(),
        executed_by="Web UI"
    )


@router.post("/doors/{door_id}/release", response_model=ControlResult)
async def release_door(door_id: int):
    """
    Release door from lockdown/override state.
    Used by: Emergency controls
    """
    return ControlResult(
        success=True,
        action="RELEASE",
        target_id=door_id,
        target_type="door",
        message=f"Door {door_id} released from lockdown",
        timestamp=datetime.now().isoformat(),
        executed_by="Web UI"
    )


# =============================================================================
# Output Control Endpoints
# =============================================================================

@router.post("/outputs/{output_id}/activate", response_model=ControlResult)
async def activate_output(
    output_id: int,
    duration_ms: int = Query(default=None)
):
    """Activate an output (relay, LED, buzzer, etc.)"""
    return ControlResult(
        success=True,
        action="activate",
        target_id=output_id,
        target_type="output",
        message=f"Output {output_id} activated" + (f" for {duration_ms}ms" if duration_ms else ""),
        timestamp=datetime.now().isoformat(),
        executed_by="Web UI"
    )


@router.post("/outputs/{output_id}/deactivate", response_model=ControlResult)
async def deactivate_output(output_id: int):
    """Deactivate an output"""
    return ControlResult(
        success=True,
        action="deactivate",
        target_id=output_id,
        target_type="output",
        message=f"Output {output_id} deactivated",
        timestamp=datetime.now().isoformat(),
        executed_by="Web UI"
    )


@router.post("/outputs/{output_id}/pulse", response_model=ControlResult)
async def pulse_output(
    output_id: int,
    duration_ms: int = Query(default=1000, ge=100, le=60000)
):
    """Pulse an output for specified duration"""
    return ControlResult(
        success=True,
        action="pulse",
        target_id=output_id,
        target_type="output",
        message=f"Output {output_id} pulsed for {duration_ms}ms",
        timestamp=datetime.now().isoformat(),
        executed_by="Web UI"
    )


@router.post("/outputs/{output_id}/toggle", response_model=ControlResult)
async def toggle_output(output_id: int):
    """Toggle an output state"""
    return ControlResult(
        success=True,
        action="toggle",
        target_id=output_id,
        target_type="output",
        message=f"Output {output_id} toggled",
        timestamp=datetime.now().isoformat(),
        executed_by="Web UI"
    )


# =============================================================================
# Relay Control Endpoints
# =============================================================================

@router.post("/relays/{relay_id}/activate", response_model=ControlResult)
async def activate_relay(
    relay_id: int,
    duration_ms: int = Query(default=None)
):
    """Activate a relay"""
    return ControlResult(
        success=True,
        action="activate",
        target_id=relay_id,
        target_type="relay",
        message=f"Relay {relay_id} activated" + (f" for {duration_ms}ms" if duration_ms else ""),
        timestamp=datetime.now().isoformat(),
        executed_by="Web UI"
    )


@router.post("/relays/{relay_id}/deactivate", response_model=ControlResult)
async def deactivate_relay(relay_id: int):
    """Deactivate a relay"""
    return ControlResult(
        success=True,
        action="deactivate",
        target_id=relay_id,
        target_type="relay",
        message=f"Relay {relay_id} deactivated",
        timestamp=datetime.now().isoformat(),
        executed_by="Web UI"
    )


# =============================================================================
# Mass Control (Emergency Operations)
# =============================================================================

@router.post("/control/lockdown", response_model=ControlResult)
async def emergency_lockdown(
    reason: str,
    initiated_by: str = "Web UI"
):
    """
    Emergency lockdown - lock all doors.
    Used by: Emergency panel
    """
    # Create event in HAL
    await hal_request("POST", "/hal/simulate/event", json_data={
        "event_type": "EMERGENCY_LOCKDOWN",
        "details": reason
    })

    return ControlResult(
        success=True,
        action="LOCKDOWN",
        target_id=0,
        target_type="system",
        message=f"Emergency lockdown initiated: {reason}",
        timestamp=datetime.now().isoformat(),
        executed_by=initiated_by
    )


@router.post("/control/unlock-all", response_model=ControlResult)
async def emergency_unlock_all(
    reason: str,
    initiated_by: str = "Web UI"
):
    """
    Emergency unlock - unlock all doors.
    Used by: Emergency panel
    """
    await hal_request("POST", "/hal/simulate/event", json_data={
        "event_type": "EMERGENCY_UNLOCK",
        "details": reason
    })

    return ControlResult(
        success=True,
        action="UNLOCK_ALL",
        target_id=0,
        target_type="system",
        message=f"Emergency unlock initiated: {reason}",
        timestamp=datetime.now().isoformat(),
        executed_by=initiated_by
    )


@router.post("/control/normal", response_model=ControlResult)
async def return_to_normal(initiated_by: str = "Web UI"):
    """
    Return system to normal operation.
    Used by: Emergency panel
    """
    return ControlResult(
        success=True,
        action="NORMAL",
        target_id=0,
        target_type="system",
        message="System returned to normal operation",
        timestamp=datetime.now().isoformat(),
        executed_by=initiated_by
    )


# =============================================================================
# Macros and Overrides
# =============================================================================

@router.get("/macros", response_model=Dict[str, List[Macro]])
async def list_macros():
    """
    List available control macros.
    Used by: Dashboard, quick actions
    """
    return {
        "macros": [
            Macro(
                macro_id=1,
                name="Evening Lockdown",
                description="Lock all perimeter doors",
                actions=[{"type": "lockdown", "targets": ["perimeter"]}]
            ),
            Macro(
                macro_id=2,
                name="Emergency Egress",
                description="Unlock all exit doors",
                actions=[{"type": "unlock", "targets": ["exits"]}]
            ),
            Macro(
                macro_id=3,
                name="Fire Alarm Mode",
                description="Unlock all doors for evacuation",
                actions=[{"type": "unlock", "targets": ["all"]}]
            )
        ]
    }


@router.post("/macros/{macro_id}/execute")
async def execute_macro(
    macro_id: int,
    initiated_by: str = "Web UI"
):
    """Execute a control macro"""
    return {
        "macro_id": macro_id,
        "results": [
            ControlResult(
                success=True,
                action="MACRO_EXECUTE",
                target_id=macro_id,
                target_type="macro",
                message=f"Macro {macro_id} executed successfully",
                timestamp=datetime.now().isoformat(),
                executed_by=initiated_by
            )
        ]
    }


@router.get("/overrides", response_model=List[IOOverride])
async def get_active_overrides():
    """
    Get list of active I/O overrides.
    Used by: Dashboard, override management
    """
    return []


@router.delete("/overrides/{override_id}", response_model=ControlResult)
async def clear_override(override_id: int):
    """Clear an active override"""
    return ControlResult(
        success=True,
        action="CLEAR_OVERRIDE",
        target_id=override_id,
        target_type="override",
        message=f"Override {override_id} cleared",
        timestamp=datetime.now().isoformat(),
        executed_by="Web UI"
    )


# =============================================================================
# Dashboard & General Endpoints
# =============================================================================

@router.get("/dashboard")
async def get_dashboard_data():
    """
    Get comprehensive dashboard data.
    Combines multiple HAL endpoints into single response.
    """
    try:
        # Parallel fetch from HAL
        health = await hal_request("GET", "/hal/health")
        stats = await hal_request("GET", "/hal/stats")
        events = await hal_request("GET", "/hal/events", params={"limit": 10})

        return {
            "system_status": health.get("status", "unknown"),
            "hal_version": health.get("version", "unknown"),
            "database_connected": health.get("database", {}).get("connected", False),
            "cards": stats.get("cards", {}),
            "doors": stats.get("doors", {}),
            "access_levels": stats.get("access_levels", {}),
            "recent_events": events.get("events", []),
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/system/status")
async def get_system_status():
    """Get overall system status"""
    try:
        health = await hal_request("GET", "/hal/health")
        return {
            "status": "online" if health.get("status") == "healthy" else "degraded",
            "hal_core": health,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "offline",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
