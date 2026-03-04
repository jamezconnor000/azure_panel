#!/usr/bin/env python3
"""
Aether Access Unified Server
============================
The complete API server combining all Aether Access modules.

This is the MAIN server that should be started for the Aether Access GUI.
It unifies all API versions and connects to HAL Core API.

Architecture:
    Browser/Frontend --> [Aether Access (port 8080)] --> [HAL Core (port 8081)]
                                |
                                +--> /api/v1/     (Frontend I/O control API)
                                +--> /api/v2.1/   (Auth, Users, Doors, Access Levels)
                                +--> /api/v2.2/   (HAL Integration - OSDP, Cards, Diagnostics)
                                +--> /api/        (Aether Access main - Dashboard, Events, PACS)
                                +--> /ws/live     (WebSocket for real-time updates)

Usage:
    python main_server.py

    Or with uvicorn:
    uvicorn main_server:app --host 0.0.0.0 --port 8080 --reload
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager
from datetime import datetime
from typing import List
import asyncio
import json
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

# =============================================================================
# Import API Routers
# =============================================================================

# v2.1 - Auth, Users, Doors, Access Levels
try:
    from api_v2_1 import router as api_v2_1_router
    V2_1_AVAILABLE = True
except ImportError as e:
    print(f"Warning: v2.1 API not available: {e}")
    V2_1_AVAILABLE = False

# v2.2 - HAL Integration (OSDP, Cards, Diagnostics)
try:
    from api_v2_2 import router as api_v2_2_router
    V2_2_AVAILABLE = True
except ImportError as e:
    print(f"Warning: v2.2 API not available: {e}")
    V2_2_AVAILABLE = False

# v1 Frontend - I/O monitoring and control (connected to HAL)
try:
    from api_v1_frontend import router as api_v1_frontend_router
    V1_FRONTEND_AVAILABLE = True
except ImportError as e:
    print(f"Warning: v1 Frontend API not available: {e}")
    V1_FRONTEND_AVAILABLE = False

# Fallback v1 - Mock I/O monitoring (standalone)
try:
    from io_monitoring import get_panel_io_status, get_reader_health, get_panel_health
    from io_control import (
        control_door, control_output, control_relay, mass_control, execute_macro,
        get_active_overrides, clear_override, EXAMPLE_MACROS,
        DoorControl, OutputControl, RelayControl, MassControl
    )
    V1_MOCK_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Mock I/O modules not available: {e}")
    V1_MOCK_AVAILABLE = False


# =============================================================================
# Configuration
# =============================================================================

VERSION = "3.0.0"
AETHER_PORT = int(os.environ.get("AETHER_PORT", 8080))
HAL_CORE_URL = os.environ.get("HAL_CORE_URL", "http://localhost:8081")


# =============================================================================
# WebSocket Manager
# =============================================================================

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass

manager = ConnectionManager()


# =============================================================================
# Lifespan Management
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    print_startup_banner()

    # Start background tasks
    task = asyncio.create_task(io_monitoring_loop())

    yield

    # Shutdown
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
    print("\nAether Access Server shutting down...")


# =============================================================================
# FastAPI Application
# =============================================================================

app = FastAPI(
    title="Aether Access - Unified Server",
    description="""
# Aether Access Control Panel API

Complete access control management system with HAL Core integration.

## API Versions

