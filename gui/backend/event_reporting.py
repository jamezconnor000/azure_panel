#!/usr/bin/env python3
"""
Aether Access - Event Reporting & Cataloging System

This module provides human-readable event reporting, search, and cataloging
capabilities for Aether Access. It READS raw event data from HAL Core and
provides context, meaning, and searchable reports.

Architecture:
    HAL Core (port 8081)     Aether Access (port 8080)
    [Raw Events in SQLite] --> [Event Reporting Module] --> [Human-Readable UI]

Key Features:
- Read raw events from HAL and add human-readable context
- Full-text search across events
- Statistical analysis and reporting
- Export to CSV/JSON/PDF
- Event categorization and filtering
- Audit trail visualization
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from pydantic import BaseModel, Field
from enum import IntEnum
import asyncio
import aiohttp
import json
import csv
import io


# =============================================================================
# Configuration
# =============================================================================

HAL_CORE_URL = "http://localhost:8081"


# =============================================================================
# Event Types (matching HAL Core)
# =============================================================================

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


# Human-readable event type names
EVENT_TYPE_NAMES = {
    EventType.CARD_READ: "Card Read",
    EventType.ACCESS_GRANTED: "Access Granted",
    EventType.ACCESS_DENIED: "Access Denied",
    EventType.DOOR_FORCED: "Door Forced",
    EventType.DOOR_HELD: "Door Held Open",
    EventType.DOOR_OPENED: "Door Opened",
    EventType.DOOR_CLOSED: "Door Closed",
    EventType.RELAY_ACTIVATED: "Relay Activated",
    EventType.RELAY_DEACTIVATED: "Relay Deactivated",
    EventType.READER_TAMPER: "Reader Tamper",
    EventType.SYSTEM_EVENT: "System Event",
    EventType.CONFIG_CHANGE: "Configuration Change",
    EventType.ALARM: "Alarm",
    EventType.TROUBLE: "Trouble",
}

# Event severity levels
EVENT_SEVERITY = {
    EventType.CARD_READ: "info",
    EventType.ACCESS_GRANTED: "success",
    EventType.ACCESS_DENIED: "warning",
    EventType.DOOR_FORCED: "critical",
    EventType.DOOR_HELD: "warning",
    EventType.DOOR_OPENED: "info",
    EventType.DOOR_CLOSED: "info",
    EventType.RELAY_ACTIVATED: "info",
    EventType.RELAY_DEACTIVATED: "info",
    EventType.READER_TAMPER: "critical",
    EventType.SYSTEM_EVENT: "info",
    EventType.CONFIG_CHANGE: "info",
    EventType.ALARM: "critical",
    EventType.TROUBLE: "warning",
}


# =============================================================================
# Pydantic Models - Human-Readable Event Format
# =============================================================================

class EventDisplay(BaseModel):
    """Human-readable event format for UI display"""
    id: int
    event_id: str
    timestamp: int
    timestamp_formatted: str
    event_type: int
    event_type_name: str
    severity: str
    card_number: Optional[str]
    cardholder_name: Optional[str]
    door_id: Optional[int]
    door_name: Optional[str]
    granted: Optional[bool]
    reason: Optional[str]
    description: str
    extra_data: Optional[Dict[str, Any]]


class EventSearchRequest(BaseModel):
    """Search parameters for events"""
    query: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    event_types: Optional[List[int]] = None
    severities: Optional[List[str]] = None
    card_numbers: Optional[List[str]] = None
    cardholder_names: Optional[List[str]] = None
    door_ids: Optional[List[int]] = None
    granted: Optional[bool] = None
    limit: int = 100
    offset: int = 0
    sort_order: str = "desc"


class EventStatistics(BaseModel):
    """Statistical summary of events"""
    total_events: int
    events_by_type: Dict[str, int]
    events_by_severity: Dict[str, int]
    events_by_door: Dict[str, int]
    events_by_hour: Dict[int, int]
    events_by_day: Dict[str, int]
    access_granted_count: int
    access_denied_count: int
    grant_rate_percent: float
    top_cardholders: List[Dict[str, Any]]
    top_doors: List[Dict[str, Any]]
    alarms_and_troubles: int
    time_range: Dict[str, Any]


class ConfigChangeDisplay(BaseModel):
    """Human-readable config change for audit trail"""
    id: int
    timestamp: int
    timestamp_formatted: str
    change_type: str
    change_type_display: str
    resource_id: Optional[str]
    action: str
    action_display: str
    source: str
    source_user: Optional[str]
    summary: str
    old_value: Optional[Dict[str, Any]]
    new_value: Optional[Dict[str, Any]]


# =============================================================================
# HAL Client for Event Data
# =============================================================================

class HALEventClient:
    """Client for fetching raw event data from HAL Core"""

    def __init__(self, hal_url: str = HAL_CORE_URL):
        self.hal_url = hal_url
        self._doors_cache: Dict[int, str] = {}
        self._cards_cache: Dict[str, str] = {}
        self._cache_time: float = 0

    async def _refresh_cache(self):
        """Refresh door and card name caches"""
        current_time = asyncio.get_event_loop().time()
        if current_time - self._cache_time > 60:  # Refresh every 60 seconds
            async with aiohttp.ClientSession() as session:
                try:
                    # Fetch doors
                    async with session.get(f"{self.hal_url}/hal/doors") as resp:
                        if resp.status == 200:
                            doors = await resp.json()
                            self._doors_cache = {d["id"]: d["door_name"] for d in doors}

                    # Fetch cards (limited for performance)
                    async with session.get(f"{self.hal_url}/hal/cards?limit=10000") as resp:
                        if resp.status == 200:
                            cards = await resp.json()
                            self._cards_cache = {
                                c["card_number"]: c["holder_name"]
                                for c in cards if c.get("holder_name")
                            }

                    self._cache_time = current_time
                except Exception:
                    pass  # Use stale cache if HAL unreachable

    def _get_door_name(self, door_id: Optional[int]) -> Optional[str]:
        """Get door name from cache"""
        if door_id is None:
            return None
        return self._doors_cache.get(door_id, f"Door {door_id}")

    def _get_cardholder_name(self, card_number: Optional[str]) -> Optional[str]:
        """Get cardholder name from cache"""
        if card_number is None:
            return None
        return self._cards_cache.get(card_number)

    async def get_events(
        self,
        limit: int = 100,
        offset: int = 0,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        event_type: Optional[int] = None,
        card_number: Optional[str] = None,
        door_id: Optional[int] = None,
        order: str = "desc"
    ) -> List[Dict[str, Any]]:
        """Fetch raw events from HAL Core"""
        await self._refresh_cache()

        params = {
            "limit": limit,
            "offset": offset,
            "order": order
        }
        if start_time:
            params["start_time"] = start_time
        if end_time:
            params["end_time"] = end_time
        if event_type is not None:
            params["event_type"] = event_type
        if card_number:
            params["card_number"] = card_number
        if door_id is not None:
            params["door_id"] = door_id

        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.hal_url}/hal/events", params=params) as resp:
                if resp.status != 200:
                    return []
                return await resp.json()

    async def get_event_count(
        self,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        event_type: Optional[int] = None
    ) -> int:
        """Get event count from HAL Core"""
        params = {}
        if start_time:
            params["start_time"] = start_time
        if end_time:
            params["end_time"] = end_time
        if event_type is not None:
            params["event_type"] = event_type

        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.hal_url}/hal/events/count", params=params) as resp:
                if resp.status != 200:
                    return 0
                data = await resp.json()
                return data.get("count", 0)

    async def get_config_changes(
        self,
        limit: int = 100,
        offset: int = 0,
        change_type: Optional[str] = None,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Fetch config changes from HAL Core"""
        params = {"limit": limit, "offset": offset}
        if change_type:
            params["change_type"] = change_type
        if start_time:
            params["start_time"] = start_time
        if end_time:
            params["end_time"] = end_time

        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.hal_url}/hal/config-changes", params=params) as resp:
                if resp.status != 200:
                    return []
                return await resp.json()

    def format_event(self, raw_event: Dict[str, Any]) -> EventDisplay:
        """Convert raw HAL event to human-readable format"""
        event_type = raw_event.get("event_type", 0)
        timestamp = raw_event.get("timestamp", 0)
        door_id = raw_event.get("door_id")
        card_number = raw_event.get("card_number")

        # Format timestamp
        timestamp_formatted = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")

        # Get names from cache
        door_name = self._get_door_name(door_id)
        cardholder_name = self._get_cardholder_name(card_number)

        # Build description
        description = self._build_description(raw_event, door_name, cardholder_name)

        return EventDisplay(
            id=raw_event.get("id", 0),
            event_id=raw_event.get("event_id", ""),
            timestamp=timestamp,
            timestamp_formatted=timestamp_formatted,
            event_type=event_type,
            event_type_name=EVENT_TYPE_NAMES.get(event_type, f"Unknown ({event_type})"),
            severity=EVENT_SEVERITY.get(event_type, "info"),
            card_number=card_number,
            cardholder_name=cardholder_name,
            door_id=door_id,
            door_name=door_name,
            granted=raw_event.get("granted"),
            reason=raw_event.get("reason"),
            description=description,
            extra_data=raw_event.get("extra_data")
        )

    def _build_description(
        self,
        event: Dict[str, Any],
        door_name: Optional[str],
        cardholder_name: Optional[str]
    ) -> str:
        """Build human-readable event description"""
        event_type = event.get("event_type", 0)
        card_number = event.get("card_number")
        granted = event.get("granted")
        reason = event.get("reason", "")

        # Identify the person
        person = cardholder_name or (f"Card {card_number}" if card_number else "Unknown")

        # Identify the location
        location = door_name or (f"Door {event.get('door_id')}" if event.get('door_id') else "")

        # Build based on event type
        if event_type == EventType.ACCESS_GRANTED:
            return f"{person} granted access at {location}"
        elif event_type == EventType.ACCESS_DENIED:
            deny_reason = reason or "Unknown reason"
            return f"{person} denied access at {location}: {deny_reason}"
        elif event_type == EventType.CARD_READ:
            return f"Card read: {person} at {location}"
        elif event_type == EventType.DOOR_FORCED:
            return f"ALARM: Door forced open at {location}"
        elif event_type == EventType.DOOR_HELD:
            return f"WARNING: Door held open at {location}"
        elif event_type == EventType.DOOR_OPENED:
            return f"Door opened: {location}"
        elif event_type == EventType.DOOR_CLOSED:
            return f"Door closed: {location}"
        elif event_type == EventType.READER_TAMPER:
            return f"ALARM: Reader tamper detected at {location}"
        elif event_type == EventType.SYSTEM_EVENT:
            return reason or "System event"
        elif event_type == EventType.CONFIG_CHANGE:
            return f"Configuration changed: {reason or 'See details'}"
        elif event_type == EventType.ALARM:
            return f"ALARM: {reason or 'See details'} at {location}"
        elif event_type == EventType.TROUBLE:
            return f"TROUBLE: {reason or 'See details'} at {location}"
        else:
            return reason or f"Event type {event_type}"

    def format_config_change(self, raw_change: Dict[str, Any]) -> ConfigChangeDisplay:
        """Convert raw config change to human-readable format"""
        timestamp = raw_change.get("timestamp", 0)
        timestamp_formatted = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")

        change_type = raw_change.get("change_type", "")
        action = raw_change.get("action", 0)
        resource_id = raw_change.get("resource_id")
        source = raw_change.get("source", 1)

        # Map action codes
        action_map = {1: "Created", 2: "Updated", 3: "Deleted"}
        action_display = action_map.get(action, f"Action {action}")

        # Map source codes
        source_map = {1: "Local", 2: "Aether Access", 3: "External PACS", 4: "Import"}
        source_display = source_map.get(source, f"Source {source}")

        # Format change type
        change_type_display = change_type.replace("_", " ").title()

        # Build summary
        summary = self._build_change_summary(raw_change, change_type_display, action_display)

        return ConfigChangeDisplay(
            id=raw_change.get("id", 0),
            timestamp=timestamp,
            timestamp_formatted=timestamp_formatted,
            change_type=change_type,
            change_type_display=change_type_display,
            resource_id=resource_id,
            action=action_display,
            action_display=action_display,
            source=source_display,
            source_user=raw_change.get("source_user"),
            summary=summary,
            old_value=raw_change.get("old_value"),
            new_value=raw_change.get("new_value")
        )

    def _build_change_summary(
        self,
        change: Dict[str, Any],
        change_type: str,
        action: str
    ) -> str:
        """Build human-readable change summary"""
        resource_id = change.get("resource_id", "")
        new_value = change.get("new_value", {})
        old_value = change.get("old_value", {})

        if change.get("change_type") == "card":
            holder = new_value.get("holder_name") or old_value.get("holder_name") or resource_id
            return f"{action} card for {holder}"
        elif change.get("change_type") == "access_level":
            name = new_value.get("name") or old_value.get("name") or resource_id
            return f"{action} access level: {name}"
        elif change.get("change_type") == "door":
            name = new_value.get("door_name") or old_value.get("door_name") or resource_id
            return f"{action} door: {name}"
        elif change.get("change_type") == "bulk_sync":
            cards = new_value.get("cards", 0)
            levels = new_value.get("access_levels", 0)
            return f"Bulk sync: {cards} cards, {levels} access levels"
        else:
            return f"{action} {change_type}: {resource_id}"


