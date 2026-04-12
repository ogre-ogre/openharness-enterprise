# OpenHarness Enterprise 配置管理方案

## 概述

本文档定义 OpenHarness Enterprise 的全局配置管理规范，将硬编码的配置项抽取为可配置项，通过 `.env` 文件或环境变量进行管理。

---

## 一、配置项清单

### 1.1 应用基础配置

| 配置项 | 环境变量 | 默认值 | 说明 |
|--------|---------|--------|------|
| 企业根目录 | `OH_ENTERPRISE_ROOT` | `~/.oh-enterprise` | 数据存储根目录 |
| 服务器端口 | `OH_PORT` | 8000 | API 服务端口 |
| 服务器地址 | `OH_HOST` | 0.0.0.0 | 监听地址 |
| 调试模式 | `OH_DEBUG` | false | 是否开启调试 |

### 1.2 JWT 认证配置

| 配置项 | 环境变量 | 默认值 | 说明 |
|--------|---------|--------|------|
| JWT 过期时间 | `OH_JWT_EXPIRE_HOURS` | 24 | JWT Token 有效期（小时） |
| JWT 密钥 | `OH_JWT_SECRET` | (自动生成) | JWT 签名密钥 |

### 1.3 LLM 配置

| 配置项 | 环境变量 | 默认值 | 说明 |
|--------|---------|--------|------|
| LLM 提供商 | `OH_PROVIDER` | anthropic | 可选: anthropic, openai, openai-compatible, bailian, zhipu, deepseek |
| API Key | `OH_API_KEY` | - | LLM API 密钥 |
| API 地址 | `OH_BASE_URL` | - | API 端点地址（可选） |
| 模型名称 | `OH_MODEL` | claude-3-5-sonnet-20241022 | 使用的模型 |
| 最大 Token | `OH_MAX_TOKENS` | 4096 | 单次请求最大 Token 数 |
| 温度参数 | `OH_TEMPERATURE` | 0.7 | 生成多样性 (0-2) |

### 1.4 记忆管理配置

| 配置项 | 环境变量 | 默认值 | 说明 |
|--------|---------|--------|------|
| 知识外置阈值 | `OH_KNOWLEDGE_THRESHOLD` | 2000 | 超过此字符数外置到单独文件 |
| 每日记忆保留数 | `OH_DAILY_MEMORY_LIMIT` | 7 | 读取最近 N 天的每日记忆 |
| 最近记忆保留数 | `OH_RECENT_MEMORY_LIMIT` | 3 | System Prompt 中包含的最近记忆天数 |

### 1.5 执行限制配置

| 配置项 | 环境变量 | 默认值 | 说明 |
|--------|---------|--------|------|
| 工具调用最大次数 | `OH_MAX_ITERATIONS` | 5 | 单次对话中工具调用上限 |
| 命令执行超时 | `OH_TOOL_TIMEOUT` | 30 | 命令执行超时时间（秒） |
| 文件读取行数限制 | `OH_FILE_READ_LIMIT` | 100 | 单次读取文件的最大行数 |

### 1.6 Meditate 定时任务配置

| 配置项 | 环境变量 | 默认值 | 说明 |
|--------|---------|--------|------|
| 执行时间-小时 | `OH_MEDITATE_HOUR` | 3 | 每日执行时间（小时） |
| 执行时间-分钟 | `OH_MEDITATE_MINUTE` | 0 | 每日执行时间（分钟） |
| 任务超时时间 | `OH_MEDITATE_TIMEOUT` | 60 | 单个用户Meditate超时（秒） |

### 1.7 日志配置

| 配置项 | 环境变量 | 默认值 | 说明 |
|--------|---------|--------|------|
| 日志目录 | `OH_LOG_DIR` | `{enterprise_root}/logs` | 日志文件目录 |
| 调试日志文件 | `OH_DEBUG_LOG` | `{enterprise_root}/memory_debug.log` | 调试日志路径 |

---

## 二、.env 文件模板

创建 `.env` 文件放置在 `~/.oh-enterprise/.env`：

