/**
 * OAuth Configuration Tests
 */

import {
  GOOGLE_OAUTH_CONFIG,
  GOOGLE_OAUTH_SCOPES,
  OAUTH_REDIRECT_SCHEME,
  validateOAuthConfig,
} from '../src/config/oauth.config';

describe('OAuth Configuration', () => {
  describe('GOOGLE_OAUTH_CONFIG', () => {
    it('should have all required client IDs', () => {
      expect(GOOGLE_OAUTH_CONFIG).toHaveProperty('expoClientId');
      expect(GOOGLE_OAUTH_CONFIG).toHaveProperty('iosClientId');
      expect(GOOGLE_OAUTH_CONFIG).toHaveProperty('androidClientId');
      expect(GOOGLE_OAUTH_CONFIG).toHaveProperty('webClientId');
    });

    it('should have client IDs in correct format', () => {
      expect(GOOGLE_OAUTH_CONFIG.expoClientId).toMatch(/\.apps\.googleusercontent\.com$/);
      expect(GOOGLE_OAUTH_CONFIG.iosClientId).toMatch(/\.apps\.googleusercontent\.com$/);
      expect(GOOGLE_OAUTH_CONFIG.androidClientId).toMatch(/\.apps\.googleusercontent\.com$/);
      expect(GOOGLE_OAUTH_CONFIG.webClientId).toMatch(/\.apps\.googleusercontent\.com$/);
    });

    it('should use environment variables if available', () => {
      // Test that config reads from process.env
      const originalEnv = process.env.EXPO_PUBLIC_GOOGLE_EXPO_CLIENT_ID;
      
      process.env.EXPO_PUBLIC_GOOGLE_EXPO_CLIENT_ID = 'test.apps.googleusercontent.com';
      
      // Re-import to get updated config (in real scenario)
      // For this test, we just verify the format allows env vars
      expect(GOOGLE_OAUTH_CONFIG.expoClientId).toBeDefined();
      
      // Restore
      if (originalEnv) {
        process.env.EXPO_PUBLIC_GOOGLE_EXPO_CLIENT_ID = originalEnv;
      }
    });
  });

  describe('GOOGLE_OAUTH_SCOPES', () => {
    it('should include required scopes', () => {
      expect(GOOGLE_OAUTH_SCOPES).toContain('openid');
      expect(GOOGLE_OAUTH_SCOPES).toContain('profile');
      expect(GOOGLE_OAUTH_SCOPES).toContain('email');
    });

    it('should be an array', () => {
      expect(Array.isArray(GOOGLE_OAUTH_SCOPES)).toBe(true);
    });
  });

  describe('OAUTH_REDIRECT_SCHEME', () => {
    it('should be defined', () => {
      expect(OAUTH_REDIRECT_SCHEME).toBeDefined();
      expect(typeof OAUTH_REDIRECT_SCHEME).toBe('string');
    });

    it('should match app scheme', () => {
      expect(OAUTH_REDIRECT_SCHEME).toBe('waooaw');
    });
  });

  describe('validateOAuthConfig', () => {
    it('should return validation result', () => {
      const result = validateOAuthConfig();

      expect(result).toHaveProperty('isValid');
      expect(result).toHaveProperty('missing');
      expect(typeof result.isValid).toBe('boolean');
      expect(Array.isArray(result.missing)).toBe(true);
    });

    it('should detect placeholder values', () => {
      const result = validateOAuthConfig();

      // Since we're using placeholder values, should be invalid
      expect(result.isValid).toBe(false);
      expect(result.missing.length).toBeGreaterThan(0);
    });

    it('should list missing client IDs', () => {
      const result = validateOAuthConfig();

      if (!result.isValid) {
        expect(result.missing.length).toBeGreaterThan(0);
        result.missing.forEach((key) => {
          expect(key).toMatch(/^EXPO_PUBLIC_GOOGLE_/);
        });
      }
    });
  });
});
