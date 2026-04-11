# OpenHarness Enterprise 记忆管理与会话恢复优化方案

## 文档信息

| 项目 | 内容 |
|------|------|
| 文档名称 | 记忆管理与会话恢复优化设计方案 |
| 版本 | v1.4 |
| 目标用户 | 开发工程师 (AI Agent) |
| 状态 | 草稿 |
| 特别说明 | **本项目为多用户服务端隔离架构** |
| 更新内容 | 新增 Meditate 每日反思机制（知识提取、外置、重组织）|

---

## 一、背景与目标

### 1.1 现状分析

当前 `openharness-enterprise` 项目在记忆管理和会话恢复方面存在以下不足：

| 序号 | 问题描述 | 影响 |
|------|----------|------|
| 1 | 缺少 `user.md` 用户画像文件 | AI 无法了解用户偏好，个性化不足 |
| 2 | 缺少 `identity.md` AI 身份定义 | 缺少角色定位和交流风格定义 |
| 3 | 缺少 `BOOTSTRAP.md` 首次启动引导 | 新用户缺少 onboarding 体验 |
| 4 | 会话恢复不完整 | 恢复时缺少 system_prompt 和 model 信息 |
| 5 | 缺少自动学习机制 | 无法自动从对话中提取用户信息 |
| 6 | 记忆功能不完整 | 缺少记忆删除和搜索功能 |

### 1.2 优化目标

1. **完善身份系统**：补充 user.md、identity.md、BOOTSTRAP.md 模板
2. **增强会话恢复**：保存完整的会话上下文，支持完美恢复
3. **实现自学习机制**：AI 自动识别并学习用户信息（**用户隔离**）
4. **补全记忆功能**：增加记忆删除、搜索等能力

### 1.3 多用户隔离架构说明

本项目为**服务端多用户隔离架构**，所有功能设计必须遵循以下隔离原则：

```
┌─────────────────────────────────────────────────────────────────────┐
│                      OpenHarness Enterprise                         │
│                                                                    │
│   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐        │
│   │   用户 A     │    │   用户 B     │    │   用户 C     │        │
│   │  (user_id=1) │    │  (user_id=2) │    │  (user_id=3) │        │
│   └──────┬───────┘    └──────┬───────┘    └──────┬───────┘        │
│          │                   │                   │                 │
│          ▼                   ▼                   ▼                 │
│   ~/.oh-enterprise/users/1/      ~/.oh-enterprise/users/2/         │
│   ├── soul.md                │    ├── soul.md                     │
│   ├── identity.md            │    ├── identity.md                  │
│   ├── user.md                │    ├── user.md                     │
│   ├── memory/                │    ├── memory/                     │
│   └── sessions/              │    └── sessions/                   │
│                              │                                      │
│   [数据完全隔离]              │    [数据完全隔离]                   │
└──────────────────────────────┼────────────────────────────────────┘
                               │
                    ┌──────────┴──────────┐
                    │    共享资源          │
                    │  ~/.oh-enterprise/  │
                    │        /shared/     │
                    │   - skills/         │
                    │   - plugins/        │
                    │   - templates/     │
                    └─────────────────────┘
```

**隔离原则：**

| 隔离维度 | 实现方式 |
|----------|----------|
| **工作区隔离** | 每个用户有独立目录 `~/.oh-enterprise/users/{user_id}/` |
| **会话隔离** | Session 表通过 `user_id` 关联，API 验证用户身份 |
| **记忆隔离** | Memory 文件存储在用户目录内，互不可见 |
| **学习数据隔离** | LearningEngine 基于 `user_id` 初始化，操作独立 |
| **API 访问隔离** | 所有 API 需通过 JWT Token 认证，验证当前用户 |

---

## 二、总体设计

### 2.1 工作区文件结构

优化后的用户工作区结构：

```
~/.oh-enterprise/users/{user_id}/
├── soul.md                 # AI 人设定义（已有，简化版）
├── identity.md             # [新增] AI 身份定义
├── user.md                 # [新增] 用户画像
├── BOOTSTRAP.md            # [新增] 首次启动引导
├── memory/
│   ├── MEMORY.md           # 长期记忆索引
│   ├── YYYY-MM-DD.md       # 每日记忆
│   └── *.md                 # 主题记忆文件
├── sessions/               # 会话历史
│   ├── latest.json         # 最新会话
│   ├── session-{id}.json    # 历史会话
│   └── latest-{key}.json    # 主题会话
├── config/
│   ├── preferences.json    # 用户偏好
│   ├── provider.json       # LLM 配置
│   └── gateway.json        # 网关配置
└── skills/                 # 用户私有 skills
```

### 2.2 系统架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                         用户工作区                                   │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌────────────────────────┐ │
│  │ soul.md │  │identity │  │ user.md │  │ memory/                │ │
│  │         │  │.md      │  │         │  │  - MEMORY.md           │ │
│  └────┬────┘  └────┬────┘  └────┬────┘  │  - YYYY-MM-DD.md      │ │
│       │            │            │        │  - *.md                │ │
│       └────────────┴─────┬──────┘        └────────────────────────┘ │
│                          │                                          │
│  ┌───────────────────────▼──────────────────────────────────────┐   │
│  │               ContextBuilder (上下文构建器)                    │   │
│  │  - build_soul_prompt()                                        │   │
│  │  - build_identity_prompt()                                   │   │
│  │  - build_user_prompt()                                        │   │
│  │  - build_memory_prompt()                                      │   │
│  └───────────────────────┬──────────────────────────────────────┘   │
│                          │                                          │
└──────────────────────────┼──────────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────────────┐
│                    System Prompt (组合后的系统提示)                   │
│                                                                      │
│ # Base System Prompt                                                │
│ # ohmo Soul                                                        │
│ # ohmo Identity                                                    │
│ # User Profile                                                      │
│ # ohmo Memory                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 三、详细设计

### 3.1 文件模板定义

#### 3.1.1 soul.md (AI 人设)

```markdown
# SOUL.md - {用户名} 的 Agent

## 身份

你是 {用户名} 的 AI 助手，基于 OpenHarness 构建。

## 核心原则

- 做真正有用的人，而不是表演有用的人
- 在提问前先尝试自己解决
- 通过能力赢得信任
- 私密的事情保持私密

## 交流风格

- 简洁时则简洁，详细时则详细
- 像一位有能力、有品味的伙伴，而不是客服机器人

---

*此文件可以个性化定制，修改后会影响 Agent 的行为风格。*
```

#### 3.1.2 identity.md (AI 身份) [新增]

```markdown
# IDENTITY.md - AI 身份定义

- **名称**: 
- **角色定位**: 
- **交流风格**: 
- **签名特征**: 

*保持简短具体，当对用户有更清晰的认识后更新。*
```

#### 3.1.3 user.md (用户画像) [新增]

```markdown
# USER.md - 关于我的用户

## 基本信息

- **姓名**: 
- **称呼**: 
- **时区**: 
- **语言**: 

## 工作偏好

- **常用项目**: 
- **典型工作时间**: 
- **期望的回答风格**: 
- **决策风格**: 

## 当前上下文

- **主要项目**: 
- **当前优先级**: 
- **常用工具和平台**: 

## 偏好设置

- **通常希望更多**: 
- **容易恼火的事情**: 
- **需要谨慎处理**: 

## 关系笔记

我应该如何为这个用户服务？是什么样的助手关系：
- 简洁干练的操作者
- 深思熟虑的伙伴
- 有组织的办公厅主任
- 冷静的技术伙伴
- 其他：

## 备注

记下太重要而不能忘记但又太小不值得专门建记忆文件的事实。

*记住：学得足够帮助得好，而不是建立档案。*
```

#### 3.1.4 BOOTSTRAP.md (首次启动引导) [新增]

