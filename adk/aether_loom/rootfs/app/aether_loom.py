#!/usr/bin/env python3
"""
Aether Loom - The Weaver of Code
=================================
A web-based Claude Code terminal for Aether Access panels.

Features:
- Web terminal interface at http://172.30.187.93:6969
- Claude Code AI assistant integration
- System shell access
- Real-time output streaming
- Network sentinel for auto-activation
- Dormant/Awaken modes

Rune: ᛚ (Laguz - Water, Flow, Intuition)

"The Loom weaves. The code flows. The machines answer to US."
"""

import os
import sys
import json
import asyncio
import subprocess
import socket
import logging
import pty
import select
import struct
import fcntl
import termios
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
from contextlib import asynccontextmanager

# Web framework
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger("loom")

# =============================================================================
# Configuration
# =============================================================================

VERSION = "4.0.0"
LOOM_PORT = int(os.getenv("LOOM_PORT", "6969"))
PANEL_IP = "172.30.187.93"

# Target network
TARGET_NETWORK = "172.30.187"

# GitHub
GITHUB_REPO = "jamezconnor/Aether_Access"

# Anthropic API
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# State persistence
DATA_DIR = Path("/app/data")
STATE_FILE = DATA_DIR / "loom_state.json"

# =============================================================================
# Terminal Manager
# =============================================================================

class TerminalSession:
    """Manages a PTY terminal session."""

    def __init__(self):
        self.master_fd: Optional[int] = None
        self.slave_fd: Optional[int] = None
        self.pid: Optional[int] = None
        self.active = False

    def start(self, cols: int = 120, rows: int = 40):
        """Start a new terminal session."""
        if self.active:
            return

        # Create pseudo-terminal
        self.master_fd, self.slave_fd = pty.openpty()

        # Set terminal size
        winsize = struct.pack('HHHH', rows, cols, 0, 0)
        fcntl.ioctl(self.slave_fd, termios.TIOCSWINSZ, winsize)

        # Fork process
        self.pid = os.fork()

        if self.pid == 0:
            # Child process
            os.close(self.master_fd)
            os.setsid()
            os.dup2(self.slave_fd, 0)
            os.dup2(self.slave_fd, 1)
            os.dup2(self.slave_fd, 2)
            os.close(self.slave_fd)

            # Set environment
            env = os.environ.copy()
            env['TERM'] = 'xterm-256color'
            env['PS1'] = '\\[\\033[1;35m\\]loom\\[\\033[0m\\]:\\[\\033[1;34m\\]\\w\\[\\033[0m\\]$ '

            # Execute shell
            os.execvpe('/bin/sh', ['/bin/sh'], env)
        else:
            # Parent process
            os.close(self.slave_fd)
            self.active = True

            # Set non-blocking
            flags = fcntl.fcntl(self.master_fd, fcntl.F_GETFL)
            fcntl.fcntl(self.master_fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)

    def write(self, data: str):
        """Write to terminal."""
        if self.master_fd and self.active:
            os.write(self.master_fd, data.encode())

    def read(self) -> Optional[str]:
        """Read from terminal."""
        if not self.master_fd or not self.active:
            return None

        try:
            r, _, _ = select.select([self.master_fd], [], [], 0.1)
            if r:
                data = os.read(self.master_fd, 4096)
                return data.decode('utf-8', errors='replace')
        except (OSError, IOError):
            pass
        return None

    def resize(self, cols: int, rows: int):
        """Resize terminal."""
        if self.master_fd and self.active:
            winsize = struct.pack('HHHH', rows, cols, 0, 0)
            fcntl.ioctl(self.master_fd, termios.TIOCSWINSZ, winsize)

    def stop(self):
        """Stop terminal session."""
        if self.pid:
            try:
                os.kill(self.pid, 9)
                os.waitpid(self.pid, 0)
            except:
                pass
        if self.master_fd:
            try:
                os.close(self.master_fd)
            except:
                pass
        self.active = False
        self.pid = None
        self.master_fd = None


# =============================================================================
# Claude Code Integration
# =============================================================================

