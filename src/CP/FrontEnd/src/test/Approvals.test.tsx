import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { FluentProvider } from '@fluentui/react-components'
import { waooawLightTheme } from '../theme'
import Approvals from '../pages/authenticated/Approvals'

const renderWithProvider = (component: React.ReactElement) => {
  return render(
    <FluentProvider theme={waooawLightTheme}>
      {component}
    </FluentProvider>
  )
}

describe('Approvals Component', () => {
  it('renders page title with pending count', () => {
    renderWithProvider(<Approvals />)
    expect(screen.getByText('Pending Approvals (2)')).toBeInTheDocument()
  })

  it('displays filter and sort controls', () => {
    renderWithProvider(<Approvals />)
    const filterSelect = screen.getAllByRole('combobox')[0]
    expect(filterSelect).toBeInTheDocument()
  })

  it('shows approval requests', () => {
    renderWithProvider(<Approvals />)
    expect(screen.getByText('SDR Agent')).toBeInTheDocument()
    expect(screen.getByText('Content Marketing Agent')).toBeInTheDocument()
  })

  it('displays approval action buttons', () => {
    renderWithProvider(<Approvals />)
    expect(screen.getAllByText('✅ APPROVE')[0]).toBeInTheDocument()
    expect(screen.getAllByText('❌ DENY')[0]).toBeInTheDocument()
    expect(screen.getAllByText('⏸ DEFER')[0]).toBeInTheDocument()
  })

  it('shows risk and cost information', () => {
    renderWithProvider(<Approvals />)
    const riskElements = screen.getAllByText(/Risk Level:/)
    expect(riskElements.length).toBe(2)
    const costElements = screen.getAllByText(/Estimated Cost:/)
    expect(costElements.length).toBe(2)
  })
})
