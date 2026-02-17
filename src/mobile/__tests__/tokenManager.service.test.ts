/**
 * Token Manager Service Tests
 * Tests JWT token decoding, validation, and lifecycle management
 */

import TokenManagerService, {
  TokenManagerError,
  type DecodedToken,
  type TokenResponse,
} from '../src/services/tokenManager.service';
import secureStorage from '../src/lib/secureStorage';
import apiClient from '../src/lib/apiClient';

// Mock dependencies
jest.mock('../src/lib/secureStorage');
jest.mock('../src/lib/apiClient');

describe('Token Manager Service', () => {
  // Helper to create mock JWT token
  const createMockToken = (payload: Partial<DecodedToken>): string => {
    const header = { alg: 'HS256', typ: 'JWT' };
    const defaultPayload: DecodedToken = {
      user_id: 'user-123',
      email: 'test@waooaw.com',
      token_type: 'access',
      exp: Math.floor(Date.now() / 1000) + 900, // 15 minutes
      iat: Math.floor(Date.now() / 1000),
      roles: ['user'],
      iss: 'waooaw.com',
      sub: 'user-123',
      ...payload,
    };

    const encodedHeader = btoa(JSON.stringify(header));
    const encodedPayload = btoa(JSON.stringify(defaultPayload));
    const signature = 'mock-signature';

    return `${encodedHeader}.${encodedPayload}.${signature}`;
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('decodeToken', () => {
    it('should decode valid JWT token', () => {
      const token = createMockToken({});
      const decoded = TokenManagerService.decodeToken(token);

      expect(decoded.user_id).toBe('user-123');
      expect(decoded.email).toBe('test@waooaw.com');
      expect(decoded.token_type).toBe('access');
      expect(decoded.roles).toEqual(['user']);
      expect(decoded.iss).toBe('waooaw.com');
      expect(decoded.exp).toBeDefined();
      expect(decoded.iat).toBeDefined();
    });

    it('should decode token with minimal claims', () => {
      const token = createMockToken({
        roles: undefined,
       iss: undefined,
        sub: undefined,
      });
      const decoded = TokenManagerService.decodeToken(token);

      expect(decoded.user_id).toBe('user-123');
      expect(decoded.email).toBe('test@waooaw.com');
      expect(decoded.roles).toBeUndefined();
    });

    it('should throw error for invalid token format', () => {
      expect(() => {
        TokenManagerService.decodeToken('invalid-token');
      }).toThrow(TokenManagerError);
    });

    it('should throw error for malformed token', () => {
      expect(() => {
        TokenManagerService.decodeToken('header.invalid-payload.signature');
      }).toThrow(TokenManagerError);
    });
  });

  describe('isTokenExpired', () => {
    beforeEach(() => {
      jest.useFakeTimers();
      jest.setSystemTime(new Date('2026-02-17T12:00:00Z'));
    });

    afterEach(() => {
      jest.useRealTimers();
    });

    it('should detect expired token', () => {
      const token = createMockToken({
        exp: Math.floor(Date.now() / 1000) - 100, // 100s ago
      });
      const decoded = TokenManagerService.decodeToken(token);
      const isExpired = TokenManagerService.isTokenExpired(decoded);

      expect(isExpired).toBe(true);
    });

    it('should detect valid token', () => {
      const token = createMockToken({
        exp: Math.floor(Date.now() / 1000) + 3600, // 1 hour from now
      });
      const decoded = TokenManagerService.decodeToken(token);
      const isExpired = TokenManagerService.isTokenExpired(decoded);

      expect(isExpired).toBe(false);
    });

    it('should use buffer time for expiry check', () => {
      const token = createMockToken({
        exp: Math.floor(Date.now() / 1000) + 20, // 20s from now
      });
      const decoded = TokenManagerService.decodeToken(token);

      // With default 30s buffer, should be considered expired
      expect(TokenManagerService.isTokenExpired(decoded)).toBe(true);

      // With 10s buffer, should still be valid
      expect(TokenManagerService.isTokenExpired(decoded, 10)).toBe(false);
    });
  });

  describe('getTokenExpiry', () => {
    it('should return expiry as Date', () => {
      const expTimestamp = Math.floor(Date.now() / 1000) + 900;
      const token = createMockToken({ exp: expTimestamp });
      const decoded = TokenManagerService.decodeToken(token);
      const expiry = TokenManagerService.getTokenExpiry(decoded);

      expect(expiry).toBeInstanceOf(Date);
      expect(expiry.getTime()).toBe(expTimestamp * 1000);
    });
  });

  describe('getTokenIssuedAt', () => {
    it('should return issued at as Date', () => {
      const iatTimestamp = Math.floor(Date.now() / 1000);
      const token = createMockToken({ iat: iatTimestamp });
      const decoded = TokenManagerService.decodeToken(token);
      const issuedAt = TokenManagerService.getTokenIssuedAt(decoded);

      expect(issuedAt).toBeInstanceOf(Date);
      expect(issuedAt.getTime()).toBe(iatTimestamp * 1000);
    });
  });

  describe('saveTokens', () => {
    it('should save tokens to secure storage', async () => {
      const response: TokenResponse = {
        access_token: 'access-token-123',
        refresh_token: 'refresh-token-456',
        token_type: 'bearer',
        expires_in: 900,
      };

      (secureStorage.setTokens as jest.Mock).mockResolvedValue(undefined);

      await TokenManagerService.saveTokens(response);

      expect(secureStorage.setTokens).toHaveBeenCalledWith({
        accessToken: 'access-token-123',
        refreshToken: 'refresh-token-456',
        expiresAt: expect.any(Number),
      });
    });

    it('should throw TokenManagerError on save failure', async () => {
      const response: TokenResponse = {
        access_token: 'token',
        refresh_token: 'refresh',
        token_type: 'bearer',
        expires_in: 900,
      };

      (secureStorage.setTokens as jest.Mock).mockRejectedValue(
        new Error('Storage error')
      );

      await expect(TokenManagerService.saveTokens(response)).rejects.toThrow(
        TokenManagerError
      );
    });
  });

  describe('getAccessToken', () => {
    it('should return valid access token', async () => {
      (secureStorage.getAccessToken as jest.Mock).mockResolvedValue('valid-token');
      (secureStorage.isTokenExpired as jest.Mock).mockResolvedValue(false);

      const token = await TokenManagerService.getAccessToken();

      expect(token).toBe('valid-token');
    });

    it('should return null if no token stored', async () => {
      (secureStorage.getAccessToken as jest.Mock).mockResolvedValue(null);

      const token = await TokenManagerService.getAccessToken();

      expect(token).toBeNull();
    });

    it('should clear and return null if token expired', async () => {
      (secureStorage.getAccessToken as jest.Mock).mockResolvedValue('expired-token');
      (secureStorage.isTokenExpired as jest.Mock).mockResolvedValue(true);
      (secureStorage.clearTokens as jest.Mock).mockResolvedValue(undefined);

      const token = await TokenManagerService.getAccessToken();

      expect(token).toBeNull();
      expect(secureStorage.clearTokens).toHaveBeenCalled();
    });
  });

  describe('getRefreshToken', () => {
    it('should return refresh token', async () => {
      (secureStorage.getRefreshToken as jest.Mock).mockResolvedValue('refresh-token');

      const token = await TokenManagerService.getRefreshToken();

      expect(token).toBe('refresh-token');
    });

    it('should return null if no refresh token', async () => {
      (secureStorage.getRefreshToken as jest.Mock).mockResolvedValue(null);

      const token = await TokenManagerService.getRefreshToken();

      expect(token).toBeNull();
    });
  });

  describe('refreshAccessToken', () => {
    it('should refresh access token successfully', async () => {
      const mockResponse: TokenResponse = {
        access_token: 'new-access-token',
        refresh_token: 'new-refresh-token',
        token_type: 'bearer',
        expires_in: 900,
      };

      (secureStorage.getRefreshToken as jest.Mock).mockResolvedValue('refresh-token');
      (apiClient.post as jest.Mock).mockResolvedValue({ data: mockResponse });
      (secureStorage.setTokens as jest.Mock).mockResolvedValue(undefined);

      const newToken = await TokenManagerService.refreshAccessToken();

      expect(newToken).toBe('new-access-token');
      expect(apiClient.post).toHaveBeenCalledWith('/auth/refresh', {
        refresh_token: 'refresh-token',
      });
      expect(secureStorage.setTokens).toHaveBeenCalled();
    });

    it('should return null if no refresh token', async () => {
      (secureStorage.getRefreshToken as jest.Mock).mockResolvedValue(null);

      const newToken = await TokenManagerService.refreshAccessToken();

      expect(newToken).toBeNull();
    });

    it('should clear tokens on refresh failure', async () => {
      (secureStorage.getRefreshToken as jest.Mock).mockResolvedValue('refresh-token');
      (apiClient.post as jest.Mock).mockRejectedValue(new Error('Refresh failed'));
      (secureStorage.clearTokens as jest.Mock).mockResolvedValue(undefined);

      await expect(TokenManagerService.refreshAccessToken()).rejects.toThrow(
        TokenManagerError
      );
      expect(secureStorage.clearTokens).toHaveBeenCalled();
    });
  });

  describe('clearTokens', () => {
    it('should clear all tokens', async () => {
      (secureStorage.clearTokens as jest.Mock).mockResolvedValue(undefined);

      await TokenManagerService.clearTokens();

      expect(secureStorage.clearTokens).toHaveBeenCalled();
    });
  });

  describe('isAuthenticated', () => {
    it('should return true if user is authenticated', async () => {
      (secureStorage.isAuthenticated as jest.Mock).mockResolvedValue(true);

      const isAuth = await TokenManagerService.isAuthenticated();

      expect(isAuth).toBe(true);
    });

    it('should return false if user is not authenticated', async () => {
      (secureStorage.isAuthenticated as jest.Mock).mockResolvedValue(false);

      const isAuth = await TokenManagerService.isAuthenticated();

      expect(isAuth).toBe(false);
    });

    it('should return false on error', async () => {
      (secureStorage.isAuthenticated as jest.Mock).mockRejectedValue(
        new Error('Storage error')
      );

      const isAuth = await TokenManagerService.isAuthenticated();

      expect(isAuth).toBe(false);
    });
  });

  describe('getUserInfo', () => {
    it('should extract user info from token', async () => {
      const token = createMockToken({});
      (secureStorage.getAccessToken as jest.Mock).mockResolvedValue(token);
      (secureStorage.isTokenExpired as jest.Mock).mockResolvedValue(false);

      const userInfo = await TokenManagerService.getUserInfo();

      expect(userInfo).toEqual({
        userId: 'user-123',
        email: 'test@waooaw.com',
        roles: ['user'],
      });
    });

    it('should return null if no token', async () => {
      (secureStorage.getAccessToken as jest.Mock).mockResolvedValue(null);

      const userInfo = await TokenManagerService.getUserInfo();

      expect(userInfo).toBeNull();
    });

    it('should use default roles if not present', async () => {
      const token = createMockToken({ roles: undefined });
      (secureStorage.getAccessToken as jest.Mock).mockResolvedValue(token);
      (secureStorage.isTokenExpired as jest.Mock).mockResolvedValue(false);

      const userInfo = await TokenManagerService.getUserInfo();

      expect(userInfo?.roles).toEqual(['user']);
    });
  });

  describe('validateTokenClaims', () => {
    it('should validate valid token claims', () => {
      const token = createMockToken({});
      const decoded = TokenManagerService.decodeToken(token);
      const isValid = TokenManagerService.validateTokenClaims(decoded);

      expect(isValid).toBe(true);
    });

    it('should reject token without required claims', () => {
      const token = createMockToken({});
      const decoded = TokenManagerService.decodeToken(token);
      
      // Remove required claim
      delete (decoded as any).user_id;
      
      const isValid = TokenManagerService.validateTokenClaims(decoded);
      expect(isValid).toBe(false);
    });

    it('should reject token with wrong issuer', () => {
      const token = createMockToken({ iss: 'wrong-issuer.com' });
      const decoded = TokenManagerService.decodeToken(token);
      const isValid = TokenManagerService.validateTokenClaims(decoded);

      expect(isValid).toBe(false);
    });

    it('should reject token issued in the future', () => {
      const token = createMockToken({
        iat: Math.floor(Date.now() / 1000) + 120, // 2 minutes in future
      });
      const decoded = TokenManagerService.decodeToken(token);
      const isValid = TokenManagerService.validateTokenClaims(decoded);

      expect(isValid).toBe(false);
    });
  });

  describe('getTimeUntilExpiry', () => {
    beforeEach(() => {
      jest.useFakeTimers();
      jest.setSystemTime(new Date('2026-02-17T12:00:00Z'));
    });

    afterEach(() => {
      jest.useRealTimers();
    });

    it('should return positive seconds for valid token', () => {
      const token = createMockToken({
        exp: Math.floor(Date.now() / 1000) + 900, // 15 minutes
      });
      const decoded = TokenManagerService.decodeToken(token);
      const timeUntilExpiry = TokenManagerService.getTimeUntilExpiry(decoded);

      expect(timeUntilExpiry).toBe(900);
    });

    it('should return negative seconds for expired token', () => {
      const token = createMockToken({
        exp: Math.floor(Date.now() / 1000) - 100, // 100s ago
      });
      const decoded = TokenManagerService.decodeToken(token);
      const timeUntilExpiry = TokenManagerService.getTimeUntilExpiry(decoded);

      expect(timeUntilExpiry).toBe(-100);
    });
  });

  describe('shouldRefreshToken', () => {
    beforeEach(() => {
      jest.useFakeTimers();
      jest.setSystemTime(new Date('2026-02-17T12:00:00Z'));
    });

    afterEach(() => {
      jest.useRealTimers();
    });

    it('should return true if token expires within threshold', () => {
      const token = createMockToken({
        exp: Math.floor(Date.now() / 1000) + 30, // 30s from now
      });
      const decoded = TokenManagerService.decodeToken(token);
      const shouldRefresh = TokenManagerService.shouldRefreshToken(decoded, 60);

      expect(shouldRefresh).toBe(true);
    });

    it('should return false if token has plenty of time left', () => {
      const token = createMockToken({
        exp: Math.floor(Date.now() / 1000) + 600, // 10 minutes
      });
      const decoded = TokenManagerService.decodeToken(token);
      const shouldRefresh = TokenManagerService.shouldRefreshToken(decoded, 60);

      expect(shouldRefresh).toBe(false);
    });

    it('should return false if token is already expired', () => {
      const token = createMockToken({
        exp: Math.floor(Date.now() / 1000) - 100, // Already expired
      });
      const decoded = TokenManagerService.decodeToken(token);
      const shouldRefresh = TokenManagerService.shouldRefreshToken(decoded, 60);

      expect(shouldRefresh).toBe(false);
    });
  });

  describe('TokenManagerError', () => {
    it('should create error with code', () => {
      const error = new TokenManagerError('Test error', 'TEST_CODE');

      expect(error.message).toBe('Test error');
      expect(error.code).toBe('TEST_CODE');
      expect(error.name).toBe('TokenManagerError');
    });

    it('should include original error', () => {
      const originalError = new Error('Original');
      const error = new TokenManagerError('Test error', 'TEST_CODE', originalError);

      expect(error.originalError).toBe(originalError);
    });
  });
});
