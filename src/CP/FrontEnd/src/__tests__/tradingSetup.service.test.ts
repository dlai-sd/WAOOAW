import { describe, it, expect, vi, beforeEach } from 'vitest'

describe('tradingSetup.service', () => {
  beforeEach(() => {
    vi.resetModules()
  })

  it('T1: getTradingSetup calls GET /cp/trading-setup/{id}', async () => {
    const gateway = await import('../services/gatewayApiClient')
    const spy = vi.spyOn(gateway, 'gatewayRequestJson' as any).mockResolvedValue({})

    const svc = await import('../services/tradingSetup.service')
    await svc.getTradingSetup('HIRED-001')

    expect(spy).toHaveBeenCalledWith('/cp/trading-setup/HIRED-001')
  })

  it('T2: sendTradingSetupMessage sends POST with {content} body to /message', async () => {
    const gateway = await import('../services/gatewayApiClient')
    const spy = vi.spyOn(gateway, 'gatewayRequestJson' as any).mockResolvedValue({})

    const svc = await import('../services/tradingSetup.service')
    await svc.sendTradingSetupMessage('HIRED-001', 'hello')

    expect(spy).toHaveBeenCalledWith(
      '/cp/trading-setup/HIRED-001/message',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ content: 'hello' }),
      })
    )
  })

  it('T3: emergencyStop sends POST to /emergency-stop', async () => {
    const gateway = await import('../services/gatewayApiClient')
    const spy = vi.spyOn(gateway, 'gatewayRequestJson' as any).mockResolvedValue({})

    const svc = await import('../services/tradingSetup.service')
    await svc.emergencyStop('HIRED-001')

    expect(spy).toHaveBeenCalledWith(
      '/cp/trading-setup/HIRED-001/emergency-stop',
      expect.objectContaining({ method: 'POST' })
    )
  })

  it('T4: getTaxReport with monthly+month builds correct query string', async () => {
    const gateway = await import('../services/gatewayApiClient')
    const spy = vi.spyOn(gateway, 'gatewayRequestJson' as any).mockResolvedValue({})

    const svc = await import('../services/tradingSetup.service')
    await svc.getTaxReport('HIRED-001', 2025, 'monthly', 3)

    expect(spy).toHaveBeenCalledWith(
      expect.stringContaining('/cp/trading/tax-report/HIRED-001')
    )
    const calledPath: string = spy.mock.calls[0][0]
    expect(calledPath).toContain('year=2025')
    expect(calledPath).toContain('period=monthly')
    expect(calledPath).toContain('month=3')
  })

  it('getTradePerformance calls GET /cp/trading/performance/{id}', async () => {
    const gateway = await import('../services/gatewayApiClient')
    const spy = vi.spyOn(gateway, 'gatewayRequestJson' as any).mockResolvedValue({})

    const svc = await import('../services/tradingSetup.service')
    await svc.getTradePerformance('HIRED-001', 30)

    expect(spy).toHaveBeenCalledWith(
      '/cp/trading/performance/HIRED-001?period_days=30'
    )
  })

  it('getTradeHistory calls GET /cp/trading/history/{id}', async () => {
    const gateway = await import('../services/gatewayApiClient')
    const spy = vi.spyOn(gateway, 'gatewayRequestJson' as any).mockResolvedValue({})

    const svc = await import('../services/tradingSetup.service')
    await svc.getTradeHistory('HIRED-001', 2, 10)

    expect(spy).toHaveBeenCalledWith(
      '/cp/trading/history/HIRED-001?page=2&page_size=10'
    )
  })

  it('getRecommendations calls GET /cp/trading/recommendations/{id}', async () => {
    const gateway = await import('../services/gatewayApiClient')
    const spy = vi.spyOn(gateway, 'gatewayRequestJson' as any).mockResolvedValue({})

    const svc = await import('../services/tradingSetup.service')
    await svc.getRecommendations('HIRED-001')

    expect(spy).toHaveBeenCalledWith('/cp/trading/recommendations/HIRED-001')
  })
})
