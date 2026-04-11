import { useMemo } from 'react'
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

  // Handle Mermaid diagrams
  if (language === 'mermaid' && !inline) {
    return <MermaidRenderer chart={codeContent} />
  }

  // Handle regular code blocks
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

  // Default case
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