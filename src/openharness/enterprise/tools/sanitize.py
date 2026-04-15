"""
OpenHarness Enterprise - 敏感信息脱敏模块

工具参数存储前进行敏感信息脱敏，防止密码、API Key 等泄露。
"""

from __future__ import annotations

import json
from typing import Dict, Any, List

# 敏感参数字段列表（包含这些关键词的参数会被脱敏）
SENSITIVE_PARAMS: List[str] = [
    "password", "pwd", "pass",
    "api_key", "apikey", "key", "api-key",
    "token", "auth_token", "access_token", "auth-token",
    "secret", "secret_key", "secret-key",
    "credential", "credentials",
    "private_key", "private-key",
    "authorization",
]


def sanitize_params(params: Dict[str, Any]) -> str:
    """
    脱敏工具参数，返回 JSON 字符串。
    
    包含敏感关键词的参数值会被替换为 "******"。
    
    Args:
        params: 工具参数字典
    
    Returns:
        脱敏后的 JSON 字符串
    """
    if not params:
        return "{}"
    
    sanitized = {}
    for key, value in params.items():
        # 检查 key 是否包含敏感关键词
        key_lower = key.lower()
        is_sensitive = any(s in key_lower for s in SENSITIVE_PARAMS)
        
        if is_sensitive:
            sanitized[key] = "******"
        else:
            sanitized[key] = value
    
    return json.dumps(sanitized, ensure_ascii=False)


def is_sensitive_param(key: str) -> bool:
    """
    检查参数名是否为敏感参数。
    
    Args:
        key: 参数名
    
    Returns:
        是否为敏感参数
    """
    key_lower = key.lower()
    return any(s in key_lower for s in SENSITIVE_PARAMS)


def mask_value(value: str, show_prefix: int = 4, show_suffix: int = 0) -> str:
    """
    部分遮蔽敏感值（可选）。
    
    例如：mask_value("abcd1234efgh", 4, 0) -> "abcd****"
    
    Args:
        value: 原始值
        show_prefix: 显示前几位
        show_suffix: 显示后几位
    
    Returns:
        遮蔽后的值
    """
    if not value or len(value) <= show_prefix + show_suffix:
        return "******"
    
    prefix = value[:show_prefix] if show_prefix > 0 else ""
    suffix = value[-show_suffix:] if show_suffix > 0 else ""
    
    return f"{prefix}****{suffix}"


# 单元测试
if __name__ == "__main__":
    # 测试用例
    test_cases = [
        {"path": "/home/user/file.txt", "password": "secret123"},
        {"url": "http://api.example.com", "api_key": "abcd1234efgh"},
        {"command": "npm install", "token": "bearer_token"},
        {"file": "test.py", "normal_param": "value"},
    ]
    
    print("=== 敏感信息脱敏测试 ===")
    for params in test_cases:
        result = sanitize_params(params)
        print(f"输入: {json.dumps(params, ensure_ascii=False)}")
        print(f"输出: {result}")
        print()