# =============================================================================
# Event Reporting Service
# =============================================================================

class EventReportingService:
    """Main service for event reporting and analysis"""

    def __init__(self, hal_url: str = HAL_CORE_URL):
        self.client = HALEventClient(hal_url)

    async def search_events(self, request: EventSearchRequest) -> Tuple[List[EventDisplay], int]:
        """
        Search events with human-readable formatting.
        Returns (events, total_count)
        """
        # Convert dates to timestamps
        start_time = int(request.start_date.timestamp()) if request.start_date else None
        end_time = int(request.end_date.timestamp()) if request.end_date else None

        # Fetch from HAL
        raw_events = await self.client.get_events(
            limit=request.limit,
            offset=request.offset,
            start_time=start_time,
            end_time=end_time,
            order=request.sort_order
        )

        # Format events
        formatted = [self.client.format_event(e) for e in raw_events]

        # Apply additional filters that HAL doesn't support
        if request.query:
            query_lower = request.query.lower()
            formatted = [
                e for e in formatted
                if query_lower in e.description.lower()
                or (e.cardholder_name and query_lower in e.cardholder_name.lower())
                or (e.card_number and query_lower in e.card_number.lower())
                or (e.door_name and query_lower in e.door_name.lower())
            ]

        if request.severities:
            formatted = [e for e in formatted if e.severity in request.severities]

        if request.cardholder_names:
            names_lower = [n.lower() for n in request.cardholder_names]
            formatted = [
                e for e in formatted
                if e.cardholder_name and e.cardholder_name.lower() in names_lower
            ]

        if request.event_types:
            formatted = [e for e in formatted if e.event_type in request.event_types]

        if request.card_numbers:
            formatted = [e for e in formatted if e.card_number in request.card_numbers]

        if request.door_ids:
            formatted = [e for e in formatted if e.door_id in request.door_ids]

        if request.granted is not None:
            formatted = [e for e in formatted if e.granted == request.granted]

        # Get total count
        total = await self.client.get_event_count(start_time=start_time, end_time=end_time)

        return formatted, total

    async def get_statistics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> EventStatistics:
        """Generate statistical summary of events"""
        # Default to last 7 days
        if not end_date:
            end_date = datetime.now()
        if not start_date:
            start_date = end_date - timedelta(days=7)

        start_time = int(start_date.timestamp())
        end_time = int(end_date.timestamp())

        # Fetch all events in range (up to 10000 for stats)
        raw_events = await self.client.get_events(
            limit=10000,
            start_time=start_time,
            end_time=end_time,
            order="asc"
        )

        formatted = [self.client.format_event(e) for e in raw_events]

        # Calculate statistics
        events_by_type: Dict[str, int] = {}
        events_by_severity: Dict[str, int] = {}
        events_by_door: Dict[str, int] = {}
        events_by_hour: Dict[int, int] = {h: 0 for h in range(24)}
        events_by_day: Dict[str, int] = {}
        cardholder_counts: Dict[str, int] = {}
        door_counts: Dict[str, int] = {}

        access_granted = 0
        access_denied = 0
        alarms_troubles = 0

        for event in formatted:
            # By type
            type_name = event.event_type_name
            events_by_type[type_name] = events_by_type.get(type_name, 0) + 1

            # By severity
            events_by_severity[event.severity] = events_by_severity.get(event.severity, 0) + 1

            # By door
            if event.door_name:
                events_by_door[event.door_name] = events_by_door.get(event.door_name, 0) + 1
                door_counts[event.door_name] = door_counts.get(event.door_name, 0) + 1

            # By hour
            hour = datetime.fromtimestamp(event.timestamp).hour
            events_by_hour[hour] += 1

            # By day
            day = datetime.fromtimestamp(event.timestamp).strftime("%Y-%m-%d")
            events_by_day[day] = events_by_day.get(day, 0) + 1

            # Cardholder activity
            if event.cardholder_name:
                cardholder_counts[event.cardholder_name] = cardholder_counts.get(event.cardholder_name, 0) + 1

            # Access decisions
            if event.event_type == EventType.ACCESS_GRANTED:
                access_granted += 1
            elif event.event_type == EventType.ACCESS_DENIED:
                access_denied += 1

            # Alarms and troubles
            if event.severity == "critical" or event.severity == "warning":
                alarms_troubles += 1

        # Calculate grant rate
        total_access = access_granted + access_denied
        grant_rate = (access_granted / total_access * 100) if total_access > 0 else 0

        # Top cardholders
        top_cardholders = sorted(
            [{"name": k, "count": v} for k, v in cardholder_counts.items()],
            key=lambda x: x["count"],
            reverse=True
        )[:10]

        # Top doors
        top_doors = sorted(
            [{"name": k, "count": v} for k, v in door_counts.items()],
            key=lambda x: x["count"],
            reverse=True
        )[:10]

        return EventStatistics(
            total_events=len(formatted),
            events_by_type=events_by_type,
            events_by_severity=events_by_severity,
            events_by_door=events_by_door,
            events_by_hour=events_by_hour,
            events_by_day=events_by_day,
            access_granted_count=access_granted,
            access_denied_count=access_denied,
            grant_rate_percent=round(grant_rate, 1),
            top_cardholders=top_cardholders,
            top_doors=top_doors,
            alarms_and_troubles=alarms_troubles,
            time_range={
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            }
        )

    async def get_audit_trail(
        self,
        limit: int = 100,
        offset: int = 0,
        change_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[ConfigChangeDisplay]:
        """Get formatted audit trail of configuration changes"""
        start_time = int(start_date.timestamp()) if start_date else None
        end_time = int(end_date.timestamp()) if end_date else None

        raw_changes = await self.client.get_config_changes(
            limit=limit,
            offset=offset,
            change_type=change_type,
            start_time=start_time,
            end_time=end_time
        )

        return [self.client.format_config_change(c) for c in raw_changes]

    async def export_events_csv(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        event_types: Optional[List[int]] = None
    ) -> str:
        """Export events to CSV format"""
        request = EventSearchRequest(
            start_date=start_date,
            end_date=end_date,
            event_types=event_types,
            limit=50000  # Max export
        )
        events, _ = await self.search_events(request)

        output = io.StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow([
            "Timestamp", "Event Type", "Severity", "Card Number",
            "Cardholder", "Door", "Granted", "Description"
        ])

        # Data
        for event in events:
            writer.writerow([
                event.timestamp_formatted,
                event.event_type_name,
                event.severity,
                event.card_number or "",
                event.cardholder_name or "",
                event.door_name or "",
                "Yes" if event.granted else "No" if event.granted is False else "",
                event.description
            ])

        return output.getvalue()

    async def export_events_json(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        event_types: Optional[List[int]] = None
    ) -> str:
        """Export events to JSON format"""
        request = EventSearchRequest(
            start_date=start_date,
            end_date=end_date,
            event_types=event_types,
            limit=50000
        )
        events, total = await self.search_events(request)

        export_data = {
            "exported_at": datetime.now().isoformat(),
            "total_events": total,
            "events": [event.model_dump() for event in events]
        }

        return json.dumps(export_data, indent=2)


# =============================================================================
# Cardholder & Access Level Reporting
# =============================================================================

class AccessReportingService:
    """Service for cardholder and access level reporting"""

    def __init__(self, hal_url: str = HAL_CORE_URL):
        self.hal_url = hal_url

    async def get_cardholders(
        self,
        limit: int = 100,
        offset: int = 0,
        search: Optional[str] = None,
        active_only: bool = False,
        access_level_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get cardholders with access level details"""
        params = {
            "limit": limit,
            "offset": offset,
            "active_only": active_only
        }
        if search:
            params["search"] = search
        if access_level_id:
            params["permission_id"] = access_level_id

        async with aiohttp.ClientSession() as session:
            # Get cards
            async with session.get(f"{self.hal_url}/hal/cards", params=params) as resp:
                if resp.status != 200:
                    return []
                cards = await resp.json()

            # Get access levels for context
            async with session.get(f"{self.hal_url}/hal/access-levels") as resp:
                if resp.status == 200:
                    levels = await resp.json()
                    level_map = {l["id"]: l for l in levels}
                else:
                    level_map = {}

        # Enrich cards with access level info
        result = []
        for card in cards:
            level = level_map.get(card.get("permission_id"), {})
            card["access_level_name"] = level.get("name", "Unknown")
            card["access_level_doors"] = len(level.get("doors", []))

            # Format dates
            if card.get("activation_date"):
                card["activation_date_formatted"] = datetime.fromtimestamp(
                    card["activation_date"]
                ).strftime("%Y-%m-%d") if card["activation_date"] > 0 else "Always"
            else:
                card["activation_date_formatted"] = "Always"

            if card.get("expiration_date"):
                card["expiration_date_formatted"] = datetime.fromtimestamp(
                    card["expiration_date"]
                ).strftime("%Y-%m-%d") if card["expiration_date"] > 0 else "Never"
            else:
                card["expiration_date_formatted"] = "Never"

            if card.get("last_access_time"):
                card["last_access_formatted"] = datetime.fromtimestamp(
                    card["last_access_time"]
                ).strftime("%Y-%m-%d %H:%M:%S")
            else:
                card["last_access_formatted"] = "Never"

            result.append(card)

        return result

    async def get_access_levels_report(self) -> List[Dict[str, Any]]:
        """Get access levels with cardholder counts"""
        async with aiohttp.ClientSession() as session:
            # Get access levels
            async with session.get(f"{self.hal_url}/hal/access-levels") as resp:
                if resp.status != 200:
                    return []
                levels = await resp.json()

            # Get card counts per level
            async with session.get(f"{self.hal_url}/hal/cards?limit=100000") as resp:
                if resp.status == 200:
                    cards = await resp.json()
                    level_counts = {}
                    for card in cards:
                        pid = card.get("permission_id", 0)
                        level_counts[pid] = level_counts.get(pid, 0) + 1
                else:
                    level_counts = {}

        # Enrich levels
        for level in levels:
            level["cardholder_count"] = level_counts.get(level["id"], 0)
            level["door_count"] = len(level.get("doors", []))

            # Get door names
            level["door_names"] = [d.get("door_name", f"Door {d.get('door_id')}") for d in level.get("doors", [])]

        return levels

    async def get_door_report(self) -> List[Dict[str, Any]]:
        """Get doors with event statistics"""
        async with aiohttp.ClientSession() as session:
            # Get doors
            async with session.get(f"{self.hal_url}/hal/doors") as resp:
                if resp.status != 200:
                    return []
                doors = await resp.json()

        # Get recent events for each door
        for door in doors:
            door["status"] = "Online" if door.get("is_online") else "Offline"
            door["osdp_status"] = "Enabled" if door.get("osdp_enabled") else "Disabled"

            if door.get("last_event_time"):
                door["last_event_formatted"] = datetime.fromtimestamp(
                    door["last_event_time"]
                ).strftime("%Y-%m-%d %H:%M:%S")
            else:
                door["last_event_formatted"] = "No events"

        return doors


# =============================================================================
# Singleton Instances
# =============================================================================

event_reporting = EventReportingService()
access_reporting = AccessReportingService()
