#!/usr/bin/env python3
"""
Aether Access API Server

The "Window" into HAL - provides human-readable management interface.
This is the management UI that READS from HAL and can WRITE changes to it.

Port: 8080
Role: Management Interface - displays HAL data, logs changes, receives PACS updates

Architecture:
    External PACS --> [Aether Access API] --> [HAL Core API] --> [Local SQLite]
                             |
    Browser UI <---> [Aether Access API] <--- [HAL Core API] <-- [Event Buffer]

Key Features:
- Human-readable event reporting and search
- Cardholder and access level management UI
- Audit trail visualization
- PACS integration endpoint for receiving updates
- Dashboard statistics
"""

from fastapi import FastAPI, HTTPException, Header, Depends, Query, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, Response
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
import asyncio
import aiohttp
import json
import time
import os

# Import our event reporting module
from event_reporting import (
    EventReportingService, AccessReportingService,
    EventSearchRequest, EventDisplay, EventStatistics,
    ConfigChangeDisplay
)
from hal_client import HALClient


# =============================================================================
# Configuration
# =============================================================================

AETHER_VERSION = "2.0.0"
AETHER_PORT = int(os.environ.get("AETHER_PORT", 8080))
HAL_CORE_URL = os.environ.get("HAL_CORE_URL", "http://localhost:8081")


# =============================================================================
# Services
# =============================================================================

hal_client = HALClient(HAL_CORE_URL)
event_service = EventReportingService(HAL_CORE_URL)
access_service = AccessReportingService(HAL_CORE_URL)


# =============================================================================
# Pydantic Models
# =============================================================================

# Auth
class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: Dict[str, Any]

# Dashboard
class DashboardStats(BaseModel):
    total_cards: int
    active_cards: int
    total_doors: int
    online_doors: int
    total_events_today: int
    access_granted_today: int
    access_denied_today: int
    alarms_today: int
    recent_events: List[EventDisplay]
    hal_status: Dict[str, Any]

# PACS Integration
class PACSCardSync(BaseModel):
    card_number: str
    facility_code: int = 0
    permission_id: int = 1
    holder_name: str = ""
    activation_date: int = 0
    expiration_date: int = 0
    is_active: bool = True

class PACSAccessLevelSync(BaseModel):
    id: int
    name: str
    description: str = ""
    door_ids: List[int] = []

class PACSSyncRequest(BaseModel):
    """Bulk sync request from external PACS"""
    source: str  # e.g., "Lenel OnGuard", "CCURE 9000"
    transaction_id: Optional[str] = None
    cards: Optional[List[PACSCardSync]] = None
    access_levels: Optional[List[PACSAccessLevelSync]] = None

class PACSSyncResponse(BaseModel):
    status: str
    transaction_id: str
    cards_synced: int = 0
    access_levels_synced: int = 0
    errors: List[Dict[str, Any]] = []

# Card Management (for UI)
class CardCreateRequest(BaseModel):
    card_number: str
    facility_code: int = 0
    permission_id: int = 1
    holder_name: str = ""
    pin: Optional[str] = None
    activation_date: int = 0
    expiration_date: int = 0

class CardUpdateRequest(BaseModel):
    facility_code: Optional[int] = None
    permission_id: Optional[int] = None
    holder_name: Optional[str] = None
    pin: Optional[str] = None
    activation_date: Optional[int] = None
    expiration_date: Optional[int] = None
    is_active: Optional[bool] = None

# Access Level Management (for UI)
class AccessLevelCreateRequest(BaseModel):
    name: str
    description: str = ""
    priority: int = 0
    door_ids: List[int] = []

class AccessLevelUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[int] = None
    is_active: Optional[bool] = None
    door_ids: Optional[List[int]] = None


# =============================================================================
# Auth Helper
# =============================================================================

def get_auth_headers(source: str = "aether", user: str = None):
    """Get headers for HAL API calls"""
    headers = {"X-HAL-Source": source}
    if user:
        headers["X-HAL-User"] = user
    return headers


