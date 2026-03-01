/**
 * Tests for AuthenticatedPortal navigation structure (CP-NAV-1)
 * Verifies the 8 sidebar items per the UX analysis navigation spec.
 */

import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import AuthenticatedPortal from '../pages/AuthenticatedPortal'

// Mock heavy page components so tests are fast
vi.mock('../pages/authenticated/CommandCentre', () => ({
  default: () => <div data-testid="page-command-centre">Command Centre Page</div>,
}))
vi.mock('../pages/authenticated/MyAgents', () => ({
  default: () => <div data-testid="page-my-agents">My Agents Page</div>,
}))
vi.mock('../pages/authenticated/GoalsSetup', () => ({
  default: () => <div data-testid="page-goals">Goals Page</div>,
}))
vi.mock('../pages/authenticated/Deliverables', () => ({
  default: () => <div data-testid="page-deliverables">Deliverables Page</div>,
}))
vi.mock('../pages/authenticated/Inbox', () => ({
  default: () => <div data-testid="page-inbox">Inbox Page</div>,
}))
vi.mock('../pages/authenticated/UsageBilling', () => ({
  default: () => <div data-testid="page-billing">Billing Page</div>,
}))
vi.mock('../pages/authenticated/ProfileSettings', () => ({
  default: () => <div data-testid="page-profile-settings">Profile & Settings Page</div>,
}))
vi.mock('../pages/AgentDiscovery', () => ({
  default: () => <div data-testid="page-discover">Discover Page</div>,
}))

const navigateMock = vi.fn()
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => navigateMock,
  }
})

function renderPortal() {
  return render(
    <BrowserRouter>
      <AuthenticatedPortal
        theme="light"
        toggleTheme={() => {}}
        onLogout={() => {}}
      />
    </BrowserRouter>
  )
}

describe('AuthenticatedPortal — navigation structure (CP-NAV-1)', () => {
  it('renders Command Centre as the default page', () => {
    renderPortal()
    expect(screen.getByTestId('page-command-centre')).toBeTruthy()
  })

  it('renders all 7 internal sidebar nav items', () => {
    renderPortal()
    expect(screen.getByText('Command Centre')).toBeTruthy()
    expect(screen.getByText('My Agents')).toBeTruthy()
    expect(screen.getByText('Goals')).toBeTruthy()
    expect(screen.getByText('Deliverables')).toBeTruthy()
    expect(screen.getByText('Inbox')).toBeTruthy()
    expect(screen.getByText('Subscriptions & Billing')).toBeTruthy()
    expect(screen.getByText('Profile & Settings')).toBeTruthy()
  })

  it('renders Discover as a sidebar item', () => {
    renderPortal()
    expect(screen.getByText('Discover')).toBeTruthy()
  })

  it('does not render old nav items (Approvals, Performance, Mobile App, Help)', () => {
    renderPortal()
    expect(screen.queryByText('Approvals')).toBeNull()
    expect(screen.queryByText('Performance')).toBeNull()
    expect(screen.queryByText('Mobile App')).toBeNull()
    expect(screen.queryByText('Help & Support')).toBeNull()
    expect(screen.queryByText('Dashboard')).toBeNull()
  })

  it('switches to My Agents page when sidebar item clicked', () => {
    renderPortal()
    fireEvent.click(screen.getByText('My Agents'))
    expect(screen.getByTestId('page-my-agents')).toBeTruthy()
  })

  it('switches to Deliverables page when sidebar item clicked', () => {
    renderPortal()
    fireEvent.click(screen.getByText('Deliverables'))
    expect(screen.getByTestId('page-deliverables')).toBeTruthy()
  })

  it('switches to Inbox page when sidebar item clicked', () => {
    renderPortal()
    fireEvent.click(screen.getByText('Inbox'))
    expect(screen.getByTestId('page-inbox')).toBeTruthy()
  })

  it('switches to Profile & Settings page when sidebar item clicked', () => {
    renderPortal()
    fireEvent.click(screen.getByText('Profile & Settings'))
    expect(screen.getByTestId('page-profile-settings')).toBeTruthy()
  })

  it('renders AgentDiscovery inline when Discover clicked (no frame break)', () => {
    renderPortal()
    fireEvent.click(screen.getByText('Discover'))
    expect(screen.getByTestId('page-discover')).toBeTruthy()
    // Discover no longer navigates away — it renders inside the authenticated shell
    expect(navigateMock).not.toHaveBeenCalledWith('/discover')
  })

  it('shows inbox unread badge', () => {
    renderPortal()
    // The inbox badge shows count 1
    const badge = document.querySelector('.sidebar-badge')
    expect(badge).toBeTruthy()
    expect(badge?.textContent).toBe('1')
  })
})
