import { useState, useEffect } from 'react'
import { Table, Button, Modal, Form, Input, Select, message, Space, Popconfirm, Tag } from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons'
import { useAuthStore } from '../../stores/auth'

const { TextArea } = Input

interface Agent {
  id: string
  name: string
  role: string
  description: string
  system_prompt: string
  model: string
  temperature: number
  is_active: boolean
}

const roleOptions = [
  { label: '方案制定', value: 'planner' },
  { label: '执行者', value: 'executor' },
  { label: '审查者', value: 'reviewer' },
  { label: '分析师', value: 'analyst' },
  { label: '开发者', value: 'developer' },
  { label: '测试员', value: 'tester' },
  { label: '自定义', value: 'custom' },
]

export default function AgentManage() {
  const [agents, setAgents] = useState<Agent[]>([])
  const [loading, setLoading] = useState(false)
  const [modalOpen, setModalOpen] = useState(false)
  const [editingAgent, setEditingAgent] = useState<Agent | null>(null)
  const [form] = Form.useForm()
  
  const { token } = useAuthStore()

  useEffect(() => {
    loadAgents()
  }, [])

  const loadAgents = async () => {
    setLoading(true)
    try {
      const response = await fetch('/api/agents', {
        headers: { Authorization: `Bearer ${token}` }
      })
      const data = await response.json()
      setAgents(data.agents || [])
    } catch (error) {
      message.error('加载失败')
    } finally {
      setLoading(false)
    }
  }

  const handleCreate = () => {
    setEditingAgent(null)
    form.resetFields()
    form.setFieldsValue({
      model: 'glm-5',
      temperature: 0.7,
      role: 'custom'
    })
    setModalOpen(true)
  }

  const handleEdit = (agent: Agent) => {
    setEditingAgent(agent)
    form.setFieldsValue(agent)
    setModalOpen(true)
  }

  const handleSubmit = async (values: any) => {
    try {
      if (editingAgent) {
        // 更新
        const response = await fetch(`/api/agents/${editingAgent.id}`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`
          },
          body: JSON.stringify(values)
        })
        if (response.ok) {
          message.success('更新成功')
          loadAgents()
        } else {
          message.error('更新失败')
        }
      } else {
        // 创建
        const response = await fetch('/api/agents', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`
          },
          body: JSON.stringify(values)
        })
        if (response.ok) {
          message.success('创建成功')
          loadAgents()
        } else {
          const data = await response.json()
          message.error(data.detail || '创建失败')
        }
      }
      setModalOpen(false)
    } catch (error) {
      message.error('操作失败')
    }
  }

  const getRoleTag = (role: string) => {
    const colors: Record<string, string> = {
      planner: 'blue',
      executor: 'green',
      reviewer: 'orange',
      analyst: 'purple',
      developer: 'cyan',
      tester: 'magenta',
      custom: 'default'
    }
    const labels: Record<string, string> = {
      planner: '方案制定',
      executor: '执行者',
      reviewer: '审查者',
      analyst: '分析师',
      developer: '开发者',
      tester: '测试员',
      custom: '自定义'
    }
    return <Tag color={colors[role] || 'default'}>{labels[role] || role}</Tag>
  }

  const columns = [
    {
      title: 'ID',
      dataIndex: 'id',
      width: 120,
    },
    {
      title: '名称',
      dataIndex: 'name',
      width: 150,
    },
    {
      title: '角色',
      dataIndex: 'role',
      width: 100,
      render: (role: string) => getRoleTag(role),
    },
    {
      title: '描述',
      dataIndex: 'description',
      ellipsis: true,
    },
    {
      title: '模型',
      dataIndex: 'model',
      width: 100,
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
      width: 120,
      render: (_: any, record: Agent) => (
        <Space>
          <Button
            size="small"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
          >
            编辑
          </Button>
        </Space>
      ),
    },
  ]

  return (
    <div>
      <div style={{ marginBottom: 16 }}>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
          创建 Agent
        </Button>
      </div>

      <Table
        columns={columns}
        dataSource={agents}
        rowKey="id"
        loading={loading}
        pagination={false}
      />

      <Modal
        title={editingAgent ? `编辑 Agent: ${editingAgent.name}` : '创建 Agent'}
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
            <Input disabled={!!editingAgent} placeholder="唯一标识符，如 my-agent" />
          </Form.Item>
          
          <Form.Item
            name="name"
            label="名称"
            rules={[{ required: true, message: '请输入名称' }]}
          >
            <Input placeholder="Agent 显示名称" />
          </Form.Item>

          <Form.Item name="role" label="角色类型">
            <Select options={roleOptions} />
          </Form.Item>

          <Form.Item name="description" label="描述">
            <Input.TextArea rows={2} placeholder="Agent 功能描述" />
          </Form.Item>

          <Form.Item
            name="system_prompt"
            label="系统提示词"
            rules={[{ required: true, message: '请输入系统提示词' }]}
          >
            <TextArea
              rows={8}
              placeholder="定义 Agent 的行为、职责和工作方式..."
            />
          </Form.Item>

          <Form.Item name="model" label="模型">
            <Select>
              <Select.Option value="glm-5">GLM-5</Select.Option>
              <Select.Option value="glm-4">GLM-4</Select.Option>
              <Select.Option value="deepseek-chat">DeepSeek</Select.Option>
            </Select>
          </Form.Item>

          <Form.Item name="temperature" label="温度">
            <Select>
              <Select.Option value={0.3}>0.3 (严谨)</Select.Option>
              <Select.Option value={0.5}>0.5 (平衡)</Select.Option>
              <Select.Option value={0.7}>0.7 (默认)</Select.Option>
              <Select.Option value={0.9}>0.9 (创意)</Select.Option>
            </Select>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}