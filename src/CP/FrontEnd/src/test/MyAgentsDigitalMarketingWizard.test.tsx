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
  validateYouTubeConnection: vi.fn(),
  attachYouTubeConnection: vi.fn(),
}))

vi.mock('../services/platformConnections.service', () => ({
  listPlatformConnections: vi.fn().mockResolvedValue([]),
  findPlatformConnection: (connections: any[], platformKey: string) =>
    connections.find((connection) => String(connection.platform_key || '').trim().toLowerCase() === String(platformKey || '').trim().toLowerCase()) || null,
}))

vi.mock('../services/marketingReview.service', () => ({
  createDraftBatch: vi.fn(),
  executeDraftPost: vi.fn(),
  approveDraftPost: vi.fn(),
  rejectDraftPost: vi.fn(),
  scheduleDraftPost: vi.fn(),
}))

vi.mock('../services/profile.service', () => ({
  getProfile: vi.fn().mockResolvedValue({
    id: 'customer-1',
    email: 'customer@example.com',
    business_name: 'Profile Business',
    location: 'Pune',
    timezone: 'Asia/Kolkata',
    primary_language: 'en',
  }),
  updateProfile: vi.fn().mockResolvedValue({
    id: 'customer-1',
    email: 'customer@example.com',
    business_name: 'Profile Business',
    location: 'Pune',
    timezone: 'Asia/Kolkata',
    primary_language: 'en',
  }),
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
    expect(screen.getByTestId('dma-step-panel-connect')).toBeInTheDocument()
  })
}

