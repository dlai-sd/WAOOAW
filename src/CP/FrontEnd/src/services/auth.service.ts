/**
 * Authentication API service
 * Handles all auth-related API calls
 */

import { API_ENDPOINTS } from '../config/oauth.config'
import { jwtDecode } from 'jwt-decode'

export interface User {
  id: string
  email: string
  name?: string
  picture?: string
  provider: string
  created_at: string
}

export interface TokenResponse {
  access_token: string
  refresh_token?: string
  token_type: string
  expires_in: number
}

export interface DecodedToken {
  user_id: string
  email: string
  token_type: string
  exp: number
  iat: number
}

const DEFAULT_EXP_SKEW_SECONDS = 30

class AuthService {
  private accessToken: string | null = null

  private static readonly ACCESS_TOKEN_KEY = 'cp_access_token'
  private static readonly LEGACY_ACCESS_TOKEN_KEY = 'access_token'
  private static readonly LEGACY_REFRESH_TOKEN_KEY = 'refresh_token'
  private static readonly TOKEN_EXPIRES_AT_KEY = 'token_expires_at'

  /**
   * Initialize from stored tokens
   */
  constructor() {
    this.loadTokens()
  }

  /**
   * Load tokens from localStorage
   */
  private loadTokens(): void {
    const current = localStorage.getItem(AuthService.ACCESS_TOKEN_KEY)

    if (!current) {
      const legacy = localStorage.getItem(AuthService.LEGACY_ACCESS_TOKEN_KEY)
      if (legacy) {
        localStorage.setItem(AuthService.ACCESS_TOKEN_KEY, legacy)
        localStorage.removeItem(AuthService.LEGACY_ACCESS_TOKEN_KEY)
        this.accessToken = legacy
      } else {
        this.accessToken = null
      }
    } else {
      this.accessToken = current
    }

    // PP parity: do not persist refresh tokens in the browser.
    localStorage.removeItem(AuthService.LEGACY_REFRESH_TOKEN_KEY)

    // Fail-closed on startup if token is already expired.
    if (this.accessToken && this.isTokenExpired()) {
      this.clearTokens()
    }
  }

  /**
   * Save tokens to localStorage
   */
  private saveTokens(tokens: TokenResponse): void {
    this.accessToken = tokens.access_token
    
    localStorage.setItem(AuthService.ACCESS_TOKEN_KEY, tokens.access_token)
    localStorage.removeItem(AuthService.LEGACY_ACCESS_TOKEN_KEY)
    localStorage.removeItem(AuthService.LEGACY_REFRESH_TOKEN_KEY)

    localStorage.setItem(AuthService.TOKEN_EXPIRES_AT_KEY, 
      String(Date.now() + tokens.expires_in * 1000)
    )
  }

  /**
   * Persist a token response from non-Google flows (e.g. OTP verify).
   */
  setTokens(tokens: TokenResponse): void {
    this.saveTokens(tokens)
  }

  /**
   * Clear tokens from storage
   */
  private clearTokens(): void {
    this.accessToken = null
    
    localStorage.removeItem(AuthService.ACCESS_TOKEN_KEY)
    localStorage.removeItem(AuthService.LEGACY_ACCESS_TOKEN_KEY)
    localStorage.removeItem(AuthService.LEGACY_REFRESH_TOKEN_KEY)
    localStorage.removeItem(AuthService.TOKEN_EXPIRES_AT_KEY)
  }

  /**
   * Check if user is authenticated
   */
  isAuthenticated(): boolean {
    return !!this.accessToken && !this.isTokenExpired()
  }

  /**
   * Check if access token is expired
   */
  private isTokenExpired(): boolean {
    if (!this.accessToken) return true

    // Prefer JWT exp claim (PP parity). Fall back to token_expires_at for legacy sessions.
    const decoded = this.decodeToken(this.accessToken)
    if (decoded?.exp) {
      const nowSeconds = Math.floor(Date.now() / 1000)
      return decoded.exp <= nowSeconds + DEFAULT_EXP_SKEW_SECONDS
    }

    const expiresAt = localStorage.getItem(AuthService.TOKEN_EXPIRES_AT_KEY)
    if (!expiresAt) return true

    return Date.now() >= parseInt(expiresAt)
  }

  /**
   * Get current access token
   */
  getAccessToken(): string | null {
    return this.accessToken
  }

  /**
   * Decode JWT token
   */
  decodeToken(token: string): DecodedToken | null {
    try {
      return jwtDecode<DecodedToken>(token)
    } catch {
      return null
    }
  }

  /**
   * Verify Google ID token and get JWT tokens
   */
  async verifyGoogleToken(idToken: string, source: string = 'cp'): Promise<TokenResponse> {
    const response = await fetch(API_ENDPOINTS.googleVerify, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        id_token: idToken,
        source
      })
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Failed to verify Google token')
    }

    const tokens: TokenResponse = await response.json()
    this.saveTokens(tokens)
    
    return tokens
  }

  /**
   * Get current user information
   */
  async getCurrentUser(): Promise<User> {
    if (!this.accessToken) {
      throw new Error('Not authenticated')
    }

    // Fail-closed on expiry (PP parity). Expiry semantics will be tightened to JWT exp.
    if (this.isTokenExpired()) {
      this.clearTokens()
      throw new Error('Session expired')
    }

    const response = await fetch(API_ENDPOINTS.me, {
      headers: {
        'Authorization': `Bearer ${this.accessToken}`
      }
    })

    if (!response.ok) {
      throw new Error('Failed to fetch user info')
    }

    return await response.json()
  }

  /**
   * Logout user
   */
  async logout(): Promise<void> {
    if (this.accessToken) {
      try {
        await fetch(API_ENDPOINTS.logout, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${this.accessToken}`
          }
        })
      } catch (error) {
        console.error('Logout API call failed:', error)
      }
    }

    this.clearTokens()
  }

  /**
   * Initiate OAuth flow (redirect to backend)
   */
  initiateOAuthFlow(source: string = 'cp'): void {
    window.location.href = `${API_ENDPOINTS.googleLogin}?source=${source}`
  }

  /**
   * Handle OAuth callback with tokens from URL
   */
  handleOAuthCallback(): TokenResponse | null {
    const params = new URLSearchParams(window.location.search)
    const accessToken = params.get('access_token')
    const expiresIn = params.get('expires_in')

    if (accessToken && expiresIn) {
      const tokens: TokenResponse = {
        access_token: accessToken,
        // Present for type compatibility with backend response, but not persisted/used in CP.
        refresh_token: params.get('refresh_token') || undefined,
        token_type: 'bearer',
        expires_in: parseInt(expiresIn)
      }

      this.saveTokens(tokens)

      // Clean URL
      window.history.replaceState({}, document.title, window.location.pathname)

      return tokens
    }

    return null
  }
}

// Export singleton instance
export const authService = new AuthService()
export default authService

// Export helper functions for testing
export const initiateGoogleLogin = () => authService.initiateOAuthFlow()
export const handleAuthCallback = async (_code: string, _state: string) => {
  return authService.handleOAuthCallback()
}
export const getUserProfile = async (_token: string) => authService.getCurrentUser()
export const logout = async (_token: string) => authService.logout()
