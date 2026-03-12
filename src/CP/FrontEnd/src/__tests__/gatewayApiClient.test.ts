import { describe, it, expect, beforeEach, vi } from 'vitest'

describe('gatewayApiClient', () => {
  beforeEach(() => {
    localStorage.clear()
    sessionStorage.clear()
    vi.restoreAllMocks()
  })

  it('adds Authorization and X-Correlation-ID headers when token is present', async () => {
    const { authService } = await import('../services/auth.service')
    authService.setTokens({
      access_token: 'token-123',
      token_type: 'bearer',
      expires_in: 3600,
    })

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

  it('clears tokens and sets auth-expired on 401 responses', async () => {
    const { authService } = await import('../services/auth.service')
    authService.setTokens({
      access_token: 'token-401',
      token_type: 'bearer',
      expires_in: 3600,
    })

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
    expect(authService.getAccessToken()).toBeNull()
    expect(sessionStorage.getItem('waooaw:auth-expired')).toBe('1')
  })

  it('forces refresh on protected 401s even without a session hint', async () => {
    const fetchSpy = vi.spyOn(globalThis, 'fetch' as any)
    fetchSpy
      .mockResolvedValueOnce({
        ok: false,
        status: 401,
        statusText: 'Unauthorized',
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => ({ detail: 'Not authenticated' })
      } as any)
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        statusText: 'OK',
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => ({ access_token: 'refreshed-token', token_type: 'bearer', expires_in: 3600 })
      } as any)
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        statusText: 'OK',
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => ({ instances: [] })
      } as any)

    const { gatewayRequestJson } = await import('../services/gatewayApiClient')

    await expect(gatewayRequestJson('/cp/my-agents/summary')).resolves.toEqual({ instances: [] })
    expect(fetchSpy).toHaveBeenCalledTimes(3)
    expect(String(fetchSpy.mock.calls[1]?.[0] || '')).toContain('/auth/refresh')
  })

  it('does not mark auth expired when backend reports user initialization lag', async () => {
    const { authService } = await import('../services/auth.service')
    authService.setTokens({
      access_token: 'token-init',
      token_type: 'bearer',
      expires_in: 3600,
    })

    vi.spyOn(globalThis, 'fetch' as any)
      .mockResolvedValueOnce({
        ok: false,
        status: 401,
        statusText: 'Unauthorized',
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => ({ detail: 'User not found' })
      } as any)
      .mockResolvedValueOnce({
        ok: false,
        status: 401,
        statusText: 'Unauthorized',
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => ({ detail: 'User not found' })
      } as any)

    const { gatewayRequestJson } = await import('../services/gatewayApiClient')

    await expect(gatewayRequestJson('/cp/my-agents/summary')).rejects.toMatchObject({
      name: 'GatewayApiError',
      status: 401,
      message: 'Your account session is still initializing. Please retry in a moment.'
    })
    expect(sessionStorage.getItem('waooaw:auth-expired')).toBeNull()
  })
})
