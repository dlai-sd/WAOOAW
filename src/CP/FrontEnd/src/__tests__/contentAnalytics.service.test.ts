import { beforeEach, describe, expect, it, vi } from 'vitest'

describe('contentAnalytics.service', () => {
  beforeEach(() => {
    vi.resetModules()
    vi.clearAllMocks()
  })

  it('returns content recommendations from the CP backend route', async () => {
    const gateway = await import('../services/gatewayApiClient')
    const spy = vi.spyOn(gateway, 'gatewayRequestJson' as any).mockResolvedValue({
      top_dimensions: ['tutorial'],
      best_posting_hours: [9, 14],
      avg_engagement_rate: 0.042,
      total_posts_analyzed: 12,
      recommendation_text: 'Focus on tutorials.',
    })

    const service = await import('../services/contentAnalytics.service')
    const result = await service.getContentRecommendations('hire-123')

    expect(spy).toHaveBeenCalledWith('/cp/content-recommendations/hire-123', { method: 'GET' })
    expect(result.total_posts_analyzed).toBe(12)
  })
})
