# LLM 模型配置指南

OpenHarness Enterprise 支持连接多种 LLM 服务。

## 配置方式

### 方式一：环境变量（推荐）

```bash
# Windows PowerShell
$env:OH_API_KEY = "your-api-key"
$env:OH_BASE_URL = "https://api.openai.com/v1"  # 可选，用于兼容 API
$env:OH_MODEL = "gpt-3.5-turbo"

# Windows CMD
set OH_API_KEY=your-api-key
set OH_BASE_URL=https://api.openai.com/v1
set OH_MODEL=gpt-3.5-turbo

# Linux/Mac
export OH_API_KEY="your-api-key"
export OH_BASE_URL="https://api.openai.com/v1"
export OH_MODEL="gpt-3.5-turbo"
```

### 方式二：启动时设置

```bash
# 启动服务时设置
OH_API_KEY=your-key OH_MODEL=gpt-4 uv run oh-enterprise start
```

## 支持的 Provider

### OpenAI

```bash
OH_PROVIDER=openai
OH_API_KEY=sk-xxx
OH_MODEL=gpt-4
# OH_BASE_URL 不需要设置，使用默认值
```

### DeepSeek

```bash
OH_PROVIDER=openai-compatible
OH_API_KEY=sk-xxx
OH_BASE_URL=https://api.deepseek.com/v1
OH_MODEL=deepseek-chat
```

### Kimi (Moonshot)

```bash
OH_PROVIDER=openai-compatible
OH_API_KEY=sk-xxx
OH_BASE_URL=https://api.moonshot.cn/v1
OH_MODEL=moonshot-v1-8k
```

### 智谱 GLM

```bash
OH_PROVIDER=openai-compatible
OH_API_KEY=xxx
OH_BASE_URL=https://open.bigmodel.cn/api/paas/v4
OH_MODEL=glm-4
```

### 阿里云百炼

```bash
OH_PROVIDER=openai-compatible
OH_API_KEY=sk-xxx
OH_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
OH_MODEL=qwen-turbo
```

### 本地模型 (Ollama)

```bash
OH_PROVIDER=openai-compatible
OH_API_KEY=ollama  # Ollama 不需要真实 key
OH_BASE_URL=http://localhost:11434/v1
OH_MODEL=llama2
```

### 其他 OpenAI 兼容服务

任何支持 OpenAI API 格式的服务都可以使用，只需设置正确的 `OH_BASE_URL`。

## 示例配置

### 使用 DeepSeek

```powershell
# PowerShell
$env:OH_API_KEY = "sk-xxxxx"
$env:OH_BASE_URL = "https://api.deepseek.com/v1"
$env:OH_MODEL = "deepseek-chat"

# 启动服务
cd D:\openharness-enterprise
uv run oh-enterprise start
```

### 使用 Kimi

```powershell
$env:OH_API_KEY = "sk-xxxxx"
$env:OH_BASE_URL = "https://api.moonshot.cn/v1"
$env:OH_MODEL = "moonshot-v1-8k"

cd D:\openharness-enterprise
uv run oh-enterprise start
```

## 验证配置

启动服务后，发送一条消息，查看后端日志：

```
[Agent] Calling LLM: openai-compatible / deepseek-chat
```

如果看到 `[Agent] No API key configured, using mock response`，说明 API Key 未正确设置。

## 常见问题

### API Key 未生效

确保环境变量在启动服务的同一个终端中设置。

### 连接超时

检查 `OH_BASE_URL` 是否正确，确保网络可以访问。

### 模型不存在

检查 `OH_MODEL` 是否正确，不同 Provider 的模型名称不同。