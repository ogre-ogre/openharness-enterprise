# OpenHarness Enterprise - 项目总结文档

## 项目概述

OpenHarness Enterprise 是一个多用户 AI 助手平台，基于 OpenHarness 开源项目二次开发。

**核心特性**：
- 多用户支持（用户隔离）
- 记忆系统（长期记忆 + 每日记忆）
- 智能记忆注入
- 会话恢复
- 自学习机制
- Meditate 每日反思

---

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端框架 | FastAPI + Uvicorn |
| 数据库 | SQLite (aiosqlite) |
| LLM | OpenAI-compatible API |
| 认证 | JWT (python-jose) |
| 前端 | Vue 3 + Vite |

---

## 核心架构

### 目录结构

```
openharness-enterprise/
├── src/openharness/enterprise/
│   ├── channels/          # WebSocket 通信
│   │   └── webchat.py     # 核心：对话处理 + 记忆注入
│   ├── config/            # 配置管理
│   │   ├── settings.py    # 统一配置（环境变量 + .env + 默认值）
│   │   └── provider.py    # LLM 提供商配置
│   ├── storage/           # 数据存储
│   │   └ database.py      # SQLite 数据库 + Session/Message 模型
│   ├── users/             # 用户模块
│   │   ├── context.py     # UserContext（soul + identity + memory）
│   │   ├── memory.py      # 记忆管理（MEMORY.md + 每日记忆）
│   │   ├── workspace.py   # 用户工作区（模板文件创建）
│   │   ├── trigger.py     # 记忆触发检测（关键词）
│   │   ├── restorer.py    # 会话恢复器
│   │   ├── learning.py    # 自学习引擎
│   │   └ meditate.py      # 每日反思机制
│   ├── tools/             # 工具定义
│   │   └ registry.py      # 工具注册（read_file, write_file, execute_command）
│   ├── llm/               # LLM 客户端
│   │   └ client.py        # OpenAI-compatible API 调用
│   ├── auth/              # 认证模块
│   │   └ service.py       # JWT 生成/验证
│   └── server.py          # FastAPI 应用 + API 端点
├── web/                   # Vue 前端
├── .env                   # 环境配置
└── docs/                  # 文档
```

---

## 数据库结构

### users 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 用户 ID |
| username | TEXT | 用户名 |
| display_name | TEXT | 显示名 |
| role | TEXT | 角色（user/admin） |
| is_active | BOOLEAN | 是否活跃 |
| created_at | TIMESTAMP | 创建时间 |

### sessions 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | TEXT | 会话 UUID |
| user_id | INTEGER | 用户 ID |
| title | TEXT | 会话标题 |
| message_count | INTEGER | 消息数 |
| is_active | BOOLEAN | 是否活跃 |
| system_prompt | TEXT | 系统提示词（新增） |
| model | TEXT | 使用的模型（新增） |
| session_key | TEXT | 会话主题（新增） |

### messages 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | TEXT | 消息 UUID |
| session_id | TEXT | 会话 ID |
| role | TEXT | 角色（user/assistant） |
| content | TEXT | 内容 |
| created_at | TIMESTAMP | 创建时间 |

---

## 用户工作区结构

```
~/.oh-enterprise/users/{user_id}/
├── memory/
│   ├── MEMORY.md         # 长期记忆
│   ├── 2026-04-11.md      # 每日记忆
│   └── knowledge/         # 外置知识文件
├── soul.md                # AI 人设
├── identity.md            # AI 身份（首次对话自动填充）
├── user.md                # 用户画像（首次对话自动填充）
├── BOOTSTRAP.md           # 首次启动引导（完成后删除）
├── config/
│   └ preferences.json     # 用户偏好
└── skills/                # 用户技能
```

---

## 记忆系统

### 记忆类型

| 类型 | 文件 | 记录内容 | 触发条件 |
|------|------|----------|----------|
| **每日记忆** | `YYYY-MM-DD.md` | 用户消息前50字符 | 每次对话完成 |
| **长期记忆** | `MEMORY.md` | 重要决策、教训、知识点 | LLM判断"重要" |
| **用户画像** | `user.md` | 用户偏好、习惯 | 首次对话学习 |
| **AI身份** | `identity.md` | AI名称、风格 | 首次对话学习 |

### 记忆注入策略

**当前策略：直接注入**

每次对话时，将记忆内容直接注入到 system_prompt：

```python
if user_context.memory and user_context.memory.strip():
    parts.append(f"\n\n## 历史记忆\n\n{user_context.memory}")
```

### 记忆更新流程

```
对话完成 → _update_memory_smart()
    → append_to_daily(user_message[:50])  # 每日记忆（必须）
    → LLM 分析是否重要
    → 如果重要 → append_to_memory("重要记录", summary)
    → 如果发现偏好 → append_to_memory("用户偏好", preference)
```

---

## Meditate 每日反思

### 功能

1. 收集昨日对话
2. AI 分析提取（操作、知识点、备忘）
3. 长内容外置到知识文件
4. 重组织 MEMORY.md

### 触发方式

| 方式 | 说明 |
|------|------|
| API | `POST /api/meditate` |
| 定时任务 | APScheduler（需安装） |
| 系统 cron | `0 3 * * * curl -X POST ...` |

