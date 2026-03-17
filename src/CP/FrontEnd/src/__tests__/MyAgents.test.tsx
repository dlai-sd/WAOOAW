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
    cancelSubscription: vi.fn(async () => ({}))
  }
})

vi.mock('../services/myAgentsSummary.service', () => {
  return {
    getMyAgentsSummary: vi.fn(async () => ({ instances: [] }))
  }
})

vi.mock('../services/hireWizard.service', () => {
  return {
    getHireWizardDraftBySubscription: vi.fn(async () => ({
      hired_instance_id: 'hire_1',
      subscription_id: 'sub_1',
      agent_id: 'AGT-MKT-DMA-001',
      agent_type_id: 'marketing.digital_marketing.v1',
      nickname: 'Growth Copilot',
      theme: 'default',
      config: {},
      configured: false,
      goals_completed: false,
      trial_status: 'not_started'
    }))
  }
})

vi.mock('../services/hiredAgentStudio.service', () => {
  return {
    getHiredAgentStudio: vi.fn(async () => ({
      hired_instance_id: 'hire_1',
      subscription_id: 'sub_1',
      agent_id: 'AGT-MKT-DMA-001',
      agent_type_id: 'marketing.digital_marketing.v1',
      customer_id: 'CUST-user-1',
      mode: 'activation',
      selection_required: false,
      current_step: 'connection',
      steps: [
        { key: 'identity', title: 'Identity and voice', complete: true, blocked: false, summary: 'Identity is ready.' },
        { key: 'connection', title: 'Connection', complete: false, blocked: false, summary: 'Connection still needs attention.' },
        { key: 'operating_plan', title: 'Operating plan', complete: false, blocked: false, summary: 'Operating plan still needs customer input.' },
        { key: 'review', title: 'Review and activate', complete: false, blocked: true, summary: 'Finish earlier steps first.' },
      ],
      identity: { nickname: 'Growth Copilot', theme: 'default', complete: true },
      connection: { platform_key: 'youtube', skill_id: 'default', connection_id: null, customer_platform_credential_id: null, status: 'missing', complete: false, summary: 'No verified publishing connection is attached yet.' },
      operating_plan: { complete: false, goals_completed: false, goal_count: 0, skill_config_count: 0, summary: 'Operating plan still needs customer input before review.' },
      review: { complete: false, summary: 'This agent still has incomplete steps before review.' },
      configured: false,
      goals_completed: false,
      trial_status: 'not_started',
      subscription_status: 'active',
      updated_at: '2026-03-17T00:00:00Z',
    })),
  }
})

vi.mock('../services/platformConnections.service', async () => {
  const actual = await vi.importActual<any>('../services/platformConnections.service')
  return {
    ...actual,
    listPlatformConnections: vi.fn(async () => [])
  }
})

vi.mock('../services/youtubeConnections.service', () => ({
  listYouTubeConnections: vi.fn(async () => [])
}))

