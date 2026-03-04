#!/usr/bin/env python3
"""
Ambient.ai Event Export Daemon

This daemon monitors the export queue and sends events to the Ambient.ai
Generic Cloud Event Ingestion API.

Endpoints:
    - Events: POST https://pacs-ingestion.ambient.ai/v1/api/event
    - Device Sync: POST https://pacs-ingestion.ambient.ai/v1/api/device
    - Person Sync: POST https://pacs-ingestion.ambient.ai/v1/api/person
    - Access Item Sync: POST https://pacs-ingestion.ambient.ai/v1/api/item
    - Alarm Sync: POST https://pacs-ingestion.ambient.ai/v1/api/alarm

Configuration:
    Environment variables:
    - AMBIENT_API_KEY: API key for Ambient.ai authentication
    - AMBIENT_API_URL: Base URL (default: https://pacs-ingestion.ambient.ai/v1/api)
    - AMBIENT_BATCH_SIZE: Events per batch (default: 100)
    - AMBIENT_POLL_INTERVAL: Seconds between polls (default: 5)
    - AMBIENT_MAX_RETRIES: Max retry attempts (default: 3)
    - AMBIENT_RETRY_DELAY: Base delay for exponential backoff (default: 2)
    - HAL_DATABASE_PATH: Path to HAL database
"""

import os
import sys
import time
import json
import signal
import logging
import argparse
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum, auto

import httpx

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from python.hal_bindings import HALInterface, HALMode

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('/var/log/aether/ambient_export.log', mode='a')
    ] if os.path.exists('/var/log/aether') else [logging.StreamHandler()]
)
logger = logging.getLogger('ambient_export')


class ExportStatus(Enum):
    """Export queue item status"""
    PENDING = 'pending'
    PROCESSING = 'processing'
    COMPLETED = 'completed'
    FAILED = 'failed'
    RETRY = 'retry'


