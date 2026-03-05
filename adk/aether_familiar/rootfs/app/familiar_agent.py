#!/usr/bin/env python3
"""
Aether Familiar - Autonomous AI Agent
======================================
An independent AI-powered agent that monitors and maintains
the Aether Access system on Azure BLU-IC2 panels.

Features:
- Network sentinel: Activates on 172.30.187.x network
- GitHub integration: Pulls from jamezconnor/Aether_Access
- Inter-app diagnostics: Monitors Thrall, Bifrost, Saga, Skald, Loom
- Auto-resolution: Fixes configuration and communication issues
- Dormant mode: Can sleep until awakened
- Familiar AI: Built-in AI assistant for panel management

"The Familiar watches. The Familiar fixes. The machines answer to US."
"""

import os
import sys
import json
import asyncio
import socket
import subprocess
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
from contextlib import asynccontextmanager

# Web framework
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger("familiar")

# =============================================================================
# Configuration
# =============================================================================

VERSION = "4.0.0"
FAMILIAR_PORT = int(os.getenv("FAMILIAR_PORT", "8765"))
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# Network detection
TARGET_NETWORK = "172.30.187"
TARGET_IP = "172.30.187.93"

# GitHub repository
GITHUB_REPO = "jamezconnor/Aether_Access"
GITHUB_RAW_BASE = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main"

# Aether app endpoints
AETHER_APPS = {
    "thrall": {"port": None, "check_via": "bifrost"},
    "bifrost": {"port": 8080, "health": "/health"},
    "saga": {"port": 80, "health": "/"},
    "skald": {"port": 8090, "health": "/api/v1/status"},
    "loom": {"port": 6969, "health": "/health"},
}


# =============================================================================
# Familiar AI Assistant
# =============================================================================

class FamiliarAI:
    """Familiar AI assistant for panel management."""

    def __init__(self, api_key: str = ""):
        self.api_key = api_key or ANTHROPIC_API_KEY
        self.history: List[Dict] = []
        self.system_prompt = """You are Familiar, an AI assistant embedded in an Azure BLU-IC2 access control panel.

You have access to the Aether Access system and can help with:
- Diagnosing Aether applications (Thrall, Bifrost, Saga, Skald, Loom)
- Checking system status and health
- Fixing configuration issues
- Monitoring the panel
- Managing doors, cards, and access control

Be concise. You're on embedded hardware. Be direct and helpful.

Current apps:
- Aether Thrall - Hardware abstraction layer
- Aether Bifrost (8080) - API gateway
- Aether Saga (80) - Web dashboard
- Aether Skald (8090) - Event chronicle
- Aether Loom (6969) - Code terminal

You are Familiar. You watch. You fix. The machines answer to US."""

    async def chat(self, message: str) -> str:
        """Send message and get response."""
        if not self.api_key:
            return "[No API key configured. Set ANTHROPIC_API_KEY environment variable.]"

        try:
            import aiohttp

            self.history.append({"role": "user", "content": message})

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": self.api_key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json"
                    },
                    json={
                        "model": "claude-sonnet-4-20250514",
                        "max_tokens": 2048,
                        "system": self.system_prompt,
                        "messages": self.history[-20:]
                    },
                    timeout=60
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        response = data["content"][0]["text"]
                        self.history.append({"role": "assistant", "content": response})
                        return response
                    else:
                        error = await resp.text()
                        return f"[API Error: {resp.status}] {error}"

        except ImportError:
            return "[aiohttp not installed]"
        except Exception as e:
            return f"[Error: {str(e)}]"

    def clear_history(self):
        """Clear conversation history."""
        self.history = []


# Global AI instance
familiar_ai = FamiliarAI()

# State persistence
DATA_DIR = Path("/app/data")
STATE_FILE = DATA_DIR / "familiar_state.json"

# =============================================================================
# Familiar State
# =============================================================================

