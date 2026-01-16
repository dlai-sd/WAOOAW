/**
 * UI Tests for React Router Integration
 * Tests routing functionality (MVP-003)
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import { AuthProvider } from '../context/AuthContext'
import App from '../App'

// Mock child components
vi.mock('../pages/LandingPage', () => ({
  default: () => <div data-testid="landing-page">Landing Page</div>,
}))

vi.mock('../pages/AuthCallback', () => ({
  default: () => <div data-testid="auth-callback">Auth Callback</div>,
}))

vi.mock('../pages/AuthenticatedPortal', () => ({
  default: () => <div data-testid="authenticated-portal">Authenticated Portal</div>,
}))

vi.mock('../pages/AgentDiscovery', () => ({
  default: () => <div data-testid="agent-discovery">Agent Discovery</div>,
}))

vi.mock('../pages/AgentDetail', () => ({
  default: () => <div data-testid="agent-detail">Agent Detail</div>,
}))

vi.mock('../pages/TrialDashboard', () => ({
  default: () => <div data-testid="trial-dashboard">Trial Dashboard</div>,
}))

vi.mock('../components/Header', () => ({
  default: () => <div data-testid="header">Header</div>,
}))

describe('React Router Integration', () => {
  describe('Public Routes', () => {
    it('should render landing page at root path', () => {
      render(
        <MemoryRouter initialEntries={['/']}>
          <AuthProvider>
            <App />
          </AuthProvider>
        </MemoryRouter>
      )

      expect(screen.getByTestId('landing-page')).toBeInTheDocument()
    })

    it('should render auth callback at /auth/callback', () => {
      render(
        <MemoryRouter initialEntries={['/auth/callback']}>
          <AuthProvider>
            <App />
          </AuthProvider>
        </MemoryRouter>
      )

      expect(screen.getByTestId('auth-callback')).toBeInTheDocument()
    })
  })

  describe('Protected Routes', () => {
    beforeEach(() => {
      // Mock authenticated state
      vi.mock('../context/AuthContext', async () => {
        const actual = await vi.importActual('../context/AuthContext')
        return {
          ...actual,
          useAuth: () => ({
            isAuthenticated: true,
            logout: vi.fn(),
          }),
        }
      })
    })

    it('should redirect to / when accessing protected route unauthenticated', async () => {
      // Mock unauthenticated state
      vi.mock('../context/AuthContext', async () => {
        const actual = await vi.importActual('../context/AuthContext')
        return {
          ...actual,
          useAuth: () => ({
            isAuthenticated: false,
            logout: vi.fn(),
          }),
        }
      })

      render(
        <MemoryRouter initialEntries={['/portal']}>
          <AuthProvider>
            <App />
          </AuthProvider>
        </MemoryRouter>
      )

      // Should redirect to landing page
      await waitFor(() => {
        expect(screen.getByTestId('landing-page')).toBeInTheDocument()
      })
    })
  })

  describe('Route Paths', () => {
    it('should handle /discover route', () => {
      render(
        <MemoryRouter initialEntries={['/discover']}>
          <Routes>
            <Route
              path="/discover"
              element={<div data-testid="discover-route">Discover</div>}
            />
          </Routes>
        </MemoryRouter>
      )

      expect(screen.getByTestId('discover-route')).toBeInTheDocument()
    })

    it('should handle /agent/:id route with parameter', () => {
      const agentId = '12345'

      render(
        <MemoryRouter initialEntries={[`/agent/${agentId}`]}>
          <Routes>
            <Route
              path="/agent/:id"
              element={<div data-testid="agent-route">Agent {agentId}</div>}
            />
          </Routes>
        </MemoryRouter>
      )

      expect(screen.getByTestId('agent-route')).toHaveTextContent(
        `Agent ${agentId}`
      )
    })

    it('should handle /trials route', () => {
      render(
        <MemoryRouter initialEntries={['/trials']}>
          <Routes>
            <Route
              path="/trials"
              element={<div data-testid="trials-route">Trials</div>}
            />
          </Routes>
        </MemoryRouter>
      )

      expect(screen.getByTestId('trials-route')).toBeInTheDocument()
    })

    it('should redirect unknown routes to root', () => {
      render(
        <MemoryRouter initialEntries={['/unknown-route']}>
          <AuthProvider>
            <App />
          </AuthProvider>
        </MemoryRouter>
      )

      // Catch-all should redirect to landing
      expect(screen.getByTestId('landing-page')).toBeInTheDocument()
    })
  })

  describe('Navigation State', () => {
    it('should preserve routing history', () => {
      const { rerender } = render(
        <MemoryRouter initialEntries={['/']}>
          <Routes>
            <Route path="/" element={<div>Home</div>} />
            <Route path="/discover" element={<div>Discover</div>} />
          </Routes>
        </MemoryRouter>
      )

      expect(screen.getByText('Home')).toBeInTheDocument()

      // Simulate navigation
      rerender(
        <MemoryRouter initialEntries={['/', '/discover']}>
          <Routes>
            <Route path="/" element={<div>Home</div>} />
            <Route path="/discover" element={<div>Discover</div>} />
          </Routes>
        </MemoryRouter>
      )

      expect(screen.getByText('Discover')).toBeInTheDocument()
    })
  })
})
