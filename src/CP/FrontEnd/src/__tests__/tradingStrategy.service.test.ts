import { describe, it, expect, vi } from 'vitest'

describe('tradingStrategy.service', () => {
  it('calls CP trading strategy endpoints', async () => {
    const gateway = await import('../services/gatewayApiClient')
    const spy = vi.spyOn(gateway, 'gatewayRequestJson' as any).mockResolvedValue([])

    const svc = await import('../services/tradingStrategy.service')
    await svc.listTradingStrategyConfigs()

    expect(spy).toHaveBeenCalledWith('/cp/trading-strategy')
  })
})
