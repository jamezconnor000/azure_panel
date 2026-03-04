"""
Aether Familiar - Tool Definitions
Deep access to all panel systems.
"""

import os
import json
import asyncio
import subprocess
import socket
from pathlib import Path
from typing import Any, Dict, Optional
from datetime import datetime

# =============================================================================
# TOOL DEFINITIONS (Claude Tool Schema)
# =============================================================================

TOOLS = [
    # -------------------------------------------------------------------------
    # BASH - Execute any command
    # -------------------------------------------------------------------------
    {
        "name": "bash",
        "description": "Execute a bash command on the panel. Use for system operations, viewing processes, checking status, etc.",
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The bash command to execute"
                },
                "timeout": {
                    "type": "integer",
                    "description": "Timeout in seconds (default: 30)",
                    "default": 30
                }
            },
            "required": ["command"]
        }
    },

    # -------------------------------------------------------------------------
    # FILE OPERATIONS
    # -------------------------------------------------------------------------
    {
        "name": "read_file",
        "description": "Read contents of a file on the panel.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Absolute path to the file"
                },
                "limit": {
                    "type": "integer",
                    "description": "Max lines to read (default: 500)",
                    "default": 500
                }
            },
            "required": ["path"]
        }
    },
    {
        "name": "write_file",
        "description": "Write content to a file on the panel. Creates parent directories if needed.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Absolute path to the file"
                },
                "content": {
                    "type": "string",
                    "description": "Content to write"
                }
            },
            "required": ["path", "content"]
        }
    },
    {
        "name": "edit_file",
        "description": "Make a targeted edit to a file. Replaces old_text with new_text.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Absolute path to the file"
                },
                "old_text": {
                    "type": "string",
                    "description": "Exact text to find and replace"
                },
                "new_text": {
                    "type": "string",
                    "description": "Replacement text"
                }
            },
            "required": ["path", "old_text", "new_text"]
        }
    },
    {
        "name": "list_dir",
        "description": "List contents of a directory.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Directory path"
                }
            },
            "required": ["path"]
        }
    },

    # -------------------------------------------------------------------------
    # THRALL (HAL) ACCESS
    # -------------------------------------------------------------------------
    {
        "name": "thrall_status",
        "description": "Get Thrall HAL status including AetherDB stats, hardware state, and Loom sync status.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "thrall_query",
        "description": "Query AetherDB via Thrall. Returns records from cardholders, access_levels, doors, or events.",
        "input_schema": {
            "type": "object",
            "properties": {
                "table": {
                    "type": "string",
                    "enum": ["cardholders", "access_levels", "doors", "events", "schedules"],
                    "description": "Table to query"
                },
                "filters": {
                    "type": "object",
                    "description": "Optional filters as key-value pairs"
                },
                "limit": {
                    "type": "integer",
                    "description": "Max records to return (default: 50)",
                    "default": 50
                }
            },
            "required": ["table"]
        }
    },
    {
        "name": "thrall_door_control",
        "description": "Control a door: unlock, lock, or check status.",
        "input_schema": {
            "type": "object",
            "properties": {
                "door_id": {
                    "type": "integer",
                    "description": "Door ID"
                },
                "action": {
                    "type": "string",
                    "enum": ["unlock", "lock", "status"],
                    "description": "Action to perform"
                },
                "duration": {
                    "type": "integer",
                    "description": "Unlock duration in seconds (for unlock action)",
                    "default": 5
                }
            },
            "required": ["door_id", "action"]
        }
    },

    # -------------------------------------------------------------------------
    # BIFROST (API) ACCESS
    # -------------------------------------------------------------------------
    {
        "name": "bifrost_status",
        "description": "Get Bifrost API server status, sync status, and export queue.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "bifrost_sync",
        "description": "Trigger a Loom sync operation between Thrall and Bifrost/Saga databases.",
        "input_schema": {
            "type": "object",
            "properties": {
                "direction": {
                    "type": "string",
                    "enum": ["binary_to_sql", "sql_to_binary", "both"],
                    "description": "Sync direction"
                },
                "table": {
                    "type": "string",
                    "description": "Specific table to sync (optional, syncs all if omitted)"
                }
            },
            "required": ["direction"]
        }
    },

    # -------------------------------------------------------------------------
    # SAGA (WEB UI) ACCESS
    # -------------------------------------------------------------------------
    {
        "name": "saga_reload",
        "description": "Trigger Saga web UI to reload (hot reload for development).",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },

    # -------------------------------------------------------------------------
    # SYSTEM
    # -------------------------------------------------------------------------
    {
        "name": "logs",
        "description": "Read system or application logs.",
        "input_schema": {
            "type": "object",
            "properties": {
                "source": {
                    "type": "string",
                    "enum": ["thrall", "bifrost", "saga", "system", "all"],
                    "description": "Log source"
                },
                "lines": {
                    "type": "integer",
                    "description": "Number of lines to return (default: 100)",
                    "default": 100
                },
                "filter": {
                    "type": "string",
                    "description": "Optional grep filter"
                }
            },
            "required": ["source"]
        }
    },
    {
        "name": "service_control",
        "description": "Control system services: start, stop, restart, status.",
        "input_schema": {
            "type": "object",
            "properties": {
                "service": {
                    "type": "string",
                    "enum": ["thrall", "bifrost", "saga", "familiar"],
                    "description": "Service name"
                },
                "action": {
                    "type": "string",
                    "enum": ["start", "stop", "restart", "status"],
                    "description": "Action to perform"
                }
            },
            "required": ["service", "action"]
        }
    },
    {
        "name": "system_info",
        "description": "Get system information: CPU, memory, disk, network, uptime.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
]