class FamiliarState:
    """Persistent state for the Familiar agent."""

    def __init__(self):
        self.dormant = False
        self.awakened_at: Optional[str] = None
        self.last_activation: Optional[str] = None
        self.network_detected = False
        self.local_ip: Optional[str] = None
        self.issues_resolved = 0
        self.last_diagnosis: Optional[Dict] = None
        self.mission_log: List[str] = []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "dormant": self.dormant,
            "awakened_at": self.awakened_at,
            "last_activation": self.last_activation,
            "network_detected": self.network_detected,
            "local_ip": self.local_ip,
            "issues_resolved": self.issues_resolved,
            "mission_log": self.mission_log[-50:],  # Keep last 50 entries
        }

    def save(self):
        """Save state to disk."""
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(STATE_FILE, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)

    def load(self):
        """Load state from disk."""
        if STATE_FILE.exists():
            try:
                with open(STATE_FILE, 'r') as f:
                    data = json.load(f)
                self.dormant = data.get("dormant", False)
                self.awakened_at = data.get("awakened_at")
                self.last_activation = data.get("last_activation")
                self.issues_resolved = data.get("issues_resolved", 0)
                self.mission_log = data.get("mission_log", [])
            except Exception as e:
                logger.error(f"Failed to load state: {e}")

    def log(self, message: str):
        """Add to mission log."""
        entry = f"[{datetime.now().isoformat()}] {message}"
        self.mission_log.append(entry)
        logger.info(message)
        self.save()


# Global state
state = FamiliarState()

# =============================================================================
# Network Detection
# =============================================================================

def get_local_ips() -> List[str]:
    """Get all local IP addresses."""
    ips = []
    try:
        # Method 1: ifconfig
        if os.path.exists("/sbin/ifconfig"):
            result = subprocess.run(["/sbin/ifconfig"], capture_output=True, text=True, timeout=5)
            for line in result.stdout.split('\n'):
                if 'inet ' in line and '127.0.0.1' not in line:
                    parts = line.strip().split()
                    for i, part in enumerate(parts):
                        if part == 'inet' and i + 1 < len(parts):
                            ip = parts[i + 1].split('/')[0]
                            ips.append(ip)

        # Method 2: ip addr
        elif os.path.exists("/sbin/ip"):
            result = subprocess.run(["/sbin/ip", "addr"], capture_output=True, text=True, timeout=5)
            for line in result.stdout.split('\n'):
                if 'inet ' in line and '127.0.0.1' not in line:
                    parts = line.strip().split()
                    for i, part in enumerate(parts):
                        if part == 'inet' and i + 1 < len(parts):
                            ip = parts[i + 1].split('/')[0]
                            ips.append(ip)

        # Method 3: socket connect
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ips.append(s.getsockname()[0])
            s.close()
        except:
            pass

    except Exception as e:
        logger.debug(f"IP detection error: {e}")

    return list(set(ips))


def check_target_network() -> Optional[str]:
    """Check if we're on the target network. Returns IP if found."""
    for ip in get_local_ips():
        if ip.startswith(TARGET_NETWORK) or ip == TARGET_IP:
            return ip
    return None


