"""
OpenHarness Enterprise - User Context

User runtime context for Agent Engine.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, List, Dict, Any

from pydantic import BaseModel

from openharness.enterprise.storage.database import User, get_database
from openharness.enterprise.users.workspace import (
    WorkspaceManager,
    get_workspace_manager,
    get_shared_root
)


# ============================================================================
# User Context Model
# ============================================================================

class UserContext(BaseModel):
    """
    User runtime context for Agent Engine.
    
    This is injected into the Agent Engine to provide:
    - User memory path
    - User soul (personality)
    - Available skills (personal + shared)
    - User preferences
    - Memory context (from MEMORY.md + daily memories)
    """
    
    user_id: int
    username: str
    display_name: Optional[str] = None
    role: str = "user"
    
    # Paths
    workspace_path: str
    memory_path: str
    soul_path: str
    skills_path: Optional[str] = None
    downloads_path: str = ""  # [新增] 默认文件生成路径
    
    # Content
    soul: str = ""
    identity: str = ""      # [新增] AI 身份
    user_profile: str = ""  # [新增] 用户画像
    memory: str = ""        # [新增] 记忆内容
    bootstrap: str = ""      # [新增] 首次启动引导
    
    # Available resources
    available_skills: List[str] = []
    available_plugins: List[str] = []
    
    # User preferences
    preferences: Dict[str, Any] = {}
    
    class Config:
        arbitrary_types_allowed = True


# ============================================================================
# Context Loader
# ============================================================================

class ContextLoader:
    """
    Load and build user context from workspace.
    """
    
    def __init__(self):
        self.workspace_manager = get_workspace_manager()
        self.db = get_database()
    
    def load_context(self, user: User) -> UserContext:
        """
        Load user context.
        
        Args:
            user: User object
        
        Returns:
            UserContext with all user data loaded
        """
        workspace_path = self.workspace_manager.get_workspace_path(user.id)
        config = self.workspace_manager.get_workspace_config(user.id)
        
        # Load soul
        soul = self._load_file(config.soul_path)
        
        # Load preferences
        preferences = self._load_json(workspace_path / "config" / "preferences.json")
        
        # [新增] Load memory context
        memory = self._load_memory_context(user.id)
        
        # [新增] Load identity and user profile
        identity = self._load_file(workspace_path / "identity.md")
        user_profile = self._load_file(workspace_path / "user.md")
        bootstrap = self._load_file(workspace_path / "BOOTSTRAP.md")
        
        # [新增] Parse downloads path from user.md
        downloads_path = self._parse_downloads_path(user_profile, workspace_path)
        
        # Ensure downloads directory exists
        downloads_dir = Path(downloads_path)
        downloads_dir.mkdir(parents=True, exist_ok=True)
        
        # Get available skills
        personal_skills = self._scan_skills(workspace_path / "skills")
        shared_skills = self._get_shared_skills_for_user(user.id)
        
        # Get available plugins
        personal_plugins = self._scan_plugins(workspace_path / "plugins")
        shared_plugins = self._get_shared_plugins_for_user(user.id)
        
        return UserContext(
            user_id=user.id,
            username=user.username,
            display_name=user.display_name,
            role=user.role,
            workspace_path=str(workspace_path),
            memory_path=config.memory_path,
            soul_path=config.soul_path,
            skills_path=str(workspace_path / "skills"),
            downloads_path=downloads_path,  # [新增]
            soul=soul,
            identity=identity,       # [新增]
            user_profile=user_profile,  # [新增]
            memory=memory,
            bootstrap=bootstrap,      # [新增]
            available_skills=personal_skills + shared_skills,
            available_plugins=personal_plugins + shared_plugins,
            preferences=preferences
        )
    
    def _load_memory_context(self, user_id: int) -> str:
        """
        [新增] Load memory context for user.
        
        Loads:
        - Long-term memory (MEMORY.md)
        - Recent daily memories (last 7 days)
        
        Returns:
            Combined memory context string
        """
        from openharness.enterprise.users.memory import get_memory_manager
        
        memory_mgr = get_memory_manager(user_id)
        
        # Build memory context (long-term + recent daily)
        return memory_mgr.build_memory_context(include_daily=True)
    
    def _parse_downloads_path(self, user_profile: str, workspace_path: Path) -> str:
        """
        [新增] Parse downloads path from user.md content.
        
        Looks for line like:
        - **默认下载路径**: /path/to/downloads
        
        If not found, returns default: workspace_path / "downloads"
        """
        import re
        
        # Default path
        default_path = str(workspace_path / "downloads")
        
        if not user_profile:
            return default_path
        
        # Try to parse the downloads path from markdown
        pattern = r"-\s*\*?\*?默认下载路径\*?\*?:\s*(.+?)(?:\n|$)"
        match = re.search(pattern, user_profile)
        
        if match:
            parsed_path = match.group(1).strip()
            # Remove trailing comment (括号内容)
            parsed_path = re.sub(r'\s*（.*?）\s*$', '', parsed_path)
            parsed_path = parsed_path.strip()
            
            # If it's a relative path, resolve against workspace
            if parsed_path and not Path(parsed_path).is_absolute():
                # Check if it starts with workspace path prefix
                if parsed_path.startswith(str(workspace_path)):
                    return parsed_path
                else:
                    # Relative path - resolve against workspace
                    return str(workspace_path / parsed_path)
            
            return parsed_path if parsed_path else default_path
        
        return default_path
    
    def _load_file(self, path: str | Path) -> str:
        """Load file content."""
        try:
            return Path(path).read_text(encoding="utf-8")
        except FileNotFoundError:
            return ""
    
    def _load_json(self, path: str | Path) -> Dict[str, Any]:
        """Load JSON file."""
        import json
        try:
            content = Path(path).read_text(encoding="utf-8")
            return json.loads(content)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    def _scan_skills(self, skills_path: Path) -> List[str]:
        """Scan skills directory for available skills."""
        skills = []
        
        if skills_path.exists():
            for skill_dir in skills_path.iterdir():
                if skill_dir.is_dir() and (skill_dir / "SKILL.md").exists():
                    skills.append(skill_dir.name)
        
        return skills
    
    def _scan_plugins(self, plugins_path: Path) -> List[str]:
        """Scan plugins directory for available plugins."""
        plugins = []
        
        if plugins_path.exists():
            for plugin_dir in plugins_path.iterdir():
                if plugin_dir.is_dir():
                    plugins.append(plugin_dir.name)
        
        return plugins
    
    def _get_shared_skills_for_user(self, user_id: int) -> List[str]:
        """Get shared skills available to user."""
        shared_skills_path = get_shared_root() / "skills"
        skills = []
        
        if shared_skills_path.exists():
            for skill_dir in shared_skills_path.iterdir():
                if skill_dir.is_dir() and (skill_dir / "SKILL.md").exists():
                    # Check if user has permission
                    if self._user_can_access_resource(user_id, "skill", skill_dir.name):
                        skills.append(skill_dir.name)
        
        return skills
    
    def _get_shared_plugins_for_user(self, user_id: int) -> List[str]:
        """Get shared plugins available to user."""
        shared_plugins_path = get_shared_root() / "plugins"
        plugins = []
        
        if shared_plugins_path.exists():
            for plugin_dir in shared_plugins_path.iterdir():
                if plugin_dir.is_dir():
                    # Check if user has permission
                    if self._user_can_access_resource(user_id, "plugin", plugin_dir.name):
                        plugins.append(plugin_dir.name)
        
        return plugins
    
    def _user_can_access_resource(self, user_id: int, resource_type: str, resource_name: str) -> bool:
        """Check if user can access shared resource."""
        return self.db.user_can_access(user_id, resource_type, resource_name)


# ============================================================================
# Context Loader Instance
# ============================================================================

_context_loader: Optional[ContextLoader] = None


def get_context_loader() -> ContextLoader:
    """Get context loader instance."""
    global _context_loader
    
    if _context_loader is None:
        _context_loader = ContextLoader()
    
    return _context_loader


def load_user_context(user: User) -> UserContext:
    """
    Convenience function to load user context.
    
    Args:
        user: User object
    
    Returns:
        UserContext
    """
    return get_context_loader().load_context(user)