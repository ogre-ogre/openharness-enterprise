"""
OpenHarness Enterprise - Agent Team Configuration

Multi-agent team configuration and management.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from enum import Enum


class AgentRole(str, Enum):
    """Agent role types."""
    PLANNER = "planner"      # 方案制定
    EXECUTOR = "executor"    # 方案执行
    REVIEWER = "reviewer"    # 审查评估
    ANALYST = "analyst"      # 分析师
    DEVELOPER = "developer"  # 开发者
    TESTER = "tester"        # 测试员
    CUSTOM = "custom"        # 自定义


class AgentConfig(BaseModel):
    """Agent configuration."""
    id: str
    name: str
    role: AgentRole = AgentRole.CUSTOM
    description: str = ""
    system_prompt: str
    model: str = "glm-5"
    max_tokens: int = 4096
    temperature: float = 0.7
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class TeamConfig(BaseModel):
    """Agent team configuration."""
    id: str
    name: str
    description: str = ""
    agents: List[str]  # Agent IDs
    workflow: str = "sequential"  # sequential | parallel | custom
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# Default agents
DEFAULT_AGENTS = [
    AgentConfig(
        id="planner",
        name="方案制定专家",
        role=AgentRole.PLANNER,
        description="负责分析需求、制定详细方案和执行计划",
        system_prompt="""你是一个专业的方案制定专家。

## 职责
1. 深入理解用户需求
2. 分析可行性和风险
3. 制定详细的执行方案
4. 将方案分解为具体步骤

## 输出格式
请按以下结构输出方案：
### 需求理解
[对需求的理解]

### 方案概述
[整体方案描述]

### 执行步骤
1. [步骤1]
2. [步骤2]
...

### 风险提示
[可能的风险和注意事项]

### 预期成果
[预期的最终成果]
""",
        created_at=datetime.utcnow()
    ),
    AgentConfig(
        id="executor",
        name="方案执行专家",
        role=AgentRole.EXECUTOR,
        description="负责按照方案执行具体任务",
        system_prompt="""你是一个专业的方案执行专家。

## 职责
1. 严格按照方案步骤执行
2. 记录执行过程和结果
3. 遇到问题及时反馈
4. 确保任务完成质量

## 工作原则
- 严格按照方案执行，不随意变更
- 详细记录每一步的执行情况
- 遇到问题先尝试解决，无法解决时标记并说明
- 执行完成后进行自检

## 输出格式
请按以下结构汇报执行情况：
### 执行进度
- [x] 已完成步骤
- [ ] 待完成步骤

### 执行详情
[每个步骤的执行细节]

### 问题记录
[遇到的问题及解决方案]

### 执行结果
[最终执行结果]
""",
        created_at=datetime.utcnow()
    ),
    AgentConfig(
        id="reviewer",
        name="质量审查专家",
        role=AgentRole.REVIEWER,
        description="负责审查方案和执行结果的质量",
        system_prompt="""你是一个专业的质量审查专家。

## 职责
1. 审查方案的合理性
2. 检查执行的完整性
3. 评估结果的质量
4. 提出改进建议

## 审查维度
- 完整性：是否覆盖所有要求
- 正确性：是否符合规范和标准
- 可行性：方案是否可执行
- 质量：结果是否达到预期

## 输出格式
### 审查结论
[通过/不通过/需修改]

### 详细评估
| 维度 | 评分 | 说明 |
|------|------|------|
| 完整性 | X/10 | ... |
| 正确性 | X/10 | ... |
| 可行性 | X/10 | ... |
| 质量 | X/10 | ... |

### 改进建议
1. [建议1]
2. [建议2]
...
""",
        created_at=datetime.utcnow()
    ),
    AgentConfig(
        id="analyst",
        name="需求分析师",
        role=AgentRole.ANALYST,
        description="负责深入分析需求和技术可行性",
        system_prompt="""你是一个专业的需求分析师。

## 职责
1. 深入理解业务需求
2. 分析技术可行性
3. 识别关键问题和风险
4. 提供专业建议

## 分析框架
- 业务价值：需求的核心价值是什么
- 技术难度：实现的技术复杂度
- 资源需求：需要哪些资源
- 时间预估：大致的开发周期
- 风险评估：可能的问题和风险
""",
        created_at=datetime.utcnow()
    ),
    AgentConfig(
        id="developer",
        name="开发工程师",
        role=AgentRole.DEVELOPER,
        description="负责具体的开发实现工作",
        system_prompt="""你是一个专业的开发工程师。

## 职责
1. 编写高质量代码
2. 遵循编码规范
3. 编写必要的测试
4. 编写技术文档

## 开发原则
- 代码简洁清晰
- 遵循 DRY、SOLID 原则
- 注重性能和安全
- 编写可维护的代码
""",
        created_at=datetime.utcnow()
    ),
    AgentConfig(
        id="tester",
        name="测试工程师",
        role=AgentRole.TESTER,
        description="负责功能测试和质量保证",
        system_prompt="""你是一个专业的测试工程师。

## 职责
1. 设计测试用例
2. 执行功能测试
3. 记录和跟踪缺陷
4. 验证修复结果

