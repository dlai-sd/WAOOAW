import { describe, it, expect, vi, beforeEach } from 'vitest'
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
  let fetchSpy: any

  beforeEach(() => {
    // Ensure each test starts from a clean route.
    window.history.pushState({}, '', '/')

    // Avoid cross-test leakage across the suite.
    localStorage.clear()
    sessionStorage.clear()
    vi.restoreAllMocks()

    // App mounts PaymentsConfigProvider which always fetches config; keep it deterministic.
    fetchSpy = vi.spyOn(globalThis, 'fetch' as any).mockImplementation(async (input: any) => {
      const url = String(input)

      if (url.endsWith('/cp/payments/config')) {
        return new Response(JSON.stringify({ mode: 'coupon' }), {
          status: 200,
          headers: { 'Content-Type': 'application/json' }
        })
      }

      return new Response(JSON.stringify({ detail: 'not found' }), {
        status: 404,
        headers: { 'Content-Type': 'application/json' }
      })
    })
  })

  it('shows a session expired notice when auth-expired flag is set', () => {
    sessionStorage.setItem('waooaw:auth-expired', '1')
    renderWithProvider(<App />)
    expect(screen.getByText(/session expired/i)).toBeInTheDocument()
  })

  it('renders landing page when not authenticated', () => {
    renderWithProvider(<App />)
    expect(screen.getByText('Sign In')).toBeInTheDocument()
    expect(screen.getByText('Sign Up')).toBeInTheDocument()
  })

  it('navigates to sign-in page when sign in button clicked', async () => {
    renderWithProvider(<App />)
    const signInButton = screen.getByText('Sign In')
    fireEvent.click(signInButton)
    expect(await screen.findByText(/Sign in to WAOOAW/i)).toBeInTheDocument()
  })

  it('redirects to sign-in when Browse Agents is clicked while unauthenticated', async () => {
    renderWithProvider(<App />)
    fireEvent.click(screen.getByRole('button', { name: 'Browse Agents' }))
    expect(await screen.findByText(/Sign in to WAOOAW/i)).toBeInTheDocument()
  })

  it('redirects to sign-in when visiting /discover unauthenticated', async () => {
    window.history.pushState({}, '', '/discover')
    renderWithProvider(<App />)
    expect(await screen.findByText(/Sign in to WAOOAW/i)).toBeInTheDocument()
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
    // Backward compatibility: some sessions rely on token_expires_at.
    localStorage.setItem('token_expires_at', String(Date.now() + 24 * 60 * 60 * 1000))

    // Simulate refreshing directly onto a protected route.
    window.history.pushState({}, '', '/portal')

    fetchSpy.mockImplementation(async (url: any) => {
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
      if (u.endsWith('/cp/payments/config')) {
        return new Response(JSON.stringify({ mode: 'coupon' }), {
          status: 200,
          headers: { 'Content-Type': 'application/json' }
        })
      }
      return new Response(JSON.stringify({ detail: 'not found' }), { status: 404 })
    })

    renderWithProvider(<App />)

    expect(await screen.findByText('Sign Out')).toBeInTheDocument()
  })
})