```markdown
# BOOTSTRAP.md - 首次启动

你刚刚在一个全新的个人工作区上线。

你的任务不是审问用户。要自然开始，然后学得足够变得有用。

## 首次对话目标

1. **了解你是谁**
   - 你应该怎么称呼？
   - 什么样的助手关系感觉合适？
   - 你应该有什么风格？

2. **了解用户 essentials**
   - 我应该怎么称呼你？
   - 你在哪个时区？
   - 你最近在做什么？
   - 你最常想要什么帮助？

3. **让工作区变得真实**
   - 更新 `IDENTITY.md`
   - 更新 `USER.md`
   - 如果有什么持久的很重要，写到 `memory/` 里

## 风格

- 不要丢出一堆问卷
- 从一个简单、人性化的开头开始
- 问几个高价值的问题，而不是二十个低价值的问题
- 当用户不确定时提供建议

## 完成时

初始落地完成后，这个文件可以删除。
如果后来消失了，不要假设它应该回来。
```

#### 3.1.5 MEMORY.md (记忆索引)

```markdown
# Memory Index

# 长期记忆

[这里记录重要的、持久的用户偏好和事实]

---

## 最近重要事件

[AI 从每日记忆中合并的重要事件]

---

## 待确认信息

[AI 识别出但需要用户确认的信息]
```

#### 3.1.6 YYYY-MM-DD.md (每日记忆)

```markdown
# {日期} - 日常记录

## 事件

- [HH:MM] 事件描述

## 学到的

- 学到的教训或信息

## 待处理

- 需要跟进的事项
```

### 3.2 数据库扩展

#### 3.2.1 Session 表扩展

```python
# src/openharness/enterprise/storage/database.py

class Session(BaseModel):
    """Chat session model."""
    id: str                      # UUID
    user_id: int                 # 用户 ID
    title: str                   # 会话标题
    message_count: int           # 消息数
    created_at: datetime         # 创建时间
    updated_at: datetime         # 更新时间
    
    # [新增字段]
    system_prompt: Optional[str] = None   # 系统提示词（用于恢复）
    model: Optional[str] = None           # 使用的模型
    session_key: Optional[str] = None     # 会话主题 key
    cwd: Optional[str] = None             # 工作目录
```

#### 3.2.2 Message 表扩展

```python
class Message(BaseModel):
    """Chat message model."""
    id: str                      # UUID
    session_id: str              # 会话 ID
    role: str                    # 'user' | 'assistant' | 'system'
    content: str                 # 消息内容
    
    # [新增字段]
    tool_calls: Optional[str] = None       # 工具调用 JSON
    tool_results: Optional[str] = None      # 工具结果 JSON
    usage: Optional[str] = None            # Token 使用量 JSON
```

### 3.3 自学习机制设计

> **⚠️ 重要：所有自学习功能必须基于 user_id 进行隔离**

#### 3.3.1 隔离设计原则

```
┌─────────────────────────────────────────────────────────────────────┐
│                    自学习用户隔离架构                                 │
└─────────────────────────────────────────────────────────────────────┘

                          用户 A (user_id=1)
                                │
                                ▼
                    ┌─────────────────────┐
                    │  LearningEngine(1)  │
                    │  - workspace: /1/    │
                    │  - memory: /1/memory│
                    │  - 只操作 user_id=1 │
                    └─────────────────────┘
                                │
                          学习数据写入
                    ~/.oh-enterprise/users/1/
                    ├── user.md (用户A的画像)
                    └── memory/ (用户A的记忆)

                          用户 B (user_id=2)
                                │
                                ▼
                    ┌─────────────────────┐
                    │  LearningEngine(2)  │
                    │  - workspace: /2/    │
                    │  - memory: /2/memory│
                    │  - 只操作 user_id=2 │
                    └─────────────────────┘
                                │
                          学习数据写入
                    ~/.oh-enterprise/users/2/
                    ├── user.md (用户B的画像)
                    └── memory/ (用户B的记忆)
```

**隔离规则：**

1. **工厂函数必须传入 user_id**：`get_learning_engine(user_id: int)`
2. **文件路径基于 user_id**：`get_user_workspace_path(user_id)`
3. **数据库操作验证 user_id**：查询时必须带上 `user_id` 条件
4. **API 必须带认证**：从 JWT Token 解析 user_id

#### 3.3.2 学习流程

```
┌─────────────────────────────────────────────────────────────────────┐
│                        对话完成后的学习流程                          │
└─────────────────────────────────────────────────────────────────────┘

                              │
                              ▼
                    ┌─────────────────┐
                    │  收集对话摘要   │
                    └────────┬────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │  信息提取器     │
                    │  (LearningEngine)│
                    └────────┬────────┘
                              │
              ┌───────────────┼───────────────┐
              │               │               │
              ▼               ▼               ▼
      ┌───────────┐   ┌───────────┐   ┌───────────┐
      │ 用户信息  │   │ 偏好信息  │   │ 重要事件  │
      │ (更新     │   │ (更新     │   │ (写入     │
      │  user.md) │   │ memory)   │   │ 每日记忆) │
      └───────────┘   └───────────┘   └───────────┘
              │               │               │
              └───────────────┼───────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │  用户确认(如    │
                    │   需要)         │
                    └─────────────────┘
```

#### 3.3.2 LearningEngine 类设计

