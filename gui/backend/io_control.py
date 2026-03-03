"""
I/O Control Module - Lenel-style I/O Control
Provides comprehensive control over panel inputs, outputs, and relays
Similar to Lenel OnGuard but better
"""

from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from enum import Enum

# =============================================================================
# I/O Control Models
# =============================================================================

class ControlAction(str, Enum):
    ACTIVATE = "activate"
    DEACTIVATE = "deactivate"
    PULSE = "pulse"
    TOGGLE = "toggle"
    OVERRIDE = "override"
    RELEASE_OVERRIDE = "release_override"

class ControlResult(BaseModel):
    """Result of an I/O control operation"""
    success: bool
    action: ControlAction
    target_id: int
    target_type: str  # output, relay, door
    message: str
    timestamp: datetime
    executed_by: Optional[str] = None

class DoorControl(BaseModel):
    """Door control operations"""
    door_id: int
    action: str  # UNLOCK, LOCK, UNLOCK_MOMENTARY, UNLOCK_TIMED, LOCKDOWN, RELEASE
    duration_seconds: Optional[int] = None
    reason: Optional[str] = None
    initiated_by: str

class OutputControl(BaseModel):
    """Output control operations"""
    output_id: int
    action: ControlAction
    duration_ms: Optional[int] = None  # For PULSE or ACTIVATE with timeout
    reason: Optional[str] = None

class RelayControl(BaseModel):
    """Relay control operations"""
    relay_id: int
    action: ControlAction
    duration_ms: Optional[int] = None
    reason: Optional[str] = None

class MassControl(BaseModel):
    """Mass control operations (all doors, etc.)"""
    target_type: str  # ALL_DOORS, ALL_OUTPUTS, ALL_RELAYS, PANEL
    action: str  # LOCKDOWN, UNLOCK_ALL, NORMAL, EMERGENCY_UNLOCK
    duration_seconds: Optional[int] = None
    reason: str
    initiated_by: str

# =============================================================================
# Door Control Functions
# =============================================================================

async def control_door(door_control: DoorControl) -> ControlResult:
    """
    Control a door (Lenel-style)

    Actions:
    - UNLOCK: Unlock door indefinitely
    - LOCK: Lock door
    - UNLOCK_MOMENTARY: Momentary unlock (e.g., 5 seconds)
    - UNLOCK_TIMED: Unlock for specified time
    - LOCKDOWN: Force door locked, disable all access
    - RELEASE: Release lockdown/unlock, return to normal
    """

    # TODO: Integrate with actual HAL door control
    # For now, return mock response

    success = True
    message = f"Door {door_control.door_id} action '{door_control.action}' executed"

    if door_control.action == "UNLOCK":
        message = f"Door {door_control.door_id} unlocked indefinitely"
    elif door_control.action == "LOCK":
        message = f"Door {door_control.door_id} locked"
    elif door_control.action == "UNLOCK_MOMENTARY":
        duration = door_control.duration_seconds or 5
        message = f"Door {door_control.door_id} unlocked for {duration} seconds"
    elif door_control.action == "LOCKDOWN":
        message = f"Door {door_control.door_id} in LOCKDOWN mode - all access disabled"
    elif door_control.action == "RELEASE":
        message = f"Door {door_control.door_id} returned to normal operation"

    return ControlResult(
        success=success,
        action=ControlAction.ACTIVATE,
        target_id=door_control.door_id,
        target_type="door",
        message=message,
        timestamp=datetime.now(),
        executed_by=door_control.initiated_by
    )

async def control_output(output_control: OutputControl) -> ControlResult:
    """
    Control a panel output

    Actions:
    - ACTIVATE: Turn on output
    - DEACTIVATE: Turn off output
    - PULSE: Pulse output for duration
    - TOGGLE: Toggle current state
    - OVERRIDE: Force output state, ignore automation
    - RELEASE_OVERRIDE: Release override, return to automation
    """

    # TODO: Integrate with actual HAL output control

    success = True
    message = f"Output {output_control.output_id} {output_control.action}"

    if output_control.action == ControlAction.PULSE and output_control.duration_ms:
        message = f"Output {output_control.output_id} pulsed for {output_control.duration_ms}ms"
    elif output_control.action == ControlAction.OVERRIDE:
        message = f"Output {output_control.output_id} overridden - manual control active"

    return ControlResult(
        success=success,
        action=output_control.action,
        target_id=output_control.output_id,
        target_type="output",
        message=message,
        timestamp=datetime.now()
    )

async def control_relay(relay_control: RelayControl) -> ControlResult:
    """
    Control a relay module

    Actions:
    - ACTIVATE: Energize relay
    - DEACTIVATE: De-energize relay
    - PULSE: Pulse relay for duration
    - TOGGLE: Toggle relay state
    """

    # TODO: Integrate with actual HAL relay control

    success = True
    message = f"Relay {relay_control.relay_id} {relay_control.action}"

    if relay_control.action == ControlAction.PULSE and relay_control.duration_ms:
        message = f"Relay {relay_control.relay_id} pulsed for {relay_control.duration_ms}ms"

    return ControlResult(
        success=success,
        action=relay_control.action,
        target_id=relay_control.relay_id,
        target_type="relay",
        message=message,
        timestamp=datetime.now()
    )

