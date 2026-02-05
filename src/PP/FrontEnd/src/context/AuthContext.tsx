import React, { createContext, useCallback, useEffect, useState, ReactNode } from 'react'

const AUTH_CHANGED_EVENT = 'waooaw:auth-changed'
const AUTH_EXPIRED_FLAG = 'waooaw:auth-expired'
const DB_UPDATES_TOKEN_STORAGE_KEY = 'pp_db_access_token'

function base64UrlDecodeToString(input: string): string {
  const normalized = input.replace(/-/g, '+').replace(/_/g, '/')
  const padded = normalized.padEnd(normalized.length + ((4 - (normalized.length % 4)) % 4), '=')
  // atob expects base64 (not base64url)
  return atob(padded)
}

function isJwtExpired(token: string, skewSeconds: number = 30): boolean {
  try {
    const parts = token.split('.')
    if (parts.length < 2) return false
    const payloadJson = base64UrlDecodeToString(parts[1])
    const payload = JSON.parse(payloadJson) as { exp?: number }
    if (!payload?.exp) return false
    const nowSeconds = Math.floor(Date.now() / 1000)
    return payload.exp <= nowSeconds + skewSeconds
  } catch {
    return false
  }
}

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

interface AuthContextType {
  isAuthenticated: boolean
  isLoading: boolean
  login: (token: string) => Promise<void>
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

interface AuthProviderProps {
  children: ReactNode
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [isLoading, setIsLoading] = useState(true)

  const syncFromStorage = useCallback(() => {
    const stored = localStorage.getItem('pp_access_token')
    if (stored && isJwtExpired(stored)) {
      localStorage.removeItem('pp_access_token')
      try {
        sessionStorage.removeItem(DB_UPDATES_TOKEN_STORAGE_KEY)
      } catch {
        // ignore
      }
      setAuthExpiredFlag()
      setIsAuthenticated(false)
      setIsLoading(false)
      return
    }
    setIsAuthenticated(!!stored)
    setIsLoading(false)
  }, [])

  useEffect(() => {
    syncFromStorage()

    const onAuthChanged = () => syncFromStorage()
    window.addEventListener(AUTH_CHANGED_EVENT, onAuthChanged)
    return () => window.removeEventListener(AUTH_CHANGED_EVENT, onAuthChanged)
  }, [])

  const login = useCallback(async (token: string) => {
    setIsLoading(true)
    localStorage.setItem('pp_access_token', token)
    try {
      sessionStorage.removeItem(DB_UPDATES_TOKEN_STORAGE_KEY)
    } catch {
      // ignore
    }
    setIsAuthenticated(true)
    setIsLoading(false)
  }, [])

  const logout = useCallback(async () => {
    localStorage.removeItem('pp_access_token')
    try {
      sessionStorage.removeItem(DB_UPDATES_TOKEN_STORAGE_KEY)
    } catch {
      // ignore
    }
    setIsAuthenticated(false)
  }, [])

  const value: AuthContextType = {
    isAuthenticated,
    isLoading,
    login,
    logout
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = React.useContext(AuthContext)
  if (!ctx) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return ctx
}

export default AuthContext
