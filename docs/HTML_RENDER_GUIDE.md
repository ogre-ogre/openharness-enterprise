# 前端 HTML 渲染技术指南

> 版本: v1.0  
> 日期: 2026-04-14  
> 适用场景: 在聊天界面中渲染用户/LLM生成的HTML内容

---

## 1. 问题背景

### 1.1 常见问题

当在聊天界面中展示HTML代码时，会遇到以下问题：

| 问题 | 原因 | 影响 |
|-----|------|------|
| HTML显示为代码块而非渲染结果 | ReactMarkdown默认将所有代码块展示为 `<pre><code>` | 用户看不到实际效果 |
| HTML实体被转义 | LLM输出经过Markdown处理，`<` → `&lt;`, `>` → `&gt;` | 内容无法正确解析 |
| 渲染后页面变窄 | HTML内包含 `max-width: 800px`、`margin: 50px auto` 等限制性样式 | 破坏页面布局 |
| 高度不够需要滚动 | iframe默认固定高度 | 用户需要滚动查看完整内容 |
| 样式污染父页面 | 直接用 `dangerouslySetInnerHTML` 渲染 | HTML样式影响整个页面 |

### 1.2 目标效果

- HTML代码块应渲染为实际页面效果
- 不影响父页面布局
- 自适应高度，无需滚动
- 内容宽度正常显示

---

## 2. 解决方案

### 2.1 技术选型对比

| 方案 | 优点 | 缺点 | 适用场景 |
|-----|------|------|---------|
| `dangerouslySetInnerHTML` | 简单直接 | 样式污染、安全风险 | 简单HTML片段 |
| **iframe + srcDoc** | 隔离渲染、安全 | 需要处理高度 | **推荐方案** |
| 新窗口预览 | 完全隔离 | 用户需手动点击 | 大型HTML页面 |

**推荐**: 使用 iframe + srcDoc 方案

---

## 3. 核心代码实现

### 3.1 CodeBlock.tsx 组件

```tsx
import { useMemo, useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import MermaidRenderer from './MermaidRenderer'

interface CodeBlockProps {
  node?: any
  inline?: boolean
  className?: string
  children?: React.ReactNode
}

export default function CodeBlock({ 
  inline, 
  className, 
  children, 
  ...props 
}: CodeBlockProps) {
  // 1. 提取语言标签
  const match = /language-(\w+)/.exec(className || '')
  const language = match ? match[1] : ''
  
  // 2. 获取代码内容
  const codeContent = useMemo(() => {
    if (!children) return ''
    if (Array.isArray(children)) {
      return children.map(child => {
        if (typeof child === 'string') return child
        if (child && typeof child === 'object' && 'props' in child) {
          return child.props.children || ''
        }
        return ''
      }).join('')
    }
    if (typeof children === 'string') return children
    return String(children)
  }, [children])

  // 3. 处理 markdown 代码块 - 渲染内容
  if (language === 'markdown' && !inline) {
    return (
      <div className="markdown-rendered">
        <ReactMarkdown remarkPlugins={[remarkGfm]}>
          {codeContent}
        </ReactMarkdown>
      </div>
    )
  }

  // 4. 【核心】处理 HTML 代码块 - iframe 隔离渲染
  if (language === 'html' && !inline) {
    // 4.1 iframe 高度状态
    const [iframeHeight, setIframeHeight] = useState(300)
    
    // 4.2 解码 HTML 实体
    const decodedContent = codeContent
      .replace(/&lt;/g, '<')
      .replace(/&gt;/g, '>')
      .replace(/&amp;/g, '&')
      .replace(/&quot;/g, '"')
      .replace(/&#39;/g, "'")
      .replace(/&nbsp;/g, ' ')
    
    // 4.3 处理限制性样式
    const processedContent = decodedContent
      // 移除 max-width 限制
      .replace(/max-width\s*:\s*\d+px/gi, '')
      .replace(/max-width\s*:\s*\d+%/gi, '')
      // 移除固定宽度
      .replace(/width\s*:\s*\d+px/gi, '')
      // 移除居中 margin（会导致内容窄）
      .replace(/margin\s*:\s*\d+px\s+auto/gi, 'margin: 0')
      // 设置 body 全宽
      .replace(/<body/gi, '<body style="width: 100%; margin: 0; padding: 20px;"')
    
    // 4.4 iframe 加载后自适应高度
    const handleIframeLoad = (e: React.SyntheticEvent<HTMLIFrameElement>) => {
      try {
        const iframe = e.currentTarget
        const doc = iframe.contentDocument || iframe.contentWindow?.document
        if (doc && doc.body) {
          // 获取内容实际高度
          const height = doc.body.scrollHeight || doc.documentElement.scrollHeight
          // 设置高度（加 padding，最小 200px）
          setIframeHeight(Math.max(height + 40, 200))
        }
      } catch (err) {
        // 跨域情况下无法访问，保持默认高度
        console.log('Cannot access iframe content:', err)
      }
    }
    
    // 4.5 返回 iframe
    return (
      <iframe
        srcDoc={processedContent}
        onLoad={handleIframeLoad}
        style={{
          width: '100%',
          height: iframeHeight,
          border: 'none',
          borderRadius: '8px',
          marginBottom: '12px',
          backgroundColor: '#fff',
          overflow: 'hidden',
        }}
        sandbox="allow-scripts allow-same-origin"
        title="HTML Preview"
      />
    )
  }

  // 5. 其他语言 - 显示为代码块
  if (!inline && className) {
    return (
      <pre style={{
        backgroundColor: '#1a2332',
        padding: '16px',
        borderRadius: '8px',
        overflow: 'auto',
        color: '#e2e8f0',
      }}>
        <code className={className}>{children}</code>
      </pre>
    )
  }

  // 6. 内联代码
  if (inline) {
    return (
      <code style={{
        backgroundColor: '#374151',
        padding: '2px 6px',
        borderRadius: '4px',
        color: '#00d4ff',
      }}>
        {children}
      </code>
    )
  }

  return <pre><code>{children}</code></pre>
}
```