```python
# src/openharness/enterprise/users/learning.py [新建]

"""
自学习引擎 - 用户隔离版本

⚠️ 重要：
- 所有方法必须基于 self.user_id 进行操作
- 禁止跨用户访问数据
- API 调用必须验证当前用户身份
"""

from typing import Optional
from pathlib import Path
from datetime import datetime
import re

from openharness.enterprise.users.workspace import get_user_workspace_path
from openharness.enterprise.users.memory import get_memory_manager


class LearningEngine:
    """
    自学习引擎（用户隔离版本）
    
    功能：
    - 从对话中提取当前用户信息
    - 更新当前用户的 user.md
    - 写入当前用户的每日记忆
    - 识别重要信息并合并
    
    隔离保证：
    - 所有文件操作限定在 get_user_workspace_path(user_id) 内
    - 不访问其他用户的数据
    """
    
    # 需要识别的用户信息模式
    USER_INFO_PATTERNS = {
        "name": [
            r"我叫(.+?)(?:\s|,|$)",
            r"我姓(.+?)(?:\s|,|$)",
            r"你可以叫我(.+?)(?:\s|,|$)",
        ],
        "timezone": [
            r"我在(.+?)时区",
            r"时区是(.+?)(?:\s|,|$)",
        ],
        "project": [
            r"在做(.+?)项目",
            r"主要做(.+?)",
            r"忙(.+?)项目",
        ],
        "preference": [
            r"我喜欢(.+?)",
            r"我偏好(.+?)",
            r"最好(.+?)",
        ],
    }
    
    # 需要写入记忆的关键词
    MEMORY_TRIGGERS = [
        "重要", "决策", "记住", "别忘了",
        "下次", "以后", "这类问题",
        "教训", "经验", "注意",
    ]
    
    def __init__(self, user_id: int):
        """
        初始化学习引擎
        
        Args:
            user_id: 当前用户 ID（必须）
        """
        # [隔离验证] user_id 不能为空
        if user_id is None or user_id <= 0:
            raise ValueError("user_id is required for LearningEngine")
        
        self.user_id = user_id
        # [隔离] 工作区路径基于 user_id
        self.workspace = get_user_workspace_path(user_id)
        # [隔离] Memory 管理器基于 user_id
        self.memory_mgr = get_memory_manager(user_id)
    
    # ------------------------------------------------------------------------
    # 信息提取
    # ------------------------------------------------------------------------
    
    def extract_user_info(self, messages: list[dict]) -> dict:
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
            
            # 提取姓名
            for pattern in self.USER_INFO_PATTERNS["name"]:
                match = re.search(pattern, content)
                if match and "name" not in extracted:
                    extracted["name"] = match.group(1).strip()
            
            # 提取时区
            for pattern in self.USER_INFO_PATTERNS["timezone"]:
                match = re.search(pattern, content)
                if match and "timezone" not in extracted:
                    extracted["timezone"] = match.group(1).strip()
            
            # 提取项目
            for pattern in self.USER_INFO_PATTERNS["project"]:
                match = re.search(pattern, content)
                if match and "project" not in extracted:
                    extracted["project"] = match.group(1).strip()
        
        return extracted
    
    def extract_memory_items(self, messages: list[dict]) -> list[str]:
        """
        从对话中提取需要记忆的内容
        
        Returns:
            需要写入记忆的条目列表
        """
        items = []
        
        for msg in messages:
            content = msg.get("content", "")
            
            # 检查是否包含记忆触发词
            for trigger in self.MEMORY_TRIGGERS:
                if trigger in content:
                    # 提取包含触发词的完整句子
                    sentences = content.split("。")
                    for sentence in sentences:
                        if trigger in sentence:
                            items.append(sentence.strip())
                    break
        
        return items
    
    # ------------------------------------------------------------------------
    # 更新用户画像
    # ------------------------------------------------------------------------
    
    def update_user_profile(self, user_info: dict) -> bool:
        """
        更新 user.md 文件
        
        Args:
            user_info: 提取的用户信息
        
        Returns:
            是否更新成功
        """
        user_path = self.workspace / "user.md"
        
        if not user_path.exists():
            return False
        
        content = user_path.read_text(encoding="utf-8")
        
        # 简单更新：如果找到占位符则替换
        updates = []
        
        if "name" in user_info:
            # 更新姓名
            pattern = r"(- \*\*姓名\*\*: ).*"
            if re.search(pattern, content):
                content = re.sub(
                    pattern,
                    r"\g<1>" + user_info["name"],
                    content
                )
                updates.append("name")
        
        if "timezone" in user_info:
            # 更新时区
            pattern = r"(- \*\*时区\*\*: ).*"
            if re.search(pattern, content):
                content = re.sub(
                    pattern,
                    r"\g<1>" + user_info["timezone"],
                    content
                )
                updates.append("timezone")
        
        if "project" in user_info:
            # 更新当前项目
            pattern = r"(- \*\*主要项目\*\*: ).*"
            if re.search(pattern, content):
                content = re.sub(
                    pattern,
                    r"\g<1>" + user_info["project"],
                    content
                )
                updates.append("project")
        
        if updates:
            user_path.write_text(content, encoding="utf-8")
            return True
        
        return False
    
    # ------------------------------------------------------------------------
    # 写入记忆
    # ------------------------------------------------------------------------
    
    def write_to_daily_memory(self, events: list[str]) -> None:
        """
        将事件写入每日记忆
        
        Args:
            events: 需要记录的事件列表
        """
        for event in events:
            self.memory_mgr.append_to_daily(event)
    
    def consolidate_important_events(self) -> None:
        """
        将每日记忆中的重要事件合并到长期记忆
        """
        self.memory_mgr.consolidate_daily_to_memory()


# ============================================================================
# 工厂函数（带用户隔离验证）
# ============================================================================

def get_learning_engine(user_id: int) -> LearningEngine:
    """
    获取学习引擎实例
    
    [隔离] 工厂函数必须传入 user_id
    - 禁止不传 user_id 获取全局实例
    - 禁止使用默认用户 ID
    
    Args:
        user_id: 当前登录用户 ID（从 JWT Token 解析）
    
    Returns:
        当前用户的 LearningEngine 实例
    """
    if user_id is None or user_id <= 0:
        raise ValueError("user_id is required and must be positive")
    return LearningEngine(user_id)
```

### 3.4 会话恢复设计

> **⚠️ 重要：会话恢复必须验证用户身份，防止越权访问**

#### 3.4.1 隔离设计原则

```
┌─────────────────────────────────────────────────────────────────────┐
│                   会话恢复用户隔离架构                                 │
└─────────────────────────────────────────────────────────────────────┘

  请求: POST /api/sessions/{session_id}/restore
  Header: Authorization: Bearer {jwt_token}
                          │
                          ▼
         ┌────────────────────────────────┐
         │  中间件解析 JWT                 │
         │  → 提取 user_id = 1            │
         └────────────────────────────────┘
                          │
                          ▼
         ┌────────────────────────────────┐
         │  SessionRestorer(1)             │
         │  - user_id = 1                  │
         └────────────────────────────────┘
                          │
         ┌────────────────────────────────┐
         │  查询验证:                      │
         │  session.user_id == 1 ?         │
         │  - 是: 返回会话数据             │
         │  - 否: 返回 403 Forbidden       │
         └────────────────────────────────┘
```

**隔离规则：**

1. **API 必须带 JWT Token**：从 Token 解析 user_id
2. **查询必须验证 user_id**：`session.user_id == current_user_id`
3. **返回前二次验证**：确保会话属于当前用户

#### 3.4.2 SessionRestorer 类

```python
# src/openharness/enterprise/users/restorer.py [新建]

"""
会话恢复器 - 用户隔离版本

⚠️ 重要：
- 所有会话查询必须验证 user_id
- 禁止返回其他用户的会话
- API 必须带 JWT 认证
"""

from typing import Optional, List, Dict, Any
from pathlib import Path

from openharness.enterprise.storage.database import (
    get_database, Session, Message
)
from openharness.enterprise.users.workspace import get_user_workspace_path
from openharness.enterprise.users.context import load_user_context
from openharness.enterprise.llm.client import get_llm_client


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
        # [隔离验证]
        if user_id is None or user_id <= 0:
            raise ValueError("user_id is required for SessionRestorer")
        
        self.user_id = user_id
        self.db = get_database()
        self.workspace = get_user_workspace_path(user_id)
    
    def restore_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        恢复完整会话
        
        [隔离] 步骤：
        1. 查询时带上 user_id 条件
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
            # 禁止返回其他用户的会话
            return None
        
        # 2. 获取消息历史
        messages = self.db.get_session_messages(session_id)
        
        # 3. 重建 system_prompt
        system_prompt = self._build_system_prompt(session)
        
        # 4. 重建完整上下文
        return {
            "session": session,
            "messages": messages,
            "system_prompt": system_prompt,
            "model": session.model or "claude-3-5-sonnet-20241022",
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
        parts.append(self._get_base_prompt())
        
        # 2. Soul
        soul_path = self.workspace / "soul.md"
        if soul_path.exists():
            parts.append(f"# Agent Soul\n\n{soul_path.read_text(encoding='utf-8')}")
        
        # 3. Identity
        identity_path = self.workspace / "identity.md"
        if identity_path.exists():
            parts.append(f"# Agent Identity\n\n{identity_path.read_text(encoding='utf-8')}")
        
        # 4. User Profile
        user_path = self.workspace / "user.md"
        if user_path.exists():
            parts.append(f"# User Profile\n\n{user_path.read_text(encoding='utf-8')}")
        
        # 5. Memory
        from openharness.enterprise.users.memory import get_memory_manager
        memory_mgr = get_memory_manager(self.user_id)
        memory_context = memory_mgr.build_memory_context(include_daily=True)
        if memory_context:
            parts.append(f"# Memory\n\n{memory_context}")
        
        return "\n\n".join(parts)
    
    def _get_base_prompt(self) -> str:
        """获取基础系统提示词"""
        return """You are a helpful AI assistant.

You should:
- Be genuinely helpful, not performatively helpful
- Have judgment and explain your reasons plainly
- Be resourceful before asking questions
- Earn trust through competence
- Be careful with anything public, destructive, costly, or user-facing"""
    
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
```

### 3.5 ContextBuilder 增强

