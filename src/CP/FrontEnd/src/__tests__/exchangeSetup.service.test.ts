import { describe, it, expect, vi } from 'vitest'

describe('exchangeSetup.service', () => {
  it('calls CP exchange setup endpoints', async () => {
    const gateway = await import('../services/gatewayApiClient')
    const spy = vi.spyOn(gateway, 'gatewayRequestJson' as any).mockResolvedValue([])

    const svc = await import('../services/exchangeSetup.service')
    await svc.listExchangeSetups()

    expect(spy).toHaveBeenCalledWith('/cp/exchange-setup')
  })
})
