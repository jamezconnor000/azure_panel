"""
Loom Translation Engine
Bidirectional conversion between AetherDB and SQL databases.
"""

import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field

from .schema_registry import TableDef, get_schema, list_tables
from .tlv_codec import TLVCodec
from .errors import (
    TranslationError,
    TranslationErrorType,
    TranslationErrorLog,
    ErrorSeverity,
    Direction,
)

logger = logging.getLogger(__name__)


class SyncStatus(Enum):
    """Status of a sync operation."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


@dataclass
class SyncResult:
    """Result of a sync operation."""
    table: str
    direction: Direction
    status: SyncStatus
    records_processed: int = 0
    records_succeeded: int = 0
    records_failed: int = 0
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    errors: List[TranslationError] = field(default_factory=list)

    @property
    def duration(self) -> Optional[timedelta]:
        if self.completed_at:
            return self.completed_at - self.started_at
        return None


class DatabaseAdapter:
    """Base class for database adapters."""

    def insert(self, table: str, data: Dict[str, Any]) -> int:
        """Insert a record, return ID."""
        raise NotImplementedError

    def update(self, table: str, id: int, data: Dict[str, Any]) -> bool:
        """Update a record by ID."""
        raise NotImplementedError

    def delete(self, table: str, id: int) -> bool:
        """Delete a record by ID."""
        raise NotImplementedError

    def get(self, table: str, id: int) -> Optional[Dict[str, Any]]:
        """Get a single record by ID."""
        raise NotImplementedError

    def query(self, table: str, filters: Optional[Dict] = None,
              limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Query records with optional filters."""
        raise NotImplementedError

    def count(self, table: str, filters: Optional[Dict] = None) -> int:
        """Count records matching filters."""
        raise NotImplementedError

    def get_modified_since(self, table: str, since: datetime) -> List[Dict[str, Any]]:
        """Get records modified since a timestamp."""
        raise NotImplementedError