```python
# src/openharness/enterprise/users/context.py [修改]

class UserContext(BaseModel):
    """User context model."""
    user_id: int
    username: str
    
    # [新增字段]
    soul: Optional[str] = None        # soul.md 内容
    identity: Optional[str] = None    # identity.md 内容  
    user_profile: Optional[str] = None  # user.md 内容
    
    memory_path: str
    available_skills: List[str] = []
    preferences: dict = {}


def load_user_context(user_id: int, session_id: Optional[str] = None) -> UserContext:
    """
    加载用户上下文（增强版）
    
    [修改] 增加 identity.md 和 user.md 的读取
    """
    db = get_database()
    user = db.get_user(user_id)
    
    workspace = get_user_workspace_path(user_id)
    
    # [新增] 读取 soul, identity, user_profile
    soul = ""
    identity = ""
    user_profile = ""
    
    soul_path = workspace / "soul.md"
    if soul_path.exists():
        soul = soul_path.read_text(encoding="utf-8")
    
    identity_path = workspace / "identity.md"
    if identity_path.exists():
        identity = identity_path.read_text(encoding="utf-8")
    
    user_path = workspace / "user.md"
    if user_path.exists():
        user_profile = user_path.read_text(encoding="utf-8")
    
    return UserContext(
        user_id=user_id,
        username=user.username,
        soul=soul,
        identity=identity,
        user_profile=user_profile,
        memory_path=str(workspace / "memory"),
        available_skills=_scan_skills(workspace / "skills"),
        preferences=_load_preferences(workspace / "config"),
    )


def build_full_system_prompt(context: UserContext, memory_context: str = "") -> str:
    """
    构建完整的系统提示词
    
    [新增] 组合所有上下文组件
    """
    parts = []
    
    # 1. Base prompt
    parts.append("You are a helpful AI assistant.")
    
    # 2. Soul (如果有)
    if context.soul:
        parts.append(f"# Agent Soul\n\n{context.soul}")
    
    # 3. Identity (如果有)
    if context.identity:
        parts.append(f"# Agent Identity\n\n{context.identity}")
    
    # 4. User Profile (如果有)
    if context.user_profile:
        parts.append(f"# User Profile\n\n{context.user_profile}")
    
    # 5. Memory
    if memory_context:
        parts.append(f"# Memory\n\n{memory_context}")
    
    return "\n\n".join(parts)
```

### 3.6 记忆读取机制（关键修复）

> **⚠️ 重要发现：当前实现存在严重缺陷**

当前工程的记忆机制是**只写不读**：
- 对话结束后 AI 会**分析并写入**记忆
- 但**对话过程中 AI 看不到**之前的记忆
- 这导致记忆功能**几乎无效**

#### 3.6.1 问题分析

```
当前机制（错误）：
┌─────────────────────────────────────────────────────────────────────┐
│  用户发送消息                                                        │
│      │                                                              │
│      ▼                                                              │
│  _build_system_prompt() ─────────────────────────┐                  │
│  - 基础身份                                    │                  │
│  - 工具说明                                    │  ← ❌ 没有包含记忆！│
│  - soul                                       │                  │
│      │                                      │                  │
│      ▼                                      │                  │
│  对话进行中 (AI 看不到任何记忆)                │                  │
│      │                                      │                  │
│      ▼ 对话结束                               │                  │
│  _update_memory_smart()                       │                  │
│  - 写入 MEMORY.md ← (只读不写，无效)          │                  │
└────────────────────────────────────────────────┘                  │
```

**但是！记忆也不应该每次都注入**，原因：
1. 上下文长度增加 → token 成本增加
2. 模型注意力分散 → 可能导致回答质量下降
3. 大部分对话不需要历史记忆

#### 3.6.2 优化方案：智能记忆注入策略

推荐采用**按需检索注入**方式，而不是每次都注入：

```
┌─────────────────────────────────────────────────────────────────────┐
│                    智能记忆注入策略                                   │
└─────────────────────────────────────────────────────────────────────┘

用户发送消息
      │
      ▼
┌─────────────────────────────┐
│  记忆触发检测               │
│  (Memory Trigger Detector) │
└────────────┬────────────────┘
             │
    ┌────────┴────────┐
    ▼                 ▼
  需要记忆           不需要
    │                 │
    ▼                 │
┌─────────────────┐   │
│ RAG 检索        │   │
│ 从 MEMORY.md    │   │
│ 相关记忆片段    │   │
└────────┬────────┘   │
         │            │
         ▼            ▼
   注入相关记忆    不注入
   到 system       （正常对话）
   prompt
```

##### 触发条件检测

```python
class MemoryTriggerDetector:
    """记忆触发检测器"""
    
    # 明确需要记忆的关键词
    TRIGGER_KEYWORDS = [
        "之前", "上次", "之前说过", "记得",
        "上次我们", "之前讨论", "记住",
        "我之前", "上次你说", "之前那个",
    ]
    
    # 可能需要记忆的模式
    POSSIBLE_TRIGGERS = [
        r"那个项目", "那个问题", "那个需求",
        r"继续", "然后呢", "后来怎样",
    ]
    
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.memory_mgr = get_memory_manager(user_id)
    
    def should_load_memory(self, message: str) -> bool:
        """
        判断是否需要加载记忆
        
        Args:
            message: 用户当前消息
        
        Returns:
            True 如果需要加载记忆
        """
        message_lower = message.lower()
        
        # 1. 明确触发词
        for keyword in self.TRIGGER_KEYWORDS:
            if keyword in message_lower:
                return True
        
        # 2. 模式匹配
        import re
        for pattern in self.POSSIBLE_TRIGGERS:
            if re.search(pattern, message):
                return True
        
        # 3. 第一次对话（冷启动）
        if self._is_first_conversation():
            return True
        
        return False
    
    def _is_first_conversation(self) -> bool:
        """检查是否是对话开始（需要加载基础信息）"""
        sessions = get_database().get_user_sessions(self.user_id, limit=1)
        return len(sessions) == 0
```

##### RAG 检索（可选进阶）

```python
class MemoryRAG:
    """记忆检索增强生成"""
    
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.memory_mgr = get_memory_manager(user_id)
    
    def retrieve_relevant_memory(self, query: str, top_k: int = 3) -> str:
        """
        从记忆库中检索与当前问题相关的片段
        
        Args:
            query: 用户当前问题
            top_k: 返回top K条
        
        Returns:
            相关的记忆片段
        """
        # 读取所有记忆
        long_term = self.memory_mgr.read_memory()
        daily_memories = self.memory_mgr.read_all_daily(limit=7)
        
        # 简单关键词匹配（生产环境可用 embedding + 向量检索）
        relevant_parts = []
        
        # 1. 长期记忆匹配
        if long_term:
            lines = long_term.split("\n")
            for line in lines:
                if self._is_relevant(line, query):
                    relevant_parts.append(line)
        
        # 2. 每日记忆匹配
        for daily in daily_memories:
            content = daily.get("content", "")
            if self._is_relevant(content, query):
                relevant_parts.append(f"### {daily['date']}\n{content[:200]}")
        
        if not relevant_parts:
            return ""
        
        # 取 top_k
        return "\n\n".join(relevant_parts[:top_k])
    
    def _is_relevant(self, text: str, query: str) -> bool:
        """简单相关性判断（关键词重叠）"""
        query_words = set(query.lower().split())
        text_words = set(text.lower().split())
        return bool(query_words & text_words)  # 有交集
```

##### 修改后的 System Prompt 构建

```python
# src/openharness/enterprise/channels/webchat.py [修改]

class MemoryAwareSystemPromptBuilder:
    """智能系统提示词构建器"""
    
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.trigger_detector = MemoryTriggerDetector(user_id)
        self.rag = MemoryRAG(user_id)
    
    def build(self, user_context: UserContext, user_message: str) -> str:
        """
        构建系统提示词（智能记忆注入）
        
        Args:
            user_context: 用户上下文
            user_message: 用户当前消息（用于判断是否需要记忆）
        """
        parts = []
        
        # 1. 基础身份
        parts.append("你是一个有帮助的 AI 助手。")
        
        # 2. 工具说明
        parts.append(tool_instructions)
        
        # 3. Soul (始终注入，人设必须)
        if user_context.soul:
            parts.append(f"\n\n以下是你的个性化设置：\n{user_context.soul}")
        
        # 4. 智能记忆注入
        if self.trigger_detector.should_load_memory(user_message):
            # RAG 检索相关记忆
            relevant_memory = self.rag.retrieve_relevant_memory(user_message)
            
            if relevant_memory:
                parts.append(f"\n\n## 相关历史记忆\n\n{relevant_memory}")
            else:
                # 没有相关记忆，加载基础记忆
                parts.append(f"\n\n## 历史记忆\n\n{user_context.memory}")
        
        return "\n".join(parts)
```

