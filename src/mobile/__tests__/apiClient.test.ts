/**
 * API Client Tests
 * Tests for axios client with interceptors
 */

import MockAdapter from 'axios-mock-adapter';
import * as SecureStore from 'expo-secure-store';
import apiClient, { APIClient } from '../src/lib/apiClient';

// Mock SecureStore
jest.mock('expo-secure-store', () => ({
  getItemAsync: jest.fn(),
  setItemAsync: jest.fn(),
  deleteItemAsync: jest.fn(),
}));

describe('API Client', () => {
  let mockAxios: MockAdapter;

  beforeEach(() => {
    // Create mock adapter for the axios instance
    mockAxios = new MockAdapter(apiClient.getInstance());
    
    // Clear all mocks
    jest.clearAllMocks();
  });

  afterEach(() => {
    mockAxios.reset();
  });

  describe('Request Interceptor', () => {
    it('should add Authorization header when token exists', async () => {
      const mockToken = 'test-jwt-token';
      (SecureStore.getItemAsync as jest.Mock).mockResolvedValue(mockToken);

      mockAxios.onGet('/test').reply((config) => {
        expect(config.headers?.Authorization).toBe(`Bearer ${mockToken}`);
        return [200, { success: true }];
      });

      await apiClient.get('/test');
      
      expect(SecureStore.getItemAsync).toHaveBeenCalledWith('cp_access_token');
    });

    it('should not add Authorization header when token is null', async () => {
      (SecureStore.getItemAsync as jest.Mock).mockResolvedValue(null);

      mockAxios.onGet('/test').reply((config) => {
        expect(config.headers?.Authorization).toBeUndefined();
        return [200, { success: true }];
      });

      await apiClient.get('/test');
    });
  });

  describe('Response Interceptor', () => {
    it('should clear tokens on 401 Unauthorized', async () => {
      (SecureStore.getItemAsync as jest.Mock).mockResolvedValue('expired-token');
      (SecureStore.deleteItemAsync as jest.Mock).mockResolvedValue(undefined);

      mockAxios.onGet('/protected').reply(401, {
        type: 'unauthorized',
        title: 'Unauthorized',
        status: 401,
        detail: 'Token expired',
      });

      try {
        await apiClient.get('/protected');
      } catch (error) {
        // Expected to fail
      }

      // Should have attempted to clear tokens
      expect(SecureStore.deleteItemAsync).toHaveBeenCalled();
    });

    it('should return response data on success', async () => {
      const responseData = { id: '123', name: 'Test Agent' };
      
      mockAxios.onGet('/agents/123').reply(200, responseData);

      const response = await apiClient.get('/agents/123');
      
      expect(response.status).toBe(200);
      expect(response.data).toEqual(responseData);
    });
  });

  describe('HTTP Methods', () => {
    beforeEach(() => {
      (SecureStore.getItemAsync as jest.Mock).mockResolvedValue('test-token');
    });

    it('should perform GET request', async () => {
      mockAxios.onGet('/agents').reply(200, { items: [] });

      const response = await apiClient.get('/agents');
      
      expect(response.status).toBe(200);
      expect(response.data).toEqual({ items: [] });
    });

    it('should perform POST request', async () => {
      const postData = { name: 'New Agent' };
      mockAxios.onPost('/agents', postData).reply(201, { id: '123', ...postData });

      const response = await apiClient.post('/agents', postData);
      
      expect(response.status).toBe(201);
      expect(response.data.id).toBe('123');
    });

    it('should perform PUT request', async () => {
      const putData = { name: 'Updated Agent' };
      mockAxios.onPut('/agents/123', putData).reply(200, { id: '123', ...putData });

      const response = await apiClient.put('/agents/123', putData);
      
      expect(response.status).toBe(200);
      expect(response.data.name).toBe('Updated Agent');
    });

    it('should perform PATCH request', async () => {
      const patchData = { name: 'Patched Agent' };
      mockAxios.onPatch('/agents/123', patchData).reply(200, { id: '123', ...patchData });

      const response = await apiClient.patch('/agents/123', patchData);
      
      expect(response.status).toBe(200);
    });

    it('should perform DELETE request', async () => {
      mockAxios.onDelete('/agents/123').reply(204);

      const response = await apiClient.delete('/agents/123');
      
      expect(response.status).toBe(204);
    });
  });

  describe('Token Management', () => {
    it('should set access token', async () => {
      (SecureStore.setItemAsync as jest.Mock).mockResolvedValue(undefined);

      await apiClient.setAccessToken('new-token');
      
      expect(SecureStore.setItemAsync).toHaveBeenCalledWith('cp_access_token', 'new-token');
    });

    it('should clear all tokens', async () => {
      (SecureStore.deleteItemAsync as jest.Mock).mockResolvedValue(undefined);

      await apiClient.clearTokens();
      
      expect(SecureStore.deleteItemAsync).toHaveBeenCalledTimes(3);
      expect(SecureStore.deleteItemAsync).toHaveBeenCalledWith('cp_access_token');
      expect(SecureStore.deleteItemAsync).toHaveBeenCalledWith('cp_refresh_token');
      expect(SecureStore.deleteItemAsync).toHaveBeenCalledWith('token_expires_at');
    });
  });

  describe('Error Handling', () => {
    it('should handle network errors', async () => {
      mockAxios.onGet('/test').networkError();

      await expect(apiClient.get('/test')).rejects.toThrow();
    });

    it('should handle timeout errors', async () => {
      mockAxios.onGet('/test').timeout();

      await expect(apiClient.get('/test')).rejects.toThrow();
    });

    it('should reject promise on API error', async () => {
      mockAxios.onGet('/test').reply(500, {
        type: 'server-error',
        title: 'Server Error',
        status: 500,
        detail: 'Internal error',
      });

      await expect(apiClient.get('/test')).rejects.toThrow();
    });
  });
});
