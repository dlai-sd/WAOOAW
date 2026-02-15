import { describe, it, expect, vi } from 'vitest'
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
        agent_type_id: 'trading.share_trader.v1'
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

vi.mock('../services/platformCredentials.service', () => ({
  upsertPlatformCredential: vi.fn()
}))

vi.mock('../services/exchangeSetup.service', () => ({
  upsertExchangeSetup: vi.fn()
}))

vi.mock('../services/hiredAgentDeliverables.service', () => ({
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
}))


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

  it('renders Goal Setting templates and can save a goal', async () => {
    const { upsertHiredAgentGoal, listHiredAgentGoals } = await import('../services/hiredAgentGoals.service')

    renderWithProvider(<MyAgents />)

    await waitFor(() => {
      expect(screen.getByText('My Agents (1)')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByRole('button', { name: 'Goal Setting' }))

    await waitFor(() => {
      expect(listHiredAgentGoals).toHaveBeenCalledTimes(1)
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
})
