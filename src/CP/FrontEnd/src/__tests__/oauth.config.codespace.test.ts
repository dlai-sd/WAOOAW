import { afterEach, describe, expect, it, vi } from 'vitest'

const originalLocation = window.location

describe('cp oauth config in codespaces', () => {
  afterEach(() => {
    vi.resetModules()
    Object.defineProperty(window, 'location', {
      value: originalLocation,
      configurable: true,
      writable: true
    })
  })

  it('uses current origin plus /api for github.dev hosts', async () => {
    ;(window as any).__WAOOAW_RUNTIME_CONFIG__ = {
      environment: 'codespace',
      googleClientId: 'runtime-client-id'
    }

    Object.defineProperty(window, 'location', {
      value: new URL('https://demo-space-3002.app.github.dev/'),
      configurable: true,
      writable: true,
    })

    const { config } = await import('../config/oauth.config')

    expect(config.apiBaseUrl).toBe('https://demo-space-3002.app.github.dev/api')
    expect(config.googleClientId).toBe('runtime-client-id')
  })
})
