# OpenHarness Enterprise

基于 OpenHarness 开源项目的企业级多用户 AI 智能体平台。

## ✨ 特性

### 核心功能

- 🏢 **多用户支持** - 用户注册、登录、独立工作区
- 🔐 **企业级安全** - JWT 认证、API Key、审计日志
- 🌐 **Web 界面** - React 前端，支持 WebSocket 实时通信
- 📁 **工作区隔离** - 每用户独立记忆文件、配置
- 🔄 **共享资源** - 企业级 Skills 共享池
- 🎯 **嵌入支持** - API Key 方式无缝嵌入其他系统

### 🧠 智能记忆机制（核心创新）

- **🧘 冥想 Meditate** - 每日自动记忆反思与知识整合
  - 每日凌晨 3:00 自动分析昨日对话
  - AI 智能提取操作记录、知识点、重要备忘
  - 长内容自动外置到独立知识文件，保持记忆简洁
  - 自动合并重复、删除过时、重组织记忆库
  
- **💾 分层记忆系统** - 双层记忆架构模拟人类记忆
  - `MEMORY.md` - 长期精选记忆，经 Meditate 整理后持久保存
  - `YYYY-MM-DD.md` - 每日事件流水，原始记录定期归档
  - 智能上下文构建：每次对话自动注入长期记忆 + 最近 3 天每日记忆
  - 知识外置引用：超长内容存储在 `knowledge/` 目录，MEMORY.md 保持引用链接
  
- **🎯 自学习引擎** - 从对话中自动学习用户偏好
  - 自动识别用户姓名、时区、项目、回答偏好
  - 自动填充 `user.md`（用户画像）和 `identity.md`（AI 身份）
  - 首次对话后自动完成 Bootstrap 引导
  - 持续更新用户画像，让 AI 更了解用户
  
- **🔄 会话恢复机制** - 完整会话上下文恢复
  - 从数据库恢复对话历史 + System Prompt
  - 恢复前验证会话归属（安全隔离）
  - System Prompt 构建顺序：Soul → Identity → User Profile → Memory

## 本地开发环境启动指南

### 环境要求

| 依赖 | 版本 | 说明 |
|------|------|------|
| Python | 3.10+ | 后端运行环境 |
| uv | 最新 | Python 包管理器（推荐） |
| Node.js | 18+ | 前端开发环境 |

#### 安装 uv（如果未安装）

```bash
# Windows PowerShell
irm https://astral.sh/uv/install.ps1 | iex

# Linux/macOS
curl -LsSf https://astral.sh/uv/install.sh | sh
```

---

### 第一步：克隆项目

```bash
git clone <repository-url>
cd openharness-enterprise
```

---

### 第二步：配置环境变量

创建 `.env` 文件（或复制 `.env.example`）：

```bash
# 复制模板
cp .env.example .env
```

编辑 `.env` 文件，配置 LLM 服务：

```bash
# 必须配置 - LLM 提供商和 API Key
OH_PROVIDER=bailian           # 可选: anthropic, openai, openai-compatible, bailian, zhipu, deepseek
OH_API_KEY=your-api-key-here  # 你的 API Key

# 可选配置
OH_MODEL=glm-5                # 模型名称
OH_BASE_URL=https://xxx       # 自定义 API 地址（部分提供商需要）
```

**常用 LLM 配置示例：**

```bash
# 百炼（阿里云）
OH_PROVIDER=bailian
OH_API_KEY=sk-xxx
OH_MODEL=glm-5

# 智谱 AI
OH_PROVIDER=zhipu
OH_API_KEY=xxx.xxx
OH_MODEL=glm-4

# DeepSeek
OH_PROVIDER=deepseek
OH_API_KEY=sk-xxx
OH_MODEL=deepseek-chat

# OpenAI 兼容接口
OH_PROVIDER=openai-compatible
OH_API_KEY=sk-xxx
OH_BASE_URL=https://your-api-endpoint
OH_MODEL=gpt-4
```

---

### 第三步：启动后端服务

#### 方式一：使用启动脚本（Windows）

```bash
# 双击运行，或在命令行执行
scripts\start-server.bat
```

#### 方式二：手动启动（推荐开发使用）

```bash
cd D:\openharness-enterprise

# 1. 安装依赖
uv sync --extra dev

# 2. 首次运行初始化（创建数据库、管理员账号等）
uv run oh-enterprise init

# 3. 启动服务
uv run oh-enterprise start --port 8000
```

**后端启动成功后：**
- API 服务: http://localhost:8000
- API 文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000/health

---

### 第四步：启动前端服务（可选）

如果需要 Web 界面，启动前端开发服务器：

#### 方式一：使用启动脚本（Windows）

```bash
# 双击运行，或在命令行执行
scripts\start-frontend.bat
```

#### 方式二：手动启动

```bash
cd D:\openharness-enterprise\web

# 1. 安装依赖
npm install

# 2. 启动开发服务器
npm run dev
```

**前端启动成功后：**
- Web 界面: http://localhost:3000

---

### 默认账号

首次 `init` 后自动创建管理员账号：

| 字段 | 值 |
|------|-----|
| 用户名 | `admin` |
| 密码 | `admin123` |
| API Key | 初始化时自动生成，显示在终端输出 |

