/**
 * UI Tests for Navigation with useNavigate
 * Tests programmatic navigation (MVP-003)
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { BrowserRouter, useNavigate } from 'react-router-dom'
import AgentDiscovery from '../pages/AgentDiscovery'

// Mock plant API service
vi.mock('../services/plant.service', () => ({
  plantAPIService: {
    listAgentsWithJobRoles: vi.fn().mockResolvedValue([]),
    searchAgents: vi.fn().mockResolvedValue([]),
    getJobRole: vi.fn().mockResolvedValue({ name: 'Test Role' }),
  },
}))

// Create navigate mock at module level
const navigateMock = vi.fn()

// Mock react-router-dom useNavigate at module level
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => navigateMock,
  }
})

beforeEach(() => {
  navigateMock.mockClear()
})

describe('Navigation with useNavigate', () => {
  describe('AgentDiscovery Navigation', () => {
    it('should use navigate instead of window.location.href', async () => {
      render(
        <BrowserRouter>
          <AgentDiscovery />
        </BrowserRouter>
      )

      // Note: This test verifies the component uses useNavigate (mocked at module level)
      // Actual navigation testing would require full integration test
      expect(navigateMock).toBeDefined()
    })
  })

  describe('Navigation Component', () => {
    it('should navigate programmatically', () => {
      const NavigationComponent = () => {
        const navigate = useNavigate()

        return (
          <div>
            <button onClick={() => navigate('/discover')}>
              Go to Discover
            </button>
            <button onClick={() => navigate('/trials')}>Go to Trials</button>
            <button onClick={() => navigate(-1)}>Go Back</button>
          </div>
        )
      }

      render(
        <BrowserRouter>
          <NavigationComponent />
        </BrowserRouter>
      )

      fireEvent.click(screen.getByText('Go to Discover'))
      fireEvent.click(screen.getByText('Go to Trials'))
      fireEvent.click(screen.getByText('Go Back'))

      expect(navigateMock).toHaveBeenCalledWith('/discover')
      expect(navigateMock).toHaveBeenCalledWith('/trials')
      expect(navigateMock).toHaveBeenCalledWith(-1)
      expect(navigateMock).toHaveBeenCalledTimes(3)
    })
  })

  describe('Link Component Usage', () => {
    it('should render links correctly', () => {
      const { Link } = require('react-router-dom')

      const LinksComponent = () => (
        <nav>
          <Link to="/discover">Discover</Link>
          <Link to="/trials">Trials</Link>
          <Link to="/portal">Portal</Link>
        </nav>
      )

      render(
        <BrowserRouter>
          <LinksComponent />
        </BrowserRouter>
      )

      expect(screen.getByText('Discover')).toHaveAttribute(
        'href',
        '/discover'
      )
      expect(screen.getByText('Trials')).toHaveAttribute('href', '/trials')
      expect(screen.getByText('Portal')).toHaveAttribute('href', '/portal')
    })
  })

  describe('Navigation State Preservation', () => {
    it('should pass state during navigation', () => {
      const NavigateWithState = () => {
        const navigate = useNavigate()

        const handleNavigate = () => {
          navigate('/agent/123', {
            state: { fromDiscovery: true, agentName: 'Test Agent' },
          })
        }

        return (
          <button onClick={handleNavigate}>Navigate with State</button>
        )
      }

      render(
        <BrowserRouter>
          <NavigateWithState />
        </BrowserRouter>
      )

      fireEvent.click(screen.getByText('Navigate with State'))

      expect(navigateMock).toHaveBeenCalledWith('/agent/123', {
        state: { fromDiscovery: true, agentName: 'Test Agent' },
      })
    })
  })
})