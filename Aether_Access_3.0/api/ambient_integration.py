"""
Aether Bifrost - Ambient.ai Cloud Integration
==============================================
Translates HAL events and entities into Ambient.ai Generic Cloud format.

This module handles:
- Event translation (access events, alarms, door states)
- Entity synchronization (devices, persons, access items, alarms)
- Real-time event export daemon (< 2 second latency)
- UUID mapping for all entities

Ambient.ai Event Ingestion API:
- Events: POST https://pacs-ingestion.ambient.ai/v1/api/event
- Devices: POST https://pacs-ingestion.ambient.ai/v1/api/device
- Persons: POST https://pacs-ingestion.ambient.ai/v1/api/person
- Items: POST https://pacs-ingestion.ambient.ai/v1/api/item
- Alarms: POST https://pacs-ingestion.ambient.ai/v1/api/alarm
"""

import asyncio
import hashlib
import json
import logging
import os
import time
import uuid
from datetime import datetime
from enum import IntEnum
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict
import aiohttp

logger = logging.getLogger(__name__)

# =============================================================================
# Configuration
# =============================================================================

AMBIENT_API_BASE = os.getenv("AMBIENT_API_URL", "https://pacs-ingestion.ambient.ai/v1/api")
AMBIENT_API_KEY = os.getenv("AMBIENT_API_KEY", "")
SOURCE_SYSTEM_UID = os.getenv("AMBIENT_SOURCE_SYSTEM_UID", "")

# Maximum event age in seconds (events older than this won't be sent)
MAX_EVENT_AGE_SECONDS = 300  # 5 minutes

# Event queue settings
EVENT_QUEUE_MAX_SIZE = 10000
EVENT_BATCH_SIZE = 100
EVENT_SEND_INTERVAL = 0.5  # 500ms - ensures < 2s latency


# =============================================================================
# Ambient.ai Device Types
# =============================================================================

class AmbientDeviceType:
    READER = "Reader"
    PANEL = "Panel"
    ALARM_INPUT = "Alarm Input"
    DOOR = "Door"
    REX = "REX"


# =============================================================================
# HAL Event Type Mapping
# =============================================================================

class HALEventType(IntEnum):
    """HAL event types mapped to Ambient.ai alarm types"""
    ACCESS_GRANTED = 1
    ACCESS_DENIED = 2
    DOOR_OPENED = 3
    DOOR_CLOSED = 4
    DOOR_FORCED = 5
    DOOR_HELD_OPEN = 6
    READER_TAMPER = 7
    PANEL_TAMPER = 8
    REX_ACTIVATED = 9
    LOCKDOWN_ACTIVATED = 10
    LOCKDOWN_RELEASED = 11
    CARD_UNKNOWN = 12
    CARD_EXPIRED = 13
    CARD_INACTIVE = 14
    ANTI_PASSBACK_VIOLATION = 15
    SYSTEM_STARTUP = 16
    SYSTEM_SHUTDOWN = 17
    COMMUNICATION_LOST = 18
    COMMUNICATION_RESTORED = 19
    MANUAL_UNLOCK = 20
    MANUAL_LOCK = 21


# Ambient.ai alarm name mapping
HAL_TO_AMBIENT_ALARM = {
    HALEventType.ACCESS_GRANTED: "Access Granted",
    HALEventType.ACCESS_DENIED: "Access Denied",
    HALEventType.DOOR_OPENED: "Door Open",
    HALEventType.DOOR_CLOSED: "Door Closed",
    HALEventType.DOOR_FORCED: "Door Forced Open",
    HALEventType.DOOR_HELD_OPEN: "Door Held Open",
    HALEventType.READER_TAMPER: "Reader Tamper",
    HALEventType.PANEL_TAMPER: "Panel Tamper",
    HALEventType.REX_ACTIVATED: "REX Activated",
    HALEventType.LOCKDOWN_ACTIVATED: "Lockdown Activated",
    HALEventType.LOCKDOWN_RELEASED: "Lockdown Released",
    HALEventType.CARD_UNKNOWN: "Unknown Card",
    HALEventType.CARD_EXPIRED: "Expired Card",
    HALEventType.CARD_INACTIVE: "Inactive Card",
    HALEventType.ANTI_PASSBACK_VIOLATION: "Anti-Passback Violation",
    HALEventType.SYSTEM_STARTUP: "System Startup",
    HALEventType.SYSTEM_SHUTDOWN: "System Shutdown",
    HALEventType.COMMUNICATION_LOST: "Communication Lost",
    HALEventType.COMMUNICATION_RESTORED: "Communication Restored",
    HALEventType.MANUAL_UNLOCK: "Manual Unlock",
    HALEventType.MANUAL_LOCK: "Manual Lock",
}


