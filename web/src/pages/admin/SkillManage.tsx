import { useState, useEffect } from 'react'
import {
  Card, Table, Button, Upload, message, Popconfirm, Tag, Space, Modal,
  Typography, Tooltip, Divider, Alert
} from 'antd'
import {
  DeleteOutlined, UploadOutlined, ReloadOutlined,
  FileZipOutlined, FolderOutlined, GlobalOutlined, UserOutlined
} from '@ant-design/icons'
import type { UploadFile } from 'antd/es/upload/interface'
import { useAuthStore } from '../../stores/auth'

const { Title, Text } = Typography

interface SkillInfo {
  name: string
  title: string
  description: string
  path: string
  has_skill_md: boolean
}

interface SkillsData {
  shared: SkillInfo[]
  personal: SkillInfo[]
  is_admin: boolean
}

export default function SkillManage() {
  const [skillsData, setSkillsData] = useState<SkillsData>({
    shared: [],
    personal: [],
    is_admin: false
  })
  const [loading, setLoading] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [deleteModal, setDeleteModal] = useState<{
    visible: boolean
    skillName: string
    skillType: 'shared' | 'personal'
  } | null>(null)

  const { user } = useAuthStore()
  const isAdmin = user?.role === 'admin'

  useEffect(() => {
    loadSkills()
  }, [])

  const loadSkills = async () => {
    setLoading(true)
    try {
      const response = await fetch('/api/skills/manage', {
        headers: {
          'Authorization': `Bearer ${useAuthStore.getState().token}`
        }
      })
      const data = await response.json()
      setSkillsData(data)
    } catch (error) {
      message.error('加载技能列表失败')
    } finally {
      setLoading(false)
    }
  }

  const handleUpload = async (file: File, type: 'shared' | 'personal') => {
    if (!file.name.endsWith('.zip')) {
      message.error('只支持 ZIP 文件格式')
      return false
    }

    setUploading(true)
    const formData = new FormData()
    formData.append('file', file)

    try {
      const endpoint = isAdmin ? '/api/skills/upload' : '/api/skills/upload'
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${useAuthStore.getState().token}`
        },
        body: formData
      })

      const result = await response.json()
      if (result.success) {
        message.success(result.message)
        loadSkills()
      } else {
        message.error(result.detail || '上传失败')
      }
    } catch (error) {
      message.error('上传失败')
    } finally {
      setUploading(false)
    }

    return false
  }

  const handleDelete = async () => {
    if (!deleteModal) return

    try {
      const response = await fetch(
        `/api/skills/${deleteModal.skillName}?skill_type=${deleteModal.skillType}`,
        {
          method: 'DELETE',
          headers: {
            'Authorization': `Bearer ${useAuthStore.getState().token}`
          }
        }
      )

      const result = await response.json()
      if (result.success) {
        message.success(result.message)
        loadSkills()
      } else {
        message.error(result.detail || '删除失败')
      }
    } catch (error) {
      message.error('删除失败')
    } finally {
      setDeleteModal(null)
    }
  }

  const handleReload = async () => {
    try {
      const response = await fetch('/api/skills/reload', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${useAuthStore.getState().token}`
        }
      })
      const result = await response.json()
      message.success(`技能已刷新：个人 ${result.personal_count} 个，共享 ${result.shared_count} 个`)
      loadSkills()
    } catch (error) {
      message.error('刷新失败')
    }
  }

  const renderSkillTable = (
    skills: SkillInfo[],
    type: 'shared' | 'personal',
    title: string,
    icon: React.ReactNode,
    canDelete: boolean
  ) => (
    <Card
      title={
        <Space>
          {icon}
          <span>{title}</span>
          <Tag color={type === 'shared' ? 'blue' : 'green'}>
            {skills.length} 个技能
          </Tag>
        </Space>
      }
      style={{ marginBottom: 24 }}
    >
      <Table
        dataSource={skills}
        rowKey="name"
        loading={loading}
        pagination={false}
        columns={[
          {
            title: '技能名称',
            dataIndex: 'name',
            key: 'name',
            render: (name: string, record: SkillInfo) => (
              <Space>
                <FolderOutlined style={{ color: '#1890ff' }} />
                <Text strong>{name}</Text>
                {record.has_skill_md && (
                  <Tag color="success" style={{ marginLeft: 4 }}>有效</Tag>
                )}
              </Space>
            )
          },
          {
            title: '描述',
            dataIndex: 'description',
            key: 'description',
            ellipsis: true,
            render: (desc: string) => desc || '-'
          },
          {
            title: '操作',
            key: 'action',
            width: 100,
            render: (_, record: SkillInfo) => (
              <Popconfirm
                title="确定删除此技能？"
                description="删除后无法恢复"
                onConfirm={() => setDeleteModal({
                  visible: true,
                  skillName: record.name,
                  skillType: type
                })}
                okText="删除"
                cancelText="取消"
                disabled={!canDelete}
              >
                <Button
                  type="text"
                  danger
                  icon={<DeleteOutlined />}
                  disabled={!canDelete}
                >
                  删除
                </Button>
              </Popconfirm>
            )
          }
        ]}
      />
    </Card>
  )

  return (
    <div style={{ padding: 24 }}>
      <Title level={3}>
        <FileZipOutlined style={{ marginRight: 8 }} />
        技能管理
      </Title>

      <Alert
        message="技能上传说明"
        description={
          <div>
            <p>1. 技能文件必须是 ZIP 格式，解压后应包含 SKILL.md 文件</p>
            <p>2. ZIP 文件名将成为技能名称（去除 .zip 后缀）</p>
            <p>3. {isAdmin ? '管理员上传的技能将共享给所有用户' : '上传的技能仅自己可用'}</p>
            {!isAdmin && (
              <p style={{ color: '#ff4d4f' }}>4. 技能名称不能与共享技能重复</p>
            )}
          </div>
        }
        type="info"
        showIcon
        style={{ marginBottom: 24 }}
      />

      <Card style={{ marginBottom: 24 }}>
        <Space wrap>
          <Upload
            accept=".zip"
            showUploadList={false}
            beforeUpload={(file) => handleUpload(file, isAdmin ? 'shared' : 'personal')}
          >
            <Button
              type="primary"
              icon={<UploadOutlined />}
              loading={uploading}
            >
              上传技能 {isAdmin ? '(共享)' : '(个人)'}
            </Button>
          </Upload>

          <Button
            icon={<ReloadOutlined />}
            onClick={handleReload}
          >
            刷新技能列表
          </Button>
        </Space>
      </Card>

      {renderSkillTable(
        skillsData.shared,
        'shared',
        '共享技能',
        <GlobalOutlined style={{ color: '#1890ff' }} />,
        isAdmin  // 只有管理员可以删除共享技能
      )}

      {/* 管理员和普通用户都显示个人技能，都可以删除 */}
      {renderSkillTable(
        skillsData.personal,
        'personal',
        '我的技能',
        <UserOutlined style={{ color: '#52c41a' }} />,
        true  // 所有人都可以删除自己的技能
      )}

      <Modal
        title="确认删除"
        open={deleteModal?.visible}
        onOk={handleDelete}
        onCancel={() => setDeleteModal(null)}
        okText="删除"
        cancelText="取消"
        okButtonProps={{ danger: true }}
      >
        <p>确定要删除技能 <strong>{deleteModal?.skillName}</strong> 吗？</p>
        <p style={{ color: '#999' }}>删除后将无法恢复。</p>
      </Modal>
    </div>
  )
}