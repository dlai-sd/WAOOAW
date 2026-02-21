/**
 * Authentication Service
 * Orchestrates the complete authentication flow:
 * 1. Google OAuth2 (via GoogleAuthService)
 * 2. Backend JWT exchange (CP/PP /auth/google/verify)
 * 3. Token storage (via TokenManagerService)
 * 4. User data storage (via SecureStorageService)
 * 
 * Compliant with CP/PP Backend authentication:
 * - Endpoint: POST /auth/google/verify
 * - Request: { id_token: string, source: "mobile" }
 * - Response: { access_token, refresh_token, token_type, expires_in }
 */

import apiClient from '../lib/apiClient';
import secureStorage from '../lib/secureStorage';
import { TokenManagerService, TokenResponse } from './tokenManager.service';
import { GoogleAuthService, GoogleUserInfo } from './googleAuth.service';

/**
 * User Profile (stored locally)
 */
export interface UserProfile {
  id: string; // user_id from JWT
  email: string;
  name?: string;
  picture?: string;
  provider: 'google';
  authenticated_at: string; // ISO timestamp
}

/**
 * Login Request (sent to backend)
 */
interface GoogleVerifyRequest {
  id_token: string;
  source: 'mobile';
  totp_code?: string; // Optional 2FA code
}

/**
 * Auth Service Error
 */
export class AuthServiceError extends Error {
  constructor(
    message: string,
    public code: string,
    public originalError?: Error
  ) {
    super(message);
    this.name = 'AuthServiceError';
  }
}

/**
 * Auth Service Error Codes
 */
export const AuthErrorCode = {
  INVALID_ID_TOKEN: 'INVALID_ID_TOKEN',
  BACKEND_VERIFICATION_FAILED: 'BACKEND_VERIFICATION_FAILED',
  TOKEN_STORAGE_FAILED: 'TOKEN_STORAGE_FAILED',
  USER_DATA_STORAGE_FAILED: 'USER_DATA_STORAGE_FAILED',
  NOT_AUTHENTICATED: 'NOT_AUTHENTICATED',
  REFRESH_FAILED: 'REFRESH_FAILED',
  TWO_FA_REQUIRED: '2FA_REQUIRED',
  INVALID_TWO_FA_CODE: 'INVALID_2FA_CODE',
} as const;

/**
 * Authentication Service
 * Static methods for stateless operation
 */
export class AuthService {
  /**
   * Login with Google ID Token
   * 
   * Flow:
   * 1. Validate ID token format
   * 2. Extract user info from ID token
   * 3. Send ID token to backend for verification
   * 4. Receive JWT tokens from backend
   * 5. Save JWT tokens to SecureStorage
   * 6. Save user profile to SecureStorage
   * 
   * @param idToken - Google ID token from OAuth flow
   * @param totpCode - Optional 2FA TOTP code
   * @returns User profile
   * @throws AuthServiceError
   */
  static async loginWithGoogle(
    idToken: string,
    totpCode?: string
  ): Promise<UserProfile> {
    try {
      // Step 1: Validate ID token format
      if (!idToken || typeof idToken !== 'string') {
        throw new AuthServiceError(
          'Invalid ID token format',
          AuthErrorCode.INVALID_ID_TOKEN
        );
      }

      // Step 2: Extract user info from ID token (local parsing)
      const googleUserInfo = GoogleAuthService.parseIdToken(idToken);

      // Step 3: Send ID token to backend for verification
      const request: GoogleVerifyRequest = {
        id_token: idToken,
        source: 'mobile',
      };

      if (totpCode) {
        request.totp_code = totpCode;
      }

      let tokenResponse: TokenResponse;
      try {
        const response = await apiClient.post<TokenResponse>(
          '/api/v1/auth/google/verify',
          request
        );
        tokenResponse = response.data;
      } catch (error: any) {
        // Handle 2FA required error
        if (error.response?.status === 401) {
          const detail = error.response?.data?.detail;
          if (detail === '2FA required') {
            throw new AuthServiceError(
              '2FA authentication required',
              AuthErrorCode.TWO_FA_REQUIRED,
              error
            );
          }
          if (detail === 'Invalid 2FA code') {
            throw new AuthServiceError(
              'Invalid 2FA code provided',
              AuthErrorCode.INVALID_TWO_FA_CODE,
              error
            );
          }
        }

        throw new AuthServiceError(
          'Backend verification failed',
          AuthErrorCode.BACKEND_VERIFICATION_FAILED,
          error
        );
      }

      // Step 4: Save JWT tokens to SecureStorage (via TokenManagerService)
      try {
        await TokenManagerService.saveTokens(tokenResponse);
      } catch (error: any) {
        throw new AuthServiceError(
          'Failed to save authentication tokens',
          AuthErrorCode.TOKEN_STORAGE_FAILED,
          error
        );
      }

      // Step 5: Decode access token to get user_id
      const decodedToken = TokenManagerService.decodeToken(
        tokenResponse.access_token
      );

      // Step 6: Create and save user profile
      const userProfile: UserProfile = {
        id: decodedToken.user_id,
        email: googleUserInfo.email,
        name: googleUserInfo.name,
        picture: googleUserInfo.picture,
        provider: 'google',
        authenticated_at: new Date().toISOString(),
      };

      try {
        await secureStorage.setUserData(userProfile);
      } catch (error: any) {
        throw new AuthServiceError(
          'Failed to save user profile',
          AuthErrorCode.USER_DATA_STORAGE_FAILED,
          error
        );
      }

      return userProfile;
    } catch (error) {
      if (error instanceof AuthServiceError) {
        throw error;
      }
      throw new AuthServiceError(
        'Login failed',
        AuthErrorCode.BACKEND_VERIFICATION_FAILED,
        error as Error
      );
    }
  }