```bash
# =============================================================================
# OpenHarness Enterprise 环境配置
# =============================================================================
# 此文件放置在 ~/.oh-enterprise/.env
# 或者项目根目录下的 .env 文件
# =============================================================================

# -----------------------------------------------------------------------------
# 应用基础配置
# -----------------------------------------------------------------------------

# 企业数据根目录（可选，默认 ~/.oh-enterprise）
# OH_ENTERPRISE_ROOT=~/.oh-enterprise

# API 服务器配置（可选，默认 8000）
# OH_PORT=8000
# OH_HOST=0.0.0.0

# 调试模式（可选，默认 false）
# OH_DEBUG=false

# -----------------------------------------------------------------------------
# JWT 认证配置
# -----------------------------------------------------------------------------

# JWT 过期时间（小时）（可选，默认 24）
# OH_JWT_EXPIRE_HOURS=24

# JWT 签名密钥（可选，未设置时自动生成随机密钥）
# OH_JWT_SECRET=your-secret-key-here

# -----------------------------------------------------------------------------
# LLM 配置（必须配置）
# -----------------------------------------------------------------------------

# LLM 提供商: anthropic, openai, openai-compatible, bailian, zhipu, deepseek
OH_PROVIDER=anthropic

# API Key（必须配置）
OH_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxx

# API 地址（可选，部分提供商需要）
# OH_BASE_URL=https://api.anthropic.com

# 模型名称（可选）
# OH_MODEL=claude-3-5-sonnet-20241022

# 最大 Token 数（可选，默认 4096）
# OH_MAX_TOKENS=4096

# 温度参数 0-2（可选，默认 0.7）
# OH_TEMPERATURE=0.7

# -----------------------------------------------------------------------------
# 记忆管理配置
# -----------------------------------------------------------------------------

# 知识外置阈值（字符数），超过此长度保存到单独文件（可选，默认 2000）
# OH_KNOWLEDGE_THRESHOLD=2000

# 每日记忆保留天数（可选，默认 7）
# OH_DAILY_MEMORY_LIMIT=7

# System Prompt 中包含的最近记忆天数（可选，默认 3）
# OH_RECENT_MEMORY_LIMIT=3

# -----------------------------------------------------------------------------
# 执行限制配置
# -----------------------------------------------------------------------------

# 工具调用最大次数（可选，默认 5）
# OH_MAX_ITERATIONS=5

# 命令执行超时秒数（可选，默认 30）
# OH_TOOL_TIMEOUT=30

# 文件读取行数限制（可选，默认 100）
# OH_FILE_READ_LIMIT=100

# -----------------------------------------------------------------------------
# Meditate 定时任务配置
# -----------------------------------------------------------------------------

# 每日执行时间（可选，默认 3:00）
# OH_MEDITATE_HOUR=3
# OH_MEDITATE_MINUTE=0

# 单个用户 Meditate 超时秒数（可选，默认 60）
# OH_MEDITATE_TIMEOUT=60

# -----------------------------------------------------------------------------
# 日志配置
# -----------------------------------------------------------------------------

# 日志目录（可选）
# OH_LOG_DIR=~/.oh-enterprise/logs

# 调试日志路径（可选）
# OH_DEBUG_LOG=~/.oh-enterprise/memory_debug.log
```

---

## 三、统一配置管理类

创建统一的配置管理模块：

```python
# src/openharness/enterprise/config/settings.py

"""
OpenHarness Enterprise - 统一配置管理

所有配置项在此集中管理，支持从环境变量或 .env 文件加载。
代码中使用默认值确保在没有配置时也能正常运行。
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional
from functools import lru_cache


class Settings:
    """
    全局配置类
    
    使用方式：
        from openharness.enterprise.config.settings import get_settings
        settings = get_settings()
        
        # 访问配置
        settings.max_tokens
        settings.enterprise_root
    """
    
    # =========================================================================
    # 应用基础配置
    # =========================================================================
    
    @property
    def enterprise_root(self) -> Path:
        """企业根目录"""
        root = os.getenv("OH_ENTERPRISE_ROOT", "").strip()
        if root:
            return Path(root).expanduser()
        return Path.home() / ".oh-enterprise"
    
    @property
    def port(self) -> int:
        """服务器端口"""
        return int(os.getenv("OH_PORT", "8000"))
    
    @property
    def host(self) -> str:
        """服务器地址"""
        return os.getenv("OH_HOST", "0.0.0.0")
    
    @property
    def debug(self) -> bool:
        """调试模式"""
        return os.getenv("OH_DEBUG", "false").lower() == "true"
    
    # =========================================================================
    # JWT 认证配置
    # =========================================================================
    
    @property
    def jwt_expire_hours(self) -> int:
        """JWT 过期时间（小时）"""
        return int(os.getenv("OH_JWT_EXPIRE_HOURS", "24"))
    
    @property
    def jwt_secret(self) -> Optional[str]:
        """JWT 签名密钥"""
        return os.getenv("OH_JWT_SECRET")
    
    # =========================================================================
    # LLM 配置
    # =========================================================================
    
    @property
    def provider(self) -> str:
        """LLM 提供商"""
        return os.getenv("OH_PROVIDER", "anthropic")
    
    @property
    def api_key(self) -> Optional[str]:
        """API Key"""
        return os.getenv("OH_API_KEY")
    
    @property
    def base_url(self) -> Optional[str]:
        """API 地址"""
        return os.getenv("OH_BASE_URL")
    
    @property
    def model(self) -> str:
        """模型名称"""
        return os.getenv("OH_MODEL", "claude-3-5-sonnet-20241022")
    
    @property
    def max_tokens(self) -> int:
        """最大 Token 数"""
        return int(os.getenv("OH_MAX_TOKENS", "4096"))
    
    @property
    def temperature(self) -> float:
        """温度参数"""
        return float(os.getenv("OH_TEMPERATURE", "0.7"))
    
    # =========================================================================
    # 记忆管理配置
    # =========================================================================
    
    @property
    def knowledge_threshold(self) -> int:
        """知识外置阈值（字符数）"""
        return int(os.getenv("OH_KNOWLEDGE_THRESHOLD", "2000"))
    
    @property
    def daily_memory_limit(self) -> int:
        """每日记忆保留天数"""
        return int(os.getenv("OH_DAILY_MEMORY_LIMIT", "7"))
    
    @property
    def recent_memory_limit(self) -> int:
        """最近记忆保留天数"""
        return int(os.getenv("OH_RECENT_MEMORY_LIMIT", "3"))
    
    # =========================================================================
    # 执行限制配置
    # =========================================================================
    
    @property
    def max_iterations(self) -> int:
        """工具调用最大次数"""
        return int(os.getenv("OH_MAX_ITERATIONS", "5"))
    
    @property
    def tool_timeout(self) -> int:
        """命令执行超时（秒）"""
        return int(os.getenv("OH_TOOL_TIMEOUT", "30"))
    
    @property
    def file_read_limit(self) -> int:
        """文件读取行数限制"""
        return int(os.getenv("OH_FILE_READ_LIMIT", "100"))
    
    # =========================================================================
    # Meditate 定时任务配置
    # =========================================================================
    
    @property
    def meditate_hour(self) -> int:
        """每日执行时间（小时）"""
        return int(os.getenv("OH_MEDITATE_HOUR", "3"))
    
    @property
    def meditate_minute(self) -> int:
        """每日执行时间（分钟）"""
        return int(os.getenv("OH_MEDITATE_MINUTE", "0"))
    
    @property
    def meditate_timeout(self) -> int:
        """Meditate 任务超时（秒）"""
        return int(os.getenv("OH_MEDITATE_TIMEOUT", "60"))
    
    # =========================================================================
    # 日志配置
    # =========================================================================
    
    @property
    def log_dir(self) -> Path:
        """日志目录"""
        log = os.getenv("OH_LOG_DIR", "").strip()
        if log:
            return Path(log).expanduser()
        return self.enterprise_root / "logs"
    
    @property
    def debug_log(self) -> Path:
        """调试日志路径"""
        debug = os.getenv("OH_DEBUG_LOG", "").strip()
        if debug:
            return Path(debug).expanduser()
        return self.enterprise_root / "memory_debug.log"


# 全局单例
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """获取配置实例（单例）"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reload_settings() -> Settings:
    """重新加载配置"""
    global _settings
    _settings = Settings()
    return _settings
```

