/**
 * Google Auth Hook Tests
 * Tests for useGoogleAuth using @react-native-google-signin/google-signin (native SDK)
 */

import { renderHook, act } from '@testing-library/react-native';
import { useGoogleAuth } from '../src/hooks/useGoogleAuth';
import { GoogleSignin } from '@react-native-google-signin/google-signin';
import GoogleAuthService, { GoogleAuthError } from '../src/services/googleAuth.service';

// jest.mock is hoisted — factory cannot reference const variables (TDZ).
// Use jest.fn() directly inside the factory; access mocks via the imported module.
jest.mock('@react-native-google-signin/google-signin', () => ({
  GoogleSignin: {
    configure: jest.fn(),
    hasPlayServices: jest.fn(() => Promise.resolve(true)),
    signIn: jest.fn(),
  },
  statusCodes: {
    SIGN_IN_CANCELLED: 'SIGN_IN_CANCELLED',
    IN_PROGRESS: 'IN_PROGRESS',
    PLAY_SERVICES_NOT_AVAILABLE: 'PLAY_SERVICES_NOT_AVAILABLE',
  },
  isSuccessResponse: (r: any) => r?.type === 'success',
  isCancelledResponse: (r: any) => r?.type === 'cancelled',
  isErrorWithCode: (e: any) => typeof e?.code === 'string',
}));

// Mock GoogleAuthService
jest.mock('../src/services/googleAuth.service', () => ({
  __esModule: true,
  default: {
    parseIdToken: jest.fn(),
    isConfigured: jest.fn(() => true),
  },
  GoogleAuthError: class GoogleAuthError extends Error {
    constructor(message: string, public code: string, public originalError?: Error) {
      super(message);
      this.name = 'GoogleAuthError';
    }
  },
}));

// Mock oauth.config (so GoogleSignin.configure() doesn't fail at module load)
jest.mock('../src/config/oauth.config', () => ({
  GOOGLE_OAUTH_CONFIG: {
    expoClientId: '',
    iosClientId: '',
    androidClientId: 'android-client-id',
    webClientId: 'web-client-id',
  },
  GOOGLE_OAUTH_SCOPES: ['openid', 'profile', 'email'],
  OAUTH_REDIRECT_SCHEME: 'waooaw',
}));