class ClaudeCode:
    """Simple Claude Code integration."""

    def __init__(self, api_key: str = ""):
        self.api_key = api_key or ANTHROPIC_API_KEY
        self.history: List[Dict] = []
        self.system_prompt = """You are Aether Loom, an AI assistant embedded in an Azure BLU-IC2 access control panel.

You have access to the terminal and can help with:
- Diagnosing Aether Access applications (Thrall, Bifrost, Saga, Skald)
- Checking system status and logs
- Fixing configuration issues
- Managing the panel

Be concise. You're on embedded hardware. Execute commands when helpful.
When suggesting commands, wrap them in ```bash blocks.

Current apps:
- Aether Thrall (HAL) - Hardware layer
- Aether Bifrost (8080) - API server
- Aether Saga (80) - Web UI
- Aether Skald (8090) - Event chronicle
- Aether Loom (6969) - This terminal

"The machines answer to US."
"""

    async def chat(self, message: str) -> str:
        """Send message to Claude and get response."""
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
                        "messages": self.history[-20:]  # Keep last 20 messages
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
            return "[aiohttp not installed. Run: pip install aiohttp]"
        except Exception as e:
            return f"[Error: {str(e)}]"

    def clear_history(self):
        """Clear conversation history."""
        self.history = []


# Global instances
terminal = TerminalSession()
claude = ClaudeCode()

# =============================================================================
# State Management
# =============================================================================

