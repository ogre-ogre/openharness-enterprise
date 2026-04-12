import { useState, useEffect, useRef, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { Layout, Button, Input, List, Tag, Dropdown, Space, message, Avatar, Popconfirm, Upload } from 'antd'
import { SendOutlined, LogoutOutlined, PlusOutlined, UserOutlined, TeamOutlined, CloseOutlined, RobotOutlined, UploadOutlined } from '@ant-design/icons'
import type { MenuProps, UploadFile } from 'antd'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import CodeBlock from '../components/CodeBlock'
import { useAuthStore } from '../stores/auth'
import { chatWebSocket, ServerMessage } from '../services/websocket'
import { sessionsApi } from '../services/api'
import TeamChatModal from '../components/TeamChatModal'
import './Chat.css'

const { TextArea } = Input
const { Sider, Content, Header } = Layout

interface ChatMessage {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: string
}

interface SessionInfo {
  id: string
  title: string | null
  message_count: number
  created_at: string
  updated_at: string | null
}

// Store messages per session
interface SessionMessages {
  [sessionId: string]: ChatMessage[]
}

export default function Chat() {
  const [sessionMessages, setSessionMessages] = useState<SessionMessages>({})
  const [inputValue, setInputValue] = useState('')
  const [sessions, setSessions] = useState<SessionInfo[]>([])
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null)
  const [isThinking, setIsThinking] = useState(false)
  const [currentResponse, setCurrentResponse] = useState('')
  const [wsConnected, setWsConnected] = useState(false)
  const [teamModalOpen, setTeamModalOpen] = useState(false)
  const [uploadedFiles, setUploadedFiles] = useState<UploadFile[]>([])
  const [uploading, setUploading] = useState(false)
  
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const currentResponseRef = useRef<string>('')
  const currentSessionIdRef = useRef<string | null>(null)
  const isConnectedRef = useRef(false)
  const navigate = useNavigate()
  const { user, logout, token } = useAuthStore()
  
  // Keep refs in sync with state
  useEffect(() => {
    currentResponseRef.current = currentResponse
  }, [currentResponse])
  
  useEffect(() => {
    currentSessionIdRef.current = currentSessionId
  }, [currentSessionId])
  
  // Get current session's messages
  const messages = currentSessionId ? (sessionMessages[currentSessionId] || []) : []

  // Load sessions on mount
  useEffect(() => {
    loadSessions()
  }, [])

  // Connect WebSocket once
  useEffect(() => {
    if (!isConnectedRef.current) {
      isConnectedRef.current = true
      connectWebSocket()
    }
    
    return () => {
      chatWebSocket.disconnect()
      isConnectedRef.current = false
    }
  }, [])

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, currentResponse])

  const loadSessions = async () => {
    try {
      const response = await sessionsApi.list()
      setSessions(response.data.sessions || [])
    } catch (error) {
      console.error('Failed to load sessions:', error)
    }
  }

  const connectWebSocket = (sessionId?: string) => {
    chatWebSocket.disconnect()
    
    chatWebSocket.connect(sessionId).then(() => {
      setWsConnected(true)
      console.log('WebSocket connected')
    }).catch(err => {
      console.error('WebSocket connection error:', err)
      setWsConnected(false)
    })
    
    // Register message handler
    chatWebSocket.onMessage((msg: ServerMessage) => {
      handleMessage(msg)
    })
  }

  const loadSessionMessages = async (sessionId: string) => {
    try {
      const response = await sessionsApi.getMessages(sessionId)
      const msgs = response.data.messages || []
      
      setSessionMessages(prev => ({
        ...prev,
        [sessionId]: msgs.map((m: any) => ({
          id: m.id,
          role: m.role,
          content: m.content,
          timestamp: m.created_at
        }))
      }))
    } catch (error) {
      console.error('Failed to load messages:', error)
    }
  }

  const handleMessage = (message: ServerMessage) => {
    console.log('Received message:', message)
    
    const sessionId = currentSessionIdRef.current
    
    switch (message.type) {
      case 'session_info':
        setCurrentSessionId(message.payload.session_id)
        loadSessions()
        break
      
      case 'session_history':
        if (message.payload.messages && sessionId) {
          setSessionMessages(prev => ({
            ...prev,
            [sessionId]: message.payload.messages.map((m: any) => ({
              id: m.id,
              role: m.role,
              content: m.content,
              timestamp: m.created_at
            }))
          }))
        }
        break
      
      case 'text':
        if (message.payload.delta) {
          setCurrentResponse(prev => prev + message.payload.content)
        }
        break
      
      case 'thinking':
        setIsThinking(true)
        break
      
      case 'done':
        setIsThinking(false)
        const finalResponse = currentResponseRef.current
        console.log('Done, final response:', finalResponse, 'sessionId:', sessionId)
        if (finalResponse && sessionId) {
          setSessionMessages(prev => ({
            ...prev,
            [sessionId]: [
              ...(prev[sessionId] || []),
              {
                id: Date.now().toString(),
                role: 'assistant' as const,
                content: finalResponse,
                timestamp: new Date().toISOString()
              }
            ]
          }))
          setCurrentResponse('')
          currentResponseRef.current = ''
          loadSessions()
        }
        break
      
      case 'error':
        setIsThinking(false)
        message.error(message.payload.message)
        break
    }
  }

  const sendMessage = () => {
    if (!inputValue.trim() || isThinking || !currentSessionId) return

    const content = inputValue.trim()
    console.log('Sending message:', content)
    
    // Add user message to current session immediately
    setSessionMessages(prev => ({
      ...prev,
      [currentSessionId]: [
        ...(prev[currentSessionId] || []),
        {
          id: Date.now().toString(),
          role: 'user' as const,
          content,
          timestamp: new Date().toISOString()
        }
      ]
    }))

    // Send to server
    chatWebSocket.sendMessage(content)
    
    setInputValue('')
  }

  // File upload handler
  const handleFileUpload = async (file: File): Promise<boolean> => {
    const allowedTypes = ['.txt', '.md', '.png', '.jpg', '.jpeg', '.docx', '.xlsx', '.csv']
    const ext = '.' + file.name.split('.').pop()?.toLowerCase()
    
    if (!allowedTypes.includes(ext)) {
      message.error(`不支持的文件类型: ${ext}`)
      return false
    }
    
    if (file.size > 10 * 1024 * 1024) {
      message.error('文件大小不能超过 10MB')
      return false
    }
    
    setUploading(true)
    
    try {
      const formData = new FormData()
      formData.append('file', file)
      
      const response = await fetch('/api/upload', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      })
      
      if (response.ok) {
        const data = await response.json()
        message.success(`文件上传成功: ${file.name}`)
        return true
      } else {
        message.error('上传失败')
        return false
      }
    } catch (error) {
      message.error('上传失败')
      return false
    } finally {
      setUploading(false)
    }
  }

  const handleRemoveFile = (file: UploadFile) => {
    setUploadedFiles(prev => prev.filter(f => f.uid !== file.uid))
  }

  const handleNewSession = () => {
    setCurrentSessionId(null)
    setCurrentResponse('')
    setIsThinking(false)
    currentSessionIdRef.current = null
    connectWebSocket()
  }

  const handleDeleteSession = async (sessionId: string, e: React.MouseEvent) => {
    e.stopPropagation()
    
    try {
      await sessionsApi.delete(sessionId)
      
      setSessions(prev => prev.filter(s => s.id !== sessionId))
      setSessionMessages(prev => {
        const newState = { ...prev }
        delete newState[sessionId]
        return newState
      })
      
      if (sessionId === currentSessionId) {
        const remaining = sessions.filter(s => s.id !== sessionId)
        if (remaining.length > 0) {
          handleSelectSession(remaining[0].id)
        } else {
          handleNewSession()
        }
      }
      
      message.success('会话已删除')
    } catch (error) {
      message.error('删除失败')
    }
  }

  const handleSelectSession = async (sessionId: string) => {
    if (sessionId === currentSessionId) return
    
    if (currentResponse && currentSessionId) {
      setSessionMessages(prev => ({
        ...prev,
        [currentSessionId]: [
          ...(prev[currentSessionId] || []),
          {
            id: Date.now().toString(),
            role: 'assistant' as const,
            content: currentResponse,
            timestamp: new Date().toISOString()
          }
        ]
      }))
      setCurrentResponse('')
    }
    
    setCurrentSessionId(sessionId)
    currentSessionIdRef.current = sessionId
    setIsThinking(false)
    
    await loadSessionMessages(sessionId)
    connectWebSocket(sessionId)
  }

  const handleLogout = () => {
    logout()
    chatWebSocket.disconnect()
    navigate('/login')
  }

  const userMenuItems: MenuProps['items'] = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: user?.display_name || user?.username,
    },
    { type: 'divider' },
  ]

  // 所有用户都能访问管理后台（普通用户只能看到技能管理）
  const adminLabel = user?.role === 'admin' ? '管理后台' : '技能管理'
  userMenuItems.splice(2, 0, {
    key: 'admin',
    icon: <TeamOutlined />,
    label: adminLabel,
    onClick: () => navigate('/admin'),
  })

  userMenuItems.push({
    key: 'logout',
    icon: <LogoutOutlined />,
    label: '退出登录',
    onClick: handleLogout,
  })

  return (
    <Layout style={{ height: '100vh' }}>
      <Sider width={280} theme="light" style={{ borderRight: '1px solid #f0f0f0' }}>
        <div style={{ padding: 16 }}>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            block
            onClick={handleNewSession}
          >
            新建会话
          </Button>
        </div>
        
        <List
          dataSource={sessions}
          style={{ padding: '0 8px' }}
          renderItem={(session) => (
            <List.Item
              onClick={() => handleSelectSession(session.id)}
              style={{
                cursor: 'pointer',
                borderRadius: 8,
                padding: '12px 16px',
                marginBottom: 4,
                backgroundColor: session.id === currentSessionId ? '#e6f4ff' : 'transparent',
                position: 'relative'
              }}
            >
              <div style={{ overflow: 'hidden', width: '100%', paddingRight: 24 }}>
                <div style={{ fontWeight: 500, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {session.title || '新会话'}
                </div>
                <div style={{ fontSize: 12, color: '#999' }}>
                  {session.message_count} 条消息
                </div>
              </div>
              <Popconfirm
                title="确定删除此会话？"
                onConfirm={(e) => handleDeleteSession(session.id, e as any)}
                onCancel={(e) => e?.stopPropagation()}
                okText="删除"
                cancelText="取消"
              >
                <Button
                  type="text"
                  size="small"
                  icon={<CloseOutlined />}
                  onClick={(e) => e.stopPropagation()}
                  style={{
                    position: 'absolute',
                    right: 8,
                    top: '50%',
                    transform: 'translateY(-50%)',
                    opacity: 0.5
                  }}
                  onMouseEnter={(e) => e.currentTarget.style.opacity = '1'}
                  onMouseLeave={(e) => e.currentTarget.style.opacity = '0.5'}
                />
              </Popconfirm>
            </List.Item>
          )}
        />
      </Sider>

      <Layout>
        <Header style={{
          background: '#fff',
          padding: '0 24px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          borderBottom: '1px solid #f0f0f0'
        }}>
          <div style={{ fontSize: 18, fontWeight: 600 }}>
            zzchatops 真小维
            {!wsConnected && <Tag color="warning" style={{ marginLeft: 8 }}>连接中...</Tag>}
          </div>
          
          <Space>
            <Button
              icon={<RobotOutlined />}
              onClick={() => setTeamModalOpen(true)}
            >
              多智能体
            </Button>
            <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
              <Space style={{ cursor: 'pointer' }}>
                <Avatar icon={<UserOutlined />} />
                <span>{user?.display_name || user?.username}</span>
              </Space>
            </Dropdown>
          </Space>
        </Header>

        <Content style={{ display: 'flex', flexDirection: 'column' }}>
          <div className="chat-messages">
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`chat-message ${msg.role}`}
              >
                <div className="message-role">
                  {msg.role === 'user' ? '你' : 'AI'}
                </div>
                <div className="message-content">
                  {msg.role === 'assistant' ? (
                    <ReactMarkdown 
                      remarkPlugins={[remarkGfm]}
                      components={{
                        code: CodeBlock as any
                      }}
                    >
                      {msg.content}
                    </ReactMarkdown>
                  ) : (
                    <div style={{ whiteSpace: 'pre-wrap' }}>{msg.content}</div>
                  )}
                </div>
              </div>
            ))}
            
            {isThinking && currentResponse && (
              <div className="chat-message assistant">
                <div className="message-role">AI</div>
                <div className="message-content">
                  <ReactMarkdown 
                    remarkPlugins={[remarkGfm]}
                    components={{
                      code: CodeBlock as any
                    }}
                  >
                    {currentResponse}
                  </ReactMarkdown>
                </div>
              </div>
            )}
            
            {isThinking && !currentResponse && (
              <div className="chat-message assistant">
                <div className="message-role">AI</div>
                <div className="message-content">
                  <Tag color="processing">正在思考...</Tag>
                </div>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>

          {/* Input Area */}
          <div className="chat-input-area">
            {/* Uploaded files preview */}
            {uploadedFiles.length > 0 && (
              <div style={{ marginBottom: 8, display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                {uploadedFiles.map(file => (
                  <Tag 
                    key={file.uid}
                    closable
                    onClose={() => handleRemoveFile(file)}
                    style={{ padding: '4px 8px', background: '#f0f0f0' }}
                  >
                    {file.name}
                  </Tag>
                ))}
              </div>
            )}
            
            <div style={{ display: 'flex', gap: 8, alignItems: 'flex-end' }}>
              {/* File upload button */}
              <Upload
                accept=".txt,.md,.png,.jpg,.jpeg,.docx,.xlsx,.csv"
                beforeUpload={(file) => {
                  handleFileUpload(file)
                  return false
                }}
                showUploadList={false}
                disabled={isThinking || !currentSessionId}
              >
                <Button
                  icon={<UploadOutlined />}
                  disabled={isThinking || !currentSessionId || uploading}
                  loading={uploading}
                >
                  文件上传
                </Button>
              </Upload>
              
              <TextArea
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onPressEnter={(e) => {
                  if (!e.shiftKey) {
                    e.preventDefault()
                    sendMessage()
                  }
                }}
                placeholder="输入消息... (Shift+Enter 换行)"
                autoSize={{ minRows: 1, maxRows: 4 }}
                disabled={isThinking || !currentSessionId}
                style={{ flex: 1 }}
              />
              <Button
                type="primary"
                icon={<SendOutlined />}
                onClick={sendMessage}
                loading={isThinking}
                disabled={!currentSessionId}
              >
                发送
              </Button>
            </div>
          </div>
        </Content>
      </Layout>
      
      {/* Multi-Agent Team Modal */}
      <TeamChatModal
        open={teamModalOpen}
        onClose={() => setTeamModalOpen(false)}
      />
    </Layout>
  )
}