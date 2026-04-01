import { beforeEach, describe, expect, it, vi } from 'vitest'

describe('contentAnalytics.service', () => {
  beforeEach(() => {
    vi.resetModules()
    vi.clearAllMocks()
  })

  it('loads content recommendations from the CP route', async () => {
    const gateway = await import('../services/gatewayApiClient')
    const spy = vi.spyOn(gateway, 'gatewayRequestJson' as any).mockResolvedValue({
      top_dimensions: ['education'],
      best_posting_hours: [9, 14],
      avg_engagement_rate: 0.042,
      total_posts_analyzed: 8,
      recommendation_text: 'Lead with education.',
    })

    const svc = await import('../services/contentAnalytics.service')
    const result = await svc.getContentRecommendations('HIRED/1')

    expect(spy).toHaveBeenCalledWith('/cp/content-recommendations/HIRED%2F1', { method: 'GET' })
    expect(result.top_dimensions).toEqual(['education'])
  })
})
