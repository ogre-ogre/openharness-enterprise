# OpenHarness Enterprise 多用户版本设计文档

> 版本: v1.0  
> 日期: 2024-04-08  
> 作者: OpenClaw Agent

---

## 1. 概述

### 1.1 项目背景

基于 OpenHarness 开源项目进行二次开发，添加企业级功能，支持：
- 服务端部署
- 多用户访问
- 用户独立工作区（记忆文件、配置）
- 内部员工使用场景

### 1.2 需求总结

| 维度 | 选择 |
|-----|------|
| 使用场景 | 内部员工生产力工具 |
| 认证方式 | 内置用户表 + 管理员管理 |
| 架构策略 | 最小改动，复用原有逻辑 |
| 访问方式 | Web 界面为主 |
| 工作区 | 用户隔离 + 可共享 skills/plugins |
| 存储 | 混合：文件（配置/记忆）+ 数据库（会话/审计） |
| 部署 | 单机部署（<100用户） |

---

## 2. 整体架构

### 2.1 架构图

```
┌─────────────────────────────────────────────────────────────┐
│                    OpenHarness Enterprise                    │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │                    Gateway Layer                        │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌───────────────┐ │ │
│  │  │ WebChat      │  │ Auth         │  │ Admin API     │ │ │
│  │  │ Channel      │  │ Middleware   │  │ (管理接口)    │ │ │
│  │  │ (WebSocket)  │  │              │  │               │ │ │
│  │  └──────────────┘  └──────────────┘  └───────────────┘ │ │
│  └────────────────────────────────────────────────────────┘ │
│                           │                                  │
│  ┌────────────────────────────────────────────────────────┐ │
│  │                    Agent Engine                         │ │
│  │            (复用 src/openharness/engine/)               │ │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐         │ │
│  │  │ Tool Loop  │ │ Memory     │ │ Skills     │         │ │
│  │  │            │ │ Manager    │ │ Loader     │         │ │
│  │  └────────────┘ └────────────┘ └────────────┘         │ │
│  └────────────────────────────────────────────────────────┘ │
│                           │                                  │
│  ┌────────────────────────────────────────────────────────┐ │
│  │                    User Context                         │ │
│  │  ┌───────────────────────────────────────────────────┐ │ │
│  │  │  User Workspaces                                  │ │ │
│  │  │  ~/.oh-enterprise/users/{user_id}/                │ │ │
│  │  │    ├── memory/         # 用户记忆文件            │ │ │
│  │  │    ├── sessions/       # 会话历史 (按日期)        │ │ │
│  │  │    ├── config/         # 用户偏好配置            │ │ │
│  │  │    └── soul.md         # 用户定制人格            │ │ │
│  │  └───────────────────────────────────────────────────┘ │ │
│  │  ┌───────────────────────────────────────────────────┐ │ │
│  │  │  Shared Resources Pool                            │ │ │
│  │  │  ~/.oh-enterprise/shared/                         │ │ │
│  │  │    ├── skills/        # 企业级共享 skills        │ │ │
│  │  │    ├── plugins/       # 企业级共享 plugins       │ │ │
│  │  │    └── templates/     # Prompt 模板库            │ │ │
│  │  └───────────────────────────────────────────────────┘ │ │
│  └────────────────────────────────────────────────────────┘ │
│                           │                                  │
│  ┌────────────────────────────────────────────────────────┐ │
│  │                    Storage Layer                       │ │
│  │  ┌──────────────────┐  ┌────────────────────────────┐ │ │
│  │  │ SQLite Database  │  │ File System                │ │ │
│  │  │ ~/.oh-enterprise │  │ (用户工作区 + 共享资源)    │ │ │
│  │  │  /data.db        │  │                            │ │ │
│  │  │  - users 表      │  │                            │ │ │
│  │  │  - sessions 表   │  │                            │ │ │
│  │  │  - audit_logs 表 │  │                            │ │ │
│  │  └──────────────────┘  └────────────────────────────┘ │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                            │
                    ┌───────┴───────┐
                    │   Web Frontend │
                    │   (React SPA)  │
                    │   /chat        │
                    │   /admin       │
                    └────────────────┘
```

