import { describe, it, expect, vi } from 'vitest'

import { couponCheckout } from '../services/couponCheckout.service'

describe('couponCheckout service', () => {
  it('posts to /api/cp/payments/coupon/checkout', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        order_id: 'ORDER-1',
        payment_provider: 'coupon',
        amount: 0,
        currency: 'INR',
        coupon_code: 'WAOOAW100',
        agent_id: 'agent-123',
        duration: 'monthly',
        subscription_status: 'active',
        trial_status: 'not_started'
      })
    })

    vi.stubGlobal('fetch', fetchMock as any)

    const res = await couponCheckout({ couponCode: 'WAOOAW100', agentId: 'agent-123', duration: 'monthly' })

    expect(res.payment_provider).toBe('coupon')
    expect(fetchMock).toHaveBeenCalledTimes(1)
    const [url] = fetchMock.mock.calls[0]
    expect(String(url)).toContain('/api/cp/payments/coupon/checkout')
  })
})
