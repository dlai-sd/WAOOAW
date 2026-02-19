/**
 * Secure Storage Service
 * Wrapper around expo-secure-store for secure token and credential storage
 * Uses iOS Keychain and Android KeyStore
 */

import * as SecureStore from 'expo-secure-store';

/**
 * Storage keys
 */
const STORAGE_KEYS = {
  ACCESS_TOKEN: 'cp_access_token',
  REFRESH_TOKEN: 'cp_refresh_token',
  TOKEN_EXPIRES_AT: 'token_expires_at',
  BIOMETRIC_ENABLED: 'biometric_enabled',
  USER_ID: 'user_id',
  USER_EMAIL: 'user_email',
  USER_NAME: 'user_name',
  USER_PICTURE: 'user_picture',
} as const;

/**
 * Storage error types
 */
export class SecureStorageError extends Error {
  constructor(message: string, public originalError?: Error) {
    super(message);
    this.name = 'SecureStorageError';
  }
}

/**
 * User data interface
 */
export interface StoredUserData {
  id: string;
  email: string;
  name?: string;
  picture?: string;
}

/**
 * Token data interface
 */
export interface TokenData {
  accessToken: string;
  refreshToken?: string;
  expiresAt: number; // Unix timestamp in seconds
}

/**
 * Secure Storage Service
 */
class SecureStorageService {
  /**
   * Set access token
   */
  async setAccessToken(token: string): Promise<void> {
    try {
      await SecureStore.setItemAsync(STORAGE_KEYS.ACCESS_TOKEN, token);
    } catch (error) {
      throw new SecureStorageError(
        'Failed to store access token',
        error as Error
      );
    }
  }

  /**
   * Get access token
   */
  async getAccessToken(): Promise<string | null> {
    try {
      return await SecureStore.getItemAsync(STORAGE_KEYS.ACCESS_TOKEN);
    } catch (error) {
      throw new SecureStorageError(
        'Failed to retrieve access token',
        error as Error
      );
    }
  }

  /**
   * Set refresh token
   */
  async setRefreshToken(token: string): Promise<void> {
    try {
      await SecureStore.setItemAsync(STORAGE_KEYS.REFRESH_TOKEN, token);
    } catch (error) {
      throw new SecureStorageError(
        'Failed to store refresh token',
        error as Error
      );
    }
  }

  /**
   * Get refresh token
   */
  async getRefreshToken(): Promise<string | null> {
    try {
      return await SecureStore.getItemAsync(STORAGE_KEYS.REFRESH_TOKEN);
    } catch (error) {
      throw new SecureStorageError(
        'Failed to retrieve refresh token',
        error as Error
      );
    }
  }

  /**
   * Set token expiry time
   * @param expiresIn - Seconds until token expires (from token response)
   */
  async setTokenExpiry(expiresIn: number): Promise<void> {
    try {
      const expiresAt = Math.floor(Date.now() / 1000) + expiresIn;
      await SecureStore.setItemAsync(
        STORAGE_KEYS.TOKEN_EXPIRES_AT,
        expiresAt.toString()
      );
    } catch (error) {
      throw new SecureStorageError(
        'Failed to store token expiry',
        error as Error
      );
    }
  }

  /**
   * Get token expiry timestamp
   * @returns Unix timestamp in seconds, or null if not set
   */
  async getTokenExpiry(): Promise<number | null> {
    try {
      const expiresAt = await SecureStore.getItemAsync(
        STORAGE_KEYS.TOKEN_EXPIRES_AT
      );
      return expiresAt ? parseInt(expiresAt, 10) : null;
    } catch (error) {
      throw new SecureStorageError(
        'Failed to retrieve token expiry',
        error as Error
      );
    }
  }

  /**
   * Check if access token is expired
   * @param bufferSeconds - Add buffer time (default: 30s) to account for network latency
   */
  async isTokenExpired(bufferSeconds: number = 30): Promise<boolean> {
    try {
      const expiresAt = await this.getTokenExpiry();
      if (!expiresAt) return true;

      const now = Math.floor(Date.now() / 1000);
      return now + bufferSeconds >= expiresAt;
    } catch (error) {
      // If we can't determine expiry, assume expired for safety
      console.warn('[SecureStorage] Failed to check token expiry:', error);
      return true;
    }
  }

  /**
   * Store complete token data (access token + refresh token + expiry)
   */
  async setTokens(data: TokenData): Promise<void> {
    try {
      await Promise.all([
        this.setAccessToken(data.accessToken),
        data.refreshToken
          ? this.setRefreshToken(data.refreshToken)
          : Promise.resolve(),
        SecureStore.setItemAsync(
          STORAGE_KEYS.TOKEN_EXPIRES_AT,
          data.expiresAt.toString()
        ),
      ]);
    } catch (error) {
      throw new SecureStorageError(
        'Failed to store token data',
        error as Error
      );
    }
  }

