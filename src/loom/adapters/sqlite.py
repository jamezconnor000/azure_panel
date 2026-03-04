"""
Loom SQLite Adapter
Database adapter for SQLite (Bifrost local cache).
"""

import logging
import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class SQLiteAdapter:
    """
    SQLite adapter for Loom translation.

    Used by Aether Bifrost for local caching and offline operation.
    """

    def __init__(self, db_path: str = "/data/bifrost_cache.db"):
        self.db_path = db_path
        self._conn: Optional[sqlite3.Connection] = None

    def connect(self):
        """Establish database connection."""
        try:
            self._conn = sqlite3.connect(
                self.db_path,
                check_same_thread=False,
                isolation_level=None,  # Autocommit mode
            )
            self._conn.row_factory = sqlite3.Row
            logger.info(f"Connected to SQLite at {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to connect to SQLite: {e}")
            raise

    def disconnect(self):
        """Close database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None

    def is_connected(self) -> bool:
        """Check if connected."""
        return self._conn is not None

    def insert(self, table: str, data: Dict[str, Any]) -> int:
        """
        Insert a record (upsert).

        Args:
            table: Table name
            data: Record data

        Returns:
            Inserted record ID
        """
        if not self._conn:
            logger.warning("Not connected, returning mock ID")
            return data.get("id", 0)

        columns = list(data.keys())
        values = [self._serialize_value(data[c]) for c in columns]
        placeholders = ", ".join(["?"] * len(columns))

        sql = f"""
            INSERT OR REPLACE INTO {table} ({', '.join(columns)})
            VALUES ({placeholders})
        """

        cursor = self._conn.execute(sql, values)
        return cursor.lastrowid or data.get("id", 0)

    def update(self, table: str, id: int, data: Dict[str, Any]) -> bool:
        """
        Update a record by ID.

        Args:
            table: Table name
            id: Record ID
            data: Updated fields

        Returns:
            True if updated
        """
        if not self._conn:
            return True

        data["updated_at"] = datetime.utcnow().isoformat()
        set_clause = ", ".join(f"{k} = ?" for k in data.keys())
        values = [self._serialize_value(v) for v in data.values()] + [id]

        sql = f"UPDATE {table} SET {set_clause} WHERE id = ?"
        cursor = self._conn.execute(sql, values)
        return cursor.rowcount > 0

    def delete(self, table: str, id: int) -> bool:
        """
        Delete a record by ID.

        Args:
            table: Table name
            id: Record ID

        Returns:
            True if deleted
        """
        if not self._conn:
            return True

        sql = f"DELETE FROM {table} WHERE id = ?"
        cursor = self._conn.execute(sql, [id])
        return cursor.rowcount > 0

    def get(self, table: str, id: int) -> Optional[Dict[str, Any]]:
        """
        Get a single record by ID.

        Args:
            table: Table name
            id: Record ID

        Returns:
            Record dict or None
        """
        if not self._conn:
            return None

        sql = f"SELECT * FROM {table} WHERE id = ?"
        cursor = self._conn.execute(sql, [id])
        row = cursor.fetchone()
        if row:
            return self._row_to_dict(row)
        return None

    def query(
        self,
        table: str,
        filters: Optional[Dict] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        Query records with optional filters.

        Args:
            table: Table name
            filters: Optional filter conditions
            limit: Max records to return
            offset: Records to skip

        Returns:
            List of record dicts
        """
        if not self._conn:
            return []

        sql = f"SELECT * FROM {table}"
        values = []

        if filters:
            conditions = []
            for key, value in filters.items():
                conditions.append(f"{key} = ?")
                values.append(self._serialize_value(value))
            sql += " WHERE " + " AND ".join(conditions)

        sql += f" ORDER BY id LIMIT ? OFFSET ?"
        values.extend([limit, offset])

        cursor = self._conn.execute(sql, values)
        return [self._row_to_dict(row) for row in cursor.fetchall()]

    def count(self, table: str, filters: Optional[Dict] = None) -> int:
        """
        Count records matching filters.

        Args:
            table: Table name
            filters: Optional filter conditions

        Returns:
            Record count
        """
        if not self._conn:
            return 0

        sql = f"SELECT COUNT(*) FROM {table}"
        values = []

        if filters:
            conditions = []
            for key, value in filters.items():
                conditions.append(f"{key} = ?")
                values.append(self._serialize_value(value))
            sql += " WHERE " + " AND ".join(conditions)

        cursor = self._conn.execute(sql, values)
        return cursor.fetchone()[0]

    def get_modified_since(
        self,
        table: str,
        since: datetime,
    ) -> List[Dict[str, Any]]:
        """
        Get records modified since a timestamp.

        Args:
            table: Table name
            since: Timestamp

        Returns:
            List of modified records
        """
        if not self._conn:
            return []

        sql = f"SELECT * FROM {table} WHERE updated_at > ? ORDER BY updated_at"
        cursor = self._conn.execute(sql, [since.isoformat()])
        return [self._row_to_dict(row) for row in cursor.fetchall()]

    def create_tables(self):
        """Create required tables if they don't exist."""
        if not self._conn:
            return

        # Cardholders table
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS cardholders (
                id INTEGER PRIMARY KEY,
                badge_number TEXT UNIQUE NOT NULL,
                first_name TEXT,
                last_name TEXT,
                pin_code TEXT,
                active INTEGER DEFAULT 1,
                access_levels TEXT,
                activation_date TEXT,
                expiration_date TEXT,
                facility_code INTEGER,
                card_data BLOB,
                created_at TEXT,
                updated_at TEXT,
                external_id TEXT
            )
        """)

        # Access levels table
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS access_levels (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                doors TEXT,
                schedules TEXT,
                active INTEGER DEFAULT 1,
                priority INTEGER DEFAULT 100,
                external_id TEXT
            )
        """)

        # Doors table
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS doors (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                reader_address INTEGER NOT NULL,
                reader_type INTEGER DEFAULT 0,
                unlock_time INTEGER DEFAULT 5,
                held_open_time INTEGER DEFAULT 30,
                forced_open_enabled INTEGER DEFAULT 1,
                rex_enabled INTEGER DEFAULT 1,
                active INTEGER DEFAULT 1,
                state INTEGER DEFAULT 0,
                external_id TEXT
            )
        """)

        # Events table
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY,
                timestamp TEXT NOT NULL,
                event_type INTEGER NOT NULL,
                door_id INTEGER,
                cardholder_id INTEGER,
                badge_number TEXT,
                granted INTEGER,
                reason_code INTEGER,
                details TEXT,
                exported INTEGER DEFAULT 0,
                exported_at TEXT
            )
        """)

        # Create indexes
        self._conn.execute("CREATE INDEX IF NOT EXISTS idx_cardholders_badge ON cardholders(badge_number)")
        self._conn.execute("CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp)")
        self._conn.execute("CREATE INDEX IF NOT EXISTS idx_events_exported ON events(exported)")

        logger.info("SQLite tables created/verified")

    def _serialize_value(self, value: Any) -> Any:
        """Serialize a value for SQLite storage."""
        if isinstance(value, datetime):
            return value.isoformat()
        elif isinstance(value, (list, dict)):
            import json
            return json.dumps(value)
        elif isinstance(value, bool):
            return 1 if value else 0
        return value

    def _deserialize_value(self, value: Any, key: str) -> Any:
        """Deserialize a value from SQLite storage."""
        if value is None:
            return None

        # Try to parse JSON for array fields
        if key in ("access_levels", "doors", "schedules", "holidays"):
            if isinstance(value, str):
                try:
                    import json
                    return json.loads(value)
                except:
                    return value
        return value

    def _row_to_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        """Convert a Row to a dictionary with deserialization."""
        result = {}
        for key in row.keys():
            result[key] = self._deserialize_value(row[key], key)
        return result

    def execute_raw(self, sql: str, params: Optional[List] = None) -> List[Dict]:
        """Execute raw SQL query."""
        if not self._conn:
            return []

        cursor = self._conn.execute(sql, params or [])
        if cursor.description:
            return [self._row_to_dict(row) for row in cursor.fetchall()]
        return []
