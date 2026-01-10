import { describe, it, expect, beforeEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { AuthProvider, useAuth } from '../context/AuthContext'
import { ReactNode } from 'react'

describe('AuthContext', () => {
  const wrapper = ({ children }: { children: ReactNode }) => (
    <AuthProvider>{children}</AuthProvider>
  )

  beforeEach(() => {
    localStorage.clear()
  })

  it('initializes with no user', () => {
    const { result } = renderHook(() => useAuth(), { wrapper })
    
    expect(result.current.isAuthenticated).toBe(false)
    expect(result.current.user).toBeNull()
  })

  it('stores tokens on login', async () => {
    const { result } = renderHook(() => useAuth(), { wrapper })
    
    const mockToken = 'mock-jwt-token'
    
    await act(async () => {
      await result.current.login(mockToken)
    })

    // Check if tokens are stored
    expect(localStorage.getItem('access_token')).toBeTruthy()
  })

  it('clears tokens on logout', async () => {
    const { result } = renderHook(() => useAuth(), { wrapper })
    
    // Login first
    await act(async () => {
      await result.current.login('mock-token')
    })

    // Then logout
    act(() => {
      result.current.logout()
    })

    expect(localStorage.getItem('access_token')).toBeNull()
    expect(result.current.isAuthenticated).toBe(false)
  })
})
