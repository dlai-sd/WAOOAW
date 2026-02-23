/**
 * Integration Test: API Configuration
 * 
 * Validates that API client is correctly configured and can reach backend.
 * Would have caught the wrong API URL issue.
 */

import { apiConfig } from '../../src/config/api.config';
import axios from 'axios';

describe('API Configuration Integration', () => {
  /**
   * CRITICAL: API URL must be Customer Portal
   */
  it('should point to Customer Portal URL', () => {
    expect(apiConfig.baseURL).toBe('https://cp.demo.waooaw.com');
  });

  /**
   * Verify environment variable reading
   */
  it('should read EXPO_PUBLIC_API_URL from environment', () => {
    // In production builds, this should be set via eas.json env
    const envUrl = process.env.EXPO_PUBLIC_API_URL;
    if (envUrl) {
      expect(apiConfig.baseURL).toBe(envUrl);
    }
  });

  /**
   * Verify API client can be created
   */
  it('should create axios client with correct config', () => {
    const client = axios.create(apiConfig);
    expect(client.defaults.baseURL).toBe('https://cp.demo.waooaw.com');
    expect(client.defaults.timeout).toBe(30000);
  });

  /**
   * Verify API health check endpoint (if available)
   */
  it('should reach API health endpoint', async () => {
    const client = axios.create(apiConfig);
    
    try {
      // Try health check (may not exist, that's okay)
      const response = await client.get('/health');
      expect(response.status).toBe(200);
    } catch (error) {
      // If health endpoint doesn't exist, at least we should get a network response
      // (not a network error like ERR_CONNECTION_REFUSED)
      if (error.code === 'ECONNREFUSED' || error.code === 'ENOTFOUND') {
        fail('API server not reachable - check URL configuration');
      }
      // 404 or other HTTP errors are acceptable (endpoint may not exist)
    }
  }, 10000);

  /**
   * Verify timeout configuration
   */
  it('should have reasonable timeout (30s)', () => {
    expect(apiConfig.timeout).toBe(30000);
  });

  /**
   * Verify headers configuration
   */
  it('should have correct default headers', () => {
    expect(apiConfig.headers['Content-Type']).toBe('application/json');
  });
});
