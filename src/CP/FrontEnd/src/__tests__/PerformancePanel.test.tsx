import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'

import { PerformancePanel } from '../pages/authenticated/MyAgents'

vi.mock('../services/performanceStats.service', () => ({
  listPerformanceStats: vi.fn(async () => [
    { stat_date: '2026-04-01', metric_key: 'posts_published', metric_value: 5 },
  ]),
}))

vi.mock('../services/contentAnalytics.service', () => ({
  getContentRecommendations: vi.fn(),
}))

describe('PerformancePanel', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders content insights with hours and dimensions', async () => {
    const analytics = await import('../services/contentAnalytics.service')
    vi.mocked(analytics.getContentRecommendations).mockResolvedValueOnce({
      top_dimensions: ['tutorial', 'behind_the_scenes'],
      best_posting_hours: [9, 14],
      avg_engagement_rate: 0.042,
      total_posts_analyzed: 6,
      recommendation_text: 'Focus on tutorial content.',
    })

    render(<PerformancePanel instance={{ hired_instance_id: 'hire-1' } as any} />)

    await waitFor(() => {
      expect(screen.getByText('Content Insights')).toBeTruthy()
    })
    expect(screen.getByText('9 AM, 2 PM')).toBeTruthy()
    expect(screen.getByText('tutorial')).toBeTruthy()
    expect(screen.getByText('Focus on tutorial content.')).toBeTruthy()
  })

  it('renders the low-data guidance when fewer than three posts were analyzed', async () => {
    const analytics = await import('../services/contentAnalytics.service')
    vi.mocked(analytics.getContentRecommendations).mockResolvedValueOnce({
      top_dimensions: [],
      best_posting_hours: [],
      avg_engagement_rate: 0,
      total_posts_analyzed: 1,
      recommendation_text: '',
    })

    render(<PerformancePanel instance={{ hired_instance_id: 'hire-1' } as any} />)

    await waitFor(() => {
      expect(screen.getByText(/Building insights — 1 posts analyzed so far/i)).toBeTruthy()
    })
  })

  it('renders an error when recommendations fail to load', async () => {
    const analytics = await import('../services/contentAnalytics.service')
    vi.mocked(analytics.getContentRecommendations).mockRejectedValueOnce(new Error('boom'))

    render(<PerformancePanel instance={{ hired_instance_id: 'hire-1' } as any} />)

    await waitFor(() => {
      expect(screen.getByText('Content insights unavailable')).toBeTruthy()
    })
  })
})
