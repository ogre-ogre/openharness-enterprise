import { useEffect, useRef, useState } from 'react'
import mermaid from 'mermaid'

// Initialize mermaid once
mermaid.initialize({
  startOnLoad: false,
  theme: 'dark',
  themeVariables: {
    primaryColor: '#3b82f6',
    primaryTextColor: '#f1f5f9',
    primaryBorderColor: '#3b82f6',
    lineColor: '#94a3b8',
    secondaryColor: '#1a2332',
    tertiaryColor: '#1a2332',
    background: '#1a2332',
    mainBkg: '#1a2332',
    nodeBkg: '#1a2332',
    nodeBorder: '#3b82f6',
    clusterBkg: '#111827',
    clusterBorder: '#3b82f6',
    titleColor: '#f1f5f9',
    edgeLabelBackground: '#1a2332',
    actorBkg: '#1a2332',
    actorBorder: '#3b82f6',
    actorTextColor: '#f1f5f9',
    actorLineColor: '#94a3b8',
    signalColor: '#f1f5f9',
    signalTextColor: '#f1f5f9',
    labelBoxBkgColor: '#1a2332',
    labelBoxBorderColor: '#3b82f6',
    labelTextColor: '#f1f5f9',
    loopTextColor: '#f1f5f9',
    nodeTextColor: '#f1f5f9',
    noteBorderColor: '#f59e0b',
    noteBkgColor: '#1a2332',
    noteTextColor: '#f1f5f9',
    activationBorderColor: '#3b82f6',
    activationBkgColor: '#1a2332',
    sequenceNumberColor: '#f1f5f9',
  },
  flowchart: {
    curve: 'basis',
    padding: 15,
  },
  sequence: {
    diagramMarginX: 50,
    diagramMarginY: 10,
    actorMargin: 50,
    width: 150,
    height: 65,
    boxMargin: 10,
    boxTextMargin: 5,
    noteMargin: 10,
    messageMargin: 35,
    mirrorActors: true,
  },
  securityLevel: 'loose',
})

interface MermaidRendererProps {
  chart: string
  className?: string
}

/**
 * 检测文本中是否包含未闭合的 mermaid 代码块
 * 返回值：
 *   - 'complete': 存在完整的 mermaid 代码块
 *   - 'incomplete': 存在未闭合的 mermaid 代码块（正在输出）
 *   - 'none': 不存在 mermaid 代码块
 */
function detectMermaidBlockStatus(text: string): { status: 'complete' | 'incomplete' | 'none'; code: string | null } {
  // 检查是否有 ```mermaid 开始标记
  const hasMermaidStart = text.includes('```mermaid')
  
  if (!hasMermaidStart) {
    // 没有 mermaid 代码块标记，检查是否是纯 mermaid 代码
    const trimmedText = text.trim()
    const chartKeywords = [
      'graph', 'flowchart', 'sequenceDiagram', 'classDiagram',
      'stateDiagram', 'erDiagram', 'gantt', 'pie', 'mindmap',
      'timeline', 'quadrantChart', 'requirementDiagram', 'gitgraph',
      'xychart-beta', 'xychart'
    ]
    
    const firstLine = trimmedText.split('\n')[0]?.trim().toLowerCase() || ''
    const isPureMermaid = chartKeywords.some(kw => firstLine.startsWith(kw.toLowerCase()))
    
    if (isPureMermaid) {
      // 纯 mermaid 代码，认为是完整的（来自非流式输出）
      return { status: 'complete', code: trimmedText }
    }
    
    return { status: 'none', code: null }
  }
  
  // 尝试匹配完整的 ```mermaid ... ``` 格式
  const completeMatch = text.match(/```mermaid\s*([\s\S]*?)```/)
  if (completeMatch) {
    return { status: 'complete', code: completeMatch[1].trim() }
  }
  
  // 有 ```mermaid 开始但没有闭合的 ```
  // 这是流式输出中的未完成状态
  return { status: 'incomplete', code: null }
}

/**
 * 验证 mermaid 代码是否有效
 */
