import { useState, useEffect } from 'react'
import { Card, Row, Col, Statistic } from 'antd'
import { UserOutlined, MessageOutlined, DatabaseOutlined, FolderOutlined } from '@ant-design/icons'
import { adminApi } from '../../services/api'

interface SystemStatus {
  total_users: number
  active_sessions: number
  db_size: number
  workspace_root: string
}

export default function Status() {
  const [status, setStatus] = useState<SystemStatus | null>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    loadStatus()
  }, [])

  const loadStatus = async () => {
    setLoading(true)
    try {
      const response = await adminApi.getStatus()
      setStatus(response.data)
    } catch (error) {
      console.error('Failed to load status:', error)
    } finally {
      setLoading(false)
    }
  }

  const formatBytes = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B'
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB'
    return (bytes / (1024 * 1024)).toFixed(2) + ' MB'
  }

  return (
    <div>
      <h2 style={{ marginBottom: 24 }}>系统状态</h2>
      
      <Row gutter={16}>
        <Col span={6}>
          <Card loading={loading}>
            <Statistic
              title="用户总数"
              value={status?.total_users || 0}
              prefix={<UserOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card loading={loading}>
            <Statistic
              title="活跃会话"
              value={status?.active_sessions || 0}
              prefix={<MessageOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card loading={loading}>
            <Statistic
              title="数据库大小"
              value={formatBytes(status?.db_size || 0)}
              prefix={<DatabaseOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card loading={loading}>
            <Statistic
              title="工作区"
              value={status?.workspace_root || '-'}
              prefix={<FolderOutlined />}
              valueStyle={{ fontSize: 14 }}
            />
          </Card>
        </Col>
      </Row>
    </div>
  )
}