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
  refresh_token: string
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

class AuthService {
  private accessToken: string | null = null
  private refreshToken: string | null = null

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
    this.accessToken = localStorage.getItem('access_token')
    this.refreshToken = localStorage.getItem('refresh_token')
  }

  /**
   * Save tokens to localStorage
   */
  private saveTokens(tokens: TokenResponse): void {
    this.accessToken = tokens.access_token
    this.refreshToken = tokens.refresh_token
    
    localStorage.setItem('access_token', tokens.access_token)
    localStorage.setItem('refresh_token', tokens.refresh_token)
    localStorage.setItem('token_expires_at', 
      String(Date.now() + tokens.expires_in * 1000)
    )
  }

  /**
   * Clear tokens from storage
   */
  private clearTokens(): void {
    this.accessToken = null
    this.refreshToken = null
    
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('token_expires_at')
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
    const expiresAt = localStorage.getItem('token_expires_at')
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
   * Refresh access token using refresh token
   */
  async refreshAccessToken(): Promise<TokenResponse> {
    if (!this.refreshToken) {
      throw new Error('No refresh token available')
    }

    const response = await fetch(API_ENDPOINTS.refresh, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.refreshToken}`
      }
    })

    if (!response.ok) {
      this.clearTokens()
      throw new Error('Failed to refresh token')
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

    // Try to refresh if token is expired
    if (this.isTokenExpired()) {
      await this.refreshAccessToken()
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
    const refreshToken = params.get('refresh_token')
    const expiresIn = params.get('expires_in')

    if (accessToken && refreshToken && expiresIn) {
      const tokens: TokenResponse = {
        access_token: accessToken,
        refresh_token: refreshToken,
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
