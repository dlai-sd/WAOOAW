/**
 * Google Auth Hook
 * React hook for Google OAuth2 authentication flow
 */

import { useEffect, useState } from 'react';
import { Platform } from 'react-native';
import * as Google from 'expo-auth-session/providers/google';
import { makeRedirectUri, ResponseType } from 'expo-auth-session';
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

  // Build the redirect URI that matches what Google Cloud Console auto-registers
  // for Android OAuth clients.
  //
  // expo-auth-session v7 default generates: com.waooaw.app:/oauthredirect
  // Google Android OAuth client auto-registers: com.googleusercontent.apps.{hash}:/oauth2redirect
  //
  // These must match exactly or Google returns 400 invalid_request.
  //
  // For non-Android (web / dev), fall back to the standard scheme-based URI.
  const redirectUri = Platform.OS === 'android' && GOOGLE_OAUTH_CONFIG.androidClientId
    ? makeRedirectUri({
        native: `com.googleusercontent.apps.${
          GOOGLE_OAUTH_CONFIG.androidClientId.replace('.apps.googleusercontent.com', '')
        }:/oauth2redirect`,
      })
    : makeRedirectUri({ scheme: 'waooaw' });

  // On Android native we MUST use only the Android client ID with the custom URI
  // scheme redirect. Passing webClientId alongside androidClientId causes
  // expo-auth-session v7 to use the web client ID in the OAuth request, which
  // Google rejects with "Custom URI scheme is not enabled for your Android client".
  const authRequestConfig = Platform.OS === 'android'
    ? {
        androidClientId: GOOGLE_OAUTH_CONFIG.androidClientId,
        // ResponseType.IdToken: Google returns id_token directly in redirect params.
        // Without this, expo-auth-session v7 defaults to ResponseType.Token which
        // returns access_token only — no id_token ever arrives, causing MISSING_ID_TOKEN.
        // The library auto-generates a nonce when IdToken is requested (required by Google).
        responseType: ResponseType.IdToken,
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
