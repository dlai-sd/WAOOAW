import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  test: {
    // Run tests in parallel workers to reduce runtime.
    // Defaults vary by Vitest version; making this explicit avoids regressions.
    pool: 'threads',
    minWorkers: process.env.VITEST_MIN_WORKERS ?? 1,
    maxWorkers: process.env.VITEST_MAX_WORKERS ?? '75%',
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/test/setup.ts',
    css: true,
    include: ['src/**/*.{test,spec}.?(c|m)[tj]s?(x)'],
    exclude: [
      '**/node_modules/**',
      '**/dist/**',
      '**/.{idea,git,cache,output,temp}/**',
      'e2e/**',
    ],
  },
})
