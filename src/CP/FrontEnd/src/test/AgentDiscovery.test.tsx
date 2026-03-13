import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { FluentProvider } from '@fluentui/react-components'
import { MemoryRouter } from 'react-router-dom'

import { waooawLightTheme } from '../theme'
import AgentDiscovery from '../pages/AgentDiscovery'

vi.mock('../services/plant.service', () => ({
  plantAPIService: {
    listCatalogAgents: vi.fn()
  }
}))

describe('AgentDiscovery catalog lifecycle', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders approved catalog agents with lifecycle and version truth', async () => {
    const service = await import('../services/plant.service')
    vi.mocked(service.plantAPIService.listCatalogAgents).mockResolvedValueOnce([
      {
        release_id: 'CAR-1',
        id: 'AGT-MKT-001',
        public_name: 'Digital Marketing Agent',
        short_description: 'Hire-ready marketing release',
        industry_name: 'Marketing',
        job_role_label: 'Digital Marketer',
        monthly_price_inr: 12000,
        trial_days: 7,
        allowed_durations: ['monthly'],
        supported_channels: ['youtube'],
        approval_mode: 'manual_review',
        agent_type_id: 'marketing.digital_marketing.v1',
        internal_definition_version_id: '1.0.0',
        external_catalog_version: 'v1',
        lifecycle_state: 'live_on_cp',
        approved_for_new_hire: true,
        retired_from_catalog_at: null,
      }
    ] as any)

    render(
      <FluentProvider theme={waooawLightTheme}>
        <MemoryRouter>
          <AgentDiscovery />
        </MemoryRouter>
      </FluentProvider>
    )

    await waitFor(() => {
      expect(screen.getByText('Digital Marketing Agent')).toBeInTheDocument()
    })
    expect(screen.getByText('Live on CP')).toBeInTheDocument()
    expect(screen.getByText('v1')).toBeInTheDocument()
    expect(screen.getByText('₹12,000/mo')).toBeInTheDocument()
  })

  it('filters approved catalog agents by search text', async () => {
    const service = await import('../services/plant.service')
    vi.mocked(service.plantAPIService.listCatalogAgents).mockResolvedValue([
      {
        release_id: 'CAR-1',
        id: 'AGT-MKT-001',
        public_name: 'Digital Marketing Agent',
        short_description: 'Hire-ready marketing release',
        industry_name: 'Marketing',
        job_role_label: 'Digital Marketer',
        monthly_price_inr: 12000,
        trial_days: 7,
        allowed_durations: ['monthly'],
        supported_channels: ['youtube'],
        approval_mode: 'manual_review',
        agent_type_id: 'marketing.digital_marketing.v1',
        internal_definition_version_id: '1.0.0',
        external_catalog_version: 'v1',
        lifecycle_state: 'live_on_cp',
        approved_for_new_hire: true,
        retired_from_catalog_at: null,
      },
      {
        release_id: 'CAR-2',
        id: 'AGT-EDU-001',
        public_name: 'Math Tutor Agent',
        short_description: 'Hire-ready tutoring release',
        industry_name: 'Education',
        job_role_label: 'Tutor',
        monthly_price_inr: 8000,
        trial_days: 7,
        allowed_durations: ['monthly'],
        supported_channels: ['whatsapp'],
        approval_mode: 'manual_review',
        agent_type_id: 'education.math_tutor.v1',
        internal_definition_version_id: '1.0.0',
        external_catalog_version: 'v2',
        lifecycle_state: 'live_on_cp',
        approved_for_new_hire: true,
        retired_from_catalog_at: null,
      }
    ] as any)

    render(
      <FluentProvider theme={waooawLightTheme}>
        <MemoryRouter>
          <AgentDiscovery />
        </MemoryRouter>
      </FluentProvider>
    )

    await waitFor(() => {
      expect(screen.getByText('Digital Marketing Agent')).toBeInTheDocument()
    })

    fireEvent.change(screen.getByTestId('cp-discover-search-input'), {
      target: { value: 'math' }
    })
    fireEvent.click(screen.getByTestId('cp-discover-search-button'))

    await waitFor(() => {
      expect(screen.getByText('Math Tutor Agent')).toBeInTheDocument()
    })
    expect(screen.queryByText('Digital Marketing Agent')).not.toBeInTheDocument()
  })
})