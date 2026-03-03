#!/usr/bin/env python3
"""
AetherAccess Database Helper Module
Async SQLite database operations for user management and access control
"""

import aiosqlite
import sqlite3
from typing import Optional, List, Dict, Any
from datetime import datetime
import json
from contextlib import asynccontextmanager

# Database path
DB_PATH = "../../hal_sdk.db"


@asynccontextmanager
async def get_db():
    """Async context manager for database connections"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        yield db


# =============================================================================
# User Operations
# =============================================================================

async def create_user(username: str, email: str, password_hash: str,
                     first_name: str = None, last_name: str = None,
                     role: str = "user", phone: str = None) -> int:
    """Create a new user"""
    async with get_db() as db:
        cursor = await db.execute("""
            INSERT INTO users (username, email, password_hash, first_name, last_name, role, phone)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (username, email, password_hash, first_name, last_name, role, phone))
        await db.commit()
        return cursor.lastrowid


async def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    """Get user by ID"""
    async with get_db() as db:
        cursor = await db.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None


async def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    """Get user by username"""
    async with get_db() as db:
        cursor = await db.execute("SELECT * FROM users WHERE username = ?", (username,))
        row = await cursor.fetchone()
        return dict(row) if row else None


async def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Get user by email"""
    async with get_db() as db:
        cursor = await db.execute("SELECT * FROM users WHERE email = ?", (email,))
        row = await cursor.fetchone()
        return dict(row) if row else None


async def get_all_users(include_inactive: bool = False) -> List[Dict[str, Any]]:
    """Get all users"""
    async with get_db() as db:
        if include_inactive:
            cursor = await db.execute("SELECT * FROM users ORDER BY username")
        else:
            cursor = await db.execute("SELECT * FROM users WHERE is_active = 1 ORDER BY username")
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def update_user(user_id: int, **kwargs) -> bool:
    """Update user fields"""
    if not kwargs:
        return False

    fields = ", ".join([f"{k} = ?" for k in kwargs.keys()])
    values = list(kwargs.values()) + [user_id]

    async with get_db() as db:
        await db.execute(f"UPDATE users SET {fields} WHERE id = ?", values)
        await db.commit()
        return True


async def delete_user(user_id: int) -> bool:
    """Delete a user (soft delete by setting is_active = 0)"""
    async with get_db() as db:
        await db.execute("UPDATE users SET is_active = 0 WHERE id = ?", (user_id,))
        await db.commit()
        return True


async def update_last_login(user_id: int):
    """Update user's last login timestamp"""
    async with get_db() as db:
        await db.execute(
            "UPDATE users SET last_login_at = ? WHERE id = ?",
            (int(datetime.now().timestamp()), user_id)
        )
        await db.commit()


async def increment_failed_login(user_id: int) -> int:
    """Increment failed login attempts, return new count"""
    async with get_db() as db:
        await db.execute(
            "UPDATE users SET failed_login_attempts = failed_login_attempts + 1 WHERE id = ?",
            (user_id,)
        )
        await db.commit()

        cursor = await db.execute(
            "SELECT failed_login_attempts FROM users WHERE id = ?",
            (user_id,)
        )
        row = await cursor.fetchone()
        return row[0] if row else 0


async def reset_failed_login(user_id: int):
    """Reset failed login attempts to 0"""
    async with get_db() as db:
        await db.execute(
            "UPDATE users SET failed_login_attempts = 0 WHERE id = ?",
            (user_id,)
        )
        await db.commit()


# =============================================================================
# Door Configuration Operations
# =============================================================================

async def create_door_config(door_id: int, door_name: str, **kwargs) -> int:
    """Create a new door configuration"""
    async with get_db() as db:
        fields = ["door_id", "door_name"] + list(kwargs.keys())
        placeholders = ", ".join(["?"] * len(fields))
        values = [door_id, door_name] + list(kwargs.values())

        await db.execute(
            f"INSERT INTO door_configs ({', '.join(fields)}) VALUES ({placeholders})",
            values
        )
        await db.commit()
        return door_id


