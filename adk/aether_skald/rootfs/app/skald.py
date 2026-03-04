#!/usr/bin/env python3
"""
Aether Skald - Event Chronicle & Audit Trail
Part of Aether Access 4.0 "Bifrost's Light"

The Skald (Norse: storyteller/poet) records all events that transpire
within the access control system. It provides:
- Real-time event chronicle
- Audit trail with integrity verification
- Event aggregation and analytics
- Export to various formats (CSV, JSON, SIEM)
- Long-term archival storage

"The Skald remembers all."
"""

import os
import sys
import json
import sqlite3
import hashlib
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from pathlib import Path

# FastAPI for REST interface
from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel
import uvicorn

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.environ.get("SKALD_LOG_LEVEL", "INFO")),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.environ.get("SKALD_LOG_PATH", "/app/logs/aether_skald.log"))
    ]
)
logger = logging.getLogger("aether_skald")

# ============================================================================
# Configuration
# ============================================================================

SKALD_VERSION = "4.0.0"
DATABASE_PATH = os.environ.get("SKALD_DATABASE_PATH", "/app/data/chronicle.db")
CHRONICLE_PATH = os.environ.get("SKALD_CHRONICLE_PATH", "/app/data/chronicles")
THRALL_SOCKET = os.environ.get("THRALL_SOCKET", "/var/run/thrall.sock")
BIFROST_URL = os.environ.get("BIFROST_URL", "http://localhost:8080")
PORT = int(os.environ.get("SKALD_PORT", 8090))

# ============================================================================
# Database Schema
# ============================================================================

SCHEMA = """
-- Chronicle Events (immutable audit log)
CREATE TABLE IF NOT EXISTS chronicle (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id TEXT UNIQUE NOT NULL,
    timestamp TEXT NOT NULL,
    event_type TEXT NOT NULL,
    source TEXT NOT NULL,
    actor_id TEXT,
    actor_name TEXT,
    target_id TEXT,
    target_name TEXT,
    action TEXT NOT NULL,
    result TEXT,
    details TEXT,
    hash TEXT NOT NULL,
    prev_hash TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Chronicle Blocks (for integrity chains)
CREATE TABLE IF NOT EXISTS blocks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    block_number INTEGER UNIQUE NOT NULL,
    start_event_id INTEGER NOT NULL,
    end_event_id INTEGER NOT NULL,
    event_count INTEGER NOT NULL,
    merkle_root TEXT NOT NULL,
    prev_block_hash TEXT,
    block_hash TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Event Aggregations (hourly/daily summaries)
CREATE TABLE IF NOT EXISTS aggregations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    period_type TEXT NOT NULL,
    period_start TEXT NOT NULL,
    period_end TEXT NOT NULL,
    event_type TEXT,
    total_count INTEGER DEFAULT 0,
    granted_count INTEGER DEFAULT 0,
    denied_count INTEGER DEFAULT 0,
    unique_actors INTEGER DEFAULT 0,
    unique_targets INTEGER DEFAULT 0,
    details TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(period_type, period_start, event_type)
);

-- Export Jobs
CREATE TABLE IF NOT EXISTS exports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id TEXT UNIQUE NOT NULL,
    status TEXT DEFAULT 'pending',
    format TEXT NOT NULL,
    filters TEXT,
    file_path TEXT,
    record_count INTEGER DEFAULT 0,
    started_at TEXT,
    completed_at TEXT,
    error TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_chronicle_timestamp ON chronicle(timestamp);
CREATE INDEX IF NOT EXISTS idx_chronicle_type ON chronicle(event_type);
CREATE INDEX IF NOT EXISTS idx_chronicle_actor ON chronicle(actor_id);
CREATE INDEX IF NOT EXISTS idx_chronicle_target ON chronicle(target_id);
CREATE INDEX IF NOT EXISTS idx_aggregations_period ON aggregations(period_type, period_start);
"""

# ============================================================================
# Models
# ============================================================================

class ChronicleEvent(BaseModel):
    event_type: str
    source: str
    action: str
    actor_id: Optional[str] = None
    actor_name: Optional[str] = None
    target_id: Optional[str] = None
    target_name: Optional[str] = None
    result: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

