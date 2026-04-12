"""
OpenHarness Enterprise - Learning Engine

自学习引擎 - 从对话中提取用户信息并更新模板文件
"""

from __future__ import annotations

import re
import json
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime

from openharness.enterprise.storage.database import get_database
from openharness.enterprise.users.workspace import get_user_workspace_path
from openharness.enterprise.users.memory import get_memory_manager


class LearningEngine:
    """
    自学习引擎（用户隔离版本）
    
    功能：
    - 从对话中提取用户信息
    - 更新 identity.md 和 user.md
    - 首次对话完成后删除 BOOTSTRAP.md
    
    隔离保证：
    - 所有文件操作限定在用户工作区内
    """
    
    # 需要识别的用户信息模式
    USER_INFO_PATTERNS = {
        "name": [
            r"我叫(.+?)(?:\s|,|，|$)",
            r"我姓(.+?)(?:\s|,|，|$)",
            r"你可以叫我(.+?)(?:\s|,|，|$)",
            r"称呼我(.+?)(?:\s|,|，|$)",
        ],
        "timezone": [
            r"我在(.+?)时区",
            r"时区是(.+?)(?:\s|,|，|$)",
            r"(.+?)时区",
        ],
        "project": [
            r"在做(.+?)项目",
            r"主要做(.+?)",
            r"忙(.+?)项目",
            r"从事(.+?)工作",
            r"职业是(.+?)",
        ],
        "preference": [
            r"我喜欢(.+?)",
            r"我偏好(.+?)",
            r"希望(.+?)回答",
            r"期望(.+?)",
        ],
    }
    
    def __init__(self, user_id: int):
        """
        初始化学习引擎
        
        Args:
            user_id: 当前用户 ID（必须）
        """
        if user_id is None or user_id <= 0:
            raise ValueError("user_id is required for LearningEngine")
        
        self.user_id = user_id
        self.workspace = get_user_workspace_path(user_id)
        self.memory_mgr = get_memory_manager(user_id)
    
    # =========================================================================
    # 信息提取
    # =========================================================================
    
    def extract_user_info(self, messages: List[Dict]) -> Dict[str, Any]:
        """
        从对话历史中提取用户信息
        
        Args:
            messages: 对话消息列表 [{"role": "user", "content": "..."}]
        
        Returns:
            提取到的信息 {"name": "...", "timezone": "...", ...}
        """
        extracted = {}
        
        for msg in messages:
            if msg.get("role") != "user":
                continue
            
            content = msg.get("content", "")
            
            # 提取各类信息
            for key, patterns in self.USER_INFO_PATTERNS.items():
                if key in extracted:
                    continue  # 已提取过
                
                for pattern in patterns:
                    match = re.search(pattern, content)
                    if match:
                        extracted[key] = match.group(1).strip()
                        break
        
        return extracted
    
    # =========================================================================
    # 更新模板文件
    # =========================================================================
    
    def update_identity(self, assistant_name: str = "", style: str = "") -> bool:
        """
        更新 identity.md
        
        Args:
            assistant_name: AI 名称
            style: 交流风格
        
        Returns:
            是否更新成功
        """
        identity_path = self.workspace / "identity.md"
        
        if not identity_path.exists():
            return False
        
        content = identity_path.read_text(encoding="utf-8")
        
        # 更新各字段
        if assistant_name:
            content = re.sub(
                r"(- \*\*名称\*\*: ).*",
                f"- **名称**: {assistant_name}",
                content
            )
        
        if style:
            content = re.sub(
                r"(- \*\*交流风格\*\*: ).*",
                f"- **交流风格**: {style}",
                content
            )
        
        identity_path.write_text(content, encoding="utf-8")
        return True
    
    def update_user_profile(self, user_info: Dict[str, Any]) -> bool:
        """
        更新 user.md
        
        Args:
            user_info: 提取的用户信息
        
        Returns:
            是否更新成功
        """
        user_path = self.workspace / "user.md"
        
        if not user_path.exists():
            return False
        
        content = user_path.read_text(encoding="utf-8")
        updates = []
        
        if "name" in user_info:
            content = re.sub(
                r"(- \*\*姓名\*\*: ).*",
                f"- **姓名**: {user_info['name']}",
                content
            )
            # 也更新称呼
            content = re.sub(
                r"(- \*\*称呼\*\*: ).*",
                f"- **称呼**: {user_info['name']}",
                content
            )
            updates.append("name")
        
        if "timezone" in user_info:
            content = re.sub(
                r"(- \*\*时区\*\*: ).*",
                f"- **时区**: {user_info['timezone']}",
                content
            )
            updates.append("timezone")
        
        if "project" in user_info:
            content = re.sub(
                r"(- \*\*主要项目\*\*: ).*",
                f"- **主要项目**: {user_info['project']}",
                content
            )
            updates.append("project")
        
        if "preference" in user_info:
            content = re.sub(
                r"(- \*\*期望的回答风格\*\*: ).*",
                f"- **期望的回答风格**: {user_info['preference']}",
                content
            )
            updates.append("preference")
        
        if updates:
            user_path.write_text(content, encoding="utf-8")
            return True
        
        return False
    
    def complete_bootstrap(self) -> bool:
        """
        完成 bootstrap 流程 - 删除 BOOTSTRAP.md
        
        Returns:
            是否删除成功
        """
        bootstrap_path = self.workspace / "BOOTSTRAP.md"
        
        if bootstrap_path.exists():
            bootstrap_path.unlink()
            return True
        
        return False
    
    # =========================================================================
    # 首次对话学习
    # =========================================================================
    
    def learn_from_first_conversation(self, messages: List[Dict]) -> Dict[str, Any]:
        """
        从首次对话中学习
        
        Args:
            messages: 对话消息列表
        
        Returns:
            学习结果
        """
        result = {
            "user_info": {},
            "identity_updated": False,
            "user_profile_updated": False,
            "bootstrap_completed": False
        }
        
        # 1. 提取用户信息
        user_info = self.extract_user_info(messages)
        result["user_info"] = user_info
        
        # 2. 更新 user.md
        if user_info:
            result["user_profile_updated"] = self.update_user_profile(user_info)
        
        # 3. 完成 bootstrap
        result["bootstrap_completed"] = self.complete_bootstrap()
        
        return result


# ============================================================================
# 工厂函数
# ============================================================================

def get_learning_engine(user_id: int) -> LearningEngine:
    """获取学习引擎实例"""
    if user_id is None or user_id <= 0:
        raise ValueError("user_id is required and must be positive")
    return LearningEngine(user_id)