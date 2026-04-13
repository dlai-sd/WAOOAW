import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { MemoryRouter } from 'react-router-dom'

import { DigitalMarketingActivationWizard } from '../components/DigitalMarketingActivationWizard'

// Mock the services and hooks
vi.mock('../services/digitalMarketingActivation.service', () => ({
  getDigitalMarketingActivationWorkspace: vi.fn(),
  upsertDigitalMarketingActivationWorkspace: vi.fn(),
  generateThemePlan: vi.fn(),
  updateThemePlan: vi.fn(),
  getActivationReadiness: vi.fn(),
}))

vi.mock('../hooks/useAuth', () => ({
  useAuth: () => ({
    user: { customer_id: 'cust-123' },
    isAuthenticated: true,
  }),
}))

describe('DigitalMarketingActivationWizard', () => {
  it('E2-S1-T2: renders brief progress badge when brief_progress is present', () => {
    const mockWorkspace = {
      hired_instance_id: 'hired-123',
      campaign_setup: {
        strategy_workshop: {
          status: 'discovery',
          assistant_message: 'Let me help you',
          messages: [],
          summary: {},
          brief_progress: {
            filled: 8,
            total: 11,
            missing_fields: ['tone', 'cta', 'youtube_angle'],
            locked_fields: {
              business_background: 'Fitness',
              objective: 'Leads',
              industry: 'Fitness',
              locality: 'Mumbai',
              target_audience: 'Professionals',
              persona: '30-45',
              channel_intent: 'Tips',
              posting_cadence: 'Weekly',
            },
          },
        },
      },
    }

    render(
      <MemoryRouter>
        <DigitalMarketingActivationWizard
          hiredInstanceId="hired-123"
          initialWorkspace={mockWorkspace}
        />
      </MemoryRouter>
    )

    // Check that the badge with text "8/11 fields locked" is in the DOM
    expect(screen.getByText('8/11 fields locked')).toBeInTheDocument()
  })
})
