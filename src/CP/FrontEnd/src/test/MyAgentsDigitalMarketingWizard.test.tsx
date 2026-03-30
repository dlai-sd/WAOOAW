import { FluentProvider } from '@fluentui/react-components'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { describe, expect, it, vi, beforeEach } from 'vitest'
import { MemoryRouter } from 'react-router-dom'

import { DigitalMarketingActivationWizard } from '../components/DigitalMarketingActivationWizard'
import { waooawLightTheme } from '../theme'
import {
  clearPendingYouTubeOAuthContext,
  readPendingYouTubeOAuthContext,
} from '../utils/youtubeOAuthFlow'

vi.mock('../services/digitalMarketingActivation.service', () => ({
  getDigitalMarketingActivationWorkspace: vi.fn(),
  upsertDigitalMarketingActivationWorkspace: vi.fn(),
  generateDigitalMarketingThemePlan: vi.fn(),
  patchDigitalMarketingThemePlan: vi.fn(),
  buildMarketingPlatformBindings: vi.fn(() => ({})),
  getActivationMilestoneCount: vi.fn(() => 2),
  getSelectedMarketingPlatforms: vi.fn((workspace: any) => workspace?.platforms_enabled || []),
  getNextPendingPlatform: (selectedPlatforms: string[], platformSteps: Array<{ platform_key: string; complete: boolean }>) => {
    const completed = new Map(platformSteps.map((step) => [step.platform_key, step.complete]))
    return selectedPlatforms.find((platform) => !completed.get(platform)) || null
  },
}))

vi.mock('../services/hiredAgents.service', () => ({
  getHiredAgentBySubscription: vi.fn().mockResolvedValue({
    subscription_id: 'SUB-1',
    hired_instance_id: 'HAI-1',
    agent_id: 'AGT-MKT-DMA-001',
    agent_type_id: 'marketing.digital_marketing.v1',
    nickname: 'Growth Copilot',
    theme: 'dark',
    config: {},
    configured: false,
    goals_completed: false,
  }),
  upsertHiredAgentDraft: vi.fn(),
}))

vi.mock('../components/PlatformConnectionsPanel', () => ({
  PlatformConnectionsPanel: () => <div>Platform connections panel</div>,
}))

vi.mock('../utils/browserNavigation', () => ({
  redirectTo: vi.fn(),
}))

vi.mock('../services/youtubeConnections.service', () => ({
  listYouTubeConnections: vi.fn().mockResolvedValue([]),
  startYouTubeConnection: vi.fn(),
  finalizeYouTubeConnection: vi.fn(),
  attachYouTubeConnection: vi.fn(),
}))

const mockInstance = {
  subscription_id: 'SUB-1',
  agent_id: 'AGT-MKT-DMA-001',
  agent_type_id: 'marketing.digital_marketing.v1',
  duration: 'monthly',
  status: 'active',
  current_period_start: '2026-03-01T00:00:00Z',
  current_period_end: '2026-04-01T00:00:00Z',
  cancel_at_period_end: false,
  hired_instance_id: 'HAI-1',
  nickname: 'Growth Copilot',
}

const mockInstance2 = {
  subscription_id: 'SUB-2',
  agent_id: 'AGT-MKT-DMA-001',
  agent_type_id: 'marketing.digital_marketing.v1',
  duration: 'monthly',
  status: 'active',
  current_period_start: '2026-03-01T00:00:00Z',
  current_period_end: '2026-04-01T00:00:00Z',
  cancel_at_period_end: false,
  hired_instance_id: 'HAI-2',
  nickname: 'SEO Pilot',
}

