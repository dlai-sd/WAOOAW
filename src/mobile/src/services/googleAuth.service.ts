/**
 * Google Authentication Service
 * Handles Google OAuth2 flow and ID token exchange
 */

import * as WebBrowser from 'expo-web-browser';
import { GOOGLE_OAUTH_CONFIG, GOOGLE_OAUTH_SCOPES } from '../config/oauth.config';

// Complete the auth session properly
WebBrowser.maybeCompleteAuthSession();

/**
 * Google OAuth2 Response Types
 */
export interface GoogleAuthResponse {
  type: 'success' | 'error' | 'cancel' | 'dismiss' | 'locked';
  params?: {
    id_token?: string;
    access_token?: string;
    code?: string;
    error?: string;
    error_description?: string;
  };
  error?: Error;
}

/**
 * Google User Info (from ID token)
 */
export interface GoogleUserInfo {
  sub: string; // Google user ID
  email: string;
  email_verified: boolean;
  name?: string;
  picture?: string;
  given_name?: string;
  family_name?: string;
  locale?: string;
}

/**
 * Google Auth Service Error
 */
export class GoogleAuthError extends Error {
  constructor(
    message: string,
    public code: string,
    public originalError?: Error
  ) {
    super(message);
    this.name = 'GoogleAuthError';
  }
}

/**
 * Google Authentication Service
 * Provides methods for Google OAuth2 flow
 */
export class GoogleAuthService {
  /**
   * Parse ID token to extract user info
   * Note: This does NOT validate the token, just decodes it
   * Backend must validate the token signature
   */
  static parseIdToken(idToken: string): GoogleUserInfo {
    try {
      // ID token format: header.payload.signature
      const parts = idToken.split('.');
      if (parts.length !== 3) {
        throw new Error('Invalid ID token format');
      }

      // Decode payload (base64url)
      const payload = parts[1];
      const base64 = payload.replace(/-/g, '+').replace(/_/g, '/');
      const jsonPayload = decodeURIComponent(
        atob(base64)
          .split('')
          .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
          .join('')
      );

      return JSON.parse(jsonPayload) as GoogleUserInfo;
    } catch (error) {
      throw new GoogleAuthError(
        'Failed to parse ID token',
        'ID_TOKEN_PARSE_ERROR',
        error as Error
      );
    }
  }

  /**
   * Validate OAuth response
   * Returns ID token if successful, throws error otherwise
   */
  static validateOAuthResponse(response: GoogleAuthResponse): string {
    if (response.type === 'cancel') {
      throw new GoogleAuthError(
        'User cancelled the sign-in flow',
        'USER_CANCELLED'
      );
    }

    if (response.type === 'dismiss') {
      throw new GoogleAuthError(
        'User dismissed the sign-in flow',
        'USER_DISMISSED'
      );
    }

    if (response.type === 'locked') {
      throw new GoogleAuthError(
        'Authentication is locked',
        'AUTH_LOCKED'
      );
    }

    if (response.type === 'error') {
      const errorMsg = response.params?.error_description || response.error?.message || 'Unknown error';
      throw new GoogleAuthError(
        `OAuth error: ${errorMsg}`,
        response.params?.error || 'OAUTH_ERROR',
        response.error
      );
    }

    if (response.type !== 'success') {
      throw new GoogleAuthError(
        `Unexpected response type: ${response.type}`,
        'UNEXPECTED_RESPONSE'
      );
    }

    // expo-auth-session v7 Google provider forces ResponseType.Code on Android native.
    // After auto code-exchange, id_token is in response.authentication.idToken.
    // For web / IdToken flow it is in response.params.id_token.
    // Check both so the same handler works regardless of which flow ran.
    const idToken =
      response.params?.id_token ||
      (response as any).authentication?.idToken ||
      null;

    if (!idToken) {
      throw new GoogleAuthError(
        'No ID token in response — ensure EXPO_PUBLIC_GOOGLE_ANDROID_CLIENT_ID is set in eas.json ' +
        'and the reverse-scheme intent filter is registered in app.json',
        'MISSING_ID_TOKEN'
      );
    }

    return idToken;
  }

  /**
   * Get user info from OAuth response
   * Validates response and parses ID token
   */
  static getUserInfoFromResponse(response: GoogleAuthResponse): GoogleUserInfo {
    const idToken = this.validateOAuthResponse(response);
    return this.parseIdToken(idToken);
  }

  /**
   * Get OAuth configuration for current platform
   */
  static getOAuthConfig() {
    return {
      expoClientId: GOOGLE_OAUTH_CONFIG.expoClientId,
      iosClientId: GOOGLE_OAUTH_CONFIG.iosClientId,
      androidClientId: GOOGLE_OAUTH_CONFIG.androidClientId,
      webClientId: GOOGLE_OAUTH_CONFIG.webClientId,
      scopes: GOOGLE_OAUTH_SCOPES,
    };
  }

  /**
   * Check if OAuth configuration is valid
   */
  static isConfigured(): boolean {
    const { webClientId } = GOOGLE_OAUTH_CONFIG;

    // Only webClientId is required for expo-auth-session browser-based flow.
    // androidClientId falls back to webClientId; iosClientId and expoClientId
    // are only needed for native / Expo Go flows respectively.
    return (
      webClientId.length > 0 &&
      !webClientId.startsWith('YOUR_')
    );
  }

  /**
   * Open Google's consent screen in system browser
   * Used as fallback if in-app browser fails
   */
  static async openConsentScreenInBrowser(authUrl: string): Promise<void> {
    try {
      await WebBrowser.openBrowserAsync(authUrl);
    } catch (error) {
      throw new GoogleAuthError(
        'Failed to open consent screen',
        'BROWSER_OPEN_ERROR',
        error as Error
      );
    }
  }

  /**
   * Dismiss web browser if still open
   */
  static async dismissBrowser(): Promise<void> {
    try {
      await WebBrowser.dismissBrowser();
    } catch (error) {
      // Ignore errors when dismissing browser
      console.warn('Failed to dismiss browser:', error);
    }
  }
}

export default GoogleAuthService;
