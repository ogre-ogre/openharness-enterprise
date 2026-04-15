"""
OpenHarness Enterprise - 统一配置管理

所有配置项在此集中管理，支持从环境变量或 .env 文件加载。
代码中使用默认值确保在没有配置时也能正常运行。

配置优先级（从高到低）：
1. 环境变量
2. .env 文件
3. 代码默认值（保底）
"""

from __future__ import annotations

import os
import json
from pathlib import Path
from typing import Optional


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
    
    def __init__(self):
        """初始化配置，加载 .env 文件"""
        self._load_env_file()
    
    def _load_env_file(self) -> None:
        """加载 .env 文件"""
        # 搜索 .env 文件位置
        env_paths = [
            Path.home() / ".oh-enterprise" / ".env",
            Path.cwd() / ".env",
            Path.cwd() / ".env.local",
        ]
        
        for env_path in env_paths:
            if env_path.exists():
                self._parse_env_file(env_path)
                break
    
    def _parse_env_file(self, env_path: Path) -> None:
        """解析 .env 文件"""
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    # 跳过注释和空行
                    if not line or line.startswith("#"):
                        continue
                    
                    # 解析 KEY=VALUE 格式
                    if "=" in line:
                        key, value = line.split("=", 1)
                        key = key.strip()
                        value = value.strip()
                        
                        # 只在环境变量未设置时设置
                        if key not in os.environ:
                            os.environ[key] = value
        except Exception:
            pass  # 忽略解析错误
    
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
        return self.enterprise_root / "memory_debug_log"
    
    # =========================================================================
    # 便捷方法
    # =========================================================================
    
    def ensure_directories(self) -> None:
        """确保必要的目录存在"""
        self.enterprise_root.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.debug_log.parent.mkdir(parents=True, exist_ok=True)


# 全局单例
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """获取配置实例（单例）"""
    global _settings
    if _settings is None:
        _settings = Settings()
        _settings.ensure_directories()
    return _settings


def reload_settings() -> Settings:
    """重新加载配置"""
    global _settings
    _settings = Settings()
    _settings.ensure_directories()
    return _settings