> ⚠️ 生产环境请立即修改默认密码！

---

### 验证安装

```bash
# 检查后端健康状态
curl http://localhost:8000/health

# 预期返回
{"status": "healthy", "version": "x.x.x"}
```

---

### 常见问题

#### 1. 端口被占用

```bash
# 查看端口占用（Windows）
netstat -ano | findstr :8000

# 使用其他端口
uv run oh-enterprise start --port 8080
```

#### 2. 依赖安装失败

```bash
# 清理缓存重新安装
uv cache clean
uv sync --extra dev --reinstall
```

#### 3. 数据库初始化失败

```bash
# 删除旧数据重新初始化
rm -rf ~/.oh-enterprise
uv run oh-enterprise init
```

#### 4. 前端连接后端失败

检查 `web/.env` 或 `web/.env.local` 中的 API 地址配置：

```bash
# web/.env.local
VITE_API_URL=http://localhost:8000
```

---

### 开发模式热重载

后端使用 `--reload` 参数启用热重载：

```bash
uv run uvicorn openharness.enterprise.server:app --reload --port 8000
```

前端默认启用热重载，修改代码自动刷新。

## 目录结构

```
openharness-enterprise/
├── src/openharness/
│   ├── enterprise/           # 企业版模块
│   │   ├── users/            # 用户管理、工作区
│   │   │   ├── context.py    # 用户上下文加载器
│   │   │   ├── memory.py     # 分层记忆管理器
│   │   │   ├── meditate.py   # 冥想反思机制
│   │   │   ├── learning.py   # 自学习引擎
│   │   │   ├── restorer.py   # 会话恢复器
│   │   │   └── workspace.py  # 工作区管理
│   │   ├── auth/             # 认证服务 (JWT, API Key)
│   │   ├── channels/         # WebChat WebSocket
│   │   ├── storage/          # SQLite 数据库
│   │   ├── config/           # 配置管理
│   │   ├── llm/              # LLM 客户端
│   │   └── server.py         # FastAPI 服务入口
│   └── ...
├── web/                      # React 前端
│   ├── src/
│   │   ├── pages/            # 页面组件
│   │   ├── services/         # API, WebSocket
│   │   └── stores/           # 状态管理
│   └── ...
├── docs/                     # 文档
├── tests/                    # 测试
└── scripts/                  # 启动脚本
```

## API 端点

### 认证
- `POST /api/auth/login` - 登录
- `POST /api/auth/token-by-api-key` - API Key 获取 Token
- `GET /api/auth/me` - 当前用户信息

### 聊天
- `WebSocket /ws/chat` - 聊天 WebSocket
- `GET /api/sessions` - 会话列表
- `GET /api/sessions/{id}/messages` - 会话消息
- `DELETE /api/sessions/{id}` - 删除会话
- `POST /api/sessions/{id}/restore` - 恢复会话上下文
- `GET /api/sessions/resumable` - 可恢复的会话列表

### 智能记忆
- `GET /api/context` - 获取用户完整上下文（含记忆）
- `POST /api/meditate` - 手动触发记忆反思（Meditate）
- `POST /api/meditate/all` - 管理员触发所有用户 Meditate
- `POST /api/learning/extract` - 手动触发用户信息提取

### Skills
- `GET /api/skills` - Skills 列表
- `GET /api/skills/{name}` - Skill 内容
- `POST /api/skills/reload` - 刷新 Skills
- `POST /api/skills/upload` - 上传 Skill（ZIP 格式）
- `DELETE /api/skills/{name}` - 删除 Skill

### 管理员
- `GET/POST /api/admin/users` - 用户列表/创建
- `GET/PUT/DELETE /api/admin/users/{id}` - 用户详情/更新/禁用
- `GET/POST /api/admin/users/{id}/api-key` - API Key 查看/重新生成
- `GET /api/admin/system/status` - 系统状态
- `GET /api/admin/audit-logs` - 审计日志

## 嵌入其他系统

使用 API Key 方式获取 Token，无需用户登录：

```javascript
// 获取 Token
const response = await fetch('/api/auth/token-by-api-key', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    api_key: 'oh_user_xxx...',
    expires_in: 3600
  })
});

const { token } = await response.json();

// 连接 WebSocket
const ws = new WebSocket(`ws://host/ws/chat?token=${token}`);
```

## 📚 文档

完整文档请查看 [docs/](docs/README.md) 目录：

| 文档 | 说明 |
|------|------|
| [工程架构](docs/ARCHITECTURE.md) | 系统架构、模块划分 |
| [源码说明](docs/SOURCE_CODE.md) | 各模块代码说明 |
| [配置文件](docs/CONFIGURATION.md) | 配置项详细说明 |
| [配置方法](docs/SETUP_GUIDE.md) | 环境变量、LLM 配置 |
| [部署指南](docs/DEPLOYMENT.md) | Linux 部署、Nginx 配置 |
| [LLM 配置](docs/LLM_CONFIG.md) | 支持的 LLM 服务列表 |

## 开发

```bash
# 运行测试
uv run pytest tests/ -v

# 代码检查
uv run ruff check src/
```

## License

MIT