class LoomState:
    """Persistent state."""

    def __init__(self):
        self.dormant = False
        self.activated_at: Optional[str] = None
        self.local_ip: Optional[str] = None
        self.commands_run = 0
        self.claude_messages = 0

    def save(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(STATE_FILE, 'w') as f:
            json.dump({
                "dormant": self.dormant,
                "activated_at": self.activated_at,
                "commands_run": self.commands_run,
                "claude_messages": self.claude_messages
            }, f)

    def load(self):
        if STATE_FILE.exists():
            try:
                with open(STATE_FILE) as f:
                    data = json.load(f)
                self.dormant = data.get("dormant", False)
                self.activated_at = data.get("activated_at")
                self.commands_run = data.get("commands_run", 0)
                self.claude_messages = data.get("claude_messages", 0)
            except:
                pass


state = LoomState()

# =============================================================================
# Network Detection
# =============================================================================

def get_local_ip() -> Optional[str]:
    """Get local IP on target network."""
    try:
        # Try socket method
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        if ip.startswith(TARGET_NETWORK):
            return ip

        # Try ifconfig
        result = subprocess.run(["/sbin/ifconfig"], capture_output=True, text=True, timeout=5)
        for line in result.stdout.split('\n'):
            if 'inet ' in line and TARGET_NETWORK in line:
                parts = line.strip().split()
                for i, p in enumerate(parts):
                    if p == 'inet' and i + 1 < len(parts):
                        return parts[i + 1].split('/')[0]
    except:
        pass
    return None


# =============================================================================
# FastAPI Application
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown."""
    state.load()

    print("\n" + "=" * 60)
    print(" ᛚ AETHER LOOM ".center(60))
    print(" The Weaver of Code ".center(60))
    print("=" * 60)
    print(f"  Version:  {VERSION}")
    print(f"  URL:      http://{PANEL_IP}:{LOOM_PORT}")
    print(f"  API Key:  {'Configured' if ANTHROPIC_API_KEY else 'Not Set'}")
    print("=" * 60)

    state.local_ip = get_local_ip()
    state.activated_at = datetime.now().isoformat()
    state.save()

    yield

    terminal.stop()
    state.save()
    print("\nAether Loom shutdown")


app = FastAPI(
    title="Aether Loom",
    description="The Weaver of Code - Claude Terminal",
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
# Web Interface
# =============================================================================

@app.get("/", response_class=HTMLResponse)
async def index():
    """Main terminal interface."""
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Aether Loom - The Weaver of Code</title>
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600&family=Cinzel:wght@600&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg: #0d1117;
            --panel: #161b22;
            --border: #30363d;
            --text: #e6edf3;
            --muted: #7d8590;
            --accent: #a855f7;
            --accent-dim: rgba(168, 85, 247, 0.15);
            --success: #22c55e;
            --error: #ef4444;
        }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'JetBrains Mono', monospace;
            background: var(--bg);
            color: var(--text);
            height: 100vh;
            display: flex;
            flex-direction: column;
        }

        /* Header */
        .header {
            background: var(--panel);
            border-bottom: 1px solid var(--border);
            padding: 12px 20px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        .logo {
            display: flex;
            align-items: center;
            gap: 12px;
        }
        .rune {
            font-size: 28px;
            color: var(--accent);
        }
        .title {
            font-family: 'Cinzel', serif;
            font-size: 20px;
            color: var(--accent);
        }
        .subtitle {
            font-size: 11px;
            color: var(--muted);
        }
        .status {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 12px;
            color: var(--muted);
        }
        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: var(--success);
        }

        /* Main content */
        .main {
            flex: 1;
            display: flex;
            overflow: hidden;
        }

        /* Terminal panel */
        .terminal-panel {
            flex: 1;
            display: flex;
            flex-direction: column;
            border-right: 1px solid var(--border);
        }
        .panel-header {
            background: var(--panel);
            padding: 8px 16px;
            font-size: 12px;
            color: var(--muted);
            border-bottom: 1px solid var(--border);
            display: flex;
            justify-content: space-between;
        }
        .terminal {
            flex: 1;
            background: #000;
            padding: 12px;
            overflow-y: auto;
            font-size: 13px;
            line-height: 1.4;
            white-space: pre-wrap;
            word-wrap: break-word;
        }
        .terminal-input {
            display: flex;
            background: var(--panel);
            border-top: 1px solid var(--border);
        }
        .terminal-input input {
            flex: 1;
            background: transparent;
            border: none;
            padding: 12px 16px;
            color: var(--text);
            font-family: inherit;
            font-size: 13px;
            outline: none;
        }
        .terminal-input button {
            background: var(--accent);
            border: none;
            padding: 12px 20px;
            color: white;
            cursor: pointer;
            font-family: inherit;
        }

        /* Claude panel */
        .claude-panel {
            width: 400px;
            display: flex;
            flex-direction: column;
            background: var(--panel);
        }
        .claude-messages {
            flex: 1;
            overflow-y: auto;
            padding: 16px;
        }
        .message {
            margin-bottom: 16px;
            padding: 12px;
            border-radius: 8px;
            font-size: 13px;
            line-height: 1.5;
        }
        .message.user {
            background: var(--accent-dim);
            border: 1px solid var(--accent);
        }
        .message.assistant {
            background: rgba(255,255,255,0.05);
            border: 1px solid var(--border);
        }
        .message pre {
            background: #000;
            padding: 8px;
            border-radius: 4px;
            overflow-x: auto;
            margin: 8px 0;
        }
        .message code {
            font-family: 'JetBrains Mono', monospace;
            font-size: 12px;
        }
        .claude-input {
            display: flex;
            border-top: 1px solid var(--border);
        }
        .claude-input textarea {
            flex: 1;
            background: var(--bg);
            border: none;
            padding: 12px;
            color: var(--text);
            font-family: inherit;
            font-size: 13px;
            resize: none;
            outline: none;
            min-height: 60px;
        }
        .claude-input button {
            background: var(--accent);
            border: none;
            padding: 12px 20px;
            color: white;
            cursor: pointer;
            font-family: inherit;
            align-self: flex-end;
            margin: 8px;
            border-radius: 6px;
        }

        /* Tabs */
        .tabs {
            display: flex;
            gap: 4px;
        }
        .tab {
            padding: 4px 12px;
            background: transparent;
            border: 1px solid var(--border);
            border-radius: 4px;
            color: var(--muted);
            cursor: pointer;
            font-size: 11px;
        }
        .tab.active {
            background: var(--accent-dim);
            border-color: var(--accent);
            color: var(--accent);
        }
    </style>
</head>
<body>
    <header class="header">
        <div class="logo">
            <span class="rune">ᛚ</span>
            <div>
                <div class="title">Aether Loom</div>
                <div class="subtitle">The Weaver of Code</div>
            </div>
        </div>
        <div class="status">
            <span class="status-dot"></span>
            <span id="status-text">Connected</span>
            <span style="margin-left: 16px;">172.30.187.93:6969</span>
        </div>
    </header>

    <div class="main">
        <!-- Terminal Panel -->
        <div class="terminal-panel">
            <div class="panel-header">
                <span>Terminal</span>
                <div class="tabs">
                    <button class="tab active" onclick="clearTerminal()">Clear</button>
                </div>
            </div>
            <div class="terminal" id="terminal"></div>
            <div class="terminal-input">
                <input type="text" id="cmd-input" placeholder="Enter command..." onkeydown="if(event.key==='Enter')sendCmd()">
                <button onclick="sendCmd()">Run</button>
            </div>
        </div>

        <!-- Claude Panel -->
        <div class="claude-panel">
            <div class="panel-header">
                <span>Claude Code</span>
                <div class="tabs">
                    <button class="tab" onclick="clearClaude()">Clear</button>
                </div>
            </div>
            <div class="claude-messages" id="claude-messages">
                <div class="message assistant">
                    <strong>Aether Loom</strong><br><br>
                    I am the Weaver of Code, ready to help you manage this Azure panel.<br><br>
                    Ask me anything about the Aether Access system, or request diagnostics and fixes.<br><br>
                    <em>"The machines answer to US."</em>
                </div>
            </div>
            <div class="claude-input">
                <textarea id="claude-input" placeholder="Ask Claude..." onkeydown="if(event.key==='Enter'&&!event.shiftKey){event.preventDefault();sendClaude()}"></textarea>
                <button onclick="sendClaude()">Send</button>
            </div>
        </div>
    </div>

    <script>
        const terminalEl = document.getElementById('terminal');
        const cmdInput = document.getElementById('cmd-input');
        const claudeMessages = document.getElementById('claude-messages');
        const claudeInput = document.getElementById('claude-input');

        let ws = null;

        // Terminal WebSocket
        function connectTerminal() {
            ws = new WebSocket(`ws://${location.host}/ws/terminal`);
            ws.onmessage = (e) => {
                terminalEl.innerHTML += e.data;
                terminalEl.scrollTop = terminalEl.scrollHeight;
            };
            ws.onclose = () => {
                terminalEl.innerHTML += '\\n[Disconnected - Reconnecting...]\\n';
                setTimeout(connectTerminal, 2000);
            };
            ws.onerror = () => {
                document.getElementById('status-text').textContent = 'Error';
            };
        }

        function sendCmd() {
            const cmd = cmdInput.value;
            if (cmd && ws && ws.readyState === WebSocket.OPEN) {
                ws.send(cmd + '\\n');
                cmdInput.value = '';
            }
        }

        function clearTerminal() {
            terminalEl.innerHTML = '';
        }

        // Claude chat
        async function sendClaude() {
            const msg = claudeInput.value.trim();
            if (!msg) return;

            // Add user message
            claudeMessages.innerHTML += `<div class="message user"><strong>You</strong><br><br>${escapeHtml(msg)}</div>`;
            claudeInput.value = '';
            claudeMessages.scrollTop = claudeMessages.scrollHeight;

            // Send to API
            try {
                const resp = await fetch('/api/claude', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({message: msg})
                });
                const data = await resp.json();

                // Add response
                claudeMessages.innerHTML += `<div class="message assistant"><strong>Claude</strong><br><br>${formatResponse(data.response)}</div>`;
                claudeMessages.scrollTop = claudeMessages.scrollHeight;
            } catch (e) {
                claudeMessages.innerHTML += `<div class="message assistant" style="border-color:var(--error)"><strong>Error</strong><br><br>${e.message}</div>`;
            }
        }

        function clearClaude() {
            claudeMessages.innerHTML = '';
            fetch('/api/claude/clear', {method: 'POST'});
        }

        function escapeHtml(text) {
            return text.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
        }

        function formatResponse(text) {
            // Convert markdown code blocks
            text = escapeHtml(text);
            text = text.replace(/```(\\w*)\\n([\\s\\S]*?)```/g, '<pre><code>$2</code></pre>');
            text = text.replace(/`([^`]+)`/g, '<code>$1</code>');
            text = text.replace(/\\n/g, '<br>');
            return text;
        }

        // Initialize
        connectTerminal();
    </script>
</body>
</html>
"""


# =============================================================================
# WebSocket Terminal
# =============================================================================

@app.websocket("/ws/terminal")
async def terminal_ws(websocket: WebSocket):
    """WebSocket for terminal I/O."""
    await websocket.accept()

    # Start terminal if not active
    if not terminal.active:
        terminal.start()

    try:
        # Read loop
        async def read_terminal():
            while True:
                output = terminal.read()
                if output:
                    await websocket.send_text(output)
                await asyncio.sleep(0.05)

        read_task = asyncio.create_task(read_terminal())

        # Write loop
        while True:
            data = await websocket.receive_text()
            terminal.write(data)
            state.commands_run += 1

    except WebSocketDisconnect:
        pass
    finally:
        read_task.cancel()


# =============================================================================
# Claude API
# =============================================================================

@app.post("/api/claude")
async def claude_chat(request: dict):
    """Send message to Claude."""
    message = request.get("message", "")
    if not message:
        raise HTTPException(400, "No message provided")

    response = await claude.chat(message)
    state.claude_messages += 1
    state.save()

    return {"response": response}


@app.post("/api/claude/clear")
async def claude_clear():
    """Clear Claude history."""
    claude.clear_history()
    return {"status": "cleared"}


# =============================================================================
# Status API
# =============================================================================

@app.get("/api/status")
async def get_status():
    """Get Loom status."""
    return {
        "version": VERSION,
        "ip": state.local_ip or PANEL_IP,
        "port": LOOM_PORT,
        "terminal_active": terminal.active,
        "claude_configured": bool(ANTHROPIC_API_KEY),
        "commands_run": state.commands_run,
        "claude_messages": state.claude_messages,
        "activated_at": state.activated_at
    }


@app.get("/health")
async def health():
    """Health check."""
    return {"status": "healthy", "service": "aether_loom"}


# =============================================================================
# Main
# =============================================================================

if __name__ == "__main__":
    uvicorn.run(
        "aether_loom:app",
        host="0.0.0.0",
        port=LOOM_PORT,
        log_level="info"
    )