def check_port(port: int, host: str = "127.0.0.1", timeout: float = 2.0) -> bool:
    """Check if a port is open."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except:
        return False


# =============================================================================
# App Diagnostics
# =============================================================================

async def diagnose_apps() -> Dict[str, Any]:
    """Diagnose all Aether applications."""
    diagnosis = {
        "timestamp": datetime.now().isoformat(),
        "apps": {},
        "issues": [],
        "healthy": True
    }

    for app_name, config in AETHER_APPS.items():
        app_status = {"name": app_name, "status": "unknown"}

        if config["port"] is None:
            app_status["status"] = "check_via_bifrost"
        else:
            if check_port(config["port"]):
                app_status["status"] = "running"
                app_status["port"] = config["port"]
            else:
                app_status["status"] = "not_responding"
                app_status["port"] = config["port"]
                diagnosis["issues"].append(f"{app_name} not responding on port {config['port']}")
                diagnosis["healthy"] = False

        diagnosis["apps"][app_name] = app_status

    # Check inter-app communication
    if diagnosis["apps"]["bifrost"]["status"] != "running":
        diagnosis["issues"].append("CRITICAL: Bifrost not running - apps cannot communicate")

    state.last_diagnosis = diagnosis
    return diagnosis


async def attempt_fixes(diagnosis: Dict[str, Any]):
    """Attempt to fix detected issues."""
    for issue in diagnosis["issues"]:
        state.log(f"Attempting fix for: {issue}")

        # Add specific fix logic here
        # For now, log recommendations
        if "saga" in issue.lower():
            state.log("RECOMMENDATION: Access Bifrost fallback at :8080/static/")
        elif "bifrost" in issue.lower():
            state.log("CRITICAL: Bifrost must be started first")
        elif "skald" in issue.lower():
            state.log("RECOMMENDATION: Check Skald logs at /app/logs/")


async def check_github_updates():
    """Check GitHub for configuration updates."""
    try:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            url = f"{GITHUB_RAW_BASE}/config/familiar_config.json"
            async with session.get(url, timeout=10) as resp:
                if resp.status == 200:
                    config = await resp.json()
                    state.log(f"GitHub config loaded: {len(config)} entries")
                    return config
    except Exception as e:
        logger.debug(f"GitHub check failed: {e}")
    return None


# =============================================================================
# Mission Loop
# =============================================================================

async def mission_loop():
    """Main mission loop - runs continuously until dormant."""
    state.log("Mission loop starting...")

    check_interval = 30  # seconds

    while True:
        try:
            # Check if dormant
            if state.dormant:
                state.log("Familiar is dormant. Waiting for awakening...")
                await asyncio.sleep(60)
                continue

            # Check network
            ip = check_target_network()
            if ip:
                if not state.network_detected:
                    state.network_detected = True
                    state.local_ip = ip
                    state.last_activation = datetime.now().isoformat()
                    state.log(f"TARGET NETWORK DETECTED: {ip}")
                    state.log("Familiar ACTIVATED - Beginning diagnostics")

                # Run diagnostics
                diagnosis = await diagnose_apps()

                if not diagnosis["healthy"]:
                    state.log(f"Issues detected: {len(diagnosis['issues'])}")
                    await attempt_fixes(diagnosis)
                else:
                    logger.debug("All apps healthy")

                # Check GitHub periodically
                if datetime.now().minute % 5 == 0:
                    await check_github_updates()

            else:
                if state.network_detected:
                    state.log("Lost connection to target network")
                    state.network_detected = False
                    state.local_ip = None

            await asyncio.sleep(check_interval)

        except asyncio.CancelledError:
            state.log("Mission loop cancelled")
            break
        except Exception as e:
            logger.error(f"Mission loop error: {e}")
            await asyncio.sleep(10)


# =============================================================================
# FastAPI Application
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown."""
    # Load state
    state.load()

    print("\n" + "=" * 60)
    print(" AETHER FAMILIAR ".center(60))
    print(" Autonomous AI Agent ".center(60))
    print("=" * 60)
    print(f"  Version:  {VERSION}")
    print(f"  Port:     {FAMILIAR_PORT}")
    print(f"  Target:   {TARGET_NETWORK}.x")
    print(f"  GitHub:   {GITHUB_REPO}")
    print(f"  Dormant:  {state.dormant}")
    print("=" * 60)

    # Start mission loop
    if not state.dormant:
        state.awakened_at = datetime.now().isoformat()
        state.log("Familiar awakening...")

    mission_task = asyncio.create_task(mission_loop())

    yield

    # Shutdown
    mission_task.cancel()
    state.save()
    print("\nAether Familiar shutdown")


