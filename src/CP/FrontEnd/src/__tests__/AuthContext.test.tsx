import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import type { ReactNode } from 'react'

describe('AuthContext', () => {
  beforeEach(() => {
    vi.resetModules()
    localStorage.clear()
    vi.clearAllMocks()

    // Use a dynamic mock to avoid leaking this mock into other test files.
    vi.doMock('../services/auth.service', () => ({
      default: {
        verifyGoogleToken: vi.fn().mockResolvedValue({
          access_token: 'mock-access-token',
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
  })

  afterEach(() => {
    vi.unmock('../services/auth.service')
    vi.resetModules()
    localStorage.clear()
  })

  it('initializes with no user', async () => {
    const { AuthProvider, useAuth } = await import('../context/AuthContext')
    const wrapper = ({ children }: { children: ReactNode }) => <AuthProvider>{children}</AuthProvider>

    const { result } = renderHook(() => useAuth(), { wrapper })
    
    expect(result.current.isAuthenticated).toBe(false)
    expect(result.current.user).toBeNull()
  })

  it('clears tokens on logout', async () => {
    const { AuthProvider, useAuth } = await import('../context/AuthContext')
    const wrapper = ({ children }: { children: ReactNode }) => <AuthProvider>{children}</AuthProvider>

    const { result } = renderHook(() => useAuth(), { wrapper })

    await act(async () => {
      await result.current.logout()
    })

    expect(localStorage.getItem('cp_access_token')).toBeNull()
    expect(result.current.isAuthenticated).toBe(false)
  })

  it('reloads user on waooaw:auth-changed when authenticated', async () => {
    const { AuthProvider, useAuth } = await import('../context/AuthContext')
    const wrapper = ({ children }: { children: ReactNode }) => <AuthProvider>{children}</AuthProvider>

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
