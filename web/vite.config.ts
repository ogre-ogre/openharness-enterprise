import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  base: '/web/',  // 前端部署在 /web/ 子路径下
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8001',  // 本地后端端口
        changeOrigin: true,
      },
      '/ws': {
        target: 'ws://localhost:8001',    // 本地后端端口
        ws: true,
      },
    },
  },
  build: {
    // Skip TypeScript check during build
    typescript: false,
  },
})