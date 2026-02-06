import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { FluentProvider } from '@fluentui/react-components'
import { GoogleOAuthProvider } from '@react-oauth/google'
import { BrowserRouter } from 'react-router-dom'
import { waooawLightTheme } from '../theme'
import App from '../App'

// Mock environment variable
const GOOGLE_CLIENT_ID = 'test-client-id'

// Mock Google OAuth
vi.mock('@react-oauth/google', async () => {
  const actual = await vi.importActual('@react-oauth/google')
  return {
    ...actual,
    GoogleOAuthProvider: ({ children }: any) => <>{children}</>,
    GoogleLogin: () => <button data-testid="mock-google-login">Sign in with Google</button>
  }
})

// Helper to render with FluentProvider, GoogleOAuthProvider, and BrowserRouter
const renderWithProvider = (component: React.ReactElement) => {
  return render(
    <BrowserRouter>
      <GoogleOAuthProvider clientId={GOOGLE_CLIENT_ID}>
        <FluentProvider theme={waooawLightTheme}>
          {component}
        </FluentProvider>
      </GoogleOAuthProvider>
    </BrowserRouter>
  )
}

describe('App Component', () => {
  it('shows a session expired notice when auth-expired flag is set', () => {
    sessionStorage.setItem('waooaw:auth-expired', '1')
    renderWithProvider(<App />)
    expect(screen.getByText(/session expired/i)).toBeInTheDocument()
  })

  it('renders landing page when not authenticated', () => {
    renderWithProvider(<App />)
    expect(screen.getByText('Sign In')).toBeInTheDocument()
  })

  it('opens auth modal when sign in button clicked', () => {
    renderWithProvider(<App />)
    const signInButton = screen.getByText('Sign In')
    fireEvent.click(signInButton)
    // Modal should open
    expect(screen.getByText(/Sign in to/i)).toBeInTheDocument()
  })

  it('allows theme toggle', () => {
    renderWithProvider(<App />)
    const themeButton = screen.getByLabelText('Toggle theme')
    expect(themeButton).toBeInTheDocument()
    fireEvent.click(themeButton)
    // Theme toggled successfully
  })
})