function isValidMermaidCode(code: string): boolean {
  if (!code || code.trim().length < 5) return false
  
  const trimmedCode = code.trim()
  
  // 必须以图表类型关键字开头
  const chartKeywords = [
    'graph', 'flowchart', 'sequenceDiagram', 'classDiagram',
    'stateDiagram', 'erDiagram', 'gantt', 'pie', 'mindmap',
    'timeline', 'quadrantChart', 'requirementDiagram', 'gitgraph',
    'xychart-beta', 'xychart'
  ]
  
  const firstLine = trimmedCode.split('\n')[0]?.trim().toLowerCase() || ''
  const hasKeyword = chartKeywords.some(kw => firstLine.startsWith(kw.toLowerCase()))
  
  if (!hasKeyword) return false
  
  return true
}

/**
 * 生成图表的哈希值，用于判断代码是否真正变化
 */
function hashChart(code: string): string {
  const lines = code.trim().split('\n').filter(l => l.trim())
  return lines.slice(0, 5).join('|')
}

export default function MermaidRenderer({ chart, className }: MermaidRendererProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const [renderedSvg, setRenderedSvg] = useState<string | null>(null)
  
  const renderCountRef = useRef(0)
  const lastRenderedHashRef = useRef<string>('')
  const isRenderedRef = useRef(false)

  useEffect(() => {
    // 检测 mermaid 代码块状态
    const { status, code } = detectMermaidBlockStatus(chart)
    
    // 如果不是 mermaid 内容，不渲染
    if (status === 'none') {
      return
    }
    
    // 如果代码块未闭合（流式输出中），显示等待状态
    if (status === 'incomplete') {
      if (containerRef.current && !isRenderedRef.current) {
        containerRef.current.innerHTML = `
          <div style="color: #64748b; text-align: center; padding: 16px; font-size: 14px;">
            <span style="animation: pulse 1.5s infinite;">正在生成图表...</span>
          </div>
          <style>
            @keyframes pulse {
              0%, 100% { opacity: 0.4; }
              50% { opacity: 1; }
            }
          </style>
        `
      }
      return // 等待完整输出
    }
    
    // 代码块完整，检查是否有效
    if (!code || !isValidMermaidCode(code)) {
      return
    }
    
    // 检查是否需要重新渲染（内容是否变化）
    const currentHash = hashChart(code)
    if (isRenderedRef.current && currentHash === lastRenderedHashRef.current) {
      return // 内容没变，保持当前状态
    }
    
    // 延迟渲染，等待内容稳定
    const currentRenderId = ++renderCountRef.current
    
    const delayTimer = setTimeout(() => {
      if (currentRenderId !== renderCountRef.current) return
      
      const renderChart = async () => {
        if (!containerRef.current || !code) return
        
        try {
          const id = `mermaid-${Date.now().toString(36)}-${Math.random().toString(36).substring(2, 7)}`
          const { svg } = await mermaid.render(id, code)
          
          if (currentRenderId === renderCountRef.current) {
            setRenderedSvg(svg)
            isRenderedRef.current = true
            lastRenderedHashRef.current = currentHash
            containerRef.current.innerHTML = svg
          }
        } catch (err) {
          console.error('Mermaid render error:', err)
          
          // 如果之前已渲染成功，保持当前状态
          if (!isRenderedRef.current && currentRenderId === renderCountRef.current && containerRef.current) {
            containerRef.current.innerHTML = `
              <pre style="color: #94a3b8; background: #1f2937; padding: 12px; border-radius: 8px; overflow-x: auto; white-space: pre-wrap; font-size: 12px;">
图表解析失败，请检查语法
              </pre>
            `
          }
        }
      }

      renderChart()
    }, 200)
    
    return () => clearTimeout(delayTimer)
  }, [chart])

  return (
    <div 
      ref={containerRef} 
      className={className}
      style={{
        backgroundColor: '#1a2332',
        borderRadius: '8px',
        padding: '16px',
        marginBottom: '12px',
        overflow: 'auto',
        maxWidth: '100%',
        minHeight: renderedSvg ? 'auto' : '60px',
      }}
    />
  )
}