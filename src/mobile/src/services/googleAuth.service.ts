/**
 * Google Authentication Service
 *
 * Provides helpers used by useGoogleAuth and AuthService:
 *   - GoogleAuthError   typed error class
 *   - GoogleUserInfo    ID-token payload type
 *   - parseIdToken()    decode (not verify) the Google ID token on the client
 *   - isConfigured()    guard for GoogleSignin.configure() readiness
 *
 * Token *verification* (signature, aud, iss, exp) is performed server-side by
 * the CP backend using google-auth library — never trust client-side parsing.
 */

import { GOOGLE_OAUTH_CONFIG } from '../config/oauth.config';

/**
 * Google User Info (from ID token payload)
 * Subset of the OpenID Connect standard claims returned by Google.
 */
export interface GoogleUserInfo {
  sub: string;           // Stable Google user ID
  email: string;
  email_verified: boolean;
  name?: string;
  picture?: string;
  given_name?: string;
  family_name?: string;
  locale?: string;
}

/**
 * Typed error class for all Google auth failures.
 * code values: NOT_CONFIGURED | USER_CANCELLED | AUTH_LOCKED |
 *              PLAY_SERVICES_UNAVAILABLE | MISSING_ID_TOKEN | SIGN_IN_ERROR |
 *              ID_TOKEN_PARSE_ERROR | <statusCodes value>
 */
export class GoogleAuthError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly originalError?: Error
  ) {
    super(message);
    this.name = 'GoogleAuthError';
  }
}

/**
 * Google Authentication Service
 */
export class GoogleAuthService {
  /**
   * Decode (not verify) the Google ID token to extract user info.
   *
   * IMPORTANT: This is client-side base64 decoding only.  The backend MUST
   * verify the token signature and claims using the google-auth library before
   * trusting any value in the payload.
   *
   * @param idToken - Raw JWT string from GoogleSignin.signIn()
   * @returns Decoded payload
   * @throws GoogleAuthError on malformed token
   */
  static parseIdToken(idToken: string): GoogleUserInfo {
    try {
      const parts = idToken.split('.');
      if (parts.length !== 3) {
        throw new Error('Invalid ID token format');
      }

      const payload = parts[1];
      const base64 = payload.replace(/-/g, '+').replace(/_/g, '/');
      const padded = base64 + '='.repeat((4 - (base64.length % 4)) % 4);

      const jsonPayload = decodeURIComponent(
        atob(padded)
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
   * Returns true when EXPO_PUBLIC_GOOGLE_WEB_CLIENT_ID is set and looks like a
   * real client ID (not a placeholder or empty string).
   */
  static isConfigured(): boolean {
    const { webClientId } = GOOGLE_OAUTH_CONFIG;
    return webClientId.length > 0 && !webClientId.startsWith('YOUR_');
  }
}

export default GoogleAuthService;
