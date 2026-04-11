"""
OpenHarness Enterprise - Workspace Manager

User workspace initialization and management.
"""

from __future__ import annotations

import json
import shutil
from datetime import date
from pathlib import Path
from typing import Optional, List

from pydantic import BaseModel

from openharness.enterprise.storage.database import User, get_database


# ============================================================================
# Workspace Paths
# ============================================================================

def get_enterprise_root() -> Path:
    """Get enterprise root directory."""
    return Path.home() / ".oh-enterprise"


def get_users_root() -> Path:
    """Get users root directory."""
    return get_enterprise_root() / "users"


def get_shared_root() -> Path:
    """Get shared resources root directory."""
    return get_enterprise_root() / "shared"


def get_user_workspace_path(user_id: int) -> Path:
    """Get user workspace directory path."""
    return get_users_root() / str(user_id)


# ============================================================================
# Workspace Config
# ============================================================================

class UserWorkspaceConfig(BaseModel):
    """User workspace configuration."""
    memory_path: str
    soul_path: str
    sessions_path: str
    config_path: str
    skills_path: str


# ============================================================================
# Workspace Manager
# ============================================================================

class WorkspaceManager:
    """
    User workspace manager.
    
    Features:
    - Workspace initialization
    - Directory structure creation
    - Default file templates
    """
    
    def __init__(self):
        self.users_root = get_users_root()
        self.shared_root = get_shared_root()
        
        # Ensure directories exist
        self.users_root.mkdir(parents=True, exist_ok=True)
        self.shared_root.mkdir(parents=True, exist_ok=True)
        
        # Initialize shared directories
        self._init_shared_dirs()
    
    def _init_shared_dirs(self) -> None:
        """Initialize shared resource directories."""
        for subdir in ["skills", "plugins", "templates"]:
            (self.shared_root / subdir).mkdir(exist_ok=True)
    
    def init_workspace(self, user: User) -> Path:
        """
        Initialize user workspace.
        
        Creates:
        - memory/ directory
        - sessions/ directory
        - config/ directory
        - skills/ directory (empty)
        - soul.md file
        - MEMORY.md file
        
        Args:
            user: User object
        
        Returns:
            Workspace path
        """
        workspace_path = get_user_workspace_path(user.id)
        
        # Create directories
        (workspace_path / "memory").mkdir(parents=True, exist_ok=True)
        (workspace_path / "sessions").mkdir(exist_ok=True)
        (workspace_path / "config").mkdir(exist_ok=True)
        (workspace_path / "skills").mkdir(exist_ok=True)
        
        # Create default files
        self._create_default_soul(workspace_path, user)
        self._create_default_memory(workspace_path, user)
        self._create_default_config(workspace_path, user)
        
        return workspace_path
    
    def _create_default_soul(self, workspace_path: Path, user: User) -> None:
        """Create default soul.md file."""
        soul_path = workspace_path / "soul.md"
        
        if not soul_path.exists():
            content = f"""# SOUL.md - {user.display_name or user.username} 的 Agent

## 身份

你是 {user.display_name or user.username} 的 AI 助手。

## 核心原则

- 做真正有用的人，而不是表演有用的人
- 在提问前先尝试自己解决
- 通过能力赢得信任
- 私密的事情保持私密

---

*此文件可以个性化定制，修改后会影响 Agent 的行为风格。*
"""
            soul_path.write_text(content, encoding="utf-8")
    
    def _create_default_memory(self, workspace_path: Path, user: User) -> None:
        """Create default MEMORY.md file."""
        memory_path = workspace_path / "memory" / "MEMORY.md"
        
        if not memory_path.exists():
            content = f"""# MEMORY.md - 长期记忆

## 用户信息

- **用户名**: {user.username}
- **显示名**: {user.display_name or user.username}
- **创建时间**: {user.created_at or "N/A"}

---

*此文件记录重要信息、决策和值得记忆的内容。*
"""
            memory_path.write_text(content, encoding="utf-8")
    
    def _create_default_config(self, workspace_path: Path, user: User) -> None:
        """Create default user config files."""
        config_dir = workspace_path / "config"
        
        # preferences.json
        preferences_path = config_dir / "preferences.json"
        if not preferences_path.exists():
            preferences = {
                "theme": "default",
                "output_style": "markdown",
                "show_tool_calls": True,
                "show_thinking": False
            }
            preferences_path.write_text(json.dumps(preferences, indent=2), encoding="utf-8")
        
        # provider.json (user can override global provider)
        provider_path = config_dir / "provider.json"
        if not provider_path.exists():
            provider = {
                "use_global": True,
                "model": None
            }
            provider_path.write_text(json.dumps(provider, indent=2), encoding="utf-8")
    
    def get_workspace_config(self, user_id: int) -> UserWorkspaceConfig:
        """
        Get user workspace configuration.
        
        Args:
            user_id: User ID
        
        Returns:
            Workspace config
        """
        workspace_path = get_user_workspace_path(user_id)
        
        return UserWorkspaceConfig(
            memory_path=str(workspace_path / "memory"),
            soul_path=str(workspace_path / "soul.md"),
            sessions_path=str(workspace_path / "sessions"),
            config_path=str(workspace_path / "config"),
            skills_path=str(workspace_path / "skills")
        )
    
    def get_workspace_path(self, user_id: int) -> Path:
        """Get user workspace path."""
        return get_user_workspace_path(user_id)
    
    def workspace_exists(self, user_id: int) -> bool:
        """Check if workspace exists."""
        return get_user_workspace_path(user_id).exists()
    
    def delete_workspace(self, user_id: int) -> None:
        """
        Delete user workspace.
        
        WARNING: This permanently deletes all user data.
        
        Args:
            user_id: User ID
        """
        workspace_path = get_user_workspace_path(user_id)
        
        if workspace_path.exists():
            shutil.rmtree(workspace_path)


# ============================================================================
# Workspace Manager Instance
# ============================================================================

_workspace_manager: Optional[WorkspaceManager] = None


def get_workspace_manager() -> WorkspaceManager:
    """Get workspace manager instance."""
    global _workspace_manager
    
    if _workspace_manager is None:
        _workspace_manager = WorkspaceManager()
    
    return _workspace_manager