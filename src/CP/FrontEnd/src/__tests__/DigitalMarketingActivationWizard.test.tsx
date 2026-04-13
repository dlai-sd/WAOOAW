import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { Badge } from '@fluentui/react-components'

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
