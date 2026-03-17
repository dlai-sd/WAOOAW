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
  }
})

vi.mock('../services/hiredAgentStudio.service', () => ({
  getHiredAgentStudio: vi.fn(),
  updateHiredAgentStudio: vi.fn(),
}))

vi.mock('../services/plant.service', () => ({
  plantAPIService: {
    getCatalogAgent: vi.fn(async () => null)
  }
}))

vi.mock('../services/youtubeConnections.service', () => ({
  startYouTubeConnection: vi.fn(),
  finalizeYouTubeConnection: vi.fn(),
  listYouTubeConnections: vi.fn(async () => []),
  getYouTubeConnection: vi.fn(),
  attachYouTubeConnection: vi.fn(),
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
    const studioSvc = await import('../services/hiredAgentStudio.service')
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
    vi.mocked(studioSvc.getHiredAgentStudio).mockResolvedValueOnce({
      hired_instance_id: 'HAI-1',
      subscription_id: 'SUB-1',
      agent_id: 'agent-1',
      agent_type_id: 'marketing.digital_marketing.v1',
      mode: 'activation',
      selection_required: false,
      current_step: 'identity',
      steps: [],
      identity: { nickname: null, theme: null, complete: false },
      connection: { status: 'missing', complete: false, summary: 'Missing connection' },
      operating_plan: { complete: false, goals_completed: false, goal_count: 0, skill_config_count: 0, summary: 'Missing operating plan' },
      review: { complete: false, summary: 'Missing steps' },
      configured: false,
      goals_completed: false,
      trial_status: 'not_started',
      subscription_status: 'active',
      updated_at: '2026-03-17T00:00:00Z',
    } as any)

    renderWizard('/hire/setup/SUB-1?agentId=agent-1')

    await waitFor(() => {
      expect(screen.getByText('Step 1 of 4')).toBeInTheDocument()
    })
    expect(screen.getByTestId('cp-hire-setup-nickname')).toBeInTheDocument()
  })

  it('resumes at step 3 when configured but not yet reviewed', async () => {
    const svc = await import('../services/hireWizard.service')
    const studioSvc = await import('../services/hiredAgentStudio.service')
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
    vi.mocked(studioSvc.getHiredAgentStudio).mockResolvedValueOnce({
      hired_instance_id: 'HAI-2',
      subscription_id: 'SUB-2',
      agent_id: 'agent-2',
      agent_type_id: 'marketing.digital_marketing.v1',
      mode: 'activation',
      selection_required: false,
      current_step: 'connection',
      steps: [],
      identity: { nickname: 'Growth Copilot', theme: 'dark', complete: true },
      connection: { status: 'missing', complete: false, summary: 'Missing connection' },
      operating_plan: { complete: false, goals_completed: false, goal_count: 0, skill_config_count: 0, summary: 'Missing operating plan' },
      review: { complete: false, summary: 'Missing steps' },
      configured: true,
      goals_completed: false,
      trial_status: 'not_started',
      subscription_status: 'active',
      updated_at: '2026-03-17T00:00:00Z',
    } as any)

    renderWizard('/hire/setup/SUB-2?agentId=agent-2')

    await waitFor(() => {
      expect(screen.getByText('Step 3 of 4')).toBeInTheDocument()
    })
    expect(screen.getByTestId('cp-hire-setup-config-json')).toBeInTheDocument()
  })

  it('resumes at step 4 when goals already completed', async () => {
    const svc = await import('../services/hireWizard.service')
    const studioSvc = await import('../services/hiredAgentStudio.service')
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
    vi.mocked(studioSvc.getHiredAgentStudio).mockResolvedValueOnce({
      hired_instance_id: 'HAI-3',
      subscription_id: 'SUB-3',
      agent_id: 'agent-3',
      agent_type_id: 'marketing.digital_marketing.v1',
      mode: 'activation',
      selection_required: false,
      current_step: 'review',
      steps: [],
      identity: { nickname: 'Ops Copilot', theme: 'light', complete: true },
      connection: { status: 'connected', complete: true, summary: 'Ready' },
      operating_plan: { complete: true, goals_completed: true, goal_count: 0, skill_config_count: 1, summary: 'Ready' },
      review: { complete: true, summary: 'Ready to start the trial.' },
      configured: true,
      goals_completed: true,
      trial_status: 'not_started',
      subscription_status: 'active',
      updated_at: '2026-03-17T00:00:00Z',
    } as any)

    renderWizard('/hire/setup/SUB-3?agentId=agent-3')

    await waitFor(() => {
      expect(screen.getByText('Step 4 of 4')).toBeInTheDocument()
    })
    expect(screen.getByText(/Review your setup and activate trial\./i)).toBeInTheDocument()
  })

  it('supports direct entry into the YouTube connection stage', async () => {
    const svc = await import('../services/hireWizard.service')
    const studioSvc = await import('../services/hiredAgentStudio.service')
    vi.mocked(svc.getHireWizardDraftBySubscription).mockResolvedValueOnce({
      hired_instance_id: 'HAI-4',
      subscription_id: 'SUB-4',
      agent_id: 'AGT-MKT-DMA-001',
      agent_type_id: 'marketing.digital_marketing.v1',
      nickname: 'Channel Copilot',
      theme: 'default',
      config: {},
      configured: false,
      goals_completed: false,
      trial_status: 'not_started',
      trial_start_at: null,
      trial_end_at: null
    } as any)
    vi.mocked(studioSvc.getHiredAgentStudio).mockResolvedValueOnce({
      hired_instance_id: 'HAI-4',
      subscription_id: 'SUB-4',
      agent_id: 'AGT-MKT-DMA-001',
      agent_type_id: 'marketing.digital_marketing.v1',
      mode: 'activation',
      selection_required: false,
      current_step: 'connection',
      steps: [],
      identity: { nickname: 'Channel Copilot', theme: 'default', complete: true },
      connection: { platform_key: 'youtube', skill_id: 'default', status: 'missing', complete: false, summary: 'Missing connection' },
      operating_plan: { complete: false, goals_completed: false, goal_count: 0, skill_config_count: 0, summary: 'Missing operating plan' },
      review: { complete: false, summary: 'Missing steps' },
      configured: false,
      goals_completed: false,
      trial_status: 'not_started',
      subscription_status: 'active',
      updated_at: '2026-03-17T00:00:00Z',
    } as any)

    renderWizard('/hire/setup/SUB-4?agentId=AGT-MKT-DMA-001&stage=youtube')

    await waitFor(() => {
      expect(screen.getByText('Step 3 of 4')).toBeInTheDocument()
    })
    expect(screen.getByTestId('cp-hire-setup-platform')).toBeInTheDocument()
  })

  it('shows marketing platform connection UI at step 3 for marketing agents', async () => {
    const svc = await import('../services/hireWizard.service')
    const studioSvc = await import('../services/hiredAgentStudio.service')
    const plantSvc = await import('../services/plant.service')
    const youtubeSvc = await import('../services/youtubeConnections.service')
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
    vi.mocked(studioSvc.getHiredAgentStudio).mockResolvedValueOnce({
      hired_instance_id: 'HAI-4',
      subscription_id: 'SUB-4',
      agent_id: 'AGENT-CATALOG-123',
      agent_type_id: 'marketing.digital_marketing.v1',
      mode: 'activation',
      selection_required: false,
      current_step: 'connection',
      steps: [],
      identity: { nickname: 'Clinic Marketer', theme: 'dark', complete: true },
      connection: { platform_key: 'youtube', skill_id: 'default', status: 'missing', complete: false, summary: 'Missing connection' },
      operating_plan: { complete: false, goals_completed: false, goal_count: 0, skill_config_count: 0, summary: 'Missing operating plan' },
      review: { complete: false, summary: 'Missing steps' },
      configured: true,
      goals_completed: false,
      trial_status: 'not_started',
      subscription_status: 'active',
      updated_at: '2026-03-17T00:00:00Z',
    } as any)
    vi.mocked(youtubeSvc.listYouTubeConnections).mockResolvedValueOnce([
      {
        id: 'cred-yt-1',
        customer_id: 'CUST-1',
        platform_key: 'youtube',
        display_name: 'WAOOAW Channel',
        granted_scopes: ['youtube.readonly'],
        verification_status: 'verified',
        connection_status: 'connected',
        created_at: '2026-03-16T10:00:00Z',
        updated_at: '2026-03-16T10:00:00Z',
      } as any,
    ])

    renderWizard('/hire/setup/SUB-4?agentId=AGENT-CATALOG-123&agentTypeId=marketing.digital_marketing.v1&catalogVersion=v1')

    await waitFor(() => {
      expect(screen.getByText('Step 3 of 4')).toBeInTheDocument()
    })
    expect(screen.getByText(/Connect your marketing platforms/i)).toBeInTheDocument()
    expect(screen.getByTestId('cp-hire-setup-youtube-connect-button')).toBeInTheDocument()
    expect(screen.queryByTestId('cp-hire-setup-access-token')).not.toBeInTheDocument()
    expect(screen.getByText(/WAOOAW Channel/i)).toBeInTheDocument()
  })

  it('activates through the studio review patch', async () => {
    const svc = await import('../services/hireWizard.service')
    const studioSvc = await import('../services/hiredAgentStudio.service')

    vi.mocked(svc.getHireWizardDraftBySubscription).mockResolvedValueOnce({
      hired_instance_id: 'HAI-5',
      subscription_id: 'SUB-5',
      agent_id: 'agent-5',
      agent_type_id: 'operations.general.v1',
      nickname: 'Growth Copilot',
      theme: 'default',
      config: {},
      configured: true,
      goals_completed: true,
      trial_status: 'not_started',
      trial_start_at: null,
      trial_end_at: null,
    } as any)
    vi.mocked(studioSvc.getHiredAgentStudio).mockResolvedValueOnce({
      hired_instance_id: 'HAI-5',
      subscription_id: 'SUB-5',
      agent_id: 'agent-5',
      agent_type_id: 'operations.general.v1',
      mode: 'activation',
      selection_required: false,
      current_step: 'review',
      steps: [],
      identity: { nickname: 'Growth Copilot', theme: 'default', complete: true },
      connection: { status: 'connected', complete: true, summary: 'Ready' },
      operating_plan: { complete: true, goals_completed: true, goal_count: 0, skill_config_count: 1, summary: 'Ready' },
      review: { complete: true, summary: 'Ready to start the trial.' },
      configured: true,
      goals_completed: true,
      trial_status: 'not_started',
      subscription_status: 'active',
      updated_at: '2026-03-17T00:00:00Z',
    } as any)
    vi.mocked(svc.upsertHireWizardDraft).mockResolvedValueOnce({
      hired_instance_id: 'HAI-5',
      subscription_id: 'SUB-5',
      agent_id: 'agent-5',
      agent_type_id: 'operations.general.v1',
      nickname: 'Growth Copilot',
      theme: 'default',
      config: {},
      configured: true,
      goals_completed: true,
      trial_status: 'not_started',
      trial_start_at: null,
      trial_end_at: null,
    } as any)
    vi.mocked(studioSvc.updateHiredAgentStudio)
      .mockResolvedValueOnce({
        hired_instance_id: 'HAI-5',
        subscription_id: 'SUB-5',
        agent_id: 'agent-5',
        agent_type_id: 'operations.general.v1',
        mode: 'activation',
        selection_required: false,
        current_step: 'review',
        steps: [],
        identity: { nickname: 'Growth Copilot', theme: 'default', complete: true },
        connection: { status: 'connected', complete: true, summary: 'Ready' },
        operating_plan: { complete: true, goals_completed: true, goal_count: 0, skill_config_count: 1, summary: 'Ready' },
        review: { complete: true, summary: 'Ready to start the trial.' },
        configured: true,
        goals_completed: true,
        trial_status: 'not_started',
        subscription_status: 'active',
        updated_at: '2026-03-17T00:00:00Z',
      } as any)
      .mockResolvedValueOnce({
        hired_instance_id: 'HAI-5',
        subscription_id: 'SUB-5',
        agent_id: 'agent-5',
        agent_type_id: 'operations.general.v1',
        mode: 'edit',
        selection_required: false,
        current_step: 'review',
        steps: [],
        identity: { nickname: 'Growth Copilot', theme: 'default', complete: true },
        connection: { status: 'connected', complete: true, summary: 'Ready' },
        operating_plan: { complete: true, goals_completed: true, goal_count: 0, skill_config_count: 1, summary: 'Ready' },
        review: { complete: true, summary: 'Ready to save the updated configuration.' },
        configured: true,
        goals_completed: true,
        trial_status: 'active',
        subscription_status: 'active',
        updated_at: '2026-03-17T00:00:01Z',
      } as any)

    renderWizard('/hire/setup/SUB-5?agentId=agent-5&agentTypeId=operations.general.v1')

    await waitFor(() => {
      expect(screen.getByText('Step 4 of 4')).toBeInTheDocument()
    })

    screen.getByTestId('cp-hire-setup-activate').click()

    await waitFor(() => {
      expect(studioSvc.updateHiredAgentStudio).toHaveBeenLastCalledWith('HAI-5', {
        review: {
          goals_completed: true,
          finalize: true,
        },
      })
    })
  })
})