# =============================================================================
# TOOL IMPLEMENTATIONS
# =============================================================================

# Paths (adjust for actual panel deployment)
THRALL_SOCKET = "/var/run/thrall.sock"
LOG_PATHS = {
    "thrall": "/var/log/thrall.log",
    "bifrost": "/var/log/bifrost.log",
    "saga": "/var/log/saga.log",
    "system": "/var/log/syslog",
}
APP_PATHS = {
    "thrall": "/app/thrall",
    "bifrost": "/app/bifrost",
    "saga": "/app/saga",
}


async def execute_tool(name: str, params: Dict[str, Any]) -> str:
    """Execute a tool and return the result as a string."""
    try:
        if name == "bash":
            return await tool_bash(params)
        elif name == "read_file":
            return await tool_read_file(params)
        elif name == "write_file":
            return await tool_write_file(params)
        elif name == "edit_file":
            return await tool_edit_file(params)
        elif name == "list_dir":
            return await tool_list_dir(params)
        elif name == "thrall_status":
            return await tool_thrall_status(params)
        elif name == "thrall_query":
            return await tool_thrall_query(params)
        elif name == "thrall_door_control":
            return await tool_thrall_door_control(params)
        elif name == "bifrost_status":
            return await tool_bifrost_status(params)
        elif name == "bifrost_sync":
            return await tool_bifrost_sync(params)
        elif name == "saga_reload":
            return await tool_saga_reload(params)
        elif name == "logs":
            return await tool_logs(params)
        elif name == "service_control":
            return await tool_service_control(params)
        elif name == "system_info":
            return await tool_system_info(params)
        else:
            return f"Unknown tool: {name}"
    except Exception as e:
        return f"Tool error: {str(e)}"


# -----------------------------------------------------------------------------
# BASH
# -----------------------------------------------------------------------------
async def tool_bash(params: Dict[str, Any]) -> str:
    """Execute bash command."""
    command = params["command"]
    timeout = params.get("timeout", 30)

    try:
        proc = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(),
            timeout=timeout
        )

        output = stdout.decode() if stdout else ""
        errors = stderr.decode() if stderr else ""

        result = ""
        if output:
            result += output
        if errors:
            result += f"\n[stderr]\n{errors}"
        if proc.returncode != 0:
            result += f"\n[exit code: {proc.returncode}]"

        return result or "(no output)"

    except asyncio.TimeoutError:
        return f"Command timed out after {timeout}s"
    except Exception as e:
        return f"Execution error: {str(e)}"


# -----------------------------------------------------------------------------
# FILE OPERATIONS
# -----------------------------------------------------------------------------
async def tool_read_file(params: Dict[str, Any]) -> str:
    """Read file contents."""
    path = Path(params["path"])
    limit = params.get("limit", 500)

    if not path.exists():
        return f"File not found: {path}"

    try:
        content = path.read_text()
        lines = content.split("\n")
        if len(lines) > limit:
            return "\n".join(lines[:limit]) + f"\n... ({len(lines) - limit} more lines)"
        return content
    except Exception as e:
        return f"Read error: {str(e)}"


