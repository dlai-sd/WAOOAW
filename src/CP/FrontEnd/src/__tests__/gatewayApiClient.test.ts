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

  it('retries retryable HTTP statuses with exponential backoff (1s, 2s, 4s)', async () => {
    vi.useFakeTimers()

    const fetchSpy = vi
      .spyOn(globalThis, 'fetch' as any)
      .mockResolvedValueOnce({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error',
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => ({ detail: 'transient error' })
      } as any)
      .mockResolvedValueOnce({
        ok: false,
        status: 503,
        statusText: 'Service Unavailable',
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => ({ detail: 'transient error 2' })
      } as any)
      .mockResolvedValueOnce({
        ok: false,
        status: 429,
        statusText: 'Too Many Requests',
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => ({ detail: 'rate limited' })
      } as any)
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        statusText: 'OK',
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => ({ ok: true })
      } as any)

    const { gatewayRequestJson } = await import('../services/gatewayApiClient')

    const promise = gatewayRequestJson('/v1/health')

    // Attempt 1 happens immediately.
    await Promise.resolve()
    expect(fetchSpy).toHaveBeenCalledTimes(1)

    // Retry 1 after 1s.
    await vi.advanceTimersByTimeAsync(999)
    expect(fetchSpy).toHaveBeenCalledTimes(1)
    await vi.advanceTimersByTimeAsync(1)
    expect(fetchSpy).toHaveBeenCalledTimes(2)

    // Retry 2 after 2s.
    await vi.advanceTimersByTimeAsync(1_999)
    expect(fetchSpy).toHaveBeenCalledTimes(2)
    await vi.advanceTimersByTimeAsync(1)
    expect(fetchSpy).toHaveBeenCalledTimes(3)

    // Retry 3 after 4s.
    await vi.advanceTimersByTimeAsync(3_999)
    expect(fetchSpy).toHaveBeenCalledTimes(3)
    await vi.advanceTimersByTimeAsync(1)
    expect(fetchSpy).toHaveBeenCalledTimes(4)

    await expect(promise).resolves.toMatchObject({ ok: true })
    vi.useRealTimers()
  })

  it('sanitizes stack traces from user-facing error messages', async () => {
    vi.useFakeTimers()

    vi.spyOn(globalThis, 'fetch' as any).mockResolvedValue({
      ok: false,
      status: 500,
      statusText: 'Internal Server Error',
      headers: new Headers({ 'content-type': 'application/json' }),
      json: async () => ({
        detail: 'Traceback (most recent call last):\n  File "app.py", line 1\nBoom'
      })
    } as any)

    const { gatewayRequestJson } = await import('../services/gatewayApiClient')

    const promise = gatewayRequestJson('/v1/health')
    const settled = promise.then(
      () => ({ ok: true } as const),
      (err: any) => ({ ok: false as const, err })
    )
    await Promise.resolve()
    await vi.advanceTimersByTimeAsync(1_000 + 2_000 + 4_000)

    const result = await settled
    expect(result.ok).toBe(false)
    expect(result.ok ? null : result.err).toMatchObject({ name: 'GatewayApiError', status: 500 })
    expect(String(result.ok ? '' : result.err?.message || '')).not.toContain('Traceback')

    vi.useRealTimers()
  })
})
