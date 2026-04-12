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

## 快速开始

### 环境要求

- Python 3.10+
- Node.js 18+ (前端开发)
- uv (Python 包管理器)

### 启动后端

```bash
# 方式一：使用脚本
scripts\start-server.bat

# 方式二：手动启动
cd D:\openharness-enterprise
uv sync --extra dev
uv run oh-enterprise init     # 首次运行初始化
uv run oh-enterprise start --port 8000
```

### 启动前端

```bash
# 方式一：使用脚本
scripts\start-frontend.bat

# 方式二：手动启动
cd D:\openharness-enterprise\web
npm install
npm run dev
```

### 配置 LLM

```bash
# Windows PowerShell
$env:ANTHROPIC_AUTH_TOKEN = "your-api-key"
$env:ANTHROPIC_BASE_URL = "https://coding.dashscope.aliyuncs.com/apps/anthropic"
$env:ANTHROPIC_MODEL = "glm-5"

# Linux/macOS
export ANTHROPIC_AUTH_TOKEN="your-api-key"
export ANTHROPIC_BASE_URL="https://coding.dashscope.aliyuncs.com/apps/anthropic"
export ANTHROPIC_MODEL="glm-5"
```

### 访问

- **前端**: http://localhost:3000
- **API 文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health

### 默认管理员

- 用户名: `admin`
- 密码: `admin123`
- API Key: 初始化时生成并显示

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