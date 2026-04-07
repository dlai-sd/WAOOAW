import { describe, it, expect, vi, beforeEach } from 'vitest'

const mockedNavigate = vi.fn()

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<any>('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockedNavigate,
  }
})

import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { FluentProvider } from '@fluentui/react-components'
import { MemoryRouter } from 'react-router-dom'
import { waooawLightTheme } from '../theme'
import MyAgents from '../pages/authenticated/MyAgents'

vi.mock('../services/subscriptions.service', () => ({
  cancelSubscription: vi.fn().mockResolvedValue({
    subscription_id: 'SUB-1',
    agent_id: 'agent-123',
    duration: 'monthly',
    status: 'active',
    current_period_start: '2026-02-01T00:00:00Z',
    current_period_end: '2026-03-01T00:00:00Z',
    cancel_at_period_end: true
  })
}))

vi.mock('../services/myAgentsSummary.service', () => ({
  getMyAgentsSummary: vi.fn().mockResolvedValue({
    instances: [
      {
        subscription_id: 'SUB-1',
        agent_id: 'AGT-TRD-DELTA-001',
        duration: 'monthly',
        status: 'active',
        current_period_start: '2026-02-01T00:00:00Z',
        current_period_end: '2026-03-01T00:00:00Z',
        cancel_at_period_end: false,
        hired_instance_id: 'HIRED-1',
        agent_type_id: 'trading.share_trader.v1',
        external_catalog_version: 'v3',
        catalog_status_at_hire: 'servicing_only'
      }
    ]
  })
}))

vi.mock('../services/agentTypes.service', () => ({
  getAgentTypeDefinition: vi.fn().mockResolvedValue({
    agent_type_id: 'trading.share_trader.v1',
    version: '1.0.0',
    config_schema: { fields: [] },
    goal_templates: [
      {
        goal_template_id: 'trading.trade_intent_draft.v1',
        name: 'Trade intent draft (enter/exit)',
        default_frequency: 'on_demand',
        settings_schema: {
          fields: [
            { key: 'coin', label: 'Coin', type: 'text', required: true },
            { key: 'side', label: 'Side', type: 'enum', required: true, options: ['buy', 'sell'] },
            { key: 'units', label: 'Units', type: 'number', required: true }
          ]
        }
      }
    ]
  })
}))

vi.mock('../services/hiredAgents.service', () => ({
  getHiredAgentBySubscription: vi.fn().mockRejectedValue({ status: 404 }),
  upsertHiredAgentDraft: vi.fn().mockResolvedValue({
    subscription_id: 'SUB-1',
    hired_instance_id: 'HIRED-1',
    agent_id: 'AGT-TRD-DELTA-001',
    agent_type_id: 'trading.share_trader.v1',
    nickname: 'Trader',
    theme: 'steady',
    config: {},
    configured: true,
  })
}))

vi.mock('../services/digitalMarketingActivation.service', async () => {
  const actual = await vi.importActual<any>('../services/digitalMarketingActivation.service')
  return {
    ...actual,
    getDigitalMarketingActivationWorkspace: vi.fn().mockResolvedValue({
      hired_instance_id: 'HIRED-1',
      agent_type_id: 'marketing.digital_marketing.v1',
      workspace: {},
      readiness: {
        brief_complete: false,
        youtube_selected: false,
        youtube_connection_ready: true,
        configured: false,
        can_finalize: false,
        missing_requirements: ['business_profile', 'agent_configuration'],
      },
      updated_at: '2026-03-19T12:00:00Z',
    }),
    upsertDigitalMarketingActivationWorkspace: vi.fn().mockResolvedValue({
      hired_instance_id: 'HIRED-1',
      agent_type_id: 'marketing.digital_marketing.v1',
      workspace: {},
      readiness: {
        brief_complete: false,
        youtube_selected: false,
        youtube_connection_ready: true,
        configured: false,
        can_finalize: false,
        missing_requirements: ['business_profile', 'agent_configuration'],
      },
      updated_at: '2026-03-19T12:05:00Z',
    }),
  }
})

vi.mock('../services/platformCredentials.service', () => ({
  upsertPlatformCredential: vi.fn()
}))

vi.mock('../services/youtubeConnections.service', () => ({
  listYouTubeConnections: vi.fn().mockResolvedValue([]),
  startYouTubeConnection: vi.fn(),
  validateYouTubeConnection: vi.fn(),
  attachYouTubeConnection: vi.fn(),
}))

vi.mock('../utils/browserNavigation', () => ({
  redirectTo: vi.fn(),
}))

vi.mock('../services/platformConnections.service', async () => {
  const actual = await vi.importActual<any>('../services/platformConnections.service')
  return {
    ...actual,
    listPlatformConnections: vi.fn().mockResolvedValue([]),
  }
})

vi.mock('../services/exchangeSetup.service', () => ({
  upsertExchangeSetup: vi.fn()
}))

vi.mock('../services/hiredAgentDeliverables.service', async () => {
  const actual = await vi.importActual<any>('../services/hiredAgentDeliverables.service')
  return {
    ...actual,
    listHiredAgentDeliverables: vi.fn().mockResolvedValue({
      hired_instance_id: 'HIRED-1',
      deliverables: [
        {
          deliverable_id: 'DEL-1',
          hired_instance_id: 'HIRED-1',
          goal_instance_id: 'GOAL-1',
          goal_template_id: 'trading.trade_intent_draft.v1',
          title: 'Trade intent draft',
          payload: { plan: 'do_something' },
          review_status: 'pending_review',
          review_notes: null,
          approval_id: null,
          execution_status: 'not_executed',
          executed_at: null,
          created_at: null,
          updated_at: null
        }
      ]
    }),
    reviewHiredAgentDeliverable: vi.fn().mockResolvedValue({
      deliverable_id: 'DEL-1',
      review_status: 'approved',
      approval_id: 'APR-1',
      updated_at: null
    })
  }
})