class ExportRequest(BaseModel):
    format: str = "json"  # json, csv, siem
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    event_types: Optional[List[str]] = None
    actor_id: Optional[str] = None
    target_id: Optional[str] = None

# ============================================================================
# Chronicle Database
# ============================================================================

class ChronicleDB:
    """Immutable event chronicle with integrity verification."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = None
        self._init_db()

    def _init_db(self):
        """Initialize database and schema."""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)
        self.conn.commit()
        logger.info(f"Chronicle database initialized: {self.db_path}")

    def _compute_hash(self, event: dict, prev_hash: str = None) -> str:
        """Compute SHA-256 hash of event for integrity chain."""
        data = json.dumps({
            "timestamp": event.get("timestamp"),
            "event_type": event.get("event_type"),
            "source": event.get("source"),
            "action": event.get("action"),
            "actor_id": event.get("actor_id"),
            "target_id": event.get("target_id"),
            "result": event.get("result"),
            "prev_hash": prev_hash
        }, sort_keys=True)
        return hashlib.sha256(data.encode()).hexdigest()

    def record_event(self, event: ChronicleEvent) -> dict:
        """Record an event to the chronicle (immutable)."""
        timestamp = datetime.utcnow().isoformat() + "Z"
        event_id = f"EVT-{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}"

        # Get previous hash for chain
        cursor = self.conn.execute(
            "SELECT hash FROM chronicle ORDER BY id DESC LIMIT 1"
        )
        row = cursor.fetchone()
        prev_hash = row["hash"] if row else "GENESIS"

        # Build event record
        record = {
            "event_id": event_id,
            "timestamp": timestamp,
            "event_type": event.event_type,
            "source": event.source,
            "actor_id": event.actor_id,
            "actor_name": event.actor_name,
            "target_id": event.target_id,
            "target_name": event.target_name,
            "action": event.action,
            "result": event.result,
            "details": json.dumps(event.details) if event.details else None
        }

        # Compute integrity hash
        record["hash"] = self._compute_hash(record, prev_hash)
        record["prev_hash"] = prev_hash

        # Insert (immutable - no updates allowed)
        self.conn.execute("""
            INSERT INTO chronicle (
                event_id, timestamp, event_type, source, actor_id, actor_name,
                target_id, target_name, action, result, details, hash, prev_hash
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            record["event_id"], record["timestamp"], record["event_type"],
            record["source"], record["actor_id"], record["actor_name"],
            record["target_id"], record["target_name"], record["action"],
            record["result"], record["details"], record["hash"], record["prev_hash"]
        ))
        self.conn.commit()

        logger.debug(f"Chronicle recorded: {event_id} - {event.event_type}/{event.action}")
        return record

    def query_events(
        self,
        start_date: str = None,
        end_date: str = None,
        event_types: List[str] = None,
        actor_id: str = None,
        target_id: str = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[dict]:
        """Query chronicle events with filters."""
        query = "SELECT * FROM chronicle WHERE 1=1"
        params = []

        if start_date:
            query += " AND timestamp >= ?"
            params.append(start_date)
        if end_date:
            query += " AND timestamp <= ?"
            params.append(end_date)
        if event_types:
            placeholders = ",".join(["?" for _ in event_types])
            query += f" AND event_type IN ({placeholders})"
            params.extend(event_types)
        if actor_id:
            query += " AND actor_id = ?"
            params.append(actor_id)
        if target_id:
            query += " AND target_id = ?"
            params.append(target_id)

        query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cursor = self.conn.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

    def verify_integrity(self, start_id: int = None, end_id: int = None) -> dict:
        """Verify chronicle integrity chain."""
        query = "SELECT * FROM chronicle"
        params = []

        if start_id:
            query += " WHERE id >= ?"
            params.append(start_id)
            if end_id:
                query += " AND id <= ?"
                params.append(end_id)
        elif end_id:
            query += " WHERE id <= ?"
            params.append(end_id)

        query += " ORDER BY id ASC"
        cursor = self.conn.execute(query, params)

        prev_hash = None
        verified = 0
        errors = []

        for row in cursor:
            record = dict(row)
            expected_hash = self._compute_hash(record, prev_hash or record["prev_hash"])

            if record["hash"] != expected_hash:
                errors.append({
                    "event_id": record["event_id"],
                    "error": "Hash mismatch",
                    "expected": expected_hash,
                    "actual": record["hash"]
                })
            else:
                verified += 1

            prev_hash = record["hash"]

        return {
            "verified": verified,
            "errors": len(errors),
            "error_details": errors[:10],  # First 10 errors
            "integrity": "VALID" if not errors else "CORRUPTED"
        }

    def get_statistics(self) -> dict:
        """Get chronicle statistics."""
        cursor = self.conn.execute("""
            SELECT
                COUNT(*) as total_events,
                MIN(timestamp) as first_event,
                MAX(timestamp) as last_event,
                COUNT(DISTINCT event_type) as event_types,
                COUNT(DISTINCT actor_id) as unique_actors,
                COUNT(DISTINCT target_id) as unique_targets
            FROM chronicle
        """)
        row = cursor.fetchone()

        # Event type breakdown
        type_cursor = self.conn.execute("""
            SELECT event_type, COUNT(*) as count
            FROM chronicle
            GROUP BY event_type
            ORDER BY count DESC
            LIMIT 10
        """)

        return {
            "total_events": row["total_events"],
            "first_event": row["first_event"],
            "last_event": row["last_event"],
            "event_types": row["event_types"],
            "unique_actors": row["unique_actors"],
            "unique_targets": row["unique_targets"],
            "type_breakdown": [dict(r) for r in type_cursor.fetchall()]
        }

# ============================================================================
# FastAPI Application
# ============================================================================

app = FastAPI(
    title="Aether Skald",
    description="Event Chronicle & Audit Trail - The Storyteller",
    version=SKALD_VERSION
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize chronicle
chronicle = ChronicleDB(DATABASE_PATH)

# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/")
async def root():
    """Skald status."""
    return {
        "name": "Aether Skald",
        "version": SKALD_VERSION,
        "status": "chronicling",
        "motto": "The Skald remembers all."
    }

@app.get("/api/v1/status")
async def status():
    """Get Skald status and statistics."""
    stats = chronicle.get_statistics()
    return {
        "status": "online",
        "version": SKALD_VERSION,
        "database": DATABASE_PATH,
        "statistics": stats
    }

@app.post("/api/v1/chronicle")
async def record_event(event: ChronicleEvent):
    """Record an event to the chronicle."""
    try:
        record = chronicle.record_event(event)
        return {"status": "recorded", "event_id": record["event_id"]}
    except Exception as e:
        logger.error(f"Failed to record event: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/chronicle")
async def query_chronicle(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    event_type: Optional[str] = None,
    actor_id: Optional[str] = None,
    target_id: Optional[str] = None,
    limit: int = Query(default=100, le=1000),
    offset: int = 0
):
    """Query chronicle events."""
    event_types = [event_type] if event_type else None
    events = chronicle.query_events(
        start_date=start_date,
        end_date=end_date,
        event_types=event_types,
        actor_id=actor_id,
        target_id=target_id,
        limit=limit,
        offset=offset
    )
    return {"events": events, "count": len(events)}

@app.get("/api/v1/chronicle/{event_id}")
async def get_event(event_id: str):
    """Get a specific event by ID."""
    cursor = chronicle.conn.execute(
        "SELECT * FROM chronicle WHERE event_id = ?", (event_id,)
    )
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Event not found")
    return dict(row)

@app.get("/api/v1/verify")
async def verify_integrity(
    start_id: Optional[int] = None,
    end_id: Optional[int] = None
):
    """Verify chronicle integrity chain."""
    result = chronicle.verify_integrity(start_id, end_id)
    return result

@app.post("/api/v1/export")
async def create_export(request: ExportRequest, background_tasks: BackgroundTasks):
    """Create an export job."""
    import uuid
    job_id = f"EXP-{uuid.uuid4().hex[:12]}"

    # Queue export job
    chronicle.conn.execute("""
        INSERT INTO exports (job_id, format, filters, status, started_at)
        VALUES (?, ?, ?, 'processing', ?)
    """, (job_id, request.format, json.dumps(request.dict()), datetime.utcnow().isoformat()))
    chronicle.conn.commit()

    # Run export in background
    background_tasks.add_task(run_export, job_id, request)

    return {"job_id": job_id, "status": "processing"}

@app.get("/api/v1/export/{job_id}")
async def get_export_status(job_id: str):
    """Get export job status."""
    cursor = chronicle.conn.execute(
        "SELECT * FROM exports WHERE job_id = ?", (job_id,)
    )
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Export job not found")
    return dict(row)

@app.get("/api/v1/export/{job_id}/download")
async def download_export(job_id: str):
    """Download completed export."""
    cursor = chronicle.conn.execute(
        "SELECT * FROM exports WHERE job_id = ? AND status = 'completed'", (job_id,)
    )
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Export not found or not completed")

    file_path = row["file_path"]
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Export file not found")

    return FileResponse(
        file_path,
        filename=os.path.basename(file_path),
        media_type="application/octet-stream"
    )

# ============================================================================
# Export Functions
# ============================================================================

async def run_export(job_id: str, request: ExportRequest):
    """Run export job."""
    try:
        events = chronicle.query_events(
            start_date=request.start_date,
            end_date=request.end_date,
            event_types=request.event_types,
            actor_id=request.actor_id,
            target_id=request.target_id,
            limit=100000
        )

        # Create export file
        Path(CHRONICLE_PATH).mkdir(parents=True, exist_ok=True)
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

        if request.format == "json":
            file_path = f"{CHRONICLE_PATH}/export_{timestamp}.json"
            with open(file_path, "w") as f:
                json.dump(events, f, indent=2)

        elif request.format == "csv":
            import csv
            file_path = f"{CHRONICLE_PATH}/export_{timestamp}.csv"
            with open(file_path, "w", newline="") as f:
                if events:
                    writer = csv.DictWriter(f, fieldnames=events[0].keys())
                    writer.writeheader()
                    writer.writerows(events)

        else:  # siem format
            file_path = f"{CHRONICLE_PATH}/export_{timestamp}.siem"
            with open(file_path, "w") as f:
                for event in events:
                    # CEF format for SIEM
                    cef = f"CEF:0|Aether|Skald|4.0|{event['event_type']}|{event['action']}|5|"
                    cef += f"src={event.get('actor_id', '')} dst={event.get('target_id', '')} "
                    cef += f"outcome={event.get('result', '')} rt={event['timestamp']}\n"
                    f.write(cef)

        # Update job status
        chronicle.conn.execute("""
            UPDATE exports SET status = 'completed', file_path = ?,
            record_count = ?, completed_at = ? WHERE job_id = ?
        """, (file_path, len(events), datetime.utcnow().isoformat(), job_id))
        chronicle.conn.commit()

        logger.info(f"Export completed: {job_id} - {len(events)} records")

    except Exception as e:
        chronicle.conn.execute("""
            UPDATE exports SET status = 'failed', error = ?, completed_at = ?
            WHERE job_id = ?
        """, (str(e), datetime.utcnow().isoformat(), job_id))
        chronicle.conn.commit()
        logger.error(f"Export failed: {job_id} - {e}")

# ============================================================================
# Event Listener (connects to Thrall/Bifrost)
# ============================================================================

async def event_listener():
    """Listen for events from Thrall and Bifrost."""
    import aiohttp

    logger.info("Starting event listener...")

    while True:
        try:
            # Poll Bifrost for recent events
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{BIFROST_URL}/api/v1/events?limit=100") as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        for event in data.get("events", []):
                            # Chronicle the event
                            chronicle.record_event(ChronicleEvent(
                                event_type="access",
                                source="bifrost",
                                action=event.get("event_type", "unknown"),
                                actor_id=event.get("cardholder_id"),
                                actor_name=event.get("cardholder_name"),
                                target_id=event.get("door_id"),
                                target_name=event.get("door_name"),
                                result="granted" if event.get("granted") else "denied",
                                details=event
                            ))
        except Exception as e:
            logger.debug(f"Event listener error (will retry): {e}")

        await asyncio.sleep(5)  # Poll every 5 seconds

# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    logger.info(f"Aether Skald v{SKALD_VERSION} starting...")
    logger.info(f"Chronicle database: {DATABASE_PATH}")
    logger.info(f"Listening on port: {PORT}")

    # Start event listener in background
    # asyncio.create_task(event_listener())  # Enable when connected to Bifrost

    # Run API server
    uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="info")