async function goToThemeStep() {
  await goToConnectStep()
  fireEvent.click(screen.getByRole('button', { name: 'Continue' }))
  await waitFor(() => {
    expect(screen.getByTestId('dma-step-panel-theme')).toBeInTheDocument()
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
    vi.mocked(serviceModule.generateDigitalMarketingThemePlan).mockResolvedValue({
      campaign_id: 'CAM-1',
      master_theme: 'Own your category with clear, premium education',
      derived_themes: [
        { title: 'Authority content', description: 'Teach the market', frequency: 'weekly' },
        { title: 'Conversion content', description: 'Convert interest into demand', frequency: 'weekly' },
      ],
      workspace: {
        brand_name: 'WAOOAW',
        location: 'Pune',
        primary_language: 'en',
        timezone: 'Asia/Kolkata',
        business_context: 'Growth marketing',
        offerings_services: ['Activation'],
        platforms_enabled: ['youtube'],
        campaign_setup: {
          ...structuredClone(defaultWorkspace).campaign_setup,
          master_theme: 'Own your category with clear, premium education',
          derived_themes: [
            { title: 'Authority content', description: 'Teach the market', frequency: 'weekly' },
            { title: 'Conversion content', description: 'Convert interest into demand', frequency: 'weekly' },
          ],
          strategy_workshop: {
            status: 'approval_ready',
            assistant_message: 'Your content should make complex buying decisions feel commercially obvious.',
            checkpoint_summary: 'We have locked the audience, the premium-natural positioning, and the first content direction.',
            current_focus_question: 'Do you want the first YouTube series to lean more into trust-building or behind-the-scenes proof?',
            next_step_options: ['Refine the audience', 'Sharpen the positioning', 'Suggest first 3 content angles'],
            time_saving_note: 'I have collapsed your earlier inputs into one working direction so we can move straight to the best next decision.',
            follow_up_questions: ['What is the first commercial outcome this content must drive?'],
            messages: [
              { role: 'assistant', content: 'Tell me what business result matters most from this channel.' },
              { role: 'user', content: 'We need more qualified inbound demand.' },
            ],
            summary: {
              profession_name: 'Beauty Artist',
              location_focus: 'Viman Nagar, Pune',
              customer_profile: 'Women aged 25-45 seeking premium beauty support for events and everyday confidence.',
              service_focus: 'Makeup, hair styling, and event-ready beauty services.',
              signature_differentiator: 'Natural, health-conscious products backed by a decade of experience.',
              business_goal: 'Grow qualified inbound demand and repeat bookings.',
              first_content_direction: 'Behind-the-scenes transformation stories that build trust.',
              business_focus: 'Activation services for growth-stage teams.',
              audience: 'Founders and operators.',
              positioning: 'The operator-led partner that turns confusion into execution.',
              tone: 'Sharp, credible, and practical.',
              content_pillars: ['Education', 'Proof', 'Execution'],
              youtube_angle: 'Turn strategy confusion into practical next steps.',
              cta: 'Book a strategy session.',
            },
          },
        },
      },
    } as any)
    vi.mocked(serviceModule.patchDigitalMarketingThemePlan).mockImplementation(async (_hiredInstanceId, patch: any) => ({
      campaign_id: patch?.campaign_setup?.campaign_id || 'CAM-1',
      master_theme: patch?.master_theme || 'Own your category with clear, premium education',
      derived_themes: patch?.derived_themes || [],
      workspace: {
        brand_name: 'WAOOAW',
        location: 'Pune',
        primary_language: 'en',
        timezone: 'Asia/Kolkata',
        business_context: 'Growth marketing',
        offerings_services: ['Activation'],
        platforms_enabled: ['youtube'],
        campaign_setup: {
          ...structuredClone(defaultWorkspace).campaign_setup,
          campaign_id: patch?.campaign_setup?.campaign_id || 'CAM-1',
          master_theme: patch?.master_theme || 'Own your category with clear, premium education',
          derived_themes: patch?.derived_themes || [],
          schedule: patch?.campaign_setup?.schedule || structuredClone(defaultWorkspace).campaign_setup.schedule,
          strategy_workshop: patch?.campaign_setup?.strategy_workshop || {
            status: 'not_started',
            assistant_message: '',
            checkpoint_summary: '',
            current_focus_question: '',
            next_step_options: [],
            time_saving_note: '',
            follow_up_questions: [],
            messages: [],
            summary: {
              profession_name: '',
              location_focus: '',
              customer_profile: '',
              service_focus: '',
              signature_differentiator: '',
              business_goal: '',
              first_content_direction: '',
              business_focus: '',
              audience: '',
              positioning: '',
              tone: '',
              content_pillars: [],
              youtube_angle: '',
              cta: '',
            },
            approved_at: null,
          },
        },
      },
    }) as any)

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
    const platformModule = await import('../services/platformConnections.service')
    const marketingReviewModule = await import('../services/marketingReview.service')
    vi.mocked(ytModule.listYouTubeConnections).mockResolvedValue([])
    vi.mocked(ytModule.attachYouTubeConnection).mockResolvedValue({
      id: 'conn-youtube-bootstrap',
      hired_instance_id: 'HAI-1',
      skill_id: 'default',
      customer_platform_credential_id: 'cred-youtube-bootstrap',
      platform_key: 'youtube',
      status: 'connected',
      connected_at: '2026-03-18T09:00:00Z',
      last_verified_at: '2026-03-18T09:00:00Z',
      created_at: '2026-03-18T09:00:00Z',
      updated_at: '2026-03-18T09:00:00Z',
    })
    vi.mocked(platformModule.listPlatformConnections).mockResolvedValue([])
    vi.mocked(marketingReviewModule.createDraftBatch).mockResolvedValue({
      batch_id: 'batch-1',
      agent_id: 'AGT-MKT-DMA-001',
      hired_instance_id: 'HAI-1',
      customer_id: 'CUST-1',
      theme: 'WAOOAW',
      brand_name: 'WAOOAW',
      created_at: '2026-03-18T09:00:00Z',
      status: 'pending_review',
      posts: [
        {
          post_id: 'post-youtube-1',
          channel: 'youtube',
          text: 'Draft YouTube copy',
          review_status: 'pending_review',
          approval_id: null,
          execution_status: 'not_scheduled',
        },
      ],
    })
    vi.mocked(marketingReviewModule.approveDraftPost).mockResolvedValue({
      post_id: 'post-youtube-1',
      review_status: 'approved',
      approval_id: 'APR-123',
    })
    vi.mocked(marketingReviewModule.executeDraftPost).mockResolvedValue({
      allowed: true,
      decision_id: 'decision-1',
      post_id: 'post-youtube-1',
      execution_status: 'posted',
      provider_post_url: 'https://youtube.com/post/123',
      provider_post_id: 'yt-123',
    })
    vi.mocked(marketingReviewModule.rejectDraftPost).mockResolvedValue({
      post_id: 'post-youtube-1',
      decision: 'rejected',
    })
    vi.mocked(marketingReviewModule.scheduleDraftPost).mockResolvedValue({
      post_id: 'post-youtube-1',
      execution_status: 'scheduled',
      scheduled_at: '2026-03-18T10:00:00Z',
    })
  })

  it('renders wizard shell with 4 outcome-led step buttons', async () => {
    renderWizard()
    await waitFor(() => {
      expect(screen.getByTestId('dma-step-panel-connect')).toBeInTheDocument()
    })
    const stepTitles = ['Channel Ready', 'Brief Chat', 'Plan', 'Review & Activate']
    for (const title of stepTitles) {
      expect(screen.getAllByText(title).length).toBeGreaterThan(0)
    }
    expect(screen.getByText('Now')).toBeInTheDocument()
  })

  it('starts on the connect panel when a DMA hire is already selected', async () => {
    renderWizard()
    await waitFor(() => {
      expect(screen.getByTestId('dma-step-panel-connect')).toBeInTheDocument()
    })
    expect(screen.queryByTestId('dma-step-panel-select')).not.toBeInTheDocument()
  })

  it('does not show Select Agent step when controlled instance is provided', async () => {
    renderWizard()
    await waitFor(() => {
      expect(screen.queryByTestId('dma-step-panel-select')).not.toBeInTheDocument()
    })
    // First visible panel should be connect (channel ready)
    expect(screen.getByTestId('dma-step-panel-connect')).toBeInTheDocument()
  })

  it('first visible stage is productive customer outcome not internal mechanics', async () => {
    renderWizard()
    await waitFor(() => {
      expect(screen.getByTestId('dma-step-panel-connect')).toBeInTheDocument()
    })
    // Should show "Channel Ready" not "Select Agent" or "Induct Agent"
    expect(screen.getByRole('button', { name: /Channel Ready/ })).toBeInTheDocument()
  })

  it('Continue and Back navigation works across reduced stage model', async () => {
    renderWizard()
    await waitFor(() => {
      expect(screen.getByTestId('dma-step-panel-connect')).toBeInTheDocument()
    })
    
    // Navigate to next stage
    const themeBtn = screen.getByText('Brief Chat').closest('button')
    expect(themeBtn).not.toBeNull()
    fireEvent.click(themeBtn!)
    
    await waitFor(() => {
      expect(screen.getByTestId('dma-step-panel-theme')).toBeInTheDocument()
    })
    
    // Navigate back
    const connectBtn = screen.getByText('Channel Ready').closest('button')
    expect(connectBtn).not.toBeNull()
    fireEvent.click(connectBtn!)
    
    await waitFor(() => {
      expect(screen.getByTestId('dma-step-panel-connect')).toBeInTheDocument()
    })
  })

  it('shows activation unavailable when no DMA hire is selected', async () => {
    render(
      <MemoryRouter>
        <FluentProvider theme={waooawLightTheme}>
          <DigitalMarketingActivationWizard
            instances={[mockInstance, mockInstance2]}
            selectedInstance={null}
            readOnly={false}
          />
        </FluentProvider>
      </MemoryRouter>
    )
    await waitFor(() => {
      expect(screen.getByText('Activation unavailable')).toBeInTheDocument()
    })
  })

  it('Activate Agent button visible on final stage', async () => {
    renderWizard()
    await waitFor(() => {
      expect(screen.getByTestId('dma-step-panel-connect')).toBeInTheDocument()
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
      expect(screen.getByTestId('dma-step-panel-connect')).toBeInTheDocument()
    })

    expect(screen.queryByText('Activation unavailable')).not.toBeInTheDocument()
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
      expect(screen.getByTestId('dma-step-panel-connect')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByRole('button', { name: 'Continue' }))

    await waitFor(() => {
      expect(screen.getByText('This hire is no longer available. Please select another agent.')).toBeInTheDocument()
    })

    expect(screen.getByTestId('dma-step-panel-connect')).toBeInTheDocument()
    expect(screen.queryByTestId('dma-step-panel-theme')).not.toBeInTheDocument()
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
      expect(screen.getByTestId('dma-step-panel-connect')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByRole('button', { name: 'Continue' }))

    await waitFor(() => {
      expect(screen.getByTestId('dma-step-panel-theme')).toBeInTheDocument()
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

  it('tests a saved YouTube connection before persisting it for the agent', async () => {
    const serviceModule = await import('../services/digitalMarketingActivation.service')
    const ytModule = await import('../services/youtubeConnections.service')
    const platformModule = await import('../services/platformConnections.service')
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
    vi.mocked(platformModule.listPlatformConnections).mockResolvedValue([])
    vi.mocked(ytModule.validateYouTubeConnection).mockResolvedValue({
      id: 'cred-youtube-1',
      customer_id: 'CUST-1',
      platform_key: 'youtube',
      provider_account_id: 'channel-1',
      display_name: 'Channel One',
      verification_status: 'verified',
      connection_status: 'connected',
      token_expires_at: null,
      last_verified_at: '2026-03-18T09:00:00Z',
      channel_count: 1,
      total_video_count: 42,
      recent_short_count: 7,
      recent_long_video_count: 35,
      subscriber_count: 1200,
      view_count: 54000,
    })
    vi.mocked(ytModule.attachYouTubeConnection).mockResolvedValue({
      id: 'conn-youtube-1',
      hired_instance_id: 'HAI-1',
      skill_id: 'default',
      customer_platform_credential_id: 'cred-youtube-1',
      platform_key: 'youtube',
      status: 'connected',
      connected_at: '2026-03-18T09:00:00Z',
      last_verified_at: '2026-03-18T09:00:00Z',
      created_at: '2026-03-18T09:00:00Z',
      updated_at: '2026-03-18T09:00:00Z',
    })

    renderWizard()
    await goToConnectStep()

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Test connection' })).toBeInTheDocument()
    })

    fireEvent.click(screen.getByRole('button', { name: 'Test connection' }))

    await waitFor(() => {
      expect(ytModule.validateYouTubeConnection).toHaveBeenCalledWith('cred-youtube-1')
    })

    expect(screen.getByTestId('youtube-validation-metrics')).toBeInTheDocument()
    expect(screen.getByText('42')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Persist connection for future use by Agent' })).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: 'Persist connection for future use by Agent' }))

    await waitFor(() => {
      expect(ytModule.attachYouTubeConnection).toHaveBeenCalledWith('cred-youtube-1', {
        hired_instance_id: 'HAI-1',
        skill_id: 'default',
      })
    })

    expect(ytModule.startYouTubeConnection).not.toHaveBeenCalled()
    expect(screen.getByText('YouTube connection saved for future agent use.')).toBeInTheDocument()
    expect(screen.getByText('✓ Connected')).toBeInTheDocument()
  })

  it('starts Google OAuth again when the user chooses to reconnect the saved channel', async () => {
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
    vi.mocked(ytModule.startYouTubeConnection).mockResolvedValue({
      state: 'yt-state-1',
      authorization_url: 'https://accounts.google.com/o/oauth2/v2/auth?state=yt-state-1',
      expires_at: '2026-03-18T10:00:00Z',
    })

    renderWizard()
    await goToConnectStep()

    fireEvent.click(screen.getByRole('button', { name: 'Reconnect with Google' }))

    await waitFor(() => {
      expect(ytModule.startYouTubeConnection).toHaveBeenCalled()
    })

    expect(browserModule.redirectTo).toHaveBeenCalledWith('https://accounts.google.com/o/oauth2/v2/auth?state=yt-state-1')
    const pending = readPendingYouTubeOAuthContext()
    expect(pending?.state).toBe('yt-state-1')
    expect(pending?.source).toBe('activation-wizard')
    expect(pending?.returnTo).toBe('/my-agents')
  })

  it('does not show a connected badge or draft CTA until the hire connection is attached', async () => {
    const serviceModule = await import('../services/digitalMarketingActivation.service')
    const ytModule = await import('../services/youtubeConnections.service')
    const platformModule = await import('../services/platformConnections.service')
    const partiallyConnectedActivation = {
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
        youtube_connection_ready: true,
        configured: true,
        can_finalize: false,
        missing_requirements: [],
      },
      updated_at: '2026-03-18T09:00:00Z',
    } as any
    vi.mocked(serviceModule.getDigitalMarketingActivationWorkspace).mockResolvedValue(partiallyConnectedActivation)
    vi.mocked(serviceModule.upsertDigitalMarketingActivationWorkspace).mockResolvedValue(partiallyConnectedActivation)
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
    vi.mocked(platformModule.listPlatformConnections).mockResolvedValue([])

    renderWizard()
    await goToConnectStep()

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Test connection' })).toBeInTheDocument()
    })

    expect(screen.getByRole('button', { name: 'Reconnect with Google' })).toBeInTheDocument()
    expect(screen.queryByTestId('youtube-connected-badge')).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Persist connection for future use by Agent' })).not.toBeInTheDocument()
    expect(screen.queryByTestId('generate-youtube-draft-btn')).not.toBeInTheDocument()
    expect(screen.getByTestId('generate-youtube-draft-next-step-hint')).toBeInTheDocument()
  })

  it('shows theme-step guidance on connect instead of any draft CTA', async () => {
    const serviceModule = await import('../services/digitalMarketingActivation.service')
    const ytModule = await import('../services/youtubeConnections.service')
    const platformModule = await import('../services/platformConnections.service')

    const attachedActivation = {
      hired_instance_id: 'HAI-1',
      customer_id: 'CUST-1',
      agent_type_id: 'marketing.digital_marketing.v1',
      workspace: {
        brand_name: '',
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
        brief_complete: false,
        youtube_selected: true,
        youtube_connection_ready: true,
        configured: true,
        can_finalize: false,
        missing_requirements: [],
      },
      updated_at: '2026-03-18T09:00:00Z',
    } as any

    vi.mocked(serviceModule.getDigitalMarketingActivationWorkspace).mockResolvedValue(attachedActivation)
    vi.mocked(serviceModule.upsertDigitalMarketingActivationWorkspace).mockResolvedValue(attachedActivation)
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
    vi.mocked(platformModule.listPlatformConnections).mockResolvedValue([
      {
        id: 'conn-youtube-1',
        hired_instance_id: 'HAI-1',
        skill_id: 'default',
        customer_platform_credential_id: 'cred-youtube-1',
        platform_key: 'youtube',
        status: 'connected',
        connected_at: '2026-03-18T09:00:00Z',
        last_verified_at: '2026-03-18T09:00:00Z',
        created_at: '2026-03-18T09:00:00Z',
        updated_at: '2026-03-18T09:00:00Z',
      },
    ] as any)

    renderWizard()
    await goToConnectStep()

    await waitFor(() => {
      expect(screen.getByTestId('youtube-connected-badge')).toBeInTheDocument()
    })

    expect(screen.queryByTestId('generate-youtube-draft-btn')).not.toBeInTheDocument()
    expect(screen.getByTestId('generate-youtube-draft-next-step-hint')).toBeInTheDocument()
  })

  it('prefills brand name from the customer profile when the activation workspace is empty', async () => {
    const serviceModule = await import('../services/digitalMarketingActivation.service')
    const profileModule = await import('../services/profile.service')

    vi.mocked(serviceModule.getDigitalMarketingActivationWorkspace).mockResolvedValueOnce({
      hired_instance_id: 'HAI-1',
      customer_id: 'CUST-1',
      agent_type_id: 'marketing.digital_marketing.v1',
      workspace: {
        brand_name: '',
        location: '',
        primary_language: '',
        timezone: '',
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
    vi.mocked(profileModule.getProfile).mockResolvedValueOnce({
      id: 'customer-1',
      email: 'customer@example.com',
      business_name: 'TestCo',
      location: 'Pune',
      timezone: 'Asia/Kolkata',
      primary_language: 'en',
    })

    renderWizard()
    await goToThemeStep()

    await waitFor(() => {
      expect(screen.getByLabelText('Brand name')).toHaveValue('TestCo')
    })
  })

  it('keeps the existing workspace brand name instead of replacing it from profile', async () => {
    const serviceModule = await import('../services/digitalMarketingActivation.service')
    const profileModule = await import('../services/profile.service')

    vi.mocked(serviceModule.getDigitalMarketingActivationWorkspace).mockResolvedValueOnce({
      hired_instance_id: 'HAI-1',
      customer_id: 'CUST-1',
      agent_type_id: 'marketing.digital_marketing.v1',
      workspace: {
        brand_name: 'ExistingBrand',
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
    vi.mocked(profileModule.getProfile).mockResolvedValueOnce({
      id: 'customer-1',
      email: 'customer@example.com',
      business_name: 'IgnoredProfileName',
      location: 'Pune',
      timezone: 'Asia/Kolkata',
      primary_language: 'en',
    })

    renderWizard()
    await goToThemeStep()

    await waitFor(() => {
      expect(screen.getByLabelText('Brand name')).toHaveValue('ExistingBrand')
    })
    expect(profileModule.getProfile).not.toHaveBeenCalled()
  })

  it('shows a strategy preview before approval when the strategy is pending', async () => {
    const serviceModule = await import('../services/digitalMarketingActivation.service')

    vi.mocked(serviceModule.getDigitalMarketingActivationWorkspace).mockResolvedValueOnce({
      hired_instance_id: 'HAI-1',
      customer_id: 'CUST-1',
      agent_type_id: 'marketing.digital_marketing.v1',
      workspace: {
        brand_name: 'WAOOAW',
        location: 'Pune',
        primary_language: 'en',
        timezone: 'Asia/Kolkata',
        business_context: 'Growth marketing',
        offerings_services: ['Activation'],
        platforms_enabled: ['youtube'],
        campaign_setup: {
          ...structuredClone(defaultWorkspace).campaign_setup,
          master_theme: 'Growth content',
          derived_themes: [
            { title: 'Proof-led content', description: 'Show customer outcomes', frequency: 'weekly' },
          ],
          strategy_workshop: {
            status: 'approval_ready',
            assistant_message: 'Pending approval',
            checkpoint_summary: 'Ready for review',
            current_focus_question: '',
            next_step_options: [],
            time_saving_note: '',
            follow_up_questions: [],
            messages: [],
            summary: {
              business_goal: 'Increase qualified inbound leads',
              positioning: 'Operator-led growth partner',
              first_content_direction: 'Show proof-led content',
            },
            approved_at: null,
          },
        },
      },
      readiness: {
        brief_complete: true,
        youtube_selected: true,
        youtube_connection_ready: true,
        configured: true,
        can_finalize: false,
        missing_requirements: [],
      },
      updated_at: '2026-03-18T09:00:00Z',
    } as any)

    renderWizard()
    await goToThemeStep()

    await waitFor(() => {
      expect(screen.getByText('Strategy Preview — review before approving')).toBeInTheDocument()
    })
    expect(screen.getByText('Master Theme: Growth content')).toBeInTheDocument()
    expect(screen.getAllByText(/Proof-led content/i).length).toBeGreaterThan(0)
  })

  it('hides the strategy preview after the strategy is approved', async () => {
    const serviceModule = await import('../services/digitalMarketingActivation.service')

    vi.mocked(serviceModule.getDigitalMarketingActivationWorkspace).mockResolvedValueOnce({
      hired_instance_id: 'HAI-1',
      customer_id: 'CUST-1',
      agent_type_id: 'marketing.digital_marketing.v1',
      workspace: {
        brand_name: 'WAOOAW',
        location: 'Pune',
        primary_language: 'en',
        timezone: 'Asia/Kolkata',
        business_context: 'Growth marketing',
        offerings_services: ['Activation'],
        platforms_enabled: ['youtube'],
        campaign_setup: {
          ...structuredClone(defaultWorkspace).campaign_setup,
          master_theme: 'Growth content',
          derived_themes: [
            { title: 'Proof-led content', description: 'Show customer outcomes', frequency: 'weekly' },
          ],
          strategy_workshop: {
            status: 'approved',
            assistant_message: 'Approved strategy',
            checkpoint_summary: 'Approved',
            current_focus_question: '',
            next_step_options: [],
            time_saving_note: '',
            follow_up_questions: [],
            messages: [],
            summary: {
              business_goal: 'Increase qualified inbound leads',
              positioning: 'Operator-led growth partner',
              first_content_direction: 'Show proof-led content',
            },
            approved_at: '2026-03-18T09:15:00Z',
          },
        },
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

    renderWizard()
    await goToThemeStep()

    await waitFor(() => {
      expect(screen.queryByText('Strategy Preview — review before approving')).not.toBeInTheDocument()
    })
  })

  it('runs the AI strategy workshop and lets the customer approve the resulting theme', async () => {
    const serviceModule = await import('../services/digitalMarketingActivation.service')

    renderWizard()
    await goToThemeStep()

    fireEvent.change(screen.getByLabelText('Strategy workshop reply'), {
      target: { value: 'We want more qualified inbound demand from founder-led teams.' },
    })
    fireEvent.click(screen.getByTestId('start-theme-workshop-btn'))

    await waitFor(() => {
      expect(serviceModule.generateDigitalMarketingThemePlan).toHaveBeenCalledWith(
        'HAI-1',
        expect.objectContaining({
          campaign_setup: expect.objectContaining({
            strategy_workshop: expect.objectContaining({
              pending_input: 'We want more qualified inbound demand from founder-led teams.',
            }),
          }),
        })
      )
    })

    expect(screen.getByTestId('strategy-assistant-message')).toHaveTextContent(
      'Your content should make complex buying decisions feel commercially obvious.'
    )
    expect(screen.getByTestId('strategy-checkpoint-summary')).toHaveTextContent(
      'We have locked the audience, the premium-natural positioning, and the first content direction.'
    )
    expect(screen.getByTestId('strategy-current-focus-question')).toHaveTextContent(
      'Do you want the first YouTube series to lean more into trust-building or behind-the-scenes proof?'
    )
    expect(screen.getByText('Beauty Artist')).toBeInTheDocument()
    expect(screen.getByText('Viman Nagar, Pune')).toBeInTheDocument()

    fireEvent.click(screen.getByTestId('approve-theme-strategy-btn'))

    await waitFor(() => {
      expect(serviceModule.patchDigitalMarketingThemePlan).toHaveBeenCalledWith(
        'HAI-1',
        expect.objectContaining({
          campaign_setup: expect.objectContaining({
            strategy_workshop: expect.objectContaining({ status: 'approved' }),
          }),
        })
      )
    })

    expect(screen.getByTestId('strategy-workshop-status')).toHaveTextContent('Approved')
  })

  it('lets the customer use a suggested next-step option without typing a long reply', async () => {
    const serviceModule = await import('../services/digitalMarketingActivation.service')

    renderWizard()
    await goToThemeStep()

    fireEvent.click(screen.getByTestId('start-theme-workshop-btn'))

    await waitFor(() => {
      expect(screen.getByTestId('strategy-option-0')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByTestId('strategy-option-2'))

    await waitFor(() => {
      expect(serviceModule.generateDigitalMarketingThemePlan).toHaveBeenLastCalledWith(
        'HAI-1',
        expect.objectContaining({
          campaign_setup: expect.objectContaining({
            strategy_workshop: expect.objectContaining({
              pending_input: 'Suggest first 3 content angles',
            }),
          }),
        })
      )
    })
  })

  it('reuses the approval returned by approve before publishing a YouTube draft', async () => {
    const serviceModule = await import('../services/digitalMarketingActivation.service')
    const platformModule = await import('../services/platformConnections.service')
    const marketingReviewModule = await import('../services/marketingReview.service')

    const attachedActivation = {
      hired_instance_id: 'HAI-1',
      customer_id: 'CUST-1',
      agent_type_id: 'marketing.digital_marketing.v1',
      workspace: {
        brand_name: 'WAOOAW',
        location: 'Pune',
        primary_language: 'en',
        timezone: 'Asia/Kolkata',
        business_context: 'Growth marketing',
        offerings_services: ['Activation'],
        platforms_enabled: ['youtube'],
        platform_bindings: { youtube: { skill_id: 'default' } },
        campaign_setup: {
          ...structuredClone(defaultWorkspace).campaign_setup,
          master_theme: 'Own your category with clear, premium education',
          derived_themes: [
            { title: 'Authority content', description: 'Teach the market', frequency: 'weekly' },
          ],
          strategy_workshop: {
            status: 'approved',
            assistant_message: 'Approved strategy',
            checkpoint_summary: 'Audience, offer, and opening YouTube direction are approved.',
            current_focus_question: '',
            next_step_options: ['Approve this direction'],
            time_saving_note: 'No more discovery is needed before drafts.',
            follow_up_questions: [],
            messages: [],
            summary: {
              profession_name: 'Beauty Artist',
              location_focus: 'Viman Nagar, Pune',
              customer_profile: 'Founders',
              service_focus: 'Activation services',
              signature_differentiator: 'Operator-led growth partner',
              business_goal: 'Generate demand',
              first_content_direction: 'Explain growth clearly',
              business_focus: 'Activation services',
              audience: 'Founders',
              positioning: 'Operator-led growth partner',
              tone: 'Clear and practical',
              content_pillars: ['Education'],
              youtube_angle: 'Explain growth clearly',
              cta: 'Book a session',
            },
            approved_at: '2026-03-18T09:10:00Z',
          },
        },
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
    } as any

    vi.mocked(serviceModule.getDigitalMarketingActivationWorkspace).mockResolvedValue(attachedActivation)
    vi.mocked(serviceModule.upsertDigitalMarketingActivationWorkspace).mockResolvedValue(attachedActivation)
    vi.mocked(platformModule.listPlatformConnections).mockResolvedValue([
      {
        id: 'conn-youtube-1',
        hired_instance_id: 'HAI-1',
        skill_id: 'default',
        customer_platform_credential_id: 'cred-youtube-1',
        platform_key: 'youtube',
        status: 'connected',
        connected_at: '2026-03-18T09:00:00Z',
        last_verified_at: '2026-03-18T09:00:00Z',
        created_at: '2026-03-18T09:00:00Z',
        updated_at: '2026-03-18T09:00:00Z',
      },
    ] as any)

    renderWizard()
    await goToThemeStep()

    await waitFor(() => {
      expect(screen.getByTestId('generate-youtube-draft-btn')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByTestId('generate-youtube-draft-btn'))

    await waitFor(() => {
      expect(screen.getByTestId('draft-post-card-post-youtube-1')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByTestId('approve-post-btn-post-youtube-1'))

    await waitFor(() => {
      expect(marketingReviewModule.approveDraftPost).toHaveBeenCalledWith('post-youtube-1')
      expect(screen.getByTestId('publish-now-btn-post-youtube-1')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByTestId('publish-now-btn-post-youtube-1'))

    await waitFor(() => {
      expect(marketingReviewModule.executeDraftPost).toHaveBeenCalledWith({
        post_id: 'post-youtube-1',
        agent_id: 'AGT-MKT-DMA-001',
        approval_id: 'APR-123',
        intent_action: 'publish',
      })
    })
  })

  it('shows workshop panel as the primary DMA brief interface', async () => {
    renderWizard()
    await goToThemeStep()

    await waitFor(() => {
      expect(screen.getByText('Brief your DMA hire')).toBeInTheDocument()
    })
    expect(screen.getByText('The assistant will ask only what it needs to build your first YouTube theme')).toBeInTheDocument()
    expect(screen.getByTestId('strategy-workshop-thread')).toBeInTheDocument()
  })

  it('shows suggested next answers as clickable options', async () => {
    renderWizard()
    await goToThemeStep()

    await waitFor(() => {
      expect(screen.getByTestId('strategy-assistant-message')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByTestId('start-theme-workshop-btn'))

    await waitFor(() => {
      expect(screen.getByTestId('strategy-option-0')).toBeInTheDocument()
    })

    expect(screen.getByTestId('strategy-option-0')).toHaveTextContent('Refine the audience')
    expect(screen.getByTestId('strategy-option-1')).toHaveTextContent('Sharpen the positioning')
    expect(screen.getByTestId('strategy-option-2')).toHaveTextContent('Suggest first 3 content angles')
  })

  it('calls theme plan API with pending_input when replying to workshop', async () => {
    const serviceModule = await import('../services/digitalMarketingActivation.service')
    
    renderWizard()
    await goToThemeStep()

    fireEvent.change(screen.getByLabelText('Strategy workshop reply'), {
      target: { value: 'My target audience is enterprise sales leaders' },
    })
    fireEvent.click(screen.getByTestId('start-theme-workshop-btn'))

    await waitFor(() => {
      expect(serviceModule.generateDigitalMarketingThemePlan).toHaveBeenCalledWith(
        'HAI-1',
        expect.objectContaining({
          campaign_setup: expect.objectContaining({
            strategy_workshop: expect.objectContaining({
              pending_input: 'My target audience is enterprise sales leaders',
            }),
          }),
        })
      )
    })
  })

  it('hides advanced business input fields during initial consultative phase', async () => {
    renderWizard()
    await goToThemeStep()

    await waitFor(() => {
      expect(screen.getByText('Brief your DMA hire')).toBeInTheDocument()
    })

    // Dense fields should be in a collapsed section
    expect(screen.queryByText('Direct input fields')).not.toBeVisible()
  })

  it('reveals advanced fields when section is expanded', async () => {
    renderWizard()
    await goToThemeStep()

    await waitFor(() => {
      expect(screen.getByText('Optional business context fields')).toBeInTheDocument()
    })

    // Expand the details section
    const summary = screen.getByText('Optional business context fields')
    fireEvent.click(summary)

    // Now fields should be accessible
    await waitFor(() => {
      expect(screen.getByText('Direct input fields')).toBeVisible()
    })
  })

  // E4-S2 Tests: Enriched YouTube validation response rendering
  it('renders recent upload proof when enriched validate response contains preview items', async () => {
    const ytModule = await import('../services/youtubeConnections.service')
    vi.mocked(ytModule.listYouTubeConnections).mockResolvedValue([
      {
        id: 'cred-youtube-1',
        customer_id: 'CUST-1',
        platform_key: 'youtube',
        display_name: 'My Channel',
        granted_scopes: [],
        verification_status: 'verified',
        connection_status: 'connected',
        created_at: '2026-04-01T10:00:00Z',
        updated_at: '2026-04-01T10:00:00Z',
      },
    ])
    vi.mocked(ytModule.validateYouTubeConnection).mockResolvedValue({
      id: 'cred-youtube-1',
      customer_id: 'CUST-1',
      platform_key: 'youtube',
      display_name: 'My Channel',
      verification_status: 'verified',
      connection_status: 'connected',
      channel_count: 1,
      total_video_count: 10,
      recent_short_count: 2,
      recent_long_video_count: 3,
      subscriber_count: 500,
      view_count: 5000,
      recent_uploads: [
        {
          video_id: 'vid-1',
          title: 'Recent Video 1',
          published_at: '2026-04-01T10:00:00Z',
          duration_seconds: 300,
        },
        {
          video_id: 'vid-2',
          title: 'Recent Video 2',
          published_at: '2026-04-02T10:00:00Z',
          duration_seconds: 120,
        },
      ],
      next_action_hint: 'connected_ready',
    })

    renderWizard()
    await goToConnectStep()

    fireEvent.click(screen.getByRole('button', { name: 'Test connection' }))

    await waitFor(() => {
      expect(screen.getByTestId('youtube-recent-uploads')).toBeInTheDocument()
    })

    expect(screen.getByText('Recent Video 1')).toBeInTheDocument()
    expect(screen.getByText('Recent Video 2')).toBeInTheDocument()
  })

  it('renders reconnect guidance when next_action_hint indicates reconnect needed', async () => {
    const ytModule = await import('../services/youtubeConnections.service')
    vi.mocked(ytModule.listYouTubeConnections).mockResolvedValue([
      {
        id: 'cred-youtube-1',
        customer_id: 'CUST-1',
        platform_key: 'youtube',
        display_name: 'My Channel',
        granted_scopes: [],
        verification_status: 'verified',
        connection_status: 'connected',
        created_at: '2026-04-01T10:00:00Z',
        updated_at: '2026-04-01T10:00:00Z',
      },
    ])
    vi.mocked(ytModule.validateYouTubeConnection).mockResolvedValue({
      id: 'cred-youtube-1',
      customer_id: 'CUST-1',
      platform_key: 'youtube',
      display_name: 'My Channel',
      verification_status: 'verified',
      connection_status: 'connected',
      channel_count: 1,
      total_video_count: 10,
      recent_short_count: 2,
      recent_long_video_count: 3,
      subscriber_count: 500,
      view_count: 5000,
      recent_uploads: [],
      next_action_hint: 'reconnect_required',
    })

    renderWizard()
    await goToConnectStep()

    fireEvent.click(screen.getByRole('button', { name: 'Test connection' }))

    await waitFor(() => {
      expect(screen.getByTestId('youtube-next-action-hint')).toBeInTheDocument()
    })

    expect(screen.getByText(/Token expired — reconnect with Google/)).toBeInTheDocument()
  })

  it('existing validate action works when preview fields are absent or empty', async () => {
    const ytModule = await import('../services/youtubeConnections.service')
    vi.mocked(ytModule.listYouTubeConnections).mockResolvedValue([
      {
        id: 'cred-youtube-1',
        customer_id: 'CUST-1',
        platform_key: 'youtube',
        display_name: 'My Channel',
        granted_scopes: [],
        verification_status: 'verified',
        connection_status: 'connected',
        created_at: '2026-04-01T10:00:00Z',
        updated_at: '2026-04-01T10:00:00Z',
      },
    ])
    vi.mocked(ytModule.validateYouTubeConnection).mockResolvedValue({
      id: 'cred-youtube-1',
      customer_id: 'CUST-1',
      platform_key: 'youtube',
      display_name: 'My Channel',
      verification_status: 'verified',
      connection_status: 'connected',
      channel_count: 1,
      total_video_count: 10,
      recent_short_count: 2,
      recent_long_video_count: 3,
      subscriber_count: 500,
      view_count: 5000,
      recent_uploads: [],
      next_action_hint: 'connected_ready',
    })

    renderWizard()
    await goToConnectStep()

    fireEvent.click(screen.getByRole('button', { name: 'Test connection' }))

    await waitFor(() => {
      expect(screen.getByTestId('youtube-validation-metrics')).toBeInTheDocument()
    })

    // Fallback metrics view still works
    expect(screen.getByText('10')).toBeInTheDocument()
    expect(screen.getByText('500')).toBeInTheDocument()
    // No upload preview or error should appear
    expect(screen.queryByTestId('youtube-recent-uploads')).not.toBeInTheDocument()
  })
})
