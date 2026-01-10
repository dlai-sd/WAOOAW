import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { GoogleOAuthProvider } from '@react-oauth/google'
import GoogleLoginButton from '../components/auth/GoogleLoginButton'

// Mock Google OAuth
vi.mock('@react-oauth/google', async () => {
  const actual = await vi.importActual('@react-oauth/google')
  return {
    ...actual,
    GoogleLogin: ({ onSuccess }: { onSuccess: (credential: any) => void }) => (
      <button
        onClick={() => {
          const mockCredential = {
            credential: 'mock-jwt-token',
            clientId: 'mock-client-id'
          }
          onSuccess(mockCredential)
        }}
        data-testid="mock-google-login"
      >
        Sign in with Google
      </button>
    )
  }
})

// Mock useAuth hook
vi.mock('../hooks/useAuth', () => ({
  useAuth: () => ({
    login: vi.fn().mockResolvedValue(undefined),
    logout: vi.fn(),
    isAuthenticated: false,
    user: null
  })
}))

describe('GoogleLoginButton', () => {
  const mockOnSuccess = vi.fn()
  const mockOnError = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders Google login button', () => {
    render(
      <GoogleOAuthProvider clientId="test-client-id">
        <GoogleLoginButton onSuccess={mockOnSuccess} onError={mockOnError} />
      </GoogleOAuthProvider>
    )

    expect(screen.getByTestId('mock-google-login')).toBeInTheDocument()
  })
})
