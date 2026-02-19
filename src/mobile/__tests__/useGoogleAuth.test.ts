/**
 * Google Auth Hook Tests
 */

import { renderHook, act, waitFor } from '@testing-library/react-native';
import { useGoogleAuth } from '../src/hooks/useGoogleAuth';
import GoogleAuthService, { GoogleAuthError } from '../src/services/googleAuth.service';

// Mock expo-auth-session
const mockPromptAsync = jest.fn();
const mockUseAuthRequest = jest.fn(() => [
  { type: 'request' }, // request
  null, // response
  mockPromptAsync, // promptAsync
]);

jest.mock('expo-auth-session/providers/google', () => ({
  useAuthRequest: (...args: any[]) => mockUseAuthRequest(...args),
}));

// Mock GoogleAuthService
jest.mock('../src/services/googleAuth.service', () => ({
  __esModule: true,
  default: {
    validateOAuthResponse: jest.fn(),
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

// Mock expo-web-browser
jest.mock('expo-web-browser', () => ({
  maybeCompleteAuthSession: jest.fn(),
}));

describe('useGoogleAuth Hook', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockUseAuthRequest.mockReturnValue([
      { type: 'request' },
      null,
      mockPromptAsync,
    ]);
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

    it('should check if configured', () => {
      const { result } = renderHook(() => useGoogleAuth());

      expect(result.current.isConfigured).toBe(true);
    });
  });

  describe('Prompt Async', () => {
    it('should call promptAsync when invoked', async () => {
      const { result } = renderHook(() => useGoogleAuth());

      await act(async () => {
        await result.current.promptAsync();
      });

      expect(mockPromptAsync).toHaveBeenCalled();
    });

    it('should set error if not configured', async () => {
      (GoogleAuthService.isConfigured as jest.Mock).mockReturnValue(false);

      const { result } = renderHook(() => useGoogleAuth());

      await act(async () => {
        await result.current.promptAsync();
      });

      expect(result.current.error).not.toBeNull();
      expect(result.current.error?.code).toBe('NOT_CONFIGURED');
      expect(mockPromptAsync).not.toHaveBeenCalled();
    });

    it('should set error if request not ready', async () => {
      mockUseAuthRequest.mockReturnValue([
        null, // no request
        null,
        mockPromptAsync,
      ]);

      const { result } = renderHook(() => useGoogleAuth());

      await act(async () => {
        await result.current.promptAsync();
      });

      expect(result.current.error).not.toBeNull();
      expect(result.current.error?.code).toBe('REQUEST_NOT_READY');
    });

    it('should handle promptAsync errors', async () => {
      mockPromptAsync.mockRejectedValue(new Error('Network error'));

      const { result } = renderHook(() => useGoogleAuth());

      await act(async () => {
        await result.current.promptAsync();
      });

      expect(result.current.error).not.toBeNull();
      expect(result.current.error?.code).toBe('PROMPT_ERROR');
      expect(result.current.loading).toBe(false);
    });
  });

  describe('Response Handling', () => {
    it('should handle successful response', async () => {
      const mockIdToken = 'mock-id-token';
      const mockUserInfo = {
        sub: 'user-123',
        email: 'test@waooaw.com',
        email_verified: true,
        name: 'Test User',
      };

      (GoogleAuthService.validateOAuthResponse as jest.Mock).mockReturnValue(mockIdToken);
      (GoogleAuthService.parseIdToken as jest.Mock).mockReturnValue(mockUserInfo);

      const { result, rerender } = renderHook(() => useGoogleAuth());

      // Simulate successful response
      mockUseAuthRequest.mockReturnValue([
        { type: 'request' },
        {
          type: 'success',
          params: { id_token: mockIdToken },
        },
        mockPromptAsync,
      ]);

      rerender();

      await waitFor(() => {
        expect(result.current.idToken).toBe(mockIdToken);
        expect(result.current.userInfo).toEqual(mockUserInfo);
        expect(result.current.error).toBeNull();
        expect(result.current.loading).toBe(false);
      });
    });

    it('should handle cancelled response', async () => {
      const mockError = new GoogleAuthError('User cancelled', 'USER_CANCELLED');
      (GoogleAuthService.validateOAuthResponse as jest.Mock).mockImplementation(() => {
        throw mockError;
      });

      const { result, rerender } = renderHook(() => useGoogleAuth());

      // Simulate cancelled response
      mockUseAuthRequest.mockReturnValue([
        { type: 'request' },
        {
          type: 'cancel',
        },
        mockPromptAsync,
      ]);

      rerender();

      await waitFor(() => {
        expect(result.current.error).not.toBeNull();
        expect(result.current.error?.code).toBe('USER_CANCELLED');
        expect(result.current.idToken).toBeNull();
        expect(result.current.userInfo).toBeNull();
      });
    });

    it('should handle error response', async () => {
      const mockError = new GoogleAuthError('OAuth error', 'OAUTH_ERROR');
      (GoogleAuthService.validateOAuthResponse as jest.Mock).mockImplementation(() => {
        throw mockError;
      });

      const { result, rerender } = renderHook(() => useGoogleAuth());

      // Simulate error response
      mockUseAuthRequest.mockReturnValue([
        { type: 'request' },
        {
          type: 'error',
          params: { error: 'access_denied' },
        },
        mockPromptAsync,
      ]);

      rerender();

      await waitFor(() => {
        expect(result.current.error).not.toBeNull();
        expect(result.current.loading).toBe(false);
      });
    });
  });

  describe('Reset', () => {
    it('should reset state', async () => {
      const { result } = renderHook(() => useGoogleAuth());

      // Set some state manually (simulating previous sign in)
      mockUseAuthRequest.mockReturnValue([
        { type: 'request' },
        {
          type: 'success',
          params: { id_token: 'token' },
        },
        mockPromptAsync,
      ]);

      (GoogleAuthService.validateOAuthResponse as jest.Mock).mockReturnValue('token');
      (GoogleAuthService.parseIdToken as jest.Mock).mockReturnValue({
        sub: 'user-123',
        email: 'test@waooaw.com',
        email_verified: true,
      });

      const { rerender } = renderHook(() => useGoogleAuth());
      rerender();

      await waitFor(() => {
        expect(result.current.idToken).toBe('token');
      });

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
