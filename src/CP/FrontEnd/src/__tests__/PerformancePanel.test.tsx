import { describe, expect, it, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'

import { PerformancePanel } from '../pages/authenticated/MyAgents'

vi.mock('../services/performanceStats.service', () => ({
  listPerformanceStats: vi.fn(async () => [
    { metric_key: 'posts_published', metric_value: 12, stat_date: '2026-03-01' },
  ]),
}))

vi.mock('../services/contentAnalytics.service', () => ({
  getContentRecommendations: vi.fn(async () => ({
    top_dimensions: ['education', 'shorts'],
    best_posting_hours: [9, 14],
    avg_engagement_rate: 0.042,
    total_posts_analyzed: 4,
    recommendation_text: 'Lead with educational shorts.',
  })),
}))

describe('PerformancePanel', () => {
  it('renders content insights when recommendations exist', async () => {
    render(
      <PerformancePanel
        instance={{ hired_instance_id: 'HIRED-1', subscription_id: 'SUB-1', agent_id: 'AGENT-1', duration: 'monthly', status: 'active', current_period_start: '', current_period_end: '', cancel_at_period_end: false }}
      />
    )

    await waitFor(() => {
      expect(screen.getByText('Content Insights')).toBeInTheDocument()
    })
    expect(screen.getByText(/9 AM, 2 PM/i)).toBeInTheDocument()
    expect(screen.getByText('education')).toBeInTheDocument()
  })

  it('renders the build-up hint when not enough posts are analyzed', async () => {
    const analytics = await import('../services/contentAnalytics.service')
    vi.mocked(analytics.getContentRecommendations).mockResolvedValueOnce({
      top_dimensions: [],
      best_posting_hours: [],
      avg_engagement_rate: 0,
      total_posts_analyzed: 1,
      recommendation_text: '',
    })

    render(
      <PerformancePanel
        instance={{ hired_instance_id: 'HIRED-2', subscription_id: 'SUB-2', agent_id: 'AGENT-2', duration: 'monthly', status: 'active', current_period_start: '', current_period_end: '', cancel_at_period_end: false }}
      />
    )

    await waitFor(() => {
      expect(screen.getByText(/Building insights/i)).toBeInTheDocument()
    })
  })

  it('renders an error when recommendations fail to load', async () => {
    const analytics = await import('../services/contentAnalytics.service')
    vi.mocked(analytics.getContentRecommendations).mockRejectedValueOnce(new Error('boom'))

    render(
      <PerformancePanel
        instance={{ hired_instance_id: 'HIRED-3', subscription_id: 'SUB-3', agent_id: 'AGENT-3', duration: 'monthly', status: 'active', current_period_start: '', current_period_end: '', cancel_at_period_end: false }}
      />
    )

    await waitFor(() => {
      expect(screen.getByText('Failed to load content insights.')).toBeInTheDocument()
    })
  })
})
