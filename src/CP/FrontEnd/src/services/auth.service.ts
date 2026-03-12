/**
 * Authentication API service
 * Handles all auth-related API calls
 *
 * E1-S4 Auth Strategy:
 * - Access token stored in memory ONLY (this.accessToken) — never in localStorage
 * - Refresh token stored exclusively in httpOnly cookie (set by backend)
 * - On app load: silently call POST /auth/refresh to restore session
 * - On 401: transparently call POST /auth/refresh and retry once
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
const SESSION_HINT_STORAGE_KEY = 'waooaw:session-restorable'

class AuthService {
  /** E1-S4: Access token held in memory only — never persisted to localStorage/sessionStorage */
  private accessToken: string | null = null

  /** E1-S4: Prevent infinite refresh loops */
  private _isRefreshing = false
  private _refreshPromise: Promise<string | null> | null = null

  constructor() {
    // E1-S4: On construction, clear any legacy stored tokens.
    // The access token will be restored by a silent refresh call on app mount.
    this._clearLegacyStorage()
  }

  private hasSessionRecoveryHint(): boolean {
    try {
      return localStorage.getItem(SESSION_HINT_STORAGE_KEY) === '1'
    } catch {
      return false
    }
  }

  private markSessionRecoveryHint(): void {
    try {
      localStorage.setItem(SESSION_HINT_STORAGE_KEY, '1')
    } catch {
      // ignore
    }
  }

  private clearSessionRecoveryHint(): void {
    try {
      localStorage.removeItem(SESSION_HINT_STORAGE_KEY)
    } catch {
      // ignore
    }
  }

  private _clearLegacyStorage(): void {
    try {
      localStorage.removeItem('cp_access_token')
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      localStorage.removeItem('token_expires_at')
    } catch {
      // Ignore — some environments (e.g. tests) may not have localStorage
    }
  }

  /**
   * E1-S4: Call POST /auth/refresh to restore session from httpOnly cookie.
   * Should be called on app mount and on any 401 response.
   * Returns the new access_token or null if refresh fails.
   */
  async silentRefresh(force: boolean = false): Promise<string | null> {
    if (!force && !this.accessToken && !this.hasSessionRecoveryHint()) {
      return null
    }

    // Prevent concurrent refresh calls (queue them behind the same promise)
    if (this._isRefreshing && this._refreshPromise) {
      return this._refreshPromise
    }

    this._isRefreshing = true
    this._refreshPromise = (async (): Promise<string | null> => {
      try {
        const response = await fetch(API_ENDPOINTS.refresh, {
          method: 'POST',
          credentials: 'include', // required to send the httpOnly cookie
          headers: { 'Content-Type': 'application/json' },
        })

        if (!response.ok) {
          this.clearTokens()
          return null
        }

        const data: TokenResponse = await response.json()
        this.accessToken = data.access_token
        this.markSessionRecoveryHint()
        return data.access_token
      } catch {
        this.clearTokens()
        return null
      } finally {
        this._isRefreshing = false
        this._refreshPromise = null
      }
    })()

    return this._refreshPromise
  }

  /**
   * Check if user is authenticated (access token in memory and not expired)
   */
  isAuthenticated(): boolean {
    return !!this.accessToken && !this.isTokenExpired()
  }

  /**
   * Check if access token is expired
   */
  private isTokenExpired(): boolean {
    if (!this.accessToken) return true

    const decoded = this.decodeToken(this.accessToken)
    if (decoded?.exp) {
      const nowSeconds = Math.floor(Date.now() / 1000)
      return decoded.exp <= nowSeconds + DEFAULT_EXP_SKEW_SECONDS
    }

    return true
  }

  /**
   * Get current access token from memory
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
   * Store a new token response (sets in memory, not localStorage)
   */
  setTokens(tokens: TokenResponse): void {
    this.accessToken = tokens.access_token
    this.markSessionRecoveryHint()
  }

  /**
   * Clear in-memory access token (cookie cleared by backend /auth/logout)
   */
  private clearTokens(): void {
    this.accessToken = null
    this.clearSessionRecoveryHint()
  }

  /**
   * Verify Google ID token and get JWT tokens
   */
  async verifyGoogleToken(idToken: string, source: string = 'cp'): Promise<TokenResponse> {
    const response = await fetch(API_ENDPOINTS.googleVerify, {
      method: 'POST',
      credentials: 'include', // allow the Set-Cookie response to be stored
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
    this.accessToken = tokens.access_token  // E1-S4: memory only
    this.markSessionRecoveryHint()
    
    return tokens
  }

  /**
   * Get current user information
   */
  async getCurrentUser(): Promise<User> {
    if (!this.accessToken) {
      throw new Error('Not authenticated')
    }

    if (this.isTokenExpired()) {
      // Try silent refresh before giving up
      const newToken = await this.silentRefresh(true)
      if (!newToken) {
        this.clearTokens()
        throw new Error('Session expired')
      }
    }

    const response = await fetch(API_ENDPOINTS.me, {
      headers: {
        'Authorization': `Bearer ${this.accessToken}`
      }
    })

    if (!response.ok) {
      if (response.status === 401) {
        // Try silent refresh once
        const newToken = await this.silentRefresh(true)
        if (!newToken) {
          this.clearTokens()
          throw new Error('Session expired')
        }
        // Retry with new token
        const retryResponse = await fetch(API_ENDPOINTS.me, {
          headers: { 'Authorization': `Bearer ${this.accessToken}` }
        })
        if (!retryResponse.ok) throw new Error('Failed to fetch user info')
        return retryResponse.json()
      }
      throw new Error('Failed to fetch user info')
    }

    return await response.json()
  }

  /**
   * Logout user — calls backend to revoke refresh token cookie
   */
  async logout(): Promise<void> {
    try {
      await fetch(API_ENDPOINTS.logout, {
        method: 'POST',
        credentials: 'include', // sends the httpOnly cookie for revocation
        headers: this.accessToken
          ? { 'Authorization': `Bearer ${this.accessToken}` }
          : {}
      })
    } catch (error) {
      console.error('Logout API call failed:', error)
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
        token_type: 'bearer',
        expires_in: parseInt(expiresIn)
      }

      // E1-S4: memory only
      this.accessToken = tokens.access_token
      this.markSessionRecoveryHint()

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