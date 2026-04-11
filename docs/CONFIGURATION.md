# OpenHarness Enterprise 配置文件说明

## 后端配置

### pyproject.toml - Python 项目配置

**位置**: `pyproject.toml`

**主要内容**:

```toml
[project]
name = "openharness-enterprise"
version = "0.1.0"
requires-python = ">=3.10"

# 核心依赖
dependencies = [
    "fastapi>=0.110.0",
    "uvicorn>=0.27.0",
    "anthropic>=0.40.0",
    "python-jose[cryptography]>=3.3.0",  # JWT
    "passlib[bcrypt]>=1.7.4",            # 密码哈希
    "aiosqlite>=0.19.0",                 # 异步 SQLite
]

# 开发依赖
[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "ruff>=0.5.0",
]

# CLI 入口
[project.scripts]
oh-enterprise = "openharness.enterprise.server:main"
```

---

### 环境变量配置

**LLM Provider 配置**:

```bash
# 方式一：使用 OpenHarness 格式
OH_API_KEY=your-api-key
OH_BASE_URL=https://api.example.com/v1
OH_MODEL=gpt-4

# 方式二：使用 Anthropic 格式（推荐）
ANTHROPIC_AUTH_TOKEN=your-api-key
ANTHROPIC_BASE_URL=https://api.example.com
ANTHROPIC_MODEL=glm-5
```

**支持的 LLM 服务**:

| Provider | ANTHROPIC_BASE_URL | ANTHROPIC_MODEL |
|----------|-------------------|-----------------|
| 阿里百炼 | `https://coding.dashscope.aliyuncs.com/apps/anthropic` | `glm-5` |
| DeepSeek | `https://api.deepseek.com` | `deepseek-chat` |
| Kimi | `https://api.moonshot.cn` | `moonshot-v1-8k` |
| 智谱 GLM | `https://open.bigmodel.cn/api/paas/v4` | `glm-4` |
| OpenAI | 不设置 | `gpt-4` |

---

### JWT 配置

**默认配置** (可在 `auth/auth.py` 修改):

```python
class AuthConfig(BaseModel):
    jwt_secret: str = "change-this-secret-in-production"
    jwt_expire_hours: int = 24
    jwt_algorithm: str = "HS256"
```

**生产环境建议**:

```python
# 通过代码设置
from openharness.enterprise.auth import set_auth_config, AuthConfig

set_auth_config(AuthConfig(
    jwt_secret="your-secure-random-secret",
    jwt_expire_hours=24
))
```

---

### 数据库配置

**默认路径**:

```
~/.oh-enterprise/data.db
```

**自定义路径** (通过代码):

```python
from openharness.enterprise.storage import init_database

db = init_database("/custom/path/data.db")
```

---

## 前端配置

### package.json - NPM 配置

**位置**: `web/package.json`

**主要内容**:

```json
{
  "name": "openharness-enterprise-web",
  "version": "0.1.0",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.2.0",
    "antd": "^5.15.0",
    "axios": "^1.6.0",
    "zustand": "^4.5.0"
  }
}
```

---

### vite.config.ts - Vite 配置

**位置**: `web/vite.config.ts`

**关键配置**:

```typescript
export default defineConfig({
  plugins: [react()],
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

**生产环境修改**:

```typescript
// 移除 proxy，改为直接请求后端地址
// 或通过环境变量配置 API 地址
```

---

### tsconfig.json - TypeScript 配置

**位置**: `web/tsconfig.json`

**主要内容**:

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "lib": ["ES2020", "DOM"],
    "jsx": "react-jsx",
    "strict": true,
    "baseUrl": ".",
    "paths": {
      "@/*": ["src/*"]
    }
  }
}
```

---

## 运行时配置

### 用户配置文件

**位置**: `~/.oh-enterprise/users/{user_id}/config/`

**preferences.json - 用户偏好**:

```json
{
  "theme": "default",
  "output_style": "markdown",
  "show_tool_calls": true,
  "show_thinking": false
}
```

**provider.json - 用户 Provider 覆盖**:

```json
{
  "use_global": true,
  "model": null
}
```

---

### soul.md - 用户人格

**位置**: `~/.oh-enterprise/users/{user_id}/soul.md`

**示例**:

```markdown
# SOUL.md - 我的 Agent

## 身份

你是我的 AI 助手。

## 核心原则

- 简洁直接，不说废话
- 代码优先，解释其次
- 保持专业
```

---

### MEMORY.md - 长期记忆

**位置**: `~/.oh-enterprise/users/{user_id}/memory/MEMORY.md`

**示例**:

```markdown
# MEMORY.md - 长期记忆

## 项目信息

- 项目名称：XXX
- 技术栈：Python + FastAPI

## 重要决策

- 2024-04-08：选择 SQLite 作为数据库
```

---

## 共享资源配置

### Skills 配置

**位置**: `~/.oh-enterprise/shared/skills/{skill_name}/SKILL.md`

**格式**:

```markdown
---
name: skill-name
description: "Skill 描述"
---

# Skill Name

## Description
详细描述

## Instructions
具体指令

## Examples
示例
```

---

### 权限配置

**数据库表**: `shared_resource_permissions`

**默认行为**: 无权限记录时，所有人可访问

**配置权限**:

```python
# API 调用
POST /api/admin/skills/{skill_name}/permissions
{
    "user_ids": [1, 2, 3]  # 或 null 表示所有人
}
```

---

## 配置优先级

```
环境变量 > 代码配置 > 默认值
```

**示例**:

```bash
# 环境变量优先
ANTHROPIC_MODEL=glm-4  # 使用 glm-4

# 即使代码中设置了其他值
config = ProviderConfig(model="gpt-4")  # 被环境变量覆盖
```