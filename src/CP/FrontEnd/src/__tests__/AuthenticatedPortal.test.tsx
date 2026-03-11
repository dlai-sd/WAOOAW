/**
 * Tests for AuthenticatedPortal navigation structure (CP-NAV-1)
 * Verifies the 8 sidebar items per the UX analysis navigation spec.
 */

import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import AuthenticatedPortal from '../pages/AuthenticatedPortal'
import { getMyAgentsSummary } from '../services/myAgentsSummary.service'
import { listHiredAgentDeliverables } from '../services/hiredAgentDeliverables.service'

vi.mock('../services/myAgentsSummary.service', () => ({
  getMyAgentsSummary: vi.fn().mockResolvedValue({
    instances: [
      {
        subscription_id: 'SUB-1',
        agent_id: 'AGT-MKT-001',
        hired_instance_id: 'HIRED-1',
        nickname: 'Healthcare Content Agent',
        duration: 'monthly',
        status: 'active',
        current_period_start: '2026-03-01T00:00:00Z',
        current_period_end: '2026-04-01T00:00:00Z',
        cancel_at_period_end: false,
      },
    ],
  }),
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
          goal_template_id: 'TPL-1',
          title: 'YouTube thought leadership draft',
          payload: {
            summary: 'Awaiting your approval before the agent publishes it.',
            destination: {
              destination_type: 'youtube',
              metadata: {
                visibility: 'private',
              },
            },
          },
          review_status: 'pending_review',
          execution_status: 'not_executed',
          created_at: '2026-03-10T12:00:00Z',
          updated_at: '2026-03-10T12:15:00Z',
        },
      ],
    }),
  }
})

vi.mock('../services/platformConnections.service', async () => {
  const actual = await vi.importActual<any>('../services/platformConnections.service')
  return {
    ...actual,
    listPlatformConnections: vi.fn().mockResolvedValue([
      {
        id: 'CONN-1',
        hired_instance_id: 'HIRED-1',
        skill_id: 'default',
        platform_key: 'youtube',
        status: 'connected',
        connected_at: '2026-03-10T12:00:00Z',
        last_verified_at: '2026-03-10T12:05:00Z',
        created_at: '2026-03-10T12:00:00Z',
        updated_at: '2026-03-10T12:05:00Z',
      },
    ]),
  }
})

// Mock heavy page components so tests are fast
vi.mock('../pages/authenticated/CommandCentre', () => ({
  default: () => <div data-testid="page-command-centre">Command Centre Page</div>,
}))
vi.mock('../pages/authenticated/MyAgents', () => ({
  default: () => <div data-testid="page-my-agents">My Agents Page</div>,
}))
vi.mock('../pages/authenticated/GoalsSetup', () => ({
  default: () => <div data-testid="page-goals">Theme Discovery Goals Page</div>,
}))
vi.mock('../pages/authenticated/Deliverables', () => ({
  default: () => <div data-testid="page-deliverables">Deliverables Page</div>,
}))
vi.mock('../pages/authenticated/Inbox', () => ({
  default: ({ items }: { items?: Array<{ channelStatusLabel?: string | null; publishReadinessLabel?: string | null }> }) => (
    <div data-testid="page-inbox">
      Inbox Page
      <div>{items?.[0]?.channelStatusLabel || 'No channel status'}</div>
      <div>{items?.[0]?.publishReadinessLabel || 'No readiness state'}</div>
    </div>
  ),
}))
vi.mock('../pages/authenticated/UsageBilling', () => ({
  default: () => <div data-testid="page-billing">Billing Page</div>,
}))
vi.mock('../pages/authenticated/ProfileSettings', () => ({
  default: () => <div data-testid="page-profile-settings">Profile & Settings Page</div>,
}))
vi.mock('../pages/AgentDiscovery', () => ({
  default: ({ onSelectAgent }: { onSelectAgent?: (agentId: string) => void }) => (
    <div data-testid="page-discover">
      Discover Page
      <button onClick={() => onSelectAgent?.('AGT-42')} data-testid="discover-select-agent">
        Open Agent
      </button>
    </div>
  ),
}))
vi.mock('../pages/AgentDetail', () => ({
  default: ({ agentIdProp }: { agentIdProp?: string }) => <div data-testid="page-agent-detail">Agent Detail {agentIdProp}</div>,
}))

const navigateMock = vi.fn()
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => navigateMock,
  }
})

async function renderPortal(props?: Partial<React.ComponentProps<typeof AuthenticatedPortal>>) {
  const view = render(
    <BrowserRouter>
      <AuthenticatedPortal
        theme="light"
        toggleTheme={() => {}}
        onLogout={() => {}}
        {...props}
      />
    </BrowserRouter>
  )

  await waitFor(() => {
    expect(vi.mocked(getMyAgentsSummary)).toHaveBeenCalled()
    expect(vi.mocked(listHiredAgentDeliverables)).toHaveBeenCalled()
  })

  return view
}

