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
  // Extract language from className (e.g., "language-mermaid")
  const match = /language-(\w+)/.exec(className || '')
  const language = match ? match[1] : ''
  
  // Get the code content
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

  // Handle markdown blocks - render them instead of showing as code
  if (language === 'markdown' && !inline) {
    return (
      <div className="markdown-rendered" style={{ marginBottom: '12px' }}>
        <ReactMarkdown remarkPlugins={[remarkGfm]}>
          {codeContent}
        </ReactMarkdown>
      </div>
    )
  }

  // [新增] Handle HTML blocks - 用iframe隔离渲染，自适应高度
  if (language === 'html' && !inline) {
    const [iframeHeight, setIframeHeight] = useState(300)
    
    // 解码HTML实体
    const decodedContent = codeContent
      .replace(/&lt;/g, '<')
      .replace(/&gt;/g, '>')
      .replace(/&amp;/g, '&')
      .replace(/&quot;/g, '"')
      .replace(/&#39;/g, "'")
      .replace(/&nbsp;/g, ' ')
    
    // 处理HTML内容，移除宽度限制
    const processedContent = decodedContent
      .replace(/max-width\s*:\s*\d+px/gi, '')
      .replace(/max-width\s*:\s*\d+%/gi, '')
      .replace(/width\s*:\s*\d+px/gi, '')
      .replace(/margin\s*:\s*\d+px\s+auto/gi, 'margin: 0')
      .replace(/<body/gi, '<body style="width: 100%; margin: 0; padding: 20px;"')
    
    // iframe加载后自适应高度
    const handleIframeLoad = (e: React.SyntheticEvent<HTMLIFrameElement>) => {
      try {
        const iframe = e.currentTarget
        const doc = iframe.contentDocument || iframe.contentWindow?.document
        if (doc && doc.body) {
          // 获取内容高度
          const height = doc.body.scrollHeight || doc.documentElement.scrollHeight
          setIframeHeight(Math.max(height + 40, 200))  // 加40px padding，最小200px
        }
      } catch (err) {
        // 跨域情况下可能无法访问，保持默认高度
        console.log('Cannot access iframe content:', err)
      }
    }
    
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

  // Handle Mermaid diagrams
  if (language === 'mermaid' && !inline) {
    return <MermaidRenderer chart={codeContent} />
  }

  // Handle regular code blocks (including html - show as code, not render)
  if (!inline && className) {
    return (
      <pre 
        style={{
          backgroundColor: '#1a2332',
          padding: '16px',
          borderRadius: '8px',
          overflow: 'auto',
          fontSize: '14px',
          lineHeight: '1.5',
          marginBottom: '12px',
          color: '#e2e8f0',
        }}
        {...props}
      >
        <code className={className}>{children}</code>
      </pre>
    )
  }

  // Handle inline code
  if (inline) {
    return (
      <code 
        style={{
          backgroundColor: '#374151',
          padding: '2px 6px',
          borderRadius: '4px',
          fontSize: '0.9em',
          color: '#00d4ff',
        }}
        {...props}
      >
        {children}
      </code>
    )
  }

  // Default case - no language specified, treat as plain text
  return (
    <pre style={{ 
      backgroundColor: '#1a2332', 
      padding: '16px', 
      borderRadius: '8px',
      overflow: 'auto',
      color: '#e2e8f0',
    }}>
      <code>{children}</code>
    </pre>
  )
}