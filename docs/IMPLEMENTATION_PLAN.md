# OpenHarness Enterprise 实现计划

> 版本: v1.0  
> 日期: 2024-04-08  
> 基于设计文档: [2024-04-08-openharness-enterprise-design.md](docs/specs/2024-04-08-openharness-enterprise-design.md)

---

## 实现阶段划分

### Phase 1: 核心功能（MVP）- 预计 2 周

#### 1.1 存储层（2天）
- [ ] 创建 SQLite 数据库初始化脚本
- [ ] 实现 database.py（用户、会话、审计表操作）
- [ ] 实现 audit.py（审计日志记录）
- [ ] 单元测试

**文件清单**:
```
src/openharness/enterprise/storage/
├── __init__.py
├── database.py      # SQLite 操作封装
├── audit.py         # 审计日志
└── models.py        # 数据模型定义
```

#### 1.2 用户管理（3天）
- [ ] 实现 UserManager（用户 CRUD）
- [ ] 实现 WorkspaceManager（工作区初始化、上下文加载）
- [ ] 用户工作区目录结构创建
- [ ] API Key 生成与管理
- [ ] 单元测试

**文件清单**:
```
src/openharness/enterprise/users/
├── __init__.py
├── manager.py       # 用户 CRUD
├── workspace.py     # 工作区管理
├── context.py       # 用户上下文注入
└── models.py        # 用户模型
```

#### 1.3 认证服务（3天）
- [ ] 实现 AuthService（登录、JWT 生成/验证）
- [ ] 实现 InternalAuthService（API Key 获取 Token）
- [ ] 认证中间件（Token 验证、用户注入）
- [ ] 密码哈希工具
- [ ] 单元测试

**文件清单**:
```
src/openharness/enterprise/auth/
├── __init__.py
├── auth.py          # 主认证服务
├── internal_api.py  # API Key 认证
├── middleware.py    # FastAPI 中间件
└── jwt_utils.py     # JWT 工具
```

#### 1.4 WebChat Channel（4天）
- [ ] 实现 WebChatChannel（WebSocket 连接处理）
- [ ] 消息协议（JSON 格式定义）
- [ ] Agent Engine 集成（用户上下文注入）
- [ ] 流式响应推送
- [ ] 会话管理（创建、恢复、历史）
- [ ] 单元测试

**文件清单**:
```
src/openharness/enterprise/channels/
├── __init__.py
├── webchat.py       # WebSocket Channel
├── session.py       # 会话管理
└── protocol.py      # 消息协议定义
```

#### 1.5 基础 Web 前端（3天）
- [ ] React 项目初始化（Vite + TypeScript）
- [ ] 登录页面
- [ ] 聊天页面（WebSocket 连接、消息渲染）
- [ ] 会话列表侧边栏
- [ ] API 服务封装

**文件清单**:
```
web/
├── src/
│   ├── pages/
│   │   ├── Login.tsx
│   │   └── Chat.tsx
│   ├── components/
│   │   ├── SessionList.tsx
│   │   ├── MessageList.tsx
│   │   ├── InputBox.tsx
│   │   └── ToolCallDisplay.tsx
│   ├── services/
│   │   ├── api.ts
│   │   ├── websocket.ts
│   │   └── auth.ts
│   └── App.tsx
├── package.json
├── vite.config.ts
└── tsconfig.json
```

---

### Phase 2: 管理功能 - 预计 1 周

#### 2.1 Admin API（3天）
- [ ] 用户管理接口（CRUD、API Key 管理）
- [ ] 系统状态接口
- [ ] 审计日志查询接口
- [ ] 共享资源管理接口（基础）
- [ ] 权限验证中间件
- [ ] 单元测试

**文件清单**:
```
src/openharness/enterprise/admin/
├── __init__.py
├── api.py           # Admin REST API
├── users.py         # 用户管理接口
├── system.py        # 系统管理接口
└── shared.py        # 共享资源管理
```

#### 2.2 管理后台前端（4天）
- [ ] 管理后台布局
- [ ] 用户管理页面（列表、创建、编辑、API Key）
- [ ] 系统状态页面
- [ ] 审计日志页面
- [ ] 权限路由守卫

**文件清单**:
```
web/src/pages/admin/
├── AdminLayout.tsx
├── Users.tsx
├── Status.tsx
├── AuditLogs.tsx
```

---

### Phase 3: 共享资源 - 预计 1 周

#### 3.1 共享资源池（3天）
- [ ] 共享 Skills/Plugins 目录扫描
- [ ] 权限表管理
- [ ] 资源注册表
- [ ] 用户可用资源查询

**文件清单**:
```
src/openharness/enterprise/shared/
├── __init__.py
├── registry.py      # 资源注册表
├── permissions.py   # 权限管理
└── loader.py        # 资源加载
```

#### 3.2 资源管理界面（2天）
- [ ] 共享资源列表页面
- [ ] 资源上传/删除
- [ ] 权限配置界面

---

### Phase 4: 增强功能 - 预计 1 周

#### 4.1 会话历史检索（2天）
- [ ] 消息存储优化
- [ ] 搜索接口
- [ ] 前端搜索组件

#### 4.2 用户偏好配置（2天）
- [ ] 用户配置文件支持
- [ ] 前端设置页面

#### 4.3 嵌入模式优化（1天）
- [ ] embed 模式前端（无侧边栏）
- [ ] 配置参数支持

#### 4.4 CLI 完善（1天）
- [ ] 所有 CLI 命令实现
- [ ] 配置文件支持

---

## 关键实现细节

### 优先级排序

```
P0 (必须): 存储层 → 认证服务 → 用户管理 → WebChat Channel → 基础前端
P1 (重要): Admin API → 管理后台
P2 (可选): 共享资源 → 会话检索 → 嵌入优化
```

### 技术依赖关系

```
database.py → auth.py → middleware.py
              ↓
           manager.py → workspace.py → context.py
              ↓
           webchat.py (依赖 context.py)
              ↓
           server.py (整合所有模块)
```

### 测试策略

- 每个模块完成后立即编写单元测试
- Phase 1 完成后进行集成测试
- Phase 2 完成后进行端到端测试
- 使用 pytest + pytest-asyncio

---

## 开发启动建议

1. **克隆 OpenHarness 原项目**
   ```bash
   git clone https://github.com/HKUDS/OpenHarness.git D:\openharness-base
   ```

2. **创建 enterprise 模块**
   - 在 `src/openharness/` 下新建 `enterprise/` 目录
   - 按上述文件清单逐步创建

3. **开发顺序**
   - Day 1-2: storage/ 模块
   - Day 3-5: auth/ 模块 + users/ 模块
   - Day 6-9: channels/ 模块
   - Day 10-12: 前端基础
   - Day 13-19: Admin + 管理后台
   - Day 20-26: 共享资源 + 增强功能

---

## 风险与缓解

| 风险 | 缓解措施 |
|-----|---------|
| Agent Engine 集成复杂 | 先做简单调用，后续优化上下文注入 |
| WebSocket 稳定性 | 使用成熟库，做好断线重连 |
| 前端开发效率 | 使用 Ant Design 减少样式工作 |
| SQLite 性能瓶颈 | 预留 PostgreSQL 迁移接口 |