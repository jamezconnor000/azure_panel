#!/usr/bin/env python3
"""
HAL REST API Server

FastAPI-based REST API server for HAL access control system.
Provides HTTP endpoints for card management, access control, and event monitoring.
"""

from fastapi import FastAPI, HTTPException, Header, Depends, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from contextlib import asynccontextmanager
import sqlite3
import json
import time
import os
from datetime import datetime
from contextlib import contextmanager

# =============================================================================
# Configuration
# =============================================================================

CONFIG_FILE = "config/hal_config.json"
SDK_DB_PATH = "hal_sdk.db"
CARD_DB_PATH = "hal_cards.db"

config = {}

def load_config():
    """Load configuration from JSON file"""
    global config
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
    return config

# =============================================================================
# Database Context Managers
# =============================================================================

@contextmanager
def get_sdk_db():
    """Get SDK database connection"""
    conn = sqlite3.connect(SDK_DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

@contextmanager
def get_card_db():
    """Get card database connection"""
    conn = sqlite3.connect(CARD_DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

# =============================================================================
# Pydantic Models
# =============================================================================

class Card(BaseModel):
    card_number: int
    permission_id: int
    card_holder_name: Optional[str] = ""
    activation_date: Optional[int] = 0
    expiration_date: Optional[int] = 0
    is_active: bool = True
    pin: Optional[int] = 0

class CardResponse(BaseModel):
    card_number: int
    permission_id: int
    card_holder_name: str
    activation_date: int
    expiration_date: int
    is_active: bool
    pin: int

class AccessDecision(BaseModel):
    card_number: int
    reader_lpa: Dict[str, int]  # {type, id, node_id}

class AccessResult(BaseModel):
    decision: str  # "grant" or "deny"
    reason: str
    strike_time_ms: int
    timestamp: int

class RelayControl(BaseModel):
    relay_id: int
    duration_ms: int

class EventSubscription(BaseModel):
    max_events_before_ack: int = 100
    src_node: int = 1
    start_serial: int = 0

class Event(BaseModel):
    serial_number: int
    timestamp: int
    node_id: int
    event_type: int
    event_subtype: int
    source: Dict[str, int]
    destination: Dict[str, int]

class APIStatus(BaseModel):
    status: str
    version: str
    timestamp: int
    database: Dict[str, bool]

# =============================================================================
# Lifespan Event Handler
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events"""
    # Startup
    load_config()
    print("=" * 70)
    print("HAL REST API Server Started")
    print("=" * 70)
    print(f"Version: 1.0.0")
    print(f"SDK Database: {SDK_DB_PATH}")
    print(f"Card Database: {CARD_DB_PATH}")
    print(f"Config: {CONFIG_FILE}")
    print(f"API Enabled: {config.get('network', {}).get('enable_api', False)}")
    print("=" * 70)

    yield

    # Shutdown
    print("HAL REST API Server Stopped")

# =============================================================================
# FastAPI Application
# =============================================================================

app = FastAPI(
    title="HAL Access Control API",
    description="REST API for HAL hardware abstraction layer",
    version="1.0.0",
    lifespan=lifespan
)

# =============================================================================
# Authentication
# =============================================================================

def verify_api_key(x_api_key: Optional[str] = Header(None)):
    """Verify API key from header"""
    # In production, check against config
    # For now, allow if network.enable_api is true
    if config.get("network", {}).get("enable_api", False):
        return True
    raise HTTPException(status_code=401, detail="API access disabled")

# =============================================================================
# Health & Status Endpoints
# =============================================================================

@app.get("/", response_model=APIStatus)
async def root():
    """API status and health check"""
    sdk_db_exists = os.path.exists(SDK_DB_PATH)
    card_db_exists = os.path.exists(CARD_DB_PATH)

    return {
        "status": "running",
        "version": "1.0.0",
        "timestamp": int(time.time()),
        "database": {
            "sdk": sdk_db_exists,
            "cards": card_db_exists
        }
    }

@app.get("/api/status")
async def api_status(authorized: bool = Depends(verify_api_key)):
    """Detailed API status"""
    with get_sdk_db() as db:
        cursor = db.execute("SELECT COUNT(*) as count FROM permissions")
        permission_count = cursor.fetchone()['count']

    with get_card_db() as db:
        cursor = db.execute("SELECT COUNT(*) as count FROM Cards")
        card_count = cursor.fetchone()['count']

    return {
        "status": "healthy",
        "timestamp": int(time.time()),
        "statistics": {
            "permissions": permission_count,
            "cards": card_count
        },
        "config": {
            "listen_port": config.get("network", {}).get("listen_port", 8080),
            "api_enabled": config.get("network", {}).get("enable_api", False),
            "websocket_enabled": config.get("network", {}).get("enable_websocket", False)
        }
    }

# =============================================================================
# Card Management Endpoints
# =============================================================================

@app.post("/api/cards", status_code=status.HTTP_201_CREATED)
async def add_card(card: Card, authorized: bool = Depends(verify_api_key)):
    """Add a new card to the database"""
    try:
        with get_card_db() as db:
            db.execute("""
                INSERT INTO Cards (card_number, permission_id, card_holder_name,
                                  activation_date, expiration_date, is_active, pin)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (card.card_number, card.permission_id, card.card_holder_name or "",
                  card.activation_date, card.expiration_date,
                  1 if card.is_active else 0, card.pin or 0))
            db.commit()

        return {"status": "success", "card_number": card.card_number}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Card already exists")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/cards/{card_number}", response_model=CardResponse)