# =============================================================================
# UUID Generation (Deterministic)
# =============================================================================

def generate_uuid(namespace: str, identifier: str) -> str:
    """
    Generate a deterministic UUID based on namespace and identifier.
    This ensures the same entity always gets the same UUID.
    """
    combined = f"{namespace}:{identifier}"
    hash_bytes = hashlib.sha256(combined.encode()).digest()[:16]
    return str(uuid.UUID(bytes=hash_bytes))


def device_uuid(door_id: int) -> str:
    """Generate UUID for a device (reader/door)"""
    return generate_uuid("aether:device", str(door_id))


def person_uuid(card_number: str) -> str:
    """Generate UUID for a person (cardholder)"""
    return generate_uuid("aether:person", card_number)


def item_uuid(card_number: str) -> str:
    """Generate UUID for an access item (credential)"""
    return generate_uuid("aether:item", card_number)


def alarm_uuid(event_type: int) -> str:
    """Generate UUID for an alarm type"""
    return generate_uuid("aether:alarm", str(event_type))


def event_uuid(event_id: int, timestamp: int) -> str:
    """Generate UUID for a specific event instance"""
    return generate_uuid("aether:event", f"{event_id}:{timestamp}")


# =============================================================================
# Data Classes for Ambient.ai Entities
# =============================================================================

