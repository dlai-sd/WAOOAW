import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { FluentProvider } from '@fluentui/react-components'
import { waooawLightTheme } from '../theme'
import Dashboard from '../pages/authenticated/Dashboard'

const renderWithProvider = (component: React.ReactElement) => {
  return render(
    <FluentProvider theme={waooawLightTheme}>
      {component}
    </FluentProvider>
  )
}

describe('Dashboard Component', () => {
  it('renders dashboard title', () => {
    renderWithProvider(<Dashboard />)
    expect(screen.getByText('Dashboard')).toBeInTheDocument()
  })

  it('displays agent stats', () => {
    renderWithProvider(<Dashboard />)
    expect(screen.getByText('2 Agents')).toBeInTheDocument()
    expect(screen.getByText('Active')).toBeInTheDocument()
  })

  it('shows activity feed', () => {
    renderWithProvider(<Dashboard />)
    expect(screen.getByText('Agent Activity Feed')).toBeInTheDocument()
    const agentElements = screen.getAllByText('Content Marketing Agent')
    expect(agentElements.length).toBeGreaterThan(0)
  })

  it('displays quick actions', () => {
    renderWithProvider(<Dashboard />)
    expect(screen.getByText('Quick Actions')).toBeInTheDocument()
    expect(screen.getByText('🎯 Add New Goal')).toBeInTheDocument()
  })
})
