# 文件管理功能设计文档

**日期**: 2026-04-12
**状态**: 已批准
**作者**: AI Assistant

---

## 1. 概述

在 OpenHarness Enterprise 管理后台新增文件管理功能，允许用户查看自己用户目录下的文件，支持下载和删除操作。

### 1.1 需求背景

用户需要能够查看和管理自己在服务器上的文件，包括：
- 查看各目录下的文件列表
- 下载单个或多个文件（打包 ZIP）
- 下载整个文件夹
- 删除文件（按目录权限区分）

### 1.2 目标用户

- 管理员：可访问管理后台，管理所有文件
- 普通用户：可访问管理后台（仅文件管理菜单），管理自己的文件

---

## 2. 功能设计

### 2.1 页面布局

采用左右分栏布局：

- **左侧**：树形目录侧边栏，展示用户目录结构
- **右侧**：文件列表表格，展示选中目录的文件

```
┌──────────────────────────────────────────────────────────────┐
│  文件管理                              [刷新] [打包下载]      │
├─────────────────┬────────────────────────────────────────────┤
│                 │                                            │
│  📁 uploads     │   文件列表                                  │
│    ├─ file1.txt │                                            │
│    └─ file2.md  │   ☐ 文件名        大小      时间     操作   │
│                 │   ☐ file1.txt    2KB    2026-04-12  [删除] │
│  📁 skills      │   ☑ file2.md    5KB    2026-04-11  [删除] │
│    └─ skill1    │   ☑ file3.png   10KB   2026-04-10  [删除] │
│                 │                                            │
│  📁 memory      │   已选择 2 个文件                            │
│    ├─ MEMORY.md │                                            │
│    └─ 2026-...  │                                            │
│                 │                                            │
│  📁 config      │                                            │
│    └─ prefs.json│                                            │
│                 │                                            │
└─────────────────┴────────────────────────────────────────────┘
```

### 2.2 目录范围

用户可以查看以下目录：

| 目录 | 路径 | 说明 |
|------|------|------|
| uploads | `~/.oh-enterprise/users/{user_id}/uploads/` | 用户上传的文件 |
| skills | `~/.oh-enterprise/users/{user_id}/skills/` | 用户私有技能 |
| memory | `~/.oh-enterprise/users/{user_id}/memory/` | 用户记忆文件 |
| config | `~/.oh-enterprise/users/{user_id}/config/` | 用户配置文件 |
| knowledge | `~/.oh-enterprise/users/{user_id}/knowledge/` | 外置知识文件 |

### 2.3 权限矩阵

按目录区分文件操作权限：

| 目录 | 查看 | 下载 | 删除 |
|------|:----:|:----:|:----:|
| `uploads/` | ✅ | ✅ | ✅ |
| `skills/` | ✅ | ✅ | ❌ 通过技能管理页面删除 |
| `memory/` | ✅ | ✅ | ❌ 记忆文件危险，禁止删除 |
| `config/` | ✅ | ✅ | ❌ 配置文件谨慎，禁止删除 |
| `knowledge/` | ✅ | ✅ | ❌ 知识文件谨慎，禁止删除 |

---

## 3. API 设计

### 3.1 新增端点

| 端点 | 方法 | 功能 | 权限 |
|------|------|------|------|
| `/api/files/tree` | GET | 获取用户目录树结构 | 所有用户 |
| `/api/files/list` | GET | 列出指定目录下的文件 | 所有用户 |
| `/api/files/download` | POST | 打包下载文件（返回 ZIP） | 所有用户 |
| `/api/files/delete` | POST | 删除文件（按目录权限） | 按目录区分 |
| `/api/files/download/{filepath}` | GET | 单文件下载 | 所有用户 |

### 3.2 API 详细设计

#### GET /api/files/tree

获取用户目录的树形结构。

**响应示例：**
```json
{
  "tree": [
    {
      "key": "uploads",
      "title": "uploads",
      "children": [
        {"key": "uploads/file1.txt", "title": "file1.txt", "isLeaf": true},
        {"key": "uploads/file2.md", "title": "file2.md", "isLeaf": true}
      ]
    },
    {
      "key": "skills",
      "title": "skills",
      "children": [
        {"key": "skills/my-skill", "title": "my-skill", "isLeaf": false, "children": [...]}
      ]
    }
  ]
}
```

