import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { FluentProvider } from '@fluentui/react-components'
import { MemoryRouter } from 'react-router-dom'
import { waooawLightTheme } from '../theme'
import MyAgents from '../pages/authenticated/MyAgents'

const navigateMock = vi.fn()

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom')
  return {
    ...actual,
    useNavigate: () => navigateMock,
  }
})

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
  upsertHiredAgentDraft: vi.fn()
}))

vi.mock('../services/hiredAgentStudio.service', () => ({
  getHiredAgentStudio: vi.fn().mockResolvedValue({
    hired_instance_id: 'HIRED-1',
    subscription_id: 'SUB-1',
    agent_id: 'AGT-TRD-DELTA-001',
    agent_type_id: 'trading.share_trader.v1',
    customer_id: 'CUST-user-1',
    mode: 'edit',
    selection_required: false,
    current_step: 'review',
    steps: [
      { key: 'identity', title: 'Identity and voice', complete: true, blocked: false, summary: 'Business-facing name and theme are ready.' },
      { key: 'connection', title: 'Connection', complete: true, blocked: false, summary: 'Connection verified and ready.' },
      { key: 'operating_plan', title: 'Operating plan', complete: true, blocked: false, summary: 'Operating plan is in place.' },
      { key: 'review', title: 'Review edits', complete: true, blocked: false, summary: 'Use review to confirm the updated operating setup.' },
    ],
    identity: { nickname: 'Trader One', theme: 'default', complete: true },
    connection: { platform_key: 'delta_exchange_india', skill_id: 'default', connection_id: null, customer_platform_credential_id: 'cred-1', status: 'connected', complete: true, summary: 'Exchange credential reference is configured.' },
    operating_plan: { complete: true, goals_completed: true, goal_count: 0, skill_config_count: 1, summary: 'Operating plan is in place.' },
    review: { complete: true, summary: 'Ready to save the updated configuration.' },
    configured: true,
    goals_completed: true,
    trial_status: 'active',
    subscription_status: 'active',
    updated_at: '2026-03-17T00:00:00Z',
  })
}))

vi.mock('../services/platformCredentials.service', () => ({
  upsertPlatformCredential: vi.fn()
}))

