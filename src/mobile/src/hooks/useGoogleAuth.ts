/**
 * Google Auth Hook
 * React hook for Google OAuth2 authentication flow
 */

import { useEffect, useState } from 'react';
import { Platform } from 'react-native';
import * as Google from 'expo-auth-session/providers/google';
import { makeRedirectUri } from 'expo-auth-session';
import GoogleAuthService, {
  GoogleAuthError,
  type GoogleUserInfo,
  type GoogleAuthResponse,
} from '../services/googleAuth.service';
import { GOOGLE_OAUTH_CONFIG, GOOGLE_OAUTH_SCOPES } from '../config/oauth.config';

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
 * Handles Google OAuth2 sign-in flow using expo-auth-session
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

  // On Android, use the Android OAuth client (type=1) with its auto-whitelisted
  // reverse-scheme redirect URI: com.googleusercontent.apps.{hash}:/oauth2redirect
  //
  // GCP Web clients (type=3) reject custom URI schemes ("must contain a domain"),
  // so the Web client cannot be used with a custom scheme redirect on Android.
  // The Android OAuth client auto-approves the reverse-scheme URI — no GCP
  // Console change required. expo-auth-session uses PKCE code exchange, which
  // Google's token endpoint supports for Android clients.
  //
  // The reverse-scheme intent filter is registered in app.json so Android can
  // route the Chrome Custom Tab redirect back to the app after sign-in.
  const redirectUri = Platform.OS === 'android' && GOOGLE_OAUTH_CONFIG.androidClientId
    ? makeRedirectUri({
        native: `com.googleusercontent.apps.${
          GOOGLE_OAUTH_CONFIG.androidClientId.replace('.apps.googleusercontent.com', '')
        }:/oauth2redirect`,
      })
    : makeRedirectUri({ scheme: 'waooaw' });

  const authRequestConfig: Google.GoogleAuthRequestConfig = Platform.OS === 'android'
    ? {
        androidClientId: GOOGLE_OAUTH_CONFIG.androidClientId,
        scopes: GOOGLE_OAUTH_SCOPES,
        redirectUri,
      }
    : {
        clientId: GOOGLE_OAUTH_CONFIG.expoClientId,
        iosClientId: GOOGLE_OAUTH_CONFIG.iosClientId,
        webClientId: GOOGLE_OAUTH_CONFIG.webClientId,
        scopes: GOOGLE_OAUTH_SCOPES,
        redirectUri,
      };

  // Create OAuth request using expo-auth-session
  const [request, response, promptAsync] = Google.useAuthRequest(authRequestConfig);

  // Handle OAuth response
  useEffect(() => {
    if (!response) return;

    setState((prev) => ({ ...prev, loading: true, error: null }));

    try {
      if (response.type === 'success') {
        // Validate response and extract ID token
        const idToken = GoogleAuthService.validateOAuthResponse(
          response as GoogleAuthResponse
        );

        // Parse ID token to get user info
        const userInfo = GoogleAuthService.parseIdToken(idToken);

        setState({
          loading: false,
          error: null,
          userInfo,
          idToken,
        });
      } else {
        // Handle error, cancel, or dismiss
        try {
          GoogleAuthService.validateOAuthResponse(response as GoogleAuthResponse);
        } catch (error) {
          if (error instanceof GoogleAuthError) {
            setState({
              loading: false,
              error,
              userInfo: null,
              idToken: null,
            });
          } else {
            setState({
              loading: false,
              error: new GoogleAuthError(
                'Unknown error occurred',
                'UNKNOWN_ERROR',
                error as Error
              ),
              userInfo: null,
              idToken: null,
            });
          }
        }
      }
    } catch (error) {
      setState({
        loading: false,
        error: error instanceof GoogleAuthError
          ? error
          : new GoogleAuthError(
              'Failed to process sign-in response',
              'PROCESSING_ERROR',
              error as Error
            ),
        userInfo: null,
        idToken: null,
      });
    }
  }, [response]);

  // Wrapper for promptAsync with loading state
  const handlePromptAsync = async (): Promise<void> => {
    if (!request) {
      setState((prev) => ({
        ...prev,
        error: new GoogleAuthError(
          'OAuth request not ready',
          'REQUEST_NOT_READY'
        ),
      }));
      return;
    }

    // Skip OAuth config check in development mode
    if (!GoogleAuthService.isConfigured() && !__DEV__) {
      setState((prev) => ({
        ...prev,
        error: new GoogleAuthError(
          'Google OAuth client IDs not configured. Please add client IDs to oauth.config.ts',
          'NOT_CONFIGURED'
        ),
      }));
      return;
    }

    setState((prev) => ({ ...prev, loading: true, error: null }));

    try {
      await promptAsync();
    } catch (error) {
      setState((prev) => ({
        ...prev,
        loading: false,
        error: new GoogleAuthError(
          'Failed to start sign-in flow',
          'PROMPT_ERROR',
          error as Error
        ),
      }));
    }
  };

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
    promptAsync: handlePromptAsync,
    reset,
    isConfigured: GoogleAuthService.isConfigured(),
  };
};

export default useGoogleAuth;
