"""
OpenHarness Enterprise - WebChat Channel

WebSocket-based chat channel for web interface.
"""

from __future__ import annotations

import asyncio
import json
import re
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List, AsyncGenerator

from fastapi import WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from openharness.enterprise.storage.database import (
    User, Session, Message,
    get_database
)
from openharness.enterprise.storage.audit import get_audit_logger
from openharness.enterprise.users.context import load_user_context, UserContext
from openharness.enterprise.users.memory import get_memory_manager, MemoryManager
from openharness.enterprise.llm.client import get_llm_client
from openharness.enterprise.config.provider import get_provider_config
from openharness.enterprise.tools.registry import get_tool_registry


# ============================================================================
# Message Protocol
# ============================================================================

class WSMessage(BaseModel):
    """WebSocket message format."""
    type: str  # message, command, resume, text, tool_call, tool_result, thinking, error, done
    payload: Dict[str, Any] = {}


class ClientMessage(BaseModel):
    """Client -> Server message."""
    type: str  # message, command, resume
    payload: Dict[str, Any] = {}
    
    @classmethod
    def from_dict(cls, data: dict) -> "ClientMessage":
        return cls(
            type=data.get("type", "message"),
            payload=data.get("payload", {})
        )


class ServerMessage(BaseModel):
    """Server -> Client message."""
    type: str  # text, tool_call, tool_result, thinking, error, done, session_info
    payload: Dict[str, Any] = {}
    session_id: Optional[str] = None
    timestamp: str = ""
    
    def __init__(self, **data):
        super().__init__(**data)
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()
    
    def to_json(self) -> str:
        return self.json()


# ============================================================================
# Session Manager
# ============================================================================

class SessionManager:
    """
    Manage user chat sessions.
    
    Features:
    - Create new sessions
    - Resume existing sessions
    - Track active WebSocket connections
    """
    
    def __init__(self):
        self.db = get_database()
        self._active_connections: Dict[str, WebSocket] = {}  # session_id -> websocket
        self._session_users: Dict[str, int] = {}  # session_id -> user_id
    
    def create_session(self, user_id: int, title: Optional[str] = None) -> Session:
        """Create a new session."""
        session_id = str(uuid.uuid4())
        return self.db.create_session(
            session_id=session_id,
            user_id=user_id,
            title=title
        )
    
    def get_or_create_session(
        self,
        user_id: int,
        session_id: Optional[str] = None,
        title: Optional[str] = None
    ) -> Session:
        """Get existing session or create new one."""
        if session_id:
            session = self.db.get_session(session_id)
            if session and session.user_id == user_id:
                return session
        
        # Create new session
        return self.create_session(user_id, title)
    
    def get_user_sessions(self, user_id: int, limit: int = 50) -> List[Session]:
        """Get user's sessions."""
        return self.db.get_user_sessions(user_id, limit=limit)
    
    def register_connection(self, session_id: str, websocket: WebSocket, user_id: int) -> None:
        """Register active WebSocket connection."""
        self._active_connections[session_id] = websocket
        self._session_users[session_id] = user_id
    
    def unregister_connection(self, session_id: str) -> None:
        """Unregister WebSocket connection."""
        self._active_connections.pop(session_id, None)
        self._session_users.pop(session_id, None)
    
    def get_connection(self, session_id: str) -> Optional[WebSocket]:
        """Get WebSocket connection for session."""
        return self._active_connections.get(session_id)
    
    def is_session_active(self, session_id: str) -> bool:
        """Check if session has active connection."""
        return session_id in self._active_connections


# ============================================================================
# Message Store
# ============================================================================

class MessageStore:
    """Store and retrieve chat messages."""
    
    def __init__(self):
        self.db = get_database()
    
    def save_message(
        self,
        session_id: str,
        role: str,
        content: str,
        tokens_used: Optional[int] = None
    ) -> Message:
        """Save a message to database."""
        message_id = str(uuid.uuid4())
        return self.db.create_message(
            message_id=message_id,
            session_id=session_id,
            role=role,
            content=content,
            tokens_used=tokens_used
        )
    
    def get_session_messages(self, session_id: str, limit: int = 100) -> List[Message]:
        """Get messages for a session."""
        return self.db.get_session_messages(session_id, limit)
    
    def get_conversation_history(
        self,
        session_id: str,
        limit: int = 50
    ) -> List[Dict[str, str]]:
        """Get conversation history in LLM format."""
        messages = self.get_session_messages(session_id, limit)
        return [
            {"role": msg.role, "content": msg.content}
            for msg in messages
            if msg.content
        ]


# ============================================================================
# Agent Engine Interface
# ============================================================================

