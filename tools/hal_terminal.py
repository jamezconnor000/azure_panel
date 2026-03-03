#!/usr/bin/env python3
"""
HAL Terminal Monitor & Diagnostic Interface

A comprehensive terminal-based interface for monitoring, testing, and validating
the HAL (Hardware Abstraction Layer) for Azure Access panels.

Features:
- Real-time event monitoring
- Hardware validation tests
- Configuration validation
- System diagnostics
- Interactive card/door testing
- Live statistics dashboard

Based on Azure SDK documentation for:
- DeviceInfo (HC2 model info)
- HardwareEvent (hardware status)
- KCMFTA (door contact states)
- OSDP Peripheral status
- ErrorCode definitions

Usage:
    python hal_terminal.py              # Launch interactive terminal
    python hal_terminal.py --dashboard  # Dashboard mode
    python hal_terminal.py --validate   # Run full validation suite
    python hal_terminal.py --monitor    # Event monitor only

Requirements:
    pip install rich httpx websockets

Author: HAL Azure Panel Project
"""

import asyncio
import argparse
import sys
import os
import time
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from enum import IntEnum
from dataclasses import dataclass, field

# Install dependencies if needed
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.layout import Layout
    from rich.live import Live
    from rich.text import Text
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
    from rich.prompt import Prompt, Confirm
    from rich.tree import Tree
    from rich.syntax import Syntax
    from rich import box