---

## 4. 关键技术点详解

### 4.1 HTML实体解码

**问题**: Markdown 解析器会将 HTML 标签转义

```html
<!-- LLM 输出 -->
<div>Hello</div>

<!-- ReactMarkdown 处理后 -->
&lt;div&gt;Hello&lt;/div&gt;
```

**解决**: 字符串替换解码

```tsx
const decodedContent = codeContent
  .replace(/&lt;/g, '<')
  .replace(/&gt;/g, '>')
  .replace(/&amp;/g, '&')
  .replace(/&quot;/g, '"')
  .replace(/&#39;/g, "'")
  .replace(/&nbsp;/g, ' ')
```

### 4.2 移除限制性样式

**问题**: HTML 内可能包含限制宽度的样式

```html
<style>
body {
  max-width: 800px;      /* 限制宽度 */
  margin: 50px auto;     /* 居中，导致窄 */
}
</style>
```

**解决**: 正则替换

```tsx
const processedContent = decodedContent
  .replace(/max-width\s*:\s*\d+px/gi, '')
  .replace(/margin\s*:\s*\d+px\s+auto/gi, 'margin: 0')
  .replace(/<body/gi, '<body style="width: 100%; margin: 0;"')
```

### 4.3 iframe 自适应高度

**核心原理**:

```
iframe 加载完成 → 读取 contentDocument.body.scrollHeight → 更新 iframe height
```

**代码**:

```tsx
const handleIframeLoad = (e) => {
  const iframe = e.currentTarget
  const doc = iframe.contentDocument
  const height = doc.body.scrollHeight
  setIframeHeight(height + 40)  // 加 padding
}
```

**注意**: 
- 需要在 `onLoad` 事件后读取（iframe内容加载完成）
- 加 40px padding 防止底部被截断
- 设置最小高度防止太短

### 4.4 iframe 安全配置

```tsx
<iframe
  srcDoc={processedContent}
  sandbox="allow-scripts allow-same-origin"  // 限制权限
  title="HTML Preview"
/>
```

**sandbox 属性说明**:

| 值 | 说明 |
|---|------|
| `allow-scripts` | 允许执行 JavaScript |
| `allow-same-origin` | 允许同源访问 |
| 无 `allow-forms` | 禁止表单提交 |
| 无 `allow-popups` | 禁止弹出窗口 |

---

## 5. 最佳实践

### 5.1 样式隔离

**推荐**: 使用 iframe 渲染 HTML