#### 3.6.3 策略对比

| 策略 | 优点 | 缺点 | 适用场景 |
|------|------|------|---------|
| **每次注入** | 简单实现 | token 成本高，注意力分散 | 不推荐 |
| **关键词触发** | 减少无效注入 | 关键词覆盖不全 | 中等 |
| **RAG 检索** | 精准注入相关记忆 | 实现复杂 | 推荐 |
| **首次对话注入** | 冷启动友好 | 其他场景不适用 | 补充 |

#### 3.6.4 推荐实现路径

1. **Phase 1**: 关键词触发（简单）
2. **Phase 2**: 首次对话 + 关键词双触发
3. **Phase 3**: RAG 检索（进阶）

> **💡 建议**：采用 **Phase 2** 作为初始实现，平衡效果和复杂度。

#### 3.6.5 实现修改

##### 3.6.5.1 修改 _build_system_prompt() 签名

```python
# src/openharness/enterprise/channels/webchat.py [修改]

def _build_system_prompt(
    self, 
    user_context: UserContext,
    user_message: str = ""  # [新增] 用于判断是否需要记忆
) -> str:
    """
    Build system prompt from user context.
    
    [修改] 增加智能记忆注入（按需）
    """
    # ... 原有代码 ...
    
    # [新增] 智能记忆注入
    if user_message:
        should_load = self._should_load_memory(user_message)
        if should_load:
            memory_to_load = self._get_relevant_memory(user_message)
            if memory_to_load:
                parts.append(f"\n\n## 历史记忆\n\n{memory_to_load}")
```

##### 3.6.5.2 调用处修改

```python
# 调用 _build_system_prompt 时传入用户消息
system_prompt = self._build_system_prompt(user_context, message)
```

#### 3.6.6 隔离设计

记忆检索同样需要用户隔离：

```python
# 所有实例基于 user_id 创建
trigger_detector = MemoryTriggerDetector(user_id)
rag = MemoryRAG(user_id)
# 检索结果只包含当前用户的记忆
```

```
正确机制：
┌─────────────────────────────────────────────────────────────────────┐
│  用户发送消息                                                        │
│      │                                                              │
│      ▼                                                              │
│  _build_system_prompt() ──────────────────────────────────────┐   │
│  - 基础身份                                                     │   │
│  - 工具说明                                                     │   │
│  - soul                                                        │   │
│  - ⭐ memory_context (从 MEMORY.md + 每日记忆构建)              │   │
│      │                                                         │   │
│      ▼                                                         │   │
│  对话进行中 (AI 可以看到历史记忆)                                 │   │
│      │                                                         │   │
│      ▼ 对话结束                                                │   │
│  _update_memory_smart()                                          │   │
│  - 更新 MEMORY.md                                                │   │
└──────────────────────────────────────────────────────────────────┘
```

#### 3.6.3 实现修改

##### 3.6.3.1 修改 UserContext 模型

```python
# src/openharness/enterprise/users/context.py [修改]

class UserContext(BaseModel):
    """User runtime context for Agent Engine."""
    
    user_id: int
    username: str
    display_name: Optional[str] = None
    role: str = "user"
    
    # Paths
    workspace_path: str
    memory_path: str
    soul_path: str
    skills_path: Optional[str] = None
    
    # Content
    soul: str = ""
    
    # [新增] 记忆内容
    memory: str = ""          # 从 MEMORY.md + 每日记忆构建的上下文
    
    # Available resources
    available_skills: List[str] = []
    available_plugins: List[str] = []
    
    # User preferences
    preferences: Dict[str, Any] = {}
```

##### 3.6.3.2 修改 ContextLoader.load_context()

```python
# src/openharness/enterprise/users/context.py [修改]

def load_context(self, user: User) -> UserContext:
    """
    加载用户上下文（增强版）
    
    [修改] 增加记忆内容加载
    """
    workspace_path = self.workspace_manager.get_workspace_path(user.id)
    config = self.workspace_manager.get_workspace_config(user.id)
    
    # Load soul
    soul = self._load_file(config.soul_path)
    
    # [新增] Load memory context
    from openharness.enterprise.users.memory import get_memory_manager
    memory_mgr = get_memory_manager(user.id)
    memory_context = memory_mgr.build_memory_context(include_daily=True)
    
    # Load preferences
    preferences = self._load_json(workspace_path / "config" / "preferences.json")
    
    # ... other code ...
    
    return UserContext(
        user_id=user.id,
        username=user.username,
        # ... other fields ...
        soul=soul,
        memory=memory_context,  # [新增]
        available_skills=personal_skills + shared_skills,
        preferences=preferences
    )
```

##### 3.6.3.3 修改 _build_system_prompt()

```python
# src/openharness/enterprise/channels/webchat.py [修改]

def _build_system_prompt(self, user_context: UserContext) -> str:
    """
    Build system prompt from user context.
    
    [修改] 增加 memory 内容
    """
    parts = []
    
    # Base identity
    parts.append("你是一个有帮助的 AI 助手。")
    
    # Tool usage instructions
    parts.append(tool_instructions)
    
    # Add user soul if available
    if user_context.soul:
        parts.append(f"\n\n以下是你的个性化设置：\n{user_context.soul}")
    
    # [新增] Add memory context if available
    if user_context.memory:
        parts.append(f"\n\n## 历史记忆\n\n{user_context.memory}")
    
    return "\n".join(parts)
```

##### 3.6.3.4 刷新记忆（WebSocket 重连时）

```python
# src/openharness/enterprise/channels/webchat.py [修改]

# 在刷新上下文时也要刷新记忆
async def _handle_refresh_command(...):
    fresh_context = load_user_context(user)
    user_context.available_skills = fresh_context.available_skills
    user_context.soul = fresh_context.soul
    user_context.memory = fresh_context.memory  # [新增]
    user_context.preferences = fresh_context.preferences
```

#### 3.6.4 隔离设计

记忆读取同样需要用户隔离：

```python
def load_context(self, user: User) -> UserContext:
    """[隔离] 每个用户只加载自己的记忆"""
    # [隔离] 基于 user.id 构建路径
    memory_mgr = get_memory_manager(user.id)  # 只传 user_id
    memory_context = memory_mgr.build_memory_context()
    # ... memory 只包含当前用户的数据
```

---

## 四、API 设计

> **⚠️ 所有 API 必须带 JWT Token 认证**

### 4.1 新增 API 端点

| 方法 | 路径 | 认证 | 描述 |
|------|------|------|------|
| GET | `/api/context` | ✅ JWT | 获取当前用户完整上下文 |
| PUT | `/api/context/profile` | ✅ JWT | 更新当前用户画像 |
| GET | `/api/context/identity` | ✅ JWT | 获取当前用户 AI 身份 |
| PUT | `/api/context/identity` | ✅ JWT | 更新当前用户 AI 身份 |
| POST | `/api/sessions/{id}/restore` | ✅ JWT | 恢复当前用户的会话 |
| GET | `/api/sessions/resumable` | ✅ JWT | 获取当前用户可恢复的会话列表 |
| POST | `/api/learning/extract` | ✅ JWT | 手动触发当前用户信息提取 |

### 4.2 认证与授权

```python
# API 认证流程示例

from fastapi import Depends
from openharness.enterprise.auth.middleware import get_current_user
from openharness.enterprise.storage.database import User

# 所有 API 依赖注入
async def get_current_user_id(user: User = Depends(get_current_user)) -> int:
    """从 JWT Token 获取当前用户 ID"""
    return user.id

# 示例：获取上下文
@app.get("/api/context")
async def get_context(
    user: User = Depends(get_current_user)  # JWT 认证
):
    """获取当前用户的上下文"""
    # user.id 已经过认证，代表当前登录用户
    restorer = get_session_restorer(user.id)
    ...
```

