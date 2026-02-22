/**
 * Secure Storage Tests
 * Tests for expo-secure-store wrapper
 */

import * as SecureStore from 'expo-secure-store';
import secureStorage, {
  SecureStorageService,
  SecureStorageError,
  STORAGE_KEYS,
  type TokenData,
  type StoredUserData,
} from '../src/lib/secureStorage';

// Mock expo-secure-store
jest.mock('expo-secure-store', () => ({
  setItemAsync: jest.fn(),
  getItemAsync: jest.fn(),
  deleteItemAsync: jest.fn(),
}));

describe('Secure Storage', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Access Token', () => {
    it('should store access token', async () => {
      (SecureStore.setItemAsync as jest.Mock).mockResolvedValue(undefined);

      await secureStorage.setAccessToken('test-token');

      expect(SecureStore.setItemAsync).toHaveBeenCalledWith(
        STORAGE_KEYS.ACCESS_TOKEN,
        'test-token'
      );
    });

    it('should retrieve access token', async () => {
      (SecureStore.getItemAsync as jest.Mock).mockResolvedValue('stored-token');

      const token = await secureStorage.getAccessToken();

      expect(token).toBe('stored-token');
      expect(SecureStore.getItemAsync).toHaveBeenCalledWith(
        STORAGE_KEYS.ACCESS_TOKEN
      );
    });

    it('should return null if no token stored', async () => {
      (SecureStore.getItemAsync as jest.Mock).mockResolvedValue(null);

      const token = await secureStorage.getAccessToken();

      expect(token).toBeNull();
    });

    it('should throw SecureStorageError on store failure', async () => {
      (SecureStore.setItemAsync as jest.Mock).mockRejectedValue(
        new Error('Storage error')
      );

      await expect(secureStorage.setAccessToken('token')).rejects.toThrow(
        SecureStorageError
      );
    });

    it('should throw SecureStorageError on retrieve failure', async () => {
      (SecureStore.getItemAsync as jest.Mock).mockRejectedValue(
        new Error('Retrieve error')
      );

      await expect(secureStorage.getAccessToken()).rejects.toThrow(
        SecureStorageError
      );
    });
  });

  describe('Refresh Token', () => {
    it('should store refresh token', async () => {
      (SecureStore.setItemAsync as jest.Mock).mockResolvedValue(undefined);

      await secureStorage.setRefreshToken('refresh-token');

      expect(SecureStore.setItemAsync).toHaveBeenCalledWith(
        STORAGE_KEYS.REFRESH_TOKEN,
        'refresh-token'
      );
    });

    it('should retrieve refresh token', async () => {
      (SecureStore.getItemAsync as jest.Mock).mockResolvedValue('refresh-token');

      const token = await secureStorage.getRefreshToken();

      expect(token).toBe('refresh-token');
    });
  });

  describe('Token Expiry', () => {
    beforeEach(() => {
      jest.useFakeTimers();
      jest.setSystemTime(new Date('2026-02-17T12:00:00Z')); // 1708171200
    });

    afterEach(() => {
      jest.useRealTimers();
    });

    it('should store token expiry', async () => {
      (SecureStore.setItemAsync as jest.Mock).mockResolvedValue(undefined);

      await secureStorage.setTokenExpiry(3600); // 1 hour

      const expectedExpiry = Math.floor(Date.now() / 1000) + 3600;
      expect(SecureStore.setItemAsync).toHaveBeenCalledWith(
        STORAGE_KEYS.TOKEN_EXPIRES_AT,
        expectedExpiry.toString()
      );
    });

    it('should retrieve token expiry', async () => {
      const expiry = 1708174800; // 1 hour from mocked time
      (SecureStore.getItemAsync as jest.Mock).mockResolvedValue(expiry.toString());

      const result = await secureStorage.getTokenExpiry();

      expect(result).toBe(expiry);
    });

    it('should return null if expiry not set', async () => {
      (SecureStore.getItemAsync as jest.Mock).mockResolvedValue(null);

      const result = await secureStorage.getTokenExpiry();

      expect(result).toBeNull();
    });

    it('should detect expired token', async () => {
      const pastExpiry = Math.floor(Date.now() / 1000) - 100; // 100s ago
      (SecureStore.getItemAsync as jest.Mock).mockResolvedValue(
        pastExpiry.toString()
      );

      const expired = await secureStorage.isTokenExpired();

      expect(expired).toBe(true);
    });

    it('should detect valid token', async () => {
      const futureExpiry = Math.floor(Date.now() / 1000) + 3600; // 1h from now
      (SecureStore.getItemAsync as jest.Mock).mockResolvedValue(
        futureExpiry.toString()
      );

      const expired = await secureStorage.isTokenExpired();

      expect(expired).toBe(false);
    });

    it('should use buffer time for expiry check', async () => {
      const soonExpiry = Math.floor(Date.now() / 1000) + 20; // 20s from now
      (SecureStore.getItemAsync as jest.Mock).mockResolvedValue(
        soonExpiry.toString()
      );

      // With default 30s buffer, should be considered expired
      const expired = await secureStorage.isTokenExpired();
      expect(expired).toBe(true);

      // With 10s buffer, should still be valid
      const expiredWith10s = await secureStorage.isTokenExpired(10);
      expect(expiredWith10s).toBe(false);
    });

    it('should return true if expiry not set', async () => {
      (SecureStore.getItemAsync as jest.Mock).mockResolvedValue(null);

      const expired = await secureStorage.isTokenExpired();

      expect(expired).toBe(true);
    });
  });

  describe('Token Data (Complete)', () => {
    it('should store complete token data', async () => {
      (SecureStore.setItemAsync as jest.Mock).mockResolvedValue(undefined);

      const tokenData: TokenData = {
        accessToken: 'access-token',
        refreshToken: 'refresh-token',
        expiresAt: 1708174800,
      };

      await secureStorage.setTokens(tokenData);

      expect(SecureStore.setItemAsync).toHaveBeenCalledWith(
        STORAGE_KEYS.ACCESS_TOKEN,
        'access-token'
      );
      expect(SecureStore.setItemAsync).toHaveBeenCalledWith(
        STORAGE_KEYS.REFRESH_TOKEN,
        'refresh-token'
      );
      expect(SecureStore.setItemAsync).toHaveBeenCalledWith(
        STORAGE_KEYS.TOKEN_EXPIRES_AT,
        '1708174800'
      );
    });

    it('should retrieve complete token data', async () => {
      (SecureStore.getItemAsync as jest.Mock)
        .mockResolvedValueOnce('access-token')
        .mockResolvedValueOnce('refresh-token')
        .mockResolvedValueOnce('1708174800');

      const result = await secureStorage.getTokens();

      expect(result).toEqual({
        accessToken: 'access-token',
        refreshToken: 'refresh-token',
        expiresAt: 1708174800,
      });
    });

    it('should return null if access token missing', async () => {
      (SecureStore.getItemAsync as jest.Mock)
        .mockResolvedValueOnce(null) // access token
        .mockResolvedValueOnce('refresh-token')
        .mockResolvedValueOnce('1708174800');

      const result = await secureStorage.getTokens();

      expect(result).toBeNull();
    });

    it('should clear all tokens', async () => {
      (SecureStore.deleteItemAsync as jest.Mock).mockResolvedValue(undefined);

      await secureStorage.clearTokens();

      expect(SecureStore.deleteItemAsync).toHaveBeenCalledWith(
        STORAGE_KEYS.ACCESS_TOKEN
      );
      expect(SecureStore.deleteItemAsync).toHaveBeenCalledWith(
        STORAGE_KEYS.REFRESH_TOKEN
      );
      expect(SecureStore.deleteItemAsync).toHaveBeenCalledWith(
        STORAGE_KEYS.TOKEN_EXPIRES_AT
      );
    });
  });

  describe('Biometric Flag', () => {
    it('should store biometric enabled flag', async () => {
      (SecureStore.setItemAsync as jest.Mock).mockResolvedValue(undefined);

      await secureStorage.setBiometricEnabled(true);

      expect(SecureStore.setItemAsync).toHaveBeenCalledWith(
        STORAGE_KEYS.BIOMETRIC_ENABLED,
        'true'
      );
    });

    it('should store biometric disabled flag', async () => {
      (SecureStore.setItemAsync as jest.Mock).mockResolvedValue(undefined);

      await secureStorage.setBiometricEnabled(false);

      expect(SecureStore.setItemAsync).toHaveBeenCalledWith(
        STORAGE_KEYS.BIOMETRIC_ENABLED,
        'false'
      );
    });

    it('should retrieve biometric enabled flag', async () => {
      (SecureStore.getItemAsync as jest.Mock).mockResolvedValue('true');

      const enabled = await secureStorage.isBiometricEnabled();

      expect(enabled).toBe(true);
    });

    it('should return false if biometric flag not set', async () => {
      (SecureStore.getItemAsync as jest.Mock).mockResolvedValue(null);

      const enabled = await secureStorage.isBiometricEnabled();

      expect(enabled).toBe(false);
    });

    it('should return false on error', async () => {
      (SecureStore.getItemAsync as jest.Mock).mockRejectedValue(
        new Error('Read error')
      );

      const enabled = await secureStorage.isBiometricEnabled();

      expect(enabled).toBe(false);
    });
  });

  describe('User Data', () => {
    it('should store user data', async () => {
      (SecureStore.setItemAsync as jest.Mock).mockResolvedValue(undefined);
      (SecureStore.deleteItemAsync as jest.Mock).mockResolvedValue(undefined);

      const userData: StoredUserData = {
        id: 'user-123',
        email: 'test@waooaw.com',
        name: 'Test User',
        picture: 'https://example.com/avatar.jpg',
      };

      await secureStorage.setUserData(userData);

      expect(SecureStore.setItemAsync).toHaveBeenCalledWith(
        STORAGE_KEYS.USER_ID,
        'user-123'
      );
      expect(SecureStore.setItemAsync).toHaveBeenCalledWith(
        STORAGE_KEYS.USER_EMAIL,
        'test@waooaw.com'
      );
      expect(SecureStore.setItemAsync).toHaveBeenCalledWith(
        STORAGE_KEYS.USER_NAME,
        'Test User'
      );
      expect(SecureStore.setItemAsync).toHaveBeenCalledWith(
        STORAGE_KEYS.USER_PICTURE,
        'https://example.com/avatar.jpg'
      );
    });

    it('should retrieve user data', async () => {
      (SecureStore.getItemAsync as jest.Mock)
        .mockResolvedValueOnce('user-123')
        .mockResolvedValueOnce('test@waooaw.com')
        .mockResolvedValueOnce('Test User')
        .mockResolvedValueOnce('https://example.com/avatar.jpg');

      const result = await secureStorage.getUserData();

      expect(result).toEqual({
        id: 'user-123',
        email: 'test@waooaw.com',
        name: 'Test User',
        picture: 'https://example.com/avatar.jpg',
      });
    });

    it('should return null if user data missing', async () => {
      (SecureStore.getItemAsync as jest.Mock)
        .mockResolvedValueOnce(null) // id
        .mockResolvedValueOnce('test@waooaw.com');

      const result = await secureStorage.getUserData();

      expect(result).toBeNull();
    });

    it('should clear user data', async () => {
      (SecureStore.deleteItemAsync as jest.Mock).mockResolvedValue(undefined);

      await secureStorage.clearUserData();

      expect(SecureStore.deleteItemAsync).toHaveBeenCalledWith(STORAGE_KEYS.USER_ID);
      expect(SecureStore.deleteItemAsync).toHaveBeenCalledWith(STORAGE_KEYS.USER_EMAIL);
      expect(SecureStore.deleteItemAsync).toHaveBeenCalledWith(STORAGE_KEYS.USER_NAME);
      expect(SecureStore.deleteItemAsync).toHaveBeenCalledWith(
        STORAGE_KEYS.USER_PICTURE
      );
    });
  });

  describe('Clear All', () => {
    it('should clear all storage', async () => {
      (SecureStore.deleteItemAsync as jest.Mock).mockResolvedValue(undefined);

      await secureStorage.clearAll();

      // Should delete all keys
      const keyCount = Object.keys(STORAGE_KEYS).length;
      expect(SecureStore.deleteItemAsync).toHaveBeenCalledTimes(keyCount);
    });

    it('should throw SecureStorageError on clear failure', async () => {
      (SecureStore.deleteItemAsync as jest.Mock).mockRejectedValue(
        new Error('Delete error')
      );

      await expect(secureStorage.clearAll()).rejects.toThrow(SecureStorageError);
    });
  });

  describe('Authentication Check', () => {
    beforeEach(() => {
      jest.useFakeTimers();
      jest.setSystemTime(new Date('2026-02-17T12:00:00Z'));
    });

    afterEach(() => {
      jest.useRealTimers();
    });

    it('should return true if token exists and not expired', async () => {
      const futureExpiry = Math.floor(Date.now() / 1000) + 3600;
      (SecureStore.getItemAsync as jest.Mock)
        .mockResolvedValueOnce('valid-token')
        .mockResolvedValueOnce(futureExpiry.toString());

      const authenticated = await secureStorage.isAuthenticated();

      expect(authenticated).toBe(true);
    });

    it('should return false if no token', async () => {
      (SecureStore.getItemAsync as jest.Mock).mockResolvedValue(null);

      const authenticated = await secureStorage.isAuthenticated();

      expect(authenticated).toBe(false);
    });

    it('should return false if token expired', async () => {
      const pastExpiry = Math.floor(Date.now() / 1000) - 100;
      (SecureStore.getItemAsync as jest.Mock)
        .mockResolvedValueOnce('expired-token')
        .mockResolvedValueOnce(pastExpiry.toString());

      const authenticated = await secureStorage.isAuthenticated();

      expect(authenticated).toBe(false);
    });

    it('should return false on error', async () => {
      (SecureStore.getItemAsync as jest.Mock).mockRejectedValue(
        new Error('Storage error')
      );

      const authenticated = await secureStorage.isAuthenticated();

      expect(authenticated).toBe(false);
    });
  });
});