---

## API 端点

### 认证

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/auth/login` | 登录获取 JWT |
| POST | `/api/auth/register` | 注册用户 |

### 会话

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/sessions` | 获取用户会话列表 |
| POST | `/api/sessions/{id}/restore` | 恢复会话完整上下文 |
| GET | `/api/sessions/resumable` | 获取可恢复会话 |
| DELETE | `/api/sessions/{id}` | 删除会话 |

### 上下文

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/context` | 获取用户完整上下文 |

### 记忆

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/meditate` | 触发记忆反思 |
| POST | `/api/learning/extract` | 手动触发用户信息提取 |

### WebSocket

| 路径 | 说明 |
|------|------|
| `/ws/chat?token={jwt}` | WebSocket 对话 |

---

## 配置管理

### 配置优先级

```
环境变量 > .env 文件 > 代码默认值
```

### 配置项列表

| 配置项 | 环境变量 | 默认值 |
|------|----------|--------|
| 企业根目录 | `OH_ENTERPRISE_ROOT` | `~/.oh-enterprise` |
| 服务器端口 | `OH_PORT` | 8000 |
| JWT 过期时间 | `OH_JWT_EXPIRE_HOURS` | 24 |
| LLM 提供商 | `OH_PROVIDER` | anthropic |
| API Key | `OH_API_KEY` | - |
| 模型 | `OH_MODEL` | claude-3-5-sonnet-20241022 |
| 知识外置阈值 | `OH_KNOWLEDGE_THRESHOLD` | 2000 |
| 工具调用最大次数 | `OH_MAX_ITERATIONS` | 5 |
| 命令执行超时 | `OH_TOOL_TIMEOUT` | 30 |
| 每日记忆保留天数 | `OH_DAILY_MEMORY_LIMIT` | 7 |
| Meditate 执行时间 | `OH_MEDITATE_HOUR` | 3 |

### .env 文件示例

```bash
OH_PROVIDER=openai-compatible
OH_API_KEY=sk-xxx
OH_BASE_URL=https://coding.dashscope.aliyuncs.com/v1
OH_MODEL=glm-5
OH_PORT=8000
OH_JWT_EXPIRE_HOURS=24
OH_KNOWLEDGE_THRESHOLD=2000
OH_MAX_ITERATIONS=5
OH_TOOL_TIMEOUT=30
OH_MEDITATE_HOUR=3
OH_MEDITATE_MINUTE=0
```

---

## 关键修复记录

### 1. JSON 花括号 `.format()` 问题

**问题**：`summary_prompt` 中有 JSON 示例 `{...}`，Python `.format()` 会解析为占位符。

**修复**：将 `{` 改为 `{{`，`}` 改为 `}}`。

### 2. SQLite 布尔查询不匹配

**问题**：数据库 `is_active` 存储为 `'TRUE'` 或 `1`，查询条件不匹配。

**修复**：改为 `is_active IN (1, 'TRUE')`。

### 3. 用户隔离问题

**问题**：`tool_instructions` 中硬编码 `users/1/`，LLM 会写入错误目录。

**修复**：动态传入 `user_id`，所有示例使用 `{user_id}`。

### 4. asyncio.run() 在 event loop 中失败

**问题**：`MeditateExecutor` 在 FastAPI event loop 中调用 `asyncio.run()`。

**修复**：改为 async 方法 `execute_async()`。

### 5. 硬编码配置项

**问题**：`KNOWLEDGE_THRESHOLD = 2000`、`max_iterations = 5` 等硬编码。

**修复**：改为从 `get_settings()` 获取配置。

---

## 部署指南

### 本地开发

```bash
# 1. 克隆仓库
git clone https://github.com/ogre-ogre/openharness-enterprise

# 2. 安装依赖
cd openharness-enterprise
pip install -r requirements.txt

# 3. 配置 .env
cp .env.example .env
# 编辑 .env，配置 OH_API_KEY 等

# 4. 启动后端
python -m uvicorn openharness.enterprise.server:app --host localhost --port 8001

# 5. 启动前端
cd web
npm install
npm run dev
```

### 远程部署

```bash
# 1. 安装依赖
pip install apscheduler

# 2. 启动服务
nohup uvicorn openharness.enterprise.server:app --host 0.0.0.0 --port 8000 > logs/server.log 2>&1 &

# 3. 配置 cron（可选）
0 3 * * * curl -X POST http://localhost:8000/api/meditate/all -H "Authorization: Bearer {admin_token}"
```

---

## 使用指南

### 登录

访问 `http://localhost:3009`，输入用户名密码登录。

### 对话

WebSocket 连接后，发送消息即可对话。记忆会自动注入。

### 触发 Meditate

```bash
curl -X POST http://localhost:8000/api/meditate \
  -H "Authorization: Bearer {token}"
```

### 查看记忆

```bash
# 查看用户上下文
curl http://localhost:8000/api/context \
  -H "Authorization: Bearer {token}"
```

---

## GitHub 仓库

- **地址**：https://github.com/ogre-ogre/openharness-enterprise
- **敏感文件排除**：`.env`（API key 等配置）
- **开发脚本排除**：`test_*.py`, `check_*.py` 等

---

*文档版本: v1.0 | 最后更新: 2026-04-11*