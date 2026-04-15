"""
OpenHarness Enterprise - A2A Protocol Adapter

Agent-to-Agent Protocol implementation for external system integration.
Based on A2A Protocol Specification v1.0.0
"""

from __future__ import annotations

import uuid
import json
import asyncio
from datetime import datetime
from typing import Optional, List, Dict, Any, AsyncGenerator, Union
from enum import Enum
from pydantic import BaseModel, Field


# ============================================================================
# A2A Data Model
# ============================================================================

class TaskState(str, Enum):
    """A2A Task states."""
    PENDING = "pending"
    RUNNING = "running"
    INPUT_REQUIRED = "input-required"
    AUTH_REQUIRED = "auth-required"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"
    REJECTED = "rejected"


class PartType(str, Enum):
    """A2A Part types."""
    TEXT = "text"
    FILE = "file"
    DATA = "data"


class Part(BaseModel):
    """A2A Part - smallest unit of content."""
    type: PartType = PartType.TEXT
    text: Optional[str] = None
    file: Optional[Dict[str, Any]] = None  # {name, mimeType, bytes, uri}
    data: Optional[Dict[str, Any]] = None  # Structured JSON data
    
    class Config:
        use_enum_values = True


class Message(BaseModel):
    """A2A Message - communication turn."""
    role: str  # "user" or "agent"
    parts: List[Part]
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    context_id: Optional[str] = None
    task_id: Optional[str] = None
    reference_task_ids: Optional[List[str]] = None
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class Artifact(BaseModel):
    """A2A Artifact - agent output."""
    artifact_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: Optional[str] = None
    description: Optional[str] = None
    parts: List[Part] = []
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class TaskStatus(BaseModel):
    """A2A Task status."""
    state: TaskState = TaskState.PENDING
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    reason: Optional[str] = None  # Reason for failure/cancellation
    message: Optional[Message] = None  # Associated message for input-required


class Task(BaseModel):
    """A2A Task - fundamental unit of work."""
    task_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    context_id: Optional[str] = None
    status: TaskStatus = Field(default_factory=TaskStatus)
    history: List[Message] = []
    artifacts: List[Artifact] = []
    metadata: Dict[str, Any] = {}
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class TaskStatusUpdateEvent(BaseModel):
    """Event for task status updates."""
    task_id: str
    status: TaskStatus
    is_final: bool = False


class TaskArtifactUpdateEvent(BaseModel):
    """Event for task artifact updates."""
    task_id: str
    artifact: Artifact
    is_final: bool = False


class AgentSkill(BaseModel):
    """A2A Agent Skill definition."""
    id: str
    name: str
    description: str
    tags: List[str] = []
    examples: List[str] = []
    input_modes: List[str] = ["text"]
    output_modes: List[str] = ["text"]


class AgentCapabilities(BaseModel):
    """A2A Agent capabilities."""
    streaming: bool = True
    push_notifications: bool = False
    extended_agent_card: bool = False


class AgentCard(BaseModel):
    """A2A Agent Card - metadata describing an agent."""
    agent_id: str
    name: str
    description: str
    version: str = "1.0.0"
    url: str  # Base URL for the agent
    capabilities: AgentCapabilities = Field(default_factory=AgentCapabilities)
    skills: List[AgentSkill] = []
    default_input_modes: List[str] = ["text"]
    default_output_modes: List[str] = ["text"]
    documentation_url: Optional[str] = None
    provider: Optional[Dict[str, str]] = None  # {organization, url}


# ============================================================================
# Request/Response Models
# ============================================================================

class SendMessageRequest(BaseModel):
    """A2A SendMessage request."""
    message: Message
    configuration: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = {}


class SendMessageResponse(BaseModel):
    """A2A SendMessage response."""
    task: Optional[Task] = None
    message: Optional[Message] = None  # Direct response for simple interactions


class StreamResponse(BaseModel):
    """A2A Stream response wrapper."""
    task: Optional[Task] = None
    message: Optional[Message] = None
    status_update: Optional[TaskStatusUpdateEvent] = None
    artifact_update: Optional[TaskArtifactUpdateEvent] = None


