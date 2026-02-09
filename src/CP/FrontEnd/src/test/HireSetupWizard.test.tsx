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
    expect(screen.getByText('Agent nickname')).toBeInTheDocument()
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
    expect(screen.getByText('Agent-specific configuration (JSON)')).toBeInTheDocument()
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
    vi.mocked(svc.getHireWizardDraftBySubscription).mockResolvedValueOnce({
      hired_instance_id: 'HAI-4',
      subscription_id: 'SUB-4',
      agent_id: 'AGT-MKT-HEALTH-001',
      nickname: 'Clinic Marketer',
      theme: 'dark',
      config: { platforms: [{ platform: 'instagram', credential_ref: 'CRED-1' }] },
      configured: true,
      goals_completed: false,
      trial_status: 'not_started',
      trial_start_at: null,
      trial_end_at: null
    } as any)

    renderWizard('/hire/setup/SUB-4?agentId=AGT-MKT-HEALTH-001')

    await waitFor(() => {
      expect(screen.getByText('Step 3 of 4')).toBeInTheDocument()
    })
    expect(screen.getByText(/Connect your marketing platforms/i)).toBeInTheDocument()
    expect(screen.getByText('Access token')).toBeInTheDocument()
  })
})