---

## 四、代码修改指南

### 4.1 修复 memory_debug.log 硬编码

**修改文件**: `src/openharness/enterprise/channels/webchat.py`

```python
# 修改前
with open('C:/Users/20171/.oh-enterprise/memory_debug.log', 'a', encoding='utf-8') as f:

# 修改后
from openharness.enterprise.config.settings import get_settings

settings = get_settings()
debug_log = settings.debug_log
debug_log.parent.mkdir(parents=True, exist_ok=True)
with open(debug_log, 'a', encoding='utf-8') as f:
```

### 4.2 使用配置类获取阈值

**修改文件**: `src/openharness/enterprise/users/meditate.py`

```python
# 修改前
KNOWLEDGE_THRESHOLD = 2000

# 修改后
from openharness.enterprise.config.settings import get_settings

@property
def knowledge_threshold(self) -> int:
    return get_settings().knowledge_threshold
```

### 4.3 使用配置类获取执行限制

**修改文件**: `src/openharness/enterprise/channels/webchat.py`

```python
# 修改前
max_iterations = 5

# 修改后
from openharness.enterprise.config.settings import get_settings

max_iterations = get_settings().max_iterations
```

### 4.4 使用配置类获取 Meditate 时间

**修改文件**: `src/openharness/enterprise/server.py`

```python
# 修改前
scheduler.add_job(
    _run_meditate_daily,
    'cron',
    hour=3,
    minute=0,
    id='meditate_daily'
)

# 修改后
from openharness.enterprise.config.settings import get_settings

settings = get_settings()
scheduler.add_job(
    _run_meditate_daily,
    'cron',
    hour=settings.meditate_hour,
    minute=settings.meditate_minute,
    id='meditate_daily'
)
```

---

## 五、配置加载顺序

配置按以下优先级加载（从高到低）：

1. **环境变量** - 最高优先级
2. **`.env` 文件** - 次优先级
3. **代码默认值** - 最低优先级（保底）

```python
# 加载逻辑示例
def get_enterprise_root() -> Path:
    # 1. 优先使用环境变量
    env_val = os.getenv("OH_ENTERPRISE_ROOT")
    if env_val:
        return Path(env_val).expanduser()
    
    # 2. 检查 .env 文件
    env_file = Path.home() / ".oh-enterprise" / ".env"
    if env_file.exists():
        # 解析 .env 文件
        ...
    
    # 3. 使用默认值
    return Path.home() / ".oh-enterprise"
```

---

## 六、验证清单

修改完成后，请验证以下项目：

- [ ] `memory_debug.log` 不再使用硬编码路径
- [ ] 所有阈值配置可通过环境变量修改
- [ ] 不配置任何环境变量时程序能正常启动（使用默认值）
- [ ] `.env` 文件模板已创建并放置到正确位置
- [ ] 所有新配置项都有中文注释

---

*文档版本: v1.0 | 最后更新: 2026-04-11*