import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { FluentProvider } from '@fluentui/react-components'
import { waooawLightTheme } from '../theme'
import MyAgents from '../pages/authenticated/MyAgents'

const renderWithProvider = (component: React.ReactElement) => {
  return render(
    <FluentProvider theme={waooawLightTheme}>
      {component}
    </FluentProvider>
  )
}

describe('MyAgents Component', () => {
  it('renders page title with agent count', () => {
    renderWithProvider(<MyAgents />)
    expect(screen.getByText('My Active Agents (2)')).toBeInTheDocument()
  })

  it('displays hire new agent button', () => {
    renderWithProvider(<MyAgents />)
    expect(screen.getByText('+ Hire New Agent')).toBeInTheDocument()
  })

  it('shows agent cards', () => {
    renderWithProvider(<MyAgents />)
    expect(screen.getByText('Content Marketing Agent')).toBeInTheDocument()
    expect(screen.getByText('SDR Agent')).toBeInTheDocument()
  })

  it('displays agent status badges', () => {
    renderWithProvider(<MyAgents />)
    expect(screen.getByText('Active')).toBeInTheDocument()
    expect(screen.getByText('Working')).toBeInTheDocument()
  })

  it('shows goal completion progress', () => {
    renderWithProvider(<MyAgents />)
    expect(screen.getByText('Current Goals (3/5 Complete):')).toBeInTheDocument()
  })
})