#### GET /api/files/list

列出指定目录下的文件和子目录。

**请求参数：**
- `path`: 目录路径（相对于用户根目录）

**响应示例：**
```json
{
  "path": "uploads",
  "files": [
    {
      "name": "file1.txt",
      "path": "uploads/file1.txt",
      "size": 2048,
      "type": "file",
      "modified_at": "2026-04-12T10:30:00",
      "can_delete": true
    }
  ],
  "folders": [
    {
      "name": "subfolder",
      "path": "uploads/subfolder",
      "type": "folder"
    }
  ]
}
```

#### POST /api/files/download

打包下载选中的文件和文件夹。

**请求体：**
```json
{
  "items": [
    "uploads/file1.txt",
    "uploads/file2.md",
    "skills/my-skill"
  ]
}
```

**响应：** ZIP 文件流，Content-Type: application/zip

#### POST /api/files/delete

删除文件（仅允许删除 uploads 目录下的文件）。

**请求体：**
```json
{
  "paths": ["uploads/file1.txt", "uploads/file2.md"]
}
```

**响应示例：**
```json
{
  "success": true,
  "deleted": ["uploads/file1.txt", "uploads/file2.md"],
  "failed": [],
  "message": "已删除 2 个文件"
}
```

---

## 4. 前端组件设计

### 4.1 新增文件

- `web/src/pages/admin/FileManage.tsx` - 文件管理页面组件

### 4.2 修改文件

- `web/src/App.tsx` - 新增 `/admin/files` 路由
- `web/src/pages/admin/AdminLayout.tsx` - 新增"文件管理"菜单项

### 4.3 组件结构

```tsx
// FileManage.tsx 主要结构
<Layout>
  <Sider width={250}>
    <Tree
      treeData={directoryTree}
      onSelect={handleDirectorySelect}
    />
  </Sider>
  <Content>
    <Card>
      <Space>
        <Button onClick={handleRefresh}>刷新</Button>
        <Button onClick={handleDownloadSelected}>打包下载</Button>
      </Space>
      <Table
        dataSource={files}
        columns={columns}
        rowSelection={rowSelection}
      />
    </Card>
  </Content>
</Layout>
```

---

## 5. 安全考虑

### 5.1 路径穿越防护

- 所有文件路径必须校验，确保在用户目录范围内
- 使用 `resolve().relative_to()` 检查路径有效性
- 禁止访问 `../` 等路径穿越字符

### 5.2 删除权限控制

- 删除 API 仅允许删除 `uploads/` 目录下的文件
- 其他目录返回 403 Forbidden

### 5.3 文件大小限制

- 单次打包下载总大小限制：100MB
- 超出限制时返回错误提示

---

## 6. 实现计划

### Phase 1: 后端 API（预计 1-2 小时）

1. 新增 `/api/files/tree` 端点
2. 新增 `/api/files/list` 端点
3. 新增 `/api/files/download` 端点
4. 新增 `/api/files/delete` 端点
5. 添加路径安全校验

### Phase 2: 前端页面（预计 1-2 小时）

1. 创建 FileManage.tsx 组件
2. 修改 AdminLayout.tsx 添加菜单
3. 修改 App.tsx 添加路由
4. 实现树形目录组件
5. 实现文件列表表格
6. 实现多选和下载功能

### Phase 3: 测试与调优

1. 测试各目录文件查看
2. 测试打包下载功能
3. 测试删除权限控制
4. 修复发现的问题

---

## 7. 验收标准

1. ✅ 普通用户和管理员都能看到"文件管理"菜单
2. ✅ 左侧树形目录正确展示用户目录结构
3. ✅ 点击目录节点展示该目录下的文件列表
4. ✅ 可以多选文件，点击"打包下载"生成 ZIP
5. ✅ 可以选择整个文件夹打包下载
6. ✅ `uploads/` 目录下的文件可以删除
7. ✅ 其他目录的文件显示删除按钮但点击时提示无权限
8. ✅ 非用户目录的路径访问返回错误