class AmbientApiClient:
    """Client for Ambient.ai PACS Ingestion API"""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://pacs-ingestion.ambient.ai/v1/api",
        timeout: float = 30.0
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client"""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=self.timeout,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "User-Agent": "Aether-Access/2.0"
                }
            )
        return self._client

    async def close(self):
        """Close the HTTP client"""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def send_event(self, event: Dict) -> Dict:
        """
        Send a single event to Ambient.ai

        Args:
            event: Event data formatted for Ambient.ai

        Returns:
            Response from API

        Raises:
            httpx.HTTPError: On network/HTTP errors
        """
        client = await self._get_client()
        response = await client.post(
            f"{self.base_url}/event",
            json=event
        )
        response.raise_for_status()
        return response.json() if response.content else {"status": "ok"}

    async def send_events_batch(self, events: List[Dict]) -> Dict:
        """
        Send multiple events to Ambient.ai

        Args:
            events: List of event data

        Returns:
            Response summary
        """
        results = {
            "sent": 0,
            "failed": 0,
            "errors": []
        }

        for event in events:
            try:
                await self.send_event(event)
                results["sent"] += 1
            except httpx.HTTPStatusError as e:
                results["failed"] += 1
                results["errors"].append({
                    "event_id": event.get("eventUid", "unknown"),
                    "error": str(e),
                    "status_code": e.response.status_code
                })
            except Exception as e:
                results["failed"] += 1
                results["errors"].append({
                    "event_id": event.get("eventUid", "unknown"),
                    "error": str(e)
                })

        return results

    async def sync_devices(self, devices: List[Dict]) -> Dict:
        """
        Sync device entities to Ambient.ai

        Args:
            devices: List of device data

        Returns:
            Response from API
        """
        client = await self._get_client()
        response = await client.post(
            f"{self.base_url}/device",
            json={"devices": devices}
        )
        response.raise_for_status()
        return response.json() if response.content else {"status": "ok"}

    async def sync_persons(self, persons: List[Dict]) -> Dict:
        """
        Sync person entities to Ambient.ai

        Args:
            persons: List of person data

        Returns:
            Response from API
        """
        client = await self._get_client()
        response = await client.post(
            f"{self.base_url}/person",
            json={"persons": persons}
        )
        response.raise_for_status()
        return response.json() if response.content else {"status": "ok"}

    async def sync_access_items(self, items: List[Dict]) -> Dict:
        """
        Sync access item (cards) to Ambient.ai

        Args:
            items: List of access item data

        Returns:
            Response from API
        """
        client = await self._get_client()
        response = await client.post(
            f"{self.base_url}/item",
            json={"items": items}
        )
        response.raise_for_status()
        return response.json() if response.content else {"status": "ok"}

    async def sync_alarms(self, alarms: List[Dict]) -> Dict:
        """
        Sync alarm definitions to Ambient.ai

        Args:
            alarms: List of alarm definition data

        Returns:
            Response from API
        """
        client = await self._get_client()
        response = await client.post(
            f"{self.base_url}/alarm",
            json={"alarms": alarms}
        )
        response.raise_for_status()
        return response.json() if response.content else {"status": "ok"}

    async def health_check(self) -> bool:
        """
        Check if Ambient.ai API is reachable

        Returns:
            True if API is healthy
        """
        try:
            client = await self._get_client()
            response = await client.get(f"{self.base_url}/health")
            return response.status_code == 200
        except Exception:
            return False


class AmbientExportDaemon:
    """
    Daemon that exports HAL events to Ambient.ai

    Features:
    - Polls export queue for pending events
    - Sends events to Ambient.ai API
    - Handles retries with exponential backoff
    - Performs initial entity sync on startup
    - Graceful shutdown handling
    """

    def __init__(
        self,
        hal: HALInterface,
        api_client: AmbientApiClient,
        batch_size: int = 100,
        poll_interval: float = 5.0,
        max_retries: int = 3,
        retry_delay: float = 2.0
    ):
        self.hal = hal
        self.api_client = api_client
        self.batch_size = batch_size
        self.poll_interval = poll_interval
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self._running = False
        self._shutdown_event = asyncio.Event()

        # Statistics
        self.stats = {
            "started_at": None,
            "events_sent": 0,
            "events_failed": 0,
            "batches_processed": 0,
            "last_export": None,
            "api_errors": 0
        }

    async def start(self):
        """Start the export daemon"""
        logger.info("Starting Ambient.ai Export Daemon")
        self._running = True
        self.stats["started_at"] = datetime.now().isoformat()

        # Perform initial entity sync
        await self._perform_initial_sync()

        # Start the main export loop
        await self._export_loop()

    async def stop(self):
        """Stop the export daemon gracefully"""
        logger.info("Stopping Ambient.ai Export Daemon")
        self._running = False
        self._shutdown_event.set()
        await self.api_client.close()
        logger.info("Export daemon stopped")

    async def _perform_initial_sync(self):
        """Perform initial entity sync with Ambient.ai"""
        logger.info("Performing initial entity sync with Ambient.ai")

        try:
            # Sync devices (doors/readers)
            devices = self.hal.get_all_devices_for_sync()
            if devices:
                result = await self.api_client.sync_devices(devices)
                logger.info(f"Synced {len(devices)} devices: {result}")

            # Sync persons
            persons = self.hal.get_all_persons_for_sync()
            if persons:
                result = await self.api_client.sync_persons(persons)
                logger.info(f"Synced {len(persons)} persons: {result}")

            # Sync access items (cards)
            items = self.hal.get_all_access_items_for_sync()
            if items:
                result = await self.api_client.sync_access_items(items)
                logger.info(f"Synced {len(items)} access items: {result}")

            # Sync alarm definitions
            alarms = self.hal.get_all_alarms_for_sync()
            if alarms:
                result = await self.api_client.sync_alarms(alarms)
                logger.info(f"Synced {len(alarms)} alarm definitions: {result}")

            logger.info("Initial entity sync completed successfully")

        except Exception as e:
            logger.error(f"Initial entity sync failed: {e}")
            # Continue anyway - events can still be exported

    async def _export_loop(self):
        """Main export loop"""
        logger.info("Starting export loop")

        while self._running:
            try:
                # Get pending events from queue
                pending = self._get_pending_events()

                if pending:
                    logger.debug(f"Processing {len(pending)} pending events")
                    await self._process_events(pending)

                # Wait for next poll or shutdown
                try:
                    await asyncio.wait_for(
                        self._shutdown_event.wait(),
                        timeout=self.poll_interval
                    )
                    # If we get here, shutdown was requested
                    break
                except asyncio.TimeoutError:
                    # Normal timeout, continue loop
                    pass

            except Exception as e:
                logger.error(f"Error in export loop: {e}")
                self.stats["api_errors"] += 1
                # Back off on errors
                await asyncio.sleep(self.poll_interval * 2)

    def _get_pending_events(self) -> List[Dict]:
        """Get pending events from export queue"""
        try:
            with self.hal._get_db_connection() as conn:
                cursor = conn.cursor()

                # Get pending or retry events
                cursor.execute("""
                    SELECT eq.id, eq.event_id, eq.payload, eq.attempts,
                           eq.last_attempt, eq.status, eq.error_message
                    FROM export_queue eq
                    WHERE eq.status IN ('pending', 'retry')
                    AND eq.attempts < ?
                    ORDER BY eq.created_at ASC
                    LIMIT ?
                """, (self.max_retries, self.batch_size))

                rows = cursor.fetchall()
                events = []

                for row in rows:
                    events.append({
                        "queue_id": row[0],
                        "event_id": row[1],
                        "payload": json.loads(row[2]),
                        "attempts": row[3],
                        "last_attempt": row[4],
                        "status": row[5],
                        "error_message": row[6]
                    })

                # Mark as processing
                if events:
                    queue_ids = [e["queue_id"] for e in events]
                    placeholders = ",".join("?" * len(queue_ids))
                    cursor.execute(f"""
                        UPDATE export_queue
                        SET status = 'processing'
                        WHERE id IN ({placeholders})
                    """, queue_ids)
                    conn.commit()

                return events

        except Exception as e:
            logger.error(f"Error getting pending events: {e}")
            return []

    async def _process_events(self, events: List[Dict]):
        """Process a batch of events"""
        for event_data in events:
            queue_id = event_data["queue_id"]
            event_id = event_data["event_id"]
            payload = event_data["payload"]
            attempts = event_data["attempts"] + 1

            try:
                # Send to Ambient.ai
                await self.api_client.send_event(payload)

                # Mark as completed
                self._update_queue_status(
                    queue_id=queue_id,
                    event_id=event_id,
                    status=ExportStatus.COMPLETED,
                    attempts=attempts
                )

                self.stats["events_sent"] += 1
                self.stats["last_export"] = datetime.now().isoformat()
                logger.debug(f"Event {event_id} exported successfully")

            except httpx.HTTPStatusError as e:
                error_msg = f"HTTP {e.response.status_code}: {e.response.text[:200]}"
                logger.warning(f"Event {event_id} export failed: {error_msg}")

                # Check if retryable
                if e.response.status_code >= 500 and attempts < self.max_retries:
                    status = ExportStatus.RETRY
                else:
                    status = ExportStatus.FAILED
                    self.stats["events_failed"] += 1

                self._update_queue_status(
                    queue_id=queue_id,
                    event_id=event_id,
                    status=status,
                    attempts=attempts,
                    error=error_msg
                )

            except Exception as e:
                error_msg = str(e)
                logger.warning(f"Event {event_id} export error: {error_msg}")

                if attempts < self.max_retries:
                    status = ExportStatus.RETRY
                else:
                    status = ExportStatus.FAILED
                    self.stats["events_failed"] += 1

                self._update_queue_status(
                    queue_id=queue_id,
                    event_id=event_id,
                    status=status,
                    attempts=attempts,
                    error=error_msg
                )

        self.stats["batches_processed"] += 1

    def _update_queue_status(
        self,
        queue_id: int,
        event_id: str,
        status: ExportStatus,
        attempts: int,
        error: str = ""
    ):
        """Update export queue item status"""
        try:
            with self.hal._get_db_connection() as conn:
                cursor = conn.cursor()
                now = int(time.time())

                cursor.execute("""
                    UPDATE export_queue
                    SET status = ?, attempts = ?, last_attempt = ?, error_message = ?
                    WHERE id = ?
                """, (status.value, attempts, now, error, queue_id))

                # If completed, also update the events table
                if status == ExportStatus.COMPLETED:
                    cursor.execute("""
                        UPDATE events
                        SET exported = 1, export_timestamp = ?
                        WHERE event_id = ?
                    """, (now, event_id))

                conn.commit()

        except Exception as e:
            logger.error(f"Error updating queue status: {e}")

    def get_stats(self) -> Dict:
        """Get daemon statistics"""
        return {
            **self.stats,
            "running": self._running,
            "pending_count": self._get_pending_count()
        }

    def _get_pending_count(self) -> int:
        """Get count of pending events in queue"""
        try:
            with self.hal._get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT COUNT(*) FROM export_queue
                    WHERE status IN ('pending', 'retry')
                """)
                return cursor.fetchone()[0]
        except Exception:
            return -1


