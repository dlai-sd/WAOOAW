import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { FluentProvider } from '@fluentui/react-components'
import { MemoryRouter, Routes, Route } from 'react-router-dom'

import { waooawLightTheme } from '../theme'
import HireSetupWizard from '../pages/HireSetupWizard'

vi.mock('../services/hireWizard.service', () => {
  return {
    getHireWizardDraftBySubscription: vi.fn(),
    upsertHireWizardDraft: vi.fn(),
    finalizeHireWizard: vi.fn()
  }
})

vi.mock('../services/plant.service', () => ({
  plantAPIService: {
    getCatalogAgent: vi.fn(async () => null)
  }
}))

const renderWizard = (initialEntry: string) => {
  return render(
    <FluentProvider theme={waooawLightTheme}>
      <MemoryRouter initialEntries={[initialEntry]}>
        <Routes>
          <Route path="/hire/setup/:subscriptionId" element={<HireSetupWizard />} />
        </Routes>
      </MemoryRouter>
    </FluentProvider>
  )
}

describe('HireSetupWizard (HIRE-3.1)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('resumes at step 1 when nickname missing', async () => {
    const svc = await import('../services/hireWizard.service')
    vi.mocked(svc.getHireWizardDraftBySubscription).mockResolvedValueOnce({
      hired_instance_id: 'HAI-1',
      subscription_id: 'SUB-1',
      agent_id: 'agent-1',
      nickname: null,
      theme: null,
      config: {},
      configured: false,
      goals_completed: false,
      trial_status: 'not_started',
      trial_start_at: null,
      trial_end_at: null
    } as any)

    renderWizard('/hire/setup/SUB-1?agentId=agent-1')

    await waitFor(() => {
      expect(screen.getByText('Step 1 of 4')).toBeInTheDocument()
    })
    expect(screen.getByTestId('cp-hire-setup-nickname')).toBeInTheDocument()
  })

  it('resumes at step 3 when configured but not yet reviewed', async () => {
    const svc = await import('../services/hireWizard.service')
    vi.mocked(svc.getHireWizardDraftBySubscription).mockResolvedValueOnce({
      hired_instance_id: 'HAI-2',
      subscription_id: 'SUB-2',
      agent_id: 'agent-2',
      nickname: 'Growth Copilot',
      theme: 'dark',
      config: {},
      configured: true,
      goals_completed: false,
      trial_status: 'not_started',
      trial_start_at: null,
      trial_end_at: null
    } as any)

    renderWizard('/hire/setup/SUB-2?agentId=agent-2')

    await waitFor(() => {
      expect(screen.getByText('Step 3 of 4')).toBeInTheDocument()
    })
    expect(screen.getByTestId('cp-hire-setup-config-json')).toBeInTheDocument()
  })

  it('resumes at step 4 when goals already completed', async () => {
    const svc = await import('../services/hireWizard.service')
    vi.mocked(svc.getHireWizardDraftBySubscription).mockResolvedValueOnce({
      hired_instance_id: 'HAI-3',
      subscription_id: 'SUB-3',
      agent_id: 'agent-3',
      nickname: 'Ops Copilot',
      theme: 'light',
      config: { a: 1 },
      configured: true,
      goals_completed: true,
      trial_status: 'not_started',
      trial_start_at: null,
      trial_end_at: null
    } as any)

    renderWizard('/hire/setup/SUB-3?agentId=agent-3')

    await waitFor(() => {
      expect(screen.getByText('Step 4 of 4')).toBeInTheDocument()
    })
    expect(screen.getByText(/Review your setup and activate trial\./i)).toBeInTheDocument()
  })

  it('shows marketing platform connection UI at step 3 for marketing agents', async () => {
    const svc = await import('../services/hireWizard.service')
    const plantSvc = await import('../services/plant.service')
    vi.mocked(plantSvc.plantAPIService.getCatalogAgent).mockResolvedValueOnce({
      release_id: 'CAR-1',
      id: 'AGENT-CATALOG-123',
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
      retired_from_catalog_at: null
    } as any)
    vi.mocked(svc.getHireWizardDraftBySubscription).mockResolvedValueOnce({
      hired_instance_id: 'HAI-4',
      subscription_id: 'SUB-4',
      agent_id: 'AGENT-CATALOG-123',
      agent_type_id: 'marketing.digital_marketing.v1',
      nickname: 'Clinic Marketer',
      theme: 'dark',
      config: { platforms: [{ platform: 'instagram', credential_ref: 'CRED-1' }] },
      configured: true,
      goals_completed: false,
      trial_status: 'not_started',
      trial_start_at: null,
      trial_end_at: null
    } as any)

    renderWizard('/hire/setup/SUB-4?agentId=AGENT-CATALOG-123&agentTypeId=marketing.digital_marketing.v1&catalogVersion=v1')

    await waitFor(() => {
      expect(screen.getByText('Step 3 of 4')).toBeInTheDocument()
    })
    expect(screen.getByText(/Connect your marketing platforms/i)).toBeInTheDocument()
    expect(screen.getByTestId('cp-hire-setup-access-token')).toBeInTheDocument()
  })
})