async def mass_control(mass_control: MassControl) -> ControlResult:
    """
    Mass control operations (Lenel-style)

    Examples:
    - Lockdown all doors in emergency
    - Unlock all doors for evacuation
    - Reset all outputs
    - Reboot panel
    """

    # TODO: Integrate with actual HAL mass control

    success = True
    message = f"Mass control: {mass_control.action} on {mass_control.target_type}"

    if mass_control.action == "LOCKDOWN":
        message = f"LOCKDOWN activated - all doors locked and secured"
    elif mass_control.action == "UNLOCK_ALL":
        message = f"EMERGENCY UNLOCK - all doors unlocked for evacuation"
    elif mass_control.action == "NORMAL":
        message = f"System returned to NORMAL operation"

    return ControlResult(
        success=success,
        action=ControlAction.ACTIVATE,
        target_id=0,
        target_type=mass_control.target_type,
        message=message,
        timestamp=datetime.now(),
        executed_by=mass_control.initiated_by
    )

# =============================================================================
# Advanced Control Features
# =============================================================================

class ScheduledControl(BaseModel):
    """Schedule an I/O control action for later"""
    control_type: str  # door, output, relay
    control_id: int
    action: str
    scheduled_time: datetime
    reason: str
    created_by: str

class ControlMacro(BaseModel):
    """Define a macro - series of control actions"""
    macro_id: int
    name: str
    description: str
    actions: List[dict]  # List of control actions
    created_by: str

# Example macros (Lenel-style):

EXAMPLE_MACROS = [
    {
        "macro_id": 1,
        "name": "Emergency Lockdown",
        "description": "Lock all doors and disable all outputs",
        "actions": [
            {"type": "mass_control", "target": "ALL_DOORS", "action": "LOCKDOWN"},
            {"type": "mass_control", "target": "ALL_OUTPUTS", "action": "DEACTIVATE"},
            {"type": "alert", "message": "EMERGENCY LOCKDOWN ACTIVATED"}
        ]
    },
    {
        "macro_id": 2,
        "name": "Fire Evacuation",
        "description": "Unlock all doors for evacuation",
        "actions": [
            {"type": "mass_control", "target": "ALL_DOORS", "action": "UNLOCK_ALL"},
            {"type": "output_control", "output_id": 10, "action": "ACTIVATE"},  # Alarm strobe
            {"type": "alert", "message": "FIRE EVACUATION - ALL DOORS UNLOCKED"}
        ]
    },
    {
        "macro_id": 3,
        "name": "After Hours Mode",
        "description": "Secure building for night",
        "actions": [
            {"type": "mass_control", "target": "ALL_DOORS", "action": "LOCK"},
            {"type": "output_control", "output_id": 5, "action": "DEACTIVATE"},  # Turn off lobby lights
            {"type": "alert", "message": "After hours mode activated"}
        ]
    },
    {
        "macro_id": 4,
        "name": "Morning Unlock",
        "description": "Unlock main entrances for business hours",
        "actions": [
            {"type": "door_control", "door_id": 1, "action": "UNLOCK"},  # Main entrance
            {"type": "door_control", "door_id": 2, "action": "UNLOCK"},  # Side entrance
            {"type": "output_control", "output_id": 5, "action": "ACTIVATE"},  # Lobby lights
            {"type": "alert", "message": "Building opened for business"}
        ]
    }
]

async def execute_macro(macro_id: int, initiated_by: str) -> List[ControlResult]:
    """Execute a predefined control macro"""

    # TODO: Implement actual macro execution
    # For now, return mock results

    results = []
    macro = next((m for m in EXAMPLE_MACROS if m["macro_id"] == macro_id), None)

    if not macro:
        return [ControlResult(
            success=False,
            action=ControlAction.ACTIVATE,
            target_id=macro_id,
            target_type="macro",
            message=f"Macro {macro_id} not found",
            timestamp=datetime.now(),
            executed_by=initiated_by
        )]

    # Execute each action in the macro
    for action in macro["actions"]:
        results.append(ControlResult(
            success=True,
            action=ControlAction.ACTIVATE,
            target_id=0,
            target_type=action["type"],
            message=f"Macro '{macro['name']}': {action.get('action', 'executed')}",
            timestamp=datetime.now(),
            executed_by=initiated_by
        ))

    return results

# =============================================================================
# I/O Override Management
# =============================================================================

class IOOverride(BaseModel):
    """I/O override status"""
    override_id: int
    target_type: str  # door, output, relay
    target_id: int
    target_name: str
    override_state: str  # LOCKED, UNLOCKED, ON, OFF
    override_since: datetime
    override_by: str
    reason: str
    auto_release: Optional[datetime] = None

async def get_active_overrides() -> List[IOOverride]:
    """Get all active I/O overrides"""

    # TODO: Query actual override states from HAL

    return [
        IOOverride(
            override_id=1,
            target_type="door",
            target_id=5,
            target_name="Server Room",
            override_state="LOCKED",
            override_since=datetime(2025, 11, 8, 10, 30),
            override_by="admin",
            reason="Maintenance in progress",
            auto_release=datetime(2025, 11, 8, 17, 0)
        )
    ]

async def clear_override(override_id: int) -> ControlResult:
    """Clear an I/O override"""

    return ControlResult(
        success=True,
        action=ControlAction.RELEASE_OVERRIDE,
        target_id=override_id,
        target_type="override",
        message=f"Override {override_id} cleared - returned to automatic control",
        timestamp=datetime.now()
    )
