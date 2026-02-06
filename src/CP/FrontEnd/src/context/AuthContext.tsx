/**
 * Authentication Context
 * Provides authentication state and methods throughout the app
 */

import React, { createContext, useState, useEffect, useCallback, ReactNode } from 'react'
import authService, { User } from '../services/auth.service'

const AUTH_CHANGED_EVENT = 'waooaw:auth-changed'
const AUTH_EXPIRED_FLAG = 'waooaw:auth-expired'

function setAuthExpiredFlag(): void {
  try {
    sessionStorage.setItem(AUTH_EXPIRED_FLAG, '1')
  } catch {
    // ignore
  }
}

export function consumeAuthExpiredFlag(): boolean {
  try {
    const raw = sessionStorage.getItem(AUTH_EXPIRED_FLAG)
    if (!raw) return false
    sessionStorage.removeItem(AUTH_EXPIRED_FLAG)
    return true
  } catch {
    return false
  }
}

function broadcastAuthChanged(): void {
  try {
    window.dispatchEvent(new Event(AUTH_CHANGED_EVENT))
  } catch {
    // ignore
  }
}

interface AuthContextType {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (idToken: string) => Promise<void>
  logout: () => Promise<void>
  refreshUser: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

interface AuthProviderProps {
  children: ReactNode
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  /**
   * Load user from stored tokens on mount
   */
  const loadUser = useCallback(async () => {
    if (authService.isAuthenticated()) {
      try {
        const userData = await authService.getCurrentUser()
        setUser(userData)
      } catch (error) {
        console.error('Failed to load user:', error)
        // Clear invalid tokens
        await authService.logout()
        setAuthExpiredFlag()
        broadcastAuthChanged()
        setUser(null)
      }
    } else {
      setUser(null)
    }
    setIsLoading(false)
  }, [])

  useEffect(() => {
    loadUser()
  }, [loadUser])

  useEffect(() => {
    const onAuthChanged = () => {
      setIsLoading(true)
      loadUser()
    }
    window.addEventListener(AUTH_CHANGED_EVENT, onAuthChanged)
    return () => window.removeEventListener(AUTH_CHANGED_EVENT, onAuthChanged)
  }, [loadUser])

  /**
   * Handle login with Google ID token
   */
  const login = useCallback(async (idToken: string) => {
    try {
      setIsLoading(true)
      await authService.verifyGoogleToken(idToken)
      broadcastAuthChanged()
      const userData = await authService.getCurrentUser()
      setUser(userData)
    } catch (error) {
      console.error('Login failed:', error)
      throw error
    } finally {
      setIsLoading(false)
    }
  }, [])

  /**
   * Handle logout
   */
  const logout = useCallback(async () => {
    try {
      await authService.logout()
      setUser(null)
      broadcastAuthChanged()
    } catch (error) {
      console.error('Logout failed:', error)
    }
  }, [])

  /**
   * Refresh user data
   */
  const refreshUser = useCallback(async () => {
    if (authService.isAuthenticated()) {
      try {
        const userData = await authService.getCurrentUser()
        setUser(userData)
      } catch (error) {
        console.error('Failed to refresh user:', error)
      }
    }
  }, [])

  const value: AuthContextType = {
    user,
    isAuthenticated: !!user,
    isLoading,
    login,
    logout,
    refreshUser
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = React.useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

export default AuthContext
