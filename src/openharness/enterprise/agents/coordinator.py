"""
OpenHarness Enterprise - Agent Team Coordinator

Coordinates multiple agents working together on tasks.
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any, AsyncGenerator
from pydantic import BaseModel
from enum import Enum

from openharness.enterprise.agents.registry import (
    AgentRegistry, AgentConfig, TeamConfig, get_agent_registry
)
from openharness.enterprise.llm.client import get_llm_client
from openharness.enterprise.config.provider import get_provider_config


class AgentMessage(BaseModel):
    """Message from an agent."""
    agent_id: str
    agent_name: str
    role: str
    content: str
    timestamp: str = ""
    
    def __init__(self, **data):
        super().__init__(**data)
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()


class TeamSession(BaseModel):
    """Team collaboration session."""
    id: str
    team_id: str
    task: str
    context: Dict[str, Any] = {}
    messages: List[AgentMessage] = []
    status: str = "running"  # running | completed | failed
    current_agent: Optional[str] = None
    created_at: str = ""
    updated_at: str = ""
    
    def __init__(self, **data):
        super().__init__(**data)
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()
        if not self.updated_at:
            self.updated_at = self.created_at


class TeamCoordinator:
    """
    Coordinates multiple agents working together.
    
    Features:
    - Sequential workflow: agents work one by one
    - Shared context: all agents see previous outputs
    - Task handoff: agents pass results to next agent
    """
    
    def __init__(self):
        self.registry = get_agent_registry()
        self.llm_client = get_llm_client()
        self.sessions: Dict[str, TeamSession] = {}
    
    def create_session(self, team_id: str, task: str, context: Dict[str, Any] = None) -> TeamSession:
        """
        Create a new team session.
        
        Args:
            team_id: Team ID
            task: The task to accomplish
            context: Additional context (files, requirements, etc.)
        
        Returns:
            TeamSession
        """
        session = TeamSession(
            id=str(uuid.uuid4()),
            team_id=team_id,
            task=task,
            context=context or {}
        )
        
        self.sessions[session.id] = session
        return session
    
    def get_session(self, session_id: str) -> Optional[TeamSession]:
        """Get session by ID."""
        return self.sessions.get(session_id)
    
    async def run_sequential(
        self,
        session: TeamSession,
        on_message: Optional[callable] = None
    ) -> AsyncGenerator[AgentMessage, None]:
        """
        Run agents sequentially.
        
        Each agent sees all previous agents' outputs.
        
        Args:
            session: Team session
            on_message: Callback for each message
        
        Yields:
            AgentMessage from each agent
        """
        team = self.registry.get_team(session.team_id)
        if not team:
            raise ValueError(f"Team {session.team_id} not found")
        
        agents = self.registry.get_team_agents(session.team_id)
        if not agents:
            raise ValueError(f"No agents found for team {session.team_id}")
        
        config = get_provider_config()
        
        # Build shared context from previous messages
        shared_context = self._build_shared_context(session)
        
        for agent in agents:
            session.current_agent = agent.id
            session.updated_at = datetime.utcnow().isoformat()
            
            # Build messages for this agent
            messages = self._build_agent_messages(session, agent, shared_context)
            
            # Build system prompt
            system_prompt = self._build_system_prompt(agent, session)
            
            # Call LLM
            try:
                full_response = ""
                async for chunk in self.llm_client.stream_chat(
                    messages=messages,
                    system_prompt=system_prompt,
                    skills=[]
                ):
                    full_response += chunk
                
                # Create message
                msg = AgentMessage(
                    agent_id=agent.id,
                    agent_name=agent.name,
                    role=agent.role.value,
                    content=full_response
                )
                
                # Add to session
                session.messages.append(msg)
                session.updated_at = datetime.utcnow().isoformat()
                
                # Update shared context
                shared_context.append({
                    "agent": agent.name,
                    "role": agent.role.value,
                    "output": full_response
                })
                
                # Yield message
                yield msg
                
                # Callback
                if on_message:
                    await on_message(msg)
                    
            except Exception as e:
                # Error message
                msg = AgentMessage(
                    agent_id=agent.id,
                    agent_name=agent.name,
                    role=agent.role.value,
                    content=f"[错误] Agent 执行失败: {str(e)}"
                )
                session.messages.append(msg)
                yield msg
        
        # Mark session as completed
        session.status = "completed"
        session.current_agent = None
        session.updated_at = datetime.utcnow().isoformat()
    
    async def run_parallel(
        self,
        session: TeamSession,
        on_message: Optional[callable] = None
    ) -> AsyncGenerator[AgentMessage, None]:
        """
        Run agents in parallel.
        
        All agents work independently on the same task.
        
        Args:
            session: Team session
            on_message: Callback for each message
        
        Yields:
            AgentMessage from each agent (order not guaranteed)
        """
        team = self.registry.get_team(session.team_id)
        if not team:
            raise ValueError(f"Team {session.team_id} not found")
        
        agents = self.registry.get_team_agents(session.team_id)
        if not agents:
            raise ValueError(f"No agents found for team {session.team_id}")
        
        # Run all agents concurrently
        tasks = []
        for agent in agents:
            task = self._run_single_agent(session, agent, on_message)
            tasks.append(task)
        
        # Collect results
        for coro in asyncio.as_completed(tasks):
            msg = await coro
            session.messages.append(msg)
            session.updated_at = datetime.utcnow().isoformat()
            yield msg
        
        session.status = "completed"
        session.updated_at = datetime.utcnow().isoformat()
    
    async def _run_single_agent(
        self,
        session: TeamSession,
        agent: AgentConfig,
        on_message: Optional[callable] = None
    ) -> AgentMessage:
        """Run a single agent."""
        messages = [{"role": "user", "content": session.task}]
        system_prompt = self._build_system_prompt(agent, session)
        
        try:
            full_response = ""
            async for chunk in self.llm_client.stream_chat(
                messages=messages,
                system_prompt=system_prompt,
                skills=[]
            ):
                full_response += chunk
            
            msg = AgentMessage(
                agent_id=agent.id,
                agent_name=agent.name,
                role=agent.role.value,
                content=full_response
            )
            
            if on_message:
                await on_message(msg)
            
            return msg
            
        except Exception as e:
            return AgentMessage(
                agent_id=agent.id,
                agent_name=agent.name,
                role=agent.role.value,
                content=f"[错误] {str(e)}"
            )
    
    def _build_shared_context(self, session: TeamSession) -> List[Dict[str, Any]]:
        """Build shared context from previous messages."""
        context = []
        for msg in session.messages:
            context.append({
                "agent": msg.agent_name,
                "role": msg.role,
                "output": msg.content
            })
        return context
    
    def _build_agent_messages(
        self,
        session: TeamSession,
        agent: AgentConfig,
        shared_context: List[Dict[str, Any]]
    ) -> List[Dict[str, str]]:
        """Build messages for an agent."""
        messages = []
        
        # Initial task
        task_msg = f"## 任务\n{session.task}\n"
        
        # Add context if provided
        if session.context:
            task_msg += "\n## 背景\n"
            for key, value in session.context.items():
                task_msg += f"- {key}: {value}\n"
        
        # Add shared context from previous agents
        if shared_context:
            task_msg += "\n## 前序工作成果\n"
            for ctx in shared_context:
                task_msg += f"\n### {ctx['agent']} ({ctx['role']})\n{ctx['output']}\n"
        
        messages.append({"role": "user", "content": task_msg})
        
        return messages
    
    def _build_system_prompt(self, agent: AgentConfig, session: TeamSession) -> str:
        """Build system prompt for an agent."""
        parts = [agent.system_prompt]
        
        # Add team context
        team = self.registry.get_team(session.team_id)
        if team:
            parts.append(f"\n\n---\n## 当前任务\n你正在参与团队「{team.name}」的协作任务。")
        
        return "\n".join(parts)
    
    def get_session_summary(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session summary."""
        session = self.sessions.get(session_id)
        if not session:
            return None
        
        return {
            "id": session.id,
            "team_id": session.team_id,
            "task": session.task,
            "status": session.status,
            "agent_count": len(session.messages),
            "messages": [
                {
                    "agent_id": m.agent_id,
                    "agent_name": m.agent_name,
                    "role": m.role,
                    "content": m.content[:200] + "..." if len(m.content) > 200 else m.content,
                    "timestamp": m.timestamp
                }
                for m in session.messages
            ],
            "created_at": session.created_at,
            "updated_at": session.updated_at
        }


# Singleton
_coordinator: Optional[TeamCoordinator] = None


def get_team_coordinator() -> TeamCoordinator:
    """Get team coordinator instance."""
    global _coordinator
    if _coordinator is None:
        _coordinator = TeamCoordinator()
    return _coordinator