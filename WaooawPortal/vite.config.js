import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    host: true
  },
  build: {
    outDir: 'dist',
    sourcemap: false, // Disable sourcemaps for cleaner production
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: false, // Keep console for debugging, but we filter it
        drop_debugger: true
      }
    }
  }
})