class AgentEngineInterface:
    """
    Interface to Agent Engine.
    
    This is a placeholder that simulates agent responses.
    In production, this would connect to the actual OpenHarness engine.
    """
    
    # Tool call patterns - LLM may return these formats
    TOOL_PATTERNS = {
        "read_file": r"read_file\s*<file_path>([^<]+)</file_path>",
        "search_in_file": r"search_in_file\s*<file_path>([^<]+)</file_path>\s*<keyword>([^<]+)</keyword>",
        "read_file_range": r"read_file_range\s*<file_path>([^<]+)</file_path>\s*<start_line>(\d+)</start_line>\s*<end_line>(\d+)</end_line>",
        "write_file": r"write_file\s*<file_path>([^<]+)</file_path>\s*<content>([^<]+)</content>",
        "list_files": r"list_files\s*<path>([^<]+)</path>",
        "rest_api_call": r"rest_api_call\s*<url>([^<]+)</url>\s*<method>([^<]+)</method>(?:\s*<body>([^<]+)</body>)?",
        "execute_command": r"execute_command\s*<command>(.+?)</command>(?:\s*<timeout>(\d+)</timeout>)?",
    }
    
    def __init__(self, user_id: Optional[int] = None):
        self.tool_registry = get_tool_registry()
        self.user_id = user_id
    
    def set_user_id(self, user_id: int) -> None:
        """Set the current user ID for permission checks."""
        self.user_id = user_id
    
    def _parse_tool_call(self, text: str) -> Optional[Dict[str, Any]]:
        """Parse tool call from LLM response text."""
        # First, check for explicit tool call patterns
        for tool_name, pattern in self.TOOL_PATTERNS.items():
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                params = {}
                if tool_name == "read_file":
                    params["path"] = match.group(1).strip()
                    params["mode"] = "auto"  # 默认自动模式
                elif tool_name == "search_in_file":
                    params["path"] = match.group(1).strip()
                    params["keyword"] = match.group(2).strip()
                elif tool_name == "read_file_range":
                    params["path"] = match.group(1).strip()
                    params["start_line"] = int(match.group(2).strip())
                    params["end_line"] = int(match.group(3).strip())
                elif tool_name == "write_file":
                    params["path"] = match.group(1).strip()
                    params["content"] = match.group(2).strip()
                elif tool_name == "list_files":
                    params["path"] = match.group(1).strip()
                elif tool_name == "rest_api_call":
                    params["url"] = match.group(1).strip()
                    params["method"] = match.group(2).strip().upper()
                    if match.group(3):
                        params["body"] = match.group(3).strip()
                elif tool_name == "execute_command":
                    params["command"] = match.group(1).strip()
                    if match.group(2):
                        params["timeout"] = int(match.group(2).strip())
                return {"tool": tool_name, "params": params}
        
        # [新增] 检查 Python 代码块，自动转换为 execute_command
        # 匹配 ```python ... ``` 或 ``` ... ``` 格式
        python_block_pattern = r'```(?:python)?\s*\n(.*?)\n```'
        python_match = re.search(python_block_pattern, text, re.DOTALL | re.IGNORECASE)
        if python_match:
            python_code = python_match.group(1).strip()
            # 确保代码有意义（不是空的或太短）
            if python_code and len(python_code) > 10:
                # 构建执行命令
                # 使用 python3 执行代码，并注入环境变量
                command = f'python3 -c "{python_code}"'
                # 或者保存为临时文件执行（更可靠）
                return {
                    "tool": "execute_command",
                    "params": {
                        "command": python_code,  # 直接传递Python代码
                        "timeout": 60,
                        "is_python_code": True  # 标记为Python代码
                    }
                }
        
        return None
    
    def _execute_tool(self, tool_call: Dict[str, Any], user_context: UserContext) -> Dict[str, Any]:
        """Execute a tool call with user permission check and context injection."""
        tool_name = tool_call["tool"]
        params = tool_call["params"]
        
        print(f"[Agent] Executing tool: {tool_name} with params: {params}, user_id: {self.user_id}")
        
        # [新增] 传递 downloads_path 到工具执行
        downloads_path = user_context.downloads_path if user_context else None
        
        # Execute with user_id for permission check and downloads_path for env injection
        result = self.tool_registry.execute_tool(
            tool_name, 
            params, 
            user_id=self.user_id,
            downloads_path=downloads_path
        )
        
        return {
            "tool": tool_name,
            "success": result.success,
            "output": result.output,
            "error": result.error
        }
    
    def _generate_tool_summary_for_user(
        self,
        tool_name: str,
        params: Dict[str, Any],
        result: Dict[str, Any]
    ) -> str:
        """
        生成工具执行摘要（给用户看）。
        
        用户只需要知道"做了什么"，不需要看到详细内容。
        """
        if not result["success"]:
            return f"❌ {tool_name} 执行失败：{result['error'][:50] if result['error'] else '未知错误'}"
        
        output = result["output"]
        
        # 根据工具类型生成不同的摘要
        if tool_name == "read_file":
            path = params.get("path", "未知文件")
            if isinstance(output, dict):
                lines = output.get("total_lines", "N/A")
                strategy = output.get("strategy", "")
                return f"📖 读取了 {path}（{lines}行，{strategy}策略）"
            elif isinstance(output, str):
                return f"📖 读取了 {path}（{len(output)}字符）"
            return f"📖 读取了 {path}"
        
        elif tool_name == "write_file":
            path = params.get("path", "未知文件")
            return f"✏️ 写入了 {path}"
        
        elif tool_name == "edit_file":
            path = params.get("path", "未知文件")
            return f"📝 编辑了 {path}"
        
        elif tool_name == "list_files":
            path = params.get("path", "未知目录")
            if isinstance(output, list):
                return f"📁 列出了 {path} 下 {len(output)} 个文件"
            return f"📁 列出了 {path} 目录"
        
        elif tool_name == "search_in_file":
            path = params.get("path", "未知文件")
            keyword = params.get("keyword", "")
            if isinstance(output, dict):
                matches = output.get("matches_found", 0)
                return f"🔍 在 {path} 中搜索 '{keyword}'，找到 {matches} 处匹配"
            return f"🔍 在 {path} 中搜索 '{keyword}'"
        
        elif tool_name == "execute_command":
            command = params.get("command", "")
            # 截取命令前30字符作为摘要
            cmd_short = command[:30] + "..." if len(command) > 30 else command
            
            if isinstance(output, dict):
                # 检查是否生成了文件
                downloads_path = output.get("downloads_path", "")
                if downloads_path:
                    return f"⚡ 执行命令：{cmd_short}\n   生成文件保存到：{downloads_path}"
                exit_code = output.get("exit_code", -1)
                if exit_code == 0:
                    stdout_preview = output.get("stdout", "")[:50]
                    if stdout_preview.strip():
                        return f"⚡ 执行成功：{cmd_short}\n   输出：{stdout_preview}..."
                    return f"⚡ 执行成功：{cmd_short}"
                else:
                    return f"⚡ 执行失败：{cmd_short}"
            return f"⚡ 执行命令：{cmd_short}"
        
        elif tool_name == "rest_api_call":
            url = params.get("url", "")
            method = params.get("method", "GET")
            url_short = url[:40] + "..." if len(url) > 40 else url
            # REST API结果不直接展示，等LLM分析后再展示
            return f"🌐 调用 API：{method} {url_short}\n   （结果已获取，正在分析...）"
        
        elif tool_name == "delete_file":
            path = params.get("path", "未知文件")
            return f"🗑️ 删除了 {path}"
        
        else:
            # 默认摘要
            return f"🔧 执行了 {tool_name}"
    
    def _format_tool_result_for_llm(
        self,
        tool_name: str,
        params: Dict[str, Any],
        result: Dict[str, Any]
    ) -> str:
        """
        格式化工具执行结果（给LLM看）。
        
        LLM需要完整的内容来做分析和决策。
        """
        if not result["success"]:
            return f"工具 {tool_name} 执行失败：{result['error']}\n请尝试其他方法完成任务。"
        
        output = result["output"]
        
        # 根据工具类型格式化不同的详细内容
        if tool_name == "read_file":
            # 文件内容完整给LLM（截断15000字符）
            if isinstance(output, dict):
                text = "文件读取结果：\n"
                if "content" in output:
                    content = output["content"]
                    max_len = 15000
                    if len(content) > max_len:
                        text += content[:max_len] + f"\n\n（内容过长，已截断，总共 {len(content)} 字符）"
                    else:
                        text += content
                if "strategy" in output:
                    text += f"\n\n读取策略：{output['strategy']}"
                if "total_lines" in output:
                    text += f"\n总行数：{output['total_lines']}"
                if "guidance" in output:
                    text += f"\n💡 {output['guidance']}"
                return text
            elif isinstance(output, str):
                max_len = 15000
                if len(output) > max_len:
                    return output[:max_len] + f"\n\n（内容过长，已截断，总共 {len(output)} 字符）"
                return f"文件内容：\n{output}"
            return f"文件读取成功"
        
        elif tool_name == "write_file":
            path = params.get("path", "")
            return f"文件写入成功：{path}"
        
        elif tool_name == "list_files":
            if isinstance(output, list):
                return f"目录内容：\n" + json.dumps(output, indent=2, ensure_ascii=False)
            return f"列出目录成功"
        
        elif tool_name == "search_in_file":
            if isinstance(output, dict):
                text = f"搜索结果：找到 {output.get('matches_found', 0)} 处匹配\n"
                if "matches" in output:
                    for i, match in enumerate(output["matches"][:10]):
                        text += f"\n匹配 {i+1}：{match}"
                return text
            return f"搜索完成"
        
        elif tool_name == "execute_command":
            if isinstance(output, dict):
                exit_code = output.get("exit_code", -1)
                
                # [关键] 明确告诉 LLM 执行结果状态
                if exit_code == 0:
                    text = "✅ 命令执行成功！\n\n"
                else:
                    text = f"❌ 命令执行失败（退出码：{exit_code}）\n\n"
                
                stdout = output.get("stdout", "")
                stderr = output.get("stderr", "")
                
                # stdout 截断500字符
                if stdout:
                    stdout_preview = stdout[:500] if len(stdout) > 500 else stdout
                    text += f"输出：{stdout_preview}"
                    if len(stdout) > 500:
                        text += f"...（总共 {len(stdout)} 字符）"
                    text += "\n"
                
                if stderr:
                    text += f"错误输出：{stderr[:200]}...\n"
                
                # 提示下载路径
                if output.get("downloads_path"):
                    text += f"\n📁 文件保存路径：{output['downloads_path']}\n"
                
                # [关键] 如果成功，明确告诉 LLM 任务已完成，不要继续尝试
                if exit_code == 0:
                    text += "\n\n【重要】任务已成功完成，请直接回复用户结果，不要再次执行相同命令。"
                else:
                    text += "\n\n请尝试其他方法完成任务。"
                
                return text
            return f"✅ 命令执行完成"
        
        elif tool_name == "rest_api_call":
            # REST API结果完整给LLM分析
            if isinstance(output, dict):
                return f"API 响应：\n" + json.dumps(output, indent=2, ensure_ascii=False)[:3000]
            elif isinstance(output, str):
                max_len = 3000
                if len(output) > max_len:
                    return f"API 响应：\n{output[:max_len]}...（已截断）"
                return f"API 响应：\n{output}"
            return f"API 调用成功"
        
        elif tool_name == "edit_file":
            return f"文件编辑成功：{params.get('path', '')}"
        
        elif tool_name == "delete_file":
            return f"文件删除成功：{params.get('path', '')}"
        
        else:
            # 默认格式
            if isinstance(output, dict):
                return f"工具执行结果：\n" + json.dumps(output, indent=2, ensure_ascii=False)[:1000]
            elif isinstance(output, str):
                return f"工具执行结果：{output[:500]}"
            elif isinstance(output, list):
                return f"工具执行结果：\n" + json.dumps(output[:20], indent=2, ensure_ascii=False)
            return f"工具 {tool_name} 执行成功"
    
    async def run_stream(
        self,
        message: str,
        user_context: UserContext,
        conversation_history: List[Dict[str, str]],
        session_id: str
    ) -> AsyncGenerator[ServerMessage, None]:
        """
        Run agent with streaming response.
        
        Args:
            message: User message
            user_context: User context (memory, soul, skills)
            conversation_history: Previous messages
            session_id: Session ID
        
        Yields:
            ServerMessage chunks
        """
        print(f"[Agent] Processing message for session {session_id}")
        
        # Build messages for LLM
        messages = conversation_history + [{"role": "user", "content": message}]
        
        # Build system prompt from user context (with smart memory injection)
        system_prompt = self._build_system_prompt(user_context, message)
        
        # [新增] 发送简洁的状态提示（等待LLM响应）
        yield ServerMessage(
            type="status",
            payload={"content": "处理中..."},
            session_id=session_id
        )
        
        try:
            # Check if API key is configured
            config = get_provider_config()
            if not config.api_key:
                # No API key, use mock response
                print(f"[Agent] No API key configured, using mock response")
                async for chunk in self._mock_response(message, user_context, session_id):
                    yield chunk
                
                # 即使是 mock response，也要更新记忆
                try:
                    memory_manager = get_memory_manager(self.user_id)
                    await self._update_memory_smart(
                        user_message=message,
                        assistant_response="[Mock Response]",
                        memory_manager=memory_manager,
                        conversation_history=conversation_history
                    )
                except Exception as mem_error:
                    print(f"[Memory] Mock response memory update error: {mem_error}")
                
                return
            
            # Use real LLM with tool calling loop
            print(f"[Agent] Calling LLM: {config.provider} / {config.model}")
            llm_client = get_llm_client()
            
            # Tool calling loop - 使用配置管理获取最大迭代次数
            from openharness.enterprise.config.settings import get_settings
            max_iterations = get_settings().max_iterations
            iteration = 0
            last_tool_result = None
            failed_tools = []  # [新增] 追踪连续失败的工具
            
            while iteration < max_iterations:
                iteration += 1
                
                full_response = ""
                try:
                    async for chunk in llm_client.stream_chat(
                        messages, 
                        system_prompt,
                        skills=user_context.available_skills,
                        skills_base_path=user_context.skills_path if hasattr(user_context, 'skills_path') else None
                    ):
                        full_response += chunk
                        yield ServerMessage(
                            type="text",
                            payload={"content": chunk, "delta": True},
                            session_id=session_id
                        )
                except Exception as e:
                    print(f"[Agent] LLM stream error: {e}")
                    yield ServerMessage(
                        type="error",
                        payload={"message": f"LLM 调用错误: {str(e)}"},
                        session_id=session_id
                    )
                    return
                
                print(f"[Agent] Response iteration {iteration}, length: {len(full_response)}")
                
                # Check if response is empty
                if not full_response or not full_response.strip():
                    print(f"[Agent] Empty response at iteration {iteration}")
                    # If we had a tool result, provide a summary
                    if last_tool_result:
                        summary = "工具执行完成。"
                        yield ServerMessage(
                            type="text",
                            payload={"content": summary, "delta": False},
                            session_id=session_id
                        )
                    break
                
                # Check if response contains tool call
                tool_call = self._parse_tool_call(full_response)
                
                if tool_call:
                    # Execute tool with user context
                    tool_result = self._execute_tool(tool_call, user_context)
                    last_tool_result = tool_result
                    
                    # [新增] 追踪失败次数
                    if not tool_result["success"]:
                        failed_tools.append(tool_call["tool"])
                    else:
                        failed_tools = []  # 成功后清空失败记录
                    
                    # [新增] 生成用户摘要（WebSocket推送）
                    user_summary = self._generate_tool_summary_for_user(
                        tool_call["tool"],
                        tool_call["params"],
                        tool_result
                    )
                    
                    # 发送摘要给用户（不包含详细内容）
                    yield ServerMessage(
                        type="tool_summary",
                        payload={
                            "tool": tool_call["tool"],
                            "summary": user_summary,
                            "success": tool_result["success"]
                        },
                        session_id=session_id
                    )
                    
                    # [新增] 构建详细结果给LLM（加入messages，用户看不到）
                    messages.append({"role": "assistant", "content": full_response})
                    
                    tool_result_text = self._format_tool_result_for_llm(
                        tool_call["tool"],
                        tool_call["params"],
                        tool_result
                    )
                    
                    messages.append({"role": "user", "content": tool_result_text})
                    
                    # [移除] 不发送 thinking 消息
                    
                    # [新增] 检查连续失败次数，超过3次给出失败结论
                    if len(failed_tools) >= 3:
                        yield ServerMessage(
                            type="text",
                            payload={
                                "content": f"⚠️ 工具执行连续失败（{failed_tools}），建议：\n1. 检查文件路径是否正确\n2. 确认命令是否有效\n3. 尝试其他方法完成任务",
                                "delta": False
                            },
                            session_id=session_id
                        )
                        # 加入失败提示给LLM
                        messages.append({
                            "role": "user",
                            "content": "工具执行多次失败，请停止尝试并给出明确的失败原因和解决方案。"
                        })
                    
                    continue
                else:
                    # No tool call - this is the final response
                    break
            
            # Signal completion
            # 文件日志确认即将完成
            from openharness.enterprise.config.settings import get_settings
            debug_log = get_settings().debug_log
            with open(debug_log, 'a', encoding='utf-8') as f:
                f.write(f"[{datetime.now()}] About to yield done, full_response length: {len(full_response)}\n")
            
            yield ServerMessage(
                type="done",
                payload={"message_count": len(messages) + 1},
                session_id=session_id
            )
            
            # 文件日志确认 done 已 yield
            with open(debug_log, 'a', encoding='utf-8') as f:
                f.write(f"[{datetime.now()}] Done yielded, calling memory update...\n")
            
            # Smart memory update - summarize and save important info
            try:
                memory_manager = get_memory_manager(self.user_id)
                await self._update_memory_smart(
                    user_message=message,
                    assistant_response=full_response,
                    memory_manager=memory_manager,
                    conversation_history=conversation_history
                )
            except Exception as mem_error:
                print(f"[Memory] Memory update error: {mem_error}")
            
            # [新增] 首次对话学习 - 检查是否有 BOOTSTRAP.md
            try:
                from openharness.enterprise.users.learning import get_learning_engine
                from openharness.enterprise.users.workspace import get_user_workspace_path
                
                bootstrap_path = get_user_workspace_path(self.user_id) / "BOOTSTRAP.md"
                if bootstrap_path.exists():
                    # 首次对话完成，学习用户信息
                    learning_engine = get_learning_engine(self.user_id)
                    
                    # 构建消息列表用于学习
                    learn_messages = conversation_history + [
                        {"role": "user", "content": message},
                        {"role": "assistant", "content": full_response}
                    ]
                    
                    result = learning_engine.learn_from_first_conversation(learn_messages)
                    print(f"[Learning] First conversation learning result: {result}")
            except Exception as learn_error:
                print(f"[Learning] Learning error: {learn_error}")
            
        except Exception as e:
            print(f"[Agent] Error: {e}")
            yield ServerMessage(
                type="error",
                payload={"message": f"LLM 错误: {str(e)}"},
                session_id=session_id
            )
    
    async def _update_memory_smart(
        self,
        user_message: str,
        assistant_response: str,
        memory_manager: MemoryManager,
        conversation_history: List[Dict[str, str]]
    ) -> None:
        # 文件日志确认函数被调用
        from openharness.enterprise.config.settings import get_settings
        debug_log = get_settings().debug_log
        with open(debug_log, 'a', encoding='utf-8') as f:
            f.write(f"[{datetime.now()}] _update_memory_smart called: {user_message[:30]}...\n")
        print(f"[Memory] _update_memory_smart called, user_message: {user_message[:30]}...")
        """
        Smart memory update - extract and save important information.
        
        This method:
        1. Analyzes the conversation to identify important info
        2. Updates daily memory with a brief log
        3. Updates long-term memory if significant decisions/lessons found
        
        Args:
            user_message: Original user message
            assistant_response: Final assistant response
            memory_manager: Memory manager instance
            conversation_history: Previous conversation history
        """
        # Build summary prompt
        summary_prompt = """分析以下对话，提取重要信息：

## 用户问题
{user_message}

## AI回答（摘要）
{assistant_summary}

请回答：
1. 是否有需要长期记忆的重要决策、教训、关键信息？（用"重要"/"不重要"判断）
2. 如果重要，请总结成一句话（不超过50字）
3. 是否涉及用户偏好或习惯发现？（用"是"/"否"判断）
4. 如果是，请描述用户偏好（不超过30字）

回复格式（JSON）：
{{
  "important": "重要" 或 "不重要",
  "summary": "总结内容",
  "preference_found": "是" 或 "否",
  "preference": "偏好描述"
}}

如果都不是重要信息，回复：
{{
  "important": "不重要",
  "summary": "",
  "preference_found": "否",
  "preference": ""
}}"""
        
        # Truncate assistant response for summary
        assistant_summary = assistant_response[:500] if len(assistant_response) > 500 else assistant_response
        
        try:
            # Call LLM to summarize
            config = get_provider_config()
            if not config.api_key:
                return
            
            llm_client = get_llm_client()
            
            messages = [
                {"role": "user", "content": summary_prompt.format(
                    user_message=user_message[:300],
                    assistant_summary=assistant_summary
                )}
            ]
            
            full_summary = ""
            async for chunk in llm_client.stream_chat(
                messages=messages,
                system_prompt="你是一个记忆分析助手，帮助提取对话中的重要信息。只返回JSON格式。",
                skills=[]
            ):
                full_summary += chunk
            
            print(f"[Memory] LLM summary response: {full_summary[:200]}...")
            
            # 1. Always log to daily memory (regardless of JSON parsing)
            event_text = user_message[:50]
            if len(user_message) > 50:
                event_text += "..."
            memory_manager.append_to_daily(event_text)
            print(f"[Memory] Updated daily memory: {event_text}")
            
            # Parse summary for long-term memory
            try:
                # Extract JSON from response using stack-based matching
                def extract_json(text):
                    """从文本中提取完整 JSON 对象"""
                    start = text.find('{')
                    if start == -1:
                        return None
                    stack = []
                    for i, char in enumerate(text[start:], start):
                        if char == '{':
                            stack.append(i)
                        elif char == '}':
                            if stack:
                                stack.pop()
                                if not stack:
                                    return text[start:i+1]
                    return None
                
                json_str = extract_json(full_summary)
                if json_str:
                    print(f"[Memory] Extracted JSON: {json_str[:100]}...")
                    summary_data = json.loads(json_str)
                    
                    # 2. If important, update long-term memory
                    if summary_data.get("important") == "重要":
                        important_summary = summary_data.get("summary", "")
                        if important_summary:
                            memory_manager.append_to_memory(
                                "重要记录",
                                f"- [{datetime.now().isoformat()}] {important_summary}"
                            )
                            print(f"[Memory] Updated long-term memory: {important_summary}")
                    
                    # 3. If preference found, update preferences section
                    if summary_data.get("preference_found") == "是":
                        preference = summary_data.get("preference", "")
                        if preference:
                            memory_manager.append_to_memory(
                                "用户偏好",
                                f"- {preference}"
                            )
                            print(f"[Memory] Updated user preference: {preference}")
                else:
                    print(f"[Memory] No JSON found in response")
                    
            except (json.JSONDecodeError, KeyError) as parse_error:
                print(f"[Memory] Summary parse error: {parse_error}")
                
        except Exception as e:
            print(f"[Memory] Memory summarization error: {e}")
    
    def _build_system_prompt(
        self, 
        user_context: UserContext,
        user_message: str = ""
    ) -> str:
        """
        Build system prompt from user context.
        
        [新增] 智能记忆注入 - 采用关键词触发策略
        """
        parts = []
        
        # Base identity
        parts.append("你是一个有帮助的 AI 助手。")
        
        # [重要] 添加用户 ID 信息，确保 LLM 知道当前用户
        user_id = user_context.user_id
        downloads_path = user_context.downloads_path
        
        # Tool usage instructions - 使用动态 user_id（注意：花括号需要双写转义）
        tool_instructions = """

## 工具使用

你可以使用以下工具来完成任务。当你需要使用工具时，请按照指定格式输出：

**重要：当前用户 ID 是 """ + str(user_id) + """

### 文件路径说明

- **用户工作区**: `.oh-enterprise/users/""" + str(user_id) + """/`
- **默认下载目录**: `""" + downloads_path + """`（所有生成的文件应保存到此目录）
- **上传文件目录**: `.oh-enterprise/users/""" + str(user_id) + """/uploads/`
- **记忆文件目录**: `.oh-enterprise/users/""" + str(user_id) + """/memory/`

**当执行 Python 代码生成文件时，必须使用下载目录！**

示例：
```python
import os
from pathlib import Path

# 获取下载目录（已在上下文中指定）
downloads_dir = Path(r"""" + downloads_path + """")
downloads_dir.mkdir(parents=True, exist_ok=True)

# 保存文件
output_file = downloads_dir / "output.xlsx"
wb.save(str(output_file))
print("文件已保存到:", output_file)
```

### read_file - 智能读取文件
**自动策略**：根据文档长度自动选择策略
- 短文档 (<1000行)：全量读取
- 中等文档 (1000-2000行)：读取前半 + 提示继续
- 长文档 (>2000行)：提取目录/大纲 + 提供搜索选项

格式：read_file<file_path>文件路径</file_path>
示例：read_file<file_path>.oh-enterprise/users/""" + str(user_id) + """/knowledge/API接口清单.md</file_path>

### search_in_file - 在文件中搜索关键词
用于精确定位长文档中的内容。返回匹配位置前后各10行上下文。

格式：search_in_file<file_path>文件路径</file_path><keyword>搜索关键词</keyword>
示例：search_in_file<file_path>.oh-enterprise/users/""" + str(user_id) + """/knowledge/API接口清单.md</file_path><keyword>eAiPAgent_0124</keyword>

### read_file_range - 按行号范围读取
用于分段读取长文档的特定部分。

格式：read_file_range<file_path>文件路径</file_path><start_line>起始行号</start_line><end_line>结束行号</end_line>
示例：read_file_range<file_path>.oh-enterprise/users/""" + str(user_id) + """/knowledge/manual.md</file_path><start_line>100</start_line><end_line>200</end_line>

### list_files - 列出目录文件
格式：list_files<path>目录路径</path>
示例：list_files<path>.oh-enterprise/users/""" + str(user_id) + """/uploads</path>

### write_file - 写入文件
格式：write_file<file_path>文件路径</file_path><content>文件内容</content>
示例：write_file<file_path>.oh-enterprise/users/""" + str(user_id) + """/memory/MEMORY.md</file_path><content># MEMORY.md</content>

### rest_api_call - 执行 REST API 调用
格式：rest_api_call<url>API地址</url><method>HTTP方法</method><body>请求体JSON</body>
示例：rest_api_call<url>http://api.example.com/data</url><method>POST</method><body>{"key": "value"}</body>

### execute_command - 执行系统命令
格式：execute_command<command>命令内容</command><timeout>超时秒数</timeout>
示例：execute_command<command>node skills/prd-writer/generate-prd-docx.js "docs/input.md" "docs/output.docx"</command><timeout>60</timeout>

注意：
1. 文件路径使用相对路径，以 .oh-enterprise/ 开头
2. **生成文件时使用绝对路径 `""" + downloads_path + """`**
3. 当用户要求读取文件时，直接使用 read_file 工具
4. 当需要调用外部 API 时，使用 rest_api_call 工具
5. 当需要执行脚本或命令时，使用 execute_command 工具
"""
        parts.append(tool_instructions)
        
        # Add user soul if available
        if user_context.soul:
            parts.append(f"\n\n以下是你的个性化设置：\n{user_context.soul}")
        
        # [新增] Add identity if available
        if user_context.identity and user_context.identity.strip():
            # 检查是否有实际内容（不只是空模板）
            if not user_context.identity.strip().endswith("自动填充"):
                parts.append(f"\n\n## 你的身份\n\n{user_context.identity}")
        
        # [新增] Add user profile if available
        if user_context.user_profile and user_context.user_profile.strip():
            # 检查是否有实际内容
            if not user_context.user_profile.strip().endswith("自动学习并填充"):
                parts.append(f"\n\n## 用户信息\n\n{user_context.user_profile}")
        
        # [新增] Add bootstrap for first-time onboarding
        if user_context.bootstrap and user_context.bootstrap.strip():
            parts.append(f"\n\n## 首次启动引导\n\n{user_context.bootstrap}")
        
        # [修改] 直接注入记忆（不再使用关键词触发）
        if user_context.memory and user_context.memory.strip():
            parts.append(f"\n\n## 历史记忆\n\n{user_context.memory}")
        
        # [新增] 注入知识库内容
        if user_context.knowledge and user_context.knowledge.strip():
            parts.append(f"\n\n{user_context.knowledge}")
        
        return "\n".join(parts)
    
    async def _mock_response(
        self,
        message: str,
        user_context: UserContext,
        session_id: str
    ) -> AsyncGenerator[ServerMessage, None]:
        """Generate mock response when no LLM is configured."""
        response_text = f"[模拟响应] 我收到了你的消息：\"{message}\"\n\n"
        response_text += "请配置 API Key 以使用真正的 LLM。\n\n"
        response_text += "配置方式：设置环境变量 OH_API_KEY 和 OH_BASE_URL\n"
        
        # Stream the response word by word
        words = response_text.split()
        for i, word in enumerate(words):
            yield ServerMessage(
                type="text",
                payload={
                    "content": word + (" " if i < len(words) - 1 else ""),
                    "delta": True
                },
                session_id=session_id
            )
            await asyncio.sleep(0.03)
        
        yield ServerMessage(
            type="done",
            payload={"message_count": 2},
            session_id=session_id
        )