async def get_card(card_number: int, authorized: bool = Depends(verify_api_key)):
    """Get card details by card number"""
    with get_card_db() as db:
        cursor = db.execute("""
            SELECT card_number, permission_id, card_holder_name,
                   activation_date, expiration_date, is_active, pin
            FROM Cards WHERE card_number = ?
        """, (card_number,))
        row = cursor.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Card not found")

    return {
        "card_number": row['card_number'],
        "permission_id": row['permission_id'],
        "card_holder_name": row['card_holder_name'],
        "activation_date": row['activation_date'],
        "expiration_date": row['expiration_date'],
        "is_active": bool(row['is_active']),
        "pin": row['pin']
    }

@app.get("/api/cards", response_model=List[CardResponse])
async def list_cards(
    limit: int = 100,
    offset: int = 0,
    authorized: bool = Depends(verify_api_key)
):
    """List all cards with pagination"""
    with get_card_db() as db:
        cursor = db.execute("""
            SELECT card_number, permission_id, card_holder_name,
                   activation_date, expiration_date, is_active, pin
            FROM Cards
            ORDER BY card_number
            LIMIT ? OFFSET ?
        """, (limit, offset))
        rows = cursor.fetchall()

    return [
        {
            "card_number": row['card_number'],
            "permission_id": row['permission_id'],
            "card_holder_name": row['card_holder_name'],
            "activation_date": row['activation_date'],
            "expiration_date": row['expiration_date'],
            "is_active": bool(row['is_active']),
            "pin": row['pin']
        }
        for row in rows
    ]

@app.put("/api/cards/{card_number}")
async def update_card(
    card_number: int,
    card: Card,
    authorized: bool = Depends(verify_api_key)
):
    """Update an existing card"""
    with get_card_db() as db:
        cursor = db.execute("""
            UPDATE Cards
            SET permission_id = ?, card_holder_name = ?,
                activation_date = ?, expiration_date = ?,
                is_active = ?, pin = ?
            WHERE card_number = ?
        """, (card.permission_id, card.card_holder_name or "",
              card.activation_date, card.expiration_date,
              1 if card.is_active else 0, card.pin or 0, card_number))
        db.commit()

        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Card not found")

    return {"status": "success", "card_number": card_number}

@app.delete("/api/cards/{card_number}")
async def delete_card(card_number: int, authorized: bool = Depends(verify_api_key)):
    """Delete a card"""
    with get_card_db() as db:
        cursor = db.execute("DELETE FROM Cards WHERE card_number = ?", (card_number,))
        db.commit()

        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Card not found")

    return {"status": "success", "card_number": card_number}