### 2.2 新增目录结构

```
openharness-enterprise/
├── src/openharness/
│   ├── ... (原有模块保持不变)
│   ├── enterprise/           # 新增企业版模块
│   │   ├── __init__.py
│   │   ├── users/            # 用户管理
│   │   │   ├── auth.py       # 认证逻辑
│   │   │   ├── manager.py    # 用户 CRUD
│   │   │   ├── workspace.py  # 工作区管理
│   │   │   └── context.py    # 用户上下文注入
│   │   ├── admin/            # 管理接口
│   │   │   ├── api.py        # Admin REST API
│   │   │   └── shared.py     # 共享资源管理
│   │   ├── channels/         # 扩展 channels
│   │   │   └── webchat.py    # WebChat channel
│   │   ├── storage/          # 存储层
│   │   │   ├── database.py   # SQLite 操作
│   │   │   └── audit.py      # 审计日志
│   │   └── server.py         # 主服务入口
│   └── web/                  # Web 前端 (可选目录)
```

---

## 3. 数据模型与存储

### 3.1 数据库表结构

```sql
-- 用户表
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    display_name TEXT,
    email TEXT,
    role TEXT DEFAULT 'user',              -- 'user' | 'admin'
    is_active BOOLEAN DEFAULT TRUE,
    api_key TEXT UNIQUE,                   -- 用户 API Key（用于内部系统获取 Token）
    api_key_enabled BOOLEAN DEFAULT TRUE,  -- API Key 是否启用
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP,
    last_api_key_used_at TIMESTAMP         -- API Key 最后使用时间
);

-- 会话表
CREATE TABLE sessions (
    id TEXT PRIMARY KEY,            -- UUID
    user_id INTEGER NOT NULL,
    title TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP,
    message_count INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- 消息表（可选，用于检索历史）
CREATE TABLE messages (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    role TEXT NOT NULL,             -- 'user' | 'assistant' | 'system'
    content TEXT,
    tokens_used INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);

-- 审计日志表
CREATE TABLE audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    action TEXT NOT NULL,           -- 'login' | 'chat' | 'admin_create_user' 等
    resource_type TEXT,
    resource_id TEXT,
    details TEXT,                   -- JSON 详情
    ip_address TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- 共享资源权限表
CREATE TABLE shared_resource_permissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    resource_type TEXT NOT NULL,    -- 'skill' | 'plugin' | 'template'
    resource_name TEXT NOT NULL,
    user_id INTEGER,                -- NULL 表示所有人可访问
    permission TEXT DEFAULT 'read', -- 'read' | 'write' | 'admin'
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

### 3.2 文件系统结构

```
~/.oh-enterprise/
├── data.db                    # SQLite 数据库
├── config.json                # 全局配置
├── users/
│   ├── {user_id_1}/
│   │   ├── memory/
│   │   │   ├── MEMORY.md      # 长期记忆
│   │   │   ├── 2024-04-08.md  # 日记文件
│   │   │   └── heartbeat-state.json
│   │   ├── sessions/
│   │   │   └── {session_id}.json  # 会话详情
│   │   ├── config/
│   │   │   ├── preferences.json   # 用户偏好
│   │   │   └── provider.json      # 用户 provider 配置
│   │   └── soul.md            # 用户定制人格
│   ├── {user_id_2}/
│   │   └── ... (同上)
│   └── ...
├── shared/
│   ├── skills/
│   │   ├── enterprise-knowledge/
│   │   │   └── SKILL.md
│   │   └── common-tools/
│   │       └── SKILL.md
│   ├── plugins/
│   │   └── enterprise-plugin/
│   └── templates/
│       ├── default-soul.md
│       └── welcome-prompt.md
└── logs/
    └── audit-2024-04-08.log   # 审计日志文件（备份）
