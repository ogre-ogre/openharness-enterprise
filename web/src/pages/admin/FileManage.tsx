import { useState, useEffect } from 'react'
import {
  Card, Table, Button, message, Popconfirm, Tag, Space, Tree, Layout, Alert, Tooltip
} from 'antd'
import {
  DeleteOutlined, DownloadOutlined, ReloadOutlined,
  FolderOutlined, FileOutlined, HomeOutlined
} from '@ant-design/icons'
import type { DataNode } from 'antd/es/tree'
import type { TableRowSelection } from 'antd/es/table/interface'
import { useAuthStore } from '../../stores/auth'

const { Sider, Content } = Layout

interface FileInfo {
  name: string
  path: string
  size: number
  type: string
  modified_at: string
  can_delete: boolean
}

interface FolderInfo {
  name: string
  path: string
  type: string
  can_delete: boolean
}

interface FileListResponse {
  path: string
  files: FileInfo[]
  folders: FolderInfo[]
}

interface TreeData {
  key: string
  title: string
  isLeaf?: boolean
  children?: TreeData[]
}

// 可删除的目录列表
const DELETABLE_DIRS = ['uploads']

export default function FileManage() {
  const [treeData, setTreeData] = useState<DataNode[]>([])
  const [currentPath, setCurrentPath] = useState('')
  const [files, setFiles] = useState<FileInfo[]>([])
  const [folders, setFolders] = useState<FolderInfo[]>([])
  const [loading, setLoading] = useState(false)
  const [selectedKeys, setSelectedKeys] = useState<React.Key[]>([])
  const [treeLoading, setTreeLoading] = useState(false)
  
  const { user } = useAuthStore()
  const isAdmin = user?.role === 'admin'
  const token = useAuthStore.getState().token

  useEffect(() => {
    loadTree()
  }, [])

  useEffect(() => {
    if (currentPath !== undefined) {
      loadFileList(currentPath)
    }
  }, [currentPath])

  const loadTree = async () => {
    setTreeLoading(true)
    try {
      const response = await fetch('/api/files/tree', {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      const data = await response.json()
      
      // Convert to Ant Design Tree format
      const convertToDataNode = (items: TreeData[]): DataNode[] => {
        return items.map(item => ({
          key: item.key,
          title: item.isLeaf ? (
            <Space>
              <FileOutlined />
              <span>{item.title}</span>
            </Space>
          ) : (
            <Space>
              <FolderOutlined />
              <span>{item.title}</span>
            </Space>
          ),
          isLeaf: item.isLeaf,
          children: item.children ? convertToDataNode(item.children) : undefined
        }))
      }
      
      setTreeData(convertToDataNode(data.tree || []))
    } catch (error) {
      message.error('加载目录树失败')
    } finally {
      setTreeLoading(false)
    }
  }

  const loadFileList = async (path: string) => {
    setLoading(true)
    try {
      const response = await fetch(`/api/files/list?path=${encodeURIComponent(path)}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      const data: FileListResponse = await response.json()
      setFiles(data.files || [])
      setFolders(data.folders || [])
      setSelectedKeys([])
    } catch (error) {
      message.error('加载文件列表失败')
    } finally {
      setLoading(false)
    }
  }

  const handleTreeSelect = (selectedKeys: React.Key[]) => {
    if (selectedKeys.length > 0) {
      const path = selectedKeys[0] as string
      setCurrentPath(path)
    }
  }

  const handleRefresh = () => {
    loadTree()
    loadFileList(currentPath)
  }

  const handleDownloadSelected = async () => {
    if (selectedKeys.length === 0) {
      message.warning('请先选择要下载的文件')
      return
    }

    try {
      const response = await fetch('/api/files/download', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(selectedKeys)
      })

      if (!response.ok) {
        const error = await response.json()
        message.error(error.detail || '下载失败')
        return
      }

      // Download ZIP file
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `download_${new Date().toISOString().slice(0, 19).replace(/[:-]/g, '')}.zip`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      window.URL.revokeObjectURL(url)
      
      message.success('下载成功')
    } catch (error) {
      message.error('下载失败')
    }
  }

  const handleDelete = async (path: string) => {
    try {
      const response = await fetch('/api/files/delete', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify([path])
      })

      const data = await response.json()
      
      if (data.deleted && data.deleted.length > 0) {
        message.success(data.message)
        loadFileList(currentPath)
        loadTree()
      } else {
        message.error(data.failed?.[0]?.reason || '删除失败')
      }
    } catch (error) {
      message.error('删除失败')
    }
  }

  const canDeletePath = (path: string) => {
    const topDir = path.split('/')[0] || path
    return DELETABLE_DIRS.includes(topDir)
  }

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  // Combine files and folders for table
  const tableData = [
    ...folders.map(f => ({ ...f, isFolder: true, key: f.path })),
    ...files.map(f => ({ ...f, isFolder: false, key: f.path }))
  ]

  const columns = [
    {
      title: '名称',
      dataIndex: 'name',
      key: 'name',
      render: (name: string, record: any) => (
        <Space>
          {record.isFolder ? <FolderOutlined style={{ color: '#1890ff' }} /> : <FileOutlined style={{ color: '#52c41a' }} />}
          <span>{name}</span>
          {record.isFolder && <Tag color="blue">文件夹</Tag>}
        </Space>
      )
    },
    {
      title: '大小',
      dataIndex: 'size',
      key: 'size',
      width: 120,
      render: (size: number, record: any) => record.isFolder ? '-' : formatFileSize(size)
    },
    {
      title: '修改时间',
      dataIndex: 'modified_at',
      key: 'modified_at',
      width: 180,
      render: (time: string, record: any) => record.isFolder ? '-' : (time ? time.slice(0, 19).replace('T', ' ') : '-')
    },
    {
      title: '操作',
      key: 'action',
      width: 120,
      render: (_, record: any) => {
        const canDelete = canDeletePath(record.path)
        
        if (!canDelete) {
          return (
            <Tooltip title="该目录下文件不允许删除">
              <Button type="text" disabled icon={<DeleteOutlined />}>
                删除
              </Button>
            </Tooltip>
          )
        }
        
        return (
          <Popconfirm
            title={`确定删除 ${record.isFolder ? '文件夹' : '文件'} "${record.name}"？`}
            description={record.isFolder ? "文件夹内所有文件将一并删除" : "删除后无法恢复"}
            onConfirm={() => handleDelete(record.path)}
            okText="删除"
            cancelText="取消"
          >
            <Button type="text" danger icon={<DeleteOutlined />}>
              删除
            </Button>
          </Popconfirm>
        )
      }
    }
  ]

  const rowSelection: TableRowSelection<any> = {
    selectedRowKeys: selectedKeys,
    onChange: (newSelectedKeys: React.Key[]) => {
      setSelectedKeys(newSelectedKeys)
    }
  }

  return (
    <div style={{ padding: 0, height: 'calc(100vh - 64px)' }}>
      <Layout style={{ height: '100%', background: '#fff' }}>
        <Sider width={250} theme="light" style={{ borderRight: '1px solid #f0f0f0' }}>
          <div style={{ padding: 16 }}>
            <Space>
              <HomeOutlined />
              <strong>目录结构</strong>
            </Space>
          </div>
          <Tree
            treeData={treeData}
            onSelect={handleTreeSelect}
            loading={treeLoading}
            defaultExpandedKeys={['uploads', 'skills', 'memory', 'config', 'knowledge']}
            style={{ padding: '8px 16px' }}
          />
        </Sider>
        <Content style={{ padding: 24 }}>
          <Card>
            <Space style={{ marginBottom: 16, width: '100%', justifyContent: 'space-between' }}>
              <Space>
                <span>当前目录: <Tag color="blue">{currentPath || '根目录'}</Tag></span>
                {selectedKeys.length > 0 && (
                  <span>已选择 <Tag color="green">{selectedKeys.length}</Tag> 个文件/文件夹</span>
                )}
              </Space>
              <Space>
                <Button icon={<ReloadOutlined />} onClick={handleRefresh}>
                  刷新
                </Button>
                <Button 
                  type="primary" 
                  icon={<DownloadOutlined />} 
                  onClick={handleDownloadSelected}
                  disabled={selectedKeys.length === 0}
                >
                  打包下载
                </Button>
              </Space>
            </Space>

            <Alert
              message="删除权限说明"
              description="只有 uploads 目录下的文件可以删除。其他目录（skills、memory、config、knowledge）的文件请通过相应功能页面管理。"
              type="info"
              showIcon
              style={{ marginBottom: 16 }}
            />

            <Table
              dataSource={tableData}
              columns={columns}
              rowKey="key"
              loading={loading}
              rowSelection={rowSelection}
              pagination={false}
              size="small"
              locale={{ emptyText: currentPath ? '目录为空' : '请从左侧选择目录' }}
            />
          </Card>
        </Content>
      </Layout>
    </div>
  )
}