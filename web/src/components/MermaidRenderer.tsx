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
  // 启用 xychart 支持（柱状图、折线图）
  xychart: {
    chartWidth: 600,
    chartHeight: 400,
    titleFontSize: 20,
    titlePadding: 10,
    xAxis: {
      labelFontSize: 14,
      labelPadding: 5,
    },
    yAxis: {
      labelFontSize: 14,
      labelPadding: 5,
    },
    plotReservedSpacePercent: 50,
  },
})

interface MermaidRendererProps {
  chart: string
  className?: string
}

/**
 * 从可能包含多个代码块的文本中提取第一个 mermaid 代码块
 */
function extractMermaidCode(text: string): string | null {
  // 尝试匹配 ```mermaid ... ``` 格式
  const mermaidBlockMatch = text.match(/```mermaid\s*([\s\S]*?)```/)
  if (mermaidBlockMatch) {
    return mermaidBlockMatch[1].trim()
  }
  
  // 如果没有明确的代码块标记，检查是否以图表类型关键字开头
  const trimmedText = text.trim()
  const chartKeywords = [
    'graph', 'flowchart', 'sequenceDiagram', 'classDiagram',
    'stateDiagram', 'erDiagram', 'gantt', 'pie', 'mindmap',
    'timeline', 'quadrantChart', 'requirementDiagram', 'gitgraph',
    'xychart-beta', 'xychart'
  ]
  
  const firstLine = trimmedText.split('\n')[0].trim().toLowerCase()
  for (const kw of chartKeywords) {
    if (firstLine.startsWith(kw.toLowerCase())) {
      // 以图表关键字开头，尝试提取到可能的结束位置
      // 简单处理：返回整个文本，让后续验证处理
      return trimmedText
    }
  }
  
  return null
}

/**
 * 检查 Mermaid 代码是否看起来完整
 */
function isMermaidCodeComplete(code: string): boolean {
  if (!code || code.trim().length < 10) return false
  
  const trimmedCode = code.trim()
  
  // 基本的 mermaid 图表类型关键字
  const mermaidKeywords = [
    'graph', 'flowchart', 'sequenceDiagram', 'classDiagram',
    'stateDiagram', 'erDiagram', 'gantt', 'pie', 'mindmap',
    'timeline', 'quadrantChart', 'requirementDiagram', 'gitgraph',
    'xychart-beta', 'xychart'
  ]
  
  // 检查是否有图表类型关键字
  const hasKeyword = mermaidKeywords.some(kw => 
    trimmedCode.toLowerCase().startsWith(kw.toLowerCase()) ||
    trimmedCode.toLowerCase().includes(kw.toLowerCase() + '\n') ||
    trimmedCode.toLowerCase().includes(kw.toLowerCase() + ' ')
  )
  
  if (!hasKeyword) return false
  
  // 检查未闭合的括号
  const hasUnclosedBracket = 
    (trimmedCode.match(/\[/g)?.length !== trimmedCode.match(/\]/g)?.length) ||
    (trimmedCode.match(/\(/g)?.length !== trimmedCode.match(/\)/g)?.length) ||
    (trimmedCode.match(/{/g)?.length !== trimmedCode.match(/}/g)?.length)
  
  if (hasUnclosedBracket) return false
  
  // 检查未闭合的引号
  const singleQuotes = trimmedCode.match(/'/g)?.length || 0
  const doubleQuotes = trimmedCode.match(/"/g)?.length || 0
  if (singleQuotes % 2 !== 0 || doubleQuotes % 2 !== 0) return false
  
  // xychart 特殊处理
  if (trimmedCode.toLowerCase().startsWith('xychart')) {
    // xychart 需要有 bar[] 或 line[] 才算完整
    const hasBarOrLine = /\b(bar|line)\s*\[/.test(trimmedCode)
    if (!hasBarOrLine) return false
  }
  
  return true
}

/**
 * 生成图表的哈希值，用于判断代码是否真正变化
 */
function hashChart(code: string): string {
  // 简单哈希：提取关键字行
  const lines = code.trim().split('\n').filter(l => l.trim())
  return lines.slice(0, 10).join('|') // 取前10行作为标识
}

export default function MermaidRenderer({ chart, className }: MermaidRendererProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const [renderedSvg, setRenderedSvg] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  
  // 使用 ref 来跟踪渲染状态
  const renderCountRef = useRef(0)
  const lastRenderedHashRef = useRef<string>('')
  const isRenderedRef = useRef(false)

  useEffect(() => {
    // 提取 mermaid 代码
    const mermaidCode = extractMermaidCode(chart)
    
    // 如果已经渲染成功，且新的代码哈希没有变化，不重新渲染
    if (isRenderedRef.current) {
      const currentHash = hashChart(mermaidCode || chart)
      if (currentHash === lastRenderedHashRef.current) {
        return // 内容没有真正变化，保持当前渲染结果
      }
    }
    
    // 检查代码是否完整
    const codeToRender = mermaidCode || chart
    if (!isMermaidCodeComplete(codeToRender)) {
      // 代码不完整时
      if (!isRenderedRef.current && containerRef.current) {
        // 还没有成功渲染过，显示等待状态
        containerRef.current.innerHTML = `
          <div style="color: #94a3b8; text-align: center; padding: 20px;">
            <span style="animation: pulse 1.5s infinite;">正在生成图表...</span>
          </div>
          <style>
            @keyframes pulse {
              0%, 100% { opacity: 0.5; }
              50% { opacity: 1; }
            }
          </style>
        `
      }
      // 如果已经渲染成功，保持当前状态，不做任何改变
      return
    }

    // 延迟渲染，等待内容稳定
    const currentRenderId = ++renderCountRef.current
    
    const delayTimer = setTimeout(() => {
      // 检查是否是最新的渲染请求
      if (currentRenderId !== renderCountRef.current) return
      
      const renderChart = async () => {
        if (!containerRef.current) return
        
        setError(null)
        
        try {
          // Generate unique ID for this diagram
          const id = `mermaid-${Date.now().toString(36)}-${Math.random().toString(36).substring(2, 7)}`
          
          // Validate and render
          const { svg } = await mermaid.render(id, codeToRender)
          
          // 再次确认这是最新的渲染结果
          if (currentRenderId === renderCountRef.current) {
            setRenderedSvg(svg)
            isRenderedRef.current = true
            lastRenderedHashRef.current = hashChart(codeToRender)
            containerRef.current.innerHTML = svg
          }
        } catch (err) {
          console.error('Mermaid render error:', err)
          
          // 只在最新的渲染请求中处理错误
          if (currentRenderId === renderCountRef.current) {
            // 如果之前没有成功渲染，显示错误
            if (!isRenderedRef.current) {
              setError('图表解析失败')
              if (containerRef.current) {
                containerRef.current.innerHTML = `<pre style="color: #f87171; background: #1f2937; padding: 12px; border-radius: 8px; overflow-x: auto; white-space: pre-wrap;">${escapeHtml(codeToRender)}</pre>`
              }
            }
            // 如果之前已经渲染成功，保持当前状态，不显示错误
          }
        }
      }

      renderChart()
    }, 300) // 300ms 延迟，等待流式输出稳定
    
    return () => {
      clearTimeout(delayTimer)
    }
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

// HTML 转义函数
function escapeHtml(text: string): string {
  const div = document.createElement('div')
  div.textContent = text
  return div.innerHTML
}