```

---

## 4. Web Chat Channel

### 4.1 WebSocket 通信协议

```
客户端 → 服务端消息格式：
{
    "type": "message" | "command" | "resume",
    "payload": {
        "content": "用户输入内容",
        "session_id": "可选，用于恢复会话"
    }
}

服务端 → 客户端消息格式：
{
    "type": "text" | "tool_call" | "tool_result" | "thinking" | "error" | "done",
    "payload": {
        "content": "内容",
        "tool_name": "工具名（type=tool_call时）",
        "tool_args": {},
        "session_id": "会话ID"
    }
}
```

### 4.2 WebChat Channel 核心类

```python
# src/openharness/enterprise/channels/webchat.py

class WebChatChannel:
    """
    WebSocket-based chat channel for web interface.
    
    Features:
    - 用户认证（JWT token 验证）
    - 会话管理（创建、恢复、历史）
    - 流式响应（实时推送 agent 输出）
    - 权限控制（确保用户只能访问自己的资源）
    """
    
    def __init__(self, config: WebChatConfig):
        self.user_manager = UserManager()
        self.workspace_manager = WorkspaceManager()
        self.audit_logger = AuditLogger()
        self.agent_engine = AgentEngine()  # 复用原有 engine
    
    async def handle_connection(self, websocket, user_id: str):
        """处理 WebSocket 连接"""
        # 1. 加载用户上下文
        user_context = self.workspace_manager.load_context(user_id)
        
        # 2. 创建或恢复会话
        session = self.session_manager.get_or_create(user_id)
        
        # 3. 初始化 Agent（注入用户上下文）
        agent = self.agent_engine.create_agent(
            memory_path=user_context.memory_path,
            skills=user_context.available_skills,
            soul=user_context.soul
        )
        
        # 4. 消息循环
        async for message in websocket:
            await self.handle_message(websocket, agent, message)
    
    async def handle_message(self, websocket, agent, message):
        """处理单条消息，流式推送响应"""
        # 记录审计日志
        self.audit_logger.log(user_id, "chat", message)
        
        # 调用 Agent Engine，流式获取响应
        for chunk in agent.run_stream(message.content):
            await websocket.send_json({
                "type": chunk.type,
                "payload": chunk.to_dict()
            })
        
        # 发送完成信号
        await websocket.send_json({"type": "done"})
```

### 4.3 用户上下文注入

```python
# src/openharness/enterprise/users/context.py

class UserContext:
    """
    用户运行时上下文，注入到 Agent Engine。
    
    包含：
    - memory_path: 用户记忆目录路径
    - soul: 用户定制的人格内容
    - available_skills: 用户可用 skills 列表（个人 + 共享）
    - config: 用户偏好配置
    """
    
    memory_path: str
    soul: str
    available_skills: List[str]
    config: dict

class WorkspaceManager:
    """管理工作区加载和上下文构建"""
    
    def load_context(self, user_id: str) -> UserContext:
        workspace_path = self.get_workspace_path(user_id)
        
        # 加载记忆
        memory_path = f"{workspace_path}/memory"
        
        # 加载人格
        soul_path = f"{workspace_path}/soul.md"
        soul = self.load_file(soul_path) or self.get_default_soul()
        
        # 加载可用 skills（个人 + 共享）
        personal_skills = self.scan_skills(f"{workspace_path}/skills")
        shared_skills = self.get_shared_skills_for_user(user_id)
        
        return UserContext(
            memory_path=memory_path,
            soul=soul,
            available_skills=personal_skills + shared_skills,
            config=self.load_config(workspace_path)
        )
```

---

## 5. Admin API

### 5.1 API 端点

```
/api/admin/                    # 管理员专用接口（需 admin 角色）

# 用户管理
POST   /api/admin/users              # 创建用户
GET    /api/admin/users              # 用户列表（支持搜索）
GET    /api/admin/users/{id}         # 用户详情
PUT    /api/admin/users/{id}         # 更新用户信息
DELETE /api/admin/users/{id}         # 删除用户（禁用）
POST   /api/admin/users/{id}/reset-password  # 重置密码

