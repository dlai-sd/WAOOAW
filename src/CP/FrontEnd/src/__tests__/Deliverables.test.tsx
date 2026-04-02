import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import Deliverables from '../pages/authenticated/Deliverables'

const {
  getMyAgentsSummaryMock,
  listHiredAgentDeliverablesMock,
  reviewHiredAgentDeliverableMock,
} = vi.hoisted(() => ({
  getMyAgentsSummaryMock: vi.fn(),
  listHiredAgentDeliverablesMock: vi.fn(),
  reviewHiredAgentDeliverableMock: vi.fn(),
}))

vi.mock('../services/myAgentsSummary.service', () => ({
  getMyAgentsSummary: getMyAgentsSummaryMock,
}))

vi.mock('../services/hiredAgentDeliverables.service', () => ({
  listHiredAgentDeliverables: listHiredAgentDeliverablesMock,
  reviewHiredAgentDeliverable: reviewHiredAgentDeliverableMock,
}))

function buildDeliverable(overrides: Record<string, unknown> = {}) {
  return {
    deliverable_id: 'DEL-1',
    hired_instance_id: 'HIRED-1',
    goal_instance_id: 'GOAL-1',
    goal_template_id: 'TPL-1',
    title: 'Real deliverable title',
    payload: {
      summary: 'A real payload summary that should render in the card.',
    },
    review_status: 'pending_review',
    execution_status: 'not_executed',
    created_at: '2026-04-02T12:00:00Z',
    updated_at: '2026-04-02T12:00:00Z',
    ...overrides,
  }
}

describe('Deliverables', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    getMyAgentsSummaryMock.mockResolvedValue({
      instances: [{ hired_instance_id: 'HIRED-1' }],
    })
    listHiredAgentDeliverablesMock.mockResolvedValue({
      hired_instance_id: 'HIRED-1',
      deliverables: [buildDeliverable()],
    })
    reviewHiredAgentDeliverableMock.mockResolvedValue({
      deliverable_id: 'DEL-1',
      review_status: 'approved',
    })
  })

  it('renders real deliverables from the API', async () => {
    listHiredAgentDeliverablesMock.mockResolvedValue({
      hired_instance_id: 'HIRED-1',
      deliverables: [
        buildDeliverable({ deliverable_id: 'DEL-1', title: 'Customer content brief' }),
        buildDeliverable({ deliverable_id: 'DEL-2', title: 'Launch email draft' }),
      ],
    })

    render(<Deliverables />)

    expect(screen.getByText('Loading deliverables...')).toBeInTheDocument()
    expect(await screen.findByText('Customer content brief')).toBeInTheDocument()
    expect(screen.getByText('Launch email draft')).toBeInTheDocument()
  })

  it('renders an error state when summary loading fails', async () => {
    getMyAgentsSummaryMock.mockRejectedValueOnce(new Error('boom'))

    render(<Deliverables />)

    expect(await screen.findByText('Failed to load deliverables. Please try again.')).toBeInTheDocument()
  })

  it('renders an empty state when the user has no hired agents', async () => {
    getMyAgentsSummaryMock.mockResolvedValueOnce({ instances: [] })

    render(<Deliverables />)

    expect(await screen.findByText(/No deliverables yet/i)).toBeInTheDocument()
  })

  it('renders the approved status badge text for approved deliverables', async () => {
    listHiredAgentDeliverablesMock.mockResolvedValueOnce({
      hired_instance_id: 'HIRED-1',
      deliverables: [buildDeliverable({ review_status: 'approved' })],
    })

    render(<Deliverables />)

    expect(await screen.findByText('approved')).toBeInTheDocument()
  })

  it('shows approve and reject actions for pending review deliverables', async () => {
    render(<Deliverables />)

    expect(await screen.findByRole('button', { name: 'Approve' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Reject' })).toBeInTheDocument()
  })

  it('hides review actions for approved deliverables', async () => {
    listHiredAgentDeliverablesMock.mockResolvedValueOnce({
      hired_instance_id: 'HIRED-1',
      deliverables: [buildDeliverable({ review_status: 'approved' })],
    })

    render(<Deliverables />)

    await screen.findByText('approved')
    expect(screen.queryByRole('button', { name: 'Approve' })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Reject' })).not.toBeInTheDocument()
  })

  it('approves a deliverable and updates the status badge', async () => {
    render(<Deliverables />)

    fireEvent.click(await screen.findByRole('button', { name: 'Approve' }))

    await waitFor(() => {
      expect(reviewHiredAgentDeliverableMock).toHaveBeenCalledWith('DEL-1', {
        decision: 'approved',
        notes: undefined,
      })
    })

    expect(await screen.findByText('approved')).toBeInTheDocument()
  })
}
