import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { FluentProvider } from '@fluentui/react-components'
import { MemoryRouter, Routes, Route } from 'react-router-dom'

import { waooawLightTheme } from '../theme'
import HireSetupWizard from '../pages/HireSetupWizard'
import {
  clearYouTubeOAuthResult,
  storeYouTubeOAuthResult,
} from '../utils/youtubeOAuthFlow'

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
    clearYouTubeOAuthResult()
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
    expect(screen.getByText(/Connect the channel once, confirm the verified account/i)).toBeInTheDocument()
    expect(screen.getByTestId('cp-hire-setup-youtube-connect-button')).toBeInTheDocument()
    expect(screen.queryByTestId('cp-hire-setup-access-token')).not.toBeInTheDocument()
    expect(screen.getByText(/WAOOAW Channel/i)).toBeInTheDocument()
  })

  it('honors an explicit step query param for reconnect flows', async () => {
    const svc = await import('../services/hireWizard.service')
    vi.mocked(svc.getHireWizardDraftBySubscription).mockResolvedValueOnce({
      hired_instance_id: 'HAI-5',
      subscription_id: 'SUB-5',
      agent_id: 'agent-5',
      nickname: 'Ops Copilot',
      theme: 'dark',
      config: {},
      configured: true,
      goals_completed: true,
      trial_status: 'active',
      trial_start_at: null,
      trial_end_at: null,
    } as any)

    renderWizard('/hire/setup/SUB-5?agentId=agent-5&step=3')

    await waitFor(() => {
      expect(screen.getByText('Step 3 of 4')).toBeInTheDocument()
    })
  })

  it('review action opens identity setup from step 4', async () => {
    const svc = await import('../services/hireWizard.service')
    vi.mocked(svc.getHireWizardDraftBySubscription).mockResolvedValueOnce({
      hired_instance_id: 'HAI-5B',
      subscription_id: 'SUB-5B',
      agent_id: 'agent-5b',
      nickname: 'Ops Copilot',
      theme: 'dark',
      config: {},
      configured: true,
      goals_completed: true,
      trial_status: 'active',
      trial_start_at: null,
      trial_end_at: null,
    } as any)

    renderWizard('/hire/setup/SUB-5B?agentId=agent-5b')

    await waitFor(() => {
      expect(screen.getByText('Step 4 of 4')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByTestId('cp-hire-setup-review-action-1'))

    await waitFor(() => {
      expect(screen.getByText('Step 1 of 4')).toBeInTheDocument()
    })
    expect(screen.getByTestId('cp-hire-setup-nickname')).toBeInTheDocument()
  })

  it('clearing a YouTube selection removes stale readiness and disables continue', async () => {
    const svc = await import('../services/hireWizard.service')
    const plantSvc = await import('../services/plant.service')
    const youtubeSvc = await import('../services/youtubeConnections.service')

    vi.mocked(plantSvc.plantAPIService.getCatalogAgent).mockResolvedValueOnce({
      release_id: 'CAR-2',
      id: 'AGENT-CATALOG-456',
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
    } as any)
    vi.mocked(svc.getHireWizardDraftBySubscription).mockResolvedValueOnce({
      hired_instance_id: 'HAI-6',
      subscription_id: 'SUB-6',
      agent_id: 'AGENT-CATALOG-456',
      agent_type_id: 'marketing.digital_marketing.v1',
      nickname: 'Clinic Marketer',
      theme: 'dark',
      config: {
        platforms: [
          {
            platform: 'youtube',
            customer_platform_credential_id: 'cred-yt-6',
            display_name: 'WAOOAW Studio',
          },
        ],
      },
      configured: true,
      goals_completed: false,
      trial_status: 'not_started',
      trial_start_at: null,
      trial_end_at: null,
    } as any)
    vi.mocked(youtubeSvc.listYouTubeConnections).mockResolvedValue([
      {
        id: 'cred-yt-6',
        customer_id: 'CUST-6',
        platform_key: 'youtube',
        display_name: 'WAOOAW Studio',
        granted_scopes: ['youtube.upload'],
        verification_status: 'verified',
        connection_status: 'connected',
        created_at: '2026-03-16T10:00:00Z',
        updated_at: '2026-03-16T10:00:00Z',
      } as any,
    ])

    renderWizard('/hire/setup/SUB-6?agentId=AGENT-CATALOG-456&agentTypeId=marketing.digital_marketing.v1&step=3&focus=youtube')

    await waitFor(() => {
      expect(screen.getByText('Step 3 of 4')).toBeInTheDocument()
    })

    await waitFor(() => {
      expect(screen.getByTestId('cp-hire-setup-next')).not.toBeDisabled()
    })

    fireEvent.click(screen.getByTestId('cp-hire-setup-youtube-clear-selection'))

    await waitFor(() => {
      expect(screen.getByTestId('cp-hire-setup-next')).toBeDisabled()
    })
  })

  it('blocks continue when a saved YouTube connection now requires reconnect', async () => {
    const svc = await import('../services/hireWizard.service')
    const plantSvc = await import('../services/plant.service')
    const youtubeSvc = await import('../services/youtubeConnections.service')

    vi.mocked(plantSvc.plantAPIService.getCatalogAgent).mockResolvedValueOnce({
      release_id: 'CAR-7',
      id: 'AGENT-CATALOG-777',
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
    } as any)
    vi.mocked(svc.getHireWizardDraftBySubscription).mockResolvedValueOnce({
      hired_instance_id: 'HAI-7',
      subscription_id: 'SUB-7',
      agent_id: 'AGENT-CATALOG-777',
      agent_type_id: 'marketing.digital_marketing.v1',
      nickname: 'Clinic Marketer',
      theme: 'dark',
      config: {
        platforms: [
          {
            platform: 'youtube',
            customer_platform_credential_id: 'cred-yt-7',
            display_name: 'WAOOAW Studio',
          },
        ],
      },
      configured: true,
      goals_completed: false,
      trial_status: 'not_started',
      trial_start_at: null,
      trial_end_at: null,
    } as any)
    vi.mocked(youtubeSvc.listYouTubeConnections).mockResolvedValue([
      {
        id: 'cred-yt-7',
        customer_id: 'CUST-7',
        platform_key: 'youtube',
        display_name: 'WAOOAW Studio',
        granted_scopes: ['youtube.upload'],
        verification_status: 'verified',
        connection_status: 'reconnect_required',
        created_at: '2026-03-16T10:00:00Z',
        updated_at: '2026-03-16T10:00:00Z',
      } as any,
    ])

    renderWizard('/hire/setup/SUB-7?agentId=AGENT-CATALOG-777&agentTypeId=marketing.digital_marketing.v1&step=3&focus=youtube')

    await waitFor(() => {
      expect(screen.getByText('Step 3 of 4')).toBeInTheDocument()
    })

    await waitFor(() => {
      expect(screen.getByTestId('cp-hire-setup-next')).toBeDisabled()
    })
    expect(screen.getByText(/needs to be reconnected before continuing/i)).toBeInTheDocument()
  })

  it('hydrates YouTube success state after returning from the callback route', async () => {
    const svc = await import('../services/hireWizard.service')
    const plantSvc = await import('../services/plant.service')

    vi.mocked(plantSvc.plantAPIService.getCatalogAgent).mockResolvedValueOnce({
      release_id: 'CAR-CB-1',
      id: 'AGENT-CB-001',
      public_name: 'Digital Marketing Agent',
      short_description: 'Hire-ready',
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
    } as any)
    vi.mocked(svc.getHireWizardDraftBySubscription).mockResolvedValueOnce({
      hired_instance_id: 'HAI-CB-1',
      subscription_id: 'SUB-CB-1',
      agent_id: 'AGENT-CB-001',
      agent_type_id: 'marketing.digital_marketing.v1',
      nickname: 'Clinic Marketer',
      theme: 'dark',
      config: { platforms: [] },
      configured: false,
      goals_completed: false,
      trial_status: 'not_started',
      trial_start_at: null,
      trial_end_at: null,
    } as any)

    const finalizedCredential = {
      id: 'cred-cb-001',
      customer_id: 'CUST-CB-1',
      platform_key: 'youtube',
      display_name: 'Callback Channel',
      granted_scopes: ['youtube.upload'],
      verification_status: 'verified',
      connection_status: 'connected',
      created_at: '2026-03-25T10:00:00Z',
      updated_at: '2026-03-25T10:00:00Z',
    } as any

    storeYouTubeOAuthResult({
      source: 'hire-setup',
      returnTo: '/hire/setup/SUB-CB-1?agentId=AGENT-CB-001&agentTypeId=marketing.digital_marketing.v1&step=3&focus=youtube',
      subscriptionId: 'SUB-CB-1',
      connection: finalizedCredential,
      message: 'Connected Callback Channel',
    })

    renderWizard(
      '/hire/setup/SUB-CB-1?agentId=AGENT-CB-001&agentTypeId=marketing.digital_marketing.v1&step=3&focus=youtube'
    )

    await waitFor(() => {
      expect(screen.getByText('Step 3 of 4')).toBeInTheDocument()
    })

    await waitFor(() => {
      expect(screen.getByText(/Connected Callback Channel/i)).toBeInTheDocument()
    })
  })

  it('save-and-continue calls attachYouTubeConnection when a connected credential is selected', async () => {
    const svc = await import('../services/hireWizard.service')
    const plantSvc = await import('../services/plant.service')
    const youtubeSvc = await import('../services/youtubeConnections.service')

    vi.mocked(plantSvc.plantAPIService.getCatalogAgent).mockResolvedValueOnce({
      release_id: 'CAR-ATT-1',
      id: 'AGENT-ATT-001',
      public_name: 'Digital Marketing Agent',
      short_description: 'Hire-ready',
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
    } as any)
    vi.mocked(svc.getHireWizardDraftBySubscription).mockResolvedValueOnce({
      hired_instance_id: 'HAI-ATT-1',
      subscription_id: 'SUB-ATT-1',
      agent_id: 'AGENT-ATT-001',
      agent_type_id: 'marketing.digital_marketing.v1',
      nickname: 'Attach Tester',
      theme: 'dark',
      config: {
        platforms: [
          {
            platform: 'youtube',
            customer_platform_credential_id: 'cred-att-001',
            display_name: 'Attach Channel',
          },
        ],
      },
      configured: true,
      goals_completed: false,
      trial_status: 'not_started',
      trial_start_at: null,
      trial_end_at: null,
    } as any)
    vi.mocked(youtubeSvc.listYouTubeConnections).mockResolvedValue([
      {
        id: 'cred-att-001',
        customer_id: 'CUST-ATT-1',
        platform_key: 'youtube',
        display_name: 'Attach Channel',
        granted_scopes: ['youtube.upload'],
        verification_status: 'verified',
        connection_status: 'connected',
        created_at: '2026-03-25T10:00:00Z',
        updated_at: '2026-03-25T10:00:00Z',
      } as any,
    ])

    vi.mocked(svc.upsertHireWizardDraft).mockResolvedValue({
      hired_instance_id: 'HAI-ATT-1',
      subscription_id: 'SUB-ATT-1',
      agent_id: 'AGENT-ATT-001',
      agent_type_id: 'marketing.digital_marketing.v1',
      nickname: 'Attach Tester',
      theme: 'dark',
      config: {},
      configured: true,
      goals_completed: false,
      trial_status: 'not_started',
      trial_start_at: null,
      trial_end_at: null,
    } as any)

    vi.mocked(youtubeSvc.attachYouTubeConnection).mockResolvedValue({
      id: 'conn-att-001',
      hired_instance_id: 'HAI-ATT-1',
      skill_id: 'default',
      customer_platform_credential_id: 'cred-att-001',
      platform_key: 'youtube',
      status: 'connected',
      connected_at: '2026-03-18T09:00:00Z',
      last_verified_at: '2026-03-18T09:00:00Z',
      created_at: '2026-03-18T09:00:00Z',
      updated_at: '2026-03-18T09:00:00Z',
    })

    renderWizard(
      '/hire/setup/SUB-ATT-1?agentId=AGENT-ATT-001&agentTypeId=marketing.digital_marketing.v1&step=3&focus=youtube'
    )

    await waitFor(() => {
      expect(screen.getByText('Step 3 of 4')).toBeInTheDocument()
    })

    await waitFor(() => {
      expect(screen.getByTestId('cp-hire-setup-next')).not.toBeDisabled()
    })

    fireEvent.click(screen.getByTestId('cp-hire-setup-next'))

    await waitFor(() => {
      expect(youtubeSvc.attachYouTubeConnection).toHaveBeenCalledWith(
        'cred-att-001',
        expect.objectContaining({ hired_instance_id: 'HAI-ATT-1', skill_id: 'default', platform_key: 'youtube' })
      )
    })
  })

  it('does not call attachYouTubeConnection when no YouTube credential is selected', async () => {
    const svc = await import('../services/hireWizard.service')
    const youtubeSvc = await import('../services/youtubeConnections.service')

    vi.mocked(svc.getHireWizardDraftBySubscription).mockResolvedValueOnce({
      hired_instance_id: 'HAI-NOATT-1',
      subscription_id: 'SUB-NOATT-1',
      agent_id: 'agent-noatt-1',
      nickname: 'No Attach',
      theme: 'dark',
      config: {},
      configured: true,
      goals_completed: true,
      trial_status: 'active',
      trial_start_at: null,
      trial_end_at: null,
    } as any)

    vi.mocked(svc.upsertHireWizardDraft).mockResolvedValue({
      hired_instance_id: 'HAI-NOATT-1',
      subscription_id: 'SUB-NOATT-1',
      agent_id: 'agent-noatt-1',
      nickname: 'No Attach',
      theme: 'dark',
      config: {},
      configured: true,
      goals_completed: true,
      trial_status: 'active',
      trial_start_at: null,
      trial_end_at: null,
    } as any)

    vi.mocked(svc.finalizeHireWizard).mockResolvedValue({
      hired_instance_id: 'HAI-NOATT-1',
      subscription_id: 'SUB-NOATT-1',
      agent_id: 'agent-noatt-1',
      nickname: 'No Attach',
      theme: 'dark',
      config: {},
      configured: true,
      goals_completed: true,
      trial_status: 'active',
      trial_start_at: null,
      trial_end_at: null,
    } as any)

    renderWizard('/hire/setup/SUB-NOATT-1?agentId=agent-noatt-1&step=4')

    await waitFor(() => {
      expect(screen.getByText('Step 4 of 4')).toBeInTheDocument()
    })

    // goalsCompleted is already true from the loaded draft — button is enabled
    await waitFor(() => {
      expect(screen.getByTestId('cp-hire-setup-activate')).not.toBeDisabled()
    })

    fireEvent.click(screen.getByTestId('cp-hire-setup-activate'))

    await waitFor(() => {
      expect(svc.finalizeHireWizard).toHaveBeenCalled()
    })

    expect(youtubeSvc.attachYouTubeConnection).not.toHaveBeenCalled()
  })
})
