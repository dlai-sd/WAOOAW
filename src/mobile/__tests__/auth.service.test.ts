/**
 * Authentication Service Tests
 * Tests for auth flow orchestration and integration
 */

// Mock modules before importing
jest.mock('expo-web-browser');
jest.mock('expo-auth-session');

import { AuthService, AuthServiceError, AuthErrorCode, UserProfile } from '../src/services/auth.service';
import { TokenManagerService, TokenResponse } from '../src/services/tokenManager.service';
import { GoogleAuthService } from '../src/services/googleAuth.service';
import secureStorage from '../src/lib/secureStorage';
import apiClient from '../src/lib/apiClient';

// Mock dependencies
jest.mock('../src/lib/apiClient');
jest.mock('../src/lib/secureStorage');
jest.mock('../src/services/tokenManager.service');
jest.mock('../src/services/googleAuth.service');

describe('AuthService', () => {
  const mockIdToken = 'eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwiZW1haWwiOiJ0ZXN0QGV4YW1wbGUuY29tIiwibmFtZSI6IlRlc3QgVXNlciIsInBpY3R1cmUiOiJodHRwczovL2V4YW1wbGUuY29tL2F2YXRhci5qcGciLCJlbWFpbF92ZXJpZmllZCI6dHJ1ZX0.signature';

  const mockGoogleUserInfo = {
    sub: '1234567890',
    email: 'test@example.com',
    email_verified: true,
    name: 'Test User',
    picture: 'https://example.com/avatar.jpg',
  };

  const mockTokenResponse: TokenResponse = {
    access_token: 'mock_access_token',
    refresh_token: 'mock_refresh_token',
    token_type: 'bearer',
    expires_in: 900,
  };

  const mockDecodedToken = {
    user_id: 'user_123',
    email: 'test@example.com',
    token_type: 'access' as const,
    exp: Math.floor(Date.now() / 1000) + 900,
    iat: Math.floor(Date.now() / 1000),
    iss: 'waooaw.com',
    sub: 'user_123',
    roles: ['user'],
  };

  const mockUserProfile: UserProfile = {
    id: 'user_123',
    email: 'test@example.com',
    name: 'Test User',
    picture: 'https://example.com/avatar.jpg',
    provider: 'google',
    authenticated_at: expect.any(String),
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('loginWithGoogle', () => {
    it('should successfully login with valid ID token', async () => {
      // Mock GoogleAuthService.parseIdToken
      (GoogleAuthService.parseIdToken as jest.Mock).mockReturnValue(mockGoogleUserInfo);

      // Mock API response
      (apiClient.post as jest.Mock).mockResolvedValue({
        data: mockTokenResponse,
      });

      // Mock TokenManagerService
      (TokenManagerService.saveTokens as jest.Mock).mockResolvedValue(undefined);
      (TokenManagerService.decodeToken as jest.Mock).mockReturnValue(mockDecodedToken);

      // Mock SecureStorage
      (secureStorage.setUserData as jest.Mock).mockResolvedValue(undefined);

      const result = await AuthService.loginWithGoogle(mockIdToken);

      // Verify GoogleAuthService.parseIdToken was called
      expect(GoogleAuthService.parseIdToken).toHaveBeenCalledWith(mockIdToken);

      // Verify API call
      expect(apiClient.post).toHaveBeenCalledWith('/auth/google/verify', {
        id_token: mockIdToken,
        source: 'mobile',
      });

      // Verify TokenManagerService.saveTokens was called
      expect(TokenManagerService.saveTokens).toHaveBeenCalledWith(mockTokenResponse);

      // Verify TokenManagerService.decodeToken was called
      expect(TokenManagerService.decodeToken).toHaveBeenCalledWith(mockTokenResponse.access_token);

      // Verify user data saved
      expect(secureStorage.setUserData).toHaveBeenCalledWith(
        expect.objectContaining({
          id: 'user_123',
          email: 'test@example.com',
          name: 'Test User',
          picture: 'https://example.com/avatar.jpg',
          provider: 'google',
        })
      );

      // Verify result
      expect(result).toMatchObject({
        id: 'user_123',
        email: 'test@example.com',
        name: 'Test User',
        picture: 'https://example.com/avatar.jpg',
        provider: 'google',
      });
      expect(result.authenticated_at).toBeDefined();
    });

    it('should successfully login with 2FA code', async () => {
      const totpCode = '123456';

      (GoogleAuthService.parseIdToken as jest.Mock).mockReturnValue(mockGoogleUserInfo);
      (apiClient.post as jest.Mock).mockResolvedValue({
        data: mockTokenResponse,
      });
      (TokenManagerService.saveTokens as jest.Mock).mockResolvedValue(undefined);
      (TokenManagerService.decodeToken as jest.Mock).mockReturnValue(mockDecodedToken);
      (secureStorage.setUserData as jest.Mock).mockResolvedValue(undefined);

      await AuthService.loginWithGoogle(mockIdToken, totpCode);

      // Verify 2FA code included in API call
      expect(apiClient.post).toHaveBeenCalledWith('/auth/google/verify', {
        id_token: mockIdToken,
        source: 'mobile',
        totp_code: totpCode,
      });
    });

    it('should throw error for invalid ID token format', async () => {
      await expect(AuthService.loginWithGoogle('')).rejects.toThrow(
        AuthServiceError
      );
      await expect(AuthService.loginWithGoogle('')).rejects.toMatchObject({
        code: AuthErrorCode.INVALID_ID_TOKEN,
      });
    });

    it('should handle 2FA required error', async () => {
      (GoogleAuthService.parseIdToken as jest.Mock).mockReturnValue(mockGoogleUserInfo);
      (apiClient.post as jest.Mock).mockRejectedValue({
        response: {
          status: 401,
          data: { detail: '2FA required' },
        },
      });

      await expect(AuthService.loginWithGoogle(mockIdToken)).rejects.toThrow(
        AuthServiceError
      );
      await expect(AuthService.loginWithGoogle(mockIdToken)).rejects.toMatchObject({
        code: AuthErrorCode.TWO_FA_REQUIRED,
      });
    });

    it('should handle invalid 2FA code error', async () => {
      (GoogleAuthService.parseIdToken as jest.Mock).mockReturnValue(mockGoogleUserInfo);
      (apiClient.post as jest.Mock).mockRejectedValue({
        response: {
          status: 401,
          data: { detail: 'Invalid 2FA code' },
        },
      });

      await expect(AuthService.loginWithGoogle(mockIdToken, '123456')).rejects.toThrow(
        AuthServiceError
      );
      await expect(AuthService.loginWithGoogle(mockIdToken, '123456')).rejects.toMatchObject({
        code: AuthErrorCode.INVALID_TWO_FA_CODE,
      });
    });

    it('should handle backend verification failure', async () => {
      (GoogleAuthService.parseIdToken as jest.Mock).mockReturnValue(mockGoogleUserInfo);
      (apiClient.post as jest.Mock).mockRejectedValue(
        new Error('Network error')
      );

      await expect(AuthService.loginWithGoogle(mockIdToken)).rejects.toThrow(
        AuthServiceError
      );
      await expect(AuthService.loginWithGoogle(mockIdToken)).rejects.toMatchObject({
        code: AuthErrorCode.BACKEND_VERIFICATION_FAILED,
      });
    });

    it('should handle token storage failure', async () => {
      (GoogleAuthService.parseIdToken as jest.Mock).mockReturnValue(mockGoogleUserInfo);
      (apiClient.post as jest.Mock).mockResolvedValue({
        data: mockTokenResponse,
      });
      (TokenManagerService.saveTokens as jest.Mock).mockRejectedValue(
        new Error('Storage error')
      );

      await expect(AuthService.loginWithGoogle(mockIdToken)).rejects.toThrow(
        AuthServiceError
      );
      await expect(AuthService.loginWithGoogle(mockIdToken)).rejects.toMatchObject({
        code: AuthErrorCode.TOKEN_STORAGE_FAILED,
      });
    });

    it('should handle user data storage failure', async () => {
      (GoogleAuthService.parseIdToken as jest.Mock).mockReturnValue(mockGoogleUserInfo);
      (apiClient.post as jest.Mock).mockResolvedValue({
        data: mockTokenResponse,
      });
      (TokenManagerService.saveTokens as jest.Mock).mockResolvedValue(undefined);
      (TokenManagerService.decodeToken as jest.Mock).mockReturnValue(mockDecodedToken);
      (secureStorage.setUserData as jest.Mock).mockRejectedValue(
        new Error('Storage error')
      );

      await expect(AuthService.loginWithGoogle(mockIdToken)).rejects.toThrow(
        AuthServiceError
      );
      await expect(AuthService.loginWithGoogle(mockIdToken)).rejects.toMatchObject({
        code: AuthErrorCode.USER_DATA_STORAGE_FAILED,
      });
    });
  });

  describe('logout', () => {
    it('should clear all authentication data', async () => {
      (secureStorage.clearAll as jest.Mock).mockResolvedValue(undefined);

      await AuthService.logout();

      expect(secureStorage.clearAll).toHaveBeenCalled();
    });

    it('should not throw error if cleanup fails', async () => {
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation();
      (secureStorage.clearAll as jest.Mock).mockRejectedValue(
        new Error('Storage error')
      );

      await expect(AuthService.logout()).resolves.not.toThrow();

      expect(consoleSpy).toHaveBeenCalled();
      consoleSpy.mockRestore();
    });
  });

  describe('isAuthenticated', () => {
    it('should return true when user is authenticated', async () => {
      (secureStorage.isAuthenticated as jest.Mock).mockResolvedValue(true);

      const result = await AuthService.isAuthenticated();

      expect(result).toBe(true);
      expect(secureStorage.isAuthenticated).toHaveBeenCalled();
    });

    it('should return false when user is not authenticated', async () => {
      (secureStorage.isAuthenticated as jest.Mock).mockResolvedValue(false);

      const result = await AuthService.isAuthenticated();

      expect(result).toBe(false);
    });

    it('should return false on error', async () => {
      (secureStorage.isAuthenticated as jest.Mock).mockRejectedValue(
        new Error('Storage error')
      );

      const result = await AuthService.isAuthenticated();

      expect(result).toBe(false);
    });
  });

  describe('getCurrentUser', () => {
    it('should return user profile when authenticated', async () => {
      (secureStorage.isAuthenticated as jest.Mock).mockResolvedValue(true);
      (secureStorage.getUserData as jest.Mock).mockResolvedValue(mockUserProfile);

      const result = await AuthService.getCurrentUser();

      expect(result).toEqual(mockUserProfile);
    });

    it('should return null when not authenticated', async () => {
      (secureStorage.isAuthenticated as jest.Mock).mockResolvedValue(false);

      const result = await AuthService.getCurrentUser();

      expect(result).toBeNull();
      expect(secureStorage.getUserData).not.toHaveBeenCalled();
    });

    it('should return null when user data not found', async () => {
      (secureStorage.isAuthenticated as jest.Mock).mockResolvedValue(true);
      (secureStorage.getUserData as jest.Mock).mockResolvedValue(null);

      const result = await AuthService.getCurrentUser();

      expect(result).toBeNull();
    });

    it('should return null on error', async () => {
      (secureStorage.isAuthenticated as jest.Mock).mockRejectedValue(
        new Error('Storage error')
      );

      const result = await AuthService.getCurrentUser();

      expect(result).toBeNull();
    });
  });

  describe('refreshToken', () => {
    it('should return true when refresh succeeds', async () => {
      (TokenManagerService.refreshAccessToken as jest.Mock).mockResolvedValue(
        mockTokenResponse
      );

      const result = await AuthService.refreshToken();

      expect(result).toBe(true);
      expect(TokenManagerService.refreshAccessToken).toHaveBeenCalled();
    });

    it('should return false when refresh fails', async () => {
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation();
      (TokenManagerService.refreshAccessToken as jest.Mock).mockRejectedValue(
        new Error('Refresh failed')
      );

      const result = await AuthService.refreshToken();

      expect(result).toBe(false);
      expect(consoleSpy).toHaveBeenCalled();
      consoleSpy.mockRestore();
    });

    it('should return false when refresh returns null', async () => {
      (TokenManagerService.refreshAccessToken as jest.Mock).mockResolvedValue(null);

      const result = await AuthService.refreshToken();

      expect(result).toBe(false);
    });
  });

  describe('getAccessToken', () => {
    it('should return access token when available', async () => {
      const mockToken = 'mock_access_token';
      (TokenManagerService.getAccessToken as jest.Mock).mockResolvedValue(mockToken);

      const result = await AuthService.getAccessToken();

      expect(result).toBe(mockToken);
    });

    it('should return null on error', async () => {
      (TokenManagerService.getAccessToken as jest.Mock).mockRejectedValue(
        new Error('Token not found')
      );

      const result = await AuthService.getAccessToken();

      expect(result).toBeNull();
    });
  });

  describe('getUserInfo', () => {
    it('should return user info from token', async () => {
      const mockUserInfo = {
        userId: 'user_123',
        email: 'test@example.com',
        roles: ['user'],
      };
      (TokenManagerService.getUserInfo as jest.Mock).mockResolvedValue(mockUserInfo);

      const result = await AuthService.getUserInfo();

      expect(result).toEqual(mockUserInfo);
    });

    it('should return null on error', async () => {
      (TokenManagerService.getUserInfo as jest.Mock).mockRejectedValue(
        new Error('Token not found')
      );

      const result = await AuthService.getUserInfo();

      expect(result).toBeNull();
    });
  });

  describe('validateAuthState', () => {
    it('should return valid state when fully authenticated', async () => {
      (secureStorage.getAccessToken as jest.Mock).mockResolvedValue(mockTokenResponse.access_token);
      (secureStorage.getUserData as jest.Mock).mockResolvedValue(mockUserProfile);
      (TokenManagerService.decodeToken as jest.Mock).mockReturnValue(mockDecodedToken);
      (TokenManagerService.isTokenExpired as jest.Mock).mockReturnValue(false);
      (TokenManagerService.validateTokenClaims as jest.Mock).mockReturnValue(true);

      const result = await AuthService.validateAuthState();

      expect(result).toEqual({
        valid: true,
        hasTokens: true,
        hasUserProfile: true,
        tokenExpired: false,
        issuerValid: true,
      });
    });

    it('should return invalid state when tokens missing', async () => {
      (secureStorage.getAccessToken as jest.Mock).mockResolvedValue(null);
      (secureStorage.getUserData as jest.Mock).mockResolvedValue(mockUserProfile);

      const result = await AuthService.validateAuthState();

      expect(result).toEqual({
        valid: false,
        hasTokens: false,
        hasUserProfile: true,
        tokenExpired: true,
        issuerValid: false,
      });
    });

    it('should return invalid state when user profile missing', async () => {
      (secureStorage.getAccessToken as jest.Mock).mockResolvedValue(mockTokenResponse.access_token);
      (secureStorage.getUserData as jest.Mock).mockResolvedValue(null);

      const result = await AuthService.validateAuthState();

      expect(result.valid).toBe(false);
      expect(result.hasUserProfile).toBe(false);
    });

    it('should return invalid state when token expired', async () => {
      (secureStorage.getAccessToken as jest.Mock).mockResolvedValue(mockTokenResponse.access_token);
      (secureStorage.getUserData as jest.Mock).mockResolvedValue(mockUserProfile);
      (TokenManagerService.decodeToken as jest.Mock).mockReturnValue(mockDecodedToken);
      (TokenManagerService.isTokenExpired as jest.Mock).mockReturnValue(true);
      (TokenManagerService.validateTokenClaims as jest.Mock).mockReturnValue(true);

      const result = await AuthService.validateAuthState();

      expect(result.valid).toBe(false);
      expect(result.tokenExpired).toBe(true);
    });

    it('should return invalid state when issuer invalid', async () => {
      (secureStorage.getAccessToken as jest.Mock).mockResolvedValue(mockTokenResponse.access_token);
      (secureStorage.getUserData as jest.Mock).mockResolvedValue(mockUserProfile);
      (TokenManagerService.decodeToken as jest.Mock).mockReturnValue(mockDecodedToken);
      (TokenManagerService.isTokenExpired as jest.Mock).mockReturnValue(false);
      (TokenManagerService.validateTokenClaims as jest.Mock).mockReturnValue(false);

      const result = await AuthService.validateAuthState();

      expect(result.valid).toBe(false);
      expect(result.issuerValid).toBe(false);
    });

    it('should handle token decoding errors', async () => {
      (secureStorage.getAccessToken as jest.Mock).mockResolvedValue(mockTokenResponse.access_token);
      (secureStorage.getUserData as jest.Mock).mockResolvedValue(mockUserProfile);
      (TokenManagerService.decodeToken as jest.Mock).mockImplementation(() => {
        throw new Error('Invalid token');
      });

      const result = await AuthService.validateAuthState();

      expect(result.valid).toBe(false);
      expect(result.tokenExpired).toBe(true);
      expect(result.issuerValid).toBe(false);
    });

    it('should return invalid state on error', async () => {
      (secureStorage.getAccessToken as jest.Mock).mockRejectedValue(
        new Error('Storage error')
      );

      const result = await AuthService.validateAuthState();

      expect(result).toEqual({
        valid: false,
        hasTokens: false,
        hasUserProfile: false,
        tokenExpired: true,
        issuerValid: false,
      });
    });
  });

  describe('AuthServiceError', () => {
    it('should create error with code and message', () => {
      const error = new AuthServiceError(
        'Test error',
        AuthErrorCode.INVALID_ID_TOKEN
      );

      expect(error.message).toBe('Test error');
      expect(error.code).toBe(AuthErrorCode.INVALID_ID_TOKEN);
      expect(error.name).toBe('AuthServiceError');
    });

    it('should include original error', () => {
      const originalError = new Error('Original');
      const error = new AuthServiceError(
        'Test error',
        AuthErrorCode.BACKEND_VERIFICATION_FAILED,
        originalError
      );

      expect(error.originalError).toBe(originalError);
    });
  });
});