# 用户 API Key 管理
GET    /api/admin/users/{id}/api-key       # 查看用户 API Key
POST   /api/admin/users/{id}/api-key/regenerate  # 重新生成 API Key
PUT    /api/admin/users/{id}/api-key/status      # 启用/禁用 API Key

# 共享资源管理
GET    /api/admin/shared/skills      # 共享 skills 列表
POST   /api/admin/shared/skills      # 上传新 skill
DELETE /api/admin/shared/skills/{name}  # 删除 skill
PUT    /api/admin/shared/skills/{name}/permissions  # 设置权限

GET    /api/admin/shared/plugins     # 共享 plugins 列表
POST   /api/admin/shared/plugins     # 上传新 plugin

# 系统管理
GET    /api/admin/system/status      # 系统状态
GET    /api/admin/system/config      # 全局配置
PUT    /api/admin/system/config      # 更新全局配置
GET    /api/admin/audit-logs         # 审计日志查询

# Provider 管理
GET    /api/admin/providers          # 可用 provider 列表
PUT    /api/admin/providers/default  # 设置默认 provider
```

### 5.2 核心实现

```python
# src/openharness/enterprise/admin/api.py

from fastapi import APIRouter, Depends, HTTPException
from .auth import require_admin

router = APIRouter(prefix="/api/admin", dependencies=[Depends(require_admin)])

# 用户管理
@router.post("/users")
async def create_user(user_data: CreateUserRequest):
    """创建新用户"""
    if user_manager.exists(user_data.username):
        raise HTTPException(400, "用户名已存在")
    
    user = user_manager.create(
        username=user_data.username,
        password=user_data.password,
        display_name=user_data.display_name,
        role=user_data.role or "user"
    )
    
    workspace_manager.init_workspace(user.id)
    audit_logger.log_admin_action("create_user", user.id, user_data)
    
    return {
        "id": user.id, 
        "username": user.username,
        "api_key": user.api_key  # 创建时返回 API Key
    }

@router.get("/users/{user_id}/api-key")
async def get_user_api_key(user_id: int):
    """查看用户 API Key"""
    user = db.get_user(user_id)
    return {
        "api_key": user.api_key,
        "api_key_enabled": user.api_key_enabled,
        "last_api_key_used_at": user.last_api_key_used_at
    }

@router.post("/users/{user_id}/api-key/regenerate")
async def regenerate_user_api_key(user_id: int):
    """重新生成用户 API Key"""
    new_key = user_manager.regenerate_api_key(user_id)
    return {
        "api_key": new_key,
        "message": "旧 API Key 已失效，请保存新 Key"
    }

@router.get("/system/status")
async def get_system_status():
    """系统状态"""
    return {
        "total_users": user_manager.count(),
        "active_sessions": session_manager.count_active(),
        "active_users_today": user_manager.count_active_today(),
        "shared_skills": skill_registry.count_shared(),
        "shared_plugins": plugin_registry.count_shared(),
        "db_size": db.get_size(),
        "storage_usage": get_storage_usage()
    }
```

---

## 6. 认证与安全

### 6.1 认证流程

```
登录流程:
用户输入账密 → Server验证密码 → 数据库查询用户 → 生成JWT Token → 返回Token+用户信息

后续请求:
请求带Token → Middleware验证JWT → 解析user_id → 检查用户状态 → 注入用户上下文
```

### 6.2 JWT Token 结构

```json
{
    "user_id": 123,
    "username": "zhangsan",
    "role": "user",
    "iat": 1712553600,
    "exp": 1712633600
}

// 使用方式
// HTTP Header: Authorization: Bearer <token>
// WebSocket: ws://server/chat?token=<token>
```

### 6.3 认证核心实现

```python
# src/openharness/enterprise/auth/auth.py

import jwt
from datetime import datetime, timedelta
from passlib.hash import bcrypt

