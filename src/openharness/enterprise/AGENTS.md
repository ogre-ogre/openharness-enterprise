# src/openharness/enterprise

**Python 后端 (FastAPI)**

## OVERVIEW

Enterprise backend module with authentication, users, storage, LLM client, agents, tools, and A2A protocol support.

## STRUCTURE

```
enterprise/
├── auth/           # JWT + API Key 认证
├── users/          # 用户、工作区、Memory 隔离
├── channels/       # WebSocket 实时聊天
├── storage/        # SQLite + 审计日志
├── llm/            # LLM 客户端封装
├── agents/         # Agent 协调器
├── tools/          # Tools 注册表
├── config/         # 配置管理
├── a2a/            # A2A 协议路由
└── server.py       # FastAPI 入口
```

## WHERE TO LOOK

| Task | File | Notes |
|------|------|-------|
| 登录认证 | `auth/auth.py` | JWT token 生成验证 |
| 密码哈希 | `auth/auth.py` | passlib bcrypt |
| 用户 CRUD | `users/workspace.py` | 工作区管理 |
| Memory 隔离 | `users/memory.py` | 每用户独立文件 |
| WebSocket | `channels/webchat.py` | 实时消息推送 |
| 数据库 | `storage/database.py` | SQLite aiosqlite |
| 审计日志 | `storage/audit.py` | 操作记录 |
| LLM 调用 | `llm/client.py` | Anthropic/OpenAI |

## CONVENTIONS

- 所有 async 函数使用 `aiosqlite`
- 密码存储使用 bcrypt
- JWT 过期时间配置在 `config/provider.py`
- API Key 格式: `oh_user_xxx`

## ANTI-PATTERNS

- 禁止使用 `as any` 类型断言
- 禁止空 catch 块 `catch(e) {}`
- 禁止 `@ts-ignore` 伪装饰器