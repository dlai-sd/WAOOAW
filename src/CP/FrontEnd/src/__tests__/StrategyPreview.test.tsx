import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'

import { StrategyPreviewPanel } from '../components/DigitalMarketingActivationWizard'

describe('StrategyPreviewPanel', () => {
  it('renders the strategy summary when approval is pending', () => {
    render(
      <StrategyPreviewPanel
        isThemeApproved={false}
        strategySummary="Focus on video content for trust-building."
        messages={[{ role: 'assistant', content: 'Lead with educational videos.' }]}
      />
    )

    expect(screen.getByText('Review your content strategy before approving')).toBeInTheDocument()
    expect(screen.getByText('Focus on video content for trust-building.')).toBeInTheDocument()
  })

  it('renders the empty placeholder when no strategy exists', () => {
    render(
      <StrategyPreviewPanel
        isThemeApproved={false}
        strategySummary=""
        messages={[]}
      />
    )

    expect(screen.getByText(/No strategy generated yet/i)).toBeInTheDocument()
  })

  it('hides itself after approval', () => {
    const { container } = render(
      <StrategyPreviewPanel
        isThemeApproved
        strategySummary="Focus on video content for trust-building."
        messages={[{ role: 'assistant', content: 'Lead with educational videos.' }]}
      />
    )

    expect(container.firstChild).toBeNull()
  })
})