@dataclass
class AmbientEvent:
    """Ambient.ai Event payload"""
    sourceSystemUid: str
    deviceUid: str
    deviceName: str
    deviceType: str
    eventUid: str
    alarmName: str
    alarmUid: str
    eventOccuredAtTimestamp: int
    eventPublishedAtTimestamp: int
    personUid: Optional[str] = None
    personFirstName: Optional[str] = None
    personLastName: Optional[str] = None
    accessItemKey: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict, excluding None values"""
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class AmbientDevice:
    """Ambient.ai Device entity"""
    sourceSystemUid: str
    deviceUid: str
    deviceName: str
    deviceType: str
    isDeleted: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AmbientPerson:
    """Ambient.ai Person entity"""
    sourceSystemUid: str
    personUid: str
    firstName: str
    lastName: str
    email: Optional[str] = None
    department: Optional[str] = None
    employeeId: Optional[str] = None
    isDeleted: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class AmbientAccessItem:
    """Ambient.ai Access Item (credential) entity"""
    sourceSystemUid: str
    accessItemUid: str
    accessItemKey: str  # Card number
    personUid: str
    isActive: bool = True
    isDeleted: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AmbientAlarm:
    """Ambient.ai Alarm type entity"""
    sourceSystemUid: str
    alarmUid: str
    alarmName: str
    isDeleted: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# =============================================================================
# HAL to Ambient.ai Translator
# =============================================================================

class AmbientTranslator:
    """Translates HAL data structures to Ambient.ai format"""

    def __init__(self, source_system_uid: str = None):
        self.source_system_uid = source_system_uid or SOURCE_SYSTEM_UID
        if not self.source_system_uid:
            # Generate a deterministic one based on the system
            self.source_system_uid = generate_uuid("aether:system", "azure-panel")
            logger.info(f"Generated source system UID: {self.source_system_uid}")

    def translate_event(
        self,
        event_id: int,
        event_type: int,
        door_id: int,
        door_name: str,
        timestamp: int,
        card_number: Optional[str] = None,
        holder_first_name: Optional[str] = None,
        holder_last_name: Optional[str] = None,
    ) -> AmbientEvent:
        """Translate a HAL event to Ambient.ai format"""

        alarm_name = HAL_TO_AMBIENT_ALARM.get(event_type, f"Unknown Event {event_type}")

        # Determine device type based on event
        if event_type in (HALEventType.ACCESS_GRANTED, HALEventType.ACCESS_DENIED,
                         HALEventType.CARD_UNKNOWN, HALEventType.CARD_EXPIRED,
                         HALEventType.CARD_INACTIVE, HALEventType.READER_TAMPER):
            device_type = AmbientDeviceType.READER
        elif event_type in (HALEventType.PANEL_TAMPER, HALEventType.COMMUNICATION_LOST,
                           HALEventType.COMMUNICATION_RESTORED, HALEventType.SYSTEM_STARTUP,
                           HALEventType.SYSTEM_SHUTDOWN):
            device_type = AmbientDeviceType.PANEL
        elif event_type == HALEventType.REX_ACTIVATED:
            device_type = AmbientDeviceType.REX
        else:
            device_type = AmbientDeviceType.DOOR

        now = int(time.time())

        return AmbientEvent(
            sourceSystemUid=self.source_system_uid,
            deviceUid=device_uuid(door_id),
            deviceName=door_name,
            deviceType=device_type,
            eventUid=event_uuid(event_id, timestamp),
            alarmName=alarm_name,
            alarmUid=alarm_uuid(event_type),
            eventOccuredAtTimestamp=timestamp,
            eventPublishedAtTimestamp=now,
            personUid=person_uuid(card_number) if card_number else None,
            personFirstName=holder_first_name,
            personLastName=holder_last_name,
            accessItemKey=card_number,
        )

    def translate_door(self, door_id: int, door_name: str) -> AmbientDevice:
        """Translate a HAL door to Ambient.ai device"""
        return AmbientDevice(
            sourceSystemUid=self.source_system_uid,
            deviceUid=device_uuid(door_id),
            deviceName=door_name,
            deviceType=AmbientDeviceType.READER,
        )

    def translate_cardholder(
        self,
        card_number: str,
        first_name: str,
        last_name: str,
        email: Optional[str] = None,
        department: Optional[str] = None,
        employee_id: Optional[str] = None,
        is_deleted: bool = False,
    ) -> tuple[AmbientPerson, AmbientAccessItem]:
        """Translate a HAL cardholder to Ambient.ai person + access item"""

        p_uid = person_uuid(card_number)

        person = AmbientPerson(
            sourceSystemUid=self.source_system_uid,
            personUid=p_uid,
            firstName=first_name,
            lastName=last_name,
            email=email,
            department=department,
            employeeId=employee_id,
            isDeleted=is_deleted,
        )

        access_item = AmbientAccessItem(
            sourceSystemUid=self.source_system_uid,
            accessItemUid=item_uuid(card_number),
            accessItemKey=card_number,
            personUid=p_uid,
            isActive=not is_deleted,
            isDeleted=is_deleted,
        )

        return person, access_item

    def translate_alarm_types(self) -> List[AmbientAlarm]:
        """Generate all alarm type entities for initial sync"""
        alarms = []
        for event_type, alarm_name in HAL_TO_AMBIENT_ALARM.items():
            alarms.append(AmbientAlarm(
                sourceSystemUid=self.source_system_uid,
                alarmUid=alarm_uuid(event_type),
                alarmName=alarm_name,
            ))
        return alarms


# =============================================================================
# Ambient.ai API Client
# =============================================================================

class AmbientClient:
    """HTTP client for Ambient.ai Event Ingestion API"""

    def __init__(self, api_key: str = None, base_url: str = None):
        self.api_key = api_key or AMBIENT_API_KEY
        self.base_url = base_url or AMBIENT_API_BASE
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session"""
        if self._session is None or self._session.closed:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            }
            self._session = aiohttp.ClientSession(headers=headers)
        return self._session

    async def close(self):
        """Close the HTTP session"""
        if self._session and not self._session.closed:
            await self._session.close()

    async def _post(self, endpoint: str, data: List[Dict]) -> Dict[str, Any]:
        """POST data to Ambient.ai API"""
        if not self.api_key:
            logger.warning("No Ambient.ai API key configured, skipping POST")
            return {"status": "skipped", "reason": "no_api_key"}

        session = await self._get_session()
        url = f"{self.base_url}/{endpoint}"

        try:
            async with session.post(url, json=data) as response:
                if response.status == 200:
                    return {"status": "success", "count": len(data)}
                else:
                    error_text = await response.text()
                    logger.error(f"Ambient.ai API error {response.status}: {error_text}")
                    return {"status": "error", "code": response.status, "message": error_text}
        except Exception as e:
            logger.exception(f"Failed to POST to Ambient.ai: {e}")
            return {"status": "error", "message": str(e)}

    async def send_events(self, events: List[AmbientEvent]) -> Dict[str, Any]:
        """Send events to Ambient.ai"""
        data = [e.to_dict() for e in events]
        return await self._post("event", data)

    async def sync_devices(self, devices: List[AmbientDevice]) -> Dict[str, Any]:
        """Sync devices to Ambient.ai"""
        data = [d.to_dict() for d in devices]
        return await self._post("device", data)

    async def sync_persons(self, persons: List[AmbientPerson]) -> Dict[str, Any]:
        """Sync persons to Ambient.ai"""
        data = [p.to_dict() for p in persons]
        return await self._post("person", data)

    async def sync_access_items(self, items: List[AmbientAccessItem]) -> Dict[str, Any]:
        """Sync access items to Ambient.ai"""
        data = [i.to_dict() for i in items]
        return await self._post("item", data)

    async def sync_alarms(self, alarms: List[AmbientAlarm]) -> Dict[str, Any]:
        """Sync alarm types to Ambient.ai"""
        data = [a.to_dict() for a in alarms]
        return await self._post("alarm", data)


