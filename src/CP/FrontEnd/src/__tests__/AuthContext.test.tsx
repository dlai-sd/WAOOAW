import { describe, it, expect, beforeEach, vi } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { AuthProvider, useAuth } from '../context/AuthContext'
import { ReactNode } from 'react'

// Mock auth service
vi.mock('../services/auth.service', () => ({
  default: {
    verifyGoogleToken: vi.fn().mockResolvedValue({
      access_token: 'mock-access-token',
      refresh_token: 'mock-refresh-token',
      user: { id: '1', email: 'test@example.com', name: 'Test User' }
    }),
    getCurrentUser: vi.fn().mockResolvedValue({
      id: '1',
      email: 'test@example.com',
      name: 'Test User'
    }),
    logout: vi.fn().mockResolvedValue(undefined),
    isAuthenticated: vi.fn().mockReturnValue(false),
    getAccessToken: vi.fn().mockReturnValue(null)
  }
}))

describe('AuthContext', () => {
  const wrapper = ({ children }: { children: ReactNode }) => (
    <AuthProvider>{children}</AuthProvider>
  )

  beforeEach(() => {
    localStorage.clear()
    vi.clearAllMocks()
  })

  it('initializes with no user', () => {
    const { result } = renderHook(() => useAuth(), { wrapper })
    
    expect(result.current.isAuthenticated).toBe(false)
    expect(result.current.user).toBeNull()
  })

  it('clears tokens on logout', async () => {
    const { result } = renderHook(() => useAuth(), { wrapper })

    await act(async () => {
      await result.current.logout()
    })

    expect(localStorage.getItem('cp_access_token')).toBeNull()
    expect(result.current.isAuthenticated).toBe(false)
  })

  it('reloads user on waooaw:auth-changed when authenticated', async () => {
    const authServiceModule = await import('../services/auth.service')
    const mockedAuth = (authServiceModule as any).default
    mockedAuth.isAuthenticated.mockReturnValue(true)

    renderHook(() => useAuth(), { wrapper })

    await act(async () => {
      window.dispatchEvent(new Event('waooaw:auth-changed'))
    })

    expect(mockedAuth.getCurrentUser).toHaveBeenCalled()
  })
})
