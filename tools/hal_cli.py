#!/usr/bin/env python3
"""
HAL Command Line Interface (CLI)

A standalone command-line tool for testing and interacting with HAL Core
WITHOUT requiring Aether Access. This allows direct testing of HAL functionality.

Features:
- Test HAL API endpoints directly
- Simulate card reads and access decisions
- View and manage cards, access levels, doors
- Monitor events in real-time
- Run diagnostic tests
- Bulk data operations

Usage:
    python hal_cli.py --help
    python hal_cli.py health
    python hal_cli.py cards list
    python hal_cli.py simulate card-read 12345678 --door 1
    python hal_cli.py test all
"""

import argparse
import asyncio
import aiohttp
import json
import sys
import time
import os
from datetime import datetime
from typing import Optional, Dict, Any, List

# HAL API Configuration
HAL_HOST = os.environ.get("HAL_HOST", "localhost")
HAL_PORT = int(os.environ.get("HAL_PORT", "8081"))
HAL_BASE_URL = f"http://{HAL_HOST}:{HAL_PORT}"


class HALCli:
    """HAL Command Line Interface"""

    def __init__(self, base_url: str = HAL_BASE_URL, verbose: bool = False):
        self.base_url = base_url
        self.verbose = verbose

    def _print(self, msg: str, level: str = "info"):
        """Print with formatting"""
        colors = {
            "info": "\033[0m",     # Default
            "success": "\033[92m", # Green
            "warning": "\033[93m", # Yellow
            "error": "\033[91m",   # Red
            "header": "\033[94m",  # Blue
            "bold": "\033[1m",     # Bold
        }
        reset = "\033[0m"
        print(f"{colors.get(level, '')}{msg}{reset}")

    def _print_json(self, data: Any, title: str = None):
        """Pretty print JSON data"""
        if title:
            self._print(f"\n{title}", "header")
        print(json.dumps(data, indent=2, default=str))

    async def _request(
        self,
        method: str,
        endpoint: str,
        data: Dict = None,
        params: Dict = None
    ) -> Dict:
        """Make HTTP request to HAL API"""
        url = f"{self.base_url}{endpoint}"
        headers = {"X-HAL-Source": "cli", "X-HAL-User": "admin"}

        if self.verbose:
            self._print(f"  {method} {url}", "info")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(
                    method,
                    url,
                    json=data,
                    params=params,
                    headers=headers
                ) as resp:
                    if resp.status == 200 or resp.status == 201:
                        return await resp.json()
                    else:
                        text = await resp.text()
                        raise Exception(f"HTTP {resp.status}: {text}")
        except aiohttp.ClientConnectorError:
            raise Exception(f"Cannot connect to HAL at {self.base_url}")

    # =========================================================================
    # HEALTH & STATUS
    # =========================================================================

    async def health(self):
        """Check HAL health status"""
        self._print("=" * 60, "header")
        self._print("HAL HEALTH CHECK", "header")
        self._print("=" * 60, "header")

        try:
            result = await self._request("GET", "/hal/health")
            self._print(f"Status:      {result.get('status', 'unknown')}", "success")
            self._print(f"Version:     {result.get('version', 'unknown')}")
            self._print(f"Uptime:      {result.get('uptime_seconds', 0)} seconds")
            self._print(f"Database:    {result.get('database_status', 'unknown')}")
            self._print(f"Card Count:  {result.get('card_count', 0)}")
            self._print(f"Event Count: {result.get('event_count', 0)}")
            self._print(f"Memory:      {result.get('memory_usage', 'unknown')}")
            return True
        except Exception as e:
            self._print(f"FAILED: {e}", "error")
            return False

    # =========================================================================
    # CARD OPERATIONS
    # =========================================================================

    async def cards_list(self, limit: int = 20, offset: int = 0, search: str = None):
        """List cards in HAL database"""
        self._print("=" * 60, "header")
        self._print("CARDS IN HAL DATABASE", "header")
        self._print("=" * 60, "header")

        params = {"limit": limit, "offset": offset}
        if search:
            params["search"] = search

        try:
            result = await self._request("GET", "/hal/cards", params=params)

            if isinstance(result, list):
                cards = result
            else:
                cards = result.get("cards", [])

            if not cards:
                self._print("No cards found", "warning")
                return

            self._print(f"{'Card Number':<15} {'Holder Name':<25} {'Access Level':<10} {'Active':<8}", "bold")
            self._print("-" * 60)

            for card in cards:
                card_num = card.get("card_number", "N/A")
                holder = card.get("holder_name", "")[:24]
                perm = card.get("permission_id", 1)
                active = "Yes" if card.get("is_active", True) else "No"
                self._print(f"{card_num:<15} {holder:<25} {perm:<10} {active:<8}")

            self._print(f"\nShowing {len(cards)} cards")

        except Exception as e:
            self._print(f"Error: {e}", "error")

    async def cards_get(self, card_number: str):
        """Get a specific card"""
        try:
            result = await self._request("GET", f"/hal/cards/{card_number}")
            self._print_json(result, f"Card: {card_number}")
        except Exception as e:
            self._print(f"Card not found: {e}", "error")

    async def cards_add(
        self,
        card_number: str,
        holder_name: str = "",
        permission_id: int = 1,
        facility_code: int = 0
    ):
        """Add a new card"""
        self._print(f"Adding card: {card_number}", "info")

        data = {
            "card_number": card_number,
            "holder_name": holder_name,
            "permission_id": permission_id,
            "facility_code": facility_code,
            "is_active": True
        }

        try:
            result = await self._request("POST", "/hal/cards", data=data)
            self._print(f"Card added successfully", "success")
            self._print_json(result)
        except Exception as e:
            self._print(f"Error: {e}", "error")

    async def cards_delete(self, card_number: str):
        """Delete a card"""
        self._print(f"Deleting card: {card_number}", "warning")

        try:
            result = await self._request("DELETE", f"/hal/cards/{card_number}")
            self._print(f"Card deleted successfully", "success")
        except Exception as e:
            self._print(f"Error: {e}", "error")

    async def cards_count(self):
        """Get card count"""
        try:
            result = await self._request("GET", "/hal/cards/count")
            self._print(f"Total Cards: {result.get('count', 0)}", "success")
            self._print(f"Capacity:    {result.get('capacity', 1000000)}")
        except Exception as e:
            self._print(f"Error: {e}", "error")

    # =========================================================================
    # ACCESS LEVEL OPERATIONS
    # =========================================================================

    async def access_levels_list(self):
        """List all access levels"""
        self._print("=" * 60, "header")
        self._print("ACCESS LEVELS IN HAL", "header")
        self._print("=" * 60, "header")

        try:
            result = await self._request("GET", "/hal/access-levels")

            if isinstance(result, list):
                levels = result
            else:
                levels = result.get("access_levels", [])

            if not levels:
                self._print("No access levels found", "warning")
                return

            self._print(f"{'ID':<5} {'Name':<25} {'Description':<25} {'Doors':<10}", "bold")
            self._print("-" * 65)

            for level in levels:
                lid = level.get("id", "N/A")
                name = level.get("name", "")[:24]
                desc = level.get("description", "")[:24]
                doors = len(level.get("door_ids", []))
                self._print(f"{lid:<5} {name:<25} {desc:<25} {doors:<10}")

        except Exception as e:
            self._print(f"Error: {e}", "error")

    async def access_levels_add(
        self,
        name: str,
        description: str = "",
        door_ids: List[int] = None
    ):
        """Add a new access level"""
        self._print(f"Adding access level: {name}", "info")

        data = {
            "name": name,
            "description": description,
            "door_ids": door_ids or []
        }

        try:
            result = await self._request("POST", "/hal/access-levels", data=data)
            self._print(f"Access level added successfully", "success")
            self._print_json(result)
        except Exception as e:
            self._print(f"Error: {e}", "error")

    # =========================================================================
    # DOOR OPERATIONS
    # =========================================================================

    async def doors_list(self):
        """List all doors"""
        self._print("=" * 60, "header")
        self._print("DOORS IN HAL", "header")
        self._print("=" * 60, "header")

        try:
            result = await self._request("GET", "/hal/doors")

            if isinstance(result, list):
                doors = result
            else:
                doors = result.get("doors", [])

            if not doors:
                self._print("No doors found", "warning")
                return

            self._print(f"{'ID':<5} {'Name':<25} {'Reader LPA':<15} {'Status':<10}", "bold")
            self._print("-" * 55)

            for door in doors:
                did = door.get("id", "N/A")
                name = door.get("name", "")[:24]
                reader = door.get("reader_lpa", "N/A")
                status = door.get("status", "unknown")
                self._print(f"{did:<5} {name:<25} {reader:<15} {status:<10}")

        except Exception as e:
            self._print(f"Error: {e}", "error")

    async def doors_unlock(self, door_id: int, duration_ms: int = 5000):
        """Unlock a door momentarily"""
        self._print(f"Unlocking door {door_id} for {duration_ms}ms", "info")

        data = {
            "action": "momentary_unlock",
            "duration_ms": duration_ms
        }

        try:
            result = await self._request("POST", f"/hal/doors/{door_id}/control", data=data)
            self._print(f"Door unlocked", "success")
        except Exception as e:
            self._print(f"Error: {e}", "error")

    # =========================================================================
    # EVENT OPERATIONS
    # =========================================================================

    async def events_list(self, limit: int = 20, event_type: int = None):
        """List recent events"""
        self._print("=" * 60, "header")
        self._print("EVENTS IN HAL BUFFER", "header")
        self._print("=" * 60, "header")

        params = {"limit": limit, "order": "desc"}
        if event_type is not None:
            params["event_type"] = event_type

        try:
            result = await self._request("GET", "/hal/events", params=params)

            if isinstance(result, list):
                events = result
            else:
                events = result.get("events", [])

            if not events:
                self._print("No events found", "warning")
                return

            event_types = {
                1: "CARD_READ",
                2: "ACCESS_GRANTED",
                3: "ACCESS_DENIED",
                4: "DOOR_FORCED",
                5: "DOOR_HELD",
                6: "DOOR_OPENED",
                7: "DOOR_CLOSED",
            }

            self._print(f"{'Timestamp':<20} {'Type':<18} {'Card':<12} {'Door':<8}", "bold")
            self._print("-" * 60)

            for event in events:
                ts = datetime.fromtimestamp(event.get("timestamp", 0)).strftime("%Y-%m-%d %H:%M:%S")
                etype = event_types.get(event.get("event_type", 0), f"TYPE_{event.get('event_type', 0)}")
                card = event.get("card_number", "")[:11]
                door = event.get("door_id", "")
                self._print(f"{ts:<20} {etype:<18} {card:<12} {door:<8}")

        except Exception as e:
            self._print(f"Error: {e}", "error")

    async def events_count(self):
        """Get event count"""
        try:
            result = await self._request("GET", "/hal/events/count")
            self._print(f"Total Events: {result.get('count', 0)}", "success")
            self._print(f"Capacity:     {result.get('capacity', 100000)}")
        except Exception as e:
            self._print(f"Error: {e}", "error")

    # =========================================================================
    # SIMULATION
    # =========================================================================

    async def simulate_card_read(
        self,
        card_number: str,
        door_id: int = 1,
        reader_id: int = 1
    ):
        """Simulate a card read event and get access decision"""
        self._print("=" * 60, "header")
        self._print("SIMULATING CARD READ", "header")
        self._print("=" * 60, "header")

        self._print(f"Card Number: {card_number}")
        self._print(f"Door ID:     {door_id}")
        self._print(f"Reader ID:   {reader_id}")
        self._print("-" * 60)

        # First, check if card exists
        try:
            card = await self._request("GET", f"/hal/cards/{card_number}")
            self._print(f"Card Found:  {card.get('holder_name', 'Unknown')}", "success")
            self._print(f"Active:      {card.get('is_active', False)}")
            self._print(f"Access Level: {card.get('permission_id', 'N/A')}")
        except:
            self._print(f"Card NOT found in database!", "error")
            self._print("Access would be DENIED - Unknown Card", "error")
            return

        # Simulate access decision
        data = {
            "card_number": card_number,
            "door_id": door_id,
            "reader_id": reader_id,
            "timestamp": int(time.time())
        }

        try:
            result = await self._request("POST", "/hal/access/decide", data=data)
            decision = result.get("decision", "unknown")
            reason = result.get("reason", "")

            if decision == "granted":
                self._print(f"\nACCESS GRANTED", "success")
            else:
                self._print(f"\nACCESS DENIED", "error")

            self._print(f"Reason: {reason}")

            if result.get("strike_time_ms"):
                self._print(f"Strike Time: {result.get('strike_time_ms')}ms")

        except Exception as e:
            self._print(f"Note: Access decision endpoint may not exist: {e}", "warning")
            self._print("Using card lookup result for manual decision")

    async def simulate_event(
        self,
        event_type: int,
        door_id: int = 1,
        card_number: str = None
    ):
        """Simulate an event (for testing)"""
        self._print(f"Simulating event type {event_type}", "info")

        data = {
            "event_type": event_type,
            "door_id": door_id,
            "timestamp": int(time.time())
        }
        if card_number:
            data["card_number"] = card_number

        try:
            result = await self._request("POST", "/hal/events/simulate", data=data)
            self._print(f"Event simulated successfully", "success")
            self._print_json(result)
        except Exception as e:
            self._print(f"Note: Event simulation endpoint may not exist: {e}", "warning")

    # =========================================================================
    # DIAGNOSTICS
    # =========================================================================

    async def test_all(self):
        """Run all diagnostic tests"""
        self._print("=" * 60, "header")
        self._print("HAL DIAGNOSTIC TEST SUITE", "header")
        self._print("=" * 60, "header")

        results = []

        # Test 1: Health Check
        self._print("\n[TEST 1] Health Check...", "info")
        try:
            await self._request("GET", "/hal/health")
            self._print("  PASS", "success")
            results.append(("Health Check", True))
        except Exception as e:
            self._print(f"  FAIL: {e}", "error")
            results.append(("Health Check", False))

        # Test 2: Card Database
        self._print("\n[TEST 2] Card Database Access...", "info")
        try:
            await self._request("GET", "/hal/cards", params={"limit": 1})
            self._print("  PASS", "success")
            results.append(("Card Database", True))
        except Exception as e:
            self._print(f"  FAIL: {e}", "error")
            results.append(("Card Database", False))

        # Test 3: Access Levels
        self._print("\n[TEST 3] Access Levels...", "info")
        try:
            await self._request("GET", "/hal/access-levels")
            self._print("  PASS", "success")
            results.append(("Access Levels", True))
        except Exception as e:
            self._print(f"  FAIL: {e}", "error")
            results.append(("Access Levels", False))

        # Test 4: Doors
        self._print("\n[TEST 4] Doors...", "info")
        try:
            await self._request("GET", "/hal/doors")
            self._print("  PASS", "success")
            results.append(("Doors", True))
        except Exception as e:
            self._print(f"  FAIL: {e}", "error")
            results.append(("Doors", False))

        # Test 5: Events
        self._print("\n[TEST 5] Event Buffer...", "info")
        try:
            await self._request("GET", "/hal/events", params={"limit": 1})
            self._print("  PASS", "success")
            results.append(("Event Buffer", True))
        except Exception as e:
            self._print(f"  FAIL: {e}", "error")
            results.append(("Event Buffer", False))

        # Test 6: Config Changes (Audit Trail)
        self._print("\n[TEST 6] Audit Trail...", "info")
        try:
            await self._request("GET", "/hal/config-changes", params={"limit": 1})
            self._print("  PASS", "success")
            results.append(("Audit Trail", True))
        except Exception as e:
            self._print(f"  FAIL: {e}", "error")
            results.append(("Audit Trail", False))

        # Test 7: Timezones
        self._print("\n[TEST 7] Timezones...", "info")
        try:
            await self._request("GET", "/hal/timezones")
            self._print("  PASS", "success")
            results.append(("Timezones", True))
        except Exception as e:
            self._print(f"  FAIL: {e}", "error")
            results.append(("Timezones", False))

        # Test 8: Export
        self._print("\n[TEST 8] Export Capability...", "info")
        try:
            await self._request("GET", "/hal/export")
            self._print("  PASS", "success")
            results.append(("Export", True))
        except Exception as e:
            self._print(f"  FAIL: {e}", "error")
            results.append(("Export", False))

        # Summary
        self._print("\n" + "=" * 60, "header")
        self._print("TEST SUMMARY", "header")
        self._print("=" * 60, "header")

        passed = sum(1 for _, p in results if p)
        total = len(results)

        for name, passed_test in results:
            status = "PASS" if passed_test else "FAIL"
            color = "success" if passed_test else "error"
            self._print(f"  {name:<20} {status}", color)

        self._print("-" * 60)
        pct = (passed / total * 100) if total > 0 else 0
        color = "success" if passed == total else "warning"
        self._print(f"  Total: {passed}/{total} ({pct:.1f}%)", color)

        return passed == total

    async def test_card_crud(self):
        """Test card Create/Read/Update/Delete operations"""
        self._print("=" * 60, "header")
        self._print("CARD CRUD TEST", "header")
        self._print("=" * 60, "header")

        test_card = f"TEST{int(time.time())}"

        # Create
        self._print(f"\n[CREATE] Adding test card {test_card}...", "info")
        try:
            await self._request("POST", "/hal/cards", data={
                "card_number": test_card,
                "holder_name": "CLI Test Card",
                "permission_id": 1,
                "is_active": True
            })
            self._print("  PASS", "success")
        except Exception as e:
            self._print(f"  FAIL: {e}", "error")
            return False

        # Read
        self._print(f"\n[READ] Getting test card...", "info")
        try:
            card = await self._request("GET", f"/hal/cards/{test_card}")
            if card.get("holder_name") == "CLI Test Card":
                self._print("  PASS", "success")
            else:
                self._print("  FAIL: Data mismatch", "error")
                return False
        except Exception as e:
            self._print(f"  FAIL: {e}", "error")
            return False

        # Update
        self._print(f"\n[UPDATE] Updating test card...", "info")
        try:
            await self._request("PUT", f"/hal/cards/{test_card}", data={
                "holder_name": "Updated Test Card"
            })
            card = await self._request("GET", f"/hal/cards/{test_card}")
            if card.get("holder_name") == "Updated Test Card":
                self._print("  PASS", "success")
            else:
                self._print("  FAIL: Update not applied", "error")
                return False
        except Exception as e:
            self._print(f"  FAIL: {e}", "error")
            return False

        # Delete
        self._print(f"\n[DELETE] Deleting test card...", "info")
        try:
            await self._request("DELETE", f"/hal/cards/{test_card}")
            self._print("  PASS", "success")
        except Exception as e:
            self._print(f"  FAIL: {e}", "error")
            return False

        self._print("\nCard CRUD Test: ALL PASSED", "success")
        return True

    # =========================================================================
    # BULK OPERATIONS
    # =========================================================================

    async def bulk_load_cards(self, count: int = 100, prefix: str = "LOAD"):
        """Bulk load test cards for performance testing"""
        self._print(f"Loading {count} test cards...", "info")

        cards = []
        for i in range(count):
            cards.append({
                "card_number": f"{prefix}{i:08d}",
                "holder_name": f"Test User {i}",
                "permission_id": 1,
                "facility_code": 100,
                "is_active": True
            })

        start = time.time()

        try:
            result = await self._request("POST", "/hal/sync", data={"cards": cards})
            elapsed = time.time() - start
            self._print(f"Loaded {count} cards in {elapsed:.2f} seconds", "success")
            self._print(f"Rate: {count/elapsed:.1f} cards/second")
        except Exception as e:
            self._print(f"Error: {e}", "error")

    async def export_config(self, output_file: str = None):
        """Export HAL configuration"""
        self._print("Exporting HAL configuration...", "info")

        try:
            result = await self._request("GET", "/hal/export")

            if output_file:
                with open(output_file, 'w') as f:
                    json.dump(result, f, indent=2)
                self._print(f"Exported to {output_file}", "success")
            else:
                self._print_json(result, "HAL Configuration Export")

        except Exception as e:
            self._print(f"Error: {e}", "error")


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="HAL Command Line Interface - Direct HAL Testing Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s health                          Check HAL health
  %(prog)s cards list                      List all cards
  %(prog)s cards add 12345678 "John Doe"   Add a card
  %(prog)s simulate card-read 12345678     Simulate a card read
  %(prog)s test all                        Run all diagnostic tests
  %(prog)s export --output config.json     Export configuration
        """
    )

    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--host", default=HAL_HOST, help=f"HAL host (default: {HAL_HOST})")
    parser.add_argument("--port", type=int, default=HAL_PORT, help=f"HAL port (default: {HAL_PORT})")

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Health
    subparsers.add_parser("health", help="Check HAL health")

    # Cards
    cards_parser = subparsers.add_parser("cards", help="Card operations")
    cards_sub = cards_parser.add_subparsers(dest="cards_cmd")

    cards_list = cards_sub.add_parser("list", help="List cards")
    cards_list.add_argument("--limit", type=int, default=20)
    cards_list.add_argument("--offset", type=int, default=0)
    cards_list.add_argument("--search", type=str)

    cards_get = cards_sub.add_parser("get", help="Get a card")
    cards_get.add_argument("card_number")

    cards_add = cards_sub.add_parser("add", help="Add a card")
    cards_add.add_argument("card_number")
    cards_add.add_argument("holder_name", nargs="?", default="")
    cards_add.add_argument("--permission", type=int, default=1)
    cards_add.add_argument("--facility", type=int, default=0)

    cards_delete = cards_sub.add_parser("delete", help="Delete a card")
    cards_delete.add_argument("card_number")

    cards_sub.add_parser("count", help="Get card count")

    # Access Levels
    levels_parser = subparsers.add_parser("levels", help="Access level operations")
    levels_sub = levels_parser.add_subparsers(dest="levels_cmd")
    levels_sub.add_parser("list", help="List access levels")

    levels_add = levels_sub.add_parser("add", help="Add access level")
    levels_add.add_argument("name")
    levels_add.add_argument("--description", default="")
    levels_add.add_argument("--doors", type=int, nargs="*", default=[])

    # Doors
    doors_parser = subparsers.add_parser("doors", help="Door operations")
    doors_sub = doors_parser.add_subparsers(dest="doors_cmd")
    doors_sub.add_parser("list", help="List doors")

    doors_unlock = doors_sub.add_parser("unlock", help="Unlock a door")
    doors_unlock.add_argument("door_id", type=int)
    doors_unlock.add_argument("--duration", type=int, default=5000)

    # Events
    events_parser = subparsers.add_parser("events", help="Event operations")
    events_sub = events_parser.add_subparsers(dest="events_cmd")

    events_list = events_sub.add_parser("list", help="List events")
    events_list.add_argument("--limit", type=int, default=20)
    events_list.add_argument("--type", type=int)

    events_sub.add_parser("count", help="Get event count")

    # Simulate
    sim_parser = subparsers.add_parser("simulate", help="Simulate events")
    sim_sub = sim_parser.add_subparsers(dest="sim_cmd")

    sim_card = sim_sub.add_parser("card-read", help="Simulate card read")
    sim_card.add_argument("card_number")
    sim_card.add_argument("--door", type=int, default=1)
    sim_card.add_argument("--reader", type=int, default=1)

    sim_event = sim_sub.add_parser("event", help="Simulate event")
    sim_event.add_argument("event_type", type=int)
    sim_event.add_argument("--door", type=int, default=1)
    sim_event.add_argument("--card", type=str)

    # Test
    test_parser = subparsers.add_parser("test", help="Run diagnostic tests")
    test_sub = test_parser.add_subparsers(dest="test_cmd")
    test_sub.add_parser("all", help="Run all tests")
    test_sub.add_parser("crud", help="Test card CRUD operations")

    # Bulk
    bulk_parser = subparsers.add_parser("bulk", help="Bulk operations")
    bulk_sub = bulk_parser.add_subparsers(dest="bulk_cmd")

    bulk_load = bulk_sub.add_parser("load", help="Bulk load test cards")
    bulk_load.add_argument("--count", type=int, default=100)
    bulk_load.add_argument("--prefix", default="LOAD")

    # Export
    export_parser = subparsers.add_parser("export", help="Export configuration")
    export_parser.add_argument("--output", "-o", help="Output file")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Create CLI instance
    base_url = f"http://{args.host}:{args.port}"
    cli = HALCli(base_url, args.verbose)

    # Route commands
    async def run():
        if args.command == "health":
            await cli.health()

        elif args.command == "cards":
            if args.cards_cmd == "list":
                await cli.cards_list(args.limit, args.offset, args.search)
            elif args.cards_cmd == "get":
                await cli.cards_get(args.card_number)
            elif args.cards_cmd == "add":
                await cli.cards_add(args.card_number, args.holder_name, args.permission, args.facility)
            elif args.cards_cmd == "delete":
                await cli.cards_delete(args.card_number)
            elif args.cards_cmd == "count":
                await cli.cards_count()
            else:
                cards_parser.print_help()

        elif args.command == "levels":
            if args.levels_cmd == "list":
                await cli.access_levels_list()
            elif args.levels_cmd == "add":
                await cli.access_levels_add(args.name, args.description, args.doors)
            else:
                levels_parser.print_help()

        elif args.command == "doors":
            if args.doors_cmd == "list":
                await cli.doors_list()
            elif args.doors_cmd == "unlock":
                await cli.doors_unlock(args.door_id, args.duration)
            else:
                doors_parser.print_help()

        elif args.command == "events":
            if args.events_cmd == "list":
                await cli.events_list(args.limit, getattr(args, 'type', None))
            elif args.events_cmd == "count":
                await cli.events_count()
            else:
                events_parser.print_help()

        elif args.command == "simulate":
            if args.sim_cmd == "card-read":
                await cli.simulate_card_read(args.card_number, args.door, args.reader)
            elif args.sim_cmd == "event":
                await cli.simulate_event(args.event_type, args.door, args.card)
            else:
                sim_parser.print_help()

        elif args.command == "test":
            if args.test_cmd == "all":
                await cli.test_all()
            elif args.test_cmd == "crud":
                await cli.test_card_crud()
            else:
                test_parser.print_help()

        elif args.command == "bulk":
            if args.bulk_cmd == "load":
                await cli.bulk_load_cards(args.count, args.prefix)
            else:
                bulk_parser.print_help()

        elif args.command == "export":
            await cli.export_config(args.output)

    asyncio.run(run())


if __name__ == "__main__":
    main()
