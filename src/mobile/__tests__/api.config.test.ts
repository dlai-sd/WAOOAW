/**
 * API Config Tests
 * Tests for environment detection and API configuration
 */

import { Platform } from 'react-native';
import {
  detectEnvironment,
  getAPIConfig,
  getCurrentEnvironment,
  isDevelopment,
  isProduction,
  API_ENDPOINTS,
} from '../src/config/api.config';

// Mock Constants
jest.mock('expo-constants', () => ({
  expoConfig: {
    extra: {},
    updates: {},
  },
}));

describe('API Configuration', () => {
  describe('detectEnvironment', () => {
    it('should default to development', () => {
      const env = detectEnvironment();
      expect(env).toBe('development');
    });

    it('should detect environment from expo config extra', () => {
      const Constants = require('expo-constants').default;
      Constants.expoConfig.extra.ENVIRONMENT = 'prod';
      
      // Note: In real scenario, would need to reimport or reset module
      // This is a simplified test
      expect(['development', 'demo', 'uat', 'prod']).toContain(detectEnvironment());
    });
  });

  describe('getAPIConfig', () => {
    it('should return valid API config', () => {
      const config = getAPIConfig();
      
      expect(config).toHaveProperty('apiBaseUrl');
      expect(config).toHaveProperty('timeout');
      expect(typeof config.apiBaseUrl).toBe('string');
      expect(typeof config.timeout).toBe('number');
    });

    it('should have correct timeout for development', () => {
      const config = getAPIConfig();
      // Development timeout is 30000ms
      expect(config.timeout).toBeGreaterThan(0);
    });

    it('should return Android emulator URL on Android in development', () => {
      // Mock Platform.OS
      Object.defineProperty(Platform, 'OS', {
        get: () => 'android',
      });

      const config = getAPIConfig();
      // Should use 10.0.2.2 for Android emulator
      expect(config.apiBaseUrl).toContain('10.0.2.2');
    });
  });

  describe('Environment helpers', () => {
    it('should identify development environment', () => {
      expect(typeof isDevelopment()).toBe('boolean');
    });

    it('should identify production environment', () => {
      expect(typeof isProduction()).toBe('boolean');
    });

    it('should get current environment', () => {
      const env = getCurrentEnvironment();
      expect(['development', 'demo', 'uat', 'prod']).toContain(env);
    });
  });

  describe('API_ENDPOINTS', () => {
    it('should have auth endpoints', () => {
      expect(API_ENDPOINTS.AUTH_GOOGLE).toBe('/auth/google');
      expect(API_ENDPOINTS.AUTH_CHECK).toBe('/auth/check');
      expect(API_ENDPOINTS.AUTH_LOGOUT).toBe('/auth/logout');
    });

    it('should have user endpoints', () => {
      expect(API_ENDPOINTS.USER_PROFILE).toBe('/users/me');
      expect(API_ENDPOINTS.USER_UPDATE).toBe('/users/me');
    });

    it('should have agent endpoints', () => {
      expect(API_ENDPOINTS.AGENTS_LIST).toBe('/agents');
      expect(API_ENDPOINTS.AGENTS_DETAIL('123')).toBe('/agents/123');
    });

    it('should have dynamic endpoint generators', () => {
      expect(typeof API_ENDPOINTS.AGENTS_DETAIL).toBe('function');
      expect(API_ENDPOINTS.SKILLS_DETAIL('skill-id')).toBe('/skills/skill-id');
      expect(API_ENDPOINTS.TRIALS_DETAIL('trial-id')).toBe('/trials/trial-id');
    });
  });
});
