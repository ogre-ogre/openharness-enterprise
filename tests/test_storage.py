"""
Tests for storage layer.
"""

import pytest
import tempfile
from pathlib import Path

from openharness.enterprise.storage.database import (
    Database,
    User,
    Session,
    init_database,
)


class TestDatabase:
    """Test database operations."""
    
    @pytest.fixture
    def db(self, tmp_path):
        """Create test database."""
        db_path = tmp_path / "test.db"
        db = Database(db_path)
        db.connect()
        db.init_schema()
        yield db
        db.close()
    
    def test_init_schema(self, db):
        """Test schema initialization."""
        # Check tables exist
        cursor = db._conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        assert "users" in tables
        assert "sessions" in tables
        assert "messages" in tables
        assert "audit_logs" in tables
    
    def test_create_user(self, db):
        """Test user creation."""
        user = db.create_user(
            username="testuser",
            password_hash="hashed_password",
            display_name="Test User",
            api_key="oh_test_key"
        )
        
        assert user.id is not None
        assert user.username == "testuser"
        assert user.display_name == "Test User"
        assert user.api_key == "oh_test_key"
    
    def test_get_user_by_username(self, db):
        """Test get user by username."""
        db.create_user(
            username="testuser",
            password_hash="hashed_password"
        )
        
        user = db.get_user_by_username("testuser")
        assert user is not None
        assert user.username == "testuser"
        
        # Non-existent user
        user = db.get_user_by_username("nonexistent")
        assert user is None
    
    def test_get_user_by_api_key(self, db):
        """Test get user by API key."""
        db.create_user(
            username="testuser",
            password_hash="hashed_password",
            api_key="oh_test_key"
        )
        
        user = db.get_user_by_api_key("oh_test_key")
        assert user is not None
        assert user.username == "testuser"
        
        # Non-existent key
        user = db.get_user_by_api_key("oh_invalid_key")
        assert user is None
    
    def test_update_user(self, db):
        """Test user update."""
        user = db.create_user(
            username="testuser",
            password_hash="hashed_password"
        )
        
        updated = db.update_user(
            user_id=user.id,
            display_name="Updated Name",
            role="admin"
        )
        
        assert updated.display_name == "Updated Name"
        assert updated.role == "admin"
    
    def test_list_users(self, db):
        """Test list users."""
        for i in range(5):
            db.create_user(
                username=f"user{i}",
                password_hash="hash"
            )
        
        users = db.list_users(page=1, limit=3)
        assert len(users) == 3
        
        total = db.count_users()
        assert total == 5
    
    def test_create_session(self, db):
        """Test session creation."""
        user = db.create_user(
            username="testuser",
            password_hash="hash"
        )
        
        session = db.create_session(
            session_id="session-123",
            user_id=user.id,
            title="Test Session"
        )
        
        assert session.id == "session-123"
        assert session.user_id == user.id
    
    def test_audit_log(self, db):
        """Test audit logging."""
        user = db.create_user(
            username="testuser",
            password_hash="hash"
        )
        
        db.log_audit(
            user_id=user.id,
            action="login",
            details={"success": True},
            ip_address="127.0.0.1"
        )
        
        logs = db.query_audit_logs(user_id=user.id)
        assert len(logs) == 1
        assert logs[0].action == "login"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])