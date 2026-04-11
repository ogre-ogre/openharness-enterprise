import { Outlet, useNavigate, useLocation } from 'react-router-dom'
import { Layout, Menu } from 'antd'
import { UserOutlined, DashboardOutlined, AuditOutlined, LogoutOutlined, RobotOutlined, TeamOutlined, ToolOutlined, FileZipOutlined } from '@ant-design/icons'
import { useAuthStore } from '../../stores/auth'

const { Sider, Content, Header } = Layout

export default function AdminLayout() {
  const navigate = useNavigate()
  const location = useLocation()
  const { logout, user } = useAuthStore()

  const menuItems = [
    { key: 'users', icon: <UserOutlined />, label: '用户管理' },
    { key: 'skills', icon: <FileZipOutlined />, label: '技能管理' },
    { key: 'agents', icon: <RobotOutlined />, label: 'Agent 管理' },
    { key: 'teams', icon: <TeamOutlined />, label: '团队管理' },
    { key: 'tools', icon: <ToolOutlined />, label: '工具管理' },
    { key: 'status', icon: <DashboardOutlined />, label: '系统状态' },
    { key: 'audit', icon: <AuditOutlined />, label: '审计日志' },
  ]

  // Get current selected key from path
  const currentKey = location.pathname.split('/').pop() || 'users'

  const handleMenuClick = ({ key }: { key: string }) => {
    navigate(`/admin/${key}`)
  }

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider width={220} theme="dark">
        <div style={{
          height: 64,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#fff',
          fontSize: 18,
          fontWeight: 'bold'
        }}>
          管理后台
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[currentKey]}
          items={menuItems}
          onClick={handleMenuClick}
        />
      </Sider>
      <Layout>
        <Header style={{
          background: '#fff',
          padding: '0 24px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <div style={{ fontSize: 16 }}>
            管理员: {user?.display_name || user?.username}
          </div>
          <div>
            <a onClick={() => navigate('/chat')} style={{ marginRight: 16 }}>
              返回聊天
            </a>
            <a onClick={handleLogout}>
              <LogoutOutlined /> 退出
            </a>
          </div>
        </Header>
        <Content style={{ margin: 24 }}>
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  )
}