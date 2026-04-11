import axios from 'axios'
import { useAuthStore } from '../stores/auth'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

// Request interceptor - add auth token
api.interceptors.request.use(
  (config) => {
    const token = useAuthStore.getState().token
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Response interceptor - handle errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      useAuthStore.getState().logout()
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// Auth API
export const authApi = {
  login: (username: string, password: string) =>
    api.post('/auth/login', { username, password }),
  
  getMe: () =>
    api.get('/auth/me'),
  
  getMyApiKey: () =>
    api.get('/user/me/api-key'),
  
  regenerateMyApiKey: () =>
    api.post('/user/me/api-key/regenerate'),
}

// Sessions API
export const sessionsApi = {
  list: () =>
    api.get('/sessions'),
  
  getMessages: (sessionId: string, limit = 100) =>
    api.get(`/sessions/${sessionId}/messages`, { params: { limit } }),
  
  delete: (sessionId: string) =>
    api.delete(`/sessions/${sessionId}`),
}

// Admin API
export const adminApi = {
  // Users
  listUsers: (search?: string, page = 1, limit = 20) =>
    api.get('/admin/users', { params: { search, page, limit } }),
  
  createUser: (data: {
    username: string
    password: string
    display_name?: string
    email?: string
    role?: string
  }) =>
    api.post('/admin/users', data),
  
  getUser: (userId: number) =>
    api.get(`/admin/users/${userId}`),
  
  updateUser: (userId: number, data: {
    display_name?: string
    email?: string
    role?: string
    is_active?: boolean
  }) =>
    api.put(`/admin/users/${userId}`, data),
  
  disableUser: (userId: number) =>
    api.delete(`/admin/users/${userId}`),
  
  getUserApiKey: (userId: number) =>
    api.get(`/admin/users/${userId}/api-key`),
  
  regenerateUserApiKey: (userId: number) =>
    api.post(`/admin/users/${userId}/api-key/regenerate`),
  
  // System
  getStatus: () =>
    api.get('/admin/system/status'),
  
  // Audit Logs
  getAuditLogs: (params: {
    user_id?: number
    action?: string
    start_date?: string
    end_date?: string
    page?: number
    limit?: number
  }) =>
    api.get('/admin/audit-logs', { params }),
}

export default api