  /**
   * Logout
   * 
   * Clears all authentication data:
   * - JWT tokens (access + refresh)
   * - Token expiry timestamp
   * - User profile data
   * 
   * Note: Does not call backend logout endpoint (tokens are stateless JWT)
   */
  static async logout(): Promise<void> {
    try {
      await secureStorage.clearAll();
    } catch (error) {
      // Log but don't throw - best effort cleanup
      console.error('Logout cleanup error:', error);
    }
  }

  /**
   * Check Authentication Status
   * 
   * Verifies user is authenticated by checking:
   * 1. Access token exists
   * 2. Access token is not expired (with 30s buffer)
   * 3. User profile exists
   * 
   * @returns True if authenticated, false otherwise
   */
  static async isAuthenticated(): Promise<boolean> {
    try {
      return await secureStorage.isAuthenticated();
    } catch {
      return false;
    }
  }

  /**
   * Get Current User Profile
   * 
   * Retrieves user profile from SecureStorage
   * 
   * @returns User profile or null if not authenticated
   */
  static async getCurrentUser(): Promise<UserProfile | null> {
    try {
      const isAuth = await this.isAuthenticated();
      if (!isAuth) {
        return null;
      }

      const userData = await secureStorage.getUserData();
      if (!userData) {
        return null;
      }

      return userData as UserProfile;
    } catch {
      return null;
    }
  }

  /**
   * Refresh Access Token
   * 
   * Attempts to refresh the access token using the refresh token.
   * If refresh fails, user must re-authenticate.
   * 
   * @returns True if refresh succeeded, false if re-authentication needed
   */
  static async refreshToken(): Promise<boolean> {
    try {
      const newTokens = await TokenManagerService.refreshAccessToken();
      return newTokens !== null;
    } catch (error) {
      console.error('Token refresh failed:', error);
      return false;
    }
  }

  /**
   * Get Access Token
   * 
   * Retrieves valid access token, automatically refreshing if expired.
   * 
   * @returns Access token or null if authentication required
   */
  static async getAccessToken(): Promise<string | null> {
    try {
      return await TokenManagerService.getAccessToken();
    } catch {
      return null;
    }
  }

  /**
   * Get User Info from Token
   * 
   * Extracts user information from the current access token
   * without making a network request.
   * 
   * @returns User info or null if not authenticated
   */
  static async getUserInfo(): Promise<{
    userId: string;
    email: string;
    roles: string[];
  } | null> {
    try {
      return await TokenManagerService.getUserInfo();
    } catch {
      return null;
    }
  }

  /**
   * Validate Authentication State
   * 
   * Comprehensive validation of authentication state:
   * - Tokens exist and are valid
   * - User profile exists
   * - Token issuer matches expected value
   * 
   * @returns Validation result with details
   */
  static async validateAuthState(): Promise<{
    valid: boolean;
    hasTokens: boolean;
    hasUserProfile: boolean;
    tokenExpired: boolean;
    issuerValid: boolean;
  }> {
    try {
      const accessToken = await secureStorage.getAccessToken();
      const userProfile = await secureStorage.getUserData();
      const hasTokens = !!accessToken;
      const hasUserProfile = !!userProfile;

      let tokenExpired = true;
      let issuerValid = false;

      if (accessToken) {
        try {
          const decoded = TokenManagerService.decodeToken(accessToken);
          tokenExpired = TokenManagerService.isTokenExpired(decoded);
          issuerValid = TokenManagerService.validateTokenClaims(decoded);
        } catch {
          // Token decoding failed
        }
      }

      const valid =
        hasTokens &&
        hasUserProfile &&
        !tokenExpired &&
        issuerValid;

      return {
        valid,
        hasTokens,
        hasUserProfile,
        tokenExpired,
        issuerValid,
      };
    } catch {
      return {
        valid: false,
        hasTokens: false,
        hasUserProfile: false,
        tokenExpired: true,
        issuerValid: false,
      };
    }
  }
}

// Export singleton-style default instance
export default AuthService;
