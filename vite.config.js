import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:5001',
        changeOrigin: true
      }
    },
    hmr: {
      // Reduce reconnection attempts when server is down
      clientPort: 5173,
      overlay: false // Disable error overlay for connection errors
    }
  },
  logLevel: 'warn',
  // Suppress connection refused errors in console
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          'react-vendor': ['react', 'react-dom'],
          'chat': ['./src/components/UnifiedChat'],
          'war-room': ['./src/pages/WarRoom']
        }
      },
      onwarn(warning, warn) {
        // Suppress network errors
        if (warning.code === 'UNRESOLVED_IMPORT' || warning.message?.includes('ERR_CONNECTION_REFUSED')) {
          return
        }
        warn(warning)
      }
    },
    chunkSizeWarningLimit: 1000 // Increased from default 500KB
  }
})

