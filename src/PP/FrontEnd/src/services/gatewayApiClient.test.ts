import { describe, it, expect, beforeEach, vi } from 'vitest'

describe('PP gatewayApiClient', () => {
  beforeEach(() => {
    localStorage.clear()
    sessionStorage.clear()
    vi.restoreAllMocks()
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

    const { gatewayRequestJson } = await import('./gatewayApiClient')

    const promise = gatewayRequestJson('/v1/health')

    await Promise.resolve()
    expect(fetchSpy).toHaveBeenCalledTimes(1)

    await vi.advanceTimersByTimeAsync(1_000)
    expect(fetchSpy).toHaveBeenCalledTimes(2)

    await vi.advanceTimersByTimeAsync(2_000)
    expect(fetchSpy).toHaveBeenCalledTimes(3)

    await vi.advanceTimersByTimeAsync(4_000)
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
      json: async () => ({ detail: 'Traceback (most recent call last):\n  File "app.py", line 1\nBoom' })
    } as any)

    const { gatewayRequestJson } = await import('./gatewayApiClient')

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
