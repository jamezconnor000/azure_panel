"""
Loom PostgreSQL Adapter
Database adapter for PostgreSQL (Saga local database).
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class PostgreSQLAdapter:
    """
    PostgreSQL adapter for Loom translation.

    Used by Aether Saga for local panel management.
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 5432,
        database: str = "aether_saga",
        user: str = "aether",
        password: str = "",
    ):
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self._conn = None

    def connect(self):
        """Establish database connection."""
        try:
            import psycopg2
            self._conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password,
            )
            logger.info(f"Connected to PostgreSQL at {self.host}:{self.port}")
        except ImportError:
            logger.warning("psycopg2 not available, using mock connection")
            self._conn = None
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
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
        Insert a record.

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
        values = [data[c] for c in columns]
        placeholders = ", ".join(["%s"] * len(columns))

        sql = f"""
            INSERT INTO {table} ({', '.join(columns)})
            VALUES ({placeholders})
            ON CONFLICT (id) DO UPDATE SET
                {', '.join(f'{c} = EXCLUDED.{c}' for c in columns if c != 'id')}
            RETURNING id
        """

        with self._conn.cursor() as cur:
            cur.execute(sql, values)
            result = cur.fetchone()
            self._conn.commit()
            return result[0] if result else 0

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

        data["updated_at"] = datetime.utcnow()
        set_clause = ", ".join(f"{k} = %s" for k in data.keys())
        values = list(data.values()) + [id]

        sql = f"UPDATE {table} SET {set_clause} WHERE id = %s"

        with self._conn.cursor() as cur:
            cur.execute(sql, values)
            self._conn.commit()
            return cur.rowcount > 0

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

        sql = f"DELETE FROM {table} WHERE id = %s"

        with self._conn.cursor() as cur:
            cur.execute(sql, [id])
            self._conn.commit()
            return cur.rowcount > 0

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

        sql = f"SELECT * FROM {table} WHERE id = %s"

        with self._conn.cursor() as cur:
            cur.execute(sql, [id])
            row = cur.fetchone()
            if row:
                columns = [desc[0] for desc in cur.description]
                return dict(zip(columns, row))
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
                conditions.append(f"{key} = %s")
                values.append(value)
            sql += " WHERE " + " AND ".join(conditions)

        sql += f" ORDER BY id LIMIT %s OFFSET %s"
        values.extend([limit, offset])

        with self._conn.cursor() as cur:
            cur.execute(sql, values)
            columns = [desc[0] for desc in cur.description]
            return [dict(zip(columns, row)) for row in cur.fetchall()]

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
                conditions.append(f"{key} = %s")
                values.append(value)
            sql += " WHERE " + " AND ".join(conditions)

        with self._conn.cursor() as cur:
            cur.execute(sql, values)
            return cur.fetchone()[0]

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

        sql = f"SELECT * FROM {table} WHERE updated_at > %s ORDER BY updated_at"

        with self._conn.cursor() as cur:
            cur.execute(sql, [since])
            columns = [desc[0] for desc in cur.description]
            return [dict(zip(columns, row)) for row in cur.fetchall()]

    def execute_raw(self, sql: str, params: Optional[List] = None) -> List[Dict]:
        """Execute raw SQL query."""
        if not self._conn:
            return []

        with self._conn.cursor() as cur:
            cur.execute(sql, params or [])
            if cur.description:
                columns = [desc[0] for desc in cur.description]
                return [dict(zip(columns, row)) for row in cur.fetchall()]
            self._conn.commit()
            return []
