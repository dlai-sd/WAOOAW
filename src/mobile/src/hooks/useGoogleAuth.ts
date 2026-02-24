/**
 * Google Auth Hook
 * React hook for Google Sign-In using the native @react-native-google-signin/google-signin SDK.
 *
 * Why native SDK instead of expo-auth-session (browser-based):
 *   - Android OAuth clients (type=1) block browser-based flows:
 *     "Custom URI scheme is not enabled for your Android client"
 *   - Web OAuth clients (type=3) reject custom URI schemes in GCP Console
 *     "Invalid Redirect: must use either http or https as the scheme"
 *   - The native SDK talks directly to Google Play Services — no browser,
 *     no redirect URI, no GCP Console change required.
 *
 * idToken audience: webClientId in configure() makes Google issue the idToken
 * with aud = webClientId, matching what the backend verifies.
 */

import { useCallback, useState } from 'react';
import {
  GoogleSignin,
  statusCodes,
  isSuccessResponse,
  isCancelledResponse,
  isErrorWithCode,
} from '@react-native-google-signin/google-signin';
import GoogleAuthService, {
  GoogleAuthError,
  type GoogleUserInfo,
} from '../services/googleAuth.service';
import { GOOGLE_OAUTH_CONFIG, GOOGLE_OAUTH_SCOPES } from '../config/oauth.config';

// Configure once at module load.
// webClientId sets the `aud` claim in the returned idToken so the backend
// can verify it. The Android client from google-services.json is used
// automatically by the native SDK — no JS env var needed for it.
GoogleSignin.configure({
  webClientId: GOOGLE_OAUTH_CONFIG.webClientId,
  scopes: GOOGLE_OAUTH_SCOPES,
});

/**
 * Google Auth Hook State
 */
export interface GoogleAuthState {
  loading: boolean;
  error: GoogleAuthError | null;
  userInfo: GoogleUserInfo | null;
  idToken: string | null;
}

/**
 * Google Auth Hook Return Type
 */
export interface GoogleAuthHook extends GoogleAuthState {
  promptAsync: () => Promise<void>;
  reset: () => void;
  isConfigured: boolean;
}

/**
 * useGoogleAuth Hook
 *
 * Handles Google Sign-In using the native Android SDK via
 * @react-native-google-signin/google-signin. No browser is opened;
 * Google Play Services handles the entire flow natively.
 *
 * @example
 * ```tsx
 * const { promptAsync, loading, error, userInfo, idToken, isConfigured } = useGoogleAuth();
 *
 * const handleSignIn = async () => {
 *   await promptAsync();
 * };
 *
 * useEffect(() => {
 *   if (idToken) {
 *     // Send ID token to backend for validation
 *     authService.signInWithGoogle(idToken);
 *   }
 * }, [idToken]);
 * ```
 */
export const useGoogleAuth = (): GoogleAuthHook => {
  const [state, setState] = useState<GoogleAuthState>({
    loading: false,
    error: null,
    userInfo: null,
    idToken: null,
  });

  const promptAsync = useCallback(async (): Promise<void> => {
    if (!GoogleAuthService.isConfigured() && !__DEV__) {
      setState((prev) => ({
        ...prev,
        error: new GoogleAuthError(
          'Google OAuth not configured. Ensure EXPO_PUBLIC_GOOGLE_WEB_CLIENT_ID is set in EAS secrets.',
          'NOT_CONFIGURED'
        ),
      }));
      return;
    }

    setState((prev) => ({ ...prev, loading: true, error: null }));

    try {
      await GoogleSignin.hasPlayServices({ showPlayServicesUpdateDialog: true });
      const response = await GoogleSignin.signIn();

      if (isCancelledResponse(response)) {
        setState((prev) => ({
          ...prev,
          loading: false,
          error: new GoogleAuthError('User cancelled the sign-in flow', 'USER_CANCELLED'),
        }));
        return;
      }

      if (!isSuccessResponse(response)) {
        setState((prev) => ({
          ...prev,
          loading: false,
          error: new GoogleAuthError('Unexpected sign-in response', 'UNEXPECTED_RESPONSE'),
        }));
        return;
      }

      const idToken = response.data.idToken;
      if (!idToken) {
        // null when webClientId is missing from GoogleSignin.configure()
        setState((prev) => ({
          ...prev,
          loading: false,
          error: new GoogleAuthError(
            'No ID token returned — ensure EXPO_PUBLIC_GOOGLE_WEB_CLIENT_ID is set in EAS secrets',
            'MISSING_ID_TOKEN'
          ),
        }));
        return;
      }

      const userInfo = GoogleAuthService.parseIdToken(idToken);

      setState({
        loading: false,
        error: null,
        userInfo,
        idToken,
      });
    } catch (error) {
      let authError: GoogleAuthError;

      if (isErrorWithCode(error)) {
        switch (error.code) {
          case statusCodes.SIGN_IN_CANCELLED:
            authError = new GoogleAuthError('User cancelled the sign-in flow', 'USER_CANCELLED', error);
            break;
          case statusCodes.IN_PROGRESS:
            authError = new GoogleAuthError('Sign-in already in progress', 'AUTH_LOCKED', error);
            break;
          case statusCodes.PLAY_SERVICES_NOT_AVAILABLE:
            authError = new GoogleAuthError('Google Play Services not available or outdated', 'PLAY_SERVICES_UNAVAILABLE', error);
            break;
          default:
            authError = new GoogleAuthError(`Sign-in error: ${error.message}`, error.code, error);
        }
      } else {
        authError = new GoogleAuthError(
          'Failed to sign in with Google',
          'SIGN_IN_ERROR',
          error as Error
        );
      }

      setState((prev) => ({
        ...prev,
        loading: false,
        error: authError,
        userInfo: null,
        idToken: null,
      }));
    }
  }, []);

  // Reset state
  const reset = (): void => {
    setState({
      loading: false,
      error: null,
      userInfo: null,
      idToken: null,
    });
  };

  return {
    ...state,
    promptAsync,
    reset,
    isConfigured: GoogleAuthService.isConfigured(),
  };
};

export default useGoogleAuth;
