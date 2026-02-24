/**
 * Google Auth Service Tests
 *
 * Tests for the live methods only:
 *   - parseIdToken()   client-side ID token decoding
 *   - isConfigured()   webClientId guard
 *   - GoogleAuthError  typed error class
 *
 * The legacy expo-auth-session methods (validateOAuthResponse,
 * getUserInfoFromResponse, getOAuthConfig) were removed in PR #750 as part of
 * the migration to @react-native-google-signin/google-signin.
 */

import GoogleAuthService, {
  GoogleAuthError,
  type GoogleUserInfo,
} from '../src/services/googleAuth.service';

describe('Google Auth Service', () => {
  const mockIdTokenPayload = {
    sub: 'google-user-123',
    email: 'test@waooaw.com',
    email_verified: true,
    name: 'Test User',
    picture: 'https://example.com/avatar.jpg',
  };

  const createMockIdToken = (payload: object): string => {
    const header = btoa(JSON.stringify({ alg: 'RS256', typ: 'JWT' }));
    const body = btoa(JSON.stringify(payload));
    return `${header}.${body}.mock-signature`;
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

    it('should throw GoogleAuthError for invalid token format', () => {
      expect(() => {
        GoogleAuthService.parseIdToken('invalid-token');
      }).toThrow(GoogleAuthError);
    });

    it('should throw GoogleAuthError for malformed token', () => {
      expect(() => {
        GoogleAuthService.parseIdToken('header.invalid-base64!@#$.signature');
      }).toThrow(GoogleAuthError);
    });

    it('should propagate ID_TOKEN_PARSE_ERROR code', () => {
      try {
        GoogleAuthService.parseIdToken('bad');
      } catch (err) {
        expect(err).toBeInstanceOf(GoogleAuthError);
        expect((err as GoogleAuthError).code).toBe('ID_TOKEN_PARSE_ERROR');
      }
    });
  });

  describe('isConfigured', () => {
    it('should return a boolean', () => {
      expect(typeof GoogleAuthService.isConfigured()).toBe('boolean');
    });

    it('should return false for placeholder values', () => {
      const originalEnv = { ...process.env };
      process.env.EXPO_PUBLIC_GOOGLE_WEB_CLIENT_ID = 'YOUR_WEB_CLIENT_ID';
      jest.resetModules();
      // eslint-disable-next-line @typescript-eslint/no-var-requires
      const { default: FreshGoogleAuthService } = require('../src/services/googleAuth.service');
      expect(FreshGoogleAuthService.isConfigured()).toBe(false);
      process.env = originalEnv;
    });

    it('should return true when web client ID is set', () => {
      const originalEnv = { ...process.env };
      process.env.EXPO_PUBLIC_GOOGLE_WEB_CLIENT_ID = 'test-web.apps.googleusercontent.com';
      jest.resetModules();
      // eslint-disable-next-line @typescript-eslint/no-var-requires
      const { default: FreshGoogleAuthService } = require('../src/services/googleAuth.service');
      expect(FreshGoogleAuthService.isConfigured()).toBe(true);
      process.env = originalEnv;
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

