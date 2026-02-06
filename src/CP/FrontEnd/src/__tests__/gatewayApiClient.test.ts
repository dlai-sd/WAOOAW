import { describe, it, expect, beforeEach, vi } from 'vitest'

describe('gatewayApiClient', () => {
  beforeEach(() => {
    localStorage.clear()
    sessionStorage.clear()
    vi.restoreAllMocks()
  })

  it('adds Authorization and X-Correlation-ID headers when token is present', async () => {
    localStorage.setItem('cp_access_token', 'token-123')

    const fetchSpy = vi.spyOn(globalThis, 'fetch' as any).mockResolvedValue({
      ok: true,
      status: 200,
      statusText: 'OK',
      headers: new Headers({ 'content-type': 'application/json' }),
      json: async () => ({ ok: true })
    } as any)

    const { gatewayRequestJson } = await import('../services/gatewayApiClient')
    await gatewayRequestJson('/v1/health')

    expect(fetchSpy).toHaveBeenCalled()
    const init = fetchSpy.mock.calls[0]?.[1] as RequestInit
    const headers = init.headers as Record<string, string>
    expect(headers.Authorization).toBe('Bearer token-123')
    expect(typeof headers['X-Correlation-ID']).toBe('string')
    expect(headers['X-Correlation-ID'].length).toBeGreaterThan(5)
  })
})
