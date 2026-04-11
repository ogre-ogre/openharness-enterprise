import { useState, useEffect } from 'react'
import { Table, InputNumber, Select, Space, Tag, message } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { useAuthStore } from '../../stores/auth'

interface AuditLog {
  id: number
  user_id: number | null
  action: string
  resource_type: string | null
  resource_id: string | null
  details: Record<string, any> | null
  ip_address: string | null
  created_at: string
}

export default function AuditLogs() {
  const [logs, setLogs] = useState<AuditLog[]>([])
  const [loading, setLoading] = useState(false)
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  
  const [userId, setUserId] = useState<number | undefined>()
  const [action, setAction] = useState<string | undefined>()
  
  const { token } = useAuthStore()

  useEffect(() => {
    if (token) {
      loadLogs()
    }
  }, [page, userId, action, token])

  const loadLogs = async () => {
    if (!token) return
    
    setLoading(true)
    try {
      const params = new URLSearchParams()
      params.append('page', String(page))
      params.append('limit', '50')
      if (userId) params.append('user_id', String(userId))
      if (action) params.append('action', action)
      
      const response = await fetch(`/api/admin/audit-logs?${params}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      
      if (!response.ok) {
        throw new Error('Failed to load audit logs')
      }
      
      const data = await response.json()
      setLogs(data.logs || [])
      setTotal(data.total || 0)
    } catch (error) {
      console.error('Failed to load audit logs:', error)
      message.error('加载审计日志失败')
    } finally {
      setLoading(false)
    }
  }

  const getActionColor = (action: string) => {
    if (action.includes('create')) return 'green'
    if (action.includes('delete') || action.includes('disable')) return 'red'
    if (action.includes('admin')) return 'gold'
    if (action.includes('login')) return 'blue'
    if (action.includes('chat')) return 'purple'
    return 'default'
  }

  const getActionText = (action: string) => {
    const actionMap: Record<string, string> = {
      'login': '登录',
      'logout': '登出',
      'chat': '聊天',
      'token_by_api_key': 'API Key 认证',
      'websocket_connect': 'WebSocket 连接',
      'file_upload': '文件上传',
      'admin_create_user': '创建用户',
      'admin_update_user': '更新用户',
      'admin_disable_user': '禁用用户',
    }
    return actionMap[action] || action
  }

  const columns: ColumnsType<AuditLog> = [
    {
      title: 'ID',
      dataIndex: 'id',
      width: 60,
    },
    {
      title: '用户ID',
      dataIndex: 'user_id',
      width: 80,
      render: (id) => id || '-'
    },
    {
      title: '操作',
      dataIndex: 'action',
      width: 150,
      render: (action) => (
        <Tag color={getActionColor(action)}>{getActionText(action)}</Tag>
      ),
    },
    {
      title: '资源类型',
      dataIndex: 'resource_type',
      width: 100,
      render: (type) => type || '-'
    },
    {
      title: '资源ID',
      dataIndex: 'resource_id',
      width: 150,
      ellipsis: true,
      render: (id) => id || '-'
    },
    {
      title: '详情',
      dataIndex: 'details',
      width: 200,
      ellipsis: true,
      render: (details) => {
        if (!details) return '-'
        const str = JSON.stringify(details)
        return str.length > 50 ? str.substring(0, 50) + '...' : str
      }
    },
    {
      title: 'IP地址',
      dataIndex: 'ip_address',
      width: 120,
      render: (ip) => ip || '-'
    },
    {
      title: '时间',
      dataIndex: 'created_at',
      width: 180,
      render: (date) => date ? new Date(date).toLocaleString() : '-'
    },
  ]

  return (
    <div>
      <h2 style={{ marginBottom: 24 }}>审计日志</h2>
      
      <div style={{ marginBottom: 16 }}>
        <Space>
          <InputNumber
            placeholder="用户ID"
            value={userId}
            onChange={(v) => setUserId(v || undefined)}
            style={{ width: 100 }}
            min={1}
          />
          <Select
            placeholder="操作类型"
            value={action}
            onChange={setAction}
            allowClear
            style={{ width: 150 }}
            options={[
              { value: 'login', label: '登录' },
              { value: 'logout', label: '登出' },
              { value: 'chat', label: '聊天' },
              { value: 'file_upload', label: '文件上传' },
              { value: 'admin_create_user', label: '创建用户' },
              { value: 'admin_disable_user', label: '禁用用户' },
            ]}
          />
        </Space>
      </div>

      <Table
        columns={columns}
        dataSource={logs}
        rowKey="id"
        loading={loading}
        pagination={{
          current: page,
          total,
          pageSize: 50,
          onChange: setPage,
          showSizeChanger: false,
        }}
      />
    </div>
  )
}