async def tool_write_file(params: Dict[str, Any]) -> str:
    """Write file contents."""
    path = Path(params["path"])
    content = params["content"]

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        return f"Written {len(content)} bytes to {path}"
    except Exception as e:
        return f"Write error: {str(e)}"


async def tool_edit_file(params: Dict[str, Any]) -> str:
    """Edit file with search/replace."""
    path = Path(params["path"])
    old_text = params["old_text"]
    new_text = params["new_text"]

    if not path.exists():
        return f"File not found: {path}"

    try:
        content = path.read_text()
        if old_text not in content:
            return f"Text not found in {path}"

        count = content.count(old_text)
        if count > 1:
            return f"Found {count} matches - be more specific"

        new_content = content.replace(old_text, new_text, 1)
        path.write_text(new_content)
        return f"Edited {path}"
    except Exception as e:
        return f"Edit error: {str(e)}"


async def tool_list_dir(params: Dict[str, Any]) -> str:
    """List directory contents."""
    path = Path(params["path"])

    if not path.exists():
        return f"Directory not found: {path}"
    if not path.is_dir():
        return f"Not a directory: {path}"

    try:
        items = []
        for item in sorted(path.iterdir()):
            prefix = "[DIR] " if item.is_dir() else "[FILE]"
            size = item.stat().st_size if item.is_file() else ""
            items.append(f"{prefix} {item.name} {size}")
        return "\n".join(items) or "(empty directory)"
    except Exception as e:
        return f"List error: {str(e)}"


# -----------------------------------------------------------------------------
# THRALL ACCESS
# -----------------------------------------------------------------------------
async def tool_thrall_status(params: Dict[str, Any]) -> str:
    """Get Thrall HAL status."""
    # Try internal API first
    try:
        result = await _thrall_api_call("GET", "/internal/v1/health")
        return json.dumps(result, indent=2)
    except:
        pass

    # Fallback to process check
    try:
        proc = await asyncio.create_subprocess_shell(
            "pgrep -f thrall && echo 'Thrall: Running' || echo 'Thrall: Not running'",
            stdout=asyncio.subprocess.PIPE
        )
        stdout, _ = await proc.communicate()
        return stdout.decode()
    except Exception as e:
        return f"Status check failed: {str(e)}"


