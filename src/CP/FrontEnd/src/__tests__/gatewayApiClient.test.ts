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

  it('migrates legacy access_token to cp_access_token for requests', async () => {
    localStorage.setItem('access_token', 'legacy-123')

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
    expect(localStorage.getItem('cp_access_token')).toBe('legacy-123')
    expect(localStorage.getItem('access_token')).toBe(null)

    const init = fetchSpy.mock.calls[0]?.[1] as RequestInit
    const headers = init.headers as Record<string, string>
    expect(headers.Authorization).toBe('Bearer legacy-123')
  })

  it('clears tokens and sets auth-expired on 401 responses', async () => {
    localStorage.setItem('cp_access_token', 'token-401')

    vi.spyOn(globalThis, 'fetch' as any).mockResolvedValue({
      ok: false,
      status: 401,
      statusText: 'Unauthorized',
      headers: new Headers({ 'content-type': 'application/json' }),
      json: async () => ({ detail: 'Could not validate credentials' })
    } as any)

    const { gatewayRequestJson, GatewayApiError } = await import('../services/gatewayApiClient')

    await expect(gatewayRequestJson('/cp/my-agents/summary')).rejects.toMatchObject({
      name: 'GatewayApiError',
      status: 401,
      message: 'Please sign in again.'
    })
    expect(localStorage.getItem('cp_access_token')).toBe(null)
    expect(sessionStorage.getItem('waooaw:auth-expired')).toBe('1')
  })
})