async def run_daemon(
    hal: HALInterface,
    api_key: str,
    base_url: str,
    batch_size: int,
    poll_interval: float,
    max_retries: int,
    retry_delay: float
):
    """Run the export daemon"""

    # Create API client
    api_client = AmbientApiClient(
        api_key=api_key,
        base_url=base_url
    )

    # Create daemon
    daemon = AmbientExportDaemon(
        hal=hal,
        api_client=api_client,
        batch_size=batch_size,
        poll_interval=poll_interval,
        max_retries=max_retries,
        retry_delay=retry_delay
    )

    # Set up signal handlers
    loop = asyncio.get_running_loop()

    def handle_signal():
        logger.info("Received shutdown signal")
        asyncio.create_task(daemon.stop())

    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, handle_signal)

    # Run daemon
    try:
        await daemon.start()
    finally:
        await daemon.stop()

    # Log final stats
    logger.info(f"Final statistics: {daemon.get_stats()}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Ambient.ai Event Export Daemon"
    )
    parser.add_argument(
        "--api-key",
        default=os.environ.get("AMBIENT_API_KEY", ""),
        help="Ambient.ai API key"
    )
    parser.add_argument(
        "--api-url",
        default=os.environ.get(
            "AMBIENT_API_URL",
            "https://pacs-ingestion.ambient.ai/v1/api"
        ),
        help="Ambient.ai API base URL"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=int(os.environ.get("AMBIENT_BATCH_SIZE", "100")),
        help="Events per batch"
    )
    parser.add_argument(
        "--poll-interval",
        type=float,
        default=float(os.environ.get("AMBIENT_POLL_INTERVAL", "5")),
        help="Seconds between polls"
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=int(os.environ.get("AMBIENT_MAX_RETRIES", "3")),
        help="Maximum retry attempts"
    )
    parser.add_argument(
        "--retry-delay",
        type=float,
        default=float(os.environ.get("AMBIENT_RETRY_DELAY", "2")),
        help="Base delay for exponential backoff"
    )
    parser.add_argument(
        "--db-path",
        default=os.environ.get(
            "HAL_DATABASE_PATH",
            "/var/lib/aether/hal_database.db"
        ),
        help="Path to HAL database"
    )
    parser.add_argument(
        "--log-level",
        default=os.environ.get("HAL_LOG_LEVEL", "INFO"),
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level"
    )

    args = parser.parse_args()

    # Validate API key
    if not args.api_key:
        logger.error("AMBIENT_API_KEY is required")
        sys.exit(1)

    # Set log level
    logging.getLogger().setLevel(getattr(logging, args.log_level))

    logger.info("=" * 60)
    logger.info("Ambient.ai Event Export Daemon")
    logger.info("=" * 60)
    logger.info(f"API URL: {args.api_url}")
    logger.info(f"Database: {args.db_path}")
    logger.info(f"Batch size: {args.batch_size}")
    logger.info(f"Poll interval: {args.poll_interval}s")
    logger.info(f"Max retries: {args.max_retries}")
    logger.info("=" * 60)

    # Initialize HAL
    try:
        hal = HALInterface(
            db_path=args.db_path,
            mode=HALMode.SIMULATION  # Always use simulation for export daemon
        )
        hal.initialize()
    except Exception as e:
        logger.error(f"Failed to initialize HAL: {e}")
        sys.exit(1)

    # Run daemon
    try:
        asyncio.run(run_daemon(
            hal=hal,
            api_key=args.api_key,
            base_url=args.api_url,
            batch_size=args.batch_size,
            poll_interval=args.poll_interval,
            max_retries=args.max_retries,
            retry_delay=args.retry_delay
        ))
    except KeyboardInterrupt:
        logger.info("Shutdown requested")
    finally:
        hal.shutdown()


if __name__ == "__main__":
    main()