```tsx
// ✅ 推荐
<iframe srcDoc={content} style={{ width: '100%' }} />

// ❌ 不推荐（样式污染）
<div dangerouslySetInnerHTML={{ __html: content }} />
```

### 5.2 高度自适应

**推荐**: 动态读取内容高度

```tsx
// ✅ 推荐
const [height, setHeight] = useState(300)
<iframe onLoad={(e) => {
  setHeight(e.currentTarget.contentDocument.body.scrollHeight)
}} />

// ❌ 不推荐（固定高度，需要滚动）
<iframe style={{ height: '400px' }} />
```

### 5.3 处理不同类型内容

| 内容类型 | 处理方式 |
|---------|---------|
| ` ```markdown ` | ReactMarkdown 渲染 |
| ` ```html ` | iframe 渲染 |
| ` ```mermaid ` | Mermaid 组件渲染 |
| ` ```python/js ` | 显示为代码块 |

### 5.4 CSS 配置

```css
/* iframe 容器样式 */
iframe {
  width: 100%;
  border: none;
  border-radius: 8px;
  background: #fff;
  overflow: hidden;  /* 防止溢出 */
}

/* markdown 渲染容器 */
.markdown-rendered {
  width: 100%;
  margin-bottom: 12px;
}
```

---

## 6. 常见问题排查

### 6.1 iframe 高度为 0

**原因**: 内容未加载完成

**解决**: 确保 `onLoad` 事件触发后再读取高度

```tsx
// 检查加载状态
const handleIframeLoad = (e) => {
  const iframe = e.currentTarget
  if (!iframe.contentDocument) {
    console.log('iframe 未加载完成')
    return
  }
  // ...读取高度
}
```

### 6.2 无法访问 contentDocument

**原因**: 跨域限制或 sandbox 配置问题

**解决**: 
1. 使用 `srcDoc` 而非 `src`（同源）
2. 添加 `allow-same-origin` 到 sandbox

```tsx
<iframe 
  srcDoc={content}           // 使用 srcDoc
  sandbox="allow-scripts allow-same-origin"
/>
```

### 6.3 内容仍然窄

**原因**: 未正确移除限制性样式

**解决**: 检查正则匹配

```tsx
// 测试正则
const testHtml = '<style>body { max-width: 800px; }</style>'
console.log(testHtml.replace(/max-width\s*:\s*\d+px/gi, ''))
// 应输出: '<style>body { ; }</style>'
```

---

## 7. 扩展方案

### 7.1 新窗口预览按钮

对于大型 HTML 页面，可提供"预览"按钮：

```tsx
const openPreview = () => {
  const blob = new Blob([processedContent], { type: 'text/html' })
  const url = URL.createObjectURL(blob)
  window.open(url, '_blank')
}

<Button onClick={openPreview}>在新窗口预览</Button>
```

### 7.2 多语言代码块统一处理

```tsx
const RENDERABLE_LANGUAGES = ['markdown', 'html', 'mermaid']

if (RENDERABLE_LANGUAGES.includes(language)) {
  // 渲染处理
} else {
  // 显示为代码块
}
```

---

## 8. 参考代码位置

| 文件 | 说明 |
|-----|------|
| `web/src/components/CodeBlock.tsx` | 核心渲染组件 |
| `web/src/components/MermaidRenderer.tsx` | Mermaid图表渲染 |
| `web/src/pages/Chat.css` | iframe样式配置 |

---

## 附录：完整代码片段

```tsx
// 最小化 HTML iframe 渲染示例
import { useState } from 'react'

function HtmlRenderer({ htmlCode }) {
  const [height, setHeight] = useState(300)
  
  // 解码 HTML 实体
  const decoded = htmlCode
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&amp;/g, '&')
  
  // 移除限制性样式
  const processed = decoded
    .replace(/max-width\s*:\s*\d+px/gi, '')
    .replace(/margin\s*:\s*\d+px\s+auto/gi, 'margin: 0')
  
  return (
    <iframe
      srcDoc={processed}
      onLoad={(e) => {
        const doc = e.currentTarget.contentDocument
        if (doc?.body) {
          setHeight(doc.body.scrollHeight + 40)
        }
      }}
      style={{ width: '100%', height, border: 'none' }}
      sandbox="allow-scripts allow-same-origin"
    />
  )
}
```

---

*文档版本: v1.0 | 更新日期: 2026-04-14*