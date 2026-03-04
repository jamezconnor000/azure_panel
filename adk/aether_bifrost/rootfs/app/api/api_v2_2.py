#!/usr/bin/env python3
"""
AetherAccess API v2.2 - HAL Core Integration
Bridges HAL C Library features into the Aether Access GUI

New endpoints for:
- OSDP Secure Channel management
- Card Database operations
- System Health & Diagnostics
- Event Buffer management
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
import auth
import database as db

# Create router
router = APIRouter(prefix="/api/v2.2", tags=["v2.2 - HAL Integration"])


# =============================================================================
# Enums and Models
# =============================================================================

class OSDPSecureChannelState(str, Enum):
    NOT_INITIALIZED = "not_initialized"
    INITIALIZING = "initializing"
    CHALLENGE_SENT = "challenge_sent"
    CRYPTOGRAM_RECEIVED = "cryptogram_received"
    ESTABLISHED = "established"
    ERROR = "error"
    DISABLED = "disabled"


class ReaderMode(str, Enum):
    LOCKED = "locked"
    CARD_ONLY = "card_only"
    CARD_AND_PIN = "card_and_pin"
    PIN_ONLY = "pin_only"
    UNLOCKED = "unlocked"
    FACILITY_CODE = "facility_code"
    SITE_CODE = "site_code"
    CIPHER = "cipher"
    TOGGLE = "toggle"
    DUAL_CUSTODY = "dual_custody"
    UNKNOWN = "unknown"


class ReaderIndicationState(str, Enum):
    OFF = "off"
    IDLE = "idle"
    GRANT = "grant"
    DENY = "deny"
    TAMPER = "tamper"
    COMM_ERROR = "comm_error"
    APB_VIOLATION = "apb_violation"
    ESCORT_WAIT = "escort_wait"
    LOCKED = "locked"
    UNLOCKED = "unlocked"
    CARD = "card"
    CARD_AND_PIN = "card_and_pin"


class RelayOperation(str, Enum):
    OFF = "off"
    ON = "on"
    PULSE = "pulse"


class LogLevel(str, Enum):
    TRACE = "trace"
    DEBUG = "debug"
    INFO = "info"
    WARN = "warn"
    ERROR = "error"
    FATAL = "fatal"


class LogCategory(str, Enum):
    SYSTEM = "system"
    DATABASE = "database"
    READER = "reader"
    OSDP = "osdp"
    ACCESS = "access"
    EVENT = "event"
    NETWORK = "network"
    RELAY = "relay"
    CONFIG = "config"
    PERFORMANCE = "performance"


# =============================================================================
# OSDP Secure Channel Models
# =============================================================================

class OSDPSCInitRequest(BaseModel):
    scbk: str = Field(..., min_length=32, max_length=32, description="16-byte SCBK as hex string")
    reader_address: int = Field(..., ge=0, le=126)


class OSDPSCStatus(BaseModel):
    door_id: int
    reader_address: int
    state: OSDPSecureChannelState
    is_established: bool
    last_handshake_time: Optional[int] = None
    handshake_attempts: int = 0
    packets_encrypted: int = 0
    packets_decrypted: int = 0
    mac_failures: int = 0
    last_error: Optional[str] = None


class OSDPSCLogEntry(BaseModel):
    timestamp: int
    event_type: str
    reader_address: int
    details: Dict[str, Any]


# =============================================================================
# Card Database Models
# =============================================================================

class CardCreate(BaseModel):
    card_number: str = Field(..., min_length=1, max_length=20)
    permission_id: int
    holder_name: Optional[str] = Field(None, max_length=100)
    pin: Optional[str] = Field(None, min_length=4, max_length=8)
    facility_code: Optional[int] = None
    activation_date: Optional[int] = None  # Unix timestamp
    expiration_date: Optional[int] = None  # Unix timestamp
    is_active: bool = True


class CardUpdate(BaseModel):
    permission_id: Optional[int] = None
    holder_name: Optional[str] = Field(None, max_length=100)
    pin: Optional[str] = Field(None, min_length=4, max_length=8)
    activation_date: Optional[int] = None
    expiration_date: Optional[int] = None
    is_active: Optional[bool] = None


class CardResponse(BaseModel):
    card_number: str
    permission_id: int
    holder_name: Optional[str]
    facility_code: Optional[int]
    activation_date: int
    expiration_date: int
    is_active: bool
    is_currently_valid: bool
    created_at: int
    updated_at: int


class CardStats(BaseModel):
    total_cards: int
    active_cards: int
    inactive_cards: int
    expired_cards: int
    not_yet_active_cards: int
    cards_by_permission: Dict[int, int]


class PINValidationRequest(BaseModel):
    pin: str


class PINValidationResponse(BaseModel):
    valid: bool
    attempts_remaining: Optional[int] = None


# =============================================================================
# System Health Models
# =============================================================================

class SystemHealth(BaseModel):
    status: str  # "healthy", "degraded", "critical"
    timestamp: int
    uptime_seconds: int
    database_connected: bool
    api_running: bool
    event_export_running: bool
    hal_initialized: bool
    reader_count: int
    readers_online: int
    readers_offline: int
    events_pending: int
    events_total_today: int
    errors_last_hour: int
    warnings_last_hour: int
    cpu_percent: Optional[float] = None
    memory_mb: Optional[float] = None


class DiagnosticLogEntry(BaseModel):
    timestamp: int
    level: LogLevel
    category: LogCategory
    message: str
    source_file: Optional[str] = None
    source_line: Optional[int] = None
    extra: Optional[Dict[str, Any]] = None


class LogConfigUpdate(BaseModel):
    min_level: LogLevel = LogLevel.INFO
    log_to_file: bool = True
    log_to_console: bool = True
    include_source_info: bool = False
    rotate_logs: bool = True
    max_log_size_mb: int = Field(100, ge=1, le=1000)


class PerformanceMetrics(BaseModel):
    timestamp: int
    period_seconds: int
    access_decisions_count: int
    avg_decision_time_ms: float
    max_decision_time_ms: float
    events_processed: int
    avg_event_time_ms: float
    database_queries: int
    avg_query_time_ms: float
    osdp_packets_sent: int
    osdp_packets_received: int


# =============================================================================
# Event Buffer Models
# =============================================================================

class EventBufferStatus(BaseModel):
    capacity: int
    event_count: int
    head_index: int
    tail_index: int
    utilization_percent: float
    is_full: bool
    overflow_count: int


class EventBufferStats(BaseModel):
    total_pushed: int
    total_popped: int
    total_acknowledged: int
    overflows: int
    avg_buffer_time_ms: float
    max_buffer_time_ms: float
    events_per_minute: float


class PendingEvent(BaseModel):
    event_id: str
    event_type: str
    timestamp: int
    card_number: Optional[str]
    door_id: Optional[int]
    door_name: Optional[str]
    granted: Optional[bool]
    reason: Optional[str]
    buffered_at: int


# =============================================================================
# Reader Configuration Models
# =============================================================================

class ReaderConfig(BaseModel):
    reader_id: int
    reader_name: str
    mode: ReaderMode
    flags: int  # Bitmask of ReaderFlags
    osdp_enabled: bool
    osdp_address: Optional[int]
    indication_state: ReaderIndicationState
    last_card_read: Optional[int]
    online: bool


class ReaderModeUpdate(BaseModel):
    mode: ReaderMode


class ReaderFlagsUpdate(BaseModel):
    flags: int  # Bitmask
    # Flag bits:
    # 0x0001 = APB_ENABLED
    # 0x0002 = SUPERVISED_INPUT
    # 0x0004 = REX_ENABLED
    # 0x0008 = PIN_REQUIRED
    # 0x0010 = TWO_PERSON_RULE
    # 0x0020 = ESCORT_REQUIRED
    # 0x0040 = DURESS_PIN_ENABLED
    # 0x0080 = KEYPAD_ENABLED


class ReaderIndicationUpdate(BaseModel):
    state: ReaderIndicationState
    duration_ms: int = Field(3000, ge=100, le=60000)


# =============================================================================
# Relay Configuration Models
# =============================================================================

class RelayCreate(BaseModel):
    relay_id: int
    relay_name: str
    pulse_duration_ms: int = Field(1000, ge=100, le=60000)
    control_timezone: Optional[int] = None
    flags: int = 0  # Bitmask of RelayFlags
    # Flag bits:
    # 0x01 = FAIL_SECURE
    # 0x02 = FAIL_SAFE
    # 0x04 = LATCHING
    # 0x08 = NORMALLY_OPEN
    # 0x10 = NORMALLY_CLOSED
    # 0x20 = SUPERVISED


class RelayUpdate(BaseModel):
    relay_name: Optional[str] = None
    pulse_duration_ms: Optional[int] = Field(None, ge=100, le=60000)
    control_timezone: Optional[int] = None
    flags: Optional[int] = None


class RelayResponse(BaseModel):
    relay_id: int
    relay_name: str
    pulse_duration_ms: int
    control_timezone: Optional[int]
    flags: int
    current_state: str  # "off", "on", "pulsing"
    last_activated: Optional[int]
    activation_count: int


class RelayControlRequest(BaseModel):
    operation: RelayOperation
    duration_ms: Optional[int] = None  # For pulse


class RelayLink(BaseModel):
    link_id: int
    relay_id: int
    source_event_type: str
    source_reader_id: Optional[int]
    relay_operation: RelayOperation
    delay_ms: int = 0
    is_active: bool = True


class RelayLinkCreate(BaseModel):
    source_event_type: str  # "access_granted", "access_denied", "door_forced", etc.
    source_reader_id: Optional[int] = None  # None = any reader
    relay_operation: RelayOperation
    delay_ms: int = Field(0, ge=0, le=60000)


# =============================================================================
# Export Daemon Models
# =============================================================================

class ExportConfig(BaseModel):
    enabled: bool
    server_url: str
    api_endpoint: str
    api_key: str
    timeout_seconds: int = Field(5, ge=1, le=60)
    retry_attempts: int = Field(3, ge=0, le=10)
    retry_delay_ms: int = Field(1000, ge=100, le=60000)
    batch_size: int = Field(100, ge=1, le=1000)


class ExportStats(BaseModel):
    events_received: int
    events_sent: int
    events_failed: int
    batches_sent: int
    retries_attempted: int
    last_send_time: Optional[int]
    last_error_code: Optional[int]
    last_error_msg: Optional[str]
    queue_depth: int


class ExportTestResult(BaseModel):
    connected: bool
    server_version: Optional[str]
    api_key_valid: bool
    response_time_ms: int
    error_message: Optional[str]


# =============================================================================
# OSDP SECURE CHANNEL ENDPOINTS
# =============================================================================

@router.post("/osdp/secure-channel/{door_id}/initialize")
async def initialize_osdp_secure_channel(
    door_id: int,
    request: OSDPSCInitRequest,
    current_user: Dict = Depends(auth.get_current_user)
):
    """
    Initialize OSDP Secure Channel for a door

    This starts the SC initialization process with the provided SCBK.
    The actual handshake is performed asynchronously.
    """
    auth.check_permission(current_user, "door.configure")

    # Validate SCBK is valid hex
    try:
        scbk_bytes = bytes.fromhex(request.scbk)
        if len(scbk_bytes) != 16:
            raise HTTPException(status_code=400, detail="SCBK must be exactly 16 bytes (32 hex chars)")
    except ValueError:
        raise HTTPException(status_code=400, detail="SCBK must be valid hexadecimal")

    # Store SC configuration
    await db.update_door_config(
        door_id,
        osdp_enabled=True,
        scbk=request.scbk,
        reader_address=request.reader_address,
        osdp_sc_state="initializing"
    )

    # TODO: Call HAL C library to actually initialize SC
    # OSDP_SC_Init(request.reader_address, scbk_bytes)

    await db.log_audit(
        current_user["id"], "osdp_sc_initialized",
        resource_type="door", resource_id=door_id,
        details={"reader_address": request.reader_address}
    )

    return {
        "status": "initializing",
        "door_id": door_id,
        "reader_address": request.reader_address,
        "message": "OSDP Secure Channel initialization started"
    }


@router.get("/osdp/secure-channel/{door_id}/status", response_model=OSDPSCStatus)
async def get_osdp_secure_channel_status(
    door_id: int,
    current_user: Dict = Depends(auth.get_current_user)
):
    """Get current OSDP Secure Channel status for a door"""
    auth.check_permission(current_user, "door.read")

    door = await db.get_door_config(door_id)
    if not door:
        raise HTTPException(status_code=404, detail="Door not found")

    # TODO: Get actual status from HAL
    # status = OSDP_SC_GetStatus(door["reader_address"])

    # For now, return stored state
    return OSDPSCStatus(
        door_id=door_id,
        reader_address=door.get("reader_address", 0),
        state=OSDPSecureChannelState(door.get("osdp_sc_state", "not_initialized")),
        is_established=door.get("osdp_sc_state") == "established",
        last_handshake_time=door.get("osdp_sc_last_handshake"),
        handshake_attempts=door.get("osdp_sc_attempts", 0),
        packets_encrypted=door.get("osdp_sc_encrypted", 0),
        packets_decrypted=door.get("osdp_sc_decrypted", 0),
        mac_failures=door.get("osdp_sc_mac_failures", 0),
        last_error=door.get("osdp_sc_last_error")
    )


@router.post("/osdp/secure-channel/{door_id}/handshake/start")
async def start_osdp_handshake(
    door_id: int,
    current_user: Dict = Depends(auth.get_current_user)
):
    """
    Initiate OSDP Secure Channel handshake

    This sends the CP challenge to the reader and waits for response.
    """
    auth.check_permission(current_user, "door.configure")

    door = await db.get_door_config(door_id)
    if not door:
        raise HTTPException(status_code=404, detail="Door not found")

    if not door.get("osdp_enabled"):
        raise HTTPException(status_code=400, detail="OSDP not enabled for this door")

    # TODO: Call HAL
    # result = OSDP_SC_StartHandshake(door["reader_address"])

    await db.update_door_config(door_id, osdp_sc_state="challenge_sent")

    await db.log_audit(
        current_user["id"], "osdp_handshake_started",
        resource_type="door", resource_id=door_id
    )

    return {
        "status": "challenge_sent",
        "door_id": door_id,
        "message": "OSDP handshake initiated, waiting for reader response"
    }


@router.post("/osdp/secure-channel/{door_id}/reset")
async def reset_osdp_secure_channel(
    door_id: int,
    current_user: Dict = Depends(auth.get_current_user)
):
    """Reset/teardown OSDP Secure Channel"""
    auth.check_permission(current_user, "door.configure")

    door = await db.get_door_config(door_id)
    if not door:
        raise HTTPException(status_code=404, detail="Door not found")

    # TODO: Call HAL
    # OSDP_SC_Reset(door["reader_address"])

    await db.update_door_config(
        door_id,
        osdp_sc_state="not_initialized",
        osdp_sc_last_error=None
    )

    await db.log_audit(
        current_user["id"], "osdp_sc_reset",
        resource_type="door", resource_id=door_id
    )

    return {
        "status": "reset",
        "door_id": door_id,
        "message": "OSDP Secure Channel has been reset"
    }


@router.get("/osdp/secure-channel/{door_id}/logs", response_model=List[OSDPSCLogEntry])
async def get_osdp_secure_channel_logs(
    door_id: int,
    limit: int = 100,
    current_user: Dict = Depends(auth.get_current_user)
):
    """Get OSDP Secure Channel operation logs"""
    auth.check_permission(current_user, "door.read")

    # TODO: Get logs from HAL diagnostic system
    logs = await db.get_osdp_sc_logs(door_id, limit=limit)
    return logs


# =============================================================================
# CARD DATABASE ENDPOINTS
# =============================================================================

@router.post("/cards", response_model=CardResponse)
async def create_card(
    card_data: CardCreate,
    current_user: Dict = Depends(auth.get_current_user)
):
    """Create a new card in the HAL card database"""
    auth.check_permission(current_user, "card_holder.create")

    # Check if card already exists
    existing = await db.get_card(card_data.card_number)
    if existing:
        raise HTTPException(status_code=400, detail="Card number already exists")

    # Hash PIN if provided
    pin_hash = None
    if card_data.pin:
        pin_hash = auth.hash_password(card_data.pin)

    card_id = await db.create_card(
        card_number=card_data.card_number,
        permission_id=card_data.permission_id,
        holder_name=card_data.holder_name,
        pin_hash=pin_hash,
        facility_code=card_data.facility_code,
        activation_date=card_data.activation_date or 0,
        expiration_date=card_data.expiration_date or 0,
        is_active=card_data.is_active
    )

    await db.log_audit(
        current_user["id"], "card_created",
        resource_type="card", resource_id=card_id,
        details={"card_number": card_data.card_number}
    )

    return await db.get_card(card_data.card_number)


@router.get("/cards/{card_number}", response_model=CardResponse)
async def get_card(
    card_number: str,
    current_user: Dict = Depends(auth.get_current_user)
):
    """Get card details by card number"""
    auth.check_permission(current_user, "card_holder.read")

    card = await db.get_card(card_number)
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")

    return card


@router.put("/cards/{card_number}", response_model=CardResponse)
async def update_card(
    card_number: str,
    card_data: CardUpdate,
    current_user: Dict = Depends(auth.get_current_user)
):
    """Update card record"""
    auth.check_permission(current_user, "card_holder.update")

    card = await db.get_card(card_number)
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")

    update_dict = card_data.dict(exclude_unset=True)

    # Hash new PIN if provided
    if "pin" in update_dict and update_dict["pin"]:
        update_dict["pin_hash"] = auth.hash_password(update_dict.pop("pin"))
    elif "pin" in update_dict:
        del update_dict["pin"]

    await db.update_card(card_number, **update_dict)

    await db.log_audit(
        current_user["id"], "card_updated",
        resource_type="card", resource_id=card["id"],
        details={"card_number": card_number}
    )

    return await db.get_card(card_number)


@router.delete("/cards/{card_number}")
async def delete_card(
    card_number: str,
    current_user: Dict = Depends(auth.get_current_user)
):
    """Delete card from database"""
    auth.check_permission(current_user, "card_holder.delete")

    card = await db.get_card(card_number)
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")

    await db.delete_card(card_number)

    await db.log_audit(
        current_user["id"], "card_deleted",
        resource_type="card", resource_id=card["id"],
        details={"card_number": card_number}
    )

    return {"message": "Card deleted successfully"}


@router.get("/cards/permission/{permission_id}", response_model=List[CardResponse])
async def get_cards_by_permission(
    permission_id: int,
    current_user: Dict = Depends(auth.get_current_user)
):
    """Get all cards linked to a permission"""
    auth.check_permission(current_user, "card_holder.read")

    cards = await db.get_cards_by_permission(permission_id)
    return cards


@router.post("/cards/{card_number}/validate-pin", response_model=PINValidationResponse)
async def validate_card_pin(
    card_number: str,
    request: PINValidationRequest,
    current_user: Dict = Depends(auth.get_current_user)
):
    """Validate PIN for a card"""
    auth.check_permission(current_user, "door.control")

    card = await db.get_card(card_number)
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")

    if not card.get("pin_hash"):
        raise HTTPException(status_code=400, detail="Card does not have a PIN set")

    valid = auth.verify_password(request.pin, card["pin_hash"])

    # TODO: Track failed attempts
    return PINValidationResponse(valid=valid, attempts_remaining=3 if not valid else None)


@router.get("/cards/stats", response_model=CardStats)
async def get_card_stats(
    current_user: Dict = Depends(auth.get_current_user)
):
    """Get card database statistics"""
    auth.check_permission(current_user, "card_holder.read")

    stats = await db.get_card_stats()
    return stats


@router.get("/cards/export")
async def export_cards(
    format: str = "json",
    current_user: Dict = Depends(auth.get_current_user)
):
    """Export all cards (JSON or CSV)"""
    auth.check_permission(current_user, "card_holder.read")

    cards = await db.get_all_cards()

    if format == "csv":
        # Return CSV
        import io
        import csv
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=[
            "card_number", "permission_id", "holder_name",
            "activation_date", "expiration_date", "is_active"
        ])
        writer.writeheader()
        for card in cards:
            writer.writerow({
                "card_number": card["card_number"],
                "permission_id": card["permission_id"],
                "holder_name": card.get("holder_name", ""),
                "activation_date": card["activation_date"],
                "expiration_date": card["expiration_date"],
                "is_active": card["is_active"]
            })

        from fastapi.responses import Response
        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=cards_export.csv"}
        )

    return {"cards": cards, "count": len(cards)}


@router.post("/cards/import")
async def import_cards(
    cards: List[CardCreate],
    current_user: Dict = Depends(auth.get_current_user)
):
    """Bulk import cards"""
    auth.check_permission(current_user, "card_holder.create")

    imported = 0
    errors = []

    for card_data in cards:
        try:
            existing = await db.get_card(card_data.card_number)
            if existing:
                errors.append({"card_number": card_data.card_number, "error": "Already exists"})
                continue

            await db.create_card(
                card_number=card_data.card_number,
                permission_id=card_data.permission_id,
                holder_name=card_data.holder_name,
                activation_date=card_data.activation_date or 0,
                expiration_date=card_data.expiration_date or 0,
                is_active=card_data.is_active
            )
            imported += 1
        except Exception as e:
            errors.append({"card_number": card_data.card_number, "error": str(e)})

    await db.log_audit(
        current_user["id"], "cards_imported",
        details={"imported": imported, "errors": len(errors)}
    )

    return {"imported": imported, "errors": errors}


# =============================================================================
# SYSTEM HEALTH & DIAGNOSTICS ENDPOINTS
# =============================================================================

@router.get("/system/health", response_model=SystemHealth)
async def get_system_health(
    current_user: Dict = Depends(auth.get_current_user)
):
    """Get comprehensive system health status"""
    auth.check_permission(current_user, "audit.read")

    # TODO: Get actual health from HAL
    # health = HAL_Diagnostic_GetHealth()

    import time
    import psutil

    # Get counts from database
    reader_count = await db.get_reader_count()
    events_today = await db.get_events_count_today()
    errors_last_hour = await db.get_log_count(level="error", hours=1)
    warnings_last_hour = await db.get_log_count(level="warn", hours=1)
    events_pending = await db.get_pending_events_count()

    # Determine overall status
    status = "healthy"
    if errors_last_hour > 10:
        status = "degraded"
    if errors_last_hour > 50:
        status = "critical"

    return SystemHealth(
        status=status,
        timestamp=int(time.time()),
        uptime_seconds=int(time.time() - psutil.boot_time()) if hasattr(psutil, 'boot_time') else 0,
        database_connected=True,  # We're responding, so DB works
        api_running=True,
        event_export_running=True,  # TODO: Check actual daemon status
        hal_initialized=True,  # TODO: Check HAL status
        reader_count=reader_count,
        readers_online=reader_count,  # TODO: Get actual online count
        readers_offline=0,
        events_pending=events_pending,
        events_total_today=events_today,
        errors_last_hour=errors_last_hour,
        warnings_last_hour=warnings_last_hour,
        cpu_percent=psutil.cpu_percent() if hasattr(psutil, 'cpu_percent') else None,
        memory_mb=psutil.Process().memory_info().rss / 1024 / 1024 if hasattr(psutil, 'Process') else None
    )


@router.get("/system/logs", response_model=List[DiagnosticLogEntry])
async def get_system_logs(
    level: Optional[LogLevel] = None,
    category: Optional[LogCategory] = None,
    since_ms: Optional[int] = None,
    limit: int = 100,
    current_user: Dict = Depends(auth.get_current_user)
):
    """Get diagnostic logs with filtering"""
    auth.check_permission(current_user, "audit.read")

    logs = await db.get_diagnostic_logs(
        level=level.value if level else None,
        category=category.value if category else None,
        since_ms=since_ms,
        limit=limit
    )

    return logs


@router.get("/system/logs/export")
async def export_system_logs(
    since_ms: Optional[int] = None,
    category: Optional[str] = None,
    current_user: Dict = Depends(auth.get_current_user)
):
    """Export logs as JSON file"""
    auth.check_permission(current_user, "audit.read")

    logs = await db.get_diagnostic_logs(
        category=category,
        since_ms=since_ms,
        limit=10000
    )

    from fastapi.responses import Response
    import json

    return Response(
        content=json.dumps({"logs": logs, "exported_at": int(datetime.now().timestamp())}),
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=logs_export.json"}
    )


@router.get("/system/report")
async def generate_system_report(
    current_user: Dict = Depends(auth.get_current_user)
):
    """Generate comprehensive diagnostic report"""
    auth.check_permission(current_user, "audit.read")

    import time

    health = await get_system_health(current_user)
    recent_errors = await db.get_diagnostic_logs(level="error", limit=50)
    card_stats = await db.get_card_stats()
    door_count = await db.get_door_count()

    return {
        "report_generated_at": int(time.time()),
        "system_health": health.dict(),
        "card_statistics": card_stats.dict() if hasattr(card_stats, 'dict') else card_stats,
        "door_count": door_count,
        "recent_errors": recent_errors,
        "recommendations": []  # TODO: Add intelligent recommendations
    }


@router.post("/system/logs/config")
async def configure_logging(
    config: LogConfigUpdate,
    current_user: Dict = Depends(auth.get_current_user)
):
    """Configure diagnostic logging"""
    auth.check_permission(current_user, "system.configure")

    await db.update_system_config("logging", config.dict())

    await db.log_audit(
        current_user["id"], "logging_configured",
        details=config.dict()
    )

    return {"message": "Logging configuration updated", "config": config.dict()}


@router.get("/system/logs/categories")
async def get_log_categories(
    current_user: Dict = Depends(auth.get_current_user)
):
    """List available log categories and their current levels"""
    auth.check_permission(current_user, "audit.read")

    return {
        "categories": [cat.value for cat in LogCategory],
        "levels": [lvl.value for lvl in LogLevel],
        "current_config": await db.get_system_config("logging")
    }


@router.get("/system/performance", response_model=PerformanceMetrics)
async def get_performance_metrics(
    period_seconds: int = 3600,
    current_user: Dict = Depends(auth.get_current_user)
):
    """Get performance metrics aggregated over time period"""
    auth.check_permission(current_user, "audit.read")

    # TODO: Get actual metrics from HAL
    import time

    return PerformanceMetrics(
        timestamp=int(time.time()),
        period_seconds=period_seconds,
        access_decisions_count=0,
        avg_decision_time_ms=0.0,
        max_decision_time_ms=0.0,
        events_processed=0,
        avg_event_time_ms=0.0,
        database_queries=0,
        avg_query_time_ms=0.0,
        osdp_packets_sent=0,
        osdp_packets_received=0
    )


# =============================================================================
# EVENT BUFFER ENDPOINTS
# =============================================================================

@router.get("/hal/event-buffer/status", response_model=EventBufferStatus)
async def get_event_buffer_status(
    current_user: Dict = Depends(auth.get_current_user)
):
    """Get HAL event buffer status"""
    auth.check_permission(current_user, "audit.read")

    # TODO: Get actual buffer status from HAL
    # status = HAL_EventBuffer_GetStatus()

    return EventBufferStatus(
        capacity=100000,
        event_count=0,
        head_index=0,
        tail_index=0,
        utilization_percent=0.0,
        is_full=False,
        overflow_count=0
    )


@router.get("/hal/event-buffer/stats", response_model=EventBufferStats)
async def get_event_buffer_stats(
    current_user: Dict = Depends(auth.get_current_user)
):
    """Get HAL event buffer statistics"""
    auth.check_permission(current_user, "audit.read")

    # TODO: Get actual stats from HAL

    return EventBufferStats(
        total_pushed=0,
        total_popped=0,
        total_acknowledged=0,
        overflows=0,
        avg_buffer_time_ms=0.0,
        max_buffer_time_ms=0.0,
        events_per_minute=0.0
    )


@router.post("/hal/event-buffer/clear")
async def clear_event_buffer(
    current_user: Dict = Depends(auth.get_current_user)
):
    """Clear/reset HAL event buffer"""
    auth.check_permission(current_user, "system.configure")

    # TODO: Call HAL
    # HAL_EventBuffer_Clear()

    await db.log_audit(
        current_user["id"], "event_buffer_cleared"
    )

    return {"message": "Event buffer cleared"}


@router.get("/hal/events/pending", response_model=List[PendingEvent])
async def get_pending_events(
    limit: int = 100,
    current_user: Dict = Depends(auth.get_current_user)
):
    """Get pending events from buffer"""
    auth.check_permission(current_user, "audit.read")

    # TODO: Get actual events from HAL buffer
    events = await db.get_pending_events(limit=limit)
    return events


# =============================================================================
# READER CONFIGURATION ENDPOINTS
# =============================================================================

@router.get("/readers/{reader_id}", response_model=ReaderConfig)
async def get_reader_config(
    reader_id: int,
    current_user: Dict = Depends(auth.get_current_user)
):
    """Get reader configuration"""
    auth.check_permission(current_user, "door.read")

    reader = await db.get_reader_config(reader_id)
    if not reader:
        raise HTTPException(status_code=404, detail="Reader not found")

    return reader


@router.put("/readers/{reader_id}/mode")
async def set_reader_mode(
    reader_id: int,
    request: ReaderModeUpdate,
    current_user: Dict = Depends(auth.get_current_user)
):
    """Set reader mode"""
    auth.check_permission(current_user, "door.configure")

    reader = await db.get_reader_config(reader_id)
    if not reader:
        raise HTTPException(status_code=404, detail="Reader not found")

    # TODO: Call HAL
    # HAL_SetReaderMode(reader_id, request.mode)

    await db.update_reader_config(reader_id, mode=request.mode.value)

    await db.log_audit(
        current_user["id"], "reader_mode_changed",
        resource_type="reader", resource_id=reader_id,
        details={"mode": request.mode.value}
    )

    return {"message": f"Reader mode set to {request.mode.value}", "reader_id": reader_id}


@router.put("/readers/{reader_id}/flags")
async def set_reader_flags(
    reader_id: int,
    request: ReaderFlagsUpdate,
    current_user: Dict = Depends(auth.get_current_user)
):
    """Set reader control flags"""
    auth.check_permission(current_user, "door.configure")

    reader = await db.get_reader_config(reader_id)
    if not reader:
        raise HTTPException(status_code=404, detail="Reader not found")

    # TODO: Call HAL
    # HAL_SetReaderFlags(reader_id, request.flags)

    await db.update_reader_config(reader_id, flags=request.flags)

    await db.log_audit(
        current_user["id"], "reader_flags_changed",
        resource_type="reader", resource_id=reader_id,
        details={"flags": request.flags}
    )

    return {"message": "Reader flags updated", "reader_id": reader_id, "flags": request.flags}


@router.get("/readers/{reader_id}/indication")
async def get_reader_indication(
    reader_id: int,
    current_user: Dict = Depends(auth.get_current_user)
):
    """Get current reader indication state"""
    auth.check_permission(current_user, "door.read")

    # TODO: Get from HAL
    # state = HAL_GetReaderIndication(reader_id)

    return {
        "reader_id": reader_id,
        "state": ReaderIndicationState.IDLE.value,
        "since": int(datetime.now().timestamp())
    }


@router.post("/readers/{reader_id}/indication/set")
async def set_reader_indication(
    reader_id: int,
    request: ReaderIndicationUpdate,
    current_user: Dict = Depends(auth.get_current_user)
):
    """Force reader indication state"""
    auth.check_permission(current_user, "door.control")

    # TODO: Call HAL
    # HAL_SetReaderIndication(reader_id, request.state, request.duration_ms)

    await db.log_audit(
        current_user["id"], "reader_indication_set",
        resource_type="reader", resource_id=reader_id,
        details={"state": request.state.value, "duration_ms": request.duration_ms}
    )

    return {
        "message": f"Reader indication set to {request.state.value}",
        "reader_id": reader_id,
        "duration_ms": request.duration_ms
    }


# =============================================================================
# RELAY CONFIGURATION ENDPOINTS
# =============================================================================

@router.post("/relays", response_model=RelayResponse)
async def create_relay(
    relay_data: RelayCreate,
    current_user: Dict = Depends(auth.get_current_user)
):
    """Create relay configuration"""
    auth.check_permission(current_user, "door.configure")

    relay_id = await db.create_relay(
        relay_id=relay_data.relay_id,
        relay_name=relay_data.relay_name,
        pulse_duration_ms=relay_data.pulse_duration_ms,
        control_timezone=relay_data.control_timezone,
        flags=relay_data.flags
    )

    await db.log_audit(
        current_user["id"], "relay_created",
        resource_type="relay", resource_id=relay_id,
        details={"relay_name": relay_data.relay_name}
    )

    return await db.get_relay(relay_id)


@router.get("/relays/{relay_id}", response_model=RelayResponse)
async def get_relay(
    relay_id: int,
    current_user: Dict = Depends(auth.get_current_user)
):
    """Get relay configuration"""
    auth.check_permission(current_user, "door.read")

    relay = await db.get_relay(relay_id)
    if not relay:
        raise HTTPException(status_code=404, detail="Relay not found")

    return relay


@router.put("/relays/{relay_id}", response_model=RelayResponse)
async def update_relay(
    relay_id: int,
    relay_data: RelayUpdate,
    current_user: Dict = Depends(auth.get_current_user)
):
    """Update relay configuration"""
    auth.check_permission(current_user, "door.configure")

    relay = await db.get_relay(relay_id)
    if not relay:
        raise HTTPException(status_code=404, detail="Relay not found")

    update_dict = relay_data.dict(exclude_unset=True)
    await db.update_relay(relay_id, **update_dict)

    await db.log_audit(
        current_user["id"], "relay_updated",
        resource_type="relay", resource_id=relay_id,
        details=update_dict
    )

    return await db.get_relay(relay_id)


@router.delete("/relays/{relay_id}")
async def delete_relay(
    relay_id: int,
    current_user: Dict = Depends(auth.get_current_user)
):
    """Delete relay configuration"""
    auth.check_permission(current_user, "door.configure")

    relay = await db.get_relay(relay_id)
    if not relay:
        raise HTTPException(status_code=404, detail="Relay not found")

    await db.delete_relay(relay_id)

    await db.log_audit(
        current_user["id"], "relay_deleted",
        resource_type="relay", resource_id=relay_id
    )

    return {"message": "Relay deleted"}


@router.post("/relays/{relay_id}/control")
async def control_relay(
    relay_id: int,
    request: RelayControlRequest,
    current_user: Dict = Depends(auth.get_current_user)
):
    """Control relay (on/off/pulse)"""
    auth.check_permission(current_user, "door.control")

    relay = await db.get_relay(relay_id)
    if not relay:
        raise HTTPException(status_code=404, detail="Relay not found")

    # TODO: Call HAL
    # HAL_ControlRelay(relay_id, request.operation, request.duration_ms)

    await db.log_audit(
        current_user["id"], "relay_controlled",
        resource_type="relay", resource_id=relay_id,
        details={"operation": request.operation.value}
    )

    return {
        "message": f"Relay {request.operation.value} command sent",
        "relay_id": relay_id
    }


@router.get("/relays/{relay_id}/state")
async def get_relay_state(
    relay_id: int,
    current_user: Dict = Depends(auth.get_current_user)
):
    """Get current relay state"""
    auth.check_permission(current_user, "door.read")

    # TODO: Get from HAL
    # state = HAL_GetRelayState(relay_id)

    return {
        "relay_id": relay_id,
        "state": "off",
        "since": int(datetime.now().timestamp())
    }


@router.post("/relays/{relay_id}/links", response_model=RelayLink)
async def create_relay_link(
    relay_id: int,
    link_data: RelayLinkCreate,
    current_user: Dict = Depends(auth.get_current_user)
):
    """Create event→relay automation link"""
    auth.check_permission(current_user, "door.configure")

    link_id = await db.create_relay_link(
        relay_id=relay_id,
        source_event_type=link_data.source_event_type,
        source_reader_id=link_data.source_reader_id,
        relay_operation=link_data.relay_operation.value,
        delay_ms=link_data.delay_ms
    )

    await db.log_audit(
        current_user["id"], "relay_link_created",
        resource_type="relay_link", resource_id=link_id,
        details={"relay_id": relay_id, "event_type": link_data.source_event_type}
    )

    return await db.get_relay_link(link_id)


@router.get("/relays/{relay_id}/links", response_model=List[RelayLink])
async def get_relay_links(
    relay_id: int,
    current_user: Dict = Depends(auth.get_current_user)
):
    """Get all automation links for a relay"""
    auth.check_permission(current_user, "door.read")

    links = await db.get_relay_links(relay_id)
    return links


# =============================================================================
# EXPORT DAEMON ENDPOINTS
# =============================================================================

@router.get("/export/config", response_model=ExportConfig)
async def get_export_config(
    current_user: Dict = Depends(auth.get_current_user)
):
    """Get event export configuration"""
    auth.check_permission(current_user, "system.configure")

    config = await db.get_system_config("export")
    if not config:
        return ExportConfig(
            enabled=False,
            server_url="",
            api_endpoint="",
            api_key=""
        )

    return ExportConfig(**config)


@router.put("/export/config", response_model=ExportConfig)
async def update_export_config(
    config: ExportConfig,
    current_user: Dict = Depends(auth.get_current_user)
):
    """Update event export configuration"""
    auth.check_permission(current_user, "system.configure")

    await db.update_system_config("export", config.dict())

    await db.log_audit(
        current_user["id"], "export_config_updated",
        details={"enabled": config.enabled, "server_url": config.server_url}
    )

    return config


@router.get("/export/stats", response_model=ExportStats)
async def get_export_stats(
    current_user: Dict = Depends(auth.get_current_user)
):
    """Get event export statistics"""
    auth.check_permission(current_user, "audit.read")

    # TODO: Get actual stats from HAL event exporter
    stats = await db.get_export_stats()
    return stats


@router.post("/export/process")
async def trigger_export_processing(
    background_tasks: BackgroundTasks,
    current_user: Dict = Depends(auth.get_current_user)
):
    """Manually trigger event export processing"""
    auth.check_permission(current_user, "system.configure")

    # TODO: Call HAL
    # HAL_EventExporter_ProcessEvents()

    await db.log_audit(
        current_user["id"], "export_processing_triggered"
    )

    return {"message": "Export processing triggered"}


@router.post("/export/test", response_model=ExportTestResult)
async def test_export_connection(
    current_user: Dict = Depends(auth.get_current_user)
):
    """Test export server connection"""
    auth.check_permission(current_user, "system.configure")

    import time
    import httpx

    config = await db.get_system_config("export")
    if not config:
        return ExportTestResult(
            connected=False,
            api_key_valid=False,
            response_time_ms=0,
            error_message="Export not configured"
        )

    start = time.time()
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{config['server_url']}/health",
                headers={"Authorization": f"Bearer {config['api_key']}"},
                timeout=5.0
            )

            response_time = int((time.time() - start) * 1000)

            return ExportTestResult(
                connected=response.status_code < 500,
                server_version=response.headers.get("X-Server-Version"),
                api_key_valid=response.status_code != 401,
                response_time_ms=response_time,
                error_message=None if response.status_code < 400 else response.text
            )
    except Exception as e:
        return ExportTestResult(
            connected=False,
            api_key_valid=False,
            response_time_ms=int((time.time() - start) * 1000),
            error_message=str(e)
        )


@router.get("/export/logs")
async def get_export_logs(
    limit: int = 100,
    current_user: Dict = Depends(auth.get_current_user)
):
    """Get export operation logs"""
    auth.check_permission(current_user, "audit.read")

    logs = await db.get_diagnostic_logs(category="event", limit=limit)
    return {"logs": logs}
