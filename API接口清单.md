# API 接口清单

## 1. 认证接口

### 1.1 登录
- **POST** `/api/auth/login`
- 描述：用户登录
- 请求体：`{ "username": "string", "password": "string" }`
- 响应：`{ "token": "string", "user": {...} }`

### 1.2 Token 获取
- **POST** `/api/auth/token-by-api-key`
- 描述：通过 API Key 获取 Token
- 请求体：`{ "api_key": "string", "expires_in": 3600 }`

### 1.3 当前用户
- **GET** `/api/auth/me`
- 描述：获取当前登录用户信息
- 认证：Bearer Token

## 2. 会话接口

### 2.1 会话列表
- **GET** `/api/sessions`
- 描述：获取用户的所有会话

### 2.2 会话消息
- **GET** `/api/sessions/{id}/messages`
- 描述：获取会话的消息历史

### 2.3 删除会话
- **DELETE** `/api/sessions/{id}`
- 描述：删除指定会话

### 2.4 恢复会话
- **POST** `/api/sessions/{id}/restore`
- 描述：恢复会话上下文

## 3. 聊天接口

### 3.1 WebSocket 聊天
- **WebSocket** `/ws/chat`
- 描述：实时聊天通信
- 参数：`token` (query parameter)

## 4. Skills 接口

### 4.1 Skills 列表
- **GET** `/api/skills`
- 描述：获取所有可用的 Skills

### 4.2 Skill 详情
- **GET** `/api/skills/{name}`
- 描述：获取指定 Skill 的详细信息

### 4.3 刷新 Skills
- **POST** `/api/skills/reload`
- 描述：重新加载 Skills

### 4.4 上传 Skill
- **POST** `/api/skills/upload`
- 描述：上传新的 Skill (ZIP 格式)

### 4.5 删除 Skill
- **DELETE** `/api/skills/{name}`
- 描述：删除指定 Skill

## 5. 管理员接口

### 5.1 用户管理
- **GET** `/api/admin/users` - 用户列表
- **POST** `/api/admin/users` - 创建用户
- **GET** `/api/admin/users/{id}` - 用户详情
- **PUT** `/api/admin/users/{id}` - 更新用户
- **DELETE** `/api/admin/users/{id}` - 禁用用户

### 5.2 API Key 管理
- **GET** `/api/admin/users/{id}/api-key` - 查看 API Key
- **POST** `/api/admin/users/{id}/api-key` - 重新生成 API Key

### 5.3 系统状态
- **GET** `/api/admin/system/status` - 系统状态

### 5.4 审计日志
- **GET** `/api/admin/audit-logs` - 审计日志列表

## 6. 智能记忆接口

### 6.1 获取上下文
- **GET** `/api/context`
- 描述：获取用户完整上下文（含记忆）

### 6.2 触发记忆反思
- **POST** `/api/meditate`
- 描述：手动触发 Meditate

### 6.3 批量 Meditate
- **POST** `/api/meditate/all`
- 描述：管理员触发所有用户 Meditate

### 6.4 提取用户信息
- **POST** `/api/learning/extract`
- 描述：手动触发用户信息提取

## 7. 文件接口

### 7.1 列出文件
- **GET** `/api/files`
- 描述：列出用户工作区文件

### 7.2 读取文件
- **GET** `/api/files/{path}`
- 描述：读取指定文件内容

### 7.3 写入文件
- **PUT** `/api/files/{path}`
- 描述：写入文件内容

### 7.4 删除文件
- **DELETE** `/api/files/{path}`
- 描述：删除指定文件

---

**总计**: 7 大类，25+ 接口