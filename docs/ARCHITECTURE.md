# OpenHarness Enterprise 工程架构

## 系统架构

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
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐         │ │
│  │  │ LLM Client │ │ Memory     │ │ Skills     │         │ │
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
│  │  │    ├── sessions/       # 会话历史                │ │ │
│  │  │    ├── config/         # 用户偏好配置            │ │ │
│  │  │    └── skills/         # 用户私有 skills         │ │ │
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
│  │  └──────────────────┘  └────────────────────────────┘ │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                            │
                    ┌───────┴───────┐
                    │   Web Frontend │
                    │   (React SPA)  │
                    └────────────────┘
```

## 技术栈

### 后端
- **语言**: Python 3.10+
- **Web框架**: FastAPI
- **数据库**: SQLite (可扩展 PostgreSQL)
- **认证**: JWT + bcrypt
- **LLM SDK**: anthropic (支持兼容 API)
- **异步**: asyncio, uvicorn

### 前端
- **语言**: TypeScript
- **框架**: React 18
- **UI库**: Ant Design
- **状态管理**: Zustand
- **构建工具**: Vite

### 实时通信
- **协议**: WebSocket
- **消息格式**: JSON

## 模块划分

```
src/openharness/enterprise/
├── __init__.py
├── server.py           # FastAPI 主服务入口
│
├── storage/            # 存储层
│   ├── database.py     # SQLite 数据库操作
│   └── audit.py        # 审计日志
│
├── auth/               # 认证模块
│   ├── auth.py         # JWT 认证、用户管理
│   └── middleware.py   # FastAPI 中间件
│
├── users/              # 用户模块
│   ├── workspace.py    # 工作区管理
│   └── context.py      # 用户上下文
│
├── channels/           # 通信通道
│   └── webchat.py      # WebSocket 聊天
│
├── llm/                # LLM 客户端
│   └── client.py       # Anthropic API 客户端
│
├── config/             # 配置模块
│   └── provider.py     # LLM Provider 配置
│
└── admin/              # 管理接口 (待完善)
```

## 数据流

### 用户登录流程
```
用户输入账密 → AuthService.login()
    → 验证密码 (bcrypt)
    → 生成 JWT Token
    → 返回 Token + 用户信息
```

### 聊天流程
```
用户发送消息 → WebSocket
    → WebChatChannel.handle_message()
    → 加载用户上下文 (skills, memory)
    → LLMClient.stream_chat()
    → 流式返回响应
    → 保存消息到数据库
```

### Skills 加载流程
```
WebSocket 连接 → load_user_context()
    → 扫描用户私有 skills
    → 扫描共享 skills
    → 检查访问权限
    → 注入到 System Prompt
    → 发送给 LLM
```

## 目录结构

```
openharness-enterprise/
├── src/openharness/enterprise/    # 后端源码
├── web/                           # 前端源码
│   ├── src/
│   │   ├── pages/                 # 页面组件
│   │   ├── services/              # API 服务
│   │   └── stores/                # 状态管理
│   └── package.json
├── docs/                          # 文档
├── tests/                         # 测试
├── scripts/                       # 脚本
├── pyproject.toml                 # Python 配置
└── README.md
```

## 运行时目录

```
~/.oh-enterprise/                  # 运行时数据目录
├── data.db                        # SQLite 数据库
├── config.json                    # 全局配置 (可选)
├── users/                         # 用户工作区
│   ├── {user_id}/
│   │   ├── memory/
│   │   │   ├── MEMORY.md
│   │   │   └── YYYY-MM-DD.md
│   │   ├── sessions/
│   │   ├── config/
│   │   │   ├── preferences.json
│   │   │   └── provider.json
│   │   └── soul.md
├── shared/                        # 共享资源
│   ├── skills/
│   ├── plugins/
│   └── templates/
└── logs/                          # 日志
    └── audit-YYYY-MM-DD.log
```