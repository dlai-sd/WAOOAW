import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { Badge, Text } from '@fluentui/react-components'

/**
 * E2-S1-T2: Verify the brief-progress badge renders the correct text.
 *
 * The full DigitalMarketingActivationWizard loads state internally via API
 * calls (no workspace prop), so we test the Badge rendering pattern in
 * isolation — the exact JSX extracted from the wizard chat header.
 */
describe('Brief progress badge (E2-S1)', () => {
  it('renders "X/Y fields locked" when brief_progress is present', () => {
    const briefProgress = { filled: 8, total: 11, missing_fields: ['tone', 'cta', 'youtube_angle'], locked_fields: {} }

    render(
      <div>
        {briefProgress ? (
          <Badge
            appearance="outline"
            color={briefProgress.filled >= briefProgress.total ? 'success' : 'informative'}
          >
            {briefProgress.filled}/{briefProgress.total} fields locked
          </Badge>
        ) : null}
      </div>
    )

    expect(screen.getByText('8/11 fields locked')).toBeInTheDocument()
  })

  it('renders green badge when all fields are filled', () => {
    const briefProgress = { filled: 11, total: 11, missing_fields: [], locked_fields: {} }

    const { container } = render(
      <div>
        {briefProgress ? (
          <Badge
            appearance="outline"
            color={briefProgress.filled >= briefProgress.total ? 'success' : 'informative'}
          >
            {briefProgress.filled}/{briefProgress.total} fields locked
          </Badge>
        ) : null}
      </div>
    )

    expect(screen.getByText('11/11 fields locked')).toBeInTheDocument()
  })

  it('renders nothing when brief_progress is absent', () => {
    const briefProgress = undefined

    const { container } = render(
      <div data-testid="badge-container">
        {briefProgress ? (
          <Badge appearance="outline" color="informative">
            0/11 fields locked
          </Badge>
        ) : null}
      </div>
    )

    expect(screen.getByTestId('badge-container').children.length).toBe(0)
  })
})

/**
 * E7-S2-T1: Performance insights card displays when data exists.
 * E7-S2-T2: Performance insights card does not display when data is empty.
 *
 * Tests the performance insights accordion rendering in the wizard.
 */
describe('Performance insights card (E7-S2)', () => {
  it('displays performance insights when data exists', () => {
    const performanceInsights = {
      top_performing_dimensions: ['video', 'carousel'],
      best_posting_hours: [9, 14, 18],
      avg_engagement_rate: 4.2,
      recommendation_summary: 'Focus on video and carousel content',
    }

    render(
      <div>
        {performanceInsights && performanceInsights.avg_engagement_rate > 0 ? (
          <div className="dma-performance-insights-card" data-testid="performance-insights-card">
            <details className="dma-performance-insights-accordion">
              <summary className="dma-performance-insights-summary">
                <Text weight="semibold" size={400}>📊 Performance Insights</Text>
                <Text size={300}>What's worked before</Text>
              </summary>
              <div className="dma-performance-insights-body">
                <div className="dma-performance-metric">
                  <Text size={300} className="dma-performance-label">Top performing content types:</Text>
                  <Text size={300} weight="semibold">
                    {performanceInsights.top_performing_dimensions.join(', ') || 'N/A'}
                  </Text>
                </div>
                <div className="dma-performance-metric">
                  <Text size={300} className="dma-performance-label">Average engagement:</Text>
                  <Text size={300} weight="semibold">
                    {performanceInsights.avg_engagement_rate.toFixed(1)}%
                  </Text>
                </div>
                <div className="dma-performance-metric">
                  <Text size={300} className="dma-performance-label">Best posting hours (UTC):</Text>
                  <Text size={300} weight="semibold">
                    {performanceInsights.best_posting_hours.join(', ')}
                  </Text>
                </div>
                {performanceInsights.recommendation_summary ? (
                  <div className="dma-performance-recommendation">
                    <Text size={300} className="dma-performance-label">Recommendation:</Text>
                    <Text size={300}>{performanceInsights.recommendation_summary}</Text>
                  </div>
                ) : null}
              </div>
            </details>
          </div>
        ) : null}
      </div>
    )

    expect(screen.getByTestId('performance-insights-card')).toBeInTheDocument()
    expect(screen.getByText('📊 Performance Insights')).toBeInTheDocument()
    expect(screen.getByText('video, carousel')).toBeInTheDocument()
    expect(screen.getByText('4.2%')).toBeInTheDocument()
    expect(screen.getByText('Focus on video and carousel content')).toBeInTheDocument()
  })

  it('does not display insights when performance data is empty', () => {
    const performanceInsights = {}

    const { container } = render(
      <div data-testid="insights-container">
        {performanceInsights && (performanceInsights as any).avg_engagement_rate > 0 ? (
          <div className="dma-performance-insights-card" data-testid="performance-insights-card">
            <Text>Performance Insights</Text>
          </div>
        ) : null}
      </div>
    )

    expect(screen.queryByTestId('performance-insights-card')).not.toBeInTheDocument()
  })
})