except ImportError:
    print("Installing rich library...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "rich", "-q"])
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.layout import Layout
    from rich.live import Live
    from rich.text import Text
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
    from rich.prompt import Prompt, Confirm
    from rich.tree import Tree
    from rich.syntax import Syntax
    from rich import box

try:
    import httpx
except ImportError:
    print("Installing httpx library...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "httpx", "-q"])
    import httpx


# =============================================================================
# Constants and Enums (from Azure SDK documentation)
# =============================================================================

HAL_URL = os.environ.get("HAL_URL", "http://localhost:8081")

# Event types from HAL
class EventType(IntEnum):
    CARD_READ = 1
    ACCESS_GRANTED = 2
    ACCESS_DENIED = 3
    DOOR_FORCED = 4
    DOOR_HELD = 5
    DOOR_OPENED = 6
    DOOR_CLOSED = 7
    RELAY_ACTIVATED = 8
    RELAY_DEACTIVATED = 9
    READER_TAMPER = 10
    SYSTEM_EVENT = 11
    CONFIG_CHANGE = 12
    ALARM = 13
    TROUBLE = 14

EVENT_NAMES = {
    1: "CARD_READ",
    2: "ACCESS_GRANTED",
    3: "ACCESS_DENIED",
    4: "DOOR_FORCED",
    5: "DOOR_HELD",
    6: "DOOR_OPENED",
    7: "DOOR_CLOSED",
    8: "RELAY_ACTIVATED",
    9: "RELAY_DEACTIVATED",
    10: "READER_TAMPER",
    11: "SYSTEM_EVENT",
    12: "CONFIG_CHANGE",
    13: "ALARM",
    14: "TROUBLE"
}

EVENT_COLORS = {
    1: "cyan",
    2: "green",
    3: "red",
    4: "red bold",
    5: "yellow",
    6: "blue",
    7: "blue",
    8: "magenta",
    9: "magenta",
    10: "red bold",
    11: "white",
    12: "yellow",
    13: "red bold blink",
    14: "yellow bold"
}

# KCMFTA states (door contact monitoring)
class KCMFTA(IntEnum):
    UNKNOWN = 0x00
    ALARM = 0x01
    TAMPER = 0x02
    FAULT = 0x04
    FAULT_SHORT = 0x05
    FAULT_OPEN = 0x06
    FAULT_GROUND = 0x07
    MASK = 0x08
    CONFIGURE = 0x10
    ACKNOWLEDGE = 0x20

# Error codes from Azure SDK
ERROR_CODES = {
    0: ("OK", "Delivered and Executed"),
    1: ("Queued", "Command queued for execution later"),
    2: ("ProtocolVersion", "Protocol version not supported"),
    3: ("Unauthorized", "Unauthorized access"),
    10: ("NodeUnknown", "Node is not defined"),
    11: ("NodeOffline", "Node is declared offline"),
    12: ("UnknownCommand", "Command is unknown"),
    13: ("CantExecute", "Can't execute command"),
    21: ("BadParams", "Wrong or bad parameters"),
    22: ("ObjectNotFound", "Requested object not found"),
    23: ("NotEnoughMemory", "Not enough memory"),
    24: ("Database", "Database error"),
    25: ("CommunicationError", "Communication error"),
    26: ("UnknownException", "Unknown exception"),
    27: ("NotStarted", "Service not started"),
    29: ("ExecuteTimeout", "Execution timeout"),
    30: ("License", "License error"),
    32: ("BufferOverflow", "Buffer overflow"),
}

# Device models
DEVICE_MODELS = {
    0: "Unknown",
    1: "ASP4",
    2: "ASP2",
    3: "HC1",
    4: "HC2",
    5: "HC4"
}


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class ValidationResult:
    name: str
    category: str
    passed: bool
    message: str
    severity: str = "info"  # info, warning, error, critical
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SystemStatus:
    connected: bool = False
    version: str = ""
    uptime: int = 0
    cards_total: int = 0
    cards_active: int = 0
    events_total: int = 0
    doors_count: int = 0
    access_levels_count: int = 0
    db_size_mb: float = 0
    last_event_time: Optional[int] = None


# =============================================================================
# HAL Client
# =============================================================================

class HALTerminalClient:
    def __init__(self, base_url: str = HAL_URL):
        self.base_url = base_url
        self.console = Console()

    async def get(self, endpoint: str, params: Dict = None) -> Dict:
        """Make GET request to HAL"""
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"{self.base_url}{endpoint}", params=params)
            resp.raise_for_status()
            return resp.json()

    async def post(self, endpoint: str, data: Dict = None) -> Dict:
        """Make POST request to HAL"""
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(f"{self.base_url}{endpoint}", json=data)
            resp.raise_for_status()
            return resp.json()

    async def get_health(self) -> Dict:
        return await self.get("/hal/health")

    async def get_diagnostics(self) -> Dict:
        return await self.get("/hal/diagnostics")

    async def get_events(self, limit: int = 50) -> List[Dict]:
        return await self.get("/hal/events", {"limit": limit, "order": "desc"})

    async def get_cards(self, limit: int = 100) -> List[Dict]:
        return await self.get("/hal/cards", {"limit": limit})

    async def get_doors(self) -> List[Dict]:
        return await self.get("/hal/doors")

    async def get_access_levels(self) -> List[Dict]:
        return await self.get("/hal/access-levels")

    async def get_timezones(self) -> List[Dict]:
        return await self.get("/hal/timezones")

    async def get_config_changes(self, limit: int = 50) -> List[Dict]:
        return await self.get("/hal/config-changes", {"limit": limit})

    async def test_access(self, card_number: str, door_id: int) -> Dict:
        return await self.post("/hal/access/decide", {
            "card_number": card_number,
            "door_id": door_id,
            "reader_id": 1
        })

    async def simulate_card_read(self, card_number: str, door_id: int) -> Dict:
        return await self.post("/hal/simulate/card-read", {
            "card_number": card_number,
            "door_id": door_id
        })

    async def export_config(self) -> Dict:
        return await self.get("/hal/export")


# =============================================================================
# Validation Tests
# =============================================================================

class HALValidator:
    """Comprehensive HAL validation suite"""

    def __init__(self, client: HALTerminalClient):
        self.client = client
        self.results: List[ValidationResult] = []

    def add_result(self, name: str, category: str, passed: bool, message: str,
                   severity: str = "info", details: Dict = None):
        self.results.append(ValidationResult(
            name=name, category=category, passed=passed, message=message,
            severity=severity, details=details or {}
        ))

    # -------------------------------------------------------------------------
    # Hardware Validation
    # -------------------------------------------------------------------------

    async def validate_connectivity(self) -> bool:
        """Test basic HAL connectivity"""
        try:
            await self.client.get("/hal/test/connectivity")
            self.add_result("Connectivity", "Hardware", True, "HAL API reachable")
            return True
        except Exception as e:
            self.add_result("Connectivity", "Hardware", False,
                           f"Cannot connect to HAL: {e}", "critical")
            return False

    async def validate_health(self) -> bool:
        """Validate HAL health status"""
        try:
            health = await self.client.get_health()
            status = health.get("status", "unknown")

            if status == "healthy":
                self.add_result("Health Status", "Hardware", True,
                               f"HAL status: {status}")
            else:
                self.add_result("Health Status", "Hardware", False,
                               f"HAL status: {status}", "error")
                return False

            # Check uptime
            uptime = health.get("uptime_seconds", 0)
            if uptime < 60:
                self.add_result("Uptime Warning", "Hardware", True,
                               f"HAL recently started ({uptime}s ago)", "warning")

            return True
        except Exception as e:
            self.add_result("Health Check", "Hardware", False,
                           f"Health check failed: {e}", "error")
            return False

    async def validate_database(self) -> bool:
        """Validate database integrity"""
        try:
            diag = await self.client.get_diagnostics()
            tables = diag.get("tables", {})
            all_ok = True

            # Check each required table exists
            required_tables = ["cards", "access_levels", "doors", "events",
                              "timezones", "config_changes"]

            for table in required_tables:
                if table in tables:
                    count = tables[table]
                    if isinstance(count, int):
                        self.add_result(f"Table: {table}", "Database", True,
                                       f"{count} records")
                    else:
                        self.add_result(f"Table: {table}", "Database", False,
                                       f"Error: {count}", "error")
                        all_ok = False
                else:
                    self.add_result(f"Table: {table}", "Database", False,
                                   "Table missing", "critical")
                    all_ok = False

            # Check database file size
            db_size = diag.get("database", {}).get("size_bytes", 0)
            if db_size == 0:
                self.add_result("Database File", "Database", False,
                               "Database file empty or missing", "critical")
                all_ok = False
            else:
                size_mb = db_size / (1024 * 1024)
                self.add_result("Database File", "Database", True,
                               f"Size: {size_mb:.2f} MB")

            return all_ok
        except Exception as e:
            self.add_result("Database Check", "Database", False,
                           f"Database validation failed: {e}", "error")
            return False

    async def validate_event_buffer(self) -> bool:
        """Validate event buffer functionality"""
        try:
            health = await self.client.get_health()
            stats = health.get("statistics", {})

            events_total = stats.get("events_total", 0)
            events_capacity = stats.get("events_capacity", 100000)
            usage_pct = (events_total / events_capacity) * 100 if events_capacity > 0 else 0

            self.add_result("Event Buffer", "Hardware", True,
                           f"{events_total:,} / {events_capacity:,} ({usage_pct:.1f}%)")

            if usage_pct > 90:
                self.add_result("Event Buffer Warning", "Hardware", True,
                               "Buffer >90% full - events may be lost", "warning")

            return True
        except Exception as e:
            self.add_result("Event Buffer", "Hardware", False,
                           f"Check failed: {e}", "error")
            return False

    # -------------------------------------------------------------------------
    # Configuration Validation
    # -------------------------------------------------------------------------

    async def validate_access_levels(self) -> bool:
        """Validate access level configuration"""
        try:
            levels = await self.client.get_access_levels()

            if len(levels) == 0:
                self.add_result("Access Levels", "Configuration", True,
                               "No access levels configured", "warning")
                return True

            # Check for default access level (ID 1)
            has_default = any(l.get("id") == 1 for l in levels)
            if not has_default:
                self.add_result("Default Access Level", "Configuration", False,
                               "Default access level (ID 1) missing", "error")

            # Check for orphaned access levels (no doors)
            orphaned = [l for l in levels if not l.get("doors")]
            if orphaned:
                names = ", ".join(l.get("name", f"ID:{l['id']}") for l in orphaned[:3])
                self.add_result("Orphaned Access Levels", "Configuration", True,
                               f"{len(orphaned)} levels have no doors: {names}", "warning")

            self.add_result("Access Levels", "Configuration", True,
                           f"{len(levels)} access levels configured")
            return True
        except Exception as e:
            self.add_result("Access Levels", "Configuration", False,
                           f"Validation failed: {e}", "error")
            return False

    async def validate_doors(self) -> bool:
        """Validate door configuration"""
        try:
            doors = await self.client.get_doors()

            if len(doors) == 0:
                self.add_result("Doors", "Configuration", True,
                               "No doors configured", "warning")
                return True

            # Check for doors with no relay
            no_relay = [d for d in doors if not d.get("strike_relay_id")]
            if no_relay:
                names = ", ".join(d.get("door_name", f"ID:{d['id']}") for d in no_relay[:3])
                self.add_result("Doors Without Relay", "Configuration", True,
                               f"{len(no_relay)} doors have no relay: {names}", "warning")

            # Check strike times
            short_strike = [d for d in doors if d.get("strike_time_ms", 3000) < 1000]
            if short_strike:
                self.add_result("Short Strike Time", "Configuration", True,
                               f"{len(short_strike)} doors have <1s strike time", "warning")

            self.add_result("Doors", "Configuration", True,
                           f"{len(doors)} doors configured")
            return True
        except Exception as e:
            self.add_result("Doors", "Configuration", False,
                           f"Validation failed: {e}", "error")
            return False

    async def validate_timezones(self) -> bool:
        """Validate timezone configuration"""
        try:
            timezones = await self.client.get_timezones()

            # Check for required timezones
            tz_ids = {tz.get("id") for tz in timezones}

            if 0 not in tz_ids and 1 not in tz_ids:
                self.add_result("Never Timezone", "Configuration", False,
                               "Never timezone (0 or 1) missing", "error")

            if 2 not in tz_ids:
                self.add_result("Always Timezone", "Configuration", False,
                               "Always timezone (2) missing", "error")

            # Check for timezones without intervals
            no_intervals = [tz for tz in timezones
                          if tz.get("id", 0) > 2 and not tz.get("intervals")]
            if no_intervals:
                self.add_result("Empty Timezones", "Configuration", True,
                               f"{len(no_intervals)} custom timezones have no intervals",
                               "warning")

            self.add_result("Timezones", "Configuration", True,
                           f"{len(timezones)} timezones configured")
            return True
        except Exception as e:
            self.add_result("Timezones", "Configuration", False,
                           f"Validation failed: {e}", "error")
            return False

    async def validate_cards(self) -> bool:
        """Validate card database"""
        try:
            health = await self.client.get_health()
            stats = health.get("statistics", {})

            cards_total = stats.get("cards_total", 0)
            cards_active = stats.get("cards_active", 0)
            cards_capacity = stats.get("cards_capacity", 1000000)

            inactive = cards_total - cards_active
            usage_pct = (cards_total / cards_capacity) * 100 if cards_capacity > 0 else 0

            self.add_result("Card Database", "Configuration", True,
                           f"{cards_total:,} cards ({cards_active:,} active, {inactive:,} inactive)")

            if usage_pct > 80:
                self.add_result("Card Capacity", "Configuration", True,
                               f"Database {usage_pct:.1f}% full", "warning")

            # Sample cards to check for issues
            cards = await self.client.get_cards(limit=100)

            # Check for cards with invalid access levels
            levels = await self.client.get_access_levels()
            valid_level_ids = {l.get("id") for l in levels}

            invalid_level_cards = [c for c in cards
                                  if c.get("permission_id") not in valid_level_ids]
            if invalid_level_cards:
                self.add_result("Invalid Access Levels", "Configuration", True,
                               f"{len(invalid_level_cards)} cards reference invalid access levels",
                               "warning")

            # Check for expired cards still active
            now = int(time.time())
            expired_active = [c for c in cards
                             if c.get("is_active") and c.get("expiration_date", 0) > 0
                             and c.get("expiration_date") < now]
            if expired_active:
                self.add_result("Expired Active Cards", "Configuration", True,
                               f"{len(expired_active)} expired cards still marked active",
                               "warning")

            return True
        except Exception as e:
            self.add_result("Cards", "Configuration", False,
                           f"Validation failed: {e}", "error")
            return False

    # -------------------------------------------------------------------------
    # Functional Tests
    # -------------------------------------------------------------------------

    async def test_access_logic(self) -> bool:
        """Test access decision logic"""
        try:
            # Get a sample card and door
            cards = await self.client.get_cards(limit=1)
            doors = await self.client.get_doors()

            if not cards or not doors:
                self.add_result("Access Logic Test", "Functional", True,
                               "Skipped - no cards or doors configured", "warning")
                return True

            card = cards[0]
            door = doors[0]

            # Test access decision
            result = await self.client.test_access(card["card_number"], door["id"])

            self.add_result("Access Logic Test", "Functional", True,
                           f"Card {card['card_number']} -> Door {door['id']}: "
                           f"{'GRANTED' if result.get('granted') else 'DENIED'} "
                           f"({result.get('reason', 'unknown')})")

            return True
        except Exception as e:
            self.add_result("Access Logic Test", "Functional", False,
                           f"Test failed: {e}", "error")
            return False

    async def test_event_generation(self) -> bool:
        """Test event generation"""
        try:
            # Get initial event count
            events_before = await self.client.get_events(limit=1)
            initial_id = events_before[0]["id"] if events_before else 0

            # Simulate an event
            cards = await self.client.get_cards(limit=1)
            doors = await self.client.get_doors()

            if cards and doors:
                await self.client.simulate_card_read(cards[0]["card_number"], doors[0]["id"])

                # Verify event was created
                events_after = await self.client.get_events(limit=1)
                if events_after and events_after[0]["id"] > initial_id:
                    self.add_result("Event Generation", "Functional", True,
                                   f"Event created: {events_after[0]['event_id'][:8]}...")
                else:
                    self.add_result("Event Generation", "Functional", False,
                                   "Event not created", "error")
                    return False
            else:
                self.add_result("Event Generation", "Functional", True,
                               "Skipped - no cards/doors", "warning")

            return True
        except Exception as e:
            self.add_result("Event Generation", "Functional", False,
                           f"Test failed: {e}", "error")
            return False

    async def test_crud_operations(self) -> bool:
        """Test CRUD operations"""
        test_card = f"VALIDATE-{int(time.time())}"

        try:
            # Create
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(f"{self.client.base_url}/hal/cards", json={
                    "card_number": test_card,
                    "facility_code": 999,
                    "permission_id": 1,
                    "holder_name": "Validation Test"
                })
                if resp.status_code != 201:
                    self.add_result("CRUD Create", "Functional", False,
                                   f"Create failed: {resp.status_code}", "error")
                    return False

                # Read
                resp = await client.get(f"{self.client.base_url}/hal/cards/{test_card}")
                if resp.status_code != 200:
                    self.add_result("CRUD Read", "Functional", False,
                                   "Read failed", "error")
                    return False

                # Update
                resp = await client.put(f"{self.client.base_url}/hal/cards/{test_card}",
                                       json={"holder_name": "Updated Validation Test"})
                if resp.status_code != 200:
                    self.add_result("CRUD Update", "Functional", False,
                                   "Update failed", "error")
                    return False

                # Delete
                resp = await client.delete(f"{self.client.base_url}/hal/cards/{test_card}")
                if resp.status_code != 200:
                    self.add_result("CRUD Delete", "Functional", False,
                                   "Delete failed", "error")
                    return False

                # Verify deletion
                resp = await client.get(f"{self.client.base_url}/hal/cards/{test_card}")
                if resp.status_code != 404:
                    self.add_result("CRUD Verify", "Functional", False,
                                   "Card not deleted", "error")
                    return False

            self.add_result("CRUD Operations", "Functional", True,
                           "Create/Read/Update/Delete all passed")
            return True

        except Exception as e:
            # Cleanup
            try:
                async with httpx.AsyncClient() as client:
                    await client.delete(f"{self.client.base_url}/hal/cards/{test_card}")
            except:
                pass
            self.add_result("CRUD Operations", "Functional", False,
                           f"Test failed: {e}", "error")
            return False

    # -------------------------------------------------------------------------
    # Run All Validations
    # -------------------------------------------------------------------------

    async def run_all(self) -> Tuple[int, int]:
        """Run all validation tests"""
        self.results = []

        # Hardware
        if not await self.validate_connectivity():
            return (0, 1)  # Can't continue without connectivity

        await self.validate_health()
        await self.validate_database()
        await self.validate_event_buffer()

        # Configuration
        await self.validate_access_levels()
        await self.validate_doors()
        await self.validate_timezones()
        await self.validate_cards()

        # Functional
        await self.test_access_logic()
        await self.test_event_generation()
        await self.test_crud_operations()

        passed = sum(1 for r in self.results if r.passed)
        failed = sum(1 for r in self.results if not r.passed)

        return (passed, failed)


# =============================================================================
# Terminal UI
# =============================================================================

class HALTerminal:
    """Interactive terminal interface for HAL"""

    def __init__(self, hal_url: str = HAL_URL):
        self.console = Console()
        self.client = HALTerminalClient(hal_url)
        self.validator = HALValidator(self.client)
        self.running = True

    def print_header(self):
        """Print terminal header"""
        self.console.print(Panel(
            "[bold cyan]HAL Terminal Monitor & Diagnostic Interface[/bold cyan]\n"
            f"[dim]Connected to: {self.client.base_url}[/dim]",
            box=box.DOUBLE
        ))

    def print_menu(self):
        """Print main menu"""
        menu = Table(show_header=False, box=box.SIMPLE)
        menu.add_column("Key", style="cyan bold")
        menu.add_column("Action")

        menu.add_row("1", "Dashboard (real-time stats)")
        menu.add_row("2", "Event Monitor (live events)")
        menu.add_row("3", "Run Validation Suite")
        menu.add_row("4", "Test Access Decision")
        menu.add_row("5", "Simulate Card Read")
        menu.add_row("6", "View Configuration")
        menu.add_row("7", "View Audit Trail")
        menu.add_row("8", "System Diagnostics")
        menu.add_row("q", "Quit")

        self.console.print(Panel(menu, title="Main Menu", box=box.ROUNDED))

    # -------------------------------------------------------------------------
    # Dashboard
    # -------------------------------------------------------------------------

    async def get_status(self) -> SystemStatus:
        """Get current system status"""
        status = SystemStatus()
        try:
            health = await self.client.get_health()
            status.connected = True
            status.version = health.get("version", "")
            status.uptime = health.get("uptime_seconds", 0)

            stats = health.get("statistics", {})
            status.cards_total = stats.get("cards_total", 0)
            status.cards_active = stats.get("cards_active", 0)
            status.events_total = stats.get("events_total", 0)
            status.doors_count = stats.get("doors", 0)
            status.access_levels_count = stats.get("access_levels", 0)

            db = health.get("database", {})
            status.db_size_mb = db.get("size_mb", 0)

            events = await self.client.get_events(limit=1)
            if events:
                status.last_event_time = events[0].get("timestamp")
        except:
            status.connected = False

        return status

    def make_dashboard(self, status: SystemStatus, recent_events: List[Dict]) -> Layout:
        """Create dashboard layout"""
        layout = Layout()

        # Top section with stats
        stats_table = Table(box=box.SIMPLE, expand=True)
        stats_table.add_column("Metric", style="cyan")
        stats_table.add_column("Value", justify="right")

        conn_style = "green" if status.connected else "red"
        stats_table.add_row("Status", f"[{conn_style}]{'Connected' if status.connected else 'Disconnected'}[/]")
        stats_table.add_row("Version", status.version or "N/A")
        stats_table.add_row("Uptime", self.format_duration(status.uptime))
        stats_table.add_row("Cards", f"{status.cards_active:,} / {status.cards_total:,}")
        stats_table.add_row("Events", f"{status.events_total:,}")
        stats_table.add_row("Doors", str(status.doors_count))
        stats_table.add_row("Access Levels", str(status.access_levels_count))
        stats_table.add_row("Database", f"{status.db_size_mb:.2f} MB")

        # Events table
        events_table = Table(title="Recent Events", box=box.SIMPLE, expand=True)
        events_table.add_column("Time", style="dim")
        events_table.add_column("Type")
        events_table.add_column("Card")
        events_table.add_column("Door")
        events_table.add_column("Result")

        for event in recent_events[:10]:
            ts = datetime.fromtimestamp(event.get("timestamp", 0))
            event_type = event.get("event_type", 0)
            color = EVENT_COLORS.get(event_type, "white")
            type_name = EVENT_NAMES.get(event_type, f"TYPE_{event_type}")

            granted = event.get("granted")
            result = ""
            if granted is True:
                result = "[green]GRANTED[/]"
            elif granted is False:
                result = "[red]DENIED[/]"

            events_table.add_row(
                ts.strftime("%H:%M:%S"),
                f"[{color}]{type_name}[/]",
                event.get("card_number", "")[:12] or "-",
                str(event.get("door_id", "")) or "-",
                result
            )

        layout.split_column(
            Layout(Panel(stats_table, title="System Status"), size=12),
            Layout(Panel(events_table, title="Event Log"), ratio=1)
        )

        return layout

    async def run_dashboard(self):
        """Run live dashboard"""
        self.console.print("[cyan]Starting dashboard... Press Ctrl+C to exit[/]")

        try:
            with Live(console=self.console, refresh_per_second=2) as live:
                while True:
                    status = await self.get_status()
                    events = await self.client.get_events(limit=15) if status.connected else []
                    layout = self.make_dashboard(status, events)
                    live.update(layout)
                    await asyncio.sleep(1)
        except KeyboardInterrupt:
            pass

    # -------------------------------------------------------------------------
    # Event Monitor
    # -------------------------------------------------------------------------

    async def run_event_monitor(self):
        """Run live event monitor"""
        self.console.print("[cyan]Starting event monitor... Press Ctrl+C to exit[/]")
        self.console.print()

        last_id = 0
        try:
            # Get initial events
            events = await self.client.get_events(limit=10)
            if events:
                last_id = events[0].get("id", 0)
                for event in reversed(events):
                    self.print_event(event)

            while True:
                events = await self.client.get_events(limit=20)
                new_events = [e for e in events if e.get("id", 0) > last_id]

                for event in reversed(new_events):
                    self.print_event(event)
                    last_id = max(last_id, event.get("id", 0))

                await asyncio.sleep(0.5)

        except KeyboardInterrupt:
            pass

    def print_event(self, event: Dict):
        """Print a single event"""
        ts = datetime.fromtimestamp(event.get("timestamp", 0))
        event_type = event.get("event_type", 0)
        color = EVENT_COLORS.get(event_type, "white")
        type_name = EVENT_NAMES.get(event_type, f"TYPE_{event_type}")

        granted = event.get("granted")
        result = ""
        if granted is True:
            result = " [green]GRANTED[/green]"
        elif granted is False:
            result = " [red]DENIED[/red]"

        card = event.get("card_number", "")
        door = event.get("door_id", "")
        reason = event.get("reason", "")

        line = f"[dim]{ts.strftime('%Y-%m-%d %H:%M:%S')}[/dim] [{color}]{type_name:15}[/{color}]"
        if card:
            line += f" Card:[cyan]{card}[/cyan]"
        if door:
            line += f" Door:[yellow]{door}[/yellow]"
        line += result
        if reason:
            line += f" [dim]({reason})[/dim]"

        self.console.print(line)

    # -------------------------------------------------------------------------
    # Validation
    # -------------------------------------------------------------------------

    async def run_validation(self):
        """Run full validation suite"""
        self.console.print("[cyan]Running HAL Validation Suite...[/]")
        self.console.print()

        passed, failed = await self.validator.run_all()

        # Group results by category
        categories = {}
        for result in self.validator.results:
            if result.category not in categories:
                categories[result.category] = []
            categories[result.category].append(result)

        # Print results by category
        for category, results in categories.items():
            table = Table(title=f"{category} Validation", box=box.SIMPLE)
            table.add_column("Test", style="cyan")
            table.add_column("Status")
            table.add_column("Message")

            for result in results:
                if result.passed:
                    status = "[green]PASS[/green]"
                else:
                    status = "[red]FAIL[/red]"

                msg_style = ""
                if result.severity == "warning":
                    msg_style = "yellow"
                elif result.severity == "error":
                    msg_style = "red"
                elif result.severity == "critical":
                    msg_style = "red bold"

                msg = f"[{msg_style}]{result.message}[/]" if msg_style else result.message
                table.add_row(result.name, status, msg)

            self.console.print(table)
            self.console.print()

        # Summary
        total = passed + failed
        color = "green" if failed == 0 else "red" if failed > passed else "yellow"
        self.console.print(Panel(
            f"[{color}]Validation Complete: {passed}/{total} tests passed[/]",
            box=box.DOUBLE
        ))

    # -------------------------------------------------------------------------
    # Interactive Tests
    # -------------------------------------------------------------------------

    async def test_access_interactive(self):
        """Interactive access decision test"""
        card_number = Prompt.ask("[cyan]Enter card number[/]")
        door_id = Prompt.ask("[cyan]Enter door ID[/]", default="1")

        try:
            result = await self.client.test_access(card_number, int(door_id))

            table = Table(title="Access Decision Result", box=box.ROUNDED)
            table.add_column("Property", style="cyan")
            table.add_column("Value")

            granted = result.get("granted", False)
            table.add_row("Decision", f"[{'green' if granted else 'red'}]{'GRANTED' if granted else 'DENIED'}[/]")
            table.add_row("Reason", result.get("reason", "N/A"))
            table.add_row("Card Found", "Yes" if result.get("card_found") else "No")
            table.add_row("Card Active", "Yes" if result.get("card_active") else "No")
            table.add_row("Permission Valid", "Yes" if result.get("permission_valid") else "No")
            table.add_row("Door Accessible", "Yes" if result.get("door_accessible") else "No")
            table.add_row("Timezone Active", "Yes" if result.get("timezone_active") else "No")

            details = result.get("details", {})
            if details:
                table.add_row("", "")
                table.add_row("[bold]Details[/]", "")
                for key, value in details.items():
                    table.add_row(f"  {key}", str(value))

            self.console.print(table)

        except Exception as e:
            self.console.print(f"[red]Error: {e}[/]")

    async def simulate_card_interactive(self):
        """Interactive card read simulation"""
        card_number = Prompt.ask("[cyan]Enter card number[/]")
        door_id = Prompt.ask("[cyan]Enter door ID[/]", default="1")

        try:
            result = await self.client.simulate_card_read(card_number, int(door_id))

            granted = result.get("granted", False)
            color = "green" if granted else "red"

            self.console.print(Panel(
                f"[{color}]{'ACCESS GRANTED' if granted else 'ACCESS DENIED'}[/]\n\n"
                f"Card: {card_number}\n"
                f"Door: {door_id}\n"
                f"Reason: {result.get('reason', 'N/A')}\n"
                f"Event ID: {result.get('event_id', 'N/A')}",
                title="Card Read Simulation",
                box=box.ROUNDED
            ))

        except Exception as e:
            self.console.print(f"[red]Error: {e}[/]")

    # -------------------------------------------------------------------------
    # Configuration View
    # -------------------------------------------------------------------------

    async def view_configuration(self):
        """View system configuration"""
        try:
            config = await self.client.export_config()

            tree = Tree("[bold cyan]HAL Configuration[/]")

            # Cards
            cards_branch = tree.add(f"[cyan]Cards[/] ({len(config.get('cards', []))} total)")
            for card in config.get('cards', [])[:5]:
                cards_branch.add(f"{card.get('card_number')} - {card.get('holder_name', 'N/A')}")
            if len(config.get('cards', [])) > 5:
                cards_branch.add(f"... and {len(config.get('cards', [])) - 5} more")

            # Access Levels
            levels_branch = tree.add(f"[cyan]Access Levels[/] ({len(config.get('access_levels', []))})")
            for level in config.get('access_levels', []):
                doors = level.get('doors', [])
                levels_branch.add(f"[{level.get('id')}] {level.get('name')} ({len(doors)} doors)")

            # Doors
            doors_branch = tree.add(f"[cyan]Doors[/] ({len(config.get('doors', []))})")
            for door in config.get('doors', []):
                doors_branch.add(f"[{door.get('id')}] {door.get('door_name')} @ {door.get('location', 'N/A')}")

            # Timezones
            tz_branch = tree.add(f"[cyan]Timezones[/] ({len(config.get('timezones', []))})")
            for tz in config.get('timezones', []):
                intervals = len(tz.get('intervals', []))
                tz_branch.add(f"[{tz.get('id')}] {tz.get('name')} ({intervals} intervals)")

            # Holidays
            holidays_branch = tree.add(f"[cyan]Holidays[/] ({len(config.get('holidays', []))})")
            for holiday in config.get('holidays', [])[:5]:
                date_str = str(holiday.get('date', ''))
                if len(date_str) == 8:
                    date_str = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"
                holidays_branch.add(f"{date_str} - {holiday.get('name', 'N/A')}")

            self.console.print(tree)

        except Exception as e:
            self.console.print(f"[red]Error: {e}[/]")

    # -------------------------------------------------------------------------
    # Audit Trail
    # -------------------------------------------------------------------------

    async def view_audit_trail(self):
        """View recent configuration changes"""
        try:
            changes = await self.client.get_config_changes(limit=20)

            table = Table(title="Recent Configuration Changes", box=box.SIMPLE)
            table.add_column("Time", style="dim")
            table.add_column("Type")
            table.add_column("Action")
            table.add_column("Resource")
            table.add_column("Source")

            actions = {1: "[green]CREATE[/]", 2: "[yellow]UPDATE[/]", 3: "[red]DELETE[/]"}
            sources = {1: "Local", 2: "Aether", 3: "PACS", 4: "Import"}

            for change in changes:
                ts = datetime.fromtimestamp(change.get("timestamp", 0))
                action = actions.get(change.get("action", 0), "UNKNOWN")
                source = sources.get(change.get("source", 1), "Unknown")

                table.add_row(
                    ts.strftime("%m/%d %H:%M"),
                    change.get("change_type", ""),
                    action,
                    change.get("resource_id", "")[:20] or "-",
                    source
                )

            self.console.print(table)

        except Exception as e:
            self.console.print(f"[red]Error: {e}[/]")

    # -------------------------------------------------------------------------
    # Diagnostics
    # -------------------------------------------------------------------------

    async def view_diagnostics(self):
        """View system diagnostics"""
        try:
            diag = await self.client.get_diagnostics()

            # System info
            self.console.print(Panel(
                f"Version: {diag.get('version', 'N/A')}\n"
                f"Uptime: {self.format_duration(diag.get('uptime_seconds', 0))}\n"
                f"Schema: v{diag.get('schema_version', 'N/A')}",
                title="System Info",
                box=box.ROUNDED
            ))

            # Database
            db = diag.get("database", {})
            self.console.print(Panel(
                f"Path: {db.get('path', 'N/A')}\n"
                f"Exists: {db.get('exists', False)}\n"
                f"Size: {db.get('size_bytes', 0) / 1024 / 1024:.2f} MB",
                title="Database",
                box=box.ROUNDED
            ))

            # Table counts
            table = Table(title="Table Counts", box=box.SIMPLE)
            table.add_column("Table", style="cyan")
            table.add_column("Records", justify="right")

            for name, count in diag.get("tables", {}).items():
                table.add_row(name, str(count))

            self.console.print(table)

            # Recent events by type
            if diag.get("recent_events_by_type"):
                self.console.print("\n[bold]Events in Last Hour:[/]")
                for type_id, count in diag.get("recent_events_by_type", {}).items():
                    type_name = EVENT_NAMES.get(int(type_id), f"TYPE_{type_id}")
                    self.console.print(f"  {type_name}: {count}")

        except Exception as e:
            self.console.print(f"[red]Error: {e}[/]")

    # -------------------------------------------------------------------------
    # Utilities
    # -------------------------------------------------------------------------

    def format_duration(self, seconds: int) -> str:
        """Format duration in human-readable form"""
        if seconds < 60:
            return f"{seconds}s"
        elif seconds < 3600:
            return f"{seconds // 60}m {seconds % 60}s"
        elif seconds < 86400:
            hours = seconds // 3600
            mins = (seconds % 3600) // 60
            return f"{hours}h {mins}m"
        else:
            days = seconds // 86400
            hours = (seconds % 86400) // 3600
            return f"{days}d {hours}h"

    # -------------------------------------------------------------------------
    # Main Loop
    # -------------------------------------------------------------------------

    async def run_interactive(self):
        """Run interactive terminal"""
        self.print_header()

        while self.running:
            self.print_menu()
            choice = Prompt.ask("Select option", default="1")

            self.console.print()

            if choice == "1":
                await self.run_dashboard()
            elif choice == "2":
                await self.run_event_monitor()
            elif choice == "3":
                await self.run_validation()
            elif choice == "4":
                await self.test_access_interactive()
            elif choice == "5":
                await self.simulate_card_interactive()
            elif choice == "6":
                await self.view_configuration()
            elif choice == "7":
                await self.view_audit_trail()
            elif choice == "8":
                await self.view_diagnostics()
            elif choice.lower() == "q":
                self.running = False
            else:
                self.console.print("[yellow]Invalid option[/]")

            self.console.print()
            if self.running and choice not in ["1", "2"]:
                Prompt.ask("[dim]Press Enter to continue[/]")
                self.console.clear()
                self.print_header()


# =============================================================================
# Main Entry Point
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="HAL Terminal Monitor & Diagnostic Interface",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python hal_terminal.py              # Interactive mode
  python hal_terminal.py --dashboard  # Live dashboard
  python hal_terminal.py --monitor    # Event monitor
  python hal_terminal.py --validate   # Run validation suite
  python hal_terminal.py --url http://192.168.1.100:8081  # Custom HAL URL
        """
    )

    parser.add_argument("--url", default=HAL_URL,
                       help=f"HAL Core API URL (default: {HAL_URL})")
    parser.add_argument("--dashboard", action="store_true",
                       help="Start in dashboard mode")
    parser.add_argument("--monitor", action="store_true",
                       help="Start in event monitor mode")
    parser.add_argument("--validate", action="store_true",
                       help="Run validation suite and exit")

    args = parser.parse_args()

    terminal = HALTerminal(args.url)

    if args.validate:
        asyncio.run(terminal.run_validation())
    elif args.dashboard:
        asyncio.run(terminal.run_dashboard())
    elif args.monitor:
        asyncio.run(terminal.run_event_monitor())
    else:
        asyncio.run(terminal.run_interactive())


if __name__ == "__main__":
    main()
