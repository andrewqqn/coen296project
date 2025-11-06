import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const backendHost =
  process.env.VITE_BACKEND_URL ||
  'https://expense-back-855319526387.us-central1.run.app'

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5173,
    proxy: {
      '/expenses': {
        target: backendHost,
        changeOrigin: true,
        secure: false,
      },
      '/auth': {
        target: backendHost,
        changeOrigin: true,
        secure: false,
      },
    },
  },
  define: {
    'process.env': process.env,
  },
})