describe('useGoogleAuth Hook', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (GoogleSignin.hasPlayServices as jest.Mock).mockResolvedValue(true);
    (GoogleAuthService.isConfigured as jest.Mock).mockReturnValue(true);
  });

  describe('Initial State', () => {
    it('should initialize with default state', () => {
      const { result } = renderHook(() => useGoogleAuth());

      expect(result.current.loading).toBe(false);
      expect(result.current.error).toBeNull();
      expect(result.current.userInfo).toBeNull();
      expect(result.current.idToken).toBeNull();
    });

    it('should have promptAsync function', () => {
      const { result } = renderHook(() => useGoogleAuth());
      expect(typeof result.current.promptAsync).toBe('function');
    });

    it('should have reset function', () => {
      const { result } = renderHook(() => useGoogleAuth());
      expect(typeof result.current.reset).toBe('function');
    });

    it('should reflect isConfigured from GoogleAuthService', () => {
      const { result } = renderHook(() => useGoogleAuth());
      expect(result.current.isConfigured).toBe(true);
    });
  });

  describe('Prompt Async — Success', () => {
    it('should set idToken and userInfo on successful sign-in', async () => {
      const mockIdToken = 'mock-id-token';
      const mockUserInfo = {
        sub: 'user-123',
        email: 'test@waooaw.com',
        email_verified: true,
        name: 'Test User',
      };

      (GoogleSignin.signIn as jest.Mock).mockResolvedValue({
        type: 'success',
        data: { idToken: mockIdToken, user: {} },
      });
      (GoogleAuthService.parseIdToken as jest.Mock).mockReturnValue(mockUserInfo);

      const { result } = renderHook(() => useGoogleAuth());

      await act(async () => {
        await result.current.promptAsync();
      });

      expect(result.current.idToken).toBe(mockIdToken);
      expect(result.current.userInfo).toEqual(mockUserInfo);
      expect(result.current.error).toBeNull();
      expect(result.current.loading).toBe(false);
    });

    it('should call hasPlayServices before signIn', async () => {
      (GoogleSignin.signIn as jest.Mock).mockResolvedValue({
        type: 'success',
        data: { idToken: 'token', user: {} },
      });
      (GoogleAuthService.parseIdToken as jest.Mock).mockReturnValue({ sub: '1', email: 'a@b.com', email_verified: true });

      const { result } = renderHook(() => useGoogleAuth());
      await act(async () => { await result.current.promptAsync(); });

      expect(GoogleSignin.hasPlayServices as jest.Mock).toHaveBeenCalledWith({ showPlayServicesUpdateDialog: true });
    });
  });

  describe('Prompt Async — Cancelled', () => {
    it('should set USER_CANCELLED error when response type is cancelled', async () => {
      (GoogleSignin.signIn as jest.Mock).mockResolvedValue({ type: 'cancelled' });

      const { result } = renderHook(() => useGoogleAuth());

      await act(async () => {
        await result.current.promptAsync();
      });

      expect(result.current.error).not.toBeNull();
      expect(result.current.error?.code).toBe('USER_CANCELLED');
      expect(result.current.idToken).toBeNull();
      expect(result.current.loading).toBe(false);
    });
  });

  describe('Prompt Async — Error Cases', () => {
    it('should set NOT_CONFIGURED error when not configured (non-dev)', async () => {
      (GoogleAuthService.isConfigured as jest.Mock).mockReturnValue(false);
      const origDev = (global as any).__DEV__;
      (global as any).__DEV__ = false;

      const { result } = renderHook(() => useGoogleAuth());

      await act(async () => {
        await result.current.promptAsync();
      });

      expect(result.current.error?.code).toBe('NOT_CONFIGURED');
      expect(GoogleSignin.signIn as jest.Mock).not.toHaveBeenCalled();
      (global as any).__DEV__ = origDev;
    });

    it('should set MISSING_ID_TOKEN error when idToken is null', async () => {
      (GoogleSignin.signIn as jest.Mock).mockResolvedValue({
        type: 'success',
        data: { idToken: null, user: {} },
      });

      const { result } = renderHook(() => useGoogleAuth());

      await act(async () => {
        await result.current.promptAsync();
      });

      expect(result.current.error?.code).toBe('MISSING_ID_TOKEN');
      expect(result.current.loading).toBe(false);
    });

    it('should handle SIGN_IN_CANCELLED statusCode error', async () => {
      const err = new Error('cancelled');
      (err as any).code = 'SIGN_IN_CANCELLED';
      (GoogleSignin.signIn as jest.Mock).mockRejectedValue(err);

      const { result } = renderHook(() => useGoogleAuth());

      await act(async () => {
        await result.current.promptAsync();
      });

      expect(result.current.error?.code).toBe('USER_CANCELLED');
      expect(result.current.loading).toBe(false);
    });

    it('should handle IN_PROGRESS statusCode error', async () => {
      const err = new Error('in progress');
      (err as any).code = 'IN_PROGRESS';
      (GoogleSignin.signIn as jest.Mock).mockRejectedValue(err);

      const { result } = renderHook(() => useGoogleAuth());

      await act(async () => {
        await result.current.promptAsync();
      });

      expect(result.current.error?.code).toBe('AUTH_LOCKED');
    });

    it('should handle PLAY_SERVICES_NOT_AVAILABLE statusCode error', async () => {
      const err = new Error('no play services');
      (err as any).code = 'PLAY_SERVICES_NOT_AVAILABLE';
      (GoogleSignin.signIn as jest.Mock).mockRejectedValue(err);

      const { result } = renderHook(() => useGoogleAuth());

      await act(async () => {
        await result.current.promptAsync();
      });

      expect(result.current.error?.code).toBe('PLAY_SERVICES_UNAVAILABLE');
    });

    it('should handle generic sign-in errors', async () => {
      (GoogleSignin.signIn as jest.Mock).mockRejectedValue(new Error('network error'));

      const { result } = renderHook(() => useGoogleAuth());

      await act(async () => {
        await result.current.promptAsync();
      });

      expect(result.current.error?.code).toBe('SIGN_IN_ERROR');
      expect(result.current.loading).toBe(false);
    });
  });

  describe('Reset', () => {
    it('should reset all state to initial values', async () => {
      (GoogleSignin.signIn as jest.Mock).mockResolvedValue({
        type: 'success',
        data: { idToken: 'token', user: {} },
      });
      (GoogleAuthService.parseIdToken as jest.Mock).mockReturnValue({
        sub: 'user-123',
        email: 'test@waooaw.com',
        email_verified: true,
      });

      const { result } = renderHook(() => useGoogleAuth());

      await act(async () => {
        await result.current.promptAsync();
      });

      expect(result.current.idToken).toBe('token');

      act(() => {
        result.current.reset();
      });

      expect(result.current.loading).toBe(false);
      expect(result.current.error).toBeNull();
      expect(result.current.userInfo).toBeNull();
      expect(result.current.idToken).toBeNull();
    });
  });
});