const defaultWorkspace = {
  hired_instance_id: 'HAI-1',
  help_visible: false,
  activation_complete: false,
  induction: {
    nickname: 'Growth Copilot',
    theme: 'dark',
    primary_language: 'en',
    timezone: 'Asia/Kolkata',
    brand_name: 'WAOOAW',
    offerings_services: ['Activation'],
    location: 'Pune',
    target_audience: 'Founders',
    notes: '',
  },
  prepare_agent: {
    selected_platforms: [],
    platform_steps: [],
    all_selected_platforms_completed: false,
  },
  campaign_setup: {
    campaign_id: 'CAM-1',
    master_theme: '',
    derived_themes: [],
    schedule: {
      start_date: '',
      posts_per_week: 0,
      preferred_days: [],
      preferred_hours_utc: [],
    },
  },
  updated_at: '2026-03-18T09:00:00Z',
}

// Renders with 1 instance → auto-advances past step 0 to step 1 (Induct Agent)
function renderWizard() {
  return render(
    <MemoryRouter>
      <FluentProvider theme={waooawLightTheme}>
        <DigitalMarketingActivationWizard
          instances={[mockInstance]}
          selectedInstance={mockInstance}
          readOnly={false}
        />
      </FluentProvider>
    </MemoryRouter>
  )
}

async function goToConnectStep() {
  await waitFor(() => {
    expect(screen.getByTestId('dma-step-panel-induct')).toBeInTheDocument()
  })
  fireEvent.click(screen.getByRole('button', { name: 'Continue' }))
  await waitFor(() => {
    expect(screen.getByTestId('dma-step-panel-platforms')).toBeInTheDocument()
  })
  fireEvent.click(screen.getByRole('button', { name: 'Continue' }))
  await waitFor(() => {
    expect(screen.getByTestId('dma-step-panel-connect')).toBeInTheDocument()
  })
}

