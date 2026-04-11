import { useState, useEffect, useRef } from 'react'
import { Modal, Select, Input, Button, List, Tag, message, Spin } from 'antd'
import { PlayCircleOutlined, TeamOutlined } from '@ant-design/icons'
import { sessionsApi } from '../services/api'

const { TextArea } = Input

interface Agent {
  id: string
  name: string
  role: string
  description: string
}

interface Team {
  id: string
  name: string
  description: string
  agents: string[]
  workflow: string
}

interface AgentMessage {
  agent_id: string
  agent_name: string
  role: string
  content: string
  timestamp: string
}

interface TeamChatModalProps {
  open: boolean
  onClose: () => void
  onSessionCreated?: (sessionId: string) => void
}

export default function TeamChatModal({ open, onClose, onSessionCreated }: TeamChatModalProps) {
  const [teams, setTeams] = useState<Team[]>([])
  const [agents, setAgents] = useState<Agent[]>([])
  const [selectedTeam, setSelectedTeam] = useState<string>()
  const [task, setTask] = useState('')
  const [loading, setLoading] = useState(false)
  const [executing, setExecuting] = useState(false)
  const [messages, setMessages] = useState<AgentMessage[]>([])
  const [sessionId, setSessionId] = useState<string>()
  const wsRef = useRef<WebSocket | null>(null)

  useEffect(() => {
    if (open) {
      loadTeams()
      loadAgents()
    }
  }, [open])

  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close()
      }
    }
  }, [])

  const loadTeams = async () => {
    setLoading(true)
    try {
      const response = await fetch('/api/teams', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('auth-storage') ? 
            JSON.parse(localStorage.getItem('auth-storage')!).state?.token : ''}`
        }
      })
      const data = await response.json()
      setTeams(data.teams || [])
    } catch (error) {
      console.error('Failed to load teams:', error)
    } finally {
      setLoading(false)
    }
  }

  const loadAgents = async () => {
    try {
      const response = await fetch('/api/agents', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('auth-storage') ? 
            JSON.parse(localStorage.getItem('auth-storage')!).state?.token : ''}`
        }
      })
      const data = await response.json()
      setAgents(data.agents || [])
    } catch (error) {
      console.error('Failed to load agents:', error)
    }
  }

  const startTeamTask = async () => {
    if (!selectedTeam || !task.trim()) {
      message.warning('请选择团队并输入任务')
      return
    }

    setExecuting(true)
    setMessages([])

    try {
      const token = localStorage.getItem('auth-storage') ? 
        JSON.parse(localStorage.getItem('auth-storage')!).state?.token : ''

      // Create session
      const response = await fetch(`/api/teams/${selectedTeam}/run`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ task })
      })

      const data = await response.json()
      setSessionId(data.session_id)

      // Connect WebSocket
      const wsUrl = `ws://${window.location.host}/ws/team/${data.session_id}?token=${token}`
      const ws = new WebSocket(wsUrl)
      wsRef.current = ws

      ws.onmessage = (event) => {
        const msg = JSON.parse(event.data)
        
        if (msg.type === 'agent_message') {
          setMessages(prev => [...prev, {
            agent_id: msg.agent_id,
            agent_name: msg.agent_name,
            role: msg.role,
            content: msg.content,
            timestamp: msg.timestamp
          }])
        } else if (msg.type === 'session_complete') {
          setExecuting(false)
          message.success('团队任务完成')
          if (onSessionCreated) {
            onSessionCreated(data.session_id)
          }
        } else if (msg.type === 'error') {
          message.error(msg.message)
          setExecuting(false)
        }
      }

      ws.onerror = (error) => {
        console.error('WebSocket error:', error)
        message.error('连接失败')
        setExecuting(false)
      }

    } catch (error) {
      console.error('Failed to start team task:', error)
      message.error('启动失败')
      setExecuting(false)
    }
  }

  const getAgentColor = (role: string) => {
    const colors: Record<string, string> = {
      planner: 'blue',
      executor: 'green',
      reviewer: 'orange',
      analyst: 'purple',
      developer: 'cyan',
      tester: 'magenta',
      custom: 'default'
    }
    return colors[role] || 'default'
  }

  const selectedTeamInfo = teams.find(t => t.id === selectedTeam)

  return (
    <Modal
      title={
        <span>
          <TeamOutlined style={{ marginRight: 8 }} />
          多智能体协作
        </span>
      }
      open={open}
      onCancel={() => {
        if (wsRef.current) {
          wsRef.current.close()
        }
        onClose()
      }}
      width={800}
      footer={null}
    >
      <div style={{ marginBottom: 16 }}>
        <div style={{ marginBottom: 8 }}>
          <label style={{ fontWeight: 500 }}>选择团队：</label>
        </div>
        <Select
          style={{ width: '100%' }}
          placeholder="选择一个团队"
          value={selectedTeam}
          onChange={setSelectedTeam}
          loading={loading}
          options={teams.map(t => ({
            label: `${t.name} (${t.agents.length} 个智能体)`,
            value: t.id
          }))}
        />
        {selectedTeamInfo && (
          <div style={{ marginTop: 8, color: '#666' }}>
            {selectedTeamInfo.description}
            <div style={{ marginTop: 4 }}>
              包含智能体：{selectedTeamInfo.agents.map(aid => {
                const agent = agents.find(a => a.id === aid)
                return agent ? (
                  <Tag key={aid} color={getAgentColor(agent.role)}>
                    {agent.name}
                  </Tag>
                ) : null
              })}
            </div>
          </div>
        )}
      </div>

      <div style={{ marginBottom: 16 }}>
        <div style={{ marginBottom: 8 }}>
          <label style={{ fontWeight: 500 }}>任务描述：</label>
        </div>
        <TextArea
          rows={4}
          placeholder="输入要让团队完成的任务..."
          value={task}
          onChange={(e) => setTask(e.target.value)}
        />
      </div>

      <Button
        type="primary"
        icon={<PlayCircleOutlined />}
        onClick={startTeamTask}
        loading={executing}
        disabled={!selectedTeam || !task.trim()}
        style={{ marginBottom: 16 }}
      >
        开始协作
      </Button>

      {messages.length > 0 && (
        <div style={{ 
          border: '1px solid #f0f0f0', 
          borderRadius: 8, 
          padding: 16,
          maxHeight: 400,
          overflowY: 'auto'
        }}>
          <div style={{ fontWeight: 500, marginBottom: 12 }}>
            协作过程
          </div>
          <List
            dataSource={messages}
            renderItem={(msg) => (
              <List.Item style={{ border: 'none', padding: '8px 0' }}>
                <div style={{ width: '100%' }}>
                  <div style={{ marginBottom: 4 }}>
                    <Tag color={getAgentColor(msg.role)}>
                      {msg.agent_name}
                    </Tag>
                    <span style={{ fontSize: 12, color: '#999', marginLeft: 8 }}>
                      {new Date(msg.timestamp).toLocaleTimeString()}
                    </span>
                  </div>
                  <div style={{ 
                    whiteSpace: 'pre-wrap',
                    background: '#fafafa',
                    padding: 8,
                    borderRadius: 4
                  }}>
                    {msg.content}
                  </div>
                </div>
              </List.Item>
            )}
          />
          {executing && (
            <div style={{ textAlign: 'center', padding: 16 }}>
              <Spin tip="智能体正在协作中..." />
            </div>
          )}
        </div>
      )}
    </Modal>
  )
}