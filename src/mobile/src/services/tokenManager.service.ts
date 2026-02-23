/**
 * JWT Token Manager Service
 * Handles JWT token lifecycle: decode, validation, refresh
 * 
 * Compliant with WAOOAW CP/PP Backend JWT implementation:
 * - Algorithm: HS256 (backend verifies)
 * - Issuer: "waooaw.com"
 * - Access Token Expiry: 15 minutes (900 seconds)
 * - Refresh Token Expiry: 7 days
 * - Token Type: "bearer"
 */

import secureStorage from '../lib/secureStorage';
import apiClient from '../lib/apiClient';

/**
 * Decoded JWT Token Payload
 * Matches backend TokenData model + JWT standard claims
 */
export interface DecodedToken {
  user_id: string;
  email: string;
  token_type: 'access' | 'refresh';
  exp: number; // Expiration timestamp (seconds since epoch)
  iat: number; // Issued at timestamp (seconds since epoch)
  roles?: string[]; // User roles (backend includes ["user"])
  iss?: string; // Issuer ("waooaw.com")
  sub?: string; // Subject (same as user_id)
}

/**
 * Token Response from Backend
 * Matches backend Token model (CP/PP /auth/google/verify response)
 */
export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: 'bearer';
  expires_in: number; // Seconds until access token expires (typically 900)
}

/**
 * JWT Token Manager Error
 */
export class TokenManagerError extends Error {
  constructor(
    message: string,
    public code: string,
    public originalError?: Error
  ) {
    super(message);
    this.name = 'TokenManagerError';
  }
}

/**
 * JWT Token Manager Service
 * Manages JWT token lifecycle for mobile authentication
 */
export class TokenManagerService {
  /**
   * Decode JWT token to extract payload
   * Note: This does NOT verify the signature (backend already validated)
   * 
   * @param token - JWT token string
   * @returns Decoded token payload
   * @throws TokenManagerError if token format is invalid
   */
  static decodeToken(token: string): DecodedToken {
    try {
      // JWT format: header.payload.signature
      const parts = token.split('.');
      if (parts.length !== 3) {
        throw new Error('Invalid JWT format');
      }

      // Decode payload (base64url)
      const payload = parts[1];
      const base64 = payload.replace(/-/g, '+').replace(/_/g, '/');
      
      // Add padding if needed
      const paddedBase64 = base64 + '='.repeat((4 - (base64.length % 4)) % 4);
      
      const jsonPayload = decodeURIComponent(
        atob(paddedBase64)
          .split('')
          .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
          .join('')
      );

      return JSON.parse(jsonPayload) as DecodedToken;
    } catch (error) {
      throw new TokenManagerError(
        'Failed to decode JWT token',
        'DECODE_ERROR',
        error as Error
      );
    }
  }

  /**
   * Validate token expiry
   * Checks if token is expired with buffer time
   * 
   * @param token - Decoded token payload
   * @param bufferSeconds - Buffer time before expiry (default: 30s, matching CP FrontEnd)
   * @returns true if token is expired or about to expire
   */
  static isTokenExpired(token: DecodedToken, bufferSeconds: number = 30): boolean {
    const now = Math.floor(Date.now() / 1000);
    return now >= (token.exp - bufferSeconds);
  }

  /**
   * Get token expiry as Date object
   * 
   * @param token - Decoded token payload
   * @returns Expiry date
   */
  static getTokenExpiry(token: DecodedToken): Date {
    return new Date(token.exp * 1000);
  }

  /**
   * Get token issued at as Date object
   * 
   * @param token - Decoded token payload
   * @returns Issued at date
   */
  static getTokenIssuedAt(token: DecodedToken): Date {
    return new Date(token.iat * 1000);
  }

  /**
   * Save tokens from authentication response
   * Stores access token, refresh token, and expiry time
   * 
   * @param response - Token response from backend
   */
  static async saveTokens(response: TokenResponse): Promise<void> {
    try {
      await secureStorage.setTokens({
        accessToken: response.access_token,
        refreshToken: response.refresh_token,
        expiresAt: Math.floor(Date.now() / 1000) + response.expires_in,
      });
    } catch (error) {
      throw new TokenManagerError(
        'Failed to save tokens',
        'SAVE_ERROR',
        error as Error
      );
    }
  }