describe('MyAgents', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  async function openDetailedWorkspace(): Promise<void> {
    fireEvent.click(await screen.findByRole('button', { name: /Operating plan/i }))
    fireEvent.click(await screen.findByRole('button', { name: 'Open operating plan' }))
  }

  it('routes a not-configured hire into the activation wizard', async () => {
    const summaryModule = await import('../services/myAgentsSummary.service')

    vi.mocked(summaryModule.getMyAgentsSummary).mockResolvedValueOnce({
      instances: [
        {
          subscription_id: 'sub_1',
          agent_id: 'agent_1',
          duration: 'monthly',
          status: 'active',
          current_period_start: '2026-02-01T00:00:00Z',
          current_period_end: '2026-03-01T00:00:00Z',
          cancel_at_period_end: false,
          hired_instance_id: 'hire_1',
          trial_status: 'pending',
          trial_start_at: null,
          trial_end_at: null,
          configured: false,
          goals_completed: false
        }
      ]
    })

    render(<MyAgents />)

    await waitFor(() => {
      expect(screen.getByTestId('cp-my-agents-activation-studio')).toBeTruthy()
    })
    expect(screen.getAllByText('Select agent').length).toBeGreaterThan(0)
    expect(screen.getByText('This is the only hired agent still waiting for activation.')).toBeTruthy()
  })

  it('shows the activation studio for a newly hired marketing agent', async () => {
    const summaryModule = await import('../services/myAgentsSummary.service')

    vi.mocked(summaryModule.getMyAgentsSummary).mockResolvedValueOnce({
      instances: [
        {
          subscription_id: 'sub_activation',
          agent_id: 'AGT-MKT-DMA-001',
          agent_type_id: 'marketing.digital_marketing.v1',
          duration: 'monthly',
          status: 'active',
          current_period_start: '2026-02-01T00:00:00Z',
          current_period_end: '2026-03-01T00:00:00Z',
          cancel_at_period_end: false,
          hired_instance_id: 'hire_activation',
          configured: false,
          goals_completed: false,
          trial_status: 'pending'
        }
      ]
    })

    render(<MyAgents />)

    expect(await screen.findByTestId('cp-my-agents-activation-studio')).toBeTruthy()
    expect(screen.getByText(/Guide one hired agent at a time through activation or edits/i)).toBeTruthy()
    expect(screen.getAllByText('Select agent').length).toBeGreaterThan(0)
    expect(screen.getAllByText('Identity and voice').length).toBeGreaterThan(0)
    expect(screen.getAllByText('YouTube connection').length).toBeGreaterThan(0)
    expect(screen.getAllByText('Operating plan').length).toBeGreaterThan(0)
    expect(screen.getAllByText('Review and activate').length).toBeGreaterThan(0)
  })

  it('shows countdown when trial is active', async () => {
    const nowSpy = vi.spyOn(Date, 'now').mockReturnValue(new Date('2026-02-01T00:00:00Z').getTime())

    const summaryModule = await import('../services/myAgentsSummary.service')

    vi.mocked(summaryModule.getMyAgentsSummary).mockResolvedValueOnce({
      instances: [
        {
          subscription_id: 'sub_2',
          agent_id: 'agent_2',
          duration: 'monthly',
          status: 'active',
          current_period_start: '2026-02-01T00:00:00Z',
          current_period_end: '2026-03-01T00:00:00Z',
          cancel_at_period_end: false,
          hired_instance_id: 'hire_2',
          trial_status: 'active',
          trial_start_at: '2026-02-01T00:00:00Z',
          trial_end_at: '2026-02-03T00:00:00Z',
          configured: true,
          goals_completed: false
        }
      ]
    })

    render(<MyAgents />)

    await openDetailedWorkspace()

    await waitFor(() => {
      expect(screen.getByText(/Trial ends in/i)).toBeTruthy()
    })

    expect(screen.getByText(/2d 0h/)).toBeTruthy()

    nowSpy.mockRestore()
  })

  it('shows post-cancel scheduled end message', async () => {
    const summaryModule = await import('../services/myAgentsSummary.service')

    vi.mocked(summaryModule.getMyAgentsSummary).mockResolvedValueOnce({
      instances: [
        {
          subscription_id: 'sub_cancel',
          agent_id: 'agent_cancel',
          duration: 'monthly',
          status: 'active',
          current_period_start: '2026-02-01T00:00:00Z',
          current_period_end: '2026-03-01T00:00:00Z',
          cancel_at_period_end: true
        }
      ]
    })

    render(<MyAgents />)

    await openDetailedWorkspace()

    await waitFor(() => {
      expect(screen.getByText(/Scheduled to end on/i)).toBeTruthy()
    })

    expect(screen.getByText(/read-only access/i)).toBeTruthy()
    expect(screen.getByText(/30 days/i)).toBeTruthy()
  })

  it('shows retention rules in cancel confirmation', async () => {
    const summaryModule = await import('../services/myAgentsSummary.service')

    vi.mocked(summaryModule.getMyAgentsSummary).mockResolvedValueOnce({
      instances: [
        {
          subscription_id: 'sub_confirm',
          agent_id: 'agent_confirm',
          duration: 'monthly',
          status: 'active',
          current_period_start: '2026-02-01T00:00:00Z',
          current_period_end: '2026-03-01T00:00:00Z',
          cancel_at_period_end: false
        }
      ]
    })

    render(<MyAgents />)

    await waitFor(() => {
      expect(screen.getByText('My Agents (1)')).toBeTruthy()
    })

    await openDetailedWorkspace()

    fireEvent.click(screen.getByText('End Hire'))

    await waitFor(() => {
      expect(screen.getByText(/End hire at next billing date/i)).toBeTruthy()
    })

    expect(screen.getByText(/After your hire ends/i)).toBeTruthy()
    expect(screen.getByText(/30 days/i)).toBeTruthy()
  })
})
