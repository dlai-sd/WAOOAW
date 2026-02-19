/**
 * Google Auth Service Tests
 */

import GoogleAuthService, {
  GoogleAuthError,
  type GoogleAuthResponse,
  type GoogleUserInfo,
} from '../src/services/googleAuth.service';

// Mock expo-web-browser
jest.mock('expo-web-browser', () => ({
  maybeCompleteAuthSession: jest.fn(),
  openBrowserAsync: jest.fn(),
  dismissBrowser: jest.fn(),
}));

describe('Google Auth Service', () => {
  // Sample ID token payload (not a real token, just for testing)
  const mockIdTokenPayload = {
    sub: 'google-user-123',
    email: 'test@waooaw.com',
    email_verified: true,
    name: 'Test User',
    picture: 'https://example.com/avatar.jpg',
  };

  // Encode mock ID token
  const createMockIdToken = (payload: object): string => {
    const header = btoa(JSON.stringify({ alg: 'RS256', typ: 'JWT' }));
    const body = btoa(JSON.stringify(payload));
    const signature = 'mock-signature';
    return `${header}.${body}.${signature}`;
  };

  describe('parseIdToken', () => {
    it('should parse valid ID token', () => {
      const idToken = createMockIdToken(mockIdTokenPayload);
      const result = GoogleAuthService.parseIdToken(idToken);

      expect(result.sub).toBe('google-user-123');
      expect(result.email).toBe('test@waooaw.com');
      expect(result.email_verified).toBe(true);
      expect(result.name).toBe('Test User');
      expect(result.picture).toBe('https://example.com/avatar.jpg');
    });

    it('should throw error for invalid token format', () => {
      expect(() => {
        GoogleAuthService.parseIdToken('invalid-token');
      }).toThrow(GoogleAuthError);
    });

    it('should throw error for malformed token', () => {
      expect(() => {
        GoogleAuthService.parseIdToken('header.invalid-base64.signature');
      }).toThrow(GoogleAuthError);
    });
  });

  describe('validateOAuthResponse', () => {
    it('should return ID token for success response', () => {
      const response: GoogleAuthResponse = {
        type: 'success',
        params: {
          id_token: 'mock-id-token',
        },
      };

      const result = GoogleAuthService.validateOAuthResponse(response);
      expect(result).toBe('mock-id-token');
    });

    it('should throw error for cancel response', () => {
      const response: GoogleAuthResponse = {
        type: 'cancel',
      };

      expect(() => {
        GoogleAuthService.validateOAuthResponse(response);
      }).toThrow(GoogleAuthError);

      try {
        GoogleAuthService.validateOAuthResponse(response);
      } catch (error) {
        expect(error).toBeInstanceOf(GoogleAuthError);
        expect((error as GoogleAuthError).code).toBe('USER_CANCELLED');
      }
    });

    it('should throw error for dismiss response', () => {
      const response: GoogleAuthResponse = {
        type: 'dismiss',
      };

      expect(() => {
        GoogleAuthService.validateOAuthResponse(response);
      }).toThrow(GoogleAuthError);

      try {
        GoogleAuthService.validateOAuthResponse(response);
      } catch (error) {
        expect(error).toBeInstanceOf(GoogleAuthError);
        expect((error as GoogleAuthError).code).toBe('USER_DISMISSED');
      }
    });

    it('should throw error for locked response', () => {
      const response: GoogleAuthResponse = {
        type: 'locked',
      };

      expect(() => {
        GoogleAuthService.validateOAuthResponse(response);
      }).toThrow(GoogleAuthError);

      try {
        GoogleAuthService.validateOAuthResponse(response);
      } catch (error) {
        expect(error).toBeInstanceOf(GoogleAuthError);
        expect((error as GoogleAuthError).code).toBe('AUTH_LOCKED');
      }
    });

    it('should throw error for error response', () => {
      const response: GoogleAuthResponse = {
        type: 'error',
        params: {
          error: 'access_denied',
          error_description: 'User denied access',
        },
      };

      expect(() => {
        GoogleAuthService.validateOAuthResponse(response);
      }).toThrow(GoogleAuthError);

      try {
        GoogleAuthService.validateOAuthResponse(response);
      } catch (error) {
        expect(error).toBeInstanceOf(GoogleAuthError);
        expect((error as GoogleAuthError).code).toBe('access_denied');
      }
    });

    it('should throw error if ID token missing', () => {
      const response: GoogleAuthResponse = {
        type: 'success',
        params: {},
      };

      expect(() => {
        GoogleAuthService.validateOAuthResponse(response);
      }).toThrow(GoogleAuthError);

      try {
        GoogleAuthService.validateOAuthResponse(response);
      } catch (error) {
        expect(error).toBeInstanceOf(GoogleAuthError);
        expect((error as GoogleAuthError).code).toBe('MISSING_ID_TOKEN');
      }
    });
  });

  describe('getUserInfoFromResponse', () => {
    it('should extract and parse user info from successful response', () => {
      const idToken = createMockIdToken(mockIdTokenPayload);
      const response: GoogleAuthResponse = {
        type: 'success',
        params: {
          id_token: idToken,
        },
      };

      const result = GoogleAuthService.getUserInfoFromResponse(response);

      expect(result.sub).toBe('google-user-123');
      expect(result.email).toBe('test@waooaw.com');
      expect(result.name).toBe('Test User');
    });

    it('should throw error for cancelled response', () => {
      const response: GoogleAuthResponse = {
        type: 'cancel',
      };

      expect(() => {
        GoogleAuthService.getUserInfoFromResponse(response);
      }).toThrow(GoogleAuthError);
    });
  });

  describe('getOAuthConfig', () => {
    it('should return OAuth configuration', () => {
      const config = GoogleAuthService.getOAuthConfig();

      expect(config).toHaveProperty('expoClientId');
      expect(config).toHaveProperty('iosClientId');
      expect(config).toHaveProperty('androidClientId');
      expect(config).toHaveProperty('webClientId');
      expect(config).toHaveProperty('scopes');
      expect(Array.isArray(config.scopes)).toBe(true);
    });
  });

  describe('isConfigured', () => {
    it('should check if OAuth is configured', () => {
      const result = GoogleAuthService.isConfigured();
      expect(typeof result).toBe('boolean');
    });

    it('should return false for placeholder values', () => {
      // Since we're using placeholder values in config, should be false
      const result = GoogleAuthService.isConfigured();
      expect(result).toBe(false);
    });
  });

  describe('GoogleAuthError', () => {
    it('should create error with code', () => {
      const error = new GoogleAuthError('Test error', 'TEST_CODE');

      expect(error.message).toBe('Test error');
      expect(error.code).toBe('TEST_CODE');
      expect(error.name).toBe('GoogleAuthError');
    });

    it('should include original error', () => {
      const originalError = new Error('Original error');
      const error = new GoogleAuthError('Test error', 'TEST_CODE', originalError);

      expect(error.originalError).toBe(originalError);
    });
  });
});
