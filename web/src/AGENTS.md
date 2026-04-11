# web/src

**React 前端 (TypeScript)**

## OVERVIEW

React 18 + TypeScript frontend with Ant Design UI, Zustand state management, and WebSocket real-time communication.

## STRUCTURE

```
src/
├── pages/
│   ├── Chat.tsx              # 主聊天页面
│   ├── Login.tsx             # 登录页面
│   └── admin/               # 管理后台
│       ├── Users.tsx         # 用户管理
│       ├── TeamManage.tsx   # 团队管理
│       ├── ToolManage.tsx   # 工具管理
│       ├── SkillManage.tsx  # Skills 管理
│       ├── Status.tsx       # 系统状态
│       └── AuditLogs.tsx    # 审计日志
├── services/
│   ├── api.ts               # REST API 封装
│   └── websocket.ts         # WebSocket 客户端
├── stores/
│   └── auth.ts               # Zustand 认证状态
└── components/
    ├── MermaidRenderer.tsx   # Mermaid 图表渲染
    └── CodeBlock.tsx         # 代码块展示
```

## WHERE TO LOOK

| Task | File | Notes |
|------|------|-------|
| 认证状态 | `stores/auth.ts` | JWT token 存储 |
| API 调用 | `services/api.ts` | Axios 封装 |
| WebSocket | `services/websocket.ts` | 实时消息 |
| 聊天逻辑 | `pages/Chat.tsx` | 消息渲染、流式输出 |
| 管理员页面 | `pages/admin/*.tsx` | Ant Design Table |

## CONVENTIONS

- 状态管理: Zustand
- UI 组件: Ant Design 5
- 路由: react-router-dom
- 图表: Mermaid
- Markdown: react-markdown + remark-gfm

## ANTI-PATTERNS

- 禁止直接操作 DOM
- 禁止使用 jQuery
- 禁止 class 组件 (用 Function 组件)