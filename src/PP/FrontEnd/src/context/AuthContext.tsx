import React, { createContext, useCallback, useEffect, useState, ReactNode } from 'react'

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

  useEffect(() => {
    const stored = localStorage.getItem('pp_access_token')
    setIsAuthenticated(!!stored)
    setIsLoading(false)
  }, [])

  const login = useCallback(async (token: string) => {
    setIsLoading(true)
    localStorage.setItem('pp_access_token', token)
    setIsAuthenticated(true)
    setIsLoading(false)
  }, [])

  const logout = useCallback(async () => {
    localStorage.removeItem('pp_access_token')
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