class AetherDBAdapter(DatabaseAdapter):
    """Adapter for AetherDB binary format."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.codec = TLVCodec()
        # TODO: Implement actual file I/O

    def insert(self, table: str, data: Dict[str, Any]) -> int:
        """Insert a record into AetherDB."""
        schema = get_schema(table)
        if not schema:
            raise ValueError(f"Unknown table: {table}")
        binary = self.codec.encode_record(schema, data)
        # TODO: Write to file
        return data.get("id", 0)

    def get(self, table: str, id: int) -> Optional[Dict[str, Any]]:
        """Get a record from AetherDB."""
        # TODO: Read from file
        return None


class LoomTranslator:
    """
    Main translation engine for Loom.

    Handles bidirectional conversion between AetherDB (binary)
    and SQL databases (PostgreSQL/SQLite).
    """

    def __init__(
        self,
        aetherdb: Optional[DatabaseAdapter] = None,
        sql_adapter: Optional[DatabaseAdapter] = None,
        error_log: Optional[TranslationErrorLog] = None,
    ):
        self.aetherdb = aetherdb
        self.sql_adapter = sql_adapter
        self.codec = TLVCodec()
        self.error_log = error_log or TranslationErrorLog()
        self._sync_callbacks: List[Callable[[SyncResult], None]] = []
        self._last_sync: Dict[str, datetime] = {}

    def register_sync_callback(self, callback: Callable[[SyncResult], None]):
        """Register a callback to be called after sync operations."""
        self._sync_callbacks.append(callback)

    def binary_to_dict(self, table: str, record: bytes) -> Dict[str, Any]:
        """
        Convert a binary TLV record to a dictionary.

        Args:
            table: Table name
            record: Binary TLV data

        Returns:
            Dictionary with field values
        """
        schema = get_schema(table)
        if not schema:
            raise ValueError(f"Unknown table: {table}")
        return self.codec.decode_record(schema, record)

    def dict_to_binary(self, table: str, data: Dict[str, Any]) -> bytes:
        """
        Convert a dictionary to binary TLV format.

        Args:
            table: Table name
            data: Dictionary with field values

        Returns:
            Binary TLV data
        """
        schema = get_schema(table)
        if not schema:
            raise ValueError(f"Unknown table: {table}")
        return self.codec.encode_record(schema, data)

    def sync_table(
        self,
        table: str,
        direction: Direction,
        since: Optional[datetime] = None,
        batch_size: int = 100,
    ) -> SyncResult:
        """
        Synchronize a table between AetherDB and SQL.

        Args:
            table: Table name to sync
            direction: Direction of sync
            since: Only sync records modified since this time
            batch_size: Number of records to process per batch

        Returns:
            SyncResult with details
        """
        result = SyncResult(table=table, direction=direction, status=SyncStatus.IN_PROGRESS)

        try:
            if direction == Direction.BINARY_TO_SQL:
                self._sync_binary_to_sql(table, since, batch_size, result)
            else:
                self._sync_sql_to_binary(table, since, batch_size, result)

            if result.records_failed == 0:
                result.status = SyncStatus.COMPLETED
            elif result.records_succeeded > 0:
                result.status = SyncStatus.PARTIAL
            else:
                result.status = SyncStatus.FAILED

        except Exception as e:
            result.status = SyncStatus.FAILED
            error = TranslationError(
                severity=ErrorSeverity.CRITICAL,
                error_type=TranslationErrorType.UNKNOWN,
                direction=direction,
                table=table,
                message=f"Sync failed: {str(e)}",
                root_cause=str(e),
            )
            result.errors.append(error)
            self.error_log.add(error)
            logger.error(f"Sync failed for {table}: {e}")

        result.completed_at = datetime.utcnow()
        self._last_sync[table] = result.completed_at

        # Notify callbacks
        for callback in self._sync_callbacks:
            try:
                callback(result)
            except Exception as e:
                logger.error(f"Sync callback failed: {e}")

        return result

    def _sync_binary_to_sql(
        self,
        table: str,
        since: Optional[datetime],
        batch_size: int,
        result: SyncResult,
    ):
        """Sync from AetherDB to SQL."""
        if not self.aetherdb or not self.sql_adapter:
            raise ValueError("Both adapters must be configured")

        # Get records from AetherDB
        if since:
            records = self.aetherdb.get_modified_since(table, since)
        else:
            records = self.aetherdb.query(table, limit=batch_size)

        result.records_processed = len(records)

        for record in records:
            try:
                # Record is already a dict from AetherDB
                self.sql_adapter.insert(table, record)
                result.records_succeeded += 1
            except Exception as e:
                error = TranslationError(
                    error_type=TranslationErrorType.CONSTRAINT_VIOLATION,
                    direction=Direction.BINARY_TO_SQL,
                    table=table,
                    record_id=record.get("id"),
                    message=f"Failed to insert into SQL: {str(e)}",
                    source_data=record,
                    root_cause=str(e),
                )
                result.errors.append(error)
                self.error_log.add(error)
                result.records_failed += 1

    def _sync_sql_to_binary(
        self,
        table: str,
        since: Optional[datetime],
        batch_size: int,
        result: SyncResult,
    ):
        """Sync from SQL to AetherDB."""
        if not self.aetherdb or not self.sql_adapter:
            raise ValueError("Both adapters must be configured")

        # Get records from SQL
        if since:
            records = self.sql_adapter.get_modified_since(table, since)
        else:
            records = self.sql_adapter.query(table, limit=batch_size)

        result.records_processed = len(records)

        for record in records:
            try:
                self.aetherdb.insert(table, record)
                result.records_succeeded += 1
            except TranslationError as e:
                result.errors.append(e)
                self.error_log.add(e)
                result.records_failed += 1
            except Exception as e:
                error = TranslationError(
                    error_type=TranslationErrorType.ENCODING_ERROR,
                    direction=Direction.SQL_TO_BINARY,
                    table=table,
                    record_id=record.get("id"),
                    message=f"Failed to encode to binary: {str(e)}",
                    source_data=record,
                    root_cause=str(e),
                )
                result.errors.append(error)
                self.error_log.add(error)
                result.records_failed += 1

    def full_sync(self, direction: Direction = Direction.BINARY_TO_SQL) -> List[SyncResult]:
        """
        Perform full sync of all tables.

        Args:
            direction: Direction of sync

        Returns:
            List of SyncResults for each table
        """
        results = []
        for table in list_tables():
            result = self.sync_table(table, direction)
            results.append(result)
        return results

    def get_sync_status(self, table: str) -> Dict[str, Any]:
        """Get sync status for a table."""
        last = self._last_sync.get(table)
        return {
            "table": table,
            "last_sync": last.isoformat() if last else None,
            "sync_lag_seconds": (datetime.utcnow() - last).total_seconds() if last else None,
            "recent_errors": len([e for e in self.error_log.errors if e.table == table]),
        }

    def get_all_sync_status(self) -> List[Dict[str, Any]]:
        """Get sync status for all tables."""
        return [self.get_sync_status(table) for table in list_tables()]
