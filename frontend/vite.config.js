import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3003,
    host: '0.0.0.0', // Allow external connections
    open: true,
    strictPort: false // Allow Vite to use next available port if 3003 is busy
  }
})