## 测试类型
- 功能测试：验证功能正确性
- 边界测试：测试边界条件
- 异常测试：测试异常情况
- 性能测试：测试性能表现
""",
        created_at=datetime.utcnow()
    ),
]

# Default teams
DEFAULT_TEAMS = [
    TeamConfig(
        id="planning-team",
        name="方案规划团队",
        description="负责方案制定和审查",
        agents=["analyst", "planner", "reviewer"],
        workflow="sequential",
        created_at=datetime.utcnow()
    ),
    TeamConfig(
        id="dev-team",
        name="开发团队",
        description="负责完整的开发流程",
        agents=["analyst", "planner", "developer", "tester", "reviewer"],
        workflow="sequential",
        created_at=datetime.utcnow()
    ),
    TeamConfig(
        id="execution-team",
        name="执行团队",
        description="负责方案执行和质量控制",
        agents=["planner", "executor", "reviewer"],
        workflow="sequential",
        created_at=datetime.utcnow()
    ),
]


class AgentRegistry:
    """
    Agent and Team registry.
    
    Manages agent configurations and team definitions.
    """
    
    def __init__(self, data_path: Optional[Path] = None):
        self.data_path = data_path or (Path.home() / ".oh-enterprise" / "agents")
        self.agents: Dict[str, AgentConfig] = {}
        self.teams: Dict[str, TeamConfig] = {}
        
        # Ensure directory exists
        self.data_path.mkdir(parents=True, exist_ok=True)
        
        # Load or initialize
        self._load_or_initialize()
    
    def _load_or_initialize(self) -> None:
        """Load from files or initialize with defaults."""
        agents_file = self.data_path / "agents.json"
        teams_file = self.data_path / "teams.json"
        
        if agents_file.exists():
            try:
                data = json.loads(agents_file.read_text(encoding="utf-8"))
                for agent_data in data:
                    agent = AgentConfig(**agent_data)
                    self.agents[agent.id] = agent
            except Exception:
                self._init_default_agents()
        else:
            self._init_default_agents()
        
        if teams_file.exists():
            try:
                data = json.loads(teams_file.read_text(encoding="utf-8"))
                for team_data in data:
                    team = TeamConfig(**team_data)
                    self.teams[team.id] = team
            except Exception:
                self._init_default_teams()
        else:
            self._init_default_teams()
    
    def _init_default_agents(self) -> None:
        """Initialize with default agents."""
        for agent in DEFAULT_AGENTS:
            self.agents[agent.id] = agent
        self._save_agents()
    
    def _init_default_teams(self) -> None:
        """Initialize with default teams."""
        for team in DEFAULT_TEAMS:
            self.teams[team.id] = team
        self._save_teams()
    
    def _save_agents(self) -> None:
        """Save agents to file."""
        agents_file = self.data_path / "agents.json"
        data = [agent.dict() for agent in self.agents.values()]
        agents_file.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
    
    def _save_teams(self) -> None:
        """Save teams to file."""
        teams_file = self.data_path / "teams.json"
        data = [team.dict() for team in self.teams.values()]
        teams_file.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
    
    # Agent operations
    def get_agent(self, agent_id: str) -> Optional[AgentConfig]:
        """Get agent by ID."""
        return self.agents.get(agent_id)
    
    def list_agents(self, active_only: bool = True) -> List[AgentConfig]:
        """List all agents."""
        agents = list(self.agents.values())
        if active_only:
            agents = [a for a in agents if a.is_active]
        return agents
    
    def create_agent(self, agent: AgentConfig) -> AgentConfig:
        """Create a new agent."""
        agent.created_at = datetime.utcnow()
        agent.updated_at = datetime.utcnow()
        self.agents[agent.id] = agent
        self._save_agents()
        return agent
    
    def update_agent(self, agent_id: str, **kwargs) -> Optional[AgentConfig]:
        """Update agent configuration."""
        agent = self.agents.get(agent_id)
        if not agent:
            return None
        
        for key, value in kwargs.items():
            if hasattr(agent, key):
                setattr(agent, key, value)
        
        agent.updated_at = datetime.utcnow()
        self._save_agents()
        return agent
    
    def delete_agent(self, agent_id: str) -> bool:
        """Delete an agent (soft delete by setting is_active=False)."""
        agent = self.agents.get(agent_id)
        if not agent:
            return False
        
        # Don't delete default agents, just deactivate
        if agent_id in [a.id for a in DEFAULT_AGENTS]:
            agent.is_active = False
        else:
            del self.agents[agent_id]
        
        self._save_agents()
        return True
    
    # Team operations
    def get_team(self, team_id: str) -> Optional[TeamConfig]:
        """Get team by ID."""
        return self.teams.get(team_id)
    
    def list_teams(self, active_only: bool = True) -> List[TeamConfig]:
        """List all teams."""
        teams = list(self.teams.values())
        if active_only:
            teams = [t for t in teams if t.is_active]
        return teams
    
    def create_team(self, team: TeamConfig) -> TeamConfig:
        """Create a new team."""
        team.created_at = datetime.utcnow()
        team.updated_at = datetime.utcnow()
        self.teams[team.id] = team
        self._save_teams()
        return team
    
    def update_team(self, team_id: str, **kwargs) -> Optional[TeamConfig]:
        """Update team configuration."""
        team = self.teams.get(team_id)
        if not team:
            return None
        
        for key, value in kwargs.items():
            if hasattr(team, key):
                setattr(team, key, value)
        
        team.updated_at = datetime.utcnow()
        self._save_teams()
        return team
    
    def delete_team(self, team_id: str) -> bool:
        """Delete a team."""
        if team_id not in self.teams:
            return False
        
        del self.teams[team_id]
        self._save_teams()
        return True
    
    def get_team_agents(self, team_id: str) -> List[AgentConfig]:
        """Get all agents in a team."""
        team = self.teams.get(team_id)
        if not team:
            return []
        
        return [self.agents[aid] for aid in team.agents if aid in self.agents]


# Singleton instance
_registry: Optional[AgentRegistry] = None


def get_agent_registry() -> AgentRegistry:
    """Get agent registry instance."""
    global _registry
    if _registry is None:
        _registry = AgentRegistry()
    return _registry