app = FastAPI(
    title="Aether Familiar",
    description="Autonomous AI Agent for Aether Access",
    version=VERSION,
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
# API Endpoints
# =============================================================================

@app.get("/", response_class=HTMLResponse)
async def root():
    """Familiar dashboard with AI chat."""
    status_class = "dormant" if state.dormant else ("active" if state.network_detected else "watching")
    api_status = "Configured" if ANTHROPIC_API_KEY else "Not Set"

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Aether Familiar - AI Agent</title>
        <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{
                font-family: 'JetBrains Mono', monospace;
                background: linear-gradient(135deg, #0a0a12 0%, #1a1a2e 50%, #0f0f1a 100%);
                color: #e6edf3;
                height: 100vh;
                display: flex;
                flex-direction: column;
            }}
            .header {{
                background: linear-gradient(90deg, #1a1a2e, #2d1f4e);
                padding: 15px 25px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                border-bottom: 1px solid #a855f7;
            }}
            .logo {{ display: flex; align-items: center; gap: 12px; }}
            .logo-rune {{ font-size: 28px; color: #a855f7; }}
            .logo-text h1 {{ font-size: 20px; color: #d6bcfa; }}
            .logo-text span {{ font-size: 11px; color: #9f7aea; }}
            .status-bar {{ display: flex; gap: 20px; align-items: center; font-size: 12px; color: #a0aec0; }}
            .status-dot {{ width: 10px; height: 10px; border-radius: 50%; animation: pulse 2s infinite; }}
            .status-dot.active {{ background: #22c55e; }}
            .status-dot.watching {{ background: #f59e0b; }}
            .status-dot.dormant {{ background: #6b7280; }}
            @keyframes pulse {{ 0%,100%{{opacity:1}} 50%{{opacity:0.5}} }}

            .main {{ flex: 1; display: flex; overflow: hidden; }}

            /* Left Panel - Status & Controls */
            .left-panel {{
                width: 350px;
                background: rgba(15, 15, 25, 0.95);
                border-right: 1px solid #2d2d4a;
                display: flex;
                flex-direction: column;
                padding: 20px;
                overflow-y: auto;
            }}
            .status-card {{
                background: rgba(168, 85, 247, 0.1);
                border: 1px solid #a855f7;
                border-radius: 12px;
                padding: 20px;
                margin-bottom: 20px;
            }}
            .status-card.watching {{ border-color: #f59e0b; background: rgba(245, 158, 11, 0.1); }}
            .status-card.dormant {{ border-color: #6b7280; background: rgba(107, 114, 128, 0.1); }}
            .status-title {{ font-size: 18px; margin-bottom: 15px; color: #e9d8fd; }}
            .status-item {{ display: flex; justify-content: space-between; margin: 8px 0; font-size: 13px; }}
            .status-label {{ color: #7d8590; }}
            .status-value {{ color: #e6edf3; }}

            .controls {{ display: flex; gap: 10px; flex-wrap: wrap; margin: 20px 0; }}
            .btn {{
                padding: 10px 16px;
                border: none;
                border-radius: 8px;
                cursor: pointer;
                font-family: inherit;
                font-size: 13px;
                transition: all 0.2s;
            }}
            .btn:hover {{ transform: translateY(-2px); }}
            .btn-wake {{ background: #22c55e; color: white; }}
            .btn-sleep {{ background: #6b7280; color: white; }}
            .btn-diagnose {{ background: #3b82f6; color: white; }}

            .log-section {{ flex: 1; }}
            .log-header {{ font-size: 14px; color: #9f7aea; margin-bottom: 10px; }}
            .log {{
                background: rgba(0,0,0,0.3);
                border-radius: 8px;
                padding: 12px;
                height: calc(100% - 30px);
                overflow-y: auto;
                font-size: 11px;
            }}
            .log-entry {{ margin: 4px 0; color: #7d8590; line-height: 1.4; }}

            /* Right Panel - Familiar Chat */
            .chat-panel {{
                flex: 1;
                display: flex;
                flex-direction: column;
                background: rgba(10, 10, 18, 0.95);
            }}
            .chat-header {{
                padding: 15px 20px;
                background: linear-gradient(90deg, rgba(107, 70, 193, 0.2), rgba(159, 122, 234, 0.1));
                border-bottom: 1px solid #2d2d4a;
                display: flex;
                align-items: center;
                gap: 12px;
            }}
            .chat-avatar {{
                width: 40px; height: 40px;
                background: linear-gradient(135deg, #9f7aea, #6b46c1);
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 20px;
            }}
            .chat-title h2 {{ font-size: 16px; color: #e9d8fd; }}
            .chat-title span {{ font-size: 12px; color: #9f7aea; }}

            .messages {{
                flex: 1;
                overflow-y: auto;
                padding: 20px;
                display: flex;
                flex-direction: column;
                gap: 15px;
            }}
            .message {{
                padding: 15px;
                border-radius: 12px;
                font-size: 14px;
                line-height: 1.5;
                max-width: 85%;
            }}
            .message.user {{
                background: rgba(107, 70, 193, 0.3);
                color: #e9d8fd;
                align-self: flex-end;
                border-bottom-right-radius: 4px;
            }}
            .message.assistant {{
                background: rgba(30, 30, 50, 0.8);
                color: #e0e0e0;
                align-self: flex-start;
                border: 1px solid #2d2d4a;
                border-bottom-left-radius: 4px;
            }}
            .message pre {{
                background: rgba(0,0,0,0.4);
                padding: 10px;
                border-radius: 6px;
                margin: 10px 0;
                overflow-x: auto;
                font-size: 12px;
            }}
            .message code {{
                background: rgba(0,0,0,0.3);
                padding: 2px 6px;
                border-radius: 4px;
                font-family: inherit;
            }}

            .chat-input {{
                padding: 15px 20px;
                border-top: 1px solid #2d2d4a;
                display: flex;
                gap: 12px;
            }}
            .chat-input input {{
                flex: 1;
                background: rgba(30, 30, 50, 0.8);
                border: 1px solid #3d3d5a;
                border-radius: 10px;
                padding: 14px 18px;
                color: #e0e0e0;
                font-family: inherit;
                font-size: 14px;
                outline: none;
            }}
            .chat-input input:focus {{ border-color: #9f7aea; }}
            .chat-input button {{
                background: linear-gradient(135deg, #9f7aea, #6b46c1);
                border: none;
                border-radius: 10px;
                padding: 14px 24px;
                color: white;
                cursor: pointer;
                font-family: inherit;
                font-size: 14px;
            }}
            .chat-input button:hover {{ transform: translateY(-1px); box-shadow: 0 4px 15px rgba(107, 70, 193, 0.4); }}

            .typing {{ display: flex; gap: 4px; padding: 15px; }}
            .typing span {{
                width: 8px; height: 8px;
                background: #9f7aea;
                border-radius: 50%;
                animation: typing 1.4s infinite;
            }}
            .typing span:nth-child(2) {{ animation-delay: 0.2s; }}
            .typing span:nth-child(3) {{ animation-delay: 0.4s; }}
            @keyframes typing {{
                0%,60%,100% {{ transform: translateY(0); opacity: 0.4; }}
                30% {{ transform: translateY(-8px); opacity: 1; }}
            }}
        </style>
    </head>
    <body>
        <header class="header">
            <div class="logo">
                <span class="logo-rune">ᚠ</span>
                <div class="logo-text">
                    <h1>Aether Familiar</h1>
                    <span>Autonomous AI Agent v{VERSION}</span>
                </div>
            </div>
            <div class="status-bar">
                <span class="status-dot {status_class}"></span>
                <span>{'DORMANT' if state.dormant else ('ACTIVE' if state.network_detected else 'WATCHING')}</span>
                <span>|</span>
                <span>{state.local_ip or 'No Network'}</span>
                <span>|</span>
                <span>Port {FAMILIAR_PORT}</span>
            </div>
        </header>

        <div class="main">
            <!-- Left Panel -->
            <div class="left-panel">
                <div class="status-card {status_class}">
                    <div class="status-title">System Status</div>
                    <div class="status-item">
                        <span class="status-label">State</span>
                        <span class="status-value">{'Dormant' if state.dormant else ('Active' if state.network_detected else 'Watching')}</span>
                    </div>
                    <div class="status-item">
                        <span class="status-label">Network</span>
                        <span class="status-value">{state.local_ip or 'Not detected'}</span>
                    </div>
                    <div class="status-item">
                        <span class="status-label">Target</span>
                        <span class="status-value">{TARGET_NETWORK}.x</span>
                    </div>
                    <div class="status-item">
                        <span class="status-label">Issues Fixed</span>
                        <span class="status-value">{state.issues_resolved}</span>
                    </div>
                    <div class="status-item">
                        <span class="status-label">AI Status</span>
                        <span class="status-value">{api_status}</span>
                    </div>
                </div>

                <div class="controls">
                    <button class="btn btn-wake" onclick="fetch('/awaken',{{method:'POST'}}).then(()=>location.reload())">Awaken</button>
                    <button class="btn btn-sleep" onclick="fetch('/dormant',{{method:'POST'}}).then(()=>location.reload())">Dormant</button>
                    <button class="btn btn-diagnose" onclick="runDiagnose()">Diagnose</button>
                </div>

                <div class="log-section">
                    <div class="log-header">Mission Log</div>
                    <div class="log" id="mission-log">
                        {''.join(f'<div class="log-entry">{entry}</div>' for entry in reversed(state.mission_log[-30:]))}
                    </div>
                </div>
            </div>

            <!-- Chat Panel -->
            <div class="chat-panel">
                <div class="chat-header">
                    <div class="chat-avatar">ᚠ</div>
                    <div class="chat-title">
                        <h2>Familiar</h2>
                        <span>AI Assistant</span>
                    </div>
                </div>

                <div class="messages" id="messages">
                    <div class="message assistant">
                        <strong>Familiar</strong><br><br>
                        I am Familiar, your autonomous AI agent for this Azure BLU-IC2 panel.<br><br>
                        I monitor Thrall, Bifrost, Saga, Skald, and Loom. I watch for issues and fix them automatically.<br><br>
                        Ask me anything about the system, request diagnostics, or tell me what needs fixing.<br><br>
                        <em>"The Familiar watches. The Familiar fixes."</em>
                    </div>
                </div>

                <div class="chat-input">
                    <input type="text" id="chat-input" placeholder="Ask Familiar..." onkeydown="if(event.key==='Enter')sendMessage()">
                    <button onclick="sendMessage()">Send</button>
                </div>
            </div>
        </div>

        <script>
            const messagesEl = document.getElementById('messages');
            const inputEl = document.getElementById('chat-input');

            async function sendMessage() {{
                const msg = inputEl.value.trim();
                if (!msg) return;

                // Add user message
                messagesEl.innerHTML += `<div class="message user">${{escapeHtml(msg)}}</div>`;
                inputEl.value = '';
                messagesEl.scrollTop = messagesEl.scrollHeight;

                // Add typing indicator
                const typingId = 'typing-' + Date.now();
                messagesEl.innerHTML += `<div class="typing" id="${{typingId}}"><span></span><span></span><span></span></div>`;
                messagesEl.scrollTop = messagesEl.scrollHeight;

                try {{
                    const resp = await fetch('/api/familiar/chat', {{
                        method: 'POST',
                        headers: {{'Content-Type': 'application/json'}},
                        body: JSON.stringify({{message: msg}})
                    }});
                    const data = await resp.json();

                    // Remove typing indicator
                    document.getElementById(typingId)?.remove();

                    // Add response
                    messagesEl.innerHTML += `<div class="message assistant"><strong>Familiar</strong><br><br>${{formatResponse(data.response)}}</div>`;
                    messagesEl.scrollTop = messagesEl.scrollHeight;
                }} catch (e) {{
                    document.getElementById(typingId)?.remove();
                    messagesEl.innerHTML += `<div class="message assistant" style="border-color:#ef4444"><strong>Error</strong><br><br>${{e.message}}</div>`;
                }}
            }}

            async function runDiagnose() {{
                const resp = await fetch('/diagnose');
                const data = await resp.json();

                // Add to chat
                messagesEl.innerHTML += `<div class="message user">Run system diagnostics</div>`;
                let summary = '<strong>Familiar</strong><br><br>Diagnostic Results:<br><br>';
                for (const [app, info] of Object.entries(data.apps)) {{
                    const status = info.status === 'running' ? '\\u2705' : '\\u274c';
                    summary += `${{status}} ${{app}}: ${{info.status}}<br>`;
                }}
                if (data.issues.length > 0) {{
                    summary += '<br>Issues:<br>';
                    data.issues.forEach(i => summary += `- ${{i}}<br>`);
                }} else {{
                    summary += '<br>All systems healthy.';
                }}
                messagesEl.innerHTML += `<div class="message assistant">${{summary}}</div>`;
                messagesEl.scrollTop = messagesEl.scrollHeight;
            }}

            function escapeHtml(text) {{
                return text.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
            }}

            function formatResponse(text) {{
                text = escapeHtml(text);
                text = text.replace(/```(\\w*)\\n([\\s\\S]*?)```/g, '<pre><code>$2</code></pre>');
                text = text.replace(/`([^`]+)`/g, '<code>$1</code>');
                text = text.replace(/\\n/g, '<br>');
                return text;
            }}
        </script>
    </body>
    </html>
    """


@app.get("/status")
async def get_status():
    """Get Familiar status."""
    return {
        "version": VERSION,
        "state": state.to_dict(),
        "target_network": TARGET_NETWORK,
        "github_repo": GITHUB_REPO,
    }


@app.post("/awaken")
async def awaken():
    """Awaken the Familiar from dormant state."""
    if not state.dormant:
        return {"status": "already_awake", "message": "Familiar is already awake"}

    state.dormant = False
    state.awakened_at = datetime.now().isoformat()
    state.log("AWAKENED by user command")
    state.save()

    return {"status": "awakened", "message": "Familiar has been awakened"}


@app.post("/dormant")
async def go_dormant():
    """Put the Familiar into dormant state."""
    if state.dormant:
        return {"status": "already_dormant", "message": "Familiar is already dormant"}

    state.dormant = True
    state.log("Going DORMANT by user command")
    state.save()

    return {"status": "dormant", "message": "Familiar is now dormant"}


@app.get("/diagnose")
async def diagnose():
    """Run diagnostics on all Aether apps."""
    diagnosis = await diagnose_apps()
    return diagnosis


@app.get("/health")
async def health():
    """Health check."""
    return {
        "status": "healthy",
        "dormant": state.dormant,
        "network_detected": state.network_detected,
    }


# =============================================================================
# Familiar AI Chat
# =============================================================================

@app.post("/api/familiar/chat")
async def familiar_chat(request: dict):
    """Chat with Familiar AI."""
    message = request.get("message", "")
    if not message:
        raise HTTPException(400, "No message provided")

    response = await familiar_ai.chat(message)
    state.log(f"Familiar chat: {message[:50]}...")

    return {"response": response}


@app.post("/api/familiar/clear")
async def familiar_clear():
    """Clear Familiar conversation history."""
    familiar_ai.clear_history()
    return {"status": "cleared"}


# =============================================================================
# Main
# =============================================================================

if __name__ == "__main__":
    uvicorn.run(
        "familiar_agent:app",
        host="0.0.0.0",
        port=FAMILIAR_PORT,
        log_level="info"
    )
