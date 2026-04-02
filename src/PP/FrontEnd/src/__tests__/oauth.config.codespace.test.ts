import { afterEach, describe, expect, it, vi } from 'vitest'

const originalLocation = window.location

describe('pp oauth config in codespaces', () => {
  afterEach(() => {
    vi.resetModules()
    Object.defineProperty(window, 'location', {
      value: originalLocation,
      configurable: true,
      writable: true
    })
  })

  it('uses current origin plus /api for github.dev hosts', async () => {
    Object.defineProperty(window, 'location', {
      value: new URL('https://demo-space-3001.app.github.dev/'),
      configurable: true,
      writable: true,
    })

    const { config } = await import('../config/oauth.config')

    expect(config.apiBaseUrl).toBe('https://demo-space-3001.app.github.dev/api')
  })
})
