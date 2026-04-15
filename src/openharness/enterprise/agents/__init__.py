"""
OpenHarness Enterprise - Multi-Agent System

Team-based multi-agent collaboration system.
"""

from openharness.enterprise.agents.registry import (
    AgentConfig,
    AgentRole,
    TeamConfig,
    AgentRegistry,
    get_agent_registry,
)
from openharness.enterprise.agents.coordinator import (
    TeamCoordinator,
    TeamSession,
    AgentMessage,
    get_team_coordinator,
)

__all__ = [
    "AgentConfig",
    "AgentRole",
    "TeamConfig",
    "AgentRegistry",
    "get_agent_registry",
    "TeamCoordinator",
    "TeamSession",
    "AgentMessage",
    "get_team_coordinator",
]