vi.mock('../services/youtubeConnections.service', () => ({
  listYouTubeConnections: vi.fn().mockResolvedValue([]),
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

async function openDetailedWorkspace(): Promise<void> {
  fireEvent.click(await screen.findByRole('button', { name: 'Open detailed workspace' }))
}

describe('MyAgents Component', () => {
  beforeEach(() => {
    navigateMock.mockReset()
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

  it('loads subscriptions and can schedule cancel', async () => {
    const { cancelSubscription } = await import('../services/subscriptions.service')

    renderWithProvider(<MyAgents />)

    await waitFor(() => {
      expect(screen.getByText('AGT-TRD-DELTA-001')).toBeInTheDocument()
    })

    await openDetailedWorkspace()

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

  it('shows lifecycle continuity for hires that are no longer open for new sale', async () => {
    renderWithProvider(<MyAgents />)

    await waitFor(() => {
      expect(screen.getByText('My Agents (1)')).toBeInTheDocument()
    })

    await openDetailedWorkspace()

    expect(screen.getByText('Version: v3')).toBeInTheDocument()
    expect(screen.getByText('Lifecycle: Servicing only')).toBeInTheDocument()
    expect(
      screen.getByText(/your active service continues on the release you already purchased/i)
    ).toBeInTheDocument()
  })

  it('renders Goal Setting templates and can save a goal', async () => {
    const { upsertHiredAgentGoal, listHiredAgentGoals } = await import('../services/hiredAgentGoals.service')

    renderWithProvider(<MyAgents />)

    await waitFor(() => {
      expect(screen.getByText('My Agents (1)')).toBeInTheDocument()
    })

    await openDetailedWorkspace()
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

    await openDetailedWorkspace()
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
      expect(screen.getByText('My Agents (1)')).toBeInTheDocument()
    })

    await openDetailedWorkspace()
    fireEvent.click(screen.getByRole('button', { name: 'Goal Setting' }))

    await waitFor(() => {
      expect(screen.getByText('Drafts (1)')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByRole('button', { name: 'Review' }))

    await waitFor(() => {
      expect(screen.getByText('YouTube channel status')).toBeInTheDocument()
    })

    expect(screen.getByText('YouTube not connected')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Open YouTube setup' })).toBeInTheDocument()
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
    vi.mocked(youtubeModule.listYouTubeConnections).mockResolvedValueOnce([
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
      expect(screen.getByText('My Agents (1)')).toBeInTheDocument()
    })

    await openDetailedWorkspace()
    fireEvent.click(screen.getByRole('button', { name: 'Goal Setting' }))

    await waitFor(() => {
      expect(screen.getByText('Drafts (1)')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByRole('button', { name: 'Review' }))

    await waitFor(() => {
      expect(screen.getByText('WAOOAW Launch Channel connected')).toBeInTheDocument()
    })
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
      expect(screen.getByText('My Agents (1)')).toBeInTheDocument()
    })

    await openDetailedWorkspace()
    fireEvent.click(screen.getByRole('button', { name: 'Goal Setting' }))

    await waitFor(() => {
      expect(screen.getByText('Drafts (1)')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByRole('button', { name: 'Review' }))

    await waitFor(() => {
      expect(screen.getByText('Dormant Channel reconnect required')).toBeInTheDocument()
    })
    expect(screen.getByRole('button', { name: 'Open YouTube setup' })).toBeInTheDocument()
  })

  it('renders the inline studio rail alongside the selected subscription UI', async () => {
    renderWithProvider(<MyAgents />)

    await waitFor(() => {
      expect(screen.getByText('Selected hire')).toBeInTheDocument()
    })

    expect(screen.getByRole('button', { name: /Identity setup/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Platform connections/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Review and (activate|approve)/i })).toBeInTheDocument()
    expect(screen.getByText('Subscription')).toBeInTheDocument()
    expect(screen.getByText('SUB-1')).toBeInTheDocument()
  })

  it('keeps identity and YouTube setup actions inline inside the studio shell', async () => {
    const summaryModule = await import('../services/myAgentsSummary.service')
    const deliverablesModule = await import('../services/hiredAgentDeliverables.service')
    const connectionsModule = await import('../services/platformConnections.service')
    const youtubeModule = await import('../services/youtubeConnections.service')

    vi.mocked(summaryModule.getMyAgentsSummary).mockResolvedValueOnce({
      instances: [
        {
          subscription_id: 'SUB-MKT-4',
          agent_id: 'AGT-MKT-YT-004',
          duration: 'monthly',
          status: 'active',
          current_period_start: '2026-03-01T00:00:00Z',
          current_period_end: '2026-04-01T00:00:00Z',
          cancel_at_period_end: false,
          hired_instance_id: 'HIRED-MKT-4',
          agent_type_id: 'marketing.digital_marketing.v1',
          nickname: 'Digital Marketing Agent',
        },
      ],
    })
    vi.mocked(deliverablesModule.listHiredAgentDeliverables).mockResolvedValueOnce({
      hired_instance_id: 'HIRED-MKT-4',
      deliverables: [
        {
          deliverable_id: 'DEL-MKT-4',
          hired_instance_id: 'HIRED-MKT-4',
          goal_instance_id: 'GOAL-MKT-4',
          goal_template_id: 'marketing.theme_discovery.v1',
          title: 'YouTube growth draft',
          payload: { destination: { destination_type: 'youtube' }, summary: 'Draft pending exact approval.' },
          review_status: 'pending_review',
          review_notes: null,
          approval_id: null,
          execution_status: 'not_executed',
          created_at: null,
          updated_at: null,
        },
      ],
    })
    vi.mocked(connectionsModule.listPlatformConnections).mockResolvedValueOnce([])
    vi.mocked(youtubeModule.listYouTubeConnections).mockResolvedValueOnce([])

    renderWithProvider(<MyAgents initialStudioStep="review" initialStudioFocus="review" initialSubscriptionId="SUB-MKT-4" />)

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Open identity setup' })).toBeInTheDocument()
    })

    fireEvent.click(screen.getByRole('button', { name: 'Open identity setup' }))
    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Continue to platform connections' })).toBeInTheDocument()
    })
    expect(navigateMock).not.toHaveBeenCalled()

    fireEvent.click(screen.getByRole('button', { name: /Review and (activate|approve)/i }))
    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Open YouTube setup' })).toBeInTheDocument()
    })

    fireEvent.click(screen.getByRole('button', { name: 'Open YouTube setup' }))
    await waitFor(() => {
      expect(screen.getByText('YouTube channel status')).toBeInTheDocument()
      expect(screen.getByText(/platform connections/i)).toBeInTheDocument()
    })
    expect(navigateMock).not.toHaveBeenCalled()
    expect(screen.queryByText('Saved Theme Discovery brief')).not.toBeInTheDocument()
  })
})
