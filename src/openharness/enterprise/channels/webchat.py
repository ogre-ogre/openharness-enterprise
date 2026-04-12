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
        for tool_name, pattern in self.TOOL_PATTERNS.items():
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                params = {}
                if tool_name == "read_file":
                    params["path"] = match.group(1).strip()
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
        return None
    
    def _execute_tool(self, tool_call: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool call with user permission check."""
        tool_name = tool_call["tool"]
        params = tool_call["params"]
        
        print(f"[Agent] Executing tool: {tool_name} with params: {params}, user_id: {self.user_id}")
        
        # Execute with user_id for permission check
        result = self.tool_registry.execute_tool(tool_name, params, user_id=self.user_id)
        
        return {
            "tool": tool_name,
            "success": result.success,
            "output": result.output,
            "error": result.error
        }
    
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
        
        # Yield thinking status
        yield ServerMessage(
            type="thinking",
            payload={"content": "正在思考..."},
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
                    # Execute tool
                    tool_result = self._execute_tool(tool_call)
                    last_tool_result = tool_result
                    
                    # Send tool result to client
                    yield ServerMessage(
                        type="tool_call",
                        payload={
                            "tool": tool_call["tool"],
                            "params": tool_call["params"],
                            "result": tool_result
                        },
                        session_id=session_id
                    )
                    
                    # Add tool result to messages for next iteration
                    messages.append({"role": "assistant", "content": full_response})
                    
                    tool_result_text = f"工具执行结果:\n"
                    if tool_result["success"]:
                        output = tool_result["output"]
                        if isinstance(output, str):
                            tool_result_text += output[:2000]  # Limit output length
                        elif isinstance(output, list):
                            tool_result_text += json.dumps(output[:100], indent=2, ensure_ascii=False)[:2000]
                        else:
                            tool_result_text += str(output)[:2000]
                    else:
                        tool_result_text += f"错误: {tool_result['error']}"
                        # If tool failed, also tell LLM to try alternative approach
                        tool_result_text += "\n请尝试其他方法完成任务。"
                    
                    messages.append({"role": "user", "content": tool_result_text})
                    
                    # Continue loop to get final response
                    yield ServerMessage(
                        type="thinking",
                        payload={"content": "处理工具结果..."},
                        session_id=session_id
                    )
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
        
        # Tool usage instructions - 使用动态 user_id（注意：花括号需要双写转义）
        tool_instructions = f"""

## 工具使用

你可以使用以下工具来完成任务。当你需要使用工具时，请按照指定格式输出：

**重要：当前用户 ID 是 {user_id}，所有文件操作都必须使用 .oh-enterprise/users/{user_id}/ 目录！**

### read_file - 读取文件
格式：read_file<file_path>文件路径</file_path>
示例：read_file<file_path>.oh-enterprise/users/{user_id}/uploads/example.txt</file_path>

### list_files - 列出目录文件
格式：list_files<path>目录路径</path>
示例：list_files<path>.oh-enterprise/users/{user_id}/uploads</path>

### write_file - 写入文件
格式：write_file<file_path>文件路径</file_path><content>文件内容</content>
示例：write_file<file_path>.oh-enterprise/users/{user_id}/memory/MEMORY.md</file_path><content># MEMORY.md</content>

### rest_api_call - 执行 REST API 调用
格式：rest_api_call<url>API地址</url><method>HTTP方法</method><body>请求体JSON</body>
示例：rest_api_call<url>http://api.example.com/data</url><method>POST</method><body>{{"key": "value"}}</body>

### execute_command - 执行系统命令
格式：execute_command<command>命令内容</command><timeout>超时秒数</timeout>
示例：execute_command<command>node skills/prd-writer/generate-prd-docx.js "docs/input.md" "docs/output.docx"</command><timeout>60</timeout>
示例：execute_command<command>cd .oh-enterprise && node scripts/example.js</command>

注意：
1. 文件路径使用相对路径，以 .oh-enterprise/ 开头
2. **当前用户的文件目录是 .oh-enterprise/users/{user_id}/**
3. 用户的上传文件位于 .oh-enterprise/users/{user_id}/uploads/ 目录
4. 用户记忆文件位于 .oh-enterprise/users/{user_id}/memory/ 目录
5. 当用户要求读取文件时，直接使用 read_file 工具
6. 当需要调用外部 API 时，使用 rest_api_call 工具
7. 当需要执行脚本或命令时，使用 execute_command 工具
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
            user_context.identity = fresh_context.identity       # [新增]
            user_context.user_profile = fresh_context.user_profile  # [新增]
            user_context.bootstrap = fresh_context.bootstrap     # [新增]
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
        user_context.identity = fresh_context.identity           # [新增]
        user_context.user_profile = fresh_context.user_profile   # [新增]
        user_context.bootstrap = fresh_context.bootstrap         # [新增]
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