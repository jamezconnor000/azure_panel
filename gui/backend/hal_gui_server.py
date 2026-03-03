#!/usr/bin/env python3
"""
HAL GUI Server - Modern Web Interface for HAL System
FastAPI backend with WebSocket support for real-time updates
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import json
import sqlite3
import subprocess
import os
import sys

# Add parent directory to path for HAL imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

app = FastAPI(
    title="Aether_Access Control Panel API",
    description="Modern web interface for Hardware Abstraction Layer with OSDP Secure Channel",
    version="2.0.1"
)

# CORS middleware for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # Vite/React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =============================================================================
# Data Models
# =============================================================================

class SystemStatus(str, Enum):
    HEALTHY = "healthy"
    WARNING = "warning"
    ERROR = "error"
    OFFLINE = "offline"

class ReaderStatus(BaseModel):
    id: int
    address: int
    name: str
    status: SystemStatus
    secure_channel: bool
    last_seen: datetime
    firmware_version: Optional[str] = None
    packets_encrypted: int = 0
    packets_decrypted: int = 0
    errors: int = 0

class SecureChannelStatus(BaseModel):
    reader_id: int
    state: str  # INIT, CHALLENGE_SENT, CHALLENGE_RECV, ESTABLISHED, ERROR
    enabled: bool
    keys_derived: bool
    handshakes_completed: int
    handshakes_failed: int
    packets_encrypted: int
    packets_decrypted: int
    mac_failures: int
    cryptogram_failures: int
    last_handshake: Optional[datetime]
    handshake_duration_ms: Optional[float]

class AccessEvent(BaseModel):
    id: int
    timestamp: datetime
    event_type: str  # ACCESS_GRANT, ACCESS_DENY, SECURE_INIT, SYSTEM_ERROR
    reader_id: int
    card_number: Optional[str] = None
    user_name: Optional[str] = None
    details: str
    severity: str  # INFO, WARNING, ERROR, CRITICAL

class DashboardMetrics(BaseModel):
    total_readers: int
    readers_online: int
    secure_channels_active: int
    events_today: int
    access_grants_today: int
    access_denies_today: int
    system_health: SystemStatus
    uptime_seconds: int
    events_per_minute: float

class DiagnosticAlert(BaseModel):
    id: int
    timestamp: datetime
    severity: str  # INFO, WARNING, ERROR, CRITICAL
    category: str  # SECURE_CHANNEL, READER, SYSTEM, DATABASE
    message: str
    details: Optional[str]
    acknowledged: bool = False

# =============================================================================
# WebSocket Connection Manager
# =============================================================================

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
                pass  # Client disconnected

manager = ConnectionManager()

# =============================================================================
# Dashboard Endpoints
# =============================================================================

@app.get("/")
async def root():
    return {
        "name": "Aether_Access Control Panel API",
        "version": "2.0.1",
        "status": "operational",
        "endpoints": {
            "dashboard": "/api/v1/dashboard",
            "readers": "/api/v1/readers",
            "events": "/api/v1/events",
            "secure": "/api/v1/secure",
            "diagnostics": "/api/v1/diagnostics",
            "websocket": "/ws/live"
        }
    }

@app.get("/api/v1/dashboard/metrics", response_model=DashboardMetrics)
async def get_dashboard_metrics():
    """Get real-time dashboard metrics"""
    # TODO: Integrate with actual HAL system
    # For now, return mock data
    return DashboardMetrics(
        total_readers=3,
        readers_online=2,
        secure_channels_active=2,
        events_today=1234,
        access_grants_today=1156,
        access_denies_today=78,
        system_health=SystemStatus.HEALTHY,
        uptime_seconds=86400,
        events_per_minute=12.5
    )

@app.get("/api/v1/dashboard/alerts", response_model=List[DiagnosticAlert])
async def get_active_alerts():
    """Get active system alerts"""
    # TODO: Read from diagnostic logger
    return [
        DiagnosticAlert(
            id=1,
            timestamp=datetime.now() - timedelta(minutes=5),
            severity="WARNING",
            category="READER",
            message="Reader 3 offline for 2 hours",
            details="Last communication: 2024-11-08 12:30:00",
            acknowledged=False
        )
    ]

# =============================================================================
# Reader Endpoints
# =============================================================================

@app.get("/api/v1/readers", response_model=List[ReaderStatus])
async def get_readers():
    """List all configured readers"""
    return [
        ReaderStatus(
            id=1,
            address=0x01,
            name="Main Entrance",
            status=SystemStatus.HEALTHY,
            secure_channel=True,
            last_seen=datetime.now(),
            firmware_version="4.5.0",
            packets_encrypted=1523,
            packets_decrypted=1489,
            errors=0
        ),
        ReaderStatus(
            id=2,
            address=0x02,
            name="Back Door",
            status=SystemStatus.HEALTHY,
            secure_channel=True,
            last_seen=datetime.now() - timedelta(seconds=5),
            firmware_version="4.5.0",
            packets_encrypted=891,
            packets_decrypted=876,
            errors=0
        ),
        ReaderStatus(
            id=3,
            address=0x03,
            name="Parking Garage",
            status=SystemStatus.OFFLINE,
            secure_channel=False,
            last_seen=datetime.now() - timedelta(hours=2),
            firmware_version="4.4.2",
            packets_encrypted=0,
            packets_decrypted=0,
            errors=3
        )
    ]

@app.get("/api/v1/readers/{reader_id}", response_model=ReaderStatus)
async def get_reader(reader_id: int):
    """Get specific reader details"""
    readers = await get_readers()
    for reader in readers:
        if reader.id == reader_id:
            return reader
    raise HTTPException(status_code=404, detail="Reader not found")

@app.post("/api/v1/readers/{reader_id}/reset")
async def reset_reader(reader_id: int):
    """Reset a reader"""
    # TODO: Implement actual reader reset
    return {"status": "success", "message": f"Reader {reader_id} reset initiated"}

@app.post("/api/v1/readers/{reader_id}/secure/handshake")
async def reinitialize_secure_channel(reader_id: int):
    """Reinitialize secure channel for a reader"""
    # TODO: Call OSDP_Reader_EstablishSecureChannel
    await manager.broadcast({
        "type": "secure_channel",
        "action": "handshake_initiated",
        "reader_id": reader_id,
        "timestamp": datetime.now().isoformat()
    })
    return {"status": "success", "message": f"Secure channel handshake initiated for reader {reader_id}"}

# =============================================================================
# Secure Channel Endpoints
# =============================================================================

@app.get("/api/v1/secure/status", response_model=List[SecureChannelStatus])
async def get_all_secure_channel_status():
    """Get secure channel status for all readers"""
    return [
        SecureChannelStatus(
            reader_id=1,
            state="ESTABLISHED",
            enabled=True,
            keys_derived=True,
            handshakes_completed=10,
            handshakes_failed=0,
            packets_encrypted=1523,
            packets_decrypted=1489,
            mac_failures=0,
            cryptogram_failures=0,
            last_handshake=datetime.now() - timedelta(hours=2),
            handshake_duration_ms=285.3
        ),
        SecureChannelStatus(
            reader_id=2,
            state="ESTABLISHED",
            enabled=True,
            keys_derived=True,
            handshakes_completed=8,
            handshakes_failed=0,
            packets_encrypted=891,
            packets_decrypted=876,
            mac_failures=0,
            cryptogram_failures=0,
            last_handshake=datetime.now() - timedelta(hours=3),
            handshake_duration_ms=312.7
        ),
        SecureChannelStatus(
            reader_id=3,
            state="INIT",
            enabled=False,
            keys_derived=False,
            handshakes_completed=0,
            handshakes_failed=3,
            packets_encrypted=0,
            packets_decrypted=0,
            mac_failures=0,
            cryptogram_failures=3,
            last_handshake=None,
            handshake_duration_ms=None
        )
    ]

@app.get("/api/v1/secure/{reader_id}", response_model=SecureChannelStatus)
async def get_secure_channel_status(reader_id: int):
    """Get secure channel status for specific reader"""
    statuses = await get_all_secure_channel_status()
    for status in statuses:
        if status.reader_id == reader_id:
            return status
    raise HTTPException(status_code=404, detail="Reader not found")

# =============================================================================
# Events Endpoints
# =============================================================================

@app.get("/api/v1/events", response_model=List[AccessEvent])
async def get_events(
    limit: int = 50,
    offset: int = 0,
    event_type: Optional[str] = None,
    reader_id: Optional[int] = None
):
    """Get access events with filtering and pagination"""
    # TODO: Query actual HAL event database
    events = []

    # Generate mock events for demonstration
    event_types = ["ACCESS_GRANT", "ACCESS_DENY", "SECURE_INIT", "SYSTEM_ERROR"]
    for i in range(limit):
        events.append(AccessEvent(
            id=i + offset,
            timestamp=datetime.now() - timedelta(minutes=i),
            event_type=event_types[i % len(event_types)],
            reader_id=(i % 3) + 1,
            card_number=f"*****{1000 + i:04d}" if i % 4 != 3 else None,
            user_name=f"User {i}" if i % 5 == 0 else None,
            details=f"Event details {i}",
            severity="INFO" if i % 4 != 3 else "WARNING"
        ))

    return events

@app.get("/api/v1/events/export")
async def export_events(format: str = "csv"):
    """Export events to CSV or JSON"""
    # TODO: Implement actual export
    if format == "csv":
        return StreamingResponse(
            iter(["timestamp,event_type,reader_id,details\n"]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=events.csv"}
        )
    return {"events": []}

# =============================================================================
# Diagnostics Endpoints
# =============================================================================

@app.get("/api/v1/diagnostics/logs")
async def get_logs(
    level: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = 100
):
    """Get diagnostic logs with filtering"""
    # TODO: Read from actual log files
    logs = []
    for i in range(limit):
        logs.append({
            "timestamp": (datetime.now() - timedelta(seconds=i)).isoformat(),
            "level": ["DEBUG", "INFO", "WARNING", "ERROR"][i % 4],
            "category": ["OSDP", "SECURE", "SYSTEM", "DATABASE"][i % 4],
            "file": "hal.c",
            "line": 100 + i,
            "function": "test_function",
            "message": f"Log message {i}"
        })

    return {"logs": logs, "total": limit}

@app.post("/api/v1/diagnostics/analyze")
async def run_diagnostic_analysis():
    """Run feedback loop analysis"""
    # TODO: Call hal_feedback_loop.py
    return {
        "status": "completed",
        "analysis": {
            "total_errors": 3,
            "critical_issues": 0,
            "recommendations": [
                "Reader 3 is offline - check power and connectivity"
            ]
        }
    }

@app.get("/api/v1/diagnostics/report")
async def generate_diagnostic_report():
    """Generate comprehensive diagnostic report"""
    # TODO: Generate actual report
    return {
        "generated_at": datetime.now().isoformat(),
        "system_health": "healthy",
        "secure_channel_status": "operational",
        "total_events": 1234,
        "errors": 3
    }

# =============================================================================
# WebSocket Endpoint for Live Updates
# =============================================================================

@app.websocket("/ws/live")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await manager.connect(websocket)

    try:
        # Send initial connection message
        await websocket.send_json({
            "type": "connected",
            "message": "Connected to Aether_Access Control Panel",
            "timestamp": datetime.now().isoformat()
        })

        # Keep connection alive and handle incoming messages
        while True:
            # Wait for messages from client
            data = await websocket.receive_text()
            message = json.loads(data)

            # Echo back for now
            await websocket.send_json({
                "type": "echo",
                "data": message,
                "timestamp": datetime.now().isoformat()
            })

            # Also broadcast to all clients
            await manager.broadcast({
                "type": "broadcast",
                "source": "client",
                "data": message,
                "timestamp": datetime.now().isoformat()
            })

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast({
            "type": "user_disconnected",
            "timestamp": datetime.now().isoformat()
        })

# =============================================================================
# Background Task for Simulating Live Updates
# =============================================================================

async def simulate_live_events():
    """Background task to simulate live events"""
    while True:
        await asyncio.sleep(5)  # Every 5 seconds

        # Simulate a new event
        await manager.broadcast({
            "type": "new_event",
            "event": {
                "timestamp": datetime.now().isoformat(),
                "event_type": "ACCESS_GRANT",
                "reader_id": 1,
                "details": "New access event"
            }
        })

@app.on_event("startup")
async def startup_event():
    """Start background tasks on startup"""
    # Start live event simulation in background
    asyncio.create_task(simulate_live_events())

    print("="*80)
    print(" HAL GUI Server Started".center(80))
    print("="*80)
    print(f" API Documentation: http://localhost:8080/docs")
    print(f" WebSocket Endpoint: ws://localhost:8080/ws/live")
    print(f" Frontend Dev Server: http://localhost:3000")
    print("="*80)

# =============================================================================
# Main Entry Point
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8080,
        log_level="info",
        reload=True  # Auto-reload on code changes (development only)
    )
