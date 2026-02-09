import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { FluentProvider } from '@fluentui/react-components'
import { MemoryRouter } from 'react-router-dom'
import { waooawLightTheme } from '../theme'
import MyAgents from '../pages/authenticated/MyAgents'

vi.mock('../services/subscriptions.service', () => ({
  listSubscriptions: vi.fn().mockResolvedValue([
    {
      subscription_id: 'SUB-1',
      agent_id: 'agent-123',
      duration: 'monthly',
      status: 'active',
      current_period_start: '2026-02-01T00:00:00Z',
      current_period_end: '2026-03-01T00:00:00Z',
      cancel_at_period_end: false
    }
  ]),
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
  it('renders page title with agent count', () => {
    renderWithProvider(<MyAgents />)
    expect(screen.getByText('My Active Agents (0)')).toBeInTheDocument()
  })

  it('displays hire new agent button', () => {
    renderWithProvider(<MyAgents />)
    expect(screen.getByText('+ Hire New Agent')).toBeInTheDocument()
  })

  it('loads subscriptions and can schedule cancel', async () => {
    const { cancelSubscription } = await import('../services/subscriptions.service')

    renderWithProvider(<MyAgents />)

    await waitFor(() => {
      expect(screen.getByText('agent-123')).toBeInTheDocument()
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
})