async def get_door_config(door_id: int) -> Optional[Dict[str, Any]]:
    """Get door configuration by ID"""
    async with get_db() as db:
        cursor = await db.execute("SELECT * FROM door_configs WHERE door_id = ?", (door_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None


async def get_all_door_configs() -> List[Dict[str, Any]]:
    """Get all door configurations"""
    async with get_db() as db:
        cursor = await db.execute("SELECT * FROM door_configs ORDER BY door_name")
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def update_door_config(door_id: int, **kwargs) -> bool:
    """Update door configuration"""
    if not kwargs:
        return False

    fields = ", ".join([f"{k} = ?" for k in kwargs.keys()])
    values = list(kwargs.values()) + [door_id]

    async with get_db() as db:
        await db.execute(f"UPDATE door_configs SET {fields} WHERE door_id = ?", values)
        await db.commit()
        return True


async def delete_door_config(door_id: int) -> bool:
    """Delete a door configuration"""
    async with get_db() as db:
        await db.execute("DELETE FROM door_configs WHERE door_id = ?", (door_id,))
        await db.commit()
        return True


# =============================================================================
# Access Level Operations
# =============================================================================

async def create_access_level(name: str, description: str = None, priority: int = 0) -> int:
    """Create a new access level"""
    async with get_db() as db:
        cursor = await db.execute(
            "INSERT INTO access_levels (name, description, priority) VALUES (?, ?, ?)",
            (name, description, priority)
        )
        await db.commit()
        return cursor.lastrowid


async def get_access_level(access_level_id: int) -> Optional[Dict[str, Any]]:
    """Get access level by ID"""
    async with get_db() as db:
        cursor = await db.execute("SELECT * FROM access_levels WHERE id = ?", (access_level_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None


async def get_all_access_levels(include_inactive: bool = False) -> List[Dict[str, Any]]:
    """Get all access levels"""
    async with get_db() as db:
        if include_inactive:
            cursor = await db.execute("SELECT * FROM access_levels ORDER BY priority DESC, name")
        else:
            cursor = await db.execute(
                "SELECT * FROM access_levels WHERE is_active = 1 ORDER BY priority DESC, name"
            )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def update_access_level(access_level_id: int, **kwargs) -> bool:
    """Update access level"""
    if not kwargs:
        return False

    fields = ", ".join([f"{k} = ?" for k in kwargs.keys()])
    values = list(kwargs.values()) + [access_level_id]

    async with get_db() as db:
        await db.execute(f"UPDATE access_levels SET {fields} WHERE id = ?", values)
        await db.commit()
        return True


async def delete_access_level(access_level_id: int) -> bool:
    """Delete an access level (soft delete)"""
    async with get_db() as db:
        await db.execute("UPDATE access_levels SET is_active = 0 WHERE id = ?", (access_level_id,))
        await db.commit()
        return True


# =============================================================================
# Access Level Door Assignment
# =============================================================================

async def add_door_to_access_level(access_level_id: int, door_id: int,
                                   timezone_id: int = 2, entry_allowed: bool = True,
                                   exit_allowed: bool = True) -> int:
    """Add a door to an access level"""
    async with get_db() as db:
        cursor = await db.execute("""
            INSERT OR REPLACE INTO access_level_doors
            (access_level_id, door_id, timezone_id, entry_allowed, exit_allowed)
            VALUES (?, ?, ?, ?, ?)
        """, (access_level_id, door_id, timezone_id, entry_allowed, exit_allowed))
        await db.commit()
        return cursor.lastrowid


async def remove_door_from_access_level(access_level_id: int, door_id: int) -> bool:
    """Remove a door from an access level"""
    async with get_db() as db:
        await db.execute(
            "DELETE FROM access_level_doors WHERE access_level_id = ? AND door_id = ?",
            (access_level_id, door_id)
        )
        await db.commit()
        return True


async def get_access_level_doors(access_level_id: int) -> List[Dict[str, Any]]:
    """Get all doors for an access level"""
    async with get_db() as db:
        cursor = await db.execute("""
            SELECT ald.*, dc.door_name, dc.location, dc.door_type
            FROM access_level_doors ald
            JOIN door_configs dc ON ald.door_id = dc.door_id
            WHERE ald.access_level_id = ?
            ORDER BY dc.door_name
        """, (access_level_id,))
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def get_door_access_levels(door_id: int) -> List[Dict[str, Any]]:
    """Get all access levels for a door"""
    async with get_db() as db:
        cursor = await db.execute("""
            SELECT al.*, ald.entry_allowed, ald.exit_allowed, ald.timezone_id
            FROM access_levels al
            JOIN access_level_doors ald ON al.id = ald.access_level_id
            WHERE ald.door_id = ? AND al.is_active = 1
            ORDER BY al.priority DESC, al.name
        """, (door_id,))
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


# =============================================================================
# User Access Level Assignment
# =============================================================================

async def grant_user_access_level(user_id: int, access_level_id: int,
                                  activation_date: int = 0, expiration_date: int = 0,
                                  granted_by: int = None, notes: str = None) -> int:
    """Grant an access level to a user"""
    async with get_db() as db:
        cursor = await db.execute("""
            INSERT OR REPLACE INTO user_access_levels
            (user_id, access_level_id, activation_date, expiration_date, granted_by, notes)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, access_level_id, activation_date, expiration_date, granted_by, notes))
        await db.commit()
        return cursor.lastrowid


async def revoke_user_access_level(user_id: int, access_level_id: int, revoked_by: int = None) -> bool:
    """Revoke an access level from a user"""
    async with get_db() as db:
        await db.execute("""
            UPDATE user_access_levels
            SET is_active = 0, revoked_by = ?, revoked_at = ?
            WHERE user_id = ? AND access_level_id = ?
        """, (revoked_by, int(datetime.now().timestamp()), user_id, access_level_id))
        await db.commit()
        return True


async def get_user_access_levels(user_id: int) -> List[Dict[str, Any]]:
    """Get all access levels for a user"""
    async with get_db() as db:
        cursor = await db.execute("""
            SELECT al.*, ual.activation_date, ual.expiration_date, ual.is_active as assignment_active
            FROM access_levels al
            JOIN user_access_levels ual ON al.id = ual.access_level_id
            WHERE ual.user_id = ? AND ual.is_active = 1
            ORDER BY al.priority DESC, al.name
        """, (user_id,))
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def get_users_with_access_level(access_level_id: int) -> List[Dict[str, Any]]:
    """Get all users who have a specific access level"""
    async with get_db() as db:
        cursor = await db.execute("""
            SELECT u.*, ual.activation_date, ual.expiration_date
            FROM users u
            JOIN user_access_levels ual ON u.id = ual.user_id
            WHERE ual.access_level_id = ? AND ual.is_active = 1 AND u.is_active = 1
            ORDER BY u.username
        """, (access_level_id,))
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def get_user_doors(user_id: int) -> List[Dict[str, Any]]:
    """Get all doors a user can access"""
    async with get_db() as db:
        cursor = await db.execute("""
            SELECT DISTINCT dc.*, ald.entry_allowed, ald.exit_allowed
            FROM door_configs dc
            JOIN access_level_doors ald ON dc.door_id = ald.door_id
            JOIN user_access_levels ual ON ald.access_level_id = ual.access_level_id
            WHERE ual.user_id = ?
                AND ual.is_active = 1
                AND (ual.activation_date = 0 OR ual.activation_date <= strftime('%s','now'))
                AND (ual.expiration_date = 0 OR ual.expiration_date >= strftime('%s','now'))
            ORDER BY dc.door_name
        """, (user_id,))
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


# =============================================================================
# Audit Log
# =============================================================================

async def log_audit(user_id: Optional[int], action_type: str, resource_type: str = None,
                   resource_id: int = None, details: Dict[str, Any] = None,
                   ip_address: str = None, user_agent: str = None,
                   success: bool = True, error_message: str = None) -> int:
    """Create an audit log entry"""
    async with get_db() as db:
        cursor = await db.execute("""
            INSERT INTO audit_log
            (user_id, action_type, resource_type, resource_id, details,
             ip_address, user_agent, success, error_message)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, action_type, resource_type, resource_id,
              json.dumps(details) if details else None,
              ip_address, user_agent, success, error_message))
        await db.commit()
        return cursor.lastrowid


async def get_audit_logs(limit: int = 100, offset: int = 0,
                        user_id: int = None, action_type: str = None,
                        start_time: int = None, end_time: int = None) -> List[Dict[str, Any]]:
    """Get audit logs with optional filters"""
    query = "SELECT * FROM audit_log WHERE 1=1"
    params = []

    if user_id:
        query += " AND user_id = ?"
        params.append(user_id)

    if action_type:
        query += " AND action_type = ?"
        params.append(action_type)

    if start_time:
        query += " AND timestamp >= ?"
        params.append(start_time)

    if end_time:
        query += " AND timestamp <= ?"
        params.append(end_time)

    query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    async with get_db() as db:
        cursor = await db.execute(query, params)
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


# =============================================================================
# Session Management
# =============================================================================

async def create_session(user_id: int, token_hash: str, expires_at: int,
                        device_info: str = None, ip_address: str = None,
                        user_agent: str = None) -> int:
    """Create a new session"""
    async with get_db() as db:
        cursor = await db.execute("""
            INSERT INTO sessions
            (user_id, token_hash, expires_at, device_info, ip_address, user_agent)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, token_hash, expires_at, device_info, ip_address, user_agent))
        await db.commit()
        return cursor.lastrowid


async def get_session(token_hash: str) -> Optional[Dict[str, Any]]:
    """Get session by token hash"""
    async with get_db() as db:
        cursor = await db.execute("""
            SELECT * FROM sessions
            WHERE token_hash = ? AND is_active = 1 AND expires_at > strftime('%s','now')
        """, (token_hash,))
        row = await cursor.fetchone()
        return dict(row) if row else None


async def invalidate_session(token_hash: str) -> bool:
    """Invalidate a session (logout)"""
    async with get_db() as db:
        await db.execute("UPDATE sessions SET is_active = 0 WHERE token_hash = ?", (token_hash,))
        await db.commit()
        return True


async def invalidate_user_sessions(user_id: int) -> bool:
    """Invalidate all sessions for a user"""
    async with get_db() as db:
        await db.execute("UPDATE sessions SET is_active = 0 WHERE user_id = ?", (user_id,))
        await db.commit()
        return True


async def cleanup_expired_sessions():
    """Remove expired sessions"""
    async with get_db() as db:
        await db.execute("DELETE FROM sessions WHERE expires_at < strftime('%s','now')")
        await db.commit()


# =============================================================================
# Card Holder Management
# =============================================================================

async def create_card_holder(card_number: str, first_name: str, last_name: str, **kwargs) -> int:
    """Create a new card holder"""
    async with get_db() as db:
        fields = ["card_number", "first_name", "last_name"] + list(kwargs.keys())
        placeholders = ", ".join(["?"] * len(fields))
        values = [card_number, first_name, last_name] + list(kwargs.values())

        cursor = await db.execute(
            f"INSERT INTO card_holders ({', '.join(fields)}) VALUES ({placeholders})",
            values
        )
        await db.commit()
        return cursor.lastrowid


async def get_card_holder(card_holder_id: int) -> Optional[Dict[str, Any]]:
    """Get card holder by ID"""
    async with get_db() as db:
        cursor = await db.execute("SELECT * FROM card_holders WHERE id = ?", (card_holder_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None


async def get_card_holder_by_card_number(card_number: str) -> Optional[Dict[str, Any]]:
    """Get card holder by card number"""
    async with get_db() as db:
        cursor = await db.execute("SELECT * FROM card_holders WHERE card_number = ?", (card_number,))
        row = await cursor.fetchone()
        return dict(row) if row else None


async def get_all_card_holders(include_inactive: bool = False) -> List[Dict[str, Any]]:
    """Get all card holders"""
    query = "SELECT * FROM card_holders"
    if not include_inactive:
        query += " WHERE is_active = 1"
    query += " ORDER BY last_name, first_name"

    async with get_db() as db:
        cursor = await db.execute(query)
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def update_card_holder(card_holder_id: int, **kwargs) -> bool:
    """Update card holder information"""
    if not kwargs:
        return False

    # Remove id from kwargs if present
    kwargs.pop('id', None)

    set_clause = ", ".join([f"{key} = ?" for key in kwargs.keys()])
    values = list(kwargs.values()) + [card_holder_id]

    async with get_db() as db:
        await db.execute(
            f"UPDATE card_holders SET {set_clause} WHERE id = ?",
            values
        )
        await db.commit()
        return True


async def delete_card_holder(card_holder_id: int) -> bool:
    """Delete a card holder (soft delete - set is_active to False)"""
    async with get_db() as db:
        await db.execute("UPDATE card_holders SET is_active = 0 WHERE id = ?", (card_holder_id,))
        await db.commit()
        return True


async def hard_delete_card_holder(card_holder_id: int) -> bool:
    """Permanently delete a card holder"""
    async with get_db() as db:
        await db.execute("DELETE FROM card_holders WHERE id = ?", (card_holder_id,))
        await db.commit()
        return True


# =============================================================================
# Card Holder Access Levels
# =============================================================================

async def grant_card_holder_access_level(card_holder_id: int, level_id: int, granted_by: int = None, **kwargs) -> int:
    """Grant an access level to a card holder"""
    async with get_db() as db:
        fields = ["card_holder_id", "level_id"]
        values = [card_holder_id, level_id]

        if granted_by:
            fields.append("granted_by")
            values.append(granted_by)

        for key, value in kwargs.items():
            fields.append(key)
            values.append(value)

        placeholders = ", ".join(["?"] * len(fields))

        cursor = await db.execute(
            f"INSERT INTO card_holder_access_levels ({', '.join(fields)}) VALUES ({placeholders})",
            values
        )
        await db.commit()
        return cursor.lastrowid


async def revoke_card_holder_access_level(card_holder_id: int, level_id: int) -> bool:
    """Revoke an access level from a card holder"""
    async with get_db() as db:
        await db.execute(
            "DELETE FROM card_holder_access_levels WHERE card_holder_id = ? AND level_id = ?",
            (card_holder_id, level_id)
        )
        await db.commit()
        return True


async def get_card_holder_access_levels(card_holder_id: int) -> List[Dict[str, Any]]:
    """Get all access levels for a card holder"""
    async with get_db() as db:
        cursor = await db.execute("""
            SELECT
                al.level_id,
                al.name as level_name,
                al.description,
                al.priority,
                chal.granted_at,
                chal.expires_at,
                chal.is_active,
                chal.notes,
                u.username as granted_by_username
            FROM card_holder_access_levels chal
            JOIN access_levels al ON chal.level_id = al.level_id
            LEFT JOIN users u ON chal.granted_by = u.id
            WHERE chal.card_holder_id = ?
            ORDER BY al.priority DESC, al.name
        """, (card_holder_id,))
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def get_card_holder_doors(card_holder_id: int) -> List[Dict[str, Any]]:
    """Get all doors a card holder can access through their access levels"""
    async with get_db() as db:
        cursor = await db.execute("""
            SELECT DISTINCT
                dc.door_id,
                dc.door_name,
                dc.location,
                dc.door_type,
                dc.osdp_enabled,
                al.name as level_name,
                al.priority
            FROM card_holder_access_levels chal
            JOIN access_levels al ON chal.level_id = al.level_id
            JOIN access_level_doors ald ON al.level_id = ald.level_id
            JOIN door_configs dc ON ald.door_id = dc.door_id
            WHERE chal.card_holder_id = ?
              AND chal.is_active = 1
              AND al.is_active = 1
            ORDER BY dc.door_name
        """, (card_holder_id,))
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def get_access_level_card_holders(level_id: int) -> List[Dict[str, Any]]:
    """Get all card holders assigned to an access level"""
    async with get_db() as db:
        cursor = await db.execute("""
            SELECT
                ch.id,
                ch.card_number,
                ch.first_name,
                ch.last_name,
                ch.email,
                ch.department,
                ch.employee_id,
                ch.is_active,
                chal.granted_at,
                chal.expires_at
            FROM card_holder_access_levels chal
            JOIN card_holders ch ON chal.card_holder_id = ch.id
            WHERE chal.level_id = ?
            ORDER BY ch.last_name, ch.first_name
        """, (level_id,))
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


# =============================================================================
# Panel Hierarchy Operations
# =============================================================================

async def create_panel(panel_id: int, panel_name: str, panel_type: str,
                      parent_panel_id: Optional[int] = None,
                      rs485_address: Optional[int] = None,
                      firmware_version: Optional[str] = None) -> int:
    """Create a new panel"""
    async with get_db() as db:
        await db.execute("""
            INSERT INTO panels (panel_id, panel_name, panel_type, parent_panel_id,
                              rs485_address, firmware_version)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (panel_id, panel_name, panel_type, parent_panel_id, rs485_address, firmware_version))
        await db.commit()
        return panel_id


async def get_panel(panel_id: int) -> Optional[Dict[str, Any]]:
    """Get panel by ID"""
    async with get_db() as db:
        cursor = await db.execute("SELECT * FROM panels WHERE panel_id = ?", (panel_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None


async def get_all_panels() -> List[Dict[str, Any]]:
    """Get all panels"""
    async with get_db() as db:
        cursor = await db.execute("SELECT * FROM panels ORDER BY panel_type, panel_id")
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def get_downstream_panels(parent_panel_id: int) -> List[Dict[str, Any]]:
    """Get all downstream panels for a master panel"""
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT * FROM panels WHERE parent_panel_id = ? ORDER BY rs485_address",
            (parent_panel_id,)
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def update_panel(panel_id: int, **kwargs) -> Optional[Dict[str, Any]]:
    """Update panel information"""
    fields = []
    values = []

    for key, value in kwargs.items():
        if value is not None:
            fields.append(f"{key} = ?")
            values.append(value)

    if not fields:
        return await get_panel(panel_id)

    values.append(panel_id)

    async with get_db() as db:
        await db.execute(f"""
            UPDATE panels
            SET {', '.join(fields)}, updated_at = strftime('%s','now')
            WHERE panel_id = ?
        """, values)
        await db.commit()
        return await get_panel(panel_id)


async def delete_panel(panel_id: int) -> bool:
    """Delete a panel and all associated devices"""
    async with get_db() as db:
        await db.execute("DELETE FROM panels WHERE panel_id = ?", (panel_id,))
        await db.commit()
        return True


async def update_panel_status(panel_id: int, status: str) -> bool:
    """Update panel online/offline status"""
    async with get_db() as db:
        await db.execute("""
            UPDATE panels
            SET status = ?, last_seen = strftime('%s','now')
            WHERE panel_id = ?
        """, (status, panel_id))
        await db.commit()
        return True


# Panel Readers
async def create_panel_reader(panel_id: int, reader_address: int,
                             reader_name: Optional[str] = None) -> int:
    """Create a new reader associated with a panel"""
    async with get_db() as db:
        cursor = await db.execute("""
            INSERT INTO readers_new (panel_id, reader_address, reader_name)
            VALUES (?, ?, ?)
        """, (panel_id, reader_address, reader_name))
        await db.commit()
        return cursor.lastrowid


async def get_panel_readers(panel_id: int) -> List[Dict[str, Any]]:
    """Get all readers for a panel"""
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT * FROM readers_new WHERE panel_id = ? ORDER BY reader_address",
            (panel_id,)
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def update_reader_status(reader_id: int, status: str) -> bool:
    """Update reader status"""
    async with get_db() as db:
        await db.execute("""
            UPDATE readers_new
            SET status = ?, last_seen = strftime('%s','now')
            WHERE reader_id = ?
        """, (status, reader_id))
        await db.commit()
        return True


# Panel Inputs
async def create_panel_input(panel_id: int, input_number: int,
                            input_name: Optional[str] = None) -> int:
    """Create a panel input"""
    async with get_db() as db:
        cursor = await db.execute("""
            INSERT INTO panel_inputs (panel_id, input_number, input_name)
            VALUES (?, ?, ?)
        """, (panel_id, input_number, input_name))
        await db.commit()
        return cursor.lastrowid


async def get_panel_inputs(panel_id: int) -> List[Dict[str, Any]]:
    """Get all inputs for a panel"""
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT * FROM panel_inputs WHERE panel_id = ? ORDER BY input_number",
            (panel_id,)
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def update_input_state(input_id: int, state: str) -> bool:
    """Update input state"""
    async with get_db() as db:
        await db.execute("""
            UPDATE panel_inputs
            SET state = ?, last_state_change = strftime('%s','now')
            WHERE input_id = ?
        """, (state, input_id))
        await db.commit()
        return True


# Panel Outputs
async def create_panel_output(panel_id: int, output_number: int,
                             output_name: Optional[str] = None) -> int:
    """Create a panel output"""
    async with get_db() as db:
        cursor = await db.execute("""
            INSERT INTO panel_outputs (panel_id, output_number, output_name)
            VALUES (?, ?, ?)
        """, (panel_id, output_number, output_name))
        await db.commit()
        return cursor.lastrowid


async def get_panel_outputs(panel_id: int) -> List[Dict[str, Any]]:
    """Get all outputs for a panel"""
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT * FROM panel_outputs WHERE panel_id = ? ORDER BY output_number",
            (panel_id,)
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def update_output_state(output_id: int, state: str) -> bool:
    """Update output state"""
    async with get_db() as db:
        await db.execute("""
            UPDATE panel_outputs
            SET state = ?, last_state_change = strftime('%s','now')
            WHERE output_id = ?
        """, (state, output_id))
        await db.commit()
        return True


# Panel Relays
async def create_panel_relay(panel_id: int, relay_number: int,
                            relay_name: Optional[str] = None) -> int:
    """Create a panel relay"""
    async with get_db() as db:
        cursor = await db.execute("""
            INSERT INTO panel_relays (panel_id, relay_number, relay_name)
            VALUES (?, ?, ?)
        """, (panel_id, relay_number, relay_name))
        await db.commit()
        return cursor.lastrowid


async def get_panel_relays(panel_id: int) -> List[Dict[str, Any]]:
    """Get all relays for a panel"""
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT * FROM panel_relays WHERE panel_id = ? ORDER BY relay_number",
            (panel_id,)
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def update_relay_state(relay_id: int, state: str) -> bool:
    """Update relay state"""
    async with get_db() as db:
        await db.execute("""
            UPDATE panel_relays
            SET state = ?, last_state_change = strftime('%s','now')
            WHERE relay_id = ?
        """, (state, relay_id))
        await db.commit()
        return True


# Hardware Tree
async def get_hardware_tree() -> List[Dict[str, Any]]:
    """
    Get complete hardware tree structure with all panels and their devices
    Returns hierarchical structure suitable for tree visualization
    """
    async with get_db() as db:
        # Get all panels
        cursor = await db.execute("""
            SELECT panel_id, panel_name, panel_type, parent_panel_id,
                   rs485_address, status, firmware_version, last_seen
            FROM panels
            ORDER BY panel_type, panel_id
        """)
        panels = [dict(row) for row in await cursor.fetchall()]

        # Build tree structure
        tree = []
        for panel in panels:
            panel_node = {
                **panel,
                'readers': await get_panel_readers(panel['panel_id']),
                'inputs': await get_panel_inputs(panel['panel_id']),
                'outputs': await get_panel_outputs(panel['panel_id']),
                'relays': await get_panel_relays(panel['panel_id']),
                'children': []
            }

            if panel['panel_type'] == 'MASTER':
                # Add downstream panels as children
                downstream = [p for p in panels if p['parent_panel_id'] == panel['panel_id']]
                for downstream_panel in downstream:
                    child_node = {
                        **downstream_panel,
                        'readers': await get_panel_readers(downstream_panel['panel_id']),
                        'inputs': await get_panel_inputs(downstream_panel['panel_id']),
                        'outputs': await get_panel_outputs(downstream_panel['panel_id']),
                        'relays': await get_panel_relays(downstream_panel['panel_id'])
                    }
                    panel_node['children'].append(child_node)

                tree.append(panel_node)

        return tree