describe('DMA Activation Wizard — step navigation', () => {
  beforeEach(async () => {
    vi.clearAllMocks()
    sessionStorage.clear()
    clearPendingYouTubeOAuthContext()
    const serviceModule = await import('../services/digitalMarketingActivation.service')
    vi.mocked(serviceModule.getDigitalMarketingActivationWorkspace).mockResolvedValue({
      hired_instance_id: 'HAI-1',
      customer_id: 'CUST-1',
      agent_type_id: 'marketing.digital_marketing.v1',
      workspace: {
        brand_name: 'WAOOAW',
        location: 'Pune',
        primary_language: 'en',
        timezone: 'Asia/Kolkata',
        business_context: '',
        offerings_services: ['Activation'],
        platforms_enabled: ['youtube'],
        campaign_setup: structuredClone(defaultWorkspace).campaign_setup,
      },
      readiness: {
        brief_complete: true,
        youtube_selected: true,
        youtube_connection_ready: true,
        configured: true,
        can_finalize: true,
        missing_requirements: [],
      },
      updated_at: '2026-03-18T09:00:00Z',
    } as any)
    vi.mocked(serviceModule.upsertDigitalMarketingActivationWorkspace).mockResolvedValue({
      hired_instance_id: 'HAI-1',
      customer_id: 'CUST-1',
      agent_type_id: 'marketing.digital_marketing.v1',
      workspace: {
        brand_name: 'WAOOAW',
        location: 'Pune',
        primary_language: 'en',
        timezone: 'Asia/Kolkata',
        business_context: '',
        offerings_services: ['Activation'],
        platforms_enabled: ['youtube'],
        activation_complete: false,
        campaign_setup: structuredClone(defaultWorkspace).campaign_setup,
      },
      readiness: {
        brief_complete: true,
        youtube_selected: true,
        youtube_connection_ready: true,
        configured: true,
        can_finalize: true,
        missing_requirements: [],
      },
      updated_at: '2026-03-18T09:00:00Z',
    } as any)

    const hiredAgentsModule = await import('../services/hiredAgents.service')
    vi.mocked(hiredAgentsModule.upsertHiredAgentDraft).mockResolvedValue({
      subscription_id: 'SUB-1',
      hired_instance_id: 'HAI-1',
      agent_id: 'AGT-MKT-DMA-001',
      agent_type_id: 'marketing.digital_marketing.v1',
      nickname: 'Growth Copilot',
      theme: 'dark',
      config: {},
      configured: true,
      goals_completed: false,
    })

    const ytModule = await import('../services/youtubeConnections.service')
    vi.mocked(ytModule.listYouTubeConnections).mockResolvedValue([])
    vi.mocked(ytModule.attachYouTubeConnection).mockResolvedValue({ status: 'connected' })
  })

  it('renders wizard shell with 7 step buttons', async () => {
    renderWizard()
    await waitFor(() => {
      expect(screen.getByTestId('dma-step-panel-induct')).toBeInTheDocument()
    })
    const stepTitles = ['Select Agent', 'Induct Agent', 'Choose Platforms', 'Connect Platforms', 'Build Master Theme', 'Confirm Schedule', 'Review & Activate']
    for (const title of stepTitles) {
      expect(screen.getAllByText(title).length).toBeGreaterThan(0)
    }
    expect(screen.getByText('Now')).toBeInTheDocument()
  })

  it('starts on step 1 — Induct Agent panel visible (auto-advanced from step 0 with 1 instance)', async () => {
    renderWizard()
    await waitFor(() => {
      expect(screen.getByTestId('dma-step-panel-induct')).toBeInTheDocument()
    })
    expect(screen.getByLabelText('Nickname')).toBeInTheDocument()
  })

  it('Continue button advances to step 2', async () => {
    renderWizard()
    await waitFor(() => {
      expect(screen.getByTestId('dma-step-panel-induct')).toBeInTheDocument()
    })
    fireEvent.click(screen.getByRole('button', { name: 'Continue' }))
    await waitFor(() => {
      expect(screen.getByTestId('dma-step-panel-platforms')).toBeInTheDocument()
    })
  })

  it('Back button goes back from step 2 to step 1', async () => {
    renderWizard()
    await waitFor(() => {
      expect(screen.getByTestId('dma-step-panel-induct')).toBeInTheDocument()
    })
    fireEvent.click(screen.getByRole('button', { name: 'Continue' }))
    await waitFor(() => {
      expect(screen.getByTestId('dma-step-panel-platforms')).toBeInTheDocument()
    })
    fireEvent.click(screen.getByRole('button', { name: 'Back' }))
    await waitFor(() => {
      expect(screen.getByTestId('dma-step-panel-induct')).toBeInTheDocument()
    })
  })

  it('Back button disabled on step 0 (Select Agent)', async () => {
    const onSelectedInstanceChange = vi.fn()
    render(
      <MemoryRouter>
        <FluentProvider theme={waooawLightTheme}>
          <DigitalMarketingActivationWizard
            instances={[mockInstance, mockInstance2]}
            selectedInstance={null}
            readOnly={false}
            onSelectedInstanceChange={onSelectedInstanceChange}
          />
        </FluentProvider>
      </MemoryRouter>
    )
    await waitFor(() => {
      expect(screen.getByTestId('dma-step-panel-select')).toBeInTheDocument()
    })
    expect(screen.getByRole('button', { name: 'Back' })).toBeDisabled()
  })

  it('Activate Agent button visible on step 7', async () => {
    renderWizard()
    await waitFor(() => {
      expect(screen.getByTestId('dma-step-panel-induct')).toBeInTheDocument()
    })
    const reviewActivateBtn = screen.getByText('Review & Activate').closest('button')
    expect(reviewActivateBtn).not.toBeNull()
    fireEvent.click(reviewActivateBtn!)
    await waitFor(() => {
      expect(screen.getByTestId('dma-step-panel-activate')).toBeInTheDocument()
    })
    expect(screen.getByRole('button', { name: 'Activate Agent' })).toBeInTheDocument()
  })

  it('treats a missing activation workspace as a blank wizard state instead of a fatal error', async () => {
    const serviceModule = await import('../services/digitalMarketingActivation.service')
    vi.mocked(serviceModule.getDigitalMarketingActivationWorkspace).mockRejectedValueOnce({ status: 404 })

    renderWizard()

    await waitFor(() => {
      expect(screen.getByTestId('dma-step-panel-induct')).toBeInTheDocument()
    })

    expect(screen.queryByText('Activation unavailable')).not.toBeInTheDocument()
    expect(screen.getByLabelText('Nickname')).toBeInTheDocument()
  })

  it('renders Step 0 agent select panel when instances provided', async () => {
    const onSelectedInstanceChange = vi.fn()
    render(
      <MemoryRouter>
        <FluentProvider theme={waooawLightTheme}>
          <DigitalMarketingActivationWizard
            instances={[mockInstance, mockInstance2]}
            selectedInstance={null}
            readOnly={false}
            onSelectedInstanceChange={onSelectedInstanceChange}
          />
        </FluentProvider>
      </MemoryRouter>
    )
    await waitFor(() => {
      expect(screen.getByTestId('dma-step-panel-select')).toBeInTheDocument()
    })
    expect(screen.getByText('Growth Copilot')).toBeInTheDocument()
    expect(screen.getByText('SEO Pilot')).toBeInTheDocument()
    fireEvent.click(screen.getByText('Growth Copilot').closest('button')!)
    expect(onSelectedInstanceChange).toHaveBeenCalledWith('SUB-1')
    await waitFor(() => {
      expect(screen.queryByTestId('dma-step-panel-select')).not.toBeInTheDocument()
    })
  })

  it('does not advance and requests refresh when save hits a stale hire reference', async () => {
    const serviceModule = await import('../services/digitalMarketingActivation.service')
    vi.mocked(serviceModule.upsertDigitalMarketingActivationWorkspace).mockRejectedValueOnce({ status: 404 })
    const onStaleReference = vi.fn()

    render(
      <MemoryRouter>
        <FluentProvider theme={waooawLightTheme}>
          <DigitalMarketingActivationWizard
            instances={[mockInstance]}
            selectedInstance={mockInstance}
            readOnly={false}
            onStaleReference={onStaleReference}
          />
        </FluentProvider>
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByTestId('dma-step-panel-induct')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByRole('button', { name: 'Continue' }))

    await waitFor(() => {
      expect(screen.getByText('This hire is no longer available. Please select another agent.')).toBeInTheDocument()
    })

    expect(screen.getByTestId('dma-step-panel-induct')).toBeInTheDocument()
    expect(screen.queryByTestId('dma-step-panel-platforms')).not.toBeInTheDocument()
    expect(onStaleReference).toHaveBeenCalledWith({ subscriptionId: 'SUB-1', hiredInstanceId: 'HAI-1' })
  })

  it('re-resolves the hire by subscription and retries the save before showing a stale error', async () => {
    const serviceModule = await import('../services/digitalMarketingActivation.service')
    const hiredAgentsModule = await import('../services/hiredAgents.service')

    vi.mocked(serviceModule.upsertDigitalMarketingActivationWorkspace)
      .mockRejectedValueOnce({ status: 404 })
      .mockResolvedValueOnce({
        hired_instance_id: 'HAI-2',
        customer_id: 'CUST-1',
        agent_type_id: 'marketing.digital_marketing.v1',
        workspace: {
          brand_name: 'WAOOAW',
          location: 'Pune',
          primary_language: 'en',
          timezone: 'Asia/Kolkata',
          business_context: '',
          offerings_services: ['Activation'],
          platforms_enabled: ['youtube'],
          activation_complete: false,
          campaign_setup: structuredClone(defaultWorkspace).campaign_setup,
        },
        readiness: {
          brief_complete: true,
          youtube_selected: true,
          youtube_connection_ready: true,
          configured: true,
          can_finalize: true,
          missing_requirements: [],
        },
        updated_at: '2026-03-18T09:00:00Z',
      } as any)

    vi.mocked(hiredAgentsModule.getHiredAgentBySubscription)
      .mockResolvedValueOnce({
        subscription_id: 'SUB-1',
        hired_instance_id: 'HAI-1',
        agent_id: 'AGT-MKT-DMA-001',
        agent_type_id: 'marketing.digital_marketing.v1',
        nickname: 'Growth Copilot',
        theme: 'dark',
        config: {},
        configured: false,
        goals_completed: false,
      })
      .mockResolvedValueOnce({
        subscription_id: 'SUB-1',
        hired_instance_id: 'HAI-2',
        agent_id: 'AGT-MKT-DMA-001',
        agent_type_id: 'marketing.digital_marketing.v1',
        nickname: 'Growth Copilot',
        theme: 'dark',
        config: {},
        configured: true,
        goals_completed: false,
      })
      .mockResolvedValueOnce({
        subscription_id: 'SUB-1',
        hired_instance_id: 'HAI-2',
        agent_id: 'AGT-MKT-DMA-001',
        agent_type_id: 'marketing.digital_marketing.v1',
        nickname: 'Growth Copilot',
        theme: 'dark',
        config: {},
        configured: true,
        goals_completed: false,
      })

    const onStaleReference = vi.fn()

    render(
      <MemoryRouter>
        <FluentProvider theme={waooawLightTheme}>
          <DigitalMarketingActivationWizard
            instances={[mockInstance]}
            selectedInstance={mockInstance}
            readOnly={false}
            onStaleReference={onStaleReference}
          />
        </FluentProvider>
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByTestId('dma-step-panel-induct')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByRole('button', { name: 'Continue' }))

    await waitFor(() => {
      expect(screen.getByTestId('dma-step-panel-platforms')).toBeInTheDocument()
    })

    expect(serviceModule.upsertDigitalMarketingActivationWorkspace).toHaveBeenNthCalledWith(
      1,
      'HAI-1',
      expect.any(Object),
    )
    expect(serviceModule.upsertDigitalMarketingActivationWorkspace).toHaveBeenNthCalledWith(
      2,
      'HAI-2',
      expect.any(Object),
    )
    expect(onStaleReference).not.toHaveBeenCalled()
    expect(screen.queryByText('This hire is no longer available. Please select another agent.')).not.toBeInTheDocument()
  })

  it('reuses a saved YouTube connection before sending the user to Google', async () => {
    const serviceModule = await import('../services/digitalMarketingActivation.service')
    const ytModule = await import('../services/youtubeConnections.service')
    const disconnectedActivation = {
      hired_instance_id: 'HAI-1',
      customer_id: 'CUST-1',
      agent_type_id: 'marketing.digital_marketing.v1',
      workspace: {
        brand_name: 'WAOOAW',
        location: 'Pune',
        primary_language: 'en',
        timezone: 'Asia/Kolkata',
        business_context: '',
        offerings_services: ['Activation'],
        platforms_enabled: ['youtube'],
        platform_bindings: { youtube: { skill_id: 'default' } },
        campaign_setup: structuredClone(defaultWorkspace).campaign_setup,
      },
      readiness: {
        brief_complete: true,
        youtube_selected: true,
        youtube_connection_ready: false,
        configured: true,
        can_finalize: false,
        missing_requirements: ['youtube_connection'],
      },
      updated_at: '2026-03-18T09:00:00Z',
    } as any
    vi.mocked(serviceModule.getDigitalMarketingActivationWorkspace).mockResolvedValue(disconnectedActivation)
    vi.mocked(serviceModule.upsertDigitalMarketingActivationWorkspace).mockResolvedValue(disconnectedActivation)
    vi.mocked(ytModule.listYouTubeConnections).mockResolvedValue([
      {
        id: 'cred-youtube-1',
        customer_id: 'CUST-1',
        platform_key: 'youtube',
        provider_account_id: 'channel-1',
        display_name: 'Channel One',
        granted_scopes: [],
        verification_status: 'verified',
        connection_status: 'connected',
        token_expires_at: null,
        last_verified_at: '2026-03-18T09:00:00Z',
        created_at: '2026-03-18T09:00:00Z',
        updated_at: '2026-03-18T09:00:00Z',
      },
    ])

    renderWizard()
    await goToConnectStep()

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Use saved YouTube connection' })).toBeInTheDocument()
    })

    fireEvent.click(screen.getByRole('button', { name: 'Use saved YouTube connection' }))

    await waitFor(() => {
      expect(ytModule.attachYouTubeConnection).toHaveBeenCalledWith('cred-youtube-1', {
        hired_instance_id: 'HAI-1',
        skill_id: 'default',
      })
    })

    expect(ytModule.startYouTubeConnection).not.toHaveBeenCalled()
    expect(screen.getByText('Saved YouTube connection linked successfully.')).toBeInTheDocument()
    expect(screen.getByText('✓ Connected')).toBeInTheDocument()
  })

  it('falls back to Google when a saved YouTube connection cannot be reused', async () => {
    const serviceModule = await import('../services/digitalMarketingActivation.service')
    const ytModule = await import('../services/youtubeConnections.service')
    const browserModule = await import('../utils/browserNavigation')
    const disconnectedActivation = {
      hired_instance_id: 'HAI-1',
      customer_id: 'CUST-1',
      agent_type_id: 'marketing.digital_marketing.v1',
      workspace: {
        brand_name: 'WAOOAW',
        location: 'Pune',
        primary_language: 'en',
        timezone: 'Asia/Kolkata',
        business_context: '',
        offerings_services: ['Activation'],
        platforms_enabled: ['youtube'],
        platform_bindings: { youtube: { skill_id: 'default' } },
        campaign_setup: structuredClone(defaultWorkspace).campaign_setup,
      },
      readiness: {
        brief_complete: true,
        youtube_selected: true,
        youtube_connection_ready: false,
        configured: true,
        can_finalize: false,
        missing_requirements: ['youtube_connection'],
      },
      updated_at: '2026-03-18T09:00:00Z',
    } as any
    vi.mocked(serviceModule.getDigitalMarketingActivationWorkspace).mockResolvedValue(disconnectedActivation)
    vi.mocked(serviceModule.upsertDigitalMarketingActivationWorkspace).mockResolvedValue(disconnectedActivation)
    vi.mocked(ytModule.listYouTubeConnections).mockResolvedValue([
      {
        id: 'cred-youtube-1',
        customer_id: 'CUST-1',
        platform_key: 'youtube',
        provider_account_id: 'channel-1',
        display_name: 'Channel One',
        granted_scopes: [],
        verification_status: 'verified',
        connection_status: 'connected',
        token_expires_at: null,
        last_verified_at: '2026-03-18T09:00:00Z',
        created_at: '2026-03-18T09:00:00Z',
        updated_at: '2026-03-18T09:00:00Z',
      },
    ])
    vi.mocked(ytModule.attachYouTubeConnection).mockRejectedValueOnce(new Error('attach failed'))
    vi.mocked(ytModule.startYouTubeConnection).mockResolvedValue({
      state: 'yt-state-1',
      authorization_url: 'https://accounts.google.com/o/oauth2/v2/auth?state=yt-state-1',
      expires_at: '2026-03-18T10:00:00Z',
    })

    renderWizard()
    await goToConnectStep()

    fireEvent.click(screen.getByRole('button', { name: 'Use saved YouTube connection' }))

    await waitFor(() => {
      expect(ytModule.startYouTubeConnection).toHaveBeenCalled()
    })

    expect(browserModule.redirectTo).toHaveBeenCalledWith('https://accounts.google.com/o/oauth2/v2/auth?state=yt-state-1')
    const pending = readPendingYouTubeOAuthContext()
    expect(pending?.state).toBe('yt-state-1')
    expect(pending?.source).toBe('activation-wizard')
    expect(pending?.returnTo).toBe('/my-agents')
  })
})