describe('AuthenticatedPortal — navigation structure (CP-NAV-1)', () => {
  it('renders Command Centre as the default page', async () => {
    await renderPortal()
    expect(screen.getByTestId('page-command-centre')).toBeTruthy()
  })

  it('renders all 7 internal sidebar nav items', async () => {
    await renderPortal()
    expect(screen.getByText('Command Centre')).toBeTruthy()
    expect(screen.getByText('My Agents')).toBeTruthy()
    expect(screen.getByText('Goals')).toBeTruthy()
    expect(screen.getByText('Deliverables')).toBeTruthy()
    expect(screen.getByText('Inbox')).toBeTruthy()
    expect(screen.getByText('Subscriptions & Billing')).toBeTruthy()
    expect(screen.getByText('Profile & Settings')).toBeTruthy()
  })

  it('renders Discover as a sidebar item', async () => {
    await renderPortal()
    expect(screen.getByText('Discover')).toBeTruthy()
  })

  it('does not render old nav items (Approvals, Performance, Mobile App, Help)', async () => {
    await renderPortal()
    expect(screen.queryByText('Approvals')).toBeNull()
    expect(screen.queryByText('Performance')).toBeNull()
    expect(screen.queryByText('Mobile App')).toBeNull()
    expect(screen.queryByText('Help & Support')).toBeNull()
    expect(screen.queryByText('Dashboard')).toBeNull()
  })

  it('switches to My Agents page when sidebar item clicked', async () => {
    await renderPortal()
    fireEvent.click(screen.getByText('My Agents'))
    expect(screen.getByTestId('page-my-agents')).toBeTruthy()
  })

  it('switches to Deliverables page when sidebar item clicked', async () => {
    await renderPortal()
    fireEvent.click(screen.getByText('Deliverables'))
    expect(screen.getByTestId('page-deliverables')).toBeTruthy()
  })

  it('switches to Goals page when sidebar item clicked', async () => {
    await renderPortal()
    fireEvent.click(screen.getByText('Goals'))
    expect(screen.getByTestId('page-goals')).toBeTruthy()
    expect(screen.getByText('Theme Discovery Goals Page')).toBeTruthy()
  })

  it('switches to Inbox page when sidebar item clicked', async () => {
    await renderPortal()
    fireEvent.click(screen.getByText('Inbox'))
    expect(screen.getByTestId('page-inbox')).toBeTruthy()
  })

  it('switches to Profile & Settings page when sidebar item clicked', async () => {
    await renderPortal()
    fireEvent.click(screen.getByText('Profile & Settings'))
    expect(screen.getByTestId('page-profile-settings')).toBeTruthy()
  })

  it('renders AgentDiscovery inline when Discover clicked (no frame break)', async () => {
    await renderPortal()
    fireEvent.click(screen.getByText('Discover'))
    expect(screen.getByTestId('page-discover')).toBeTruthy()
    // Discover no longer navigates away — it renders inside the authenticated shell
    expect(navigateMock).not.toHaveBeenCalledWith('/discover')
  })

  it('shows inbox unread badge from live deliverable state', async () => {
    renderPortal()

    await waitFor(() => {
      const badge = document.querySelector('.sidebar-badge')
      expect(badge).toBeTruthy()
      expect(badge?.textContent).toBe('1')
    })
  })

  it('updates hero copy when billing is opened', async () => {
    await renderPortal()
    fireEvent.click(screen.getByText('Subscriptions & Billing'))

    expect(screen.getByRole('heading', { name: 'Understand What You Are Paying For' })).toBeTruthy()
    expect(screen.getByText('Live subscription view')).toBeTruthy()
    expect(screen.getByTestId('page-billing')).toBeTruthy()
  })

  it('keeps Discover highlighted while showing agent detail', async () => {
    await renderPortal()

    fireEvent.click(screen.getByText('Discover'))
    fireEvent.click(screen.getByTestId('discover-select-agent'))

    expect(screen.getByTestId('page-agent-detail')).toBeTruthy()
    expect(screen.getByText('Agent Detail AGT-42')).toBeTruthy()
    expect(screen.getByTestId('cp-nav-discover').className).toContain('active')
  })

  it('uses truthful shell copy instead of fake runtime counters', async () => {
    await renderPortal()

    expect(screen.getByText('Customer shell')).toBeTruthy()
    expect(screen.getByText('Truthful state first')).toBeTruthy()
    expect(screen.getByText('Open My Agents for runtime truth')).toBeTruthy()
    expect(screen.queryByText('1 approval waiting')).toBeNull()
    expect(screen.queryByText('2 active hires')).toBeNull()
  })

  it('shows a resume-setup banner when entering from payment confirmation', async () => {
    await renderPortal({
      initialPage: 'my-agents',
      initialAgentId: 'AGT-MKT-001',
      initialJourneyContext: {
        source: 'payment-confirmed',
        subscriptionId: 'SUB-123',
      },
    })

    expect(screen.getByTestId('cp-portal-entry-banner')).toBeTruthy()
    expect(screen.getByText('Setup is still required for AGT-MKT-001')).toBeTruthy()
    expect(screen.getByText('Agent: AGT-MKT-001')).toBeTruthy()
    expect(screen.getByText('Subscription: SUB-123')).toBeTruthy()

    fireEvent.click(screen.getByTestId('cp-portal-entry-primary'))

    expect(navigateMock).toHaveBeenCalledWith('/hire/setup/SUB-123?agentId=AGT-MKT-001')
  })

  it('lands on My Agents with truthful post-activation guidance', async () => {
    await renderPortal({
      initialPage: 'my-agents',
      initialAgentId: 'AGT-TRD-001',
      initialJourneyContext: {
        source: 'trial-activated',
        subscriptionId: 'SUB-456',
      },
    })

    expect(screen.getByTestId('page-my-agents')).toBeTruthy()
    expect(screen.getByText('AGT-TRD-001 is now in runtime setup')).toBeTruthy()
    expect(screen.getByText('Agent: AGT-TRD-001')).toBeTruthy()
  })
})