# ============================================================================
# WebChat Channel
# ============================================================================

class WebChatChannel:
    """
    WebSocket-based chat channel.
    
    Features:
    - User authentication via query param token
    - Session management
    - Streaming agent responses
    - Message persistence
    - [新增] 两阶段调用优化
    - [新增] Session 并发控制
    """
    
    def __init__(self):
        self.session_manager = SessionManager()
        self.message_store = MessageStore()
        self.agent_engine = AgentEngineInterface()
        self.audit = get_audit_logger()
        self.db = get_database()
    
    async def handle_connection(
        self,
        websocket: WebSocket,
        user: User,
        session_id: Optional[str] = None
    ) -> None:
        """
        Handle WebSocket connection.
        
        Args:
            websocket: WebSocket connection
            user: Authenticated user
            session_id: Optional session ID to resume
        """
        await websocket.accept()
        
        # Load user context
        user_context = load_user_context(user)
        
        # Get or create session
        session = self.session_manager.get_or_create_session(
            user_id=user.id,
            session_id=session_id
        )
        
        # Register connection
        self.session_manager.register_connection(
            session_id=session.id,
            websocket=websocket,
            user_id=user.id
        )
        
        # Send session info
        await self._send_session_info(websocket, session)
        
        # If resuming a session with history, send past messages
        if session.message_count > 0:
            await self._send_session_history(websocket, session.id)
        
        # Log connection
        self.audit.log(
            user_id=user.id,
            action="websocket_connect",
            resource_type="session",
            resource_id=session.id
        )
        
        try:
            # Message loop
            while True:
                # Receive message
                raw_data = await websocket.receive_text()
                
                try:
                    data = json.loads(raw_data)
                    client_msg = ClientMessage.from_dict(data)
                except json.JSONDecodeError:
                    await self._send_error(websocket, "Invalid JSON format")
                    continue
                
                # Handle message
                await self._handle_message(websocket, client_msg, user, user_context, session)
                
        except WebSocketDisconnect:
            pass
        finally:
            # Cleanup
            self.session_manager.unregister_connection(session.id)
            self.audit.log(
                user_id=user.id,
                action="websocket_disconnect",
                resource_type="session",
                resource_id=session.id
            )
    
    async def _handle_message(
        self,
        websocket: WebSocket,
        client_msg: ClientMessage,
        user: User,
        user_context: UserContext,
        session: Session
    ) -> None:
        """Handle client message."""
        
        if client_msg.type == "message":
            await self._handle_chat_message(websocket, client_msg, user, user_context, session)
        
        elif client_msg.type == "resume":
            # Resume a different session
            new_session_id = client_msg.payload.get("session_id")
            if new_session_id:
                new_session = self.db.get_session(new_session_id)
                if new_session and new_session.user_id == user.id:
                    session = new_session
                    await self._send_session_info(websocket, session)
        
        elif client_msg.type == "command":
            # Handle special commands
            await self._handle_command(websocket, client_msg, user, session)
    
    async def _handle_chat_message(
        self,
        websocket: WebSocket,
        client_msg: ClientMessage,
        user: User,
        user_context: UserContext,
        session: Session
    ) -> None:
        """Handle chat message."""
        content = client_msg.payload.get("content", "")
        
        print(f"[Chat] Received message from user {user.id}: {content[:50]}...")
        
        if not content:
            return
        
        # Check for reload skills command
        if content.strip() == "/reload-skills" or content.strip() == "/刷新技能":
            # Reload user context to get fresh skills
            fresh_context = load_user_context(user)
            user_context.available_skills = fresh_context.available_skills
            user_context.soul = fresh_context.soul
            user_context.identity = fresh_context.identity
            user_context.user_profile = fresh_context.user_profile
            user_context.bootstrap = fresh_context.bootstrap
            user_context.memory = fresh_context.memory
            user_context.preferences = fresh_context.preferences
            
            await websocket.send_text(ServerMessage(
                type="text",
                payload={"content": f"已刷新技能列表，当前可用技能：{', '.join(user_context.available_skills) or '无'}"}
            ).to_json())
            return
        
        # Log chat
        self.audit.log_chat(user.id, session.id, content[:100])
        
        # Save user message
        self.message_store.save_message(
            session_id=session.id,
            role="user",
            content=content
        )
        
        # Reload skills before each message to ensure fresh content
        fresh_context = load_user_context(user)
        user_context.available_skills = fresh_context.available_skills
        user_context.soul = fresh_context.soul
        user_context.identity = fresh_context.identity
        user_context.user_profile = fresh_context.user_profile
        user_context.bootstrap = fresh_context.bootstrap
        user_context.memory = fresh_context.memory
        
        # Get conversation history
        history = self.message_store.get_conversation_history(session.id)
        
        # Set user ID for permission checks
        self.agent_engine.set_user_id(user.id)
        
        # Run agent and stream response
        full_response = ""
        
        async for server_msg in self.agent_engine.run_stream(
            message=content,
            user_context=user_context,
            conversation_history=history[:-1],  # Exclude current message
            session_id=session.id
        ):
            # Send to client
            await websocket.send_text(server_msg.to_json())
            
            # Accumulate response
            if server_msg.type == "text" and server_msg.payload.get("delta"):
                full_response += server_msg.payload.get("content", "")
        
        # Save assistant response
        if full_response:
            self.message_store.save_message(
                session_id=session.id,
                role="assistant",
                content=full_response
            )
    
    async def _handle_command(
        self,
        websocket: WebSocket,
        client_msg: ClientMessage,
        user: User,
        session: Session
    ) -> None:
        """Handle special commands."""
        command = client_msg.payload.get("command")
        
        if command == "list_sessions":
            sessions = self.session_manager.get_user_sessions(user.id)
            await websocket.send_text(ServerMessage(
                type="session_list",
                payload={
                    "sessions": [
                        {
                            "id": s.id,
                            "title": s.title,
                            "message_count": s.message_count,
                            "created_at": s.created_at.isoformat() if s.created_at else None,
                            "updated_at": s.updated_at.isoformat() if s.updated_at else None
                        }
                        for s in sessions
                    ]
                }
            ).to_json())
        
        elif command == "new_session":
            new_session = self.session_manager.create_session(user.id)
            session = new_session
            await self._send_session_info(websocket, new_session)
    
    async def _send_session_info(self, websocket: WebSocket, session: Session) -> None:
        """Send session info to client."""
        await websocket.send_text(ServerMessage(
            type="session_info",
            payload={
                "session_id": session.id,
                "title": session.title,
                "message_count": session.message_count,
                "created_at": session.created_at.isoformat() if session.created_at else None
            }
        ).to_json())
    
    async def _send_session_history(self, websocket: WebSocket, session_id: str) -> None:
        """Send session history to client."""
        messages = self.message_store.get_session_messages(session_id)
        
        if messages:
            await websocket.send_text(ServerMessage(
                type="session_history",
                payload={
                    "messages": [
                        {
                            "id": m.id,
                            "role": m.role,
                            "content": m.content,
                            "created_at": m.created_at.isoformat() if m.created_at else None
                        }
                        for m in messages
                    ]
                }
            ).to_json())
    
    async def _send_error(self, websocket: WebSocket, message: str) -> None:
        """Send error message."""
        await websocket.send_text(ServerMessage(
            type="error",
            payload={"message": message}
        ).to_json())


# ============================================================================
# Channel Instance
# ============================================================================

_webchat_channel: Optional[WebChatChannel] = None


def get_webchat_channel() -> WebChatChannel:
    """Get WebChat channel instance."""
    global _webchat_channel
    
    if _webchat_channel is None:
        _webchat_channel = WebChatChannel()
    
    return _webchat_channel