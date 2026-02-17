import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'

function parseMinWorkers(value: string | undefined, fallback: number): number {
  if (!value) return fallback
  const parsed = Number.parseInt(value, 10)
  return Number.isFinite(parsed) && parsed > 0 ? parsed : fallback
}

function parseMaxWorkers(value: string | undefined, fallback: string | number): string | number {
  if (!value) return fallback
  const trimmed = value.trim()
  if (!trimmed) return fallback
  if (/^\d+%$/.test(trimmed)) return trimmed
  const parsed = Number.parseInt(trimmed, 10)
  return Number.isFinite(parsed) && parsed > 0 ? parsed : fallback
}

export default defineConfig({
  plugins: [react()],
  test: {
    // Run tests in parallel workers to reduce runtime.
    // Defaults vary by Vitest version; making this explicit avoids regressions.
    // Use forks (multi-process) for better stability in constrained environments.
    pool: 'forks',
    minWorkers: parseMinWorkers(process.env.VITEST_MIN_WORKERS, 1),
    // Default to using all available cores (can be overridden in CI).
    maxWorkers: parseMaxWorkers(process.env.VITEST_MAX_WORKERS, '100%'),
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/test/setup.ts',
    css: true,
    fileParallelism: true,
    include: ['src/**/*.{test,spec}.?(c|m)[tj]s?(x)'],
    exclude: [
      '**/node_modules/**',
      '**/dist/**',
      '**/.{idea,git,cache,output,temp}/**',
      'e2e/**',
    ],
  },
})
