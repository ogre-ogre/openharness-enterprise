"""
OpenHarness Enterprise - Audit Logger

Audit log recording for tracking user actions.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, date
from pathlib import Path
from typing import Optional, Dict, Any, List

from openharness.enterprise.storage.database import Database, AuditLog, get_database


class AuditLogger:
    """
    Audit logger for recording user actions.
    
    Features:
    - Database logging
    - File logging (backup)
    - Query and filtering
    """
    
    def __init__(
        self,
        db: Optional[Database] = None,
        log_dir: Optional[Path] = None,
        retention_days: int = 90
    ):
        self.db = db or get_database()
        self.log_dir = log_dir or (Path.home() / ".oh-enterprise" / "logs")
        self.retention_days = retention_days
        
        # Ensure log directory exists
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup file logger
        self._file_logger = logging.getLogger("audit")
        self._file_logger.setLevel(logging.INFO)
        
        # Add file handler for daily logs
        self._setup_file_handler()
    
    def _setup_file_handler(self) -> None:
        """Setup daily rotating file handler."""
        today = date.today().isoformat()
        log_file = self.log_dir / f"audit-{today}.log"
        
        # Remove existing handlers
        self._file_logger.handlers.clear()
        
        # Add file handler
        handler = logging.FileHandler(log_file)
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        ))
        self._file_logger.addHandler(handler)
    
    def log(
        self,
        user_id: Optional[int],
        action: str,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None
    ) -> None:
        """
        Log an audit entry.
        
        Args:
            user_id: User ID (None for anonymous/system actions)
            action: Action type (e.g., 'login', 'chat', 'create_user')
            details: Additional details as dict
            ip_address: Client IP address
            resource_type: Resource type (e.g., 'user', 'skill', 'session')
            resource_id: Resource ID
        """
        # Log to database
        self.db.log_audit(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            ip_address=ip_address
        )
        
        # Log to file
        log_entry = {
            "user_id": user_id,
            "action": action,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "details": details,
            "ip_address": ip_address,
            "timestamp": datetime.utcnow().isoformat()
        }
        self._file_logger.info(json.dumps(log_entry))
    
    def log_login(self, user_id: int, success: bool, ip_address: Optional[str] = None) -> None:
        """Log login attempt."""
        self.log(
            user_id=user_id,
            action="login",
            details={"success": success},
            ip_address=ip_address
        )
    
    def log_logout(self, user_id: int, ip_address: Optional[str] = None) -> None:
        """Log logout."""
        self.log(
            user_id=user_id,
            action="logout",
            ip_address=ip_address
        )
    
    def log_chat(self, user_id: int, session_id: str, message_preview: Optional[str] = None) -> None:
        """Log chat message."""
        self.log(
            user_id=user_id,
            action="chat",
            resource_type="session",
            resource_id=session_id,
            details={"message_preview": message_preview[:100] if message_preview else None}
        )
    
    def log_api_key_usage(self, user_id: int, expires_in: Optional[int] = None) -> None:
        """Log API key usage."""
        self.log(
            user_id=user_id,
            action="token_by_api_key",
            details={"expires_in": expires_in}
        )
    
    def log_admin_action(
        self,
        admin_user_id: int,
        action: str,
        target_user_id: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log admin action."""
        self.log(
            user_id=admin_user_id,
            action=f"admin_{action}",
            resource_type="user",
            resource_id=str(target_user_id) if target_user_id else None,
            details=details
        )
    
    def log_resource_action(
        self,
        user_id: int,
        action: str,
        resource_type: str,
        resource_name: str,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log shared resource action."""
        self.log(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_name,
            details=details
        )
    
    def query(
        self,
        user_id: Optional[int] = None,
        action: Optional[str] = None,
        resource_type: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        page: int = 1,
        limit: int = 50
    ) -> List[AuditLog]:
        """
        Query audit logs.
        
        Args:
            user_id: Filter by user ID
            action: Filter by action type
            resource_type: Filter by resource type
            start_date: Filter by start date
            end_date: Filter by end date
            page: Page number
            limit: Results per page
        
        Returns:
            List of audit logs
        """
        return self.db.query_audit_logs(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            start_date=datetime.combine(start_date, datetime.min.time()) if start_date else None,
            end_date=datetime.combine(end_date, datetime.max.time()) if end_date else None,
            page=page,
            limit=limit
        )
    
    def cleanup_old_logs(self) -> int:
        """
        Clean up old log files beyond retention period.
        
        Returns:
            Number of files deleted
        """
        deleted = 0
        cutoff_date = date.today() - self.retention_days
        
        for log_file in self.log_dir.glob("audit-*.log"):
            try:
                # Extract date from filename
                file_date_str = log_file.stem.replace("audit-", "")
                file_date = date.fromisoformat(file_date_str)
                
                if file_date < cutoff_date:
                    log_file.unlink()
                    deleted += 1
            except ValueError:
                # Skip files with invalid date format
                continue
        
        return deleted


# ============================================================================
# Audit Logger Singleton
# ============================================================================

_logger_instance: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    """Get audit logger instance."""
    global _logger_instance
    
    if _logger_instance is None:
        _logger_instance = AuditLogger()
    
    return _logger_instance