class ListTasksRequest(BaseModel):
    """A2A ListTasks request."""
    context_id: Optional[str] = None
    status: Optional[TaskState] = None
    page_size: int = 50
    page_token: Optional[str] = None
    history_length: Optional[int] = None


class ListTasksResponse(BaseModel):
    """A2A ListTasks response."""
    tasks: List[Task] = []
    next_page_token: str = ""
    page_size: int
    total_size: int


class GetTaskRequest(BaseModel):
    """A2A GetTask request."""
    task_id: str
    history_length: Optional[int] = None


class CancelTaskRequest(BaseModel):
    """A2A CancelTask request."""
    task_id: str
    metadata: Dict[str, Any] = {}


class A2AError(BaseModel):
    """A2A Error response."""
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None


# ============================================================================
# A2A Service
# ============================================================================

class A2AService:
    """
    A2A Protocol Service.
    
    Provides A2A-compliant endpoints for external agent systems to:
    - Discover agent capabilities (Agent Card)
    - Send messages and receive responses
    - Manage tasks (get, list, cancel)
    - Stream updates in real-time
    """
    
    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        self.contexts: Dict[str, List[str]] = {}  # context_id -> [task_ids]
        
    # ------------------------------------------------------------------------
    # Agent Card
    # ------------------------------------------------------------------------
    
    def get_agent_card(self, base_url: str) -> AgentCard:
        """
        Get the Agent Card describing this agent's capabilities.
        
        Args:
            base_url: Base URL for this agent
            
        Returns:
            AgentCard with capabilities and skills
        """
        from openharness.enterprise.agents.registry import get_agent_registry
        
        registry = get_agent_registry()
        agents = registry.list_agents()
        
        # Convert internal agents to A2A skills
        skills = []
        for agent in agents:
            skill = AgentSkill(
                id=agent.id,
                name=agent.name,
                description=agent.description or f"{agent.role.value} agent",
                tags=[agent.role.value],
                input_modes=["text", "data"],
                output_modes=["text", "data"]
            )
            skills.append(skill)
        
        # Add built-in skills from skills directory
        from openharness.enterprise.users.workspace import get_shared_root
        shared_skills_path = get_shared_root() / "skills"
        if shared_skills_path.exists():
            for skill_dir in shared_skills_path.iterdir():
                if skill_dir.is_dir():
                    skill_file = skill_dir / "SKILL.md"
                    if skill_file.exists():
                        try:
                            content = skill_file.read_text(encoding="utf-8")
                            # Extract description from first heading
                            desc = skill_dir.name
                            for line in content.split("\n")[:10]:
                                if line.startswith("# "):
                                    desc = line[2:].strip()
                                    break
                            
                            skill = AgentSkill(
                                id=skill_dir.name,
                                name=desc,
                                description=f"Skill: {desc}",
                                tags=["skill"],
                                input_modes=["text"],
                                output_modes=["text"]
                            )
                            skills.append(skill)
                        except Exception:
                            pass
        
        return AgentCard(
            agent_id="zzchatops-zhenxiaowei",
            name="zzchatops 真小维",
            description="企业级多用户 AI 智能体平台，支持多智能体协作、工具调用、技能扩展",
            version="1.0.0",
            url=base_url,
            capabilities=AgentCapabilities(
                streaming=True,
                push_notifications=False,
                extended_agent_card=True
            ),
            skills=skills,
            default_input_modes=["text", "data"],
            default_output_modes=["text", "data"],
            documentation_url=f"{base_url}/docs",
            provider={
                "organization": "zzchatops",
                "url": "https://github.com/openclaw/openclaw"
            }
        )
    
    # ------------------------------------------------------------------------
    # Send Message
    # ------------------------------------------------------------------------
    
    async def send_message(
        self,
        request: SendMessageRequest,
        user_id: int,
        base_url: str
    ) -> SendMessageResponse:
        """
        Send a message to the agent and get a response.
        
        Args:
            request: SendMessage request
            user_id: User ID making the request
            base_url: Base URL for this agent
            
        Returns:
            SendMessageResponse with Task or Message
        """
        from openharness.enterprise.llm.client import get_llm_client
        from openharness.enterprise.users.workspace import get_enterprise_root
        from openharness.enterprise.storage.database import get_database
        
        # Extract text content from message parts
        text_parts = [p.text for p in request.message.parts if p.text]
        user_message = "\n".join(text_parts)
        
        if not user_message:
            return SendMessageResponse(
                message=Message(
                    role="agent",
                    parts=[Part(type=PartType.TEXT, text="请提供有效的消息内容")]
                )
            )
        
        # Create or get task
        task = Task(
            context_id=request.message.context_id,
            status=TaskStatus(state=TaskState.RUNNING),
            history=[request.message],
            metadata={"user_id": user_id, **request.metadata}
        )
        
        # Store task
        self.tasks[task.task_id] = task
        
        # Link to context
        if task.context_id:
            if task.context_id not in self.contexts:
                self.contexts[task.context_id] = []
            self.contexts[task.context_id].append(task.task_id)
        
        try:
            # Get LLM client and process
            llm_client = get_llm_client()
            skills_path = str(get_enterprise_root() / "users" / str(user_id) / "skills")
            
            # Get agent config
            agent_id = request.metadata.get("agent_id", "planner")
            
            # Stream response and collect
            response_text = ""
            async for chunk in llm_client.stream_chat(
                messages=[{"role": "user", "content": user_message}],
                skills_base_path=skills_path
            ):
                response_text += chunk
            
            # Create response message
            response_message = Message(
                role="agent",
                parts=[Part(type=PartType.TEXT, text=response_text)],
                context_id=task.context_id,
                task_id=task.task_id
            )
            
            # Update task
            task.history.append(response_message)
            task.status = TaskStatus(state=TaskState.COMPLETED)
            task.updated_at = datetime.utcnow().isoformat()
            
            # Save to database
            db = get_database()
            db_session = db.create_session(user_id, title=user_message[:50])
            db.add_message(db_session.id, "user", user_message)
            db.add_message(db_session.id, "agent", response_text)
            
            # Return based on configuration
            return_immediately = request.configuration.get("return_immediately", False) if request.configuration else False
            
            if return_immediately:
                return SendMessageResponse(task=task)
            else:
                return SendMessageResponse(
                    task=task,
                    message=response_message
                )
                
        except Exception as e:
            task.status = TaskStatus(
                state=TaskState.FAILED,
                reason=str(e)
            )
            task.updated_at = datetime.utcnow().isoformat()
            return SendMessageResponse(task=task)
    
    async def send_streaming_message(
        self,
        request: SendMessageRequest,
        user_id: int,
        base_url: str
    ) -> AsyncGenerator[StreamResponse, None]:
        """
        Send a message and stream the response.
        
        Args:
            request: SendMessage request
            user_id: User ID making the request
            base_url: Base URL for this agent
            
        Yields:
            StreamResponse events
        """
        from openharness.enterprise.llm.client import get_llm_client
        from openharness.enterprise.users.workspace import get_enterprise_root
        from openharness.enterprise.storage.database import get_database
        
        # Extract text content
        text_parts = [p.text for p in request.message.parts if p.text]
        user_message = "\n".join(text_parts)
        
        if not user_message:
            yield StreamResponse(
                message=Message(
                    role="agent",
                    parts=[Part(type=PartType.TEXT, text="请提供有效的消息内容")]
                )
            )
            return
        
        # Create task
        task = Task(
            context_id=request.message.context_id,
            status=TaskStatus(state=TaskState.RUNNING),
            history=[request.message],
            metadata={"user_id": user_id, **request.metadata}
        )
        
        self.tasks[task.task_id] = task
        
        # Yield initial task
        yield StreamResponse(task=task)
        
        # Link to context
        if task.context_id:
            if task.context_id not in self.contexts:
                self.contexts[task.context_id] = []
            self.contexts[task.context_id].append(task.task_id)
        
        try:
            llm_client = get_llm_client()
            skills_path = str(get_enterprise_root() / "users" / str(user_id) / "skills")
            agent_id = request.metadata.get("agent_id", "planner")
            
            # Stream response
            response_text = ""
            async for chunk in llm_client.stream_chat(
                messages=[{"role": "user", "content": user_message}],
                skills_base_path=skills_path
            ):
                response_text += chunk
                
                # Yield artifact update with partial content
                artifact = Artifact(
                    name="response",
                    parts=[Part(type=PartType.TEXT, text=response_text)]
                )
                yield StreamResponse(
                    artifact_update=TaskArtifactUpdateEvent(
                        task_id=task.task_id,
                        artifact=artifact,
                        is_final=False
                    )
                )
            
            # Create final message
            response_message = Message(
                role="agent",
                parts=[Part(type=PartType.TEXT, text=response_text)],
                context_id=task.context_id,
                task_id=task.task_id
            )
            
            # Update task
            task.history.append(response_message)
            task.status = TaskStatus(state=TaskState.COMPLETED)
            task.updated_at = datetime.utcnow().isoformat()
            
            # Save to database
            db = get_database()
            db_session = db.create_session(user_id, title=user_message[:50])
            db.add_message(db_session.id, "user", user_message)
            db.add_message(db_session.id, "agent", response_text)
            
            # Yield final status update
            yield StreamResponse(
                status_update=TaskStatusUpdateEvent(
                    task_id=task.task_id,
                    status=task.status,
                    is_final=True
                )
            )
            
        except Exception as e:
            task.status = TaskStatus(
                state=TaskState.FAILED,
                reason=str(e)
            )
            task.updated_at = datetime.utcnow().isoformat()
            
            yield StreamResponse(
                status_update=TaskStatusUpdateEvent(
                    task_id=task.task_id,
                    status=task.status,
                    is_final=True
                )
            )
    
    # ------------------------------------------------------------------------
    # Task Management
    # ------------------------------------------------------------------------
    
    def get_task(self, task_id: str, history_length: Optional[int] = None) -> Optional[Task]:
        """Get task by ID."""
        task = self.tasks.get(task_id)
        if task and history_length is not None:
            # Limit history
            task = task.copy()
            task.history = task.history[-history_length:] if history_length > 0 else []
        return task
    
    def list_tasks(
        self,
        context_id: Optional[str] = None,
        status: Optional[TaskState] = None,
        page_size: int = 50,
        page_token: Optional[str] = None,
        user_id: Optional[int] = None
    ) -> ListTasksResponse:
        """List tasks with filtering."""
        tasks = list(self.tasks.values())
        
        # Filter by context
        if context_id:
            task_ids = self.contexts.get(context_id, [])
            tasks = [t for t in tasks if t.task_id in task_ids]
        
        # Filter by status
        if status:
            tasks = [t for t in tasks if t.status.state == status]
        
        # Filter by user
        if user_id:
            tasks = [t for t in tasks if t.metadata.get("user_id") == user_id]
        
        # Sort by updated_at descending
        tasks.sort(key=lambda t: t.updated_at, reverse=True)
        
        # Pagination
        total_size = len(tasks)
        start_idx = 0
        if page_token:
            try:
                start_idx = int(page_token)
            except ValueError:
                pass
        
        end_idx = start_idx + page_size
        page_tasks = tasks[start_idx:end_idx]
        
        next_page_token = ""
        if end_idx < total_size:
            next_page_token = str(end_idx)
        
        return ListTasksResponse(
            tasks=page_tasks,
            next_page_token=next_page_token,
            page_size=page_size,
            total_size=total_size
        )
    
    def cancel_task(self, task_id: str) -> Optional[Task]:
        """Cancel a task."""
        task = self.tasks.get(task_id)
        if not task:
            return None
        
        if task.status.state in (TaskState.COMPLETED, TaskState.FAILED, TaskState.CANCELED):
            return None  # Cannot cancel terminal tasks
        
        task.status = TaskStatus(state=TaskState.CANCELED)
        task.updated_at = datetime.utcnow().isoformat()
        
        return task


# ============================================================================
# Singleton
# ============================================================================

_a2a_service: Optional[A2AService] = None


def get_a2a_service() -> A2AService:
    """Get the A2A service singleton."""
    global _a2a_service
    if _a2a_service is None:
        _a2a_service = A2AService()
    return _a2a_service