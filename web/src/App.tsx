import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from './stores/auth'
import Login from './pages/Login'
import Chat from './pages/Chat'
import AdminLayout from './pages/admin/AdminLayout'
import Users from './pages/admin/Users'
import Status from './pages/admin/Status'
import AuditLogs from './pages/admin/AuditLogs'
import AgentManage from './pages/admin/AgentManage'
import TeamManage from './pages/admin/TeamManage'
import ToolManage from './pages/admin/ToolManage'
import SkillManage from './pages/admin/SkillManage'
import FileManage from './pages/admin/FileManage'

function PrivateRoute({ children }: { children: React.ReactNode }) {
  const { user, token } = useAuthStore()
  
  if (!token) {
    return <Navigate to="/login" replace />
  }
  
  return <>{children}</>
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route
          path="/chat"
          element={
            <PrivateRoute>
              <Chat />
            </PrivateRoute>
          }
        />
        <Route
          path="/admin"
          element={
            <PrivateRoute>
              <AdminLayout />
            </PrivateRoute>
          }
        >
          <Route index element={<Navigate to="skills" replace />} />
          <Route path="users" element={<Users />} />
          <Route path="skills" element={<SkillManage />} />
          <Route path="files" element={<FileManage />} />
          <Route path="agents" element={<AgentManage />} />
          <Route path="teams" element={<TeamManage />} />
          <Route path="tools" element={<ToolManage />} />
          <Route path="status" element={<Status />} />
          <Route path="audit" element={<AuditLogs />} />
        </Route>
        <Route path="/" element={<Navigate to="/chat" replace />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App