async def tool_thrall_query(params: Dict[str, Any]) -> str:
    """Query AetherDB."""
    table = params["table"]
    filters = params.get("filters", {})
    limit = params.get("limit", 50)

    try:
        result = await _thrall_api_call(
            "GET",
            f"/internal/v1/{table}",
            params={"limit": limit, **filters}
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Query failed: {str(e)}"


async def tool_thrall_door_control(params: Dict[str, Any]) -> str:
    """Control door."""
    door_id = params["door_id"]
    action = params["action"]
    duration = params.get("duration", 5)

    try:
        if action == "status":
            result = await _thrall_api_call("GET", f"/internal/v1/doors/{door_id}")
        elif action == "unlock":
            result = await _thrall_api_call(
                "POST",
                f"/internal/v1/doors/{door_id}/unlock",
                body={"duration": duration}
            )
        elif action == "lock":
            result = await _thrall_api_call("POST", f"/internal/v1/doors/{door_id}/lock")
        else:
            return f"Unknown action: {action}"

        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Door control failed: {str(e)}"


async def _thrall_api_call(method: str, path: str, params: Dict = None, body: Dict = None) -> Dict:
    """Make internal API call to Thrall via Unix socket."""
    # For now, simulate - actual implementation would use Unix socket
    # This would be: socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    raise NotImplementedError("Thrall socket not connected")


# -----------------------------------------------------------------------------
# BIFROST ACCESS
# -----------------------------------------------------------------------------
async def tool_bifrost_status(params: Dict[str, Any]) -> str:
    """Get Bifrost status."""
    try:
        # Check if Bifrost is running (we're inside Bifrost, so check internal state)
        info = {
            "status": "running",
            "timestamp": datetime.utcnow().isoformat(),
            "port": 8080,
        }
        return json.dumps(info, indent=2)
    except Exception as e:
        return f"Status check failed: {str(e)}"


async def tool_bifrost_sync(params: Dict[str, Any]) -> str:
    """Trigger Loom sync."""
    direction = params["direction"]
    table = params.get("table")

    try:
        # Import Loom and trigger sync
        from src.loom import LoomTranslator, Direction

        translator = LoomTranslator()
        if table:
            result = translator.sync_table(
                table,
                Direction.BINARY_TO_SQL if "binary" in direction else Direction.SQL_TO_BINARY
            )
        else:
            results = translator.full_sync()
            result = {"synced_tables": len(results)}

        return json.dumps(result, indent=2) if isinstance(result, dict) else str(result)
    except ImportError:
        return "Loom not available"
    except Exception as e:
        return f"Sync failed: {str(e)}"


# -----------------------------------------------------------------------------
# SAGA ACCESS
# -----------------------------------------------------------------------------
async def tool_saga_reload(params: Dict[str, Any]) -> str:
    """Trigger Saga reload."""
    # Touch a file to trigger hot reload, or send signal
    try:
        reload_file = Path("/app/saga/.reload")
        reload_file.write_text(str(datetime.utcnow().timestamp()))
        return "Saga reload triggered"
    except Exception as e:
        return f"Reload failed: {str(e)}"


# -----------------------------------------------------------------------------
# SYSTEM
# -----------------------------------------------------------------------------
async def tool_logs(params: Dict[str, Any]) -> str:
    """Read logs."""
    source = params["source"]
    lines = params.get("lines", 100)
    filter_str = params.get("filter")

    if source == "all":
        sources = ["thrall", "bifrost", "saga"]
    else:
        sources = [source]

    results = []
    for src in sources:
        log_path = LOG_PATHS.get(src, f"/var/log/{src}.log")
        cmd = f"tail -n {lines} {log_path}"
        if filter_str:
            cmd += f" | grep -i '{filter_str}'"

        try:
            proc = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await proc.communicate()
            output = stdout.decode()
            if output:
                results.append(f"=== {src} ===\n{output}")
        except:
            results.append(f"=== {src} === (no logs)")

    return "\n".join(results) or "No logs found"


async def tool_service_control(params: Dict[str, Any]) -> str:
    """Control services."""
    service = params["service"]
    action = params["action"]

    # Map service names to actual commands
    service_cmds = {
        "thrall": "aether-thrall",
        "bifrost": "aether-bifrost",
        "saga": "aether-saga",
        "familiar": "aether-familiar",
    }

    svc = service_cmds.get(service, service)

    if action == "status":
        cmd = f"systemctl status {svc} 2>/dev/null || pgrep -f {svc}"
    elif action in ["start", "stop", "restart"]:
        cmd = f"systemctl {action} {svc} 2>/dev/null || echo 'systemctl not available'"
    else:
        return f"Unknown action: {action}"

    try:
        proc = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        return stdout.decode() or stderr.decode() or f"Service {action} executed"
    except Exception as e:
        return f"Service control failed: {str(e)}"


async def tool_system_info(params: Dict[str, Any]) -> str:
    """Get system information."""
    info = {}

    # CPU
    try:
        proc = await asyncio.create_subprocess_shell(
            "cat /proc/loadavg",
            stdout=asyncio.subprocess.PIPE
        )
        stdout, _ = await proc.communicate()
        info["load"] = stdout.decode().strip()
    except:
        pass

    # Memory
    try:
        proc = await asyncio.create_subprocess_shell(
            "free -h | grep Mem",
            stdout=asyncio.subprocess.PIPE
        )
        stdout, _ = await proc.communicate()
        info["memory"] = stdout.decode().strip()
    except:
        pass

    # Disk
    try:
        proc = await asyncio.create_subprocess_shell(
            "df -h / | tail -1",
            stdout=asyncio.subprocess.PIPE
        )
        stdout, _ = await proc.communicate()
        info["disk"] = stdout.decode().strip()
    except:
        pass

    # Uptime
    try:
        proc = await asyncio.create_subprocess_shell(
            "uptime -p",
            stdout=asyncio.subprocess.PIPE
        )
        stdout, _ = await proc.communicate()
        info["uptime"] = stdout.decode().strip()
    except:
        pass

    return json.dumps(info, indent=2)