- **/api/v1/** - Frontend I/O control API (panels, readers, doors, outputs)
- **/api/v2.1/** - Authentication, Users, Doors, Access Levels
- **/api/v2.2/** - HAL Integration (OSDP, Cards, Diagnostics)
- **/api/** - Main Aether Access API (Dashboard, Events, PACS sync)

## WebSocket

- **ws://localhost:8080/ws/live** - Real-time I/O updates

## Architecture

```
Frontend (React) --> Aether Access (8080) --> HAL Core (8081) --> SQLite
```
    """,
    version=VERSION,
    lifespan=lifespan
)


# =============================================================================
# CORS Middleware
# =============================================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",     # React dev server
        "http://localhost:5173",     # Vite dev server
        "http://localhost:8080",     # Self
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8080",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# Include API Routers
# =============================================================================

# Include v1 Frontend API (HAL-connected)
if V1_FRONTEND_AVAILABLE:
    app.include_router(api_v1_frontend_router)
    print("  [OK] v1 Frontend API (HAL-connected)")

# Include v2.1 API (Auth, Users, etc.)
if V2_1_AVAILABLE:
    app.include_router(api_v2_1_router)
    print("  [OK] v2.1 API (Auth, Users, Doors, Access Levels)")

# Include v2.2 API (HAL Integration)
if V2_2_AVAILABLE:
    app.include_router(api_v2_2_router)
    print("  [OK] v2.2 API (OSDP, Cards, Diagnostics)")


# =============================================================================
# Root Endpoint
# =============================================================================

@app.get("/", response_class=HTMLResponse)
async def root():
    """API Root - Server information and links"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Aether Access API</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                max-width: 800px;
                margin: 50px auto;
                padding: 20px;
                background: #1a1a2e;
                color: #eee;
            }}
            h1 {{ color: #00d4ff; }}
            h2 {{ color: #00d4ff; border-bottom: 1px solid #333; padding-bottom: 10px; }}
            a {{ color: #00d4ff; text-decoration: none; }}
            a:hover {{ text-decoration: underline; }}
            .status {{
                display: inline-block;
                padding: 2px 8px;
                border-radius: 4px;
                font-size: 12px;
            }}
            .ok {{ background: #00aa55; }}
            .warn {{ background: #ffaa00; color: #000; }}
            table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
            th, td {{ text-align: left; padding: 8px; border-bottom: 1px solid #333; }}
            code {{ background: #333; padding: 2px 6px; border-radius: 3px; }}
        </style>
    </head>
    <body>
        <h1>Aether Access API Server</h1>
        <p>Version {VERSION} | HAL Core: <code>{HAL_CORE_URL}</code></p>

        <h2>API Documentation</h2>
        <ul>
            <li><a href="/docs">Swagger UI (Interactive)</a></li>
            <li><a href="/redoc">ReDoc (Reference)</a></li>
        </ul>

        <h2>API Versions</h2>
        <table>
            <tr>
                <th>Version</th>
                <th>Prefix</th>
                <th>Purpose</th>
                <th>Status</th>
            </tr>
            <tr>
                <td>v1</td>
                <td><code>/api/v1/</code></td>
                <td>Frontend I/O Control</td>
                <td><span class="status {'ok' if V1_FRONTEND_AVAILABLE else 'warn'}">{'OK' if V1_FRONTEND_AVAILABLE else 'N/A'}</span></td>
            </tr>
            <tr>
                <td>v2.1</td>
                <td><code>/api/v2.1/</code></td>
                <td>Auth, Users, Doors, Access Levels</td>
                <td><span class="status {'ok' if V2_1_AVAILABLE else 'warn'}">{'OK' if V2_1_AVAILABLE else 'N/A'}</span></td>
            </tr>
            <tr>
                <td>v2.2</td>
                <td><code>/api/v2.2/</code></td>
                <td>HAL Integration (OSDP, Cards, Diagnostics)</td>
                <td><span class="status {'ok' if V2_2_AVAILABLE else 'warn'}">{'OK' if V2_2_AVAILABLE else 'N/A'}</span></td>
            </tr>
        </table>

        <h2>Quick Links</h2>
        <ul>
            <li><a href="/api/v1/dashboard">Dashboard</a></li>
            <li><a href="/api/v1/panels/1/io">Panel I/O Status</a></li>
            <li><a href="/api/v1/readers/health/summary">Reader Health</a></li>
            <li><a href="/api/v2.1/doors">Door Configuration</a></li>
            <li><a href="/api/v2.1/access-levels">Access Levels</a></li>
        </ul>

        <h2>WebSocket</h2>
        <p>Real-time updates: <code>ws://localhost:{AETHER_PORT}/ws/live</code></p>

        <h2>Architecture</h2>
        <pre>
Frontend (React:3000) --> Aether Access (8080) --> HAL Core (8081)
                              |                        |
                              v                        v
                         Web UI API              SQLite Database
                         WebSocket               Event Buffer
        </pre>
    </body>
    </html>
    """


# =============================================================================
# Health Check
# =============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    import aiohttp

    # Check HAL Core connectivity
    hal_status = "unknown"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{HAL_CORE_URL}/hal/health", timeout=aiohttp.ClientTimeout(total=2)) as resp:
                if resp.status == 200:
                    hal_status = "connected"
                else:
                    hal_status = f"error: {resp.status}"
    except Exception as e:
        hal_status = f"unreachable: {str(e)[:50]}"

    return {
        "status": "healthy",
        "version": VERSION,
        "hal_core": {
            "url": HAL_CORE_URL,
            "status": hal_status
        },
        "api_versions": {
            "v1": V1_FRONTEND_AVAILABLE,
            "v2.1": V2_1_AVAILABLE,
            "v2.2": V2_2_AVAILABLE
        },
        "websocket_clients": len(manager.active_connections),
        "timestamp": datetime.now().isoformat()
    }


# =============================================================================
# WebSocket Endpoint
# =============================================================================

@app.websocket("/ws/live")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time updates"""
    await manager.connect(websocket)

    try:
        await websocket.send_json({
            "type": "connected",
            "message": f"Connected to Aether Access v{VERSION}",
            "features": ["io_monitoring", "io_control", "reader_health", "panel_health", "events"],
            "timestamp": datetime.now().isoformat()
        })

        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)

                # Handle subscription requests
                if message.get("action") == "subscribe":
                    await websocket.send_json({
                        "type": "subscription_confirmed",
                        "topics": message.get("topics", []),
                        "timestamp": datetime.now().isoformat()
                    })

                # Handle ping/pong
                elif message.get("type") == "ping":
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": datetime.now().isoformat()
                    })

            except json.JSONDecodeError:
                pass

    except WebSocketDisconnect:
        manager.disconnect(websocket)


# =============================================================================
# Background Tasks
# =============================================================================

async def io_monitoring_loop():
    """Background task to broadcast I/O updates"""
    while True:
        await asyncio.sleep(5)  # Every 5 seconds

        if manager.active_connections:
            await manager.broadcast({
                "type": "heartbeat",
                "server": "aether_access",
                "version": VERSION,
                "timestamp": datetime.now().isoformat()
            })


# =============================================================================
# Startup Banner
# =============================================================================

def print_startup_banner():
    """Print startup information"""
    print()
    print("=" * 80)
    print(" AETHER ACCESS - Unified Server ".center(80))
    print("=" * 80)
    print(f"  Version:    {VERSION}")
    print(f"  Port:       {AETHER_PORT}")
    print(f"  HAL Core:   {HAL_CORE_URL}")
    print()
    print("  API Routers:")


# =============================================================================
# Main Entry Point
# =============================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main_server:app",
        host="0.0.0.0",
        port=AETHER_PORT,
        reload=True,
        log_level="info"
    )