class AuthService:
    def login(self, username: str, password: str) -> dict:
        """用户登录"""
        user = db.get_user_by_username(username)
        if not user or not bcrypt.verify(password, user.password_hash):
            raise AuthError("用户名或密码错误")
        
        if not user.is_active:
            raise AuthError("用户已禁用")
        
        token = self.generate_token(user)
        db.update_last_login(user.id)
        audit_logger.log(user.id, "login", {"success": True})
        
        return {
            "token": token,
            "user": {
                "id": user.id,
                "username": user.username,
                "display_name": user.display_name,
                "role": user.role,
                "api_key": user.api_key
            }
        }
    
    def generate_token(self, user, expire_hours=24) -> str:
        payload = {
            "user_id": user.id,
            "username": user.username,
            "role": user.role,
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(hours=expire_hours)
        }
        return jwt.encode(payload, JWT_SECRET, algorithm="HS256")
```

### 6.4 用户 API Key 获取 Token（嵌入场景）

```python
# src/openharness/enterprise/auth/internal_api.py

class InternalAuthService:
    """通过用户 API Key 获取 Token"""
    
    def get_token_by_api_key(self, api_key: str, expires_in: int = None) -> dict:
        user = db.get_user_by_api_key(api_key)
        
        if not user or not user.is_active or not user.api_key_enabled:
            raise AuthError("API Key 无效或用户已禁用")
        
        expire_hours = (expires_in or 3600) / 3600
        token = auth_service.generate_token(user, expire_hours=expire_hours)
        
        db.update_api_key_last_used(user.id)
        audit_logger.log(user_id=user.id, action="token_by_api_key")
        
        return {
            "token": token,
            "expires_at": datetime.utcnow() + timedelta(seconds=expires_in or 3600),
            "user": {
                "id": user.id,
                "username": user.username,
                "display_name": user.display_name
            }
        }

# API 端点
@router.post("/api/auth/token-by-api-key")
async def get_token_by_api_key(request: ApiKeyTokenRequest):
    return internal_auth_service.get_token_by_api_key(
        api_key=request.api_key,
        expires_in=request.expires_in
    )
```

### 6.5 用户自己管理 API Key

```python
@router.get("/api/user/me/api-key")
async def get_my_api_key(current_user: User = Depends(get_current_user)):
    """查看自己的 API Key"""
    return {
        "api_key": current_user.api_key,
        "api_key_enabled": current_user.api_key_enabled
    }

@router.post("/api/user/me/api-key/regenerate")
async def regenerate_my_api_key(current_user: User = Depends(get_current_user)):
    """重新生成自己的 API Key"""
    new_key = user_manager.regenerate_api_key(current_user.id)
    return {"api_key": new_key}
```

### 6.6 嵌入使用示例

```html
<script>
// 外部系统通过用户 API Key 获取 Token
const response = await fetch('https://openharness-server/api/auth/token-by-api-key', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        api_key: 'oh_user_xxx...',
        expires_in: 3600
    })
});

const { token } = await response.json();

// 嵌入聊天界面
document.getElementById('chat-iframe').src = 
    `https://openharness-server/chat?token=${token}`;
</script>
```

### 6.7 安全措施清单

1. 密码安全：bcrypt 哈希，迭代次数 12
2. Token 安全：JWT HS256，24小时过期
3. 会话安全：WebSocket 验证 Token，异常断开自动清理
4. 权限隔离：用户只能访问自己的工作区
5. 输入验证：参数化查询防 SQL 注入，限制文件访问范围防路径穿越
6. 审计日志：记录所有关键操作，保留 90 天
7. API Key 安全：可单独启用/禁用，可重新生成，有使用记录

---

## 7. Web 前端

### 7.1 页面结构

```
/
├── /login              # 登录页
├── /chat               # 聊天主页（普通用户）
│   ├── 会话列表侧边栏
│   ├── 聊天窗口
│   ├── 工具调用展示区
│   └── 用户设置入口
└── /admin              # 管理后台（管理员）
    ├── /admin/users    # 用户管理
    ├── /admin/shared   # 共享资源管理
    ├── /admin/audit    # 审计日志
    └── /admin/system   # 系统配置
