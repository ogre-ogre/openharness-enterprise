import { Outlet, useNavigate, useLocation } from 'react-router-dom'
import { Layout, Menu } from 'antd'
import { UserOutlined, DashboardOutlined, AuditOutlined, LogoutOutlined, RobotOutlined, TeamOutlined, ToolOutlined, FileZipOutlined } from '@ant-design/icons'
import { useAuthStore } from '../../stores/auth'

const { Sider, Content, Header } = Layout

export default function AdminLayout() {
  const navigate = useNavigate()
  const location = useLocation()
  const { logout, user } = useAuthStore()

  const isAdmin = user?.role === 'admin'

  // 根据角色过滤菜单：普通用户只显示"技能管理"
  const allMenuItems = [
    { key: 'users', icon: <UserOutlined />, label: '用户管理', adminOnly: true },
    { key: 'skills', icon: <FileZipOutlined />, label: '技能管理', adminOnly: false },
    { key: 'agents', icon: <RobotOutlined />, label: 'Agent 管理', adminOnly: true },
    { key: 'teams', icon: <TeamOutlined />, label: '团队管理', adminOnly: true },
    { key: 'tools', icon: <ToolOutlined />, label: '工具管理', adminOnly: true },
    { key: 'status', icon: <DashboardOutlined />, label: '系统状态', adminOnly: true },
    { key: 'audit', icon: <AuditOutlined />, label: '审计日志', adminOnly: true },
  ]

  const menuItems = allMenuItems.filter(item => isAdmin || !item.adminOnly)

  // Get current selected key from path
  const currentKey = location.pathname.split('/').pop() || 'skills'

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
          {isAdmin ? '管理后台' : '技能管理'}
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
            {isAdmin ? '管理员' : '用户'}: {user?.display_name || user?.username}
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