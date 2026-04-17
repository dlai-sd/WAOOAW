/**
 * Google Auth Hook
 * React hook for Google Sign-In.
 *
 * Platform behaviour:
 *   - Android/iOS: uses @react-native-google-signin/google-signin (native Play Services SDK)
 *   - Web (Codespace / browser preview): uses expo-auth-session OAuth2 redirect to Google's
 *     token endpoint, which supports HTTPS redirect URIs.
 *
 * Why native SDK on mobile instead of expo-auth-session:
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

import { useCallback, useEffect, useMemo, useState } from 'react';
import { Platform } from 'react-native';
import {
  GoogleSignin,
  statusCodes,
  isSuccessResponse,
  isCancelledResponse,
  isErrorWithCode,
} from '@react-native-google-signin/google-signin';
import * as AuthSession from 'expo-auth-session';
import * as Google from 'expo-auth-session/providers/google';
import GoogleAuthService, {
  GoogleAuthError,
  type GoogleUserInfo,
} from '../services/googleAuth.service';
import { GOOGLE_OAUTH_CONFIG, GOOGLE_OAUTH_SCOPES } from '../config/oauth.config';

// Configure native SDK once at module load (no-op on web).
if (Platform.OS !== 'web') {
  GoogleSignin.configure({
    webClientId: GOOGLE_OAUTH_CONFIG.webClientId,
    scopes: GOOGLE_OAUTH_SCOPES,
  });
}

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
/**
 * Web-only inner hook that uses expo-auth-session's Google provider.
 * Uses ResponseType.IdToken so Google returns an id_token directly in
 * the URL fragment (OpenID Connect implicit flow). A nonce is required.
 */
function useWebGoogleAuth() {
  // Stable nonce per hook mount — used to bind the id_token to this request.
  const nonce = useMemo(
    () => Math.random().toString(36).slice(2) + Math.random().toString(36).slice(2),
    []
  );

  // On web, makeRedirectUri() returns window.location.origin (no trailing slash).
  const redirectUri = AuthSession.makeRedirectUri();
  // eslint-disable-next-line no-console
  console.log('[useGoogleAuth] web redirectUri:', redirectUri);

  const [_request, response, promptAsync] = Google.useAuthRequest({
    clientId: GOOGLE_OAUTH_CONFIG.webClientId,
    scopes: GOOGLE_OAUTH_SCOPES,
    redirectUri,
    responseType: AuthSession.ResponseType.IdToken,
    extraParams: { nonce },
  });
  return { webPromptAsync: promptAsync, webResponse: response };
}

export const useGoogleAuth = (): GoogleAuthHook => {
  const [state, setState] = useState<GoogleAuthState>({
    loading: false,
    error: null,
    userInfo: null,
    idToken: null,
  });

  // Web OAuth session (only active on web platform).
  const { webPromptAsync, webResponse } = useWebGoogleAuth();

  // Handle web OAuth redirect response.
  useEffect(() => {
    if (Platform.OS !== 'web') return;
    if (!webResponse) return;

    if (webResponse.type === 'cancel' || webResponse.type === 'dismiss') {
      setState((prev) => ({
        ...prev,
        loading: false,
        error: new GoogleAuthError('User cancelled the sign-in flow', 'USER_CANCELLED'),
      }));
      return;
    }

    if (webResponse.type === 'error') {
      setState((prev) => ({
        ...prev,
        loading: false,
        error: new GoogleAuthError(
          webResponse.error?.message ?? 'OAuth error',
          'SIGN_IN_ERROR'
        ),
      }));
      return;
    }

    if (webResponse.type === 'success') {
      const idToken = (webResponse.params as any).id_token as string | undefined;
      // DEBUG: decode JWT payload to expose aud/iss/exp in browser DevTools
      if (idToken) {
        try {
          const parts = idToken.split('.');
          const raw = parts[1].replace(/-/g, '+').replace(/_/g, '/');
          const pad = raw + '='.repeat((4 - (raw.length % 4)) % 4);
          const decoded = JSON.parse(atob(pad));
          // eslint-disable-next-line no-console
          console.log('[useGoogleAuth] id_token claims:', {
            aud: decoded.aud,
            iss: decoded.iss,
            exp: decoded.exp,
            exp_utc: decoded.exp ? new Date(decoded.exp * 1000).toISOString() : null,
            email: decoded.email,
            sub: decoded.sub,
          });
        } catch (e) {
          // eslint-disable-next-line no-console
          console.log('[useGoogleAuth] could not decode id_token:', e);
        }
      }
      if (!idToken) {
        // Authorization code flow — exchange for token using TokenResponse.
        // expo-auth-session/providers/google returns tokens directly in the
        // `authentication` field when using the implicit flow.
        const authentication = (webResponse as any).authentication;
        const fallbackToken = authentication?.idToken;
        if (!fallbackToken) {
          setState((prev) => ({
            ...prev,
            loading: false,
            error: new GoogleAuthError(
              'No ID token in Google response',
              'MISSING_ID_TOKEN'
            ),
          }));
          return;
        }
        const userInfo = GoogleAuthService.parseIdToken(fallbackToken);
        setState({ loading: false, error: null, userInfo, idToken: fallbackToken });
        return;
      }
      const userInfo = GoogleAuthService.parseIdToken(idToken);
      setState({ loading: false, error: null, userInfo, idToken });
    }
  }, [webResponse]);

  const promptAsync = useCallback(async (): Promise<void> => {
    // ── Web path ──────────────────────────────────────────────────────────
    if (Platform.OS === 'web') {
      if (!GOOGLE_OAUTH_CONFIG.webClientId) {
        setState((prev) => ({
          ...prev,
          error: new GoogleAuthError(
            'Google OAuth not configured. Ensure EXPO_PUBLIC_GOOGLE_WEB_CLIENT_ID is set.',
            'NOT_CONFIGURED'
          ),
        }));
        return;
      }
      setState((prev) => ({ ...prev, loading: true, error: null }));
      try {
        await webPromptAsync();
      } catch (err) {
        setState((prev) => ({
          ...prev,
          loading: false,
          error: new GoogleAuthError(
            'Failed to open Google sign-in',
            'SIGN_IN_ERROR',
            err as Error
          ),
        }));
      }
      return;
    }

    // ── Native (Android / iOS) path ───────────────────────────────────────
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

      // Sign out first so the native SDK clears its cached credentials and
      // forces the account-picker to be shown every time the button is pressed.
      try {
        await GoogleSignin.signOut();
      } catch {
        // Not a problem — signOut may throw if not currently signed in.
      }

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
      setState({ loading: false, error: null, userInfo, idToken });
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
  }, [webPromptAsync]);

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
    isConfigured: Platform.OS === 'web'
      ? !!GOOGLE_OAUTH_CONFIG.webClientId
      : GoogleAuthService.isConfigured(),
  };
};

export default useGoogleAuth;
