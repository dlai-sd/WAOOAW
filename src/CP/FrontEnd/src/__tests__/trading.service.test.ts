import { describe, it, expect, vi } from 'vitest'

describe('trading.service', () => {
  it('calls CP trading draft endpoint', async () => {
    const gateway = await import('../services/gatewayApiClient')
    const spy = vi.spyOn(gateway, 'gatewayRequestJson' as any).mockResolvedValue({})

    const svc = await import('../services/trading.service')
    await svc.draftTradePlan({
      exchange_account_id: 'EXCH-1',
      coin: 'BTC',
      units: 1,
      side: 'long',
      action: 'enter',
      market: true
    })

    expect(spy).toHaveBeenCalledWith('/cp/trading/draft-plan', expect.anything())
  })
})
