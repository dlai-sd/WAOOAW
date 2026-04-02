import { render, screen, waitFor, within } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import CommandCentre from '../pages/authenticated/CommandCentre'

const { getMyAgentsSummaryMock } = vi.hoisted(() => ({
  getMyAgentsSummaryMock: vi.fn(),
}))

vi.mock('../services/myAgentsSummary.service', () => ({
  getMyAgentsSummary: getMyAgentsSummaryMock,
}))

describe('CommandCentre', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders live counts from the my agents summary response', async () => {
    getMyAgentsSummaryMock.mockResolvedValueOnce({
      instances: [
        {
          subscription_id: 'SUB-1',
          agent_id: 'AGT-1',
          duration: 'monthly',
          status: 'active',
          current_period_start: '',
          current_period_end: '',
          cancel_at_period_end: false,
          configured: false,
          goals_completed: false,
          trial_status: 'active',
        },
        {
          subscription_id: 'SUB-2',
          agent_id: 'AGT-2',
          duration: 'monthly',
          status: 'active',
          current_period_start: '',
          current_period_end: '',
          cancel_at_period_end: false,
          configured: true,
          goals_completed: true,
          trial_status: 'expired',
        },
        {
          subscription_id: 'SUB-3',
          agent_id: 'AGT-3',
          duration: 'monthly',
          status: 'active',
          current_period_start: '',
          current_period_end: '',
          cancel_at_period_end: false,
          configured: true,
          goals_completed: true,
          trial_status: 'expired',
        },
      ],
    })

    render(
      <CommandCentre
        onOpenBilling={vi.fn()}
        onOpenDiscover={vi.fn()}
        onOpenGoals={vi.fn()}
        onOpenMyAgents={vi.fn()}
      />
    )

    expect(screen.getByText('Loading dashboard data...')).toBeInTheDocument()

    const totalAgentsCard = await screen.findByText('Total agents')
    expect(within(totalAgentsCard.closest('.stat-card') as HTMLElement).getByText('3')).toBeInTheDocument()
    expect(within(screen.getByText('In trial').closest('.stat-card') as HTMLElement).getByText('1')).toBeInTheDocument()
    expect(within(screen.getByText('Need setup').closest('.stat-card') as HTMLElement).getByText('1')).toBeInTheDocument()
    expect(screen.getByText(/1 agent needs setup/i)).toBeInTheDocument()
  })

  it('renders an error state when dashboard loading fails', async () => {
    getMyAgentsSummaryMock.mockRejectedValueOnce(new Error('boom'))

    render(
      <CommandCentre
        onOpenBilling={vi.fn()}
        onOpenDiscover={vi.fn()}
        onOpenGoals={vi.fn()}
        onOpenMyAgents={vi.fn()}
      />
    )

    expect(await screen.findByText('Failed to load dashboard data.')).toBeInTheDocument()
  })

  it('shows the hire-your-first-agent priority when the workspace is empty', async () => {
    getMyAgentsSummaryMock.mockResolvedValueOnce({ instances: [] })

    render(
      <CommandCentre
        onOpenBilling={vi.fn()}
        onOpenDiscover={vi.fn()}
        onOpenGoals={vi.fn()}
        onOpenMyAgents={vi.fn()}
      />
    )

    await waitFor(() => {
      expect(screen.getByText('Hire your first agent from Discover to get started.')).toBeInTheDocument()
    })
  })
}