```

### 7.2 技术栈

```
前端框架: React 18 + TypeScript
UI 组件库: Ant Design 或 TailwindCSS + shadcn/ui
WebSocket: 原生 WebSocket API
路由: React Router v6
状态管理: Zustand 或 React Context
构建工具: Vite
```

### 7.3 WebSocket 连接管理

```typescript
class ChatWebSocket {
  private ws: WebSocket;
  private sessionId: string;
  
  connect(token: string) {
    this.ws = new WebSocket(`ws://server/chat?token=${token}`);
    
    this.ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      switch (message.type) {
        case 'text': this.appendText(message.payload.content); break;
        case 'tool_call': this.showToolCall(message.payload); break;
        case 'thinking': this.showThinking(message.payload.content); break;
        case 'done': this.finishResponse(); break;
        case 'error': this.showError(message.payload.content); break;
      }
    };
  }
  
  sendMessage(content: string) {
    this.ws.send(JSON.stringify({
      type: 'message',
      payload: { content, session_id: this.sessionId }
    }));
  }
}
```

---

## 8. 启动与服务管理

### 8.1 服务入口

```python
# src/openharness/enterprise/server.py

app = FastAPI(title="OpenHarness Enterprise")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True)

app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(admin_router)
app.include_router(user_router)

@app.on_event("startup")
async def startup():
    init_database()
    ensure_admin_user()
    init_shared_pool()
    skill_registry.scan_shared_skills()

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
```

### 8.2 CLI 命令

```bash
oh-enterprise start                      # 启动服务
oh-enterprise start --port 8080          # 指定端口
oh-enterprise init                       # 初始化系统
oh-enterprise create-user zhangsan pwd   # 创建用户
oh-enterprise status                     # 查看状态
```

### 8.3 配置文件

```json
# ~/.oh-enterprise/config.json
{
    "server": { "port": 8000, "host": "0.0.0.0" },
    "auth": { "jwt_secret": "xxx", "jwt_expire_hours": 24 },
    "storage": { "data_dir": "~/.oh-enterprise", "database": "data.db" },
    "provider": { "default": "anthropic", "api_key": "xxx" },
    "cors": { "allow_origins": ["*"] },
    "audit": { "log_retention_days": 90 }
}
```

### 8.4 部署步骤

```bash
git clone https://github.com/your-org/openharness-enterprise.git
cd openharness-enterprise
uv sync --extra enterprise
oh-enterprise init
oh-enterprise create-user admin admin123 --role admin
oh-enterprise create-user zhangsan password123
oh-enterprise start

# 访问
# Web: http://localhost:8000/chat
# Admin: http://localhost:8000/admin
```

---

## 9. 实现优先级

### Phase 1: 核心功能（MVP）
- 数据库与用户表
- 认证服务（登录、JWT）
- WebChat Channel（WebSocket）
- Agent Engine 集成（用户上下文注入）
- 基础 Web 前端（登录页 + 聊天页）

### Phase 2: 管理功能
- Admin API（用户 CRUD、API Key 管理）
- 管理后台前端
- 审计日志

### Phase 3: 共享资源
- 共享 Skills/Plugins Pool
- 权限控制表
- 资源管理界面

### Phase 4: 增强功能
- 会话历史检索
- 用户偏好配置
- 嵌入模式优化
- 系统监控面板

---

## 10. 附录

### 10.1 关键技术选型

| 模块 | 技术 |
|-----|------|
| 后端框架 | FastAPI |
| 数据库 | SQLite（可扩展 PostgreSQL） |
| 认证 | JWT + bcrypt |
| WebSocket | FastAPI WebSocket |
| 前端 | React + TypeScript + Vite |
| CLI | Typer |

### 10.2 性能预估

- 单机支持：50-100 并发用户
- WebSocket 连接：1000+ 连接
- 响应延迟：<100ms（不含 LLM API）

### 10.3 后续扩展方向

- PostgreSQL 支持（更大规模）
- Redis Session 缓存
- Kubernetes 部署
- 多节点负载均衡
- 企业 AD/LDAP 集成
- SSO 单点登录