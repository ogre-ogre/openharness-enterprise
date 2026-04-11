import { useState, useEffect } from 'react'
import { Table, Button, Modal, Form, Input, Select, message, Space, Tag, Switch, Popconfirm, Alert } from 'antd'
import { PlayCircleOutlined, WarningOutlined } from '@ant-design/icons'
import { useAuthStore } from '../../stores/auth'

interface ToolParameter {
  type: string
  description: string
  required: boolean
  default?: any
}

interface Tool {
  name: string
  description: string
  category: string
  permission: string
  is_dangerous: boolean
  is_enabled: boolean
  parameters: Record<string, ToolParameter>
}

export default function ToolManage() {
  const [tools, setTools] = useState<Tool[]>([])
  const [loading, setLoading] = useState(false)
  const [executeModalOpen, setExecuteModalOpen] = useState(false)
  const [selectedTool, setSelectedTool] = useState<Tool | null>(null)
  const [executeForm] = Form.useForm()
  const [executeResult, setExecuteResult] = useState<any>(null)
  
  const { token } = useAuthStore()

  useEffect(() => {
    loadTools()
  }, [])

  const loadTools = async () => {
    setLoading(true)
    try {
      const response = await fetch('/api/tools', {
        headers: { Authorization: `Bearer ${token}` }
      })
      const data = await response.json()
      setTools(data.tools || [])
    } catch (error) {
      message.error('加载失败')
    } finally {
      setLoading(false)
    }
  }

  const handleToggleEnabled = async (toolName: string, enabled: boolean) => {
    try {
      const response = await fetch(`/api/tools/${toolName}/enabled?enabled=${enabled}`, {
        method: 'PUT',
        headers: { Authorization: `Bearer ${token}` }
      })
      
      if (response.ok) {
        message.success(enabled ? '已启用' : '已禁用')
        loadTools()
      } else {
        message.error('操作失败')
      }
    } catch (error) {
      message.error('操作失败')
    }
  }

  const handleExecute = (tool: Tool) => {
    setSelectedTool(tool)
    setExecuteResult(null)
    executeForm.resetFields()
    
    // Set default values
    const defaultValues: Record<string, any> = {}
    Object.entries(tool.parameters).forEach(([key, param]) => {
      if (param.default !== undefined && param.default !== null) {
        defaultValues[key] = param.default
      }
    })
    executeForm.setFieldsValue(defaultValues)
    
    setExecuteModalOpen(true)
  }

  const handleExecuteSubmit = async (values: any) => {
    if (!selectedTool) return
    
    try {
      const response = await fetch(`/api/tools/${selectedTool.name}/execute`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({ parameters: values })
      })
      
      const data = await response.json()
      setExecuteResult(data)
      
      if (data.success) {
        message.success('执行成功')
      } else {
        message.error(data.error || '执行失败')
      }
    } catch (error) {
      message.error('执行失败')
    }
  }

  const getCategoryTag = (category: string) => {
    const colors: Record<string, string> = {
      file: 'blue',
      web: 'green',
      system: 'orange',
      database: 'purple',
      custom: 'cyan'
    }
    const labels: Record<string, string> = {
      file: '文件',
      web: '网络',
      system: '系统',
      database: '数据库',
      custom: '自定义'
    }
    return <Tag color={colors[category] || 'default'}>{labels[category] || category}</Tag>
  }

  const getPermissionTag = (permission: string) => {
    const colors: Record<string, string> = {
      read: 'green',
      write: 'orange',
      execute: 'red',
      admin: 'purple'
    }
    return <Tag color={colors[permission] || 'default'}>{permission}</Tag>
  }

  const columns = [
    {
      title: '工具名称',
      dataIndex: 'name',
      width: 150,
    },
    {
      title: '描述',
      dataIndex: 'description',
      ellipsis: true,
    },
    {
      title: '类别',
      dataIndex: 'category',
      width: 80,
      render: (category: string) => getCategoryTag(category),
    },
    {
      title: '权限',
      dataIndex: 'permission',
      width: 80,
      render: (permission: string) => getPermissionTag(permission),
    },
    {
      title: '危险',
      dataIndex: 'is_dangerous',
      width: 60,
      render: (dangerous: boolean) => dangerous ? (
        <Tag color="red" icon={<WarningOutlined />}>危险</Tag>
      ) : null,
    },
    {
      title: '状态',
      dataIndex: 'is_enabled',
      width: 80,
      render: (enabled: boolean, record: Tool) => (
        <Switch
          checked={enabled}
          onChange={(checked) => handleToggleEnabled(record.name, checked)}
        />
      ),
    },
    {
      title: '操作',
      width: 100,
      render: (_: any, record: Tool) => (
        <Button
          size="small"
          icon={<PlayCircleOutlined />}
          onClick={() => handleExecute(record)}
          disabled={!record.is_enabled}
        >
          执行
        </Button>
      ),
    },
  ]

  return (
    <div>
      <Alert
        message="工具管理"
        description="管理系统中可用的工具。危险工具需要谨慎使用。"
        type="info"
        showIcon
        style={{ marginBottom: 16 }}
      />

      <Table
        columns={columns}
        dataSource={tools}
        rowKey="name"
        loading={loading}
        pagination={false}
      />

      {/* Execute Tool Modal */}
      <Modal
        title={`执行工具: ${selectedTool?.name}`}
        open={executeModalOpen}
        onCancel={() => setExecuteModalOpen(false)}
        onOk={() => executeForm.submit()}
        width={600}
      >
        {selectedTool?.is_dangerous && (
          <Alert
            message="危险操作"
            description="此工具可能执行危险操作，请谨慎使用。"
            type="warning"
            showIcon
            style={{ marginBottom: 16 }}
          />
        )}
        
        <p style={{ color: '#666', marginBottom: 16 }}>
          {selectedTool?.description}
        </p>

        <Form
          form={executeForm}
          layout="vertical"
          onFinish={handleExecuteSubmit}
        >
          {selectedTool && Object.entries(selectedTool.parameters).map(([key, param]) => (
            <Form.Item
              key={key}
              name={key}
              label={key}
              rules={[{ required: param.required, message: `请输入 ${key}` }]}
            >
              {param.type === 'integer' ? (
                <Input type="number" placeholder={param.description} />
              ) : param.type === 'boolean' ? (
                <Select placeholder={param.description}>
                  <Select.Option value={true}>true</Select.Option>
                  <Select.Option value={false}>false</Select.Option>
                </Select>
              ) : param.description.includes('\n') || param.description.length > 50 ? (
                <Input.TextArea rows={4} placeholder={param.description} />
              ) : (
                <Input placeholder={param.description} />
              )}
            </Form.Item>
          ))}
        </Form>

        {executeResult && (
          <div style={{ marginTop: 16 }}>
            <div style={{ fontWeight: 500, marginBottom: 8 }}>执行结果:</div>
            <pre style={{
              background: executeResult.success ? '#f6ffed' : '#fff2f0',
              border: `1px solid ${executeResult.success ? '#b7eb8f' : '#ffccc7'}`,
              borderRadius: 4,
              padding: 12,
              maxHeight: 300,
              overflow: 'auto'
            }}>
              {JSON.stringify(executeResult.output || executeResult.error, null, 2)}
            </pre>
          </div>
        )}
      </Modal>
    </div>
  )
}