# =============================================================================
# Lifespan Handler
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown"""
    print("=" * 70)
    print("AETHER ACCESS API Server")
    print("=" * 70)
    print(f"Version:  {AETHER_VERSION}")
    print(f"Port:     {AETHER_PORT}")
    print(f"HAL Core: {HAL_CORE_URL}")
    print("=" * 70)
    print("Aether Access is the WINDOW into HAL")
    print("Reads HAL data, displays human-readable info, logs changes")
    print("=" * 70)

    # Test HAL connection
    try:
        health = await hal_client.get_health()
        print(f"HAL Core Status: {health.get('status', 'unknown')}")
    except Exception as e:
        print(f"WARNING: Cannot connect to HAL Core: {e}")

    yield

    print("Aether Access API Server stopped")


# =============================================================================
# FastAPI Application
# =============================================================================

app = FastAPI(
    title="Aether Access API",
    description="""
    Aether Access - The Window into HAL

    This is the management interface that provides human-readable access
    to HAL's data. It also receives updates from external PACS systems.

    Key Features:
    - Dashboard with real-time statistics
    - Event search and reporting
    - Cardholder management
    - Access level configuration
    - Audit trail viewing
    - PACS integration endpoint
    """,
    version=AETHER_VERSION,
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# Authentication Endpoints
# =============================================================================

@app.post("/api/auth/login", response_model=LoginResponse, tags=["Authentication"])
async def login(request: LoginRequest):
    """Login to Aether Access"""
    # Simple auth for now - in production use proper JWT
    if request.username == "admin" and request.password == "admin":
        return {
            "access_token": "aether-token-placeholder",
            "token_type": "bearer",
            "user": {
                "username": "admin",
                "role": "administrator",
                "permissions": ["read", "write", "admin"]
            }
        }
    raise HTTPException(status_code=401, detail="Invalid credentials")


@app.get("/api/auth/me", tags=["Authentication"])
async def get_current_user():
    """Get current user info"""
    return {
        "username": "admin",
        "role": "administrator",
        "permissions": ["read", "write", "admin"]
    }


# =============================================================================
# Dashboard Endpoints
# =============================================================================

@app.get("/api/dashboard/stats", response_model=DashboardStats, tags=["Dashboard"])
async def get_dashboard_stats():
    """Get dashboard statistics"""
    # Get HAL health
    try:
        hal_health = await hal_client.get_health()
    except Exception:
        hal_health = {"status": "unreachable"}

    # Get today's date range
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)

    # Get event statistics
    try:
        stats = await event_service.get_statistics(start_date=today_start, end_date=today_end)
    except Exception:
        stats = EventStatistics(
            total_events=0, events_by_type={}, events_by_severity={},
            events_by_door={}, events_by_hour={}, events_by_day={},
            access_granted_count=0, access_denied_count=0, grant_rate_percent=0,
            top_cardholders=[], top_doors=[], alarms_and_troubles=0, time_range={}
        )

    # Get recent events
    try:
        request = EventSearchRequest(limit=10, sort_order="desc")
        recent_events, _ = await event_service.search_events(request)
    except Exception:
        recent_events = []

    return DashboardStats(
        total_cards=hal_health.get("statistics", {}).get("cards_total", 0),
        active_cards=hal_health.get("statistics", {}).get("cards_active", 0),
        total_doors=hal_health.get("statistics", {}).get("doors", 0),
        online_doors=hal_health.get("statistics", {}).get("doors", 0),  # TODO: track online status
        total_events_today=stats.total_events,
        access_granted_today=stats.access_granted_count,
        access_denied_today=stats.access_denied_count,
        alarms_today=stats.alarms_and_troubles,
        recent_events=recent_events,
        hal_status=hal_health
    )


@app.get("/api/dashboard/health", tags=["Dashboard"])
async def get_system_health():
    """Get detailed system health"""
    try:
        return await hal_client.get_health()
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "hal_reachable": False
        }


# =============================================================================
# Event Reporting Endpoints
# =============================================================================

@app.get("/api/events", response_model=List[EventDisplay], tags=["Events"])
async def search_events(
    query: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    event_types: Optional[str] = None,  # comma-separated
    severities: Optional[str] = None,   # comma-separated
    card_numbers: Optional[str] = None, # comma-separated
    door_ids: Optional[str] = None,     # comma-separated
    granted: Optional[bool] = None,
    limit: int = Query(100, le=1000),
    offset: int = 0,
    sort_order: str = "desc"
):
    """
    Search events with human-readable formatting.
    This is what Aether Access shows in the event log.
    """
    # Parse comma-separated values
    event_type_list = [int(x) for x in event_types.split(",")] if event_types else None
    severity_list = severities.split(",") if severities else None
    card_list = card_numbers.split(",") if card_numbers else None
    door_list = [int(x) for x in door_ids.split(",")] if door_ids else None

    request = EventSearchRequest(
        query=query,
        start_date=start_date,
        end_date=end_date,
        event_types=event_type_list,
        severities=severity_list,
        card_numbers=card_list,
        door_ids=door_list,
        granted=granted,
        limit=limit,
        offset=offset,
        sort_order=sort_order
    )

    events, total = await event_service.search_events(request)
    return events


@app.get("/api/events/count", tags=["Events"])
async def get_event_count(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    event_type: Optional[int] = None
):
    """Get event count for pagination"""
    start_time = int(start_date.timestamp()) if start_date else None
    end_time = int(end_date.timestamp()) if end_date else None

    count = await event_service.client.get_event_count(
        start_time=start_time,
        end_time=end_time,
        event_type=event_type
    )
    return {"count": count}


@app.get("/api/events/statistics", response_model=EventStatistics, tags=["Events"])
async def get_event_statistics(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
):
    """Get statistical analysis of events"""
    return await event_service.get_statistics(start_date=start_date, end_date=end_date)


@app.get("/api/events/export/csv", tags=["Events"])
async def export_events_csv(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    event_types: Optional[str] = None
):
    """Export events to CSV"""
    event_type_list = [int(x) for x in event_types.split(",")] if event_types else None
    csv_data = await event_service.export_events_csv(
        start_date=start_date,
        end_date=end_date,
        event_types=event_type_list
    )

    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=events.csv"}
    )


@app.get("/api/events/export/json", tags=["Events"])
async def export_events_json(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    event_types: Optional[str] = None
):
    """Export events to JSON"""
    event_type_list = [int(x) for x in event_types.split(",")] if event_types else None
    json_data = await event_service.export_events_json(
        start_date=start_date,
        end_date=end_date,
        event_types=event_type_list
    )

    return Response(
        content=json_data,
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=events.json"}
    )


# =============================================================================
# Audit Trail Endpoints
# =============================================================================

@app.get("/api/audit/changes", response_model=List[ConfigChangeDisplay], tags=["Audit Trail"])
async def get_audit_trail(
    limit: int = Query(100, le=1000),
    offset: int = 0,
    change_type: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
):
    """
    Get configuration change audit trail.
    Shows all changes made to cards, access levels, doors, etc.
    """
    return await event_service.get_audit_trail(
        limit=limit,
        offset=offset,
        change_type=change_type,
        start_date=start_date,
        end_date=end_date
    )


# =============================================================================
# Card Management Endpoints (UI)
# =============================================================================

@app.get("/api/cards", tags=["Cards"])
async def list_cards(
    limit: int = Query(100, le=1000),
    offset: int = 0,
    search: Optional[str] = None,
    active_only: bool = False,
    access_level_id: Optional[int] = None
):
    """
    List cardholders with human-readable details.
    Enriched with access level names and formatted dates.
    """
    return await access_service.get_cardholders(
        limit=limit,
        offset=offset,
        search=search,
        active_only=active_only,
        access_level_id=access_level_id
    )


@app.get("/api/cards/{card_number}", tags=["Cards"])
async def get_card(card_number: str):
    """Get cardholder details"""
    try:
        return await hal_client.get_card(card_number)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/api/cards", status_code=status.HTTP_201_CREATED, tags=["Cards"])
async def create_card(request: CardCreateRequest, current_user: str = "admin"):
    """
    Add a new cardholder.
    Changes are logged to HAL's audit trail.
    """
    try:
        result = await hal_client.create_card(
            card_number=request.card_number,
            facility_code=request.facility_code,
            permission_id=request.permission_id,
            holder_name=request.holder_name,
            pin=request.pin,
            activation_date=request.activation_date,
            expiration_date=request.expiration_date,
            source="aether",
            source_user=current_user
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.put("/api/cards/{card_number}", tags=["Cards"])
async def update_card(card_number: str, request: CardUpdateRequest, current_user: str = "admin"):
    """
    Update cardholder details.
    Changes are logged to HAL's audit trail.
    """
    update_data = request.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    try:
        result = await hal_client.update_card(
            card_number=card_number,
            source="aether",
            source_user=current_user,
            **update_data
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/api/cards/{card_number}", tags=["Cards"])
async def delete_card(card_number: str, current_user: str = "admin"):
    """
    Delete a cardholder.
    Changes are logged to HAL's audit trail.
    """
    try:
        return await hal_client.delete_card(
            card_number=card_number,
            source="aether",
            source_user=current_user
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# =============================================================================
# Access Level Management Endpoints (UI)
# =============================================================================

@app.get("/api/access-levels", tags=["Access Levels"])
async def list_access_levels():
    """
    List access levels with cardholder counts.
    Enriched with statistics for the UI.
    """
    return await access_service.get_access_levels_report()


@app.get("/api/access-levels/{level_id}", tags=["Access Levels"])
async def get_access_level(level_id: int):
    """Get access level details"""
    try:
        return await hal_client.get_access_level(level_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/api/access-levels", status_code=status.HTTP_201_CREATED, tags=["Access Levels"])
async def create_access_level(request: AccessLevelCreateRequest, current_user: str = "admin"):
    """Create a new access level"""
    try:
        return await hal_client.create_access_level(
            name=request.name,
            description=request.description,
            priority=request.priority,
            door_ids=request.door_ids,
            source="aether",
            source_user=current_user
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.put("/api/access-levels/{level_id}", tags=["Access Levels"])
async def update_access_level(level_id: int, request: AccessLevelUpdateRequest, current_user: str = "admin"):
    """Update an access level"""
    update_data = request.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    try:
        return await hal_client.update_access_level(
            level_id=level_id,
            source="aether",
            source_user=current_user,
            **update_data
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/api/access-levels/{level_id}", tags=["Access Levels"])
async def delete_access_level(level_id: int, current_user: str = "admin"):
    """Delete an access level"""
    try:
        return await hal_client.delete_access_level(
            level_id=level_id,
            source="aether",
            source_user=current_user
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# =============================================================================
# Door Management Endpoints (UI)
# =============================================================================

@app.get("/api/doors", tags=["Doors"])
async def list_doors():
    """List doors with status information"""
    return await access_service.get_door_report()


@app.get("/api/doors/{door_id}", tags=["Doors"])
async def get_door(door_id: int):
    """Get door details"""
    try:
        return await hal_client.get_door(door_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/api/doors/{door_id}/control", tags=["Doors"])
async def control_door(door_id: int, action: str, duration_ms: Optional[int] = None, current_user: str = "admin"):
    """
    Control door lock state.
    Actions: lock, unlock, momentary_unlock, lockdown
    """
    try:
        return await hal_client.control_door(
            door_id=door_id,
            action=action,
            duration_ms=duration_ms,
            source="aether",
            source_user=current_user
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# =============================================================================
# PACS Integration Endpoints
# =============================================================================

@app.post("/api/pacs/sync", response_model=PACSSyncResponse, tags=["PACS Integration"])
async def pacs_sync(request: PACSSyncRequest):
    """
    Bulk sync endpoint for external PACS systems.

    External PACS (Lenel, CCURE, Genetec, etc.) push updates here.
    Aether Access forwards to HAL and logs the transaction.

    Example:
    ```
    POST /api/pacs/sync
    {
        "source": "Lenel OnGuard",
        "transaction_id": "abc123",
        "cards": [
            {"card_number": "12345678", "permission_id": 5, "holder_name": "John Doe"}
        ],
        "access_levels": [
            {"id": 5, "name": "All Access", "door_ids": [1, 2, 3]}
        ]
    }
    ```
    """
    transaction_id = request.transaction_id or f"pacs-{int(time.time())}"

    try:
        result = await hal_client.bulk_sync(
            cards=request.cards,
            access_levels=request.access_levels,
            source="pacs",
            source_user=request.source,
            transaction_id=transaction_id
        )

        return PACSSyncResponse(
            status="success",
            transaction_id=transaction_id,
            cards_synced=result.get("cards", {}).get("created", 0) + result.get("cards", {}).get("updated", 0),
            access_levels_synced=result.get("access_levels", {}).get("created", 0) + result.get("access_levels", {}).get("updated", 0),
            errors=result.get("cards", {}).get("errors", []) + result.get("access_levels", {}).get("errors", [])
        )

    except Exception as e:
        return PACSSyncResponse(
            status="error",
            transaction_id=transaction_id,
            errors=[{"error": str(e)}]
        )


@app.post("/api/pacs/webhook", tags=["PACS Integration"])
async def pacs_webhook(request: Request):
    """
    Webhook endpoint for real-time PACS updates.

    PACS systems can send individual changes here for immediate processing.
    """
    body = await request.json()

    # Determine operation type
    operation = body.get("operation", "unknown")
    resource = body.get("resource", "unknown")

    try:
        if resource == "card":
            if operation == "create":
                return await hal_client.create_card(
                    source="pacs",
                    source_user=body.get("source", "webhook"),
                    **body.get("data", {})
                )
            elif operation == "update":
                return await hal_client.update_card(
                    card_number=body.get("card_number"),
                    source="pacs",
                    source_user=body.get("source", "webhook"),
                    **body.get("data", {})
                )
            elif operation == "delete":
                return await hal_client.delete_card(
                    card_number=body.get("card_number"),
                    source="pacs",
                    source_user=body.get("source", "webhook")
                )

        elif resource == "access_level":
            if operation == "create":
                return await hal_client.create_access_level(
                    source="pacs",
                    source_user=body.get("source", "webhook"),
                    **body.get("data", {})
                )
            elif operation == "update":
                return await hal_client.update_access_level(
                    level_id=body.get("level_id"),
                    source="pacs",
                    source_user=body.get("source", "webhook"),
                    **body.get("data", {})
                )

        return {"status": "processed", "operation": operation, "resource": resource}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/pacs/events", tags=["PACS Integration"])
async def get_events_for_pacs(
    since: Optional[int] = None,
    limit: int = Query(1000, le=10000)
):
    """
    Get events for PACS consumption.

    External PACS systems can poll this endpoint to receive events
    from HAL for their own records.

    Parameters:
    - since: Unix timestamp to get events after
    - limit: Maximum number of events to return
    """
    async with aiohttp.ClientSession() as session:
        params = {"limit": limit, "order": "asc"}
        if since:
            params["start_time"] = since

        async with session.get(f"{HAL_CORE_URL}/hal/events", params=params) as resp:
            if resp.status != 200:
                return {"events": [], "error": "Failed to fetch events"}
            events = await resp.json()

    return {
        "events": events,
        "count": len(events),
        "last_timestamp": events[-1]["timestamp"] if events else None
    }


# =============================================================================
# Timezone & Holiday Endpoints
# =============================================================================

@app.get("/api/timezones", tags=["Timezones"])
async def list_timezones():
    """List all timezones"""
    return await hal_client.list_timezones()


@app.get("/api/holidays", tags=["Holidays"])
async def list_holidays(year: Optional[int] = None):
    """List holidays"""
    return await hal_client.list_holidays(year=year)


# =============================================================================
# System Configuration
# =============================================================================

@app.get("/api/system/export", tags=["System"])
async def export_configuration():
    """Export full system configuration from HAL"""
    return await hal_client.export_configuration()


@app.get("/api/system/info", tags=["System"])
async def get_system_info():
    """Get system information"""
    return {
        "aether_version": AETHER_VERSION,
        "aether_port": AETHER_PORT,
        "hal_url": HAL_CORE_URL,
        "features": {
            "event_reporting": True,
            "audit_trail": True,
            "pacs_integration": True,
            "export_csv": True,
            "export_json": True
        }
    }


# =============================================================================
# Main Entry Point
# =============================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=AETHER_PORT,
        log_level="info"
    )
