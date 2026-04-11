"""
OpenHarness Enterprise - Storage Layer

SQLite database operations for users, sessions, audit logs.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

from pydantic import BaseModel


# ============================================================================
# Data Models
# ============================================================================

class User(BaseModel):
    """User model."""
    id: int
    username: str
    password_hash: str
    display_name: Optional[str] = None
    email: Optional[str] = None
    role: str = "user"  # 'user' | 'admin'
    is_active: bool = True
    api_key: Optional[str] = None
    api_key_enabled: bool = True
    created_at: Optional[datetime] = None
    last_login_at: Optional[datetime] = None
    last_api_key_used_at: Optional[datetime] = None


class Session(BaseModel):
    """Session model."""
    id: str
    user_id: int
    title: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    message_count: int = 0
    is_active: bool = True


class Message(BaseModel):
    """Message model."""
    id: str
    session_id: str
    role: str  # 'user' | 'assistant' | 'system'
    content: Optional[str] = None
    tokens_used: Optional[int] = None
    created_at: Optional[datetime] = None


class AuditLog(BaseModel):
    """Audit log model."""
    id: int
    user_id: Optional[int] = None
    action: str
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    created_at: Optional[datetime] = None


class SharedResourcePermission(BaseModel):
    """Shared resource permission model."""
    id: int
    resource_type: str  # 'skill' | 'plugin' | 'template'
    resource_name: str
    user_id: Optional[int] = None  # NULL means everyone can access
    permission: str = "read"  # 'read' | 'write' | 'admin'


# ============================================================================
# Database Manager
# ============================================================================

class Database:
    """
    SQLite database manager for OpenHarness Enterprise.
    
    Features:
    - Users CRUD
    - Sessions CRUD
    - Messages CRUD
    - Audit logs
    - Shared resource permissions
    """
    
    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        self._conn: Optional[sqlite3.Connection] = None
    
    def connect(self) -> None:
        """Connect to database."""
        self._conn = sqlite3.connect(str(self.db_path))
        self._conn.row_factory = sqlite3.Row
    
    def close(self) -> None:
        """Close database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None
    
    def init_schema(self) -> None:
        """Initialize database schema."""
        if not self._conn:
            self.connect()
        
        cursor = self._conn.cursor()
        
        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                display_name TEXT,
                email TEXT,
                role TEXT DEFAULT 'user',
                is_active BOOLEAN DEFAULT 1,
                api_key TEXT UNIQUE,
                api_key_enabled BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login_at TIMESTAMP,
                last_api_key_used_at TIMESTAMP
            )
        """)
        
        # Sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                title TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP,
                message_count INTEGER DEFAULT 0,
                is_active BOOLEAN DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        
        # Messages table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT,
                tokens_used INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions(id)
            )
        """)
        
        # Audit logs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                action TEXT NOT NULL,
                resource_type TEXT,
                resource_id TEXT,
                details TEXT,
                ip_address TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        
        # Shared resource permissions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS shared_resource_permissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                resource_type TEXT NOT NULL,
                resource_name TEXT NOT NULL,
                user_id INTEGER,
                permission TEXT DEFAULT 'read',
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_api_key ON users(api_key)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_session_id ON messages(session_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at)")
        
        self._conn.commit()
    
    # ------------------------------------------------------------------------
    # User Operations
    # ------------------------------------------------------------------------
    
    def get_user(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        cursor = self._conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        return self._row_to_user(row) if row else None
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        cursor = self._conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
        return self._row_to_user(row) if row else None
    
    def get_user_by_api_key(self, api_key: str) -> Optional[User]:
        """Get user by API key."""
        cursor = self._conn.cursor()
        cursor.execute(
            "SELECT * FROM users WHERE api_key = ? AND is_active = 1",
            (api_key,)
        )
        row = cursor.fetchone()
        return self._row_to_user(row) if row else None
    
    def create_user(
        self,
        username: str,
        password_hash: str,
        display_name: Optional[str] = None,
        email: Optional[str] = None,
        role: str = "user",
        api_key: Optional[str] = None
    ) -> User:
        """Create a new user."""
        cursor = self._conn.cursor()
        cursor.execute("""
            INSERT INTO users (username, password_hash, display_name, email, role, api_key)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (username, password_hash, display_name, email, role, api_key))
        self._conn.commit()
        
        user_id = cursor.lastrowid
        return self.get_user(user_id)
    
    def update_user(
        self,
        user_id: int,
        display_name: Optional[str] = None,
        email: Optional[str] = None,
        role: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> Optional[User]:
        """Update user info."""
        updates = []
        params = []
        
        if display_name is not None:
            updates.append("display_name = ?")
            params.append(display_name)
        if email is not None:
            updates.append("email = ?")
            params.append(email)
        if role is not None:
            updates.append("role = ?")
            params.append(role)
        if is_active is not None:
            updates.append("is_active = ?")
            params.append(is_active)
        
        if not updates:
            return self.get_user(user_id)
        
        params.append(user_id)
        cursor = self._conn.cursor()
        cursor.execute(
            f"UPDATE users SET {', '.join(updates)} WHERE id = ?",
            params
        )
        self._conn.commit()
        
        return self.get_user(user_id)
    
    def update_password(self, user_id: int, password_hash: str) -> None:
        """Update user password."""
        cursor = self._conn.cursor()
        cursor.execute(
            "UPDATE users SET password_hash = ? WHERE id = ?",
            (password_hash, user_id)
        )
        self._conn.commit()
    
    def update_last_login(self, user_id: int) -> None:
        """Update user last login time."""
        cursor = self._conn.cursor()
        cursor.execute(
            "UPDATE users SET last_login_at = CURRENT_TIMESTAMP WHERE id = ?",
            (user_id,)
        )
        self._conn.commit()
    
    def update_api_key(self, user_id: int, api_key: str) -> None:
        """Update user API key."""
        cursor = self._conn.cursor()
        cursor.execute(
            "UPDATE users SET api_key = ?, api_key_enabled = 1 WHERE id = ?",
            (api_key, user_id)
        )
        self._conn.commit()
    
    def set_api_key_enabled(self, user_id: int, enabled: bool) -> None:
        """Enable/disable user API key."""
        cursor = self._conn.cursor()
        cursor.execute(
            "UPDATE users SET api_key_enabled = ? WHERE id = ?",
            (enabled, user_id)
        )
        self._conn.commit()
    
    def update_api_key_last_used(self, user_id: int) -> None:
        """Update API key last used time."""
        cursor = self._conn.cursor()
        cursor.execute(
            "UPDATE users SET last_api_key_used_at = CURRENT_TIMESTAMP WHERE id = ?",
            (user_id,)
        )
        self._conn.commit()
    
    def list_users(
        self,
        search: Optional[str] = None,
        page: int = 1,
        limit: int = 20
    ) -> List[User]:
        """List users with optional search and pagination."""
        cursor = self._conn.cursor()
        
        offset = (page - 1) * limit
        
        if search:
            cursor.execute("""
                SELECT * FROM users
                WHERE username LIKE ? OR display_name LIKE ?
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            """, (f"%{search}%", f"%{search}%", limit, offset))
        else:
            cursor.execute("""
                SELECT * FROM users
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            """, (limit, offset))
        
        rows = cursor.fetchall()
        return [self._row_to_user(row) for row in rows]
    
    def count_users(self, search: Optional[str] = None) -> int:
        """Count users."""
        cursor = self._conn.cursor()
        
        if search:
            cursor.execute("""
                SELECT COUNT(*) FROM users
                WHERE username LIKE ? OR display_name LIKE ?
            """, (f"%{search}%", f"%{search}%"))
        else:
            cursor.execute("SELECT COUNT(*) FROM users")
        
        return cursor.fetchone()[0]
    
    def user_exists(self, username: str) -> bool:
        """Check if user exists."""
        cursor = self._conn.cursor()
        cursor.execute("SELECT 1 FROM users WHERE username = ?", (username,))
        return cursor.fetchone() is not None
    
    def _row_to_user(self, row: sqlite3.Row) -> User:
        """Convert row to User model."""
        return User(
            id=row["id"],
            username=row["username"],
            password_hash=row["password_hash"],
            display_name=row["display_name"],
            email=row["email"],
            role=row["role"],
            is_active=row["is_active"],
            api_key=row["api_key"],
            api_key_enabled=row["api_key_enabled"],
            created_at=self._parse_datetime(row["created_at"]),
            last_login_at=self._parse_datetime(row["last_login_at"]),
            last_api_key_used_at=self._parse_datetime(row["last_api_key_used_at"]),
        )
    
    # ------------------------------------------------------------------------
    # Session Operations
    # ------------------------------------------------------------------------
    
    def create_session(
        self,
        session_id: str,
        user_id: int,
        title: Optional[str] = None
    ) -> Session:
        """Create a new session."""
        cursor = self._conn.cursor()
        cursor.execute("""
            INSERT INTO sessions (id, user_id, title)
            VALUES (?, ?, ?)
        """, (session_id, user_id, title))
        self._conn.commit()
        
        return self.get_session(session_id)
    
    def get_session(self, session_id: str) -> Optional[Session]:
        """Get session by ID."""
        cursor = self._conn.cursor()
        cursor.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
        row = cursor.fetchone()
        return self._row_to_session(row) if row else None
    
    def get_user_sessions(
        self,
        user_id: int,
        active_only: bool = True,
        limit: int = 50
    ) -> List[Session]:
        """Get user sessions (only sessions with messages)."""
        cursor = self._conn.cursor()
        
        if active_only:
            cursor.execute("""
                SELECT * FROM sessions
                WHERE user_id = ? AND is_active = 'TRUE' AND message_count > 0
                ORDER BY updated_at DESC, created_at DESC
                LIMIT ?
            """, (user_id, limit))
        else:
            cursor.execute("""
                SELECT * FROM sessions
                WHERE user_id = ? AND message_count > 0
                ORDER BY updated_at DESC, created_at DESC
                LIMIT ?
            """, (user_id, limit))
        
        rows = cursor.fetchall()
        return [self._row_to_session(row) for row in rows]
    
    def update_session(
        self,
        session_id: str,
        title: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> Optional[Session]:
        """Update session."""
        updates = ["updated_at = CURRENT_TIMESTAMP"]
        params = []
        
        if title is not None:
            updates.append("title = ?")
            params.append(title)
        if is_active is not None:
            updates.append("is_active = ?")
            params.append(is_active)
        
        params.append(session_id)
        cursor = self._conn.cursor()
        cursor.execute(
            f"UPDATE sessions SET {', '.join(updates)} WHERE id = ?",
            params
        )
        self._conn.commit()
        
        return self.get_session(session_id)
    
    def increment_message_count(self, session_id: str) -> None:
        """Increment session message count."""
        cursor = self._conn.cursor()
        cursor.execute("""
            UPDATE sessions
            SET message_count = message_count + 1, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (session_id,))
        self._conn.commit()
    
    def count_active_sessions(self) -> int:
        """Count active sessions."""
        cursor = self._conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM sessions WHERE is_active = 1")
        return cursor.fetchone()[0]
    
    def _row_to_session(self, row: sqlite3.Row) -> Session:
        """Convert row to Session model."""
        return Session(
            id=row["id"],
            user_id=row["user_id"],
            title=row["title"],
            created_at=self._parse_datetime(row["created_at"]),
            updated_at=self._parse_datetime(row["updated_at"]),
            message_count=row["message_count"],
            is_active=row["is_active"],
        )
    
    # ------------------------------------------------------------------------
    # Message Operations
    # ------------------------------------------------------------------------
    
    def create_message(
        self,
        message_id: str,
        session_id: str,
        role: str,
        content: Optional[str] = None,
        tokens_used: Optional[int] = None
    ) -> Message:
        """Create a new message."""
        cursor = self._conn.cursor()
        cursor.execute("""
            INSERT INTO messages (id, session_id, role, content, tokens_used)
            VALUES (?, ?, ?, ?, ?)
        """, (message_id, session_id, role, content, tokens_used))
        self._conn.commit()
        
        # Increment session message count
        self.increment_message_count(session_id)
        
        return self.get_message(message_id)
    
    def get_message(self, message_id: str) -> Optional[Message]:
        """Get message by ID."""
        cursor = self._conn.cursor()
        cursor.execute("SELECT * FROM messages WHERE id = ?", (message_id,))
        row = cursor.fetchone()
        return self._row_to_message(row) if row else None
    
    def get_session_messages(
        self,
        session_id: str,
        limit: int = 100
    ) -> List[Message]:
        """Get session messages."""
        cursor = self._conn.cursor()
        cursor.execute("""
            SELECT * FROM messages
            WHERE session_id = ?
            ORDER BY created_at ASC
            LIMIT ?
        """, (session_id, limit))
        
        rows = cursor.fetchall()
        return [self._row_to_message(row) for row in rows]
    
    def _row_to_message(self, row: sqlite3.Row) -> Message:
        """Convert row to Message model."""
        return Message(
            id=row["id"],
            session_id=row["session_id"],
            role=row["role"],
            content=row["content"],
            tokens_used=row["tokens_used"],
            created_at=self._parse_datetime(row["created_at"]),
        )
    
    # ------------------------------------------------------------------------
    # Audit Log Operations
    # ------------------------------------------------------------------------
    
    def log_audit(
        self,
        user_id: Optional[int],
        action: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None
    ) -> None:
        """Log audit entry."""
        cursor = self._conn.cursor()
        cursor.execute("""
            INSERT INTO audit_logs (user_id, action, resource_type, resource_id, details, ip_address)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            action,
            resource_type,
            resource_id,
            json.dumps(details) if details else None,
            ip_address
        ))
        self._conn.commit()
    
    def query_audit_logs(
        self,
        user_id: Optional[int] = None,
        action: Optional[str] = None,
        resource_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        page: int = 1,
        limit: int = 50
    ) -> List[AuditLog]:
        """Query audit logs with filters."""
        cursor = self._conn.cursor()
        
        conditions = []
        params = []
        
        if user_id is not None:
            conditions.append("user_id = ?")
            params.append(user_id)
        if action:
            conditions.append("action = ?")
            params.append(action)
        if resource_type:
            conditions.append("resource_type = ?")
            params.append(resource_type)
        if start_date:
            conditions.append("created_at >= ?")
            params.append(start_date.isoformat())
        if end_date:
            conditions.append("created_at <= ?")
            params.append(end_date.isoformat())
        
        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
        offset = (page - 1) * limit
        
        cursor.execute(f"""
            SELECT * FROM audit_logs
            {where_clause}
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        """, params + [limit, offset])
        
        rows = cursor.fetchall()
        return [self._row_to_audit_log(row) for row in rows]
    
    def _row_to_audit_log(self, row: sqlite3.Row) -> AuditLog:
        """Convert row to AuditLog model."""
        return AuditLog(
            id=row["id"],
            user_id=row["user_id"],
            action=row["action"],
            resource_type=row["resource_type"],
            resource_id=row["resource_id"],
            details=json.loads(row["details"]) if row["details"] else None,
            ip_address=row["ip_address"],
            created_at=self._parse_datetime(row["created_at"]),
        )
    
    # ------------------------------------------------------------------------
    # Shared Resource Permission Operations
    # ------------------------------------------------------------------------
    
    def set_permission(
        self,
        resource_type: str,
        resource_name: str,
        user_id: Optional[int],
        permission: str = "read"
    ) -> None:
        """Set resource permission."""
        cursor = self._conn.cursor()
        
        # Delete existing permission for this resource+user
        cursor.execute("""
            DELETE FROM shared_resource_permissions
            WHERE resource_type = ? AND resource_name = ? AND user_id IS ?
        """, (resource_type, resource_name, user_id))
        
        # Insert new permission
        cursor.execute("""
            INSERT INTO shared_resource_permissions (resource_type, resource_name, user_id, permission)
            VALUES (?, ?, ?, ?)
        """, (resource_type, resource_name, user_id, permission))
        
        self._conn.commit()
    
    def get_permissions(
        self,
        resource_type: str,
        resource_name: str
    ) -> List[SharedResourcePermission]:
        """Get permissions for a resource."""
        cursor = self._conn.cursor()
        cursor.execute("""
            SELECT * FROM shared_resource_permissions
            WHERE resource_type = ? AND resource_name = ?
        """, (resource_type, resource_name))
        
        rows = cursor.fetchall()
        return [self._row_to_permission(row) for row in rows]
    
    def user_can_access(
        self,
        user_id: int,
        resource_type: str,
        resource_name: str
    ) -> bool:
        """Check if user can access a shared resource.
        
        Default behavior: If no permission records exist, everyone can access.
        Only returns False if there are permission records but user is not in them.
        """
        cursor = self._conn.cursor()
        
        # Check if any permission records exist for this resource
        cursor.execute("""
            SELECT COUNT(*) FROM shared_resource_permissions
            WHERE resource_type = ? AND resource_name = ?
        """, (resource_type, resource_name))
        count = cursor.fetchone()[0]
        
        # If no permission records, default to allow access
        if count == 0:
            return True
        
        # Check if user has specific permission
        cursor.execute("""
            SELECT 1 FROM shared_resource_permissions
            WHERE resource_type = ? AND resource_name = ? AND user_id = ?
        """, (resource_type, resource_name, user_id))
        if cursor.fetchone():
            return True
        
        # Check if resource is open to everyone (user_id IS NULL)
        cursor.execute("""
            SELECT 1 FROM shared_resource_permissions
            WHERE resource_type = ? AND resource_name = ? AND user_id IS NULL
        """, (resource_type, resource_name))
        return cursor.fetchone() is not None
    
    def _row_to_permission(self, row: sqlite3.Row) -> SharedResourcePermission:
        """Convert row to Permission model."""
        return SharedResourcePermission(
            id=row["id"],
            resource_type=row["resource_type"],
            resource_name=row["resource_name"],
            user_id=row["user_id"],
            permission=row["permission"],
        )
    
    # ------------------------------------------------------------------------
    # Utility Methods
    # ------------------------------------------------------------------------
    
    def _parse_datetime(self, value: Optional[str]) -> Optional[datetime]:
        """Parse datetime string."""
        if not value:
            return None
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return None
    
    def get_db_size(self) -> int:
        """Get database file size."""
        return self.db_path.stat().st_size if self.db_path.exists() else 0


# ============================================================================
# Database Singleton
# ============================================================================

_db_instance: Optional[Database] = None


def get_database(db_path: Optional[str | Path] = None) -> Database:
    """Get database instance."""
    global _db_instance
    
    if _db_instance is None:
        if db_path is None:
            # Default path
            db_path = Path.home() / ".oh-enterprise" / "data.db"
        
        # Ensure directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        _db_instance = Database(db_path)
        _db_instance.connect()
        _db_instance.init_schema()
    
    return _db_instance


def init_database(db_path: Optional[str | Path] = None) -> Database:
    """Initialize database."""
    db = get_database(db_path)
    db.init_schema()
    return db