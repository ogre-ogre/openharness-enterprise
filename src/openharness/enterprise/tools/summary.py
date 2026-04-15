"""
OpenHarness Enterprise - 工具摘要生成模块

为工具调用生成简短摘要，用于两阶段调用的第二阶段上下文。
"""

from __future__ import annotations

import json
from typing import Dict, Any, Callable, Optional


# 工具摘要模板映射
# 每个模板是一个 lambda 函数，接收 {"params": {...}, "output": {...}} 结构
SUMMARY_TEMPLATES: Dict[str, Callable[[Dict], str]] = {
    "read_file": lambda r: f"读取了 {r['params'].get('path', 'unknown')} 文件"
        + (f"（{r['output'].get('total_lines', 'N/A')}行）" if isinstance(r['output'], dict) and 'total_lines' in r['output'] else ""),
    
    "write_file": lambda r: f"写入了 {r['params'].get('path', 'unknown')} 文件"
        + f"（{len(r['params'].get('content', ''))}字符）",
    
    "edit_file": lambda r: f"编辑了 {r['params'].get('path', 'unknown')} 文件",
    
    "list_files": lambda r: f"列出了 {r['params'].get('path', 'unknown')} 目录"
        + (f"下的 {len(r['output']) if isinstance(r['output'], list) else '若干'} 个文件" if r['output'] else ""),
    
    "search_in_file": lambda r: f"在 {r['params'].get('path', 'unknown')} 中搜索 '{r['params'].get('keyword', 'unknown')}'"
        + (f"，找到 {r['output'].get('matches_found', 0)} 处匹配" if isinstance(r['output'], dict) else ""),
    
    "delete_file": lambda r: f"删除了 {r['params'].get('path', 'unknown')}",
    
    "execute_command": lambda r: f"执行命令：{r['params'].get('command', 'unknown')[:50]}"
        + ("..." if len(r['params'].get('command', '')) > 50 else ""),
    
    "rest_api_call": lambda r: f"调用 API：{r['params'].get('method', 'GET')} {r['params'].get('url', 'unknown')[:30]}"
        + ("..." if len(r['params'].get('url', '')) > 30 else ""),
    
    "fetch_url": lambda r: f"获取了 {r['params'].get('url', 'unknown')[:30]}"
        + ("..." if len(r['params'].get('url', '')) > 30 else "") + " 的内容",
    
    "search_web": lambda r: f"搜索了 '{r['params'].get('query', 'unknown')}'"
        + (f"，返回 {r['params'].get('count', 5)} 条结果" if r['params'].get('count') else ""),
}


def generate_template_summary(tool_name: str, params: Dict[str, Any], result: Dict[str, Any]) -> str:
    """
    使用模板生成工具摘要。
    
    如果工具不在模板映射中，返回默认摘要。
    
    Args:
        tool_name: 工具名称
        params: 工具参数
        result: 工具执行结果
    
    Returns:
        摘要字符串（不超过 100 字）
    """
    if tool_name in SUMMARY_TEMPLATES:
        try:
            summary = SUMMARY_TEMPLATES[tool_name]({"params": params, "output": result})
            # 限制长度
            if len(summary) > 100:
                summary = summary[:100] + "..."
            return summary
        except Exception as e:
            # 模板执行失败，返回默认摘要
            return f"执行了 {tool_name} 工具（摘要生成失败）"
    
    # 没有模板，返回默认摘要
    return f"执行了 {tool_name} 工具"


def truncate_content(content: Any, max_length: int = 200) -> str:
    """
    截断内容并添加提示。
    
    用于存储到 process_logs 时截断工具返回结果。
    
    Args:
        content: 原始内容（可以是 dict, list, str）
        max_length: 最大长度
    
    Returns:
        截断后的字符串
    """
    # 处理不同类型
    if isinstance(content, dict):
        content_str = json.dumps(content, ensure_ascii=False)
    elif isinstance(content, list):
        # 列表只取前 10 项
        truncated_list = content[:10]
        content_str = json.dumps(truncated_list, ensure_ascii=False)
        if len(content) > 10:
            content_str += f" ... (共 {len(content)} 项，已截断)"
    elif content is None:
        return ""
    else:
        content_str = str(content)
    
    # 截断
    if len(content_str) <= max_length:
        return content_str
    
    return content_str[:max_length] + f"... (已截断，共 {len(content_str)} 字)"


def format_error_summary(tool_name: str, error: str) -> str:
    """
    格式化错误摘要。
    
    Args:
        tool_name: 工具名称
        error: 错误信息
    
    Returns:
        错误摘要
    """
    # 截断错误信息
    error_short = error[:50] if len(error) > 50 else error
    return f"{tool_name} 执行失败：{error_short}"


def build_phase_one_summary(tool_summaries: list) -> str:
    """
    构建第一阶段的摘要上下文，用于第二阶段。
    
    Args:
        tool_summaries: 工具摘要列表 [{"tool": "...", "summary": "..."}, ...]
    
    Returns:
        格式化的摘要文本
    """
    if not tool_summaries:
        return "没有执行工具调用。"
    
    lines = []
    for i, item in enumerate(tool_summaries, 1):
        tool_name = item.get("tool", "unknown")
        summary = item.get("summary", "执行完成")
        lines.append(f"{i}. [{tool_name}] {summary}")
    
    return "\n".join(lines)


# 单元测试
if __name__ == "__main__":
    print("=== 工具摘要生成测试 ===")
    
    # 测试用例
    test_cases = [
        ("read_file", {"path": "/config.py"}, {"total_lines": 500, "content": "..."}),
        ("write_file", {"path": "/output.txt", "content": "Hello World"}, {}),
        ("execute_command", {"command": "npm install axios lodash react"}, {"exit_code": 0}),
        ("search_in_file", {"path": "/readme.md", "keyword": "API"}, {"matches_found": 3}),
        ("unknown_tool", {"param": "value"}, {"result": "ok"}),
    ]
    
    for tool_name, params, result in test_cases:
        summary = generate_template_summary(tool_name, params, result)
        print(f"工具: {tool_name}")
        print(f"参数: {json.dumps(params, ensure_ascii=False)}")
        print(f"摘要: {summary}")
        print()
    
    # 测试截断
    long_content = "这是一段很长的内容..." * 100
    truncated = truncate_content(long_content, 200)
    print(f"截断测试:")
    print(f"原长度: {len(long_content)}")
    print(f"截断后: {len(truncated)} 字")
    print(f"内容: {truncated[:50]}...")
    
    # 测试摘要构建
    tool_summaries = [
        {"tool": "read_file", "summary": "读取了 config.py 文件（500行）"},
        {"tool": "execute_command", "summary": "执行命令：npm install"},
    ]
    context = build_phase_one_summary(tool_summaries)
    print(f"\n摘要上下文:\n{context}")