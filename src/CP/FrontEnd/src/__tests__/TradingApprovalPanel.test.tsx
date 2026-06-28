import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { FluentProvider } from '@fluentui/react-components'
import { waooawLightTheme } from '../theme'
import { TradingApprovalPanel } from '../components/TradingApprovalPanel'
import type { Deliverable } from '../services/hiredAgentDeliverables.service'

vi.mock('../services/hiredAgentDeliverables.service', () => ({
  listHiredAgentDeliverables: vi.fn(),
  reviewHiredAgentDeliverable: vi.fn(),
}))

const makeDeliverable = (overrides: Partial<Deliverable> = {}): Deliverable => ({
  deliverable_id: 'DEL-TRADE-1',
  hired_instance_id: 'HIRED-TRD-1',
  goal_instance_id: 'GOAL-TRD-1',
  goal_template_id: 'trading.trade_intent_draft.v1',
  title: 'BTC Buy Signal',
  payload: {
    coin: 'BTC',
    side: 'LONG',
    units: 0.1,
    stop_loss_price: 3000000,
    take_profit_price: 3500000,
  },
  review_status: 'pending_review',
  review_notes: null,
  approval_id: null,
  execution_status: 'not_executed',
  created_at: new Date(Date.now() - 5 * 60000).toISOString(), // 5 min ago
  updated_at: null,
  ...overrides,
})

const renderPanel = (hiredInstanceId = 'HIRED-TRD-1') =>
  render(
    <FluentProvider theme={waooawLightTheme}>
      <TradingApprovalPanel hiredInstanceId={hiredInstanceId} />
    </FluentProvider>
  )

describe('TradingApprovalPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('T1: pending deliverables render as TradingApprovalCard list', async () => {
    const { listHiredAgentDeliverables } = await import('../services/hiredAgentDeliverables.service')
    vi.mocked(listHiredAgentDeliverables).mockResolvedValue({
      hired_instance_id: 'HIRED-TRD-1',
      deliverables: [makeDeliverable()],
    })

    renderPanel()

    await waitFor(() => {
      expect(screen.getByTestId('trading-approval-panel')).toBeInTheDocument()
    })
    expect(screen.getByTestId('trade-approval-card-DEL-TRADE-1')).toBeInTheDocument()
    expect(screen.getByText('BTC')).toBeInTheDocument()
    expect(screen.getByText('BUY')).toBeInTheDocument()
  })

  it('T2: empty state renders when no pending deliverables', async () => {
    const { listHiredAgentDeliverables } = await import('../services/hiredAgentDeliverables.service')
    vi.mocked(listHiredAgentDeliverables).mockResolvedValue({
      hired_instance_id: 'HIRED-TRD-1',
      deliverables: [
        makeDeliverable({ review_status: 'approved' }),
        makeDeliverable({ deliverable_id: 'DEL-TRADE-2', review_status: 'rejected' }),
      ],
    })

    renderPanel()

    await waitFor(() => {
      expect(screen.getByTestId('approval-empty-state')).toBeInTheDocument()
    })
    expect(screen.getByText(/No pending trade approvals/)).toBeInTheDocument()
  })

  it('T3: Approve button calls reviewHiredAgentDeliverable with "approved" and removes card', async () => {
    const { listHiredAgentDeliverables, reviewHiredAgentDeliverable } = await import('../services/hiredAgentDeliverables.service')
    vi.mocked(listHiredAgentDeliverables).mockResolvedValue({
      hired_instance_id: 'HIRED-TRD-1',
      deliverables: [makeDeliverable()],
    })
    vi.mocked(reviewHiredAgentDeliverable).mockResolvedValue({
      deliverable_id: 'DEL-TRADE-1',
      review_status: 'approved',
      approval_id: 'APR-1',
      updated_at: new Date().toISOString(),
    })

    renderPanel()

    await waitFor(() => {
      expect(screen.getByTestId('approve-btn-DEL-TRADE-1')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByTestId('approve-btn-DEL-TRADE-1'))

    await waitFor(() => {
      expect(reviewHiredAgentDeliverable).toHaveBeenCalledWith('DEL-TRADE-1', { decision: 'approved' })
    })

    await waitFor(() => {
      expect(screen.queryByTestId('trade-approval-card-DEL-TRADE-1')).not.toBeInTheDocument()
    })
    expect(screen.getByTestId('approval-empty-state')).toBeInTheDocument()
  })

  it('T4: signal age warning shown when created_at > 15 min ago', async () => {
    const { listHiredAgentDeliverables } = await import('../services/hiredAgentDeliverables.service')
    vi.mocked(listHiredAgentDeliverables).mockResolvedValue({
      hired_instance_id: 'HIRED-TRD-1',
      deliverables: [
        makeDeliverable({
          created_at: new Date(Date.now() - 20 * 60000).toISOString(), // 20 min ago
        }),
      ],
    })

    renderPanel()

    await waitFor(() => {
      expect(screen.getByText(/Signal is \d+ min old — market may have moved/)).toBeInTheDocument()
    })
  })

  it('Reject button calls reviewHiredAgentDeliverable with "rejected" and removes card', async () => {
    const { listHiredAgentDeliverables, reviewHiredAgentDeliverable } = await import('../services/hiredAgentDeliverables.service')
    vi.mocked(listHiredAgentDeliverables).mockResolvedValue({
      hired_instance_id: 'HIRED-TRD-1',
      deliverables: [makeDeliverable()],
    })
    vi.mocked(reviewHiredAgentDeliverable).mockResolvedValue({
      deliverable_id: 'DEL-TRADE-1',
      review_status: 'rejected',
      approval_id: null,
      updated_at: new Date().toISOString(),
    })

    renderPanel()

    await waitFor(() => {
      expect(screen.getByTestId('reject-btn-DEL-TRADE-1')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByTestId('reject-btn-DEL-TRADE-1'))

    await waitFor(() => {
      expect(reviewHiredAgentDeliverable).toHaveBeenCalledWith('DEL-TRADE-1', { decision: 'rejected' })
    })

    await waitFor(() => {
      expect(screen.queryByTestId('trade-approval-card-DEL-TRADE-1')).not.toBeInTheDocument()
    })
  })
})
