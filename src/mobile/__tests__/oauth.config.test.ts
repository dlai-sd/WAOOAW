/**
 * OAuth Configuration Tests
 */

const loadOAuthConfigModule = () => {
  jest.resetModules();
  // eslint-disable-next-line @typescript-eslint/no-var-requires
  return require('../src/config/oauth.config');
};

describe('OAuth Configuration', () => {
  const originalEnv = { ...process.env };

  afterEach(() => {
    process.env = { ...originalEnv };
  });

  describe('GOOGLE_OAUTH_CONFIG', () => {
    it('should have all required client IDs', () => {
      process.env.EXPO_PUBLIC_GOOGLE_EXPO_CLIENT_ID = 'test-expo.apps.googleusercontent.com';
      process.env.EXPO_PUBLIC_GOOGLE_IOS_CLIENT_ID = 'test-ios.apps.googleusercontent.com';
      process.env.EXPO_PUBLIC_GOOGLE_ANDROID_CLIENT_ID = 'test-android.apps.googleusercontent.com';
      process.env.EXPO_PUBLIC_GOOGLE_WEB_CLIENT_ID = 'test-web.apps.googleusercontent.com';

      const { GOOGLE_OAUTH_CONFIG } = loadOAuthConfigModule();

      expect(GOOGLE_OAUTH_CONFIG).toHaveProperty('expoClientId');
      expect(GOOGLE_OAUTH_CONFIG).toHaveProperty('iosClientId');
      expect(GOOGLE_OAUTH_CONFIG).toHaveProperty('androidClientId');
      expect(GOOGLE_OAUTH_CONFIG).toHaveProperty('webClientId');
    });

    it('should have client IDs in correct format', () => {
      process.env.EXPO_PUBLIC_GOOGLE_EXPO_CLIENT_ID = 'test-expo.apps.googleusercontent.com';
      process.env.EXPO_PUBLIC_GOOGLE_IOS_CLIENT_ID = 'test-ios.apps.googleusercontent.com';
      process.env.EXPO_PUBLIC_GOOGLE_ANDROID_CLIENT_ID = 'test-android.apps.googleusercontent.com';
      process.env.EXPO_PUBLIC_GOOGLE_WEB_CLIENT_ID = 'test-web.apps.googleusercontent.com';

      const { GOOGLE_OAUTH_CONFIG } = loadOAuthConfigModule();

      expect(GOOGLE_OAUTH_CONFIG.expoClientId).toMatch(/\.apps\.googleusercontent\.com$/);
      expect(GOOGLE_OAUTH_CONFIG.iosClientId).toMatch(/\.apps\.googleusercontent\.com$/);
      expect(GOOGLE_OAUTH_CONFIG.androidClientId).toMatch(/\.apps\.googleusercontent\.com$/);
      expect(GOOGLE_OAUTH_CONFIG.webClientId).toMatch(/\.apps\.googleusercontent\.com$/);
    });

    it('should use environment variables if available', () => {
      process.env.EXPO_PUBLIC_GOOGLE_EXPO_CLIENT_ID = 'test.apps.googleusercontent.com';
      const { GOOGLE_OAUTH_CONFIG } = loadOAuthConfigModule();
      expect(GOOGLE_OAUTH_CONFIG.expoClientId).toBe('test.apps.googleusercontent.com');
    });
  });

  describe('GOOGLE_OAUTH_SCOPES', () => {
    it('should include required scopes', () => {
      const { GOOGLE_OAUTH_SCOPES } = loadOAuthConfigModule();
      expect(GOOGLE_OAUTH_SCOPES).toContain('openid');
      expect(GOOGLE_OAUTH_SCOPES).toContain('profile');
      expect(GOOGLE_OAUTH_SCOPES).toContain('email');
    });

    it('should be an array', () => {
      const { GOOGLE_OAUTH_SCOPES } = loadOAuthConfigModule();
      expect(Array.isArray(GOOGLE_OAUTH_SCOPES)).toBe(true);
    });
  });

  describe('OAUTH_REDIRECT_SCHEME', () => {
    it('should be defined', () => {
      const { OAUTH_REDIRECT_SCHEME } = loadOAuthConfigModule();
      expect(OAUTH_REDIRECT_SCHEME).toBeDefined();
      expect(typeof OAUTH_REDIRECT_SCHEME).toBe('string');
    });

    it('should match app scheme', () => {
      const { OAUTH_REDIRECT_SCHEME } = loadOAuthConfigModule();
      expect(OAUTH_REDIRECT_SCHEME).toBe('waooaw');
    });
  });

  describe('validateOAuthConfig', () => {
    it('should return validation result', () => {
      const { validateOAuthConfig } = loadOAuthConfigModule();
      const result = validateOAuthConfig();

      expect(result).toHaveProperty('isValid');
      expect(result).toHaveProperty('missing');
      expect(typeof result.isValid).toBe('boolean');
      expect(Array.isArray(result.missing)).toBe(true);
    });

    it('should be invalid when web client ID is missing', () => {
      delete process.env.EXPO_PUBLIC_GOOGLE_WEB_CLIENT_ID;
      const { validateOAuthConfig } = loadOAuthConfigModule();
      const result = validateOAuthConfig();

      expect(result.isValid).toBe(false);
      expect(result.missing).toContain('EXPO_PUBLIC_GOOGLE_WEB_CLIENT_ID');
    });

    it('should be valid when web client ID is present', () => {
      process.env.EXPO_PUBLIC_GOOGLE_WEB_CLIENT_ID = 'test-web.apps.googleusercontent.com';
      const { validateOAuthConfig } = loadOAuthConfigModule();
      const result = validateOAuthConfig();

      expect(result.isValid).toBe(true);
      expect(result.missing).toHaveLength(0);
    });

    it('should list missing client IDs', () => {
      delete process.env.EXPO_PUBLIC_GOOGLE_WEB_CLIENT_ID;
      const { validateOAuthConfig } = loadOAuthConfigModule();
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
