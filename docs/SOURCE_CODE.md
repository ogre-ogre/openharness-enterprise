# OpenHarness Enterprise 源码说明

## 后端源码

### server.py - 主服务入口

**位置**: `src/openharness/enterprise/server.py`

**功能**:
- FastAPI 应用初始化
- 路由注册
- 生命周期管理
- CLI 命令入口

**关键代码**:

```python
# FastAPI 应用
app = FastAPI(title="OpenHarness Enterprise", lifespan=lifespan)

# 路由注册
@app.post("/api/auth/login")           # 用户登录
@app.post("/api/auth/token-by-api-key") # API Key 获取 Token
@app.websocket("/ws/chat")             # WebSocket 聊天
@app.get("/api/sessions")              # 会话列表
@app.delete("/api/sessions/{id}")      # 删除会话
@app.get("/api/skills")                # Skills 列表
@app.get("/api/admin/users")           # 管理员：用户列表
@app.get("/api/admin/system/status")   # 管理员：系统状态
```

---

### storage/database.py - 数据库层

**位置**: `src/openharness/enterprise/storage/database.py`

**功能**:
- SQLite 数据库操作封装
- 用户、会话、消息、审计日志 CRUD

**数据模型**:

```python
class User(BaseModel):
    id: int
    username: str
    password_hash: str
    role: str              # 'user' | 'admin'
    api_key: str           # 用户 API Key
    api_key_enabled: bool

class Session(BaseModel):
    id: str                # UUID
    user_id: int
    title: str
    message_count: int

class Message(BaseModel):
    id: str
    session_id: str
    role: str              # 'user' | 'assistant'
    content: str

class AuditLog(BaseModel):
    user_id: int
    action: str
    details: dict
    ip_address: str
```

**关键方法**:

```python
# 用户操作
db.create_user(username, password_hash, role, api_key)
db.get_user(user_id)
db.get_user_by_username(username)
db.get_user_by_api_key(api_key)

# 会话操作
db.create_session(session_id, user_id)
db.get_user_sessions(user_id)  # 只返回有消息的会话

# 消息操作
db.create_message(message_id, session_id, role, content)
db.get_session_messages(session_id)

# 权限操作
db.user_can_access(user_id, resource_type, resource_name)
```

---

### storage/audit.py - 审计日志

**位置**: `src/openharness/enterprise/storage/audit.py`

**功能**:
- 记录用户操作
- 同时写入数据库和文件

**日志类型**:
- `login` - 登录
- `logout` - 登出
- `chat` - 聊天消息
- `token_by_api_key` - API Key 获取 Token
- `admin_*` - 管理员操作

---

### auth/auth.py - 认证服务

**位置**: `src/openharness/enterprise/auth/auth.py`

**功能**:
- 用户登录验证
- JWT Token 生成/验证
- 密码哈希
- API Key 管理

**关键类**:

```python
class AuthService:
    def login(username, password)     # 登录
    def generate_token(user)          # 生成 JWT
    def verify_token(token)           # 验证 JWT
    def hash_password(password)       # 密码哈希

class InternalAuthService:
    def get_token_by_api_key(api_key) # API Key 换 Token

class UserManager:
    def create_user(username, password, role)
    def generate_api_key()            # 生成用户 API Key
    def regenerate_api_key(user_id)
```

---

### auth/middleware.py - 认证中间件

**位置**: `src/openharness/enterprise/auth/middleware.py`

**功能**:
- FastAPI 中间件
- Token 验证
- 权限检查

**依赖注入**:

```python
# 获取当前用户
async def get_current_user(token) -> User

# 需要管理员权限
async def require_admin(user) -> User
```

---

### users/workspace.py - 工作区管理

**位置**: `src/openharness/enterprise/users/workspace.py`

**功能**:
- 创建用户工作区
- 初始化默认文件 (soul.md, MEMORY.md)

**工作区结构**:

```
~/.oh-enterprise/users/{user_id}/
├── memory/
│   └── MEMORY.md
├── sessions/
├── config/
│   └── preferences.json
└── soul.md
```

---

### users/context.py - 用户上下文

**位置**: `src/openharness/enterprise/users/context.py`

**功能**:
- 加载用户上下文
- 扫描可用 skills

**上下文模型**:

