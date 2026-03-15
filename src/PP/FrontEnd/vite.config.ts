import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

function manualChunks(id: string): string | undefined {
  if (!id.includes('node_modules')) {
    return undefined
  }

  if (id.includes('@fluentui/react-icons')) {
    return 'fluent-icons'
  }

  if (id.includes('@griffel/')) {
    return 'griffel'
  }

  if (id.includes('@fluentui/')) {
    return 'fluent-ui'
  }

  if (id.includes('react-router-dom') || id.includes('@remix-run/router')) {
    return 'router'
  }

  if (id.includes('@react-oauth/google') || id.includes('jwt-decode')) {
    return 'auth'
  }

  return undefined
}

export default defineConfig({
  plugins: [react()],
  build: {
    chunkSizeWarningLimit: 600,
    rollupOptions: {
      output: {
        manualChunks,
      },
    },
  },
  server: {
    port: 8080,
    host: '0.0.0.0',
    strictPort: true,
    hmr: {
      clientPort: 8080
    },
    proxy: {
      '/api': {
        target: 'http://localhost:8015',
        changeOrigin: true,
      },
    },
  },
  test: {
    globals: true,
    environment: 'jsdom',
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html', 'text-summary'],
      include: ['src/**/*.{ts,tsx}'],
      exclude: [
        'node_modules/',
        'src/**/*.test.{ts,tsx}',
        'src/**/__tests__/**',
        'e2e/**',
        'src/main.tsx',
        'src/vite-env.d.ts'
      ],
      all: true,
      lines: 80,
      functions: 80,
      branches: 80,
      statements: 80
    }
  }
})
