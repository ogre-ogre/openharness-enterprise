import { useState, useEffect } from 'react'
import { Table, Button, Space, Tag, Modal, Form, Input, Select, message, Popconfirm, Typography } from 'antd'
import { PlusOutlined, ReloadOutlined, KeyOutlined, StopOutlined } from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import { adminApi } from '../../services/api'

interface User {
  id: number
  username: string
  display_name: string | null
  email: string | null
  role: string
  is_active: boolean
  api_key_enabled: boolean
  created_at: string
  last_login_at: string | null
}

export default function Users() {
  const [users, setUsers] = useState<User[]>([])
  const [loading, setLoading] = useState(false)
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  
  const [createModalOpen, setCreateModalOpen] = useState(false)
  const [apiKeyModalOpen, setApiKeyModalOpen] = useState(false)
  const [selectedUser, setSelectedUser] = useState<User | null>(null)
  const [apiKey, setApiKey] = useState('')
  
  const [createForm] = Form.useForm()

  useEffect(() => {
    loadUsers()
  }, [page])

  const loadUsers = async () => {
    setLoading(true)
    try {
      const response = await adminApi.listUsers(search, page)
      setUsers(response.data.users)
      setTotal(response.data.total)
    } catch (error) {
      message.error('加载用户失败')
    } finally {
      setLoading(false)
    }
  }

  const handleCreate = async (values: any) => {
    try {
      const response = await adminApi.createUser(values)
      message.success('用户创建成功')
      message.info(`API Key: ${response.data.api_key}`)
      setCreateModalOpen(false)
      createForm.resetFields()
      loadUsers()
    } catch (error: any) {
      message.error(error.response?.data?.detail || '创建失败')
    }
  }

  const handleDisable = async (userId: number) => {
    try {
      await adminApi.disableUser(userId)
      message.success('用户已禁用')
      loadUsers()
    } catch (error) {
      message.error('操作失败')
    }
  }

  const handleShowApiKey = async (user: User) => {
    setSelectedUser(user)
    try {
      const response = await adminApi.getUserApiKey(user.id)
      setApiKey(response.data.api_key)
      setApiKeyModalOpen(true)
    } catch (error) {
      message.error('获取 API Key 失败')
    }
  }

  const handleRegenerateApiKey = async () => {
    if (!selectedUser) return
    
    try {
      const response = await adminApi.regenerateUserApiKey(selectedUser.id)
      setApiKey(response.data.api_key)
      message.success('API Key 已重新生成')
    } catch (error) {
      message.error('操作失败')
    }
  }

  const columns: ColumnsType<User> = [
    {
      title: 'ID',
      dataIndex: 'id',
      width: 60,
    },
    {
      title: '用户名',
      dataIndex: 'username',
      width: 120,
    },
    {
      title: '显示名',
      dataIndex: 'display_name',
      width: 120,
    },
    {
      title: '角色',
      dataIndex: 'role',
      width: 80,
      render: (role) => (
        <Tag color={role === 'admin' ? 'gold' : 'blue'}>
          {role === 'admin' ? '管理员' : '用户'}
        </Tag>
      ),
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      width: 80,
      render: (active) => (
        <Tag color={active ? 'green' : 'red'}>
          {active ? '启用' : '禁用'}
        </Tag>
      ),
    },
    {
      title: 'API Key',
      dataIndex: 'api_key_enabled',
      width: 100,
      render: (enabled) => (
        <Tag color={enabled ? 'green' : 'default'}>
          {enabled ? '已启用' : '已禁用'}
        </Tag>
      ),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      width: 160,
      render: (date) => date ? new Date(date).toLocaleString() : '-',
    },
    {
      title: '操作',
      key: 'action',
      width: 200,
      render: (_, record) => (
        <Space size="small">
          <Button
            size="small"
            icon={<KeyOutlined />}
            onClick={() => handleShowApiKey(record)}
          >
            API Key
          </Button>
          {record.is_active && record.role !== 'admin' && (
            <Popconfirm
              title="确定要禁用此用户吗？"
              onConfirm={() => handleDisable(record.id)}
            >
              <Button size="small" danger icon={<StopOutlined />}>
                禁用
              </Button>
            </Popconfirm>
          )}
        </Space>
      ),
    },
  ]

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between' }}>
        <Space>
          <Input.Search
            placeholder="搜索用户"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            onSearch={loadUsers}
            style={{ width: 200 }}
          />
        </Space>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => setCreateModalOpen(true)}
        >
          创建用户
        </Button>
      </div>

      <Table
        columns={columns}
        dataSource={users}
        rowKey="id"
        loading={loading}
        pagination={{
          current: page,
          total,
          pageSize: 20,
          onChange: setPage,
        }}
      />

      {/* Create User Modal */}
      <Modal
        title="创建用户"
        open={createModalOpen}
        onCancel={() => setCreateModalOpen(false)}
        footer={null}
      >
        <Form
          form={createForm}
          layout="vertical"
          onFinish={handleCreate}
        >
          <Form.Item
            name="username"
            label="用户名"
            rules={[{ required: true, message: '请输入用户名' }]}
          >
            <Input />
          </Form.Item>
          <Form.Item
            name="password"
            label="密码"
            rules={[
              { required: true, message: '请输入密码' },
              { min: 8, message: '密码至少8位' },
            ]}
          >
            <Input.Password />
          </Form.Item>
          <Form.Item name="display_name" label="显示名">
            <Input />
          </Form.Item>
          <Form.Item name="email" label="邮箱">
            <Input />
          </Form.Item>
          <Form.Item name="role" label="角色" initialValue="user">
            <Select>
              <Select.Option value="user">用户</Select.Option>
              <Select.Option value="admin">管理员</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">
                创建
              </Button>
              <Button onClick={() => setCreateModalOpen(false)}>
                取消
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* API Key Modal */}
      <Modal
        title={`API Key - ${selectedUser?.username}`}
        open={apiKeyModalOpen}
        onCancel={() => setApiKeyModalOpen(false)}
        footer={null}
      >
        <Typography.Paragraph copyable>
          {apiKey}
        </Typography.Paragraph>
        <Button
          icon={<ReloadOutlined />}
          onClick={handleRegenerateApiKey}
        >
          重新生成
        </Button>
      </Modal>
    </div>
  )
}