  /**
   * Retrieve complete token data
   */
  async getTokens(): Promise<TokenData | null> {
    try {
      const [accessToken, refreshToken, expiresAtStr] = await Promise.all([
        this.getAccessToken(),
        this.getRefreshToken(),
        SecureStore.getItemAsync(STORAGE_KEYS.TOKEN_EXPIRES_AT),
      ]);

      if (!accessToken || !expiresAtStr) {
        return null;
      }

      return {
        accessToken,
        refreshToken: refreshToken || undefined,
        expiresAt: parseInt(expiresAtStr, 10),
      };
    } catch (error) {
      throw new SecureStorageError(
        'Failed to retrieve token data',
        error as Error
      );
    }
  }

  /**
   * Clear all tokens
   */
  async clearTokens(): Promise<void> {
    try {
      await Promise.all([
        SecureStore.deleteItemAsync(STORAGE_KEYS.ACCESS_TOKEN),
        SecureStore.deleteItemAsync(STORAGE_KEYS.REFRESH_TOKEN),
        SecureStore.deleteItemAsync(STORAGE_KEYS.TOKEN_EXPIRES_AT),
      ]);
    } catch (error) {
      throw new SecureStorageError('Failed to clear tokens', error as Error);
    }
  }

  /**
   * Set biometric authentication enabled flag
   */
  async setBiometricEnabled(enabled: boolean): Promise<void> {
    try {
      await SecureStore.setItemAsync(
        STORAGE_KEYS.BIOMETRIC_ENABLED,
        enabled ? 'true' : 'false'
      );
    } catch (error) {
      throw new SecureStorageError(
        'Failed to set biometric flag',
        error as Error
      );
    }
  }

  /**
   * Get biometric authentication enabled flag
   */
  async isBiometricEnabled(): Promise<boolean> {
    try {
      const value = await SecureStore.getItemAsync(
        STORAGE_KEYS.BIOMETRIC_ENABLED
      );
      return value === 'true';
    } catch (error) {
      // Default to false if not set or error
      return false;
    }
  }

  /**
   * Store user data
   */
  async setUserData(user: StoredUserData): Promise<void> {
    try {
      await Promise.all([
        SecureStore.setItemAsync(STORAGE_KEYS.USER_ID, user.id),
        SecureStore.setItemAsync(STORAGE_KEYS.USER_EMAIL, user.email),
        user.name
          ? SecureStore.setItemAsync(STORAGE_KEYS.USER_NAME, user.name)
          : SecureStore.deleteItemAsync(STORAGE_KEYS.USER_NAME),
        user.picture
          ? SecureStore.setItemAsync(STORAGE_KEYS.USER_PICTURE, user.picture)
          : SecureStore.deleteItemAsync(STORAGE_KEYS.USER_PICTURE),
      ]);
    } catch (error) {
      throw new SecureStorageError(
        'Failed to store user data',
        error as Error
      );
    }
  }

  /**
   * Retrieve user data
   */
  async getUserData(): Promise<StoredUserData | null> {
    try {
      const [id, email, name, picture] = await Promise.all([
        SecureStore.getItemAsync(STORAGE_KEYS.USER_ID),
        SecureStore.getItemAsync(STORAGE_KEYS.USER_EMAIL),
        SecureStore.getItemAsync(STORAGE_KEYS.USER_NAME),
        SecureStore.getItemAsync(STORAGE_KEYS.USER_PICTURE),
      ]);

      if (!id || !email) {
        return null;
      }

      return {
        id,
        email,
        name: name || undefined,
        picture: picture || undefined,
      };
    } catch (error) {
      throw new SecureStorageError(
        'Failed to retrieve user data',
        error as Error
      );
    }
  }

  /**
   * Clear user data
   */
  async clearUserData(): Promise<void> {
    try {
      await Promise.all([
        SecureStore.deleteItemAsync(STORAGE_KEYS.USER_ID),
        SecureStore.deleteItemAsync(STORAGE_KEYS.USER_EMAIL),
        SecureStore.deleteItemAsync(STORAGE_KEYS.USER_NAME),
        SecureStore.deleteItemAsync(STORAGE_KEYS.USER_PICTURE),
      ]);
    } catch (error) {
      throw new SecureStorageError(
        'Failed to clear user data',
        error as Error
      );
    }
  }

  /**
   * Clear all stored data
   */
  async clearAll(): Promise<void> {
    try {
      await Promise.all(
        Object.values(STORAGE_KEYS).map((key) =>
          SecureStore.deleteItemAsync(key)
        )
      );
    } catch (error) {
      throw new SecureStorageError(
        'Failed to clear all storage',
        error as Error
      );
    }
  }

  /**
   * Check if user is authenticated (has valid token)
   */
  async isAuthenticated(): Promise<boolean> {
    try {
      const token = await this.getAccessToken();
      if (!token) return false;

      const expired = await this.isTokenExpired();
      return !expired;
    } catch (error) {
      console.warn('[SecureStorage] Failed to check authentication:', error);
      return false;
    }
  }
}

/**
 * Singleton instance
 */
const secureStorage = new SecureStorageService();

/**
 * Export singleton instance
 */
export default secureStorage;

/**
 * Export class for testing
 */
export { SecureStorageService, STORAGE_KEYS };
