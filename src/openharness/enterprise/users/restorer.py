"""
OpenHarness Enterprise - Session Restorer

会话恢复器 - 从数据库恢复完整会话上下文
"""

from __future__ import annotations

from typing import Optional, Dict, Any, List
from pathlib import Path

from openharness.enterprise.storage.database import (
    get_database, Session, Message
)
from openharness.enterprise.users.workspace import get_user_workspace_path
from openharness.enterprise.users.memory import get_memory_manager


class SessionRestorer:
    """
    会话恢复器（用户隔离版本）
    
    功能：
    - 从数据库恢复当前用户的完整会话上下文
    - 重建 system_prompt
    - 恢复对话历史
    
    隔离保证：
    - 查询必须带上 user_id 条件
    - 验证会话归属后再返回数据
    """
    
    def __init__(self, user_id: int):
        """
        初始化会话恢复器
        
        Args:
            user_id: 当前用户 ID（必须，从 JWT 解析）
        """
        if user_id is None or user_id <= 0:
            raise ValueError("user_id is required for SessionRestorer")
        
        self.user_id = user_id
        self.db = get_database()
        self.workspace = get_user_workspace_path(user_id)
    
    def restore_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        恢复完整会话
        
        [隔离] 步骤：
        1. 查询时验证 user_id
        2. 验证会话属于当前用户
        3. 只返回属于当前用户的数据
        
        Args:
            session_id: 会话 ID
        
        Returns:
            恢复的会话数据，或 None（无权限）
        """
        # 1. [隔离] 获取会话信息时验证 user_id
        session = self.db.get_session(session_id)
        
        # [隔离] 验证会话属于当前用户
        if not session or session.user_id != self.user_id:
            return None
        
        # 2. 获取消息历史
        messages = self.db.get_session_messages(session_id)
        
        # 3. 重建 system_prompt（如果之前保存过）
        system_prompt = session.system_prompt or self._build_system_prompt(session)
        
        # 4. 重建完整上下文
        return {
            "session": session,
            "messages": messages,
            "system_prompt": system_prompt,
            "model": session.model or "glm-5",
            "session_key": session.session_key,
        }
    
    def _build_system_prompt(self, session: Session) -> str:
        """
        重建系统提示词
        
        组合顺序：
        1. Base System Prompt
        2. Soul (人设)
        3. Identity (身份)
        4. User Profile (用户画像)
        5. Memory (记忆)
        """
        parts = []
        
        # 1. Base prompt
        parts.append("你是一个有帮助的 AI 助手。")
        
        # 2. Soul
        soul_path = self.workspace / "soul.md"
        if soul_path.exists():
            parts.append(f"# Agent Soul\n\n{soul_path.read_text(encoding='utf-8')}")
        
        # 3. Identity
        identity_path = self.workspace / "identity.md"
        if identity_path.exists():
            content = identity_path.read_text(encoding="utf-8")
            # 只有非空模板才加载
            if not content.strip().endswith("自动填充"):
                parts.append(f"# Agent Identity\n\n{content}")
        
        # 4. User Profile
        user_path = self.workspace / "user.md"
        if user_path.exists():
            content = user_path.read_text(encoding="utf-8")
            if not content.strip().endswith("自动学习并填充"):
                parts.append(f"# User Profile\n\n{content}")
        
        # 5. Memory
        memory_mgr = get_memory_manager(self.user_id)
        memory_context = memory_mgr.build_memory_context(include_daily=True)
        if memory_context:
            parts.append(f"# Memory\n\n{memory_context}")
        
        return "\n\n".join(parts)
    
    def get_resumable_sessions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        获取可恢复的会话列表
        
        Returns:
            会话信息列表 [{"session_id": "...", "title": "...", "updated_at": ...}]
        """
        sessions = self.db.get_user_sessions(self.user_id, limit=limit)
        
        result = []
        for session in sessions:
            result.append({
                "session_id": session.id,
                "title": session.title or "Untitled",
                "message_count": session.message_count,
                "updated_at": session.updated_at.isoformat() if session.updated_at else None,
                "has_context": bool(session.system_prompt),
            })
        
        return result


# ============================================================================
# 工厂函数
# ============================================================================

def get_session_restorer(user_id: int) -> SessionRestorer:
    """获取会话恢复器"""
    return SessionRestorer(user_id)