# =============================================================================
# Event Export Daemon
# =============================================================================

class EventExportDaemon:
    """
    Asynchronous daemon that exports HAL events to Ambient.ai in real-time.
    Ensures events are sent within 2 seconds of occurrence.
    """

    def __init__(self, translator: AmbientTranslator = None, client: AmbientClient = None):
        self.translator = translator or AmbientTranslator()
        self.client = client or AmbientClient()
        self._queue: asyncio.Queue = asyncio.Queue(maxsize=EVENT_QUEUE_MAX_SIZE)
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._stats = {
            "events_queued": 0,
            "events_sent": 0,
            "events_failed": 0,
            "events_dropped": 0,
            "last_send_time": None,
            "last_error": None,
        }

    @property
    def stats(self) -> Dict[str, Any]:
        """Get export statistics"""
        return self._stats.copy()

    def queue_event(
        self,
        event_id: int,
        event_type: int,
        door_id: int,
        door_name: str,
        timestamp: int,
        card_number: Optional[str] = None,
        holder_first_name: Optional[str] = None,
        holder_last_name: Optional[str] = None,
    ) -> bool:
        """
        Queue an event for export to Ambient.ai.
        Returns True if queued successfully, False if queue is full.
        """
        # Check event age
        now = int(time.time())
        if now - timestamp > MAX_EVENT_AGE_SECONDS:
            logger.warning(f"Dropping stale event {event_id} (age: {now - timestamp}s)")
            self._stats["events_dropped"] += 1
            return False

        event = self.translator.translate_event(
            event_id=event_id,
            event_type=event_type,
            door_id=door_id,
            door_name=door_name,
            timestamp=timestamp,
            card_number=card_number,
            holder_first_name=holder_first_name,
            holder_last_name=holder_last_name,
        )

        try:
            self._queue.put_nowait(event)
            self._stats["events_queued"] += 1
            return True
        except asyncio.QueueFull:
            logger.error("Event queue full, dropping event")
            self._stats["events_dropped"] += 1
            return False

    async def _export_loop(self):
        """Main export loop - sends batches to Ambient.ai"""
        while self._running:
            batch: List[AmbientEvent] = []

            # Collect batch
            try:
                # Wait for at least one event
                event = await asyncio.wait_for(
                    self._queue.get(),
                    timeout=EVENT_SEND_INTERVAL
                )
                batch.append(event)

                # Grab more if available (up to batch size)
                while len(batch) < EVENT_BATCH_SIZE:
                    try:
                        event = self._queue.get_nowait()
                        batch.append(event)
                    except asyncio.QueueEmpty:
                        break

            except asyncio.TimeoutError:
                # No events, continue loop
                continue

            # Send batch
            if batch:
                result = await self.client.send_events(batch)
                self._stats["last_send_time"] = datetime.now().isoformat()

                if result.get("status") == "success":
                    self._stats["events_sent"] += len(batch)
                    logger.debug(f"Sent {len(batch)} events to Ambient.ai")
                elif result.get("status") == "skipped":
                    logger.debug("Ambient.ai export skipped (no API key)")
                else:
                    self._stats["events_failed"] += len(batch)
                    self._stats["last_error"] = result.get("message")
                    logger.error(f"Failed to send events: {result}")

    async def start(self):
        """Start the export daemon"""
        if self._running:
            return

        self._running = True
        self._task = asyncio.create_task(self._export_loop())
        logger.info("Ambient.ai event export daemon started")

    async def stop(self):
        """Stop the export daemon"""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        await self.client.close()
        logger.info("Ambient.ai event export daemon stopped")


