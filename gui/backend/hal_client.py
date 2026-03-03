#!/usr/bin/env python3
"""
HAL Client - Aether Access Interface to HAL Core

This module provides the connection between Aether Access (the management UI)
and HAL Core (the panel brain). Aether Access READS from HAL and can WRITE
changes to HAL, but HAL is the single source of truth.

HAL operates like a Mercury panel - all data is stored locally and access
decisions are made locally without requiring network connectivity.
"""

import aiohttp
import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime
import json
import os

# HAL API Configuration
HAL_API_HOST = os.environ.get("HAL_API_HOST", "localhost")
HAL_API_PORT = int(os.environ.get("HAL_API_PORT", "8081"))
HAL_API_BASE = f"http://{HAL_API_HOST}:{HAL_API_PORT}"


class HALClient:
    """
    Client for communicating with HAL Core API

    HAL is the "brain" of the panel and owns all access control data.
    This client allows Aether Access to:
    - READ cards, access levels, doors, events from HAL
    - WRITE changes to HAL (which logs them in its audit trail)
    - STREAM real-time events from HAL

    All data lives in HAL's local SQLite database and HAL makes all
    access decisions locally, just like a Mercury panel.
    """

    def __init__(self, base_url: str = HAL_API_BASE):
        self.base_url = base_url
        self._connected = False

    def _get_headers(self, source: str = "aether", source_user: str = None, transaction_id: str = None) -> Dict[str, str]:
        """Build headers for HAL API calls"""
        headers = {"X-HAL-Source": source}
        if source_user:
            headers["X-HAL-User"] = source_user
        if transaction_id:
            headers["X-HAL-Transaction"] = transaction_id
        return headers

    async def check_connection(self) -> bool:
        """Check if HAL API is reachable"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/hal/health") as resp:
                    self._connected = resp.status == 200
                    return self._connected
        except Exception:
            self._connected = False
            return False

    @property
    def is_connected(self) -> bool:
        return self._connected

    async def get_health(self) -> Dict[str, Any]:
        """Get HAL system health"""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/hal/health") as resp:
                if resp.status == 200:
                    return await resp.json()
                raise Exception(f"HAL health check failed: {resp.status}")

    # =========================================================================
    # CARD DATABASE OPERATIONS
    # HAL stores up to 1M+ cards locally
    # =========================================================================

    async def get_cards(
        self,
        limit: int = 100,
        offset: int = 0,
        permission_id: Optional[int] = None,
        active_only: bool = False,
        search: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get cards from HAL's local database"""
        params = {"limit": limit, "offset": offset, "active_only": active_only}
        if permission_id:
            params["permission_id"] = permission_id
        if search:
            params["search"] = search

        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/hal/cards", params=params) as resp:
                if resp.status == 200:
                    return await resp.json()
                raise Exception(f"Failed to get cards: {await resp.text()}")

    async def get_card(self, card_number: str) -> Dict[str, Any]:
        """Get a single card from HAL"""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/hal/cards/{card_number}") as resp:
                if resp.status == 200:
                    return await resp.json()
                raise Exception(f"Card not found: {card_number}")

    async def create_card(
        self,
        card_number: str,
        permission_id: int = 1,
        holder_name: str = "",
        facility_code: int = 0,
        pin: Optional[str] = None,
        activation_date: int = 0,
        expiration_date: int = 0,
        source: str = "aether",
        source_user: str = None
    ) -> Dict[str, Any]:
        """Add a card to HAL's local database"""
        payload = {
            "card_number": card_number,
            "permission_id": permission_id,
            "holder_name": holder_name,
            "facility_code": facility_code,
            "activation_date": activation_date,
            "expiration_date": expiration_date,
            "is_active": True
        }
        if pin:
            payload["pin"] = pin

        headers = self._get_headers(source, source_user)

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/hal/cards",
                json=payload,
                headers=headers
            ) as resp:
                if resp.status in [200, 201]:
                    return await resp.json()
                raise Exception(f"Failed to create card: {await resp.text()}")

    async def update_card(
        self,
        card_number: str,
        source: str = "aether",
        source_user: str = None,
        **updates
    ) -> Dict[str, Any]:
        """Update a card in HAL's database"""
        headers = self._get_headers(source, source_user)

        async with aiohttp.ClientSession() as session:
            async with session.put(
                f"{self.base_url}/hal/cards/{card_number}",
                json=updates,
                headers=headers
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
                raise Exception(f"Failed to update card: {await resp.text()}")

    async def delete_card(
        self,
        card_number: str,
        source: str = "aether",
        source_user: str = None
    ) -> Dict[str, Any]:
        """Delete a card from HAL's database"""
        headers = self._get_headers(source, source_user)

        async with aiohttp.ClientSession() as session:
            async with session.delete(
                f"{self.base_url}/hal/cards/{card_number}",
                headers=headers
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
                raise Exception(f"Failed to delete card: {await resp.text()}")

    async def get_card_count(self) -> Dict[str, Any]:
        """Get total card count from HAL"""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/hal/cards/count") as resp:
                if resp.status == 200:
                    return await resp.json()
                return {"count": 0, "capacity": 1000000}

    # =========================================================================
    # ACCESS LEVEL OPERATIONS
    # Access levels define which doors a card can access and when
    # =========================================================================

    async def get_access_levels(self, include_doors: bool = True) -> List[Dict[str, Any]]:
        """Get all access levels from HAL"""
        params = {"include_doors": include_doors}
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/hal/access-levels", params=params) as resp:
                if resp.status == 200:
                    return await resp.json()
                raise Exception(f"Failed to get access levels: {await resp.text()}")

    async def get_access_level(self, level_id: int) -> Dict[str, Any]:
        """Get a single access level with its door assignments"""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/hal/access-levels/{level_id}") as resp:
                if resp.status == 200:
                    return await resp.json()
                raise Exception(f"Access level not found: {level_id}")

    async def create_access_level(
        self,
        name: str,
        description: str = "",
        priority: int = 0,
        door_ids: List[int] = None,
        source: str = "aether",
        source_user: str = None
    ) -> Dict[str, Any]:
        """Create an access level in HAL"""
        payload = {
            "name": name,
            "description": description,
            "priority": priority,
            "door_ids": door_ids or []
        }

        headers = self._get_headers(source, source_user)

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/hal/access-levels",
                json=payload,
                headers=headers
            ) as resp:
                if resp.status in [200, 201]:
                    return await resp.json()
                raise Exception(f"Failed to create access level: {await resp.text()}")

    async def update_access_level(
        self,
        level_id: int,
        source: str = "aether",
        source_user: str = None,
        **updates
    ) -> Dict[str, Any]:
        """Update an access level in HAL"""
        headers = self._get_headers(source, source_user)

        async with aiohttp.ClientSession() as session:
            async with session.put(
                f"{self.base_url}/hal/access-levels/{level_id}",
                json=updates,
                headers=headers
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
                raise Exception(f"Failed to update access level: {await resp.text()}")

    async def delete_access_level(
        self,
        level_id: int,
        source: str = "aether",
        source_user: str = None
    ) -> Dict[str, Any]:
        """Delete an access level from HAL"""
        headers = self._get_headers(source, source_user)

        async with aiohttp.ClientSession() as session:
            async with session.delete(
                f"{self.base_url}/hal/access-levels/{level_id}",
                headers=headers
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
                raise Exception(f"Failed to delete access level: {await resp.text()}")

    # =========================================================================
    # DOOR OPERATIONS
    # =========================================================================

    async def get_doors(self) -> List[Dict[str, Any]]:
        """Get all doors from HAL"""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/hal/doors") as resp:
                if resp.status == 200:
                    return await resp.json()
                raise Exception(f"Failed to get doors: {await resp.text()}")

    async def get_door(self, door_id: int) -> Dict[str, Any]:
        """Get a single door with current status"""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/hal/doors/{door_id}") as resp:
                if resp.status == 200:
                    return await resp.json()
                raise Exception(f"Door not found: {door_id}")

    async def control_door(
        self,
        door_id: int,
        action: str,  # "lock", "unlock", "momentary_unlock", "lockdown"
        duration_ms: Optional[int] = None,
        source: str = "aether",
        source_user: str = None
    ) -> Dict[str, Any]:
        """Send control command to a door"""
        payload = {"action": action}
        if duration_ms:
            payload["duration_ms"] = duration_ms

        headers = self._get_headers(source, source_user)

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/hal/doors/{door_id}/control",
                json=payload,
                headers=headers
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
                raise Exception(f"Failed to control door: {await resp.text()}")

    # =========================================================================
    # EVENT OPERATIONS
    # HAL stores 100K+ events locally (kept in RAW format)
    # =========================================================================

    async def get_events(
        self,
        limit: int = 100,
        offset: int = 0,
        door_id: Optional[int] = None,
        card_number: Optional[str] = None,
        event_type: Optional[int] = None,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        order: str = "desc"
    ) -> List[Dict[str, Any]]:
        """Get events from HAL's local event buffer (RAW format)"""
        params = {"limit": limit, "offset": offset, "order": order}
        if door_id:
            params["door_id"] = door_id
        if card_number:
            params["card_number"] = card_number
        if event_type is not None:
            params["event_type"] = event_type
        if start_time:
            params["start_time"] = start_time
        if end_time:
            params["end_time"] = end_time

        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/hal/events", params=params) as resp:
                if resp.status == 200:
                    return await resp.json()
                return []

    async def get_event_count(
        self,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        event_type: Optional[int] = None
    ) -> int:
        """Get event count from HAL"""
        params = {}
        if start_time:
            params["start_time"] = start_time
        if end_time:
            params["end_time"] = end_time
        if event_type is not None:
            params["event_type"] = event_type

        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/hal/events/count", params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("count", 0)
                return 0

    # =========================================================================
    # CONFIG CHANGE AUDIT TRAIL
    # HAL logs all configuration changes
    # =========================================================================

    async def get_config_changes(
        self,
        limit: int = 100,
        offset: int = 0,
        change_type: Optional[str] = None,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get configuration change audit trail from HAL

        This shows all changes to cards, access levels, doors, etc.
        with who made the change and when.
        """
        params = {"limit": limit, "offset": offset}
        if change_type:
            params["change_type"] = change_type
        if start_time:
            params["start_time"] = start_time
        if end_time:
            params["end_time"] = end_time

        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/hal/config-changes", params=params) as resp:
                if resp.status == 200:
                    return await resp.json()
                return []

    # =========================================================================
    # TIMEZONE OPERATIONS
    # =========================================================================

    async def list_timezones(self) -> List[Dict[str, Any]]:
        """Get all timezones from HAL"""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/hal/timezones") as resp:
                if resp.status == 200:
                    return await resp.json()
                return []

    async def create_timezone(
        self,
        name: str,
        description: str = "",
        intervals: List[Dict[str, Any]] = None,
        source: str = "aether",
        source_user: str = None
    ) -> Dict[str, Any]:
        """Create a timezone in HAL"""
        payload = {
            "name": name,
            "description": description,
            "intervals": intervals or []
        }
        headers = self._get_headers(source, source_user)

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/hal/timezones",
                json=payload,
                headers=headers
            ) as resp:
                if resp.status in [200, 201]:
                    return await resp.json()
                raise Exception(f"Failed to create timezone: {await resp.text()}")

    # =========================================================================
    # HOLIDAY OPERATIONS
    # =========================================================================

    async def list_holidays(self, year: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get holidays from HAL"""
        params = {}
        if year:
            params["year"] = year

        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/hal/holidays", params=params) as resp:
                if resp.status == 200:
                    return await resp.json()
                return []

    async def create_holiday(
        self,
        date: int,  # YYYYMMDD
        name: str = "",
        holiday_type: int = 1,
        source: str = "aether",
        source_user: str = None
    ) -> Dict[str, Any]:
        """Add a holiday to HAL"""
        payload = {
            "date": date,
            "name": name,
            "holiday_type": holiday_type
        }
        headers = self._get_headers(source, source_user)

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/hal/holidays",
                json=payload,
                headers=headers
            ) as resp:
                if resp.status in [200, 201]:
                    return await resp.json()
                raise Exception(f"Failed to create holiday: {await resp.text()}")

    # =========================================================================
    # BULK SYNC (for PACS integration)
    # =========================================================================

    async def bulk_sync(
        self,
        cards: Optional[List[Dict[str, Any]]] = None,
        access_levels: Optional[List[Dict[str, Any]]] = None,
        source: str = "pacs",
        source_user: str = None,
        transaction_id: str = None
    ) -> Dict[str, Any]:
        """
        Bulk sync from external PACS

        HAL will:
        - Add new cards/access levels
        - Update existing ones
        - Log all changes to audit trail
        """
        payload = {}
        if cards:
            payload["cards"] = [
                {
                    "card_number": c.get("card_number") or c.card_number,
                    "facility_code": c.get("facility_code", 0) if isinstance(c, dict) else c.facility_code,
                    "permission_id": c.get("permission_id", 1) if isinstance(c, dict) else c.permission_id,
                    "holder_name": c.get("holder_name", "") if isinstance(c, dict) else c.holder_name,
                    "activation_date": c.get("activation_date", 0) if isinstance(c, dict) else c.activation_date,
                    "expiration_date": c.get("expiration_date", 0) if isinstance(c, dict) else c.expiration_date,
                    "is_active": c.get("is_active", True) if isinstance(c, dict) else c.is_active
                }
                for c in cards
            ]
        if access_levels:
            payload["access_levels"] = [
                {
                    "id": al.get("id") if isinstance(al, dict) else al.id,
                    "name": al.get("name") if isinstance(al, dict) else al.name,
                    "description": al.get("description", "") if isinstance(al, dict) else al.description,
                    "door_ids": al.get("door_ids", []) if isinstance(al, dict) else al.door_ids
                }
                for al in access_levels
            ]
        if transaction_id:
            payload["transaction_id"] = transaction_id

        headers = self._get_headers(source, source_user, transaction_id)

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/hal/sync",
                json=payload,
                headers=headers
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
                raise Exception(f"Bulk sync failed: {await resp.text()}")

    # =========================================================================
    # EXPORT CONFIGURATION
    # =========================================================================

    async def export_configuration(self) -> Dict[str, Any]:
        """Export full HAL configuration as JSON"""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/hal/export") as resp:
                if resp.status == 200:
                    return await resp.json()
                raise Exception(f"Export failed: {await resp.text()}")
