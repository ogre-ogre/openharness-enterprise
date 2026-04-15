"""
OpenHarness Enterprise - Memory Trigger Detector

检测用户消息是否需要加载历史记忆。
采用关键词触发策略，避免每次对话都注入记忆。
"""

from __future__ import annotations

import re
from typing import List

from openharness.enterprise.storage.database import get_database


class MemoryTriggerDetector:
    """
    记忆触发检测器
    
    检测用户消息中是否包含需要历史记忆的关键词或模式。
    """
    
    # 明确需要记忆的关键词
    TRIGGER_KEYWORDS = [
        # 时间相关
        "之前", "上次", "上次我们", "之前说过", "之前讨论",
        "上次你说", "上次那个", "之前那个", "记得", "记住",
        
        # 引用相关
        "那个项目", "那个问题", "那个需求", "那个文档",
        "那个功能", "那个bug", "那个错误",
        
        # 继续相关
        "继续", "然后呢", "后来怎样", "接下来",
        
        # 询问历史
        "我们讨论过", "我说过", "你说过", "我们之前",
        
        # 重要标记
        "别忘了", "记住这个", "下次记得",
        
        # [新增] 工作/项目相关关键词（从用户画像提取）
        "任务", "调度", "配置", "版本", 
        "分析", "报表", "数据", "结果",
        "系统", "项目", "工程", "代码",
        "网络", "电路", "设备", "网元",
        "Job", "job", "Handler", "handler",
        
        # [新增] 询问/帮助关键词
        "怎么做", "怎么处理", "帮我", "帮帮我",
        "查一下", "找一下", "看一下", "分析一下",
    ]
    
    # 模式匹配（正则）
    TRIGGER_PATTERNS = [
        r"那个\w+",
        r"上次\w+",
        r"之前\w+",
        r"继续\w+",
        r"记得\w+",
        r"怎么\w+",        # [新增]
        r"帮我\w+",       # [新增]
        r"\w+任务",       # [新增] 以任务结尾
        r"\w+分析",       # [新增] 以分析结尾
        r"\w+调度",       # [新增] 以调度结尾
    ]
    
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.db = get_database()
    
    def should_load_memory(self, message: str) -> bool:
        """
        判断是否需要加载记忆
        
        Args:
            message: 用户当前消息
        
        Returns:
            True 如果需要加载记忆
        """
        if not message:
            return False
        
        message_lower = message.lower()
        
        # 1. 检查明确触发词
        for keyword in self.TRIGGER_KEYWORDS:
            if keyword in message_lower:
                return True
        
        # 2. 模式匹配
        for pattern in self.TRIGGER_PATTERNS:
            if re.search(pattern, message):
                return True
        
        # 3. 检查是否是首次对话（冷启动）
        if self._is_first_conversation():
            return True
        
        return False
    
    def _is_first_conversation(self) -> bool:
        """
        检查是否是用户的首次对话
        
        首次对话时加载记忆，帮助 AI 了解用户
        """
        sessions = self.db.get_user_sessions(self.user_id, limit=1)
        return len(sessions) == 0 or sessions[0].message_count < 2


# ============================================================================
# 工厂函数
# ============================================================================

def get_trigger_detector(user_id: int) -> MemoryTriggerDetector:
    """获取记忆触发检测器"""
    return MemoryTriggerDetector(user_id)