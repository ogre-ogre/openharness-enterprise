import { useState, useEffect } from 'react'
import { Table, Button, Modal, Form, Input, Select, message, Space, Tag, Popconfirm, Checkbox } from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons'
import { useAuthStore } from '../../stores/auth'

interface Agent {
  id: string
  name: string
  role: string
}

interface Team {
  id: string
  name: string
  description: string
  agents: string[]
  workflow: string
  is_active: boolean
}

const workflowOptions = [
  { label: '顺序执行', value: 'sequential' },
  { label: '并行执行', value: 'parallel' },
]

export default function TeamManage() {
  const [teams, setTeams] = useState<Team[]>([])
  const [agents, setAgents] = useState<Agent[]>([])
  const [loading, setLoading] = useState(false)
  const [modalOpen, setModalOpen] = useState(false)
  const [editingTeam, setEditingTeam] = useState<Team | null>(null)
  const [form] = Form.useForm()
  const [selectedAgents, setSelectedAgents] = useState<string[]>([])
  
  const { token } = useAuthStore()

  useEffect(() => {
    loadTeams()
    loadAgents()
  }, [])

  const loadTeams = async () => {
    setLoading(true)
    try {
      const response = await fetch('/api/teams', {
        headers: { Authorization: `Bearer ${token}` }
      })
      const data = await response.json()
      setTeams(data.teams || [])
    } catch (error) {
      message.error('加载失败')
    } finally {
      setLoading(false)
    }
  }

  const loadAgents = async () => {
    try {
      const response = await fetch('/api/agents', {
        headers: { Authorization: `Bearer ${token}` }
      })
      const data = await response.json()
      setAgents(data.agents || [])
    } catch (error) {
      console.error('Failed to load agents:', error)
    }
  }

  const handleCreate = () => {
    setEditingTeam(null)
    form.resetFields()
    form.setFieldsValue({
      workflow: 'sequential'
    })
    setSelectedAgents([])
    setModalOpen(true)
  }

  const handleEdit = (team: Team) => {
    setEditingTeam(team)
    form.setFieldsValue(team)
    setSelectedAgents(team.agents || [])
    setModalOpen(true)
  }

  const handleDelete = async (teamId: string) => {
    try {
      const response = await fetch(`/api/teams/${teamId}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` }
      })
      if (response.ok) {
        message.success('删除成功')
        loadTeams()
      } else {
        message.error('删除失败')
      }
    } catch (error) {
      message.error('删除失败')
    }
  }

  const handleSubmit = async (values: any) => {
    try {
      const data = {
        ...values,
        agents: selectedAgents
      }

      if (editingTeam) {
        const response = await fetch(`/api/teams/${editingTeam.id}`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`
          },
          body: JSON.stringify(data)
        })
        if (response.ok) {
          message.success('更新成功')
          loadTeams()
        } else {
          message.error('更新失败')
        }
      } else {
        const response = await fetch('/api/teams', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`
          },
          body: JSON.stringify(data)
        })
        if (response.ok) {
          message.success('创建成功')
          loadTeams()
        } else {
          const respData = await response.json()
          message.error(respData.detail || '创建失败')
        }
      }
      setModalOpen(false)
    } catch (error) {
      message.error('操作失败')
    }
  }

  const toggleAgent = (agentId: string) => {
    setSelectedAgents(prev => {
      if (prev.includes(agentId)) {
        return prev.filter(id => id !== agentId)
      } else {
        return [...prev, agentId]
      }
    })
  }

  const moveAgentUp = (index: number) => {
    if (index === 0) return
    setSelectedAgents(prev => {
      const newList = [...prev]
      ;[newList[index - 1], newList[index]] = [newList[index], newList[index - 1]]
      return newList
    })
  }

  const moveAgentDown = (index: number) => {
    if (index === selectedAgents.length - 1) return
    setSelectedAgents(prev => {
      const newList = [...prev]
      ;[newList[index], newList[index + 1]] = [newList[index + 1], newList[index]]
      return newList
    })
  }

  const getWorkflowTag = (workflow: string) => {
    const labels: Record<string, string> = {
      sequential: '顺序执行',
      parallel: '并行执行'
    }
    const colors: Record<string, string> = {
      sequential: 'blue',
      parallel: 'green'
    }
    return <Tag color={colors[workflow] || 'default'}>{labels[workflow] || workflow}</Tag>
  }

  const getAgentName = (agentId: string) => {
    const agent = agents.find(a => a.id === agentId)
    return agent ? agent.name : agentId
  }

  const columns = [
    {
      title: 'ID',
      dataIndex: 'id',
      width: 120,
    },
    {
      title: '团队名称',
      dataIndex: 'name',
      width: 150,
    },
    {
      title: '描述',
      dataIndex: 'description',
      ellipsis: true,
    },
    {
      title: '包含 Agent',
      dataIndex: 'agents',
      width: 250,
      render: (agentIds: string[]) => (
        <Space size={[0, 4]} wrap>
          {agentIds.map(id => (
            <Tag key={id}>{getAgentName(id)}</Tag>
          ))}
        </Space>
      ),
    },
    {
      title: '工作流',
      dataIndex: 'workflow',
      width: 100,
      render: (workflow: string) => getWorkflowTag(workflow),
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      width: 80,
      render: (active: boolean) => (
        <Tag color={active ? 'green' : 'red'}>{active ? '启用' : '禁用'}</Tag>
      ),
    },
    {
      title: '操作',
      width: 150,
      render: (_: any, record: Team) => (
        <Space>
          <Button
            size="small"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
          >
            编辑
          </Button>
          <Popconfirm
            title="确定删除此团队？"
            onConfirm={() => handleDelete(record.id)}
          >
            <Button size="small" danger icon={<DeleteOutlined />}>
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  return (
    <div>
      <div style={{ marginBottom: 16 }}>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
          创建团队
        </Button>
      </div>

      <Table
        columns={columns}
        dataSource={teams}
        rowKey="id"
        loading={loading}
        pagination={false}
      />

      <Modal
        title={editingTeam ? `编辑团队: ${editingTeam.name}` : '创建团队'}
        open={modalOpen}
        onCancel={() => setModalOpen(false)}
        onOk={() => form.submit()}
        width={700}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
        >
          <Form.Item
            name="id"
            label="ID"
            rules={[{ required: true, message: '请输入 ID' }]}
          >
            <Input disabled={!!editingTeam} placeholder="唯一标识符，如 my-team" />
          </Form.Item>
          
          <Form.Item
            name="name"
            label="团队名称"
            rules={[{ required: true, message: '请输入名称' }]}
          >
            <Input placeholder="团队显示名称" />
          </Form.Item>

          <Form.Item name="description" label="描述">
            <Input.TextArea rows={2} placeholder="团队功能描述" />
          </Form.Item>

          <Form.Item label="选择 Agent">
            <div style={{ display: 'flex', gap: 16 }}>
              {/* 可选 Agent 列表 */}
              <div style={{ flex: 1, border: '1px solid #d9d9d9', borderRadius: 4, padding: 8, maxHeight: 250, overflowY: 'auto' }}>
                <div style={{ fontWeight: 500, marginBottom: 8, color: '#666' }}>可选 Agent</div>
                {agents.map(agent => (
                  <div
                    key={agent.id}
                    onClick={() => !selectedAgents.includes(agent.id) && toggleAgent(agent.id)}
                    style={{
                      padding: '4px 8px',
                      cursor: selectedAgents.includes(agent.id) ? 'not-allowed' : 'pointer',
                      background: selectedAgents.includes(agent.id) ? '#f5f5f5' : '#fff',
                      borderRadius: 4,
                      marginBottom: 4,
                      opacity: selectedAgents.includes(agent.id) ? 0.5 : 1
                    }}
                  >
                    <Tag>{agent.name}</Tag>
                  </div>
                ))}
              </div>

              {/* 已选 Agent 列表 */}
              <div style={{ flex: 1, border: '1px solid #1890ff', borderRadius: 4, padding: 8, maxHeight: 250, overflowY: 'auto' }}>
                <div style={{ fontWeight: 500, marginBottom: 8, color: '#1890ff' }}>已选 Agent（按执行顺序）</div>
                {selectedAgents.length === 0 ? (
                  <div style={{ color: '#999', textAlign: 'center', padding: 16 }}>
                    点击左侧 Agent 添加
                  </div>
                ) : (
                  selectedAgents.map((agentId, index) => (
                    <div
                      key={agentId}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        padding: '4px 8px',
                        background: '#e6f7ff',
                        borderRadius: 4,
                        marginBottom: 4
                      }}
                    >
                      <span>
                        <Tag color="blue">{index + 1}</Tag>
                        {getAgentName(agentId)}
                      </span>
                      <Space size="small">
                        <Button
                          size="small"
                          onClick={() => moveAgentUp(index)}
                          disabled={index === 0}
                        >
                          ↑
                        </Button>
                        <Button
                          size="small"
                          onClick={() => moveAgentDown(index)}
                          disabled={index === selectedAgents.length - 1}
                        >
                          ↓
                        </Button>
                        <Button
                          size="small"
                          danger
                          onClick={() => toggleAgent(agentId)}
                        >
                          ×
                        </Button>
                      </Space>
                    </div>
                  ))
                )}
              </div>
            </div>
          </Form.Item>

          <Form.Item name="workflow" label="工作流模式">
            <Select options={workflowOptions} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}