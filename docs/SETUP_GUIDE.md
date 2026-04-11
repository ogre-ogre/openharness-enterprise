# OpenHarness Enterprise 配置方法

## 目录

1. [LLM Provider 配置](#llm-provider-配置)
2. [用户认证配置](#用户认证配置)
3. [数据库配置](#数据库配置)
4. [前端配置](#前端配置)
5. [Skills 配置](#skills-配置)

---

## LLM Provider 配置

### 环境变量方式（推荐）

**Windows PowerShell**:

```powershell
# 阿里百炼 GLM-5
$env:ANTHROPIC_AUTH_TOKEN = "sk-sp-xxxxx"
$env:ANTHROPIC_BASE_URL = "https://coding.dashscope.aliyuncs.com/apps/anthropic"
$env:ANTHROPIC_MODEL = "glm-5"
```

**Linux/macOS**:

```bash
# 阿里百炼 GLM-5
export ANTHROPIC_AUTH_TOKEN="sk-sp-xxxxx"
export ANTHROPIC_BASE_URL="https://coding.dashscope.aliyuncs.com/apps/anthropic"
export ANTHROPIC_MODEL="glm-5"
```

### 支持的 LLM 服务配置

#### 阿里百炼（推荐）

```bash
ANTHROPIC_AUTH_TOKEN="sk-sp-xxxxx"
ANTHROPIC_BASE_URL="https://coding.dashscope.aliyuncs.com/apps/anthropic"
ANTHROPIC_MODEL="glm-5"
```

#### DeepSeek

```bash
ANTHROPIC_AUTH_TOKEN="sk-xxxxx"
ANTHROPIC_BASE_URL="https://api.deepseek.com"
ANTHROPIC_MODEL="deepseek-chat"
```

#### Kimi (Moonshot)

```bash
ANTHROPIC_AUTH_TOKEN="sk-xxxxx"
ANTHROPIC_BASE_URL="https://api.moonshot.cn"
ANTHROPIC_MODEL="moonshot-v1-8k"
```

#### 智谱 GLM

```bash
ANTHROPIC_AUTH_TOKEN="xxxxx"
ANTHROPIC_BASE_URL="https://open.bigmodel.cn/api/paas/v4"
ANTHROPIC_MODEL="glm-4"
```

#### OpenAI

```bash
ANTHROPIC_AUTH_TOKEN="sk-xxxxx"
# 不设置 BASE_URL，使用默认值
ANTHROPIC_MODEL="gpt-4"
```

### 配置文件方式

创建 `~/.oh-enterprise/config.json`:

```json
{
  "provider": {
    "api_key": "your-api-key",
    "base_url": "https://api.example.com",
    "model": "glm-5",
    "max_tokens": 4096,
    "temperature": 0.7
  },
  "auth": {
    "jwt_secret": "your-jwt-secret",
    "jwt_expire_hours": 24
  },
  "server": {
    "port": 8000,
    "host": "0.0.0.0"
  }
}
```

---

## 用户认证配置

### JWT 配置

**默认值**:
- Secret: `change-this-secret-in-production`
- 过期时间: 24 小时

**生产环境配置**:

```python
# 方式一：代码配置
from openharness.enterprise.auth import set_auth_config, AuthConfig

set_auth_config(AuthConfig(
    jwt_secret="your-secure-random-secret-at-least-32-chars",
    jwt_expire_hours=24
))
```

```bash
# 方式二：环境变量（需要修改代码支持）
export JWT_SECRET="your-secure-random-secret"
export JWT_EXPIRE_HOURS="24"
```

### 密码策略

**默认要求**:
- 至少 8 个字符
- 包含至少一个字母
- 包含至少一个数字

**自定义密码策略** (修改 `auth/auth.py`):

```python
def validate_password_strength(self, password: str) -> bool:
    if len(password) < 8:
        return False
    has_letter = any(c.isalpha() for c in password)
    has_number = any(c.isdigit() for c in password)
    return has_letter and has_number
```

---

## 数据库配置

### 默认配置

- 类型: SQLite
- 路径: `~/.oh-enterprise/data.db`

### 自定义数据库路径

```python
from openharness.enterprise.storage import init_database

# 初始化时指定路径
db = init_database("/data/openharness/data.db")
```

### PostgreSQL 支持（扩展）

需要修改 `database.py`:

```python
# 安装依赖
# pip install asyncpg

# 修改连接方式
import asyncpg

async def get_postgres_connection():
    return await asyncpg.connect(
        host="localhost",
        port=5432,
        user="postgres",
        password="password",
        database="openharness"
    )
```

---

## 前端配置

### 开发环境代理配置

**文件**: `web/vite.config.ts`

```typescript
export default defineConfig({
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true,
      },
    },
  },
})
```

### 生产环境 API 地址

**方式一：环境变量**

创建 `web/.env.production`:

```
VITE_API_BASE_URL=https://api.your-domain.com
```

**方式二：修改代码**

```typescript
// web/src/services/api.ts
const api = axios.create({
  baseURL: 'https://api.your-domain.com/api',
  timeout: 30000,
})
```

### 构建配置

```bash
# 构建
cd web
npm run build

# 输出目录: web/dist/
```

---

## Skills 配置

### 目录结构

```
~/.oh-enterprise/
├── shared/
│   └── skills/              # 共享 Skills（所有用户可用）
│       ├── brainstorming/
│       │   └── SKILL.md
│       └── enterprise-knowledge/
│           └── SKILL.md
└── users/
    └── {user_id}/
        └── skills/          # 用户私有 Skills
            └── my-skill/
                └── SKILL.md
```

### SKILL.md 格式

```markdown
---
name: skill-name
description: "Skill 描述"
---

# Skill Name

## Description
详细描述

## Instructions
具体指令，告诉 AI 如何使用这个 skill

## Examples
- 示例 1
- 示例 2
```

### 创建新 Skill

**命令行方式**:

```bash
# 创建目录
mkdir -p ~/.oh-enterprise/shared/skills/my-skill

# 创建 SKILL.md
cat > ~/.oh-enterprise/shared/skills/my-skill/SKILL.md << 'EOF'
# My Skill

## Description
这是一个示例 Skill

## Instructions
当用户询问 X 时，你应该：
1. 步骤一
2. 步骤二
EOF
```

**API 方式**:

```bash
# 暂不支持 API 创建，需手动创建文件
```

### Skill 权限配置

**默认行为**: 所有共享 Skills 对所有用户可用

**限制访问**:

```bash
# 调用 Admin API
curl -X POST http://localhost:8000/api/admin/skills/my-skill/permissions \
  -H "Authorization: Bearer <admin-token>" \
  -H "Content-Type: application/json" \
  -d '{"user_ids": [1, 2, 3]}'
```

---

## 完整配置示例

### 开发环境

```bash
# ~/.bashrc 或 PowerShell Profile

# LLM 配置
export ANTHROPIC_AUTH_TOKEN="sk-sp-xxxxx"
export ANTHROPIC_BASE_URL="https://coding.dashscope.aliyuncs.com/apps/anthropic"
export ANTHROPIC_MODEL="glm-5"

# JWT 配置
export JWT_SECRET="dev-secret-change-in-production"
```

### 生产环境

```bash
# /etc/systemd/system/openharness.service

[Service]
Environment="ANTHROPIC_AUTH_TOKEN=sk-sp-xxxxx"
Environment="ANTHROPIC_BASE_URL=https://coding.dashscope.aliyuncs.com/apps/anthropic"
Environment="ANTHROPIC_MODEL=glm-5"
```

```bash
# ~/.oh-enterprise/config.json

{
  "provider": {
    "api_key": "sk-sp-xxxxx",
    "base_url": "https://coding.dashscope.aliyuncs.com/apps/anthropic",
    "model": "glm-5",
    "max_tokens": 4096
  },
  "auth": {
    "jwt_secret": "production-secret-at-least-32-characters-long",
    "jwt_expire_hours": 24
  }
}
```

---

## 配置验证

### 检查 LLM 配置

```bash
# 启动服务后发送消息
# 后端日志应显示：
# [Agent] Calling LLM: anthropic / glm-5
```

### 检查 Skills 配置

```bash
# 调用 API
curl http://localhost:8000/api/skills \
  -H "Authorization: Bearer <token>"

# 应返回 skills 列表
{
  "personal": [],
  "shared": [
    {"name": "brainstorming", "title": "..."},
    {"name": "enterprise-knowledge", "title": "..."}
  ]
}
```

### 检查数据库

```bash
# 查看数据库文件
ls -la ~/.oh-enterprise/data.db

# 查看表结构
sqlite3 ~/.oh-enterprise/data.db ".tables"
```

---

## 常见配置问题

### 1. LLM 无响应

**检查**:
```bash
echo $ANTHROPIC_AUTH_TOKEN
echo $ANTHROPIC_BASE_URL
```

**解决**: 确保环境变量在启动服务的终端中设置

### 2. Skills 未加载

**检查**:
```bash
ls ~/.oh-enterprise/shared/skills/
```

**解决**: 确保 SKILL.md 文件存在且格式正确

### 3. JWT Token 过期

**解决**: 重新登录获取新 Token，或调整 `jwt_expire_hours`

### 4. 跨域问题

**解决**: 检查 Nginx 或 FastAPI CORS 配置

```python
# server.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-domain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```