# =============================================================================
# Entity Sync Manager
# =============================================================================

class EntitySyncManager:
    """
    Manages initial and differential entity synchronization with Ambient.ai.
    Handles full sync on startup and incremental updates during operation.
    """

    def __init__(self, translator: AmbientTranslator = None, client: AmbientClient = None):
        self.translator = translator or AmbientTranslator()
        self.client = client or AmbientClient()
        self._last_sync: Optional[datetime] = None
        self._sync_stats = {
            "devices_synced": 0,
            "persons_synced": 0,
            "items_synced": 0,
            "alarms_synced": 0,
            "last_full_sync": None,
            "last_error": None,
        }

    @property
    def stats(self) -> Dict[str, Any]:
        """Get sync statistics"""
        return self._sync_stats.copy()

    async def full_sync(
        self,
        doors: List[Dict[str, Any]],
        cardholders: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Perform full entity synchronization with Ambient.ai.
        Should be called on system startup.
        """
        results = {}

        # Sync alarm types first
        alarms = self.translator.translate_alarm_types()
        result = await self.client.sync_alarms(alarms)
        results["alarms"] = result
        if result.get("status") == "success":
            self._sync_stats["alarms_synced"] = len(alarms)

        # Sync devices (doors/readers)
        devices = []
        for door in doors:
            device = self.translator.translate_door(
                door_id=door.get("door_id"),
                door_name=door.get("name", f"Door {door.get('door_id')}"),
            )
            devices.append(device)

        if devices:
            result = await self.client.sync_devices(devices)
            results["devices"] = result
            if result.get("status") == "success":
                self._sync_stats["devices_synced"] = len(devices)

        # Sync persons and access items
        persons = []
        access_items = []

        for holder in cardholders:
            person, item = self.translator.translate_cardholder(
                card_number=holder.get("card_number"),
                first_name=holder.get("first_name", ""),
                last_name=holder.get("last_name", ""),
                email=holder.get("email"),
                department=holder.get("department"),
                employee_id=holder.get("employee_id"),
                is_deleted=not holder.get("is_active", True),
            )
            persons.append(person)
            access_items.append(item)

        if persons:
            result = await self.client.sync_persons(persons)
            results["persons"] = result
            if result.get("status") == "success":
                self._sync_stats["persons_synced"] = len(persons)

        if access_items:
            result = await self.client.sync_access_items(access_items)
            results["access_items"] = result
            if result.get("status") == "success":
                self._sync_stats["items_synced"] = len(access_items)

        self._sync_stats["last_full_sync"] = datetime.now().isoformat()
        self._last_sync = datetime.now()

        logger.info(f"Full Ambient.ai sync completed: {results}")
        return results

    async def sync_device(self, door_id: int, door_name: str, is_deleted: bool = False):
        """Sync a single device (incremental update)"""
        device = self.translator.translate_door(door_id, door_name)
        device.isDeleted = is_deleted
        return await self.client.sync_devices([device])

    async def sync_cardholder(
        self,
        card_number: str,
        first_name: str,
        last_name: str,
        email: Optional[str] = None,
        department: Optional[str] = None,
        employee_id: Optional[str] = None,
        is_deleted: bool = False,
    ):
        """Sync a single cardholder (incremental update)"""
        person, item = self.translator.translate_cardholder(
            card_number=card_number,
            first_name=first_name,
            last_name=last_name,
            email=email,
            department=department,
            employee_id=employee_id,
            is_deleted=is_deleted,
        )

        results = {}
        results["person"] = await self.client.sync_persons([person])
        results["item"] = await self.client.sync_access_items([item])
        return results


# =============================================================================
# Global Instances (for use by Bifrost API)
# =============================================================================

# These are initialized when the module is imported
_translator: Optional[AmbientTranslator] = None
_client: Optional[AmbientClient] = None
_export_daemon: Optional[EventExportDaemon] = None
_sync_manager: Optional[EntitySyncManager] = None


def get_translator() -> AmbientTranslator:
    """Get the global translator instance"""
    global _translator
    if _translator is None:
        _translator = AmbientTranslator()
    return _translator


def get_client() -> AmbientClient:
    """Get the global client instance"""
    global _client
    if _client is None:
        _client = AmbientClient()
    return _client


def get_export_daemon() -> EventExportDaemon:
    """Get the global export daemon instance"""
    global _export_daemon
    if _export_daemon is None:
        _export_daemon = EventExportDaemon(get_translator(), get_client())
    return _export_daemon


def get_sync_manager() -> EntitySyncManager:
    """Get the global sync manager instance"""
    global _sync_manager
    if _sync_manager is None:
        _sync_manager = EntitySyncManager(get_translator(), get_client())
    return _sync_manager


# =============================================================================
# Convenience Functions
# =============================================================================

async def queue_hal_event(
    event_id: int,
    event_type: int,
    door_id: int,
    door_name: str,
    timestamp: int,
    card_number: Optional[str] = None,
    holder_first_name: Optional[str] = None,
    holder_last_name: Optional[str] = None,
) -> bool:
    """Queue a HAL event for export to Ambient.ai"""
    daemon = get_export_daemon()
    return daemon.queue_event(
        event_id=event_id,
        event_type=event_type,
        door_id=door_id,
        door_name=door_name,
        timestamp=timestamp,
        card_number=card_number,
        holder_first_name=holder_first_name,
        holder_last_name=holder_last_name,
    )


async def start_ambient_integration():
    """Start the Ambient.ai integration (call on app startup)"""
    daemon = get_export_daemon()
    await daemon.start()


async def stop_ambient_integration():
    """Stop the Ambient.ai integration (call on app shutdown)"""
    daemon = get_export_daemon()
    await daemon.stop()


async def perform_full_sync(doors: List[Dict], cardholders: List[Dict]):
    """Perform full entity sync with Ambient.ai"""
    manager = get_sync_manager()
    return await manager.full_sync(doors, cardholders)


def get_integration_status() -> Dict[str, Any]:
    """Get status of Ambient.ai integration"""
    daemon = get_export_daemon()
    manager = get_sync_manager()

    return {
        "enabled": bool(AMBIENT_API_KEY),
        "source_system_uid": get_translator().source_system_uid,
        "api_base": AMBIENT_API_BASE,
        "export_daemon": {
            "running": daemon._running,
            "queue_size": daemon._queue.qsize(),
            **daemon.stats,
        },
        "sync": manager.stats,
    }