```python
class UserContext(BaseModel):
    user_id: int
    username: str
    soul: str                    # soul.md 内容
    memory_path: str
    available_skills: List[str]  # 可用 skills 列表
    preferences: dict
```

---

### channels/webchat.py - WebSocket 聊天

**位置**: `src/openharness/enterprise/channels/webchat.py`

**功能**:
- WebSocket 连接管理
- 消息收发
- 流式响应

**消息协议**:

```python
# 客户端 → 服务端
{
    "type": "message",
    "payload": {"content": "用户消息"}
}

# 服务端 → 客户端
{
    "type": "text",
    "payload": {"content": "AI响应", "delta": true}
}
{
    "type": "done",
    "payload": {"message_count": 10}
}
```

**关键类**:

```python
class WebChatChannel:
    async def handle_connection(websocket, user, session_id)
    async def _handle_chat_message(...)
    async def _send_session_history(...)

class SessionManager:
    def create_session(user_id)
    def get_or_create_session(user_id, session_id)

class MessageStore:
    def save_message(session_id, role, content)
    def get_conversation_history(session_id)
```

---

### llm/client.py - LLM 客户端

**位置**: `src/openharness/enterprise/llm/client.py`

**功能**:
- 调用 LLM API
- 流式响应
- Skills 注入

**关键方法**:

```python
class LLMClient:
    async def stream_chat(messages, system_prompt, skills)
    
    def build_system_prompt(base_prompt, skills)
        # 将 skills 内容注入到 system prompt
    
    def load_skill_content(skill_name, path)
        # 加载 skill 文件内容
```

---

### config/provider.py - Provider 配置

**位置**: `src/openharness/enterprise/config/provider.py`

**功能**:
- LLM Provider 配置
- 环境变量读取

**配置项**:

```python
class ProviderConfig(BaseModel):
    provider: str       # 'anthropic'
    api_key: str        # API Key
    base_url: str       # API 地址
    model: str          # 模型名称
    max_tokens: int     # 最大 Token
    temperature: float  # 温度
```

---

## 前端源码

### App.tsx - 应用入口

**位置**: `web/src/App.tsx`

**功能**:
- 路由配置
- 权限守卫

**路由**:
- `/login` - 登录页
- `/chat` - 聊天页
- `/admin/*` - 管理后台

---

### pages/Chat.tsx - 聊天页面

**位置**: `web/src/pages/Chat.tsx`

**功能**:
- WebSocket 连接管理
- 消息收发
- 会话管理

**状态管理**:

```typescript
const [sessionMessages, setSessionMessages] = useState<SessionMessages>({})
const [sessions, setSessions] = useState<SessionInfo[]>([])
const [currentSessionId, setCurrentSessionId] = useState<string | null>(null)
const [isThinking, setIsThinking] = useState(false)
const [currentResponse, setCurrentResponse] = useState('')
```

---

### services/api.ts - API 服务

**位置**: `web/src/services/api.ts`

**功能**:
- HTTP 请求封装
- Token 注入

**API 模块**:

```typescript
// 认证
authApi.login(username, password)
authApi.getMe()
authApi.getMyApiKey()

// 会话
sessionsApi.list()
sessionsApi.getMessages(sessionId)
sessionsApi.delete(sessionId)

// Skills
skillsApi.list()
skillsApi.reload()

// 管理员
adminApi.listUsers()
adminApi.createUser()
adminApi.getStatus()
```

---

### services/websocket.ts - WebSocket 服务

**位置**: `web/src/services/websocket.ts`

**功能**:
- WebSocket 连接
- 消息处理
- 自动重连

**消息类型**:

```typescript
interface ServerMessage {
    type: 'text' | 'thinking' | 'done' | 'error' | 'session_info' | 'session_history'
    payload: Record<string, any>
    session_id?: string
}
```

---

### pages/admin/*.tsx - 管理后台

**位置**: `web/src/pages/admin/`

**页面**:
- `AdminLayout.tsx` - 布局
- `Users.tsx` - 用户管理
- `Status.tsx` - 系统状态
- `AuditLogs.tsx` - 审计日志

---

## 测试

**位置**: `tests/`

**测试文件**:
- `test_storage.py` - 数据库操作测试

**运行测试**:

```bash
uv run pytest tests/ -v
```