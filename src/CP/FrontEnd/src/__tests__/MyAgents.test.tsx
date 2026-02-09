import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'

import MyAgents from '../pages/authenticated/MyAgents'

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<any>('react-router-dom')
  return {
    ...actual,
    useNavigate: () => vi.fn()
  }
})

vi.mock('../services/subscriptions.service', () => {
  return {
    listSubscriptions: vi.fn(async () => []),
    cancelSubscription: vi.fn(async () => ({}))
  }
})

vi.mock('../services/trialStatus.service', () => {
  return {
    listTrialStatus: vi.fn(async () => [])
  }
})

describe('MyAgents', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('shows "Trial will start after setup" when not configured', async () => {
    const subsModule = await import('../services/subscriptions.service')
    const trialsModule = await import('../services/trialStatus.service')

    vi.mocked(subsModule.listSubscriptions).mockResolvedValueOnce([
      {
        subscription_id: 'sub_1',
        agent_id: 'agent_1',
        duration: 'monthly',
        status: 'active',
        current_period_start: '2026-02-01T00:00:00Z',
        current_period_end: '2026-03-01T00:00:00Z',
        cancel_at_period_end: false
      }
    ])

    vi.mocked(trialsModule.listTrialStatus).mockResolvedValueOnce([
      {
        subscription_id: 'sub_1',
        hired_instance_id: 'hire_1',
        trial_status: 'pending',
        trial_start_at: null,
        trial_end_at: null,
        configured: false,
        goals_completed: false
      }
    ])

    render(<MyAgents />)

    await waitFor(() => {
      expect(screen.getByText('Trial will start after setup')).toBeTruthy()
    })
  })

  it('shows countdown when trial is active', async () => {
    const nowSpy = vi.spyOn(Date, 'now').mockReturnValue(new Date('2026-02-01T00:00:00Z').getTime())

    const subsModule = await import('../services/subscriptions.service')
    const trialsModule = await import('../services/trialStatus.service')

    vi.mocked(subsModule.listSubscriptions).mockResolvedValueOnce([
      {
        subscription_id: 'sub_2',
        agent_id: 'agent_2',
        duration: 'monthly',
        status: 'active',
        current_period_start: '2026-02-01T00:00:00Z',
        current_period_end: '2026-03-01T00:00:00Z',
        cancel_at_period_end: false
      }
    ])

    vi.mocked(trialsModule.listTrialStatus).mockResolvedValueOnce([
      {
        subscription_id: 'sub_2',
        hired_instance_id: 'hire_2',
        trial_status: 'active',
        trial_start_at: '2026-02-01T00:00:00Z',
        trial_end_at: '2026-02-03T00:00:00Z',
        configured: true,
        goals_completed: false
      }
    ])

    render(<MyAgents />)

    await waitFor(() => {
      expect(screen.getByText(/Trial ends in/i)).toBeTruthy()
    })

    expect(screen.getByText(/2d 0h/)).toBeTruthy()

    nowSpy.mockRestore()
  })

  it('shows post-cancel scheduled end message', async () => {
    const subsModule = await import('../services/subscriptions.service')
    const trialsModule = await import('../services/trialStatus.service')

    vi.mocked(subsModule.listSubscriptions).mockResolvedValueOnce([
      {
        subscription_id: 'sub_cancel',
        agent_id: 'agent_cancel',
        duration: 'monthly',
        status: 'active',
        current_period_start: '2026-02-01T00:00:00Z',
        current_period_end: '2026-03-01T00:00:00Z',
        cancel_at_period_end: true
      }
    ])

    vi.mocked(trialsModule.listTrialStatus).mockResolvedValueOnce([])

    render(<MyAgents />)

    await waitFor(() => {
      expect(screen.getByText(/Scheduled to end on/i)).toBeTruthy()
    })

    expect(screen.getByText(/read-only access/i)).toBeTruthy()
    expect(screen.getByText(/30 days/i)).toBeTruthy()
  })

  it('shows retention rules in cancel confirmation', async () => {
    const subsModule = await import('../services/subscriptions.service')
    const trialsModule = await import('../services/trialStatus.service')

    vi.mocked(subsModule.listSubscriptions).mockResolvedValueOnce([
      {
        subscription_id: 'sub_confirm',
        agent_id: 'agent_confirm',
        duration: 'monthly',
        status: 'active',
        current_period_start: '2026-02-01T00:00:00Z',
        current_period_end: '2026-03-01T00:00:00Z',
        cancel_at_period_end: false
      }
    ])

    vi.mocked(trialsModule.listTrialStatus).mockResolvedValueOnce([])

    render(<MyAgents />)

    await waitFor(() => {
      expect(screen.getByText('My Active Agents (1)')).toBeTruthy()
    })

    fireEvent.click(screen.getByText('End Hire'))

    await waitFor(() => {
      expect(screen.getByText(/End hire at next billing date/i)).toBeTruthy()
    })

    expect(screen.getByText(/After your hire ends/i)).toBeTruthy()
    expect(screen.getByText(/30 days/i)).toBeTruthy()
  })
})
