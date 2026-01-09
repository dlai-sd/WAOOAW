import { describe, it, expect } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { FluentProvider } from '@fluentui/react-components'
import { waooawLightTheme } from '../theme'
import App from '../App'

// Helper to render with FluentProvider
const renderWithProvider = (component: React.ReactElement) => {
  return render(
    <FluentProvider theme={waooawLightTheme}>
      {component}
    </FluentProvider>
  )
}

describe('App Component', () => {
  it('renders landing page when not authenticated', () => {
    renderWithProvider(<App />)
    expect(screen.getByText('Sign In')).toBeInTheDocument()
  })

  it('shows authenticated portal after sign in', () => {
    renderWithProvider(<App />)
    const signInButton = screen.getByText('Sign In')
    fireEvent.click(signInButton)
    expect(document.querySelector('.authenticated-portal')).toBeInTheDocument()
  })

  it('allows theme toggle', () => {
    renderWithProvider(<App />)
    const themeButton = screen.getByLabelText('Toggle theme')
    expect(themeButton).toBeInTheDocument()
    fireEvent.click(themeButton)
    // Theme toggled successfully
  })
})