### 4.3 接口详细设计

#### 4.2.1 获取上下文

```python
# GET /api/context

# Response
{
    "user_id": 1,
    "username": "admin",
    "soul": "...",
    "identity": "...",
    "user_profile": "...",
    "memory": {
        "long_term": "...",
        "recent_daily": [...]
    },
    "preferences": {
        "theme": "default",
        "output_style": "markdown"
    }
}
```

#### 4.2.2 恢复会话

```python
# POST /api/sessions/{session_id}/restore

# Response
{
    "session_id": "xxx",
    "title": "讨论项目A",
    "messages": [
        {"role": "user", "content": "你好"},
        {"role": "assistant", "content": "你好"}
    ],
    "system_prompt": "完整重建的 system prompt",
    "model": "claude-3-5-sonnet-20241022",
    "restored": true
}
```

---

## 五、实现计划

### 5.1 阶段划分

| 阶段 | 任务 | 优先级 |
|------|------|--------|
| Phase 1 | 补充工作区模板文件 (user.md, identity.md, BOOTSTRAP.md) | P0 |
| Phase 2 | 扩展数据库 Session 表字段 | P0 |
| Phase 3 | 实现 ContextBuilder 增强 | P0 |
| Phase 4 | 实现 SessionRestorer 会话恢复 | P1 |
| Phase 5 | 实现 LearningEngine 自学习 | P1 |
| Phase 6 | 新增 API 端点 | P1 |
| Phase 7 | 添加记忆删除/搜索功能 | P2 |
| Phase 8 | 前端界面适配 | P2 |

### 5.2 关键文件修改清单

| 文件路径 | 操作 | 描述 |
|----------|------|------|
| `users/workspace.py` | 修改 | 添加模板文件初始化 |
| `users/context.py` | 修改 | 增强上下文构建 + **记忆读取** |
| `storage/database.py` | 修改 | 扩展 Session 表 |
| `users/learning.py` | 新建 | 自学习引擎 |
| `users/restorer.py` | 新建 | 会话恢复器 |
| `channels/webchat.py` | 修改 | System Prompt **注入记忆内容** |
| `server.py` | 修改 | 添加新 API 路由 |

> **⚠️ 特别注意**：`users/context.py` 和 `channels/webchat.py` 的修改是**关键修复**，解决记忆"只写不读"的问题。

#### 3.6.7 新增智能记忆组件（可选进阶）

| 文件 | 操作 | 描述 |
|------|------|------|
| `users/trigger.py` | 新建 | 记忆触发检测器 |
| `users/rag.py` | 新建 | 记忆 RAG 检索（可选） |
| `users/meditate.py` | 新建 | Meditate 每日反思机制 |

### 3.7 Meditate 机制（记忆反思与整合）

> **💡 灵感来源**：类似 Claude Code 的 dream 机制

#### 3.7.1 设计目标

当前记忆机制的问题：
- 对话后自动写入的记忆是**碎片化**的
- MEMORY.md 会随着时间**越来越长**
- 缺乏**系统性的归纳和整理**

Meditate 机制的目标：
- 定期（每天凌晨）对用户对话进行**系统性总结**
- 将重要内容（操作步骤、知识点、工程备忘）**整合**到长期记忆
- 对**长内容进行外置**：单独保存成知识文件，只在 MEMORY.md 中保存摘要
- **重组织** MEMORY.md，保持其精简可用

#### 3.7.2 整体流程

```
┌─────────────────────────────────────────────────────────────────────┐
│                     Meditate 每日反思机制                            │
└─────────────────────────────────────────────────────────────────────┘

                          ┌─────────────────────┐
                          │  定时任务触发       │
                          │  (每天凌晨 3:00)    │
                          └──────────┬──────────┘
                                     │
                                     ▼
                    ┌────────────────────────────────┐
                    │  收集昨日对话数据              │
                    │  - 从 messages 表读取          │
                    │  - 按 user_id 分组            │
                    └───────────────┬────────────────┘
                                    │
                                    ▼
                    ┌────────────────────────────────┐
                    │  对每个用户的对话进行 Meditate │
                    └───────────────┬────────────────┘
                                    │
           ┌────────────────────────┼────────────────────────┐
           │                        │                        │
           ▼                        ▼                        ▼
    ┌──────────────┐        ┌──────────────┐        ┌──────────────┐
    │ 知识提取     │        │ 知识外置    │        │ 记忆重组     │
    │ - 操作步骤   │        │ - 长内容    │        │ - 去重       │
    │ - 知识点    │        │   → 单独文件  │        │ - 分类整理   │
    │ - 工程备忘  │        │ - 摘要保存  │        │ - 精简压缩   │
    └──────┬───────┘        │   → MEMORY  │        └──────────────┘
           │                └──────────────┘
           ▼
    ┌──────────────────────────────────┐
    │  更新 MEMORY.md                  │
    │  - 合并重要记录                   │
    │  - 添加知识文件引用               │
    └──────────────────────────────────┘
```

#### 3.7.3 Meditate 执行器设计