  /**
   * Get valid access token
   * Returns token if valid, null if expired or not found
   * Automatically clears expired tokens
   * 
   * @returns Access token or null
   */
  static async getAccessToken(): Promise<string | null> {
    try {
      const token = await secureStorage.getAccessToken();
      if (!token) return null;

      // Check expiry using SecureStorage (30s buffer)
      const isExpired = await secureStorage.isTokenExpired();
      if (isExpired) {
        await this.clearTokens();
        return null;
      }

      return token;
    } catch (error) {
      throw new TokenManagerError(
        'Failed to retrieve access token',
        'GET_TOKEN_ERROR',
        error as Error
      );
    }
  }

  /**
   * Get refresh token
   * 
   * @returns Refresh token or null
   */
  static async getRefreshToken(): Promise<string | null> {
    try {
      return await secureStorage.getRefreshToken();
    } catch (error) {
      throw new TokenManagerError(
        'Failed to retrieve refresh token',
        'GET_REFRESH_TOKEN_ERROR',
        error as Error
      );
    }
  }

  /**
   * Refresh access token using refresh token
   * Exchanges refresh token for new access token
   * 
   * @returns New access token or null if refresh failed
   */
  static async refreshAccessToken(): Promise<string | null> {
    try {
      const refreshToken = await secureStorage.getRefreshToken();
      if (!refreshToken) {
        return null;
      }

      // Call backend refresh endpoint
      const { data } = await apiClient.post<TokenResponse>('/auth/refresh', {
        refresh_token: refreshToken,
      });

      // Save new tokens
      await this.saveTokens(data);

      return data.access_token;
    } catch (error) {
      // If refresh fails, clear all tokens
      await this.clearTokens();
      
      throw new TokenManagerError(
        'Failed to refresh access token',
        'REFRESH_ERROR',
        error as Error
      );
    }
  }

  /**
   * Clear all tokens from storage
   * Called on logout or token invalidation
   */
  static async clearTokens(): Promise<void> {
    try {
      await secureStorage.clearTokens();
    } catch (error) {
      throw new TokenManagerError(
        'Failed to clear tokens',
        'CLEAR_ERROR',
        error as Error
      );
    }
  }

  /**
   * Check if user is authenticated
   * Validates that access token exists and is not expired
   * 
   * @returns true if user has valid access token
   */
  static async isAuthenticated(): Promise<boolean> {
    try {
      return await secureStorage.isAuthenticated();
    } catch (error) {
      return false;
    }
  }

  /**
   * Get user info from current token
   * Decodes access token and extracts user information
   * 
   * @returns User info or null if no token
   */
  static async getUserInfo(): Promise<{
    userId: string;
    email: string;
    roles: string[];
  } | null> {
    try {
      const token = await this.getAccessToken();
      if (!token) return null;

      const decoded = this.decodeToken(token);
      
      return {
        userId: decoded.user_id,
        email: decoded.email,
        roles: decoded.roles || ['user'],
      };
    } catch (error) {
      throw new TokenManagerError(
        'Failed to get user info from token',
        'GET_USER_INFO_ERROR',
        error as Error
      );
    }
  }

  /**
   * Validate token format and claims
   * Checks issuer, token type, and required claims
   * 
   * @param token - Decoded token payload
   * @returns true if token is valid
   */
  static validateTokenClaims(token: DecodedToken): boolean {
    // Check required claims
    if (!token.user_id || !token.email || !token.exp || !token.iat) {
      return false;
    }

    // Check issuer (if present)
    if (token.iss && token.iss !== 'waooaw.com') {
      return false;
    }

    // Check issued at is not in the future
    const now = Math.floor(Date.now() / 1000);
    if (token.iat > now + 60) { // Allow 60s clock skew
      return false;
    }

    return true;
  }

  /**
   * Get time until token expires
   * 
   * @param token - Decoded token payload
   * @returns Seconds until expiry (negative if expired)
   */
  static getTimeUntilExpiry(token: DecodedToken): number {
    const now = Math.floor(Date.now() / 1000);
    return token.exp - now;
  }

  /**
   * Check if token needs refresh
   * Returns true if token expires within threshold
   * 
   * @param token - Decoded token payload
   * @param thresholdSeconds - Refresh threshold (default: 60s)
   * @returns true if token should be refreshed
   */
  static shouldRefreshToken(token: DecodedToken, thresholdSeconds: number = 60): boolean {
    const timeUntilExpiry = this.getTimeUntilExpiry(token);
    return timeUntilExpiry > 0 && timeUntilExpiry < thresholdSeconds;
  }
}

export default TokenManagerService;
