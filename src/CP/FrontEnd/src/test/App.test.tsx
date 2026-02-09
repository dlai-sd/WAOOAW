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

  it('opens auth modal when Browse Agents is clicked while unauthenticated', () => {
    renderWithProvider(<App />)
    fireEvent.click(screen.getByRole('button', { name: 'Browse Agents' }))
    expect(screen.getByText(/Sign in to/i)).toBeInTheDocument()
  })

  it('redirects to landing and opens auth when visiting /discover unauthenticated', () => {
    window.history.pushState({}, '', '/discover')
    renderWithProvider(<App />)
    expect(screen.getByText(/Sign in to/i)).toBeInTheDocument()
  })

  it('allows theme toggle', () => {
    renderWithProvider(<App />)
    const themeButton = screen.getByLabelText('Toggle theme')
    expect(themeButton).toBeInTheDocument()
    fireEvent.click(themeButton)
    // Theme toggled successfully
  })

  it('restores session from stored token on refresh', async () => {
    // JWT with far-future exp; payload is not verified client-side.
    localStorage.setItem(
      'cp_access_token',
      'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiMSIsImVtYWlsIjoidUBleGFtcGxlLmNvbSIsInRva2VuX3R5cGUiOiJhY2Nlc3MiLCJleHAiOjQxMDAwMDAwMDAsImlhdCI6MTcwMDAwMDAwMH0.dummy'
    )

    // Simulate refreshing directly onto a protected route.
    window.history.pushState({}, '', '/portal')

    global.fetch = vi.fn(async (url: any) => {
      const u = String(url)
      if (u.endsWith('/auth/me')) {
        return new Response(
          JSON.stringify({
            id: '1',
            email: 'u@example.com',
            provider: 'google',
            created_at: '2026-01-01T00:00:00Z'
          }),
          { status: 200, headers: { 'Content-Type': 'application/json' } }
        )
      }
      return new Response(JSON.stringify({ detail: 'not found' }), { status: 404 })
    }) as any

    renderWithProvider(<App />)

    expect(await screen.findByText('Sign Out')).toBeInTheDocument()
  })
})