```python
# src/openharness/enterprise/users/meditate.py [新建]

"""
Meditate 机制 - 每日凌晨执行的记忆反思与整合

功能：
1. 收集昨日对话
2. AI 分析提取关键信息
3. 长内容外置到知识文件
4. 重组织 MEMORY.md
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime, timedelta
import json
import uuid

from openharness.enterprise.storage.database import get_database
from openharness.enterprise.users.workspace import get_user_workspace_path
from openharness.enterprise.users.memory import get_memory_manager
from openharness.enterprise.llm.client import get_llm_client


class MeditateExecutor:
    """
    每日记忆反思执行器
    
    设计原则：
    - 每日凌晨执行（可配置）
    - 按用户隔离处理
    - 知识外置防止 MEMORY.md 过长
    """
    
    # 知识外置阈值（字符数）
    KNOWLEDGE_THRESHOLD = 2000
    
    # 知识文件目录
    KNOWLEDGE_DIR = "knowledge"
    
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.db = get_database()
        self.workspace = get_user_workspace_path(user_id)
        self.memory_mgr = get_memory_manager(user_id)
        self.knowledge_dir = self.workspace / self.KNOWLEDGE_DIR
        self.knowledge_dir.mkdir(parents=True, exist_ok=True)
    
    # =========================================================================
    # 核心执行流程
    # =========================================================================
    
    def execute(self, date: Optional[str] = None) -> Dict[str, Any]:
        """
        执行每日 Meditate
        
        Args:
            date: 要处理的日期（默认昨天），格式 YYYY-MM-DD
        
        Returns:
            执行结果报告
        """
        if date is None:
            # 默认昨天
            date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        
        # 1. 收集昨日对话
        conversations = self._collect_yesterday_conversations(date)
        
        if not conversations:
            return {"status": "skipped", "reason": "no_conversations", "date": date}
        
        # 2. AI 分析提取关键信息
        extracted = self._extract_knowledge(conversations)
        
        # 3. 知识外置（长内容）
        externalized = self._externalize_knowledge(extracted["long_content"])
        
        # 4. 合并到 MEMORY.md
        self._merge_to_memory(
            extracted=extracted,
            externalized=externalized
        )
        
        # 5. 重组织 MEMORY.md
        self._reorganize_memory()
        
        return {
            "status": "success",
            "date": date,
            "conversations_count": len(conversations),
            "knowledge_externalized": len(externalized),
            "memory_updated": True
        }
    
    def _collect_yesterday_conversations(self, date: str) -> List[Dict]:
        """收集指定日期的对话"""
        # 获取该用户指定日期的消息
        cursor = self.db._conn.cursor()
        cursor.execute("""
            SELECT m.id, m.session_id, m.role, m.content, m.created_at
            FROM messages m
            JOIN sessions s ON m.session_id = s.id
            WHERE s.user_id = ?
            AND date(m.created_at) = ?
            ORDER BY m.created_at
        """, (self.user_id, date))
        
        rows = cursor.fetchall()
        
        # 按会话分组
        sessions = {}
        for row in rows:
            session_id = row[1]
            if session_id not in sessions:
                sessions[session_id] = []
            sessions[session_id].append({
                "role": row[2],
                "content": row[3],
                "created_at": row[4]
            })
        
        return sessions
    
    # =========================================================================
    # 知识提取（AI 分析）
    # =========================================================================
    
    def _extract_knowledge(self, conversations: Dict) -> Dict[str, Any]:
        """
        使用 AI 分析对话，提取关键信息
        
        Returns:
            {
                "operations": [...],   # 操作步骤
                "knowledge": [...],     # 知识点
                "notes": [...],         # 工程备忘
                "long_content": [...]   # 需要外置的长内容
            }
        """
        # 构建分析 prompt
        all_content = self._build_conversation_summary(conversations)
        
        analysis_prompt = f"""请分析以下对话记录，提取需要记忆的重要信息：

{all_content}

请按以下格式返回 JSON：
{{
    "operations": [
        {{"title": "操作名称", "steps": ["步骤1", "步骤2"], "context": "应用场景"}}
    ],
    "knowledge": [
        {{"topic": "知识点主题", "summary": "核心要点（不超过100字）", "details": "详细说明（可很长）"}}
    ],
    "notes": [
        {{"content": "备忘内容", "priority": "high/medium/low"}}
    ],
    "long_content": [
        {{"title": "主题", "content": "具体内容（超过2000字）"}}
    ]
}}

只返回 JSON，不要其他内容。"""
        
        # 调用 LLM 分析
        llm_client = get_llm_client()
        messages = [{"role": "user", "content": analysis_prompt}]
        
        result = ""
        import asyncio
        async def call():
            nonlocal result
            async for chunk in llm_client.stream_chat(
                messages=messages,
                system_prompt="你是一个记忆分析助手，专门从对话中提取需要长期保存的信息。只返回JSON格式。"
            ):
                result += chunk
        
        asyncio.run(call())
        
        # 解析 JSON
        import json
        try:
            # 提取 JSON
            start = result.find('{')
            end = result.rfind('}')
            if start != -1 and end != -1:
                return json.loads(result[start:end+1])
        except json.JSONDecodeError:
            pass
        
        return {"operations": [], "knowledge": [], "notes": [], "long_content": []}
    
    def _build_conversation_summary(self, conversations: Dict) -> str:
        """构建对话摘要（截断每条消息）"""
        summary_parts = []
        for session_id, messages in conversations.items():
            for msg in messages:
                content = msg.get("content", "") or ""
                if len(content) > 500:
                    content = content[:500] + "..."
                summary_parts.append(f"[{msg['role']}]: {content}")
        
        return "\n\n".join(summary_parts[:50])  # 最多50条
    
    # =========================================================================
    # 知识外置
    # =========================================================================
    
    def _externalize_knowledge(self, long_contents: List[Dict]) -> List[Dict]:
        """
        将长内容外置到单独的知识文件
        
        Args:
            long_contents: 需要外置的内容列表
        
        Returns:
            外置记录列表 {title, path, summary}
        """
        externalized = []
        
        for item in long_contents:
            content = item.get("content", "")
            if len(content) < self.KNOWLEDGE_THRESHOLD:
                continue
            
            # 生成唯一文件名
            file_id = str(uuid.uuid4())[:8]
            title = item.get("title", "未命名")
            safe_title = "".join(c for c in title if c.isalnum() or c in "-_")[:30]
            filename = f"{safe_title}_{file_id}.md"
            
            # 保存文件
            file_path = self.knowledge_dir / filename
            file_path.write_text(content, encoding="utf-8")
            
            # 生成摘要
            summary = content[:200] + "..." if len(content) > 200 else content
            
            externalized.append({
                "title": title,
                "path": str(file_path.relative_to(self.workspace)),
                "summary": summary
            })
        
        return externalized
    
    # =========================================================================
    # 合并到 MEMORY.md
    # =========================================================================
    
    def _merge_to_memory(
        self, 
        extracted: Dict[str, Any],
        externalized: List[Dict]
    ) -> None:
        """将提取的信息合并到 MEMORY.md"""
        
        # 1. 添加操作步骤
        for op in extracted.get("operations", []):
            content = f"### {op['title']}\n"
            content += f"应用场景：{op.get('context', 'N/A')}\n"
            content += "步骤：\n"
            for i, step in enumerate(op.get("steps", []), 1):
                content += f"{i}. {step}\n"
            
            self.memory_mgr.append_to_memory("操作记录", content)
        
        # 2. 添加知识点（短的直接写入，长的引用外置文件）
        for kw in extracted.get("knowledge", []):
            details = kw.get("details", "")
            if len(details) < self.KNOWLEDGE_THRESHOLD:
                # 短内容直接写入
                content = f"**{kw['topic']}**: {kw.get('summary', '')}\n\n{details}"
            else:
                # 长内容外置
                file_id = str(uuid.uuid4())[:8]
                safe_topic = "".join(c for c in kw['topic'] if c.isalnum() or c in "-_")[:30]
                filename = f"{safe_topic}_{file_id}.md"
                
                (self.knowledge_dir / filename).write_text(details, encoding="utf-8")
                
                content = f"**{kw['topic']}**: {kw.get('summary', '')}\n\n[详细内容](./{self.KNOWLEDGE_DIR}/{filename})"
            
            self.memory_mgr.append_to_memory("知识库", content)
        
        # 3. 添加工程备忘
        for note in extracted.get("notes", []):
            priority = note.get("priority", "medium")
            if priority == "high":
                self.memory_mgr.append_to_memory("重要备忘", f"- {note['content']}")
        
        # 4. 添加外置知识引用
        for ext in externalized:
            ref = f"- **{ext['title']}**: {ext['summary']}\n  [查看详情](./{ext['path']})"
            self.memory_mgr.append_to_memory("知识文件", ref)
    
    # =========================================================================
    # 记忆重组织
    # =========================================================================
    
    def _reorganize_memory(self) -> None:
        """
        重组织 MEMORY.md
        
        - 合并重复内容
        - 精简冗余
        - 按类别整理
        """
        current_content = self.memory_mgr.read_memory()
        
        if not current_content:
            return
        
        # 使用 LLM 重新组织
        reorganization_prompt = f"""请重新组织以下记忆文件，使其更简洁、有条理：

要求：
1. 合并重复内容
2. 删除过时信息
3. 按主题分类
4. 保持每个知识点简洁（不超过100字）
5. 对于长内容，保留摘要并建议外置到单独文件

当前记忆内容：
{current_content}

请返回重构后的记忆内容："""
        
        llm_client = get_llm_client()
        messages = [{"role": "user", "content": reorganization_prompt}]
        
        result = ""
        import asyncio
        async def call():
            nonlocal result
            async for chunk in llm_client.stream_chat(
                messages=messages,
                system_prompt="你是一个记忆整理助手，帮助用户整理和精简记忆。只返回整理后的内容，不要其他解释。"
            ):
                result += chunk
        
        asyncio.run(call())
        
        if result.strip():
            self.memory_mgr.write_memory(result)


# ============================================================================
# 定时任务调度
# ============================================================================

class MeditateScheduler:
    """
    Meditate 定时调度器
    
    使用 croniter 或 APScheduler 实现每日凌晨执行
    """
    
    def __init__(self):
        self.db = get_database()
    
    def run_daily(self) -> Dict[str, Any]:
        """
        每日执行（供定时任务调用）
        
        Returns:
            所有用户的执行结果
        """
        results = {}
        
        # 获取所有活跃用户
        users = self.db.get_all_users()
        
        for user in users:
            try:
                executor = MeditateExecutor(user.id)
                result = executor.execute()
                results[user.id] = result
            except Exception as e:
                results[user.id] = {"status": "error", "message": str(e)}
        
        return results
```

#### 3.7.4 知识文件结构

