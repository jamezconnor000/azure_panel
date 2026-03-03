#!/usr/bin/env python3
"""
HAL + Aether Access Integration Test Suite

Tests the integration between HAL Core API (port 8081) and
Aether Access API (port 8080).

Usage:
    python test_hal_aether_integration.py [--hal-only] [--aether-only] [--verbose]

Requirements:
    - HAL Core API running on localhost:8081
    - Aether Access API running on localhost:8080 (unless --hal-only)
    - Python 3.8+
    - aiohttp, httpx
"""

import asyncio
import argparse
import sys
import time
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

try:
    import httpx
except ImportError:
    print("Installing httpx...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "httpx", "-q"])
    import httpx


# Configuration
HAL_URL = "http://localhost:8081"
AETHER_URL = "http://localhost:8080"

# Test data
TEST_CARD_PREFIX = "INTTEST"
TEST_ACCESS_LEVEL_NAME = "Integration Test Level"


class TestResult:
    def __init__(self, name: str, passed: bool, message: str = "", duration: float = 0):
        self.name = name
        self.passed = passed
        self.message = message
        self.duration = duration

    def __str__(self):
        status = "PASS" if self.passed else "FAIL"
        msg = f" - {self.message}" if self.message else ""
        return f"[{status}] {self.name} ({self.duration:.2f}s){msg}"


class IntegrationTestSuite:
    def __init__(self, hal_url: str = HAL_URL, aether_url: str = AETHER_URL, verbose: bool = False):
        self.hal_url = hal_url
        self.aether_url = aether_url
        self.verbose = verbose
        self.results: List[TestResult] = []
        self.test_card_numbers: List[str] = []
        self.test_access_level_ids: List[int] = []
        self.test_door_ids: List[int] = []

    def log(self, message: str):
        if self.verbose:
            print(f"  {message}")

    async def run_test(self, name: str, test_func) -> TestResult:
        """Run a single test and record the result"""
        start = time.time()
        try:
            result = await test_func()
            duration = time.time() - start
            if isinstance(result, tuple):
                passed, message = result
            else:
                passed, message = result, ""
            test_result = TestResult(name, passed, message, duration)
        except Exception as e:
            duration = time.time() - start
            test_result = TestResult(name, False, str(e), duration)

        self.results.append(test_result)
        print(test_result)
        return test_result

    # ==========================================================================
    # HAL Core Tests
    # ==========================================================================

    async def test_hal_connectivity(self) -> Tuple[bool, str]:
        """Test HAL Core API connectivity"""
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{self.hal_url}/hal/test/connectivity", timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                return True, f"HAL v{data.get('version', 'unknown')}"
            return False, f"Status {resp.status_code}"

    async def test_hal_health(self) -> Tuple[bool, str]:
        """Test HAL health endpoint"""
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{self.hal_url}/hal/health", timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                cards = data.get("statistics", {}).get("cards_total", 0)
                return True, f"Cards: {cards}, Status: {data.get('status')}"
            return False, f"Status {resp.status_code}"

    async def test_hal_card_create(self) -> Tuple[bool, str]:
        """Test creating a card in HAL"""
        card_number = f"{TEST_CARD_PREFIX}-{int(time.time())}"
        self.test_card_numbers.append(card_number)

        async with httpx.AsyncClient() as client:
            data = {
                "card_number": card_number,
                "facility_code": 100,
                "permission_id": 1,
                "holder_name": "Integration Test User"
            }
            resp = await client.post(f"{self.hal_url}/hal/cards", json=data, timeout=5)
            if resp.status_code == 201:
                return True, f"Created {card_number}"
            return False, resp.json().get("detail", f"Status {resp.status_code}")

    async def test_hal_card_read(self) -> Tuple[bool, str]:
        """Test reading a card from HAL"""
        if not self.test_card_numbers:
            return False, "No test card available"

        card_number = self.test_card_numbers[0]
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{self.hal_url}/hal/cards/{card_number}", timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                return True, f"Read {card_number} (holder: {data.get('holder_name')})"
            return False, f"Status {resp.status_code}"

    async def test_hal_card_update(self) -> Tuple[bool, str]:
        """Test updating a card in HAL"""
        if not self.test_card_numbers:
            return False, "No test card available"

        card_number = self.test_card_numbers[0]
        async with httpx.AsyncClient() as client:
            data = {"holder_name": "Updated Integration Test User"}
            resp = await client.put(f"{self.hal_url}/hal/cards/{card_number}", json=data, timeout=5)
            if resp.status_code == 200:
                updated = resp.json()
                if updated.get("holder_name") == "Updated Integration Test User":
                    return True, f"Updated {card_number}"
                return False, "Name not updated"
            return False, f"Status {resp.status_code}"

    async def test_hal_access_level_create(self) -> Tuple[bool, str]:
        """Test creating an access level in HAL"""
        async with httpx.AsyncClient() as client:
            data = {
                "name": TEST_ACCESS_LEVEL_NAME,
                "description": "Created by integration test",
                "priority": 0,
                "door_ids": []
            }
            resp = await client.post(f"{self.hal_url}/hal/access-levels", json=data, timeout=5)
            if resp.status_code == 201:
                level = resp.json()
                self.test_access_level_ids.append(level["id"])
                return True, f"Created level ID {level['id']}"
            return False, resp.json().get("detail", f"Status {resp.status_code}")

    async def test_hal_door_create(self) -> Tuple[bool, str]:
        """Test creating a door in HAL"""
        async with httpx.AsyncClient() as client:
            data = {
                "door_name": f"Test Door {int(time.time())}",
                "location": "Integration Test",
                "reader_address": 1,
                "strike_time_ms": 3000
            }
            resp = await client.post(f"{self.hal_url}/hal/doors", json=data, timeout=5)
            if resp.status_code == 201:
                door = resp.json()
                self.test_door_ids.append(door["id"])
                return True, f"Created door ID {door['id']}"
            return False, resp.json().get("detail", f"Status {resp.status_code}")

    async def test_hal_access_decision(self) -> Tuple[bool, str]:
        """Test access decision endpoint"""
        if not self.test_card_numbers or not self.test_door_ids:
            return False, "Missing test card or door"

        async with httpx.AsyncClient() as client:
            data = {
                "card_number": self.test_card_numbers[0],
                "door_id": self.test_door_ids[0],
                "reader_id": 1,
                "direction": "entry"
            }
            resp = await client.post(f"{self.hal_url}/hal/access/decide", json=data, timeout=5)
            if resp.status_code == 200:
                result = resp.json()
                granted = result.get("granted", False)
                reason = result.get("reason", "Unknown")
                return True, f"Decision: {'GRANTED' if granted else 'DENIED'} - {reason}"
            return False, f"Status {resp.status_code}"

    async def test_hal_simulate_card_read(self) -> Tuple[bool, str]:
        """Test card read simulation"""
        if not self.test_card_numbers or not self.test_door_ids:
            return False, "Missing test card or door"

        async with httpx.AsyncClient() as client:
            data = {
                "card_number": self.test_card_numbers[0],
                "door_id": self.test_door_ids[0],
                "reader_id": 1
            }
            resp = await client.post(f"{self.hal_url}/hal/simulate/card-read", json=data, timeout=5)
            if resp.status_code == 200:
                result = resp.json()
                return True, f"Event ID: {result.get('event_id', 'N/A')[:8]}..."
            return False, f"Status {resp.status_code}"

    async def test_hal_events_list(self) -> Tuple[bool, str]:
        """Test listing events from HAL"""
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{self.hal_url}/hal/events?limit=10", timeout=5)
            if resp.status_code == 200:
                events = resp.json()
                return True, f"Retrieved {len(events)} events"
            return False, f"Status {resp.status_code}"

    async def test_hal_diagnostics(self) -> Tuple[bool, str]:
        """Test diagnostics endpoint"""
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{self.hal_url}/hal/diagnostics", timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                tables = data.get("tables", {})
                return True, f"Tables: {len(tables)}, Cards: {tables.get('cards', 0)}"
            return False, f"Status {resp.status_code}"

    async def test_hal_export(self) -> Tuple[bool, str]:
        """Test configuration export"""
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{self.hal_url}/hal/export", timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                cards = len(data.get("cards", []))
                levels = len(data.get("access_levels", []))
                doors = len(data.get("doors", []))
                return True, f"Export: {cards} cards, {levels} levels, {doors} doors"
            return False, f"Status {resp.status_code}"

    # ==========================================================================
    # Aether Access Tests
    # ==========================================================================

    async def test_aether_connectivity(self) -> Tuple[bool, str]:
        """Test Aether Access API connectivity"""
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{self.aether_url}/api/test/connectivity", timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                return True, f"Aether v{data.get('aether_version', 'unknown')}, HAL: {data.get('hal_status')}"
            return False, f"Status {resp.status_code}"

    async def test_aether_dashboard(self) -> Tuple[bool, str]:
        """Test Aether dashboard stats"""
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{self.aether_url}/api/dashboard/stats", timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                cards = data.get("total_cards", 0)
                events = data.get("total_events_today", 0)
                return True, f"Cards: {cards}, Events today: {events}"
            return False, f"Status {resp.status_code}"

    async def test_aether_cards_list(self) -> Tuple[bool, str]:
        """Test Aether cards listing"""
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{self.aether_url}/api/cards?limit=5", timeout=5)
            if resp.status_code == 200:
                cards = resp.json()
                return True, f"Retrieved {len(cards)} cards"
            return False, f"Status {resp.status_code}"

    async def test_aether_events_list(self) -> Tuple[bool, str]:
        """Test Aether events listing with formatting"""
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{self.aether_url}/api/events?limit=5", timeout=5)
            if resp.status_code == 200:
                events = resp.json()
                return True, f"Retrieved {len(events)} formatted events"
            return False, f"Status {resp.status_code}"

    async def test_aether_run_all_tests(self) -> Tuple[bool, str]:
        """Test Aether's built-in test suite"""
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{self.aether_url}/api/test/run-all", timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                passed = data.get("passed", 0)
                failed = data.get("failed", 0)
                if failed == 0:
                    return True, f"All {passed} tests passed"
                return False, f"{passed} passed, {failed} failed"
            return False, f"Status {resp.status_code}"

    async def test_aether_card_crud(self) -> Tuple[bool, str]:
        """Test Aether's CRUD test endpoint"""
        async with httpx.AsyncClient() as client:
            resp = await client.post(f"{self.aether_url}/api/test/card-crud", timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("success"):
                    steps = len(data.get("steps", []))
                    return True, f"All {steps} CRUD steps passed"
                failed_steps = [s["step"] for s in data.get("steps", []) if s.get("status") != "PASS"]
                return False, f"Failed steps: {', '.join(failed_steps)}"
            return False, f"Status {resp.status_code}"

    async def test_aether_access_decision(self) -> Tuple[bool, str]:
        """Test Aether's access decision test endpoint"""
        if not self.test_card_numbers or not self.test_door_ids:
            return False, "Missing test card or door"

        async with httpx.AsyncClient() as client:
            data = {
                "card_number": self.test_card_numbers[0],
                "door_id": self.test_door_ids[0]
            }
            resp = await client.post(f"{self.aether_url}/api/test/access-decision", json=data, timeout=5)
            if resp.status_code == 200:
                result = resp.json()
                return True, f"Decision tested successfully"
            return False, f"Status {resp.status_code}"

    # ==========================================================================
    # Cleanup
    # ==========================================================================

    async def cleanup(self):
        """Clean up test resources"""
        self.log("Cleaning up test resources...")
        async with httpx.AsyncClient() as client:
            # Delete test cards
            for card_number in self.test_card_numbers:
                try:
                    await client.delete(f"{self.hal_url}/hal/cards/{card_number}", timeout=5)
                    self.log(f"Deleted card {card_number}")
                except Exception as e:
                    self.log(f"Failed to delete card {card_number}: {e}")

            # Delete test access levels
            for level_id in self.test_access_level_ids:
                try:
                    await client.delete(f"{self.hal_url}/hal/access-levels/{level_id}", timeout=5)
                    self.log(f"Deleted access level {level_id}")
                except Exception as e:
                    self.log(f"Failed to delete access level {level_id}: {e}")

            # Note: We don't delete doors as they may have events associated

    # ==========================================================================
    # Main Run Methods
    # ==========================================================================

    async def run_hal_tests(self):
        """Run all HAL Core API tests"""
        print("\n" + "=" * 60)
        print("HAL CORE API TESTS")
        print("=" * 60)

        await self.run_test("HAL Connectivity", self.test_hal_connectivity)
        await self.run_test("HAL Health", self.test_hal_health)
        await self.run_test("HAL Card Create", self.test_hal_card_create)
        await self.run_test("HAL Card Read", self.test_hal_card_read)
        await self.run_test("HAL Card Update", self.test_hal_card_update)
        await self.run_test("HAL Access Level Create", self.test_hal_access_level_create)
        await self.run_test("HAL Door Create", self.test_hal_door_create)
        await self.run_test("HAL Access Decision", self.test_hal_access_decision)
        await self.run_test("HAL Card Read Simulation", self.test_hal_simulate_card_read)
        await self.run_test("HAL Events List", self.test_hal_events_list)
        await self.run_test("HAL Diagnostics", self.test_hal_diagnostics)
        await self.run_test("HAL Export", self.test_hal_export)

    async def run_aether_tests(self):
        """Run all Aether Access API tests"""
        print("\n" + "=" * 60)
        print("AETHER ACCESS API TESTS")
        print("=" * 60)

        await self.run_test("Aether Connectivity", self.test_aether_connectivity)
        await self.run_test("Aether Dashboard", self.test_aether_dashboard)
        await self.run_test("Aether Cards List", self.test_aether_cards_list)
        await self.run_test("Aether Events List", self.test_aether_events_list)
        await self.run_test("Aether Built-in Tests", self.test_aether_run_all_tests)
        await self.run_test("Aether CRUD Test", self.test_aether_card_crud)
        await self.run_test("Aether Access Decision", self.test_aether_access_decision)

    async def run_all(self, hal_only: bool = False, aether_only: bool = False):
        """Run the full test suite"""
        print("=" * 60)
        print("HAL + AETHER ACCESS INTEGRATION TEST SUITE")
        print("=" * 60)
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"HAL URL: {self.hal_url}")
        print(f"Aether URL: {self.aether_url}")

        try:
            if not aether_only:
                await self.run_hal_tests()

            if not hal_only:
                await self.run_aether_tests()
        finally:
            await self.cleanup()

        # Summary
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)

        passed = sum(1 for r in self.results if r.passed)
        failed = sum(1 for r in self.results if not r.passed)
        total = len(self.results)

        print(f"Total:  {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Rate:   {(passed/total*100) if total > 0 else 0:.1f}%")

        if failed > 0:
            print("\nFailed tests:")
            for r in self.results:
                if not r.passed:
                    print(f"  - {r.name}: {r.message}")

        print("=" * 60)
        return failed == 0


def main():
    parser = argparse.ArgumentParser(description="HAL + Aether Access Integration Tests")
    parser.add_argument("--hal-only", action="store_true", help="Only run HAL tests")
    parser.add_argument("--aether-only", action="store_true", help="Only run Aether tests")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--hal-url", default=HAL_URL, help=f"HAL Core URL (default: {HAL_URL})")
    parser.add_argument("--aether-url", default=AETHER_URL, help=f"Aether URL (default: {AETHER_URL})")
    args = parser.parse_args()

    suite = IntegrationTestSuite(
        hal_url=args.hal_url,
        aether_url=args.aether_url,
        verbose=args.verbose
    )

    success = asyncio.run(suite.run_all(
        hal_only=args.hal_only,
        aether_only=args.aether_only
    ))

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
