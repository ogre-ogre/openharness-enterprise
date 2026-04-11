# PROJECT KNOWLEDGE BASE

**Generated:** 2026-04-11
**Type:** Python (FastAPI) + TypeScript (React) Monorepo

## OVERVIEW

OpenHarness Enterprise - 基于 OpenHarness 的企业级多用户 AI 编程助手，支持多用户、JWT 认证、WebSocket 实时聊天、企业级 Skills 共享。

## STRUCTURE

```
openharness-enterprise/
├── src/openharness/enterprise/   # Python 后端 (FastAPI)
│   ├── auth/                     # 认证 (JWT, API Key, Middleware)
│   ├── users/                    # 用户、工作区、Memory
│   ├── channels/                 # WebSocket 聊天
│   ├── storage/                  # SQLite + 审计日志
│   ├── llm/                      # LLM 客户端
│   ├── agents/                   # Agent 协调器
│   ├── tools/                    # Tools 注册
│   ├── config/                   # 配置
│   └── a2a/                      # A2A 协议
├── web/                          # React 前端 (TypeScript)
│   └── src/
│       ├── pages/                # 页面 (Chat, Login, Admin)
│       ├── services/             # API, WebSocket
│       └── stores/               # Zustand 状态
├── docs/                         # 文档 (ARCHITECTURE, SOURCE_CODE...)
├── tests/                        # pytest
└── pyproject.toml                # Python 项目配置
```

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| 认证逻辑 | `src/openharness/enterprise/auth/` | JWT + API Key |
| 用户/工作区 | `src/openharness/enterprise/users/` | Memory 隔离 |
| WebSocket 聊天 | `src/openharness/enterprise/channels/webchat.py` | 实时消息 |
| 前端页面 | `web/src/pages/` | Chat, Login, Admin |
| 前端 API | `web/src/services/` | api.ts, websocket.ts |
| 架构文档 | `docs/ARCHITECTURE.md` | 完整架构 |
| 源码说明 | `docs/SOURCE_CODE.md` | 模块详解 |

## CONVENTIONS

- **Python**: `ruff` (line-length 100, py311), `mypy` strict
- **TypeScript**: Vite + React 18 + Ant Design + Zustand
- **包管理**: Python `uv`, Node `npm`
- **入口命令**: `oh-enterprise` (pyproject.toml scripts)

## COMMANDS

```bash
# 后端启动
uv run oh-enterprise init
uv run oh-enterprise start --port 8000

# 前端启动
cd web && npm run dev

# 测试
uv run pytest tests/ -v

# 代码检查
uv run ruff check src/
```

## NOTES

- 默认管理员: admin / admin123
- 双语言项目: Python 后端 + TypeScript 前端
- 工作区隔离: 每用户独立 memory 文件
- 企业级: JWT 认证、审计日志、API Key