vi.mock('../services/hiredAgentGoals.service', () => ({
  listHiredAgentGoals: vi.fn().mockResolvedValue({ hired_instance_id: 'HIRED-1', goals: [] }),
  upsertHiredAgentGoal: vi.fn().mockResolvedValue({
    goal_instance_id: 'GOAL-1',
    hired_instance_id: 'HIRED-1',
    goal_template_id: 'trading.trade_intent_draft.v1',
    frequency: 'on_demand',
    settings: { coin: 'BTC', side: 'buy', units: 1 }
  }),
  deleteHiredAgentGoal: vi.fn().mockResolvedValue({ deleted: true, goal_instance_id: 'GOAL-1' })
}))

const renderWithProvider = (component: React.ReactElement) => {
  return render(
    <MemoryRouter>
      <FluentProvider theme={waooawLightTheme}>
        {component}
      </FluentProvider>
    </MemoryRouter>
  )
}

describe('MyAgents Component', () => {
  beforeEach(() => {
    sessionStorage.clear()
    mockedNavigate.mockReset()
  })

  it('starts YouTube reconnect directly from My Agents when the channel needs attention', async () => {

    const summaryModule = await import('../services/myAgentsSummary.service')
    const deliverablesModule = await import('../services/hiredAgentDeliverables.service')
    const connectionsModule = await import('../services/platformConnections.service')
    const youtubeModule = await import('../services/youtubeConnections.service')
    const browserModule = await import('../utils/browserNavigation')

    vi.mocked(summaryModule.getMyAgentsSummary).mockResolvedValueOnce({
      instances: [
        {
          subscription_id: 'SUB-MKT-0',
          agent_id: 'AGT-MKT-YT-000',
          duration: 'monthly',
          status: 'active',
          current_period_start: '2026-03-01T00:00:00Z',
          current_period_end: '2026-04-01T00:00:00Z',
          cancel_at_period_end: false,
          hired_instance_id: 'HIRED-MKT-0',
          agent_type_id: 'marketing.digital_marketing.v1'
        },
        {
          subscription_id: 'SUB-TRD-0',
          agent_id: 'AGT-TRD-DELTA-010',
          duration: 'monthly',
          status: 'active',
          current_period_start: '2026-03-01T00:00:00Z',
          current_period_end: '2026-04-01T00:00:00Z',
          cancel_at_period_end: false,
          hired_instance_id: 'HIRED-TRD-0',
          agent_type_id: 'trading.share_trader.v1'
        }
      ]
    })

    vi.mocked(deliverablesModule.listHiredAgentDeliverables).mockResolvedValueOnce({
      hired_instance_id: 'HIRED-MKT-0',
      deliverables: [
        {
          deliverable_id: 'DEL-MKT-0',
          hired_instance_id: 'HIRED-MKT-0',
          goal_instance_id: 'GOAL-MKT-0',
          goal_template_id: 'marketing.theme_discovery.v1',
          title: 'YouTube setup draft',
          payload: { destination: { destination_type: 'youtube' } },
          review_status: 'approved',
          review_notes: null,
          approval_id: 'APR-MKT-0',
          execution_status: 'not_executed',
          created_at: null,
          updated_at: null,
        }
      ]
    })

    vi.mocked(connectionsModule.listPlatformConnections).mockResolvedValue([])
    vi.mocked(youtubeModule.listYouTubeConnections).mockResolvedValue([
      {
        id: 'cred-yt-0',
        customer_id: 'CUST-0',
        platform_key: 'youtube',
        display_name: 'Dormant Channel',
        granted_scopes: ['youtube.upload'],
        verification_status: 'verified',
        connection_status: 'reconnect_required',
        created_at: '2026-03-10T10:00:00Z',
        updated_at: '2026-03-16T10:05:00Z',
      }
    ] as any)
    vi.mocked(youtubeModule.startYouTubeConnection).mockResolvedValueOnce({
      state: 'yt-state-0',
      authorization_url: 'https://accounts.google.com/o/oauth2/v2/auth?state=yt-state-0',
      expires_at: '2026-03-19T10:00:00Z',
    })

    renderWithProvider(<MyAgents />)

    await waitFor(() => {
      expect(screen.getByText('My Agents (2)')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByRole('button', { name: 'Goal Setting' }))

    await waitFor(() => {
      expect(screen.getByText('Drafts (1)')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByRole('button', { name: 'Review' }))

    const reconnectButton = await screen.findByRole('button', { name: /connect with google/i })
    fireEvent.click(reconnectButton)

    await waitFor(() => {
      expect(youtubeModule.startYouTubeConnection).toHaveBeenCalled()
    })

    expect(browserModule.redirectTo).toHaveBeenCalledWith('https://accounts.google.com/o/oauth2/v2/auth?state=yt-state-0')
  })

  it('shows DMA agent selector at the top when all agents are DMA', async () => {
    const summaryModule = await import('../services/myAgentsSummary.service')
    
    vi.mocked(summaryModule.getMyAgentsSummary).mockResolvedValueOnce({
      instances: [
        {
          subscription_id: 'SUB-DM-1',
          agent_id: 'AGT-MKT-DMA-001',
          duration: 'monthly',
          status: 'active',
          current_period_start: '2026-03-01T00:00:00Z',
          current_period_end: '2026-04-01T00:00:00Z',
          cancel_at_period_end: false,
          hired_instance_id: 'HIRED-DM-1',
          agent_type_id: 'marketing.digital_marketing.v1',
          nickname: 'Growth Engine',
        },
        {
          subscription_id: 'SUB-DM-2',
          agent_id: 'AGT-MKT-DMA-002',
          duration: 'monthly',
          status: 'active',
          current_period_start: '2026-03-01T00:00:00Z',
          current_period_end: '2026-04-01T00:00:00Z',
          cancel_at_period_end: false,
          hired_instance_id: 'HIRED-DM-2',
          agent_type_id: 'marketing.digital_marketing.v1',
          nickname: 'SEO Pilot',
        }
      ]
    })

    renderWithProvider(<MyAgents />)

    await waitFor(() => {
      expect(screen.getByText('My Agents (2)')).toBeInTheDocument()
    })

    expect(screen.getByText('Selected DMA Hire')).toBeInTheDocument()
  })

  it('changes the DMA activation area when selected hire changes', async () => {
    const summaryModule = await import('../services/myAgentsSummary.service')
    const hiredModule = await import('../services/hiredAgents.service')
    const activationModule = await import('../services/digitalMarketingActivation.service')
    
    vi.mocked(summaryModule.getMyAgentsSummary).mockResolvedValueOnce({
      instances: [
        {
          subscription_id: 'SUB-DM-1',
          agent_id: 'AGT-MKT-DMA-001',
          duration: 'monthly',
          status: 'active',
          current_period_start: '2026-03-01T00:00:00Z',
          current_period_end: '2026-04-01T00:00:00Z',
          cancel_at_period_end: false,
          hired_instance_id: 'HIRED-DM-1',
          agent_type_id: 'marketing.digital_marketing.v1',
          nickname: 'Growth Engine',
        },
        {
          subscription_id: 'SUB-DM-2',
          agent_id: 'AGT-MKT-DMA-002',
          duration: 'monthly',
          status: 'active',
          current_period_start: '2026-03-01T00:00:00Z',
          current_period_end: '2026-04-01T00:00:00Z',
          cancel_at_period_end: false,
          hired_instance_id: 'HIRED-DM-2',
          agent_type_id: 'marketing.digital_marketing.v1',
          nickname: 'SEO Pilot',
        }
      ]
    })

    vi.mocked(hiredModule.getHiredAgentBySubscription)
      .mockResolvedValueOnce({
        subscription_id: 'SUB-DM-1',
        hired_instance_id: 'HIRED-DM-1',
        agent_id: 'AGT-MKT-DMA-001',
        agent_type_id: 'marketing.digital_marketing.v1',
        nickname: 'Growth Engine',
        theme: 'midnight',
        config: {},
        configured: false,
      })
      .mockResolvedValueOnce({
        subscription_id: 'SUB-DM-2',
        hired_instance_id: 'HIRED-DM-2',
        agent_id: 'AGT-MKT-DMA-002',
        agent_type_id: 'marketing.digital_marketing.v1',
        nickname: 'SEO Pilot',
        theme: 'midnight',
        config: {},
        configured: false,
      })

    vi.mocked(activationModule.getDigitalMarketingActivationWorkspace)
      .mockResolvedValue({
        hired_instance_id: 'HIRED-DM-1',
        agent_type_id: 'marketing.digital_marketing.v1',
        workspace: {
          brand_name: 'WAOOAW',
          location: 'Bengaluru',
          primary_language: 'English',
          timezone: 'Asia/Kolkata',
          offerings_services: ['SEO'],
          platforms_enabled: [],
          platform_bindings: {},
        },
        readiness: {
          brief_complete: false,
          youtube_selected: false,
          youtube_connection_ready: false,
          configured: false,
          can_finalize: false,
          missing_requirements: [],
        },
        updated_at: '2026-03-19T12:00:00Z',
      })

    renderWithProvider(<MyAgents />)

    await waitFor(() => {
      expect(screen.getByText('My Agents (2)')).toBeInTheDocument()
    })

    const selector = screen.getByRole('combobox')
    fireEvent.click(selector)
    
    const seoOption = await screen.findByText('SEO Pilot')
    fireEvent.click(seoOption)

    await waitFor(() => {
      expect(hiredModule.getHiredAgentBySubscription).toHaveBeenCalledWith('SUB-DM-2')
    })
  })

  it('renders the digital marketing activation wizard and saves its workspace', async () => {
    const summaryModule = await import('../services/myAgentsSummary.service')
    const hiredModule = await import('../services/hiredAgents.service')
    const activationModule = await import('../services/digitalMarketingActivation.service')

    vi.mocked(summaryModule.getMyAgentsSummary).mockResolvedValueOnce({
      instances: [
        {
          subscription_id: 'SUB-DM-1',
          agent_id: 'AGT-MKT-DMA-001',
          duration: 'monthly',
          status: 'active',
          current_period_start: '2026-03-01T00:00:00Z',
          current_period_end: '2026-04-01T00:00:00Z',
          cancel_at_period_end: false,
          hired_instance_id: 'HIRED-DM-1',
          agent_type_id: 'marketing.digital_marketing.v1',
        }
      ]
    })

    vi.mocked(hiredModule.getHiredAgentBySubscription)
      .mockResolvedValueOnce({
        subscription_id: 'SUB-DM-1',
        hired_instance_id: 'HIRED-DM-1',
        agent_id: 'AGT-MKT-DMA-001',
        agent_type_id: 'marketing.digital_marketing.v1',
        nickname: 'Growth Engine',
        theme: 'midnight',
        config: {},
        configured: false,
      })
      .mockResolvedValueOnce({
        subscription_id: 'SUB-DM-1',
        hired_instance_id: 'HIRED-DM-1',
        agent_id: 'AGT-MKT-DMA-001',
        agent_type_id: 'marketing.digital_marketing.v1',
        nickname: 'Growth Engine',
        theme: 'midnight',
        config: {},
        configured: true,
      })

    vi.mocked(activationModule.getDigitalMarketingActivationWorkspace).mockResolvedValueOnce({
      hired_instance_id: 'HIRED-DM-1',
      agent_type_id: 'marketing.digital_marketing.v1',
      workspace: {
        brand_name: 'WAOOAW',
        location: 'Bengaluru',
        primary_language: 'English',
        timezone: 'Asia/Kolkata',
        offerings_services: ['SEO'],
        platforms_enabled: ['youtube'],
        platform_bindings: { youtube: { skill_id: 'default' } },
      },
      readiness: {
        brief_complete: false,
        youtube_selected: true,
        youtube_connection_ready: true,
        configured: false,
        can_finalize: false,
        missing_requirements: ['business_profile', 'agent_configuration'],
      },
      updated_at: '2026-03-19T12:00:00Z',
    })

    vi.mocked(activationModule.upsertDigitalMarketingActivationWorkspace).mockResolvedValue({
      hired_instance_id: 'HIRED-DM-1',
      agent_type_id: 'marketing.digital_marketing.v1',
      workspace: {
        brand_name: 'WAOOAW',
        location: 'Bengaluru',
        primary_language: 'English',
        timezone: 'Asia/Kolkata',
        offerings_services: ['SEO', 'Content'],
        platforms_enabled: ['youtube'],
        platform_bindings: { youtube: { skill_id: 'default' } },
      },
      readiness: {
        brief_complete: true,
        youtube_selected: true,
        youtube_connection_ready: false,
        configured: true,
        can_finalize: false,
        missing_requirements: ['youtube_connection'],
      },
      updated_at: '2026-03-19T12:05:00Z',
    })

    renderWithProvider(<MyAgents />)

    await waitFor(() => {
      expect(screen.getByTestId('dma-step-panel-connect')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByRole('button', { name: 'Continue' }))

    await waitFor(() => {
      expect(screen.getByTestId('dma-step-panel-theme')).toBeInTheDocument()
    })

    expect(hiredModule.upsertHiredAgentDraft).toHaveBeenCalledTimes(1)

    expect(activationModule.upsertDigitalMarketingActivationWorkspace).toHaveBeenLastCalledWith('HIRED-1', {
      workspace: expect.objectContaining({
        brand_name: 'WAOOAW',
        platforms_enabled: ['youtube'],
        platform_bindings: {
          youtube: { skill_id: 'default' },
        },
      }),
    })
  })
  it('renders page title with agent count', async () => {
    renderWithProvider(<MyAgents />)
    await waitFor(() => {
      expect(screen.getByText('My Agents (1)')).toBeInTheDocument()
    })
  })

  it('displays hire new agent button', () => {
    renderWithProvider(<MyAgents />)
    expect(screen.getByText('+ Hire New Agent')).toBeInTheDocument()
  })

  it('does not render dead View Dashboard or Settings actions', async () => {
    renderWithProvider(<MyAgents />)

    await waitFor(() => {
      expect(screen.getByText('AGT-TRD-DELTA-001')).toBeInTheDocument()
    })

    expect(screen.queryByRole('button', { name: 'View Dashboard' })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Settings' })).not.toBeInTheDocument()
  })

  it('loads subscriptions and can schedule cancel', async () => {
    const { cancelSubscription } = await import('../services/subscriptions.service')

    renderWithProvider(<MyAgents />)

    await waitFor(() => {
      expect(screen.getByText('AGT-TRD-DELTA-001')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByRole('button', { name: 'End Hire' }))
    expect(screen.getByText('End hire at next billing date?')).toBeInTheDocument()
    expect(screen.getByText('After your hire ends')).toBeInTheDocument()
    expect(screen.getByText('Deliverables and configuration remain available in read-only.')).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: 'Confirm end hire' }))
    await waitFor(() => {
      expect(cancelSubscription).toHaveBeenCalledTimes(1)
    })
    expect(cancelSubscription).toHaveBeenCalledWith('SUB-1')

    await waitFor(() => {
      expect(screen.getByText(/Scheduled to end on/i)).toBeInTheDocument()
    })
    expect(screen.getByText(/you keep read-only access to deliverables and configuration/i)).toBeInTheDocument()
  })

  it('saves configuration using the persisted agent type instead of agent-id prefix inference', async () => {
    const summaryModule = await import('../services/myAgentsSummary.service')
    const hiredModule = await import('../services/hiredAgents.service')

    vi.mocked(summaryModule.getMyAgentsSummary).mockResolvedValueOnce({
      instances: [
        {
          subscription_id: 'SUB-CUSTOM-1',
          agent_id: 'CUSTOM-AGENT-001',
          duration: 'monthly',
          status: 'active',
          current_period_start: '2026-03-01T00:00:00Z',
          current_period_end: '2026-04-01T00:00:00Z',
          cancel_at_period_end: false,
          hired_instance_id: 'HIRED-CUSTOM-1',
          agent_type_id: 'trading.share_trader.v1',
        }
      ]
    })

    vi.mocked(hiredModule.getHiredAgentBySubscription).mockRejectedValueOnce({ status: 404 })

    renderWithProvider(<MyAgents />)

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Save configuration' })).toBeInTheDocument()
    })

    fireEvent.click(screen.getByRole('button', { name: 'Save configuration' }))

    await waitFor(() => {
      expect(hiredModule.upsertHiredAgentDraft).toHaveBeenCalledWith(
        expect.objectContaining({
          subscription_id: 'SUB-CUSTOM-1',
          agent_id: 'CUSTOM-AGENT-001',
          agent_type_id: 'trading.share_trader.v1',
        })
      )
    })
  })

  it('shows lifecycle continuity for hires that are no longer open for new sale', async () => {
    renderWithProvider(<MyAgents />)

    await waitFor(() => {
      expect(screen.getByText('Servicing only')).toBeInTheDocument()
    })

    expect(screen.getByText('Version: v3')).toBeInTheDocument()
    expect(screen.getByText('Lifecycle: Servicing only')).toBeInTheDocument()
    expect(
      screen.getByText(/your active service continues on the release you already purchased/i)
    ).toBeInTheDocument()
  })

  it('lets users switch away from an expired read-only hire', async () => {
    const summaryModule = await import('../services/myAgentsSummary.service')

    window.localStorage.clear()

    vi.mocked(summaryModule.getMyAgentsSummary).mockResolvedValueOnce({
      instances: [
        {
          subscription_id: 'SUB-EXP-1',
          agent_id: 'AGT-OLD-001',
          nickname: 'Expired Agent',
          duration: 'monthly',
          status: 'canceled',
          current_period_start: '2025-01-01T00:00:00Z',
          current_period_end: '2025-01-31T00:00:00Z',
          retention_expires_at: '2025-02-02T00:00:00Z',
          cancel_at_period_end: false,
          hired_instance_id: 'HIRED-EXP-1',
          agent_type_id: 'trading.share_trader.v1',
        },
        {
          subscription_id: 'SUB-ACT-1',
          agent_id: 'AGT-LIVE-001',
          nickname: 'Active Agent',
          duration: 'monthly',
          status: 'active',
          current_period_start: '2026-03-01T00:00:00Z',
          current_period_end: '2026-04-01T00:00:00Z',
          cancel_at_period_end: false,
          hired_instance_id: 'HIRED-ACT-1',
          agent_type_id: 'trading.share_trader.v1',
          configured: true,
        }
      ]
    })

    renderWithProvider(<MyAgents />)

    await waitFor(() => {
      expect(screen.getByText('Read-only access expired')).toBeInTheDocument()
    })

    expect(screen.getByText("This agent's trial has ended. Select another hire or review retained access.")).toBeInTheDocument()

    fireEvent.click(screen.getByRole('combobox'))
    fireEvent.click(await screen.findByText('Active Agent'))

    await waitFor(() => {
      expect(screen.queryByText('Read-only access expired')).not.toBeInTheDocument()
    })

    expect(screen.getByRole('combobox')).toHaveTextContent('Active Agent')
    expect(screen.getByRole('button', { name: 'Configure' })).not.toBeDisabled()
  })

  it('renders Goal Setting templates and can save a goal', async () => {
    const { upsertHiredAgentGoal, listHiredAgentGoals } = await import('../services/hiredAgentGoals.service')

    renderWithProvider(<MyAgents />)

    await waitFor(() => {
      expect(screen.getByText('My Agents (1)')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByRole('button', { name: 'Goal Setting' }))

    await waitFor(() => {
      expect(listHiredAgentGoals).toHaveBeenCalled()
    })

    await waitFor(() => {
      expect(screen.getByText('Add goal')).toBeInTheDocument()
      expect(screen.getByText('Trade intent draft (enter/exit)')).toBeInTheDocument()
    })

    // Required fields are empty initially; save disabled.
    expect(screen.getByRole('button', { name: 'Save goal' })).toBeDisabled()

    fireEvent.change(screen.getByLabelText('Coin'), { target: { value: 'BTC' } })
    fireEvent.change(screen.getByLabelText('Side'), { target: { value: 'buy' } })
    fireEvent.change(screen.getByLabelText('Units'), { target: { value: '1' } })

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Save goal' })).not.toBeDisabled()
    })

    fireEvent.click(screen.getByRole('button', { name: 'Save goal' }))

    await waitFor(() => {
      expect(upsertHiredAgentGoal).toHaveBeenCalledTimes(1)
    })
  })

  it('lists drafts and can approve with notes', async () => {
    const { listHiredAgentDeliverables, reviewHiredAgentDeliverable } = await import('../services/hiredAgentDeliverables.service')

    renderWithProvider(<MyAgents />)

    await waitFor(() => {
      expect(screen.getByText('My Agents (1)')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByRole('button', { name: 'Goal Setting' }))

    await waitFor(() => {
      expect(listHiredAgentDeliverables).toHaveBeenCalled()
    })

    await waitFor(() => {
      expect(screen.getByText('Drafts (1)')).toBeInTheDocument()
      expect(screen.getByText('Trade intent draft')).toBeInTheDocument()
    })

    fireEvent.click(screen.getAllByRole('button', { name: 'Review' })[0])
    fireEvent.change(screen.getByLabelText('Review notes'), { target: { value: 'Looks good' } })
    fireEvent.click(screen.getByRole('button', { name: 'Approve' }))

    await waitFor(() => {
      expect(reviewHiredAgentDeliverable).toHaveBeenCalledTimes(1)
    })
    expect(reviewHiredAgentDeliverable).toHaveBeenCalledWith('DEL-1', { decision: 'approved', notes: 'Looks good' })
  })

  it('shows YouTube connection and approval gating for digital marketing drafts', async () => {
    const summaryModule = await import('../services/myAgentsSummary.service')
    const deliverablesModule = await import('../services/hiredAgentDeliverables.service')
    const connectionsModule = await import('../services/platformConnections.service')
    const youtubeModule = await import('../services/youtubeConnections.service')

    vi.mocked(summaryModule.getMyAgentsSummary).mockResolvedValueOnce({
      instances: [
        {
          subscription_id: 'SUB-MKT-1',
          agent_id: 'AGT-MKT-YT-001',
          duration: 'monthly',
          status: 'active',
          current_period_start: '2026-03-01T00:00:00Z',
          current_period_end: '2026-04-01T00:00:00Z',
          cancel_at_period_end: false,
          hired_instance_id: 'HIRED-MKT-1',
          agent_type_id: 'marketing.digital_marketing.v1'
        },
        {
          subscription_id: 'SUB-TRD-1',
          agent_id: 'AGT-TRD-DELTA-011',
          duration: 'monthly',
          status: 'active',
          current_period_start: '2026-03-01T00:00:00Z',
          current_period_end: '2026-04-01T00:00:00Z',
          cancel_at_period_end: false,
          hired_instance_id: 'HIRED-TRD-1',
          agent_type_id: 'trading.share_trader.v1'
        }
      ]
    })

    vi.mocked(deliverablesModule.listHiredAgentDeliverables).mockResolvedValueOnce({
      hired_instance_id: 'HIRED-MKT-1',
      deliverables: [
        {
          deliverable_id: 'DEL-MKT-1',
          hired_instance_id: 'HIRED-MKT-1',
          goal_instance_id: 'GOAL-MKT-1',
          goal_template_id: 'marketing.theme_discovery.v1',
          title: 'YouTube explainer draft',
          payload: {
            destination: {
              destination_type: 'youtube',
              metadata: {
                visibility: 'private',
                public_release_requested: false,
              },
            },
            summary: 'Draft explainer for approval.'
          },
          review_status: 'pending_review',
          review_notes: null,
          approval_id: null,
          execution_status: 'not_executed',
          created_at: null,
          updated_at: null,
        }
      ]
    })

    vi.mocked(connectionsModule.listPlatformConnections).mockResolvedValueOnce([])
  vi.mocked(youtubeModule.listYouTubeConnections).mockResolvedValueOnce([])

    renderWithProvider(<MyAgents />)

    await waitFor(() => {
      expect(screen.getByText('My Agents (2)')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByRole('button', { name: 'Goal Setting' }))

    await waitFor(() => {
      expect(screen.getByText('Drafts (1)')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByRole('button', { name: 'Review' }))

    await waitFor(() => {
      expect(screen.getByText('YouTube channel status')).toBeInTheDocument()
    })

    expect(screen.getByText('YouTube channel status')).toBeInTheDocument()
    expect(screen.getByText('YouTube operating decision')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Reconnect with Google' })).toBeInTheDocument()
    expect(screen.getByText('Blocked by approval')).toBeInTheDocument()
    expect(screen.getByText('Customer approval')).toBeInTheDocument()
    expect(screen.getByText('Approve exact deliverable')).toBeInTheDocument()
  })

  it('shows YouTube connected state for approved digital marketing drafts', async () => {
    const summaryModule = await import('../services/myAgentsSummary.service')
    const deliverablesModule = await import('../services/hiredAgentDeliverables.service')
    const connectionsModule = await import('../services/platformConnections.service')
    const youtubeModule = await import('../services/youtubeConnections.service')

    vi.mocked(summaryModule.getMyAgentsSummary).mockResolvedValueOnce({
      instances: [
        {
          subscription_id: 'SUB-MKT-2',
          agent_id: 'AGT-MKT-YT-002',
          duration: 'monthly',
          status: 'active',
          current_period_start: '2026-03-01T00:00:00Z',
          current_period_end: '2026-04-01T00:00:00Z',
          cancel_at_period_end: false,
          hired_instance_id: 'HIRED-MKT-2',
          agent_type_id: 'marketing.digital_marketing.v1'
        },
        {
          subscription_id: 'SUB-TRD-2',
          agent_id: 'AGT-TRD-DELTA-012',
          duration: 'monthly',
          status: 'active',
          current_period_start: '2026-03-01T00:00:00Z',
          current_period_end: '2026-04-01T00:00:00Z',
          cancel_at_period_end: false,
          hired_instance_id: 'HIRED-TRD-2',
          agent_type_id: 'trading.share_trader.v1'
        }
      ]
    })

    vi.mocked(deliverablesModule.listHiredAgentDeliverables).mockResolvedValueOnce({
      hired_instance_id: 'HIRED-MKT-2',
      deliverables: [
        {
          deliverable_id: 'DEL-MKT-2',
          hired_instance_id: 'HIRED-MKT-2',
          goal_instance_id: 'GOAL-MKT-2',
          goal_template_id: 'marketing.theme_discovery.v1',
          title: 'YouTube short draft',
          payload: {
            destination: {
              destination_type: 'youtube',
              metadata: {
                visibility: 'private',
              },
            },
            summary: 'Short draft approved and waiting for upload.'
          },
          review_status: 'approved',
          review_notes: 'Ship it',
          approval_id: 'APR-MKT-2',
          execution_status: 'not_executed',
          created_at: null,
          updated_at: null,
        }
      ]
    })

    vi.mocked(connectionsModule.listPlatformConnections).mockResolvedValue([
      {
        id: 'CONN-1',
        hired_instance_id: 'HIRED-MKT-2',
        skill_id: 'default',
        customer_platform_credential_id: 'cred-yt-2',
        platform_key: 'youtube',
        status: 'connected',
        connected_at: '2026-03-10T10:00:00Z',
        last_verified_at: '2026-03-10T10:05:00Z',
        created_at: '2026-03-10T10:00:00Z',
        updated_at: '2026-03-10T10:05:00Z',
      }
    ])
    vi.mocked(youtubeModule.listYouTubeConnections).mockResolvedValue([
      {
        id: 'cred-yt-2',
        customer_id: 'CUST-2',
        platform_key: 'youtube',
        display_name: 'WAOOAW Launch Channel',
        granted_scopes: ['youtube.upload'],
        verification_status: 'verified',
        connection_status: 'connected',
        last_verified_at: '2026-03-10T10:05:00Z',
        created_at: '2026-03-10T10:00:00Z',
        updated_at: '2026-03-10T10:05:00Z',
      }
    ] as any)

    renderWithProvider(<MyAgents />)

    await waitFor(() => {
      expect(screen.getByText('My Agents (2)')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByRole('button', { name: 'Goal Setting' }))

    await waitFor(() => {
      expect(screen.getByText('Drafts (1)')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByRole('button', { name: 'Review' }))

    await waitFor(() => {
      expect(screen.getByText('YouTube channel status')).toBeInTheDocument()
      expect(screen.getByText('Ready for upload')).toBeInTheDocument()
    })
    expect(screen.getByText('YouTube channel status')).toBeInTheDocument()
  })

  it('shows reconnect-required state for stale YouTube credentials', async () => {
    const summaryModule = await import('../services/myAgentsSummary.service')
    const deliverablesModule = await import('../services/hiredAgentDeliverables.service')
    const connectionsModule = await import('../services/platformConnections.service')
    const youtubeModule = await import('../services/youtubeConnections.service')

    vi.mocked(summaryModule.getMyAgentsSummary).mockResolvedValueOnce({
      instances: [
        {
          subscription_id: 'SUB-MKT-3',
          agent_id: 'AGT-MKT-YT-003',
          duration: 'monthly',
          status: 'active',
          current_period_start: '2026-03-01T00:00:00Z',
          current_period_end: '2026-04-01T00:00:00Z',
          cancel_at_period_end: false,
          hired_instance_id: 'HIRED-MKT-3',
          agent_type_id: 'marketing.digital_marketing.v1'
        },
        {
          subscription_id: 'SUB-TRD-3',
          agent_id: 'AGT-TRD-DELTA-013',
          duration: 'monthly',
          status: 'active',
          current_period_start: '2026-03-01T00:00:00Z',
          current_period_end: '2026-04-01T00:00:00Z',
          cancel_at_period_end: false,
          hired_instance_id: 'HIRED-TRD-3',
          agent_type_id: 'trading.share_trader.v1'
        }
      ]
    })

    vi.mocked(deliverablesModule.listHiredAgentDeliverables).mockResolvedValueOnce({
      hired_instance_id: 'HIRED-MKT-3',
      deliverables: [
        {
          deliverable_id: 'DEL-MKT-3',
          hired_instance_id: 'HIRED-MKT-3',
          goal_instance_id: 'GOAL-MKT-3',
          goal_template_id: 'marketing.theme_discovery.v1',
          title: 'YouTube reconnect draft',
          payload: { destination: { destination_type: 'youtube' } },
          review_status: 'approved',
          review_notes: null,
          approval_id: 'APR-MKT-3',
          execution_status: 'not_executed',
          created_at: null,
          updated_at: null,
        }
      ]
    })

    vi.mocked(connectionsModule.listPlatformConnections).mockResolvedValue([
      {
        id: 'CONN-3',
        hired_instance_id: 'HIRED-MKT-3',
        skill_id: 'default',
        customer_platform_credential_id: 'cred-yt-3',
        platform_key: 'youtube',
        status: 'connected',
        connected_at: '2026-03-10T10:00:00Z',
        last_verified_at: '2026-03-10T10:05:00Z',
        created_at: '2026-03-10T10:00:00Z',
        updated_at: '2026-03-10T10:05:00Z',
      }
    ])

    vi.mocked(youtubeModule.listYouTubeConnections).mockResolvedValue([
      {
        id: 'cred-yt-3',
        customer_id: 'CUST-3',
        platform_key: 'youtube',
        display_name: 'Dormant Channel',
        granted_scopes: ['youtube.upload'],
        verification_status: 'verified',
        connection_status: 'reconnect_required',
        last_verified_at: '2026-03-10T10:05:00Z',
        created_at: '2026-03-10T10:00:00Z',
        updated_at: '2026-03-16T10:05:00Z',
      }
    ] as any)

    renderWithProvider(<MyAgents />)

    await waitFor(() => {
      expect(screen.getByText('My Agents (2)')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByRole('button', { name: 'Goal Setting' }))

    await waitFor(() => {
      expect(screen.getByText('Drafts (1)')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByRole('button', { name: 'Review' }))

    await waitFor(() => {
      expect(screen.getByText('Dormant Channel reconnect required')).toBeInTheDocument()
    })
    expect(screen.getByRole('button', { name: 'Reconnect with Google' })).toBeInTheDocument()
  })

  it('shows ready-to-attach state when a saved credential exists but is not attached to this hire', async () => {
    const summaryModule = await import('../services/myAgentsSummary.service')
    const deliverablesModule = await import('../services/hiredAgentDeliverables.service')
    const connectionsModule = await import('../services/platformConnections.service')
    const youtubeModule = await import('../services/youtubeConnections.service')

    vi.mocked(summaryModule.getMyAgentsSummary).mockResolvedValueOnce({
      instances: [
        {
          subscription_id: 'SUB-MKT-RTA',
          agent_id: 'AGT-MKT-YT-RTA',
          duration: 'monthly',
          status: 'active',
          current_period_start: '2026-03-01T00:00:00Z',
          current_period_end: '2026-04-01T00:00:00Z',
          cancel_at_period_end: false,
          hired_instance_id: 'HIRED-MKT-RTA',
          agent_type_id: 'marketing.digital_marketing.v1',
        },
        {
          subscription_id: 'SUB-TRD-RTA',
          agent_id: 'AGT-TRD-RTA',
          duration: 'monthly',
          status: 'active',
          current_period_start: '2026-03-01T00:00:00Z',
          current_period_end: '2026-04-01T00:00:00Z',
          cancel_at_period_end: false,
          hired_instance_id: 'HIRED-TRD-RTA',
          agent_type_id: 'trading.share_trader.v1',
        },
      ],
    })

    vi.mocked(deliverablesModule.listHiredAgentDeliverables).mockResolvedValueOnce({
      hired_instance_id: 'HIRED-MKT-RTA',
      deliverables: [
        {
          deliverable_id: 'DEL-MKT-RTA',
          hired_instance_id: 'HIRED-MKT-RTA',
          goal_instance_id: 'GOAL-MKT-RTA',
          goal_template_id: 'marketing.theme_discovery.v1',
          title: 'YouTube draft awaiting channel attach',
          payload: { destination: { destination_type: 'youtube' } },
          review_status: 'pending_review',
          review_notes: null,
          approval_id: null,
          execution_status: 'not_executed',
          created_at: null,
          updated_at: null,
        },
      ],
    })

    // No platform connection attached to this hire
    vi.mocked(connectionsModule.listPlatformConnections).mockResolvedValue([])
    // But a connected credential exists in the customer account
    vi.mocked(youtubeModule.listYouTubeConnections).mockResolvedValue([
      {
        id: 'cred-yt-rta',
        customer_id: 'CUST-RTA',
        platform_key: 'youtube',
        display_name: 'Ready Channel',
        granted_scopes: ['youtube.upload'],
        verification_status: 'verified',
        connection_status: 'connected',
        created_at: '2026-03-20T10:00:00Z',
        updated_at: '2026-03-20T10:00:00Z',
      },
    ] as any)

    renderWithProvider(<MyAgents />)

    await waitFor(() => {
      expect(screen.getByText('My Agents (2)')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByRole('button', { name: 'Goal Setting' }))

    await waitFor(() => {
      expect(screen.getByText('Drafts (1)')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByRole('button', { name: 'Review' }))

    await waitFor(() => {
      expect(screen.getByText('YouTube channel status')).toBeInTheDocument()
      expect(screen.getByText('Ready Channel ready to attach')).toBeInTheDocument()
    })
    expect(screen.getByRole('button', { name: 'Test connection' })).toBeInTheDocument()
  })

  it('tests and persists a saved YouTube credential from the My Agents operating rail', async () => {
    const summaryModule = await import('../services/myAgentsSummary.service')
    const deliverablesModule = await import('../services/hiredAgentDeliverables.service')
    const connectionsModule = await import('../services/platformConnections.service')
    const youtubeModule = await import('../services/youtubeConnections.service')

    vi.mocked(summaryModule.getMyAgentsSummary).mockResolvedValueOnce({
      instances: [
        {
          subscription_id: 'SUB-MKT-PERSIST',
          agent_id: 'AGT-MKT-YT-PERSIST',
          duration: 'monthly',
          status: 'active',
          current_period_start: '2026-03-01T00:00:00Z',
          current_period_end: '2026-04-01T00:00:00Z',
          cancel_at_period_end: false,
          hired_instance_id: 'HIRED-MKT-PERSIST',
          agent_type_id: 'marketing.digital_marketing.v1',
        },
        {
          subscription_id: 'SUB-TRD-PERSIST',
          agent_id: 'AGT-TRD-PERSIST',
          duration: 'monthly',
          status: 'active',
          current_period_start: '2026-03-01T00:00:00Z',
          current_period_end: '2026-04-01T00:00:00Z',
          cancel_at_period_end: false,
          hired_instance_id: 'HIRED-TRD-PERSIST',
          agent_type_id: 'trading.share_trader.v1',
        },
      ],
    })

    vi.mocked(deliverablesModule.listHiredAgentDeliverables).mockResolvedValueOnce({
      hired_instance_id: 'HIRED-MKT-PERSIST',
      deliverables: [
        {
          deliverable_id: 'DEL-MKT-PERSIST',
          hired_instance_id: 'HIRED-MKT-PERSIST',
          goal_instance_id: 'GOAL-MKT-PERSIST',
          goal_template_id: 'marketing.theme_discovery.v1',
          title: 'YouTube draft awaiting attach',
          payload: { destination: { destination_type: 'youtube' } },
          review_status: 'approved',
          review_notes: null,
          approval_id: 'APR-MKT-PERSIST',
          execution_status: 'not_executed',
          created_at: null,
          updated_at: null,
        },
      ],
    })

    vi.mocked(connectionsModule.listPlatformConnections)
      .mockResolvedValueOnce([])
      .mockResolvedValueOnce([])
      .mockResolvedValueOnce([
        {
          id: 'CONN-PERSIST',
          hired_instance_id: 'HIRED-MKT-PERSIST',
          skill_id: 'default',
          customer_platform_credential_id: 'cred-yt-persist',
          platform_key: 'youtube',
          status: 'connected',
          connected_at: '2026-03-20T10:00:00Z',
          last_verified_at: '2026-03-20T10:05:00Z',
          created_at: '2026-03-20T10:00:00Z',
          updated_at: '2026-03-20T10:05:00Z',
        },
      ] as any)
    vi.mocked(youtubeModule.listYouTubeConnections)
      .mockResolvedValue([
        {
          id: 'cred-yt-persist',
          customer_id: 'CUST-PERSIST',
          platform_key: 'youtube',
          display_name: 'Persist Channel',
          granted_scopes: ['youtube.upload'],
          verification_status: 'verified',
          connection_status: 'connected',
          last_verified_at: '2026-03-20T10:05:00Z',
          created_at: '2026-03-20T10:00:00Z',
          updated_at: '2026-03-20T10:05:00Z',
        },
      ] as any)
    vi.mocked(youtubeModule.validateYouTubeConnection).mockResolvedValueOnce({
      id: 'cred-yt-persist',
      customer_id: 'CUST-PERSIST',
      platform_key: 'youtube',
      display_name: 'Persist Channel',
      verification_status: 'verified',
      connection_status: 'connected',
      token_expires_at: null,
      last_verified_at: '2026-03-20T10:05:00Z',
      channel_count: 1,
      total_video_count: 42,
      recent_short_count: 7,
      recent_long_video_count: 35,
      subscriber_count: 1200,
      view_count: 54000,
      recent_uploads: [],
      next_action_hint: 'connected_ready',
    })
    vi.mocked(youtubeModule.attachYouTubeConnection).mockResolvedValueOnce({
      id: 'CONN-PERSIST',
      hired_instance_id: 'HIRED-MKT-PERSIST',
      skill_id: 'default',
      customer_platform_credential_id: 'cred-yt-persist',
      platform_key: 'youtube',
      status: 'connected',
      connected_at: '2026-03-20T10:00:00Z',
      last_verified_at: '2026-03-20T10:05:00Z',
      created_at: '2026-03-20T10:00:00Z',
      updated_at: '2026-03-20T10:05:00Z',
    })

    renderWithProvider(<MyAgents />)

    await waitFor(() => {
      expect(screen.getByText('My Agents (2)')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByRole('button', { name: 'Goal Setting' }))

    await waitFor(() => {
      expect(screen.getByText('Drafts (1)')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByRole('button', { name: 'Review' }))

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Test connection' })).toBeInTheDocument()
    })

    fireEvent.click(screen.getByRole('button', { name: 'Test connection' }))

    await waitFor(() => {
      expect(youtubeModule.validateYouTubeConnection).toHaveBeenCalledWith('cred-yt-persist')
    })

    expect(screen.getByTestId('youtube-validation-metrics')).toBeInTheDocument()
    expect(screen.getByText('42')).toBeInTheDocument()
    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Persist connection for future use by Agent' })).toBeInTheDocument()
    })

    fireEvent.click(screen.getByRole('button', { name: 'Persist connection for future use by Agent' }))

    await waitFor(() => {
      expect(youtubeModule.attachYouTubeConnection).toHaveBeenCalledWith('cred-yt-persist', {
        hired_instance_id: 'HIRED-MKT-PERSIST',
        skill_id: 'default',
      })
    })

    expect(screen.getByText('YouTube connection saved for future agent use.')).toBeInTheDocument()
  })
})
