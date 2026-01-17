import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0', // This allows Docker to expose the port
    port: 3000,
    watch: {
      usePolling: true // Crucial for Windows Docker to see file changes
    }
  }
})