# =============================================================================
# Access Control Endpoints
# =============================================================================

@app.post("/api/access/decide", response_model=AccessResult)
async def decide_access(
    decision: AccessDecision,
    authorized: bool = Depends(verify_api_key)
):
    """Make an access control decision"""

    # Check if card exists and is active
    with get_card_db() as db:
        cursor = db.execute("""
            SELECT card_number, permission_id, is_active, card_holder_name
            FROM Cards WHERE card_number = ?
        """, (decision.card_number,))
        card = cursor.fetchone()

    if not card:
        return {
            "decision": "deny",
            "reason": "Card not found",
            "strike_time_ms": 0,
            "timestamp": int(time.time())
        }

    if not card['is_active']:
        return {
            "decision": "deny",
            "reason": "Card is inactive",
            "strike_time_ms": 0,
            "timestamp": int(time.time())
        }

    # Check permission (simplified - in production, check against reader)
    with get_sdk_db() as db:
        cursor = db.execute("""
            SELECT id FROM permissions WHERE id = ?
        """, (card['permission_id'],))
        permission = cursor.fetchone()

    if not permission:
        return {
            "decision": "deny",
            "reason": "No valid permission",
            "strike_time_ms": 0,
            "timestamp": int(time.time())
        }

    # Grant access
    return {
        "decision": "grant",
        "reason": f"Access granted for {card['card_holder_name']}",
        "strike_time_ms": 5000,  # 5 seconds
        "timestamp": int(time.time())
    }

# =============================================================================
# Relay Control Endpoints
# =============================================================================

@app.post("/api/relays/energize")
async def energize_relay(
    control: RelayControl,
    authorized: bool = Depends(verify_api_key)
):
    """Energize a relay for specified duration"""

    # In production, this would trigger actual hardware
    # For now, just log the request
    print(f"Relay {control.relay_id} energized for {control.duration_ms}ms")

    return {
        "status": "success",
        "relay_id": control.relay_id,
        "duration_ms": control.duration_ms,
        "timestamp": int(time.time())
    }

# =============================================================================
# Event Endpoints
# =============================================================================

@app.post("/api/events/subscribe")
async def subscribe_events(
    sub: EventSubscription,
    authorized: bool = Depends(verify_api_key)
):
    """Subscribe to event stream"""

    # Store subscription (in production, use WebSocket or long-polling)
    return {
        "status": "success",
        "subscription": {
            "max_events": sub.max_events_before_ack,
            "src_node": sub.src_node,
            "start_serial": sub.start_serial
        }
    }

@app.get("/api/events", response_model=List[Event])
async def get_events(
    limit: int = 100,
    since_serial: int = 0,
    authorized: bool = Depends(verify_api_key)
):
    """Get events from event buffer"""

    # In production, query from event_database
    # For now, return empty list
    return []

@app.post("/api/events/ack")
async def acknowledge_events(
    serial_number: int,
    authorized: bool = Depends(verify_api_key)
):
    """Acknowledge events up to serial number"""

    return {
        "status": "success",
        "acknowledged_up_to": serial_number,
        "timestamp": int(time.time())
    }

# =============================================================================
# Configuration Endpoints
# =============================================================================

@app.get("/api/config")
async def get_config(authorized: bool = Depends(verify_api_key)):
    """Get current configuration"""
    return config

@app.get("/api/config/export")
async def export_config(authorized: bool = Depends(verify_api_key)):
    """Export full configuration as JSON"""

    # This would call HAL_ExportToJSON in production
    return {
        "status": "success",
        "message": "Use /api/config/download for full export"
    }

# =============================================================================
# Startup & Shutdown Events
# =============================================================================

# Startup and shutdown now handled by lifespan context manager above

# =============================================================================
# Main Entry Point
# =============================================================================

if __name__ == "__main__":
    import uvicorn

    # Load config
    load_config()

    # Get port from config
    port = config.get("network", {}).get("listen_port", 8080)

    # Run server
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
