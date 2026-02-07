import { describe, it, expect, vi, beforeEach } from 'vitest'

describe('paymentsConfig.service', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
    localStorage.clear()
    sessionStorage.clear()
  })

  it('calls the CP payments config endpoint', async () => {
    const fetchSpy = vi.spyOn(globalThis, 'fetch' as any).mockResolvedValue({
      ok: true,
      status: 200,
      statusText: 'OK',
      headers: new Headers({ 'content-type': 'application/json' }),
      json: async () => ({ mode: 'coupon', coupon_code: 'WAOOAW100', coupon_unlimited: true })
    } as any)

    const { getPaymentsConfig } = await import('../services/paymentsConfig.service')
    const cfg = await getPaymentsConfig()

    expect(cfg.mode).toBe('coupon')
    expect(fetchSpy).toHaveBeenCalled()
    const url = fetchSpy.mock.calls[0]?.[0] as string
    expect(url).toContain('/api/cp/payments/config')
  })
})
