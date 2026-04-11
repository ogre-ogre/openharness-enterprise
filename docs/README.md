# OpenHarness Enterprise 文档索引

## 文档列表

| 文档 | 说明 |
|------|------|
| [ARCHITECTURE.md](ARCHITECTURE.md) | 工程架构说明 |
| [SOURCE_CODE.md](SOURCE_CODE.md) | 源码说明 |
| [CONFIGURATION.md](CONFIGURATION.md) | 配置文件说明 |
| [SETUP_GUIDE.md](SETUP_GUIDE.md) | 配置方法 |
| [DEPLOYMENT.md](DEPLOYMENT.md) | 部署方式说明 |
| [LLM_CONFIG.md](LLM_CONFIG.md) | LLM 模型配置指南 |
| [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) | 实现计划 |
| [specs/2024-04-08-openharness-enterprise-design.md](specs/2024-04-08-openharness-enterprise-design.md) | 设计文档 |

## 快速开始

### 1. 配置 LLM

```bash
export ANTHROPIC_AUTH_TOKEN="your-api-key"
export ANTHROPIC_BASE_URL="https://coding.dashscope.aliyuncs.com/apps/anthropic"
export ANTHROPIC_MODEL="glm-5"
```

### 2. 启动服务

```bash
uv sync --extra dev
uv run oh-enterprise init
uv run oh-enterprise start
```

### 3. 访问

- 前端: http://localhost:3000
- API: http://localhost:8000/docs
- 默认账号: admin / admin123

## 常用命令

```bash
# 后端开发
uv run oh-enterprise start              # 启动服务
uv run oh-enterprise init               # 初始化
uv run pytest tests/ -v                 # 运行测试

# 前端开发
cd web && npm run dev                   # 启动开发服务器
cd web && npm run build                 # 构建生产版本
```

## 目录结构

```
openharness-enterprise/
├── src/openharness/enterprise/    # 后端源码
├── web/                           # 前端源码
├── docs/                          # 文档
│   ├── ARCHITECTURE.md
│   ├── SOURCE_CODE.md
│   ├── CONFIGURATION.md
│   ├── SETUP_GUIDE.md
│   ├── DEPLOYMENT.md
│   └── LLM_CONFIG.md
├── tests/                         # 测试
└── scripts/                       # 脚本
```