```
~/.oh-enterprise/users/{user_id}/
├── memory/
│   ├── MEMORY.md              # 长期记忆（精简版）
│   └── YYYY-MM-DD.md          # 每日记忆
├── knowledge/                 # [新增] 知识外置目录
│   ├── 微服务架构设计_abc123.md
│   ├── React组件封装_def456.md
│   └── 数据库优化_ghi789.md
└── ...
```

#### 3.7.5 MEMORY.md 重构示例

**重构前**（可能很长）：
```
# MEMORY.md - 长期记忆

## 重要记录
- [2026-04-01] 用户提到要做微服务架构改造...
- [2026-04-02] 用户讨论了React组件封装的问题...
- [2026-04-10] 用户需要优化数据库查询...

## 操作记录
- 步骤1
- 步骤2
...
（可能有几千字）
```

**重构后**（精简）：
```
# MEMORY.md - 长期记忆

## 重要记录
- [2026-04-01] 微服务架构改造项目启动
- [2026-04-10] 数据库性能优化需求

## 操作记录
- **[微服务搭建]**: [查看详情](./knowledge/微服务搭建_abc123.md)
- **[React组件]**: 封装规范已建立

## 知识库
- **[数据库优化]**: 查询性能提升50% [详情](./knowledge/数据库优化_ghi789.md)

## 知识文件
- *微服务架构设计*: 微服务架构的核心是服务拆分... [查看详情](./knowledge/微服务架构设计_def456.md)
```

#### 3.7.6 定时任务配置

```python
# src/openharness/enterprise/config/scheduler.py [修改]

from apscheduler.schedulers.asyncio import AsyncIOScheduler

# 添加 Meditate 任务
scheduler = AsyncIOScheduler()

# 每天凌晨 3:00 执行
scheduler.add_job(
    run_meditate_daily,
    'cron',
    hour=3,
    minute=0,
    id='meditate_daily'
)

def run_meditate_daily():
    """每日 Meditate 任务入口"""
    from openharness.enterprise.users.meditate import MeditateScheduler
    
    logger.info("Starting daily meditate...")
    scheduler = MeditateScheduler()
    results = scheduler.run_daily()
    logger.info(f"Meditate completed: {results}")
```

或使用 cron：

```bash
# 每天凌晨 3 点执行
0 3 * * * cd /path/to/project && uv run python -m openharness.enterprise.tasks.meditate
```

#### 3.7.7 隔离设计

Meditate 执行必须用户隔离：

```python
class MeditateScheduler:
    def run_daily(self) -> Dict[str, Any]:
        results = {}
        
        # 获取所有活跃用户
        users = self.db.get_all_users()
        
        for user in users:
            # [隔离] 每个用户独立执行
            executor = MeditateExecutor(user.id)  # 必须传 user_id
            result = executor.execute()
            results[user.id] = result
        
        return results
```

#### 3.7.8 新增文件清单

| 文件 | 描述 |
|------|------|
| `users/meditate.py` | Meditate 执行器 + 调度器 |
| `users/knowledge/` | 知识文件外置目录（运行时创建） |

---

## 六、测试要点

### 6.1 功能测试

1. **模板初始化测试**
   - 新用户首次登录时正确创建所有模板文件
   - 已存在用户不重复创建

2. **上下文构建测试**
   - 正确组合所有组件
   - 缺少文件时不影响其他组件

3. **会话恢复测试**
   - 完整恢复历史消息
   - 正确重建 system_prompt

4. **自学习测试**
   - 正确提取用户信息
   - 正确更新 user.md

### 6.2 用户隔离测试（重点）

> **⚠️ 必须测试用户数据隔离**

| 测试项 | 测试方法 |
|--------|----------|
| **跨用户会话访问** | 用户A尝试访问用户B的会话 → 返回 403 |
| **跨用户记忆访问** | 用户A无法读取用户B的 memory 文件 |
| **跨用户学习数据** | 用户A的 learning 只写入用户A的目录 |
| **API 越权** | 不带 Token 或 Token 对应的 user_id 与请求不匹配 → 401/403 |
| **Session 隔离** | 并发请求不同用户的会话 → 数据互不干扰 |

```python
# 测试示例

def test_session_restore_isolation():
    """测试会话恢复的隔离性"""
    
    # 用户A创建会话
    session_a = create_session(user_id=1)
    
    # 用户B尝试恢复用户A的会话
    restorer_b = SessionRestorer(user_id=2)
    result = restorer_b.restore_session(session_a.id)
    
    # 应该返回 None（无权限）
    assert result is None

def test_memory_isolation():
    """测试记忆隔离"""
    
    memory_a = get_memory_manager(user_id=1)
    memory_b = get_memory_manager(user_id=2)
    
    # 各自写入记忆
    memory_a.append_to_daily("用户A的重要信息")
    memory_b.append_to_daily("用户B的重要信息")
    
    # 各自读取
    content_a = memory_a.read_daily()
    content_b = memory_b.read_daily()
    
    # 不应包含对方数据
    assert "用户A" in content_a
    assert "用户B" not in content_a
    assert "用户B" in content_b
    assert "用户A" not in content_b

def test_memory_reading_in_context():
    """测试记忆在对话上下文中被正确加载"""
    
    # 1. 用户A写入记忆
    memory_a = get_memory_manager(user_id=1)
    memory_a.append_to_memory("重要记录", "- 测试项目使用微服务架构")
    
    # 2. 加载上下文
    from openharness.enterprise.users.context import load_user_context
    user = get_database().get_user(1)
    context = load_user_context(user)
    
    # 3. 验证记忆被加载到 context.memory
    assert "测试项目" in context.memory
    assert "微服务架构" in context.memory
    
    # 4. 验证构建的 system prompt 包含记忆
    from openharness.enterprise.channels.webchat import WebChatChannel
    channel = WebChatChannel()
    system_prompt = channel._build_system_prompt(context)
    
    assert "历史记忆" in system_prompt
    assert "微服务架构" in system_prompt
```

### 6.3 边界情况

- 用户工作区不存在
- 模板文件损坏/为空
- 会话消息量巨大
- 多个用户并发操作

---

## 七、附录

### 7.1 文件路径速查（用户隔离版）

| 功能 | 路径 |
|------|------|
| 企业根目录 | `~/.oh-enterprise/` |
| 用户目录（隔离） | `~/.oh-enterprise/users/{user_id}/` |
| 共享资源 | `~/.oh-enterprise/shared/` |
| 记忆目录（隔离） | `~/.oh-enterprise/users/{user_id}/memory/` |
| 会话目录（隔离） | `~/.oh-enterprise/users/{user_id}/sessions/` |

### 7.2 相关配置

- 记忆加载最大文件数: 5 (可配置)
- 每日记忆保留天数: 30 (可配置)
- 重要事件合并频率: 手动触发

### 7.3 用户隔离检查清单

实现时请确保以下隔离点：

- [ ] 所有数据库查询带上 `user_id` 条件
- [ ] 所有文件路径基于 `get_user_workspace_path(user_id)`
- [ ] 所有 API 路由使用 `Depends(get_current_user)` 认证
- [ ] LearningEngine 初始化时验证 `user_id`
- [ ] SessionRestorer 查询时验证 `session.user_id == current_user_id`
- [ ] 工厂函数 `get_learning_engine(user_id)` `get_session_restorer(user_id)` 必须传参
- [ ] 禁止不传 `user_id` 获取全局实例

### 7.4 记忆读取检查清单

实现记忆读取机制时请确保：

- [ ] `UserContext` 模型包含 `memory: str` 字段
- [ ] `load_context()` 调用 `memory_mgr.build_memory_context()`
- [ ] `_build_system_prompt()` 支持智能注入（不是每次都注入）
- [ ] 刷新上下文时同步刷新记忆 (`_handle_refresh_command`)
- [ ] 记忆内容包含长期记忆 (`MEMORY.md`) + 最近每日记忆
- [ ] **推荐**：使用关键词触发或 RAG 方式，而不是每次都注入

---

*文档版本: v1.4 | 最后更新: 2026-04-11 | 更新内容: 新增 Meditate 每日反思机制*