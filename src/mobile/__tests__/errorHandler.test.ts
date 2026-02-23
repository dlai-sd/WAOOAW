/**
 * Error Handler Tests
 * Tests for API error handling utilities
 */

import { AxiosError } from 'axios';
import {
  handleAPIError,
  getUserMessage,
  shouldRetry,
  logError,
} from '../src/lib/errorHandler';
import { APIError, NetworkError, TimeoutError } from '../src/types/api.types';

describe('Error Handler', () => {
  describe('handleAPIError', () => {
    it('should handle network errors', () => {
      const error = new Error('Network request failed');
      const handled = handleAPIError(error);

      expect(handled.severity).toBe('error');
      expect(handled.shouldRetry).toBe(true);
      expect(handled.originalError).toBeInstanceOf(NetworkError);
      expect(handled.userMessage).toContain('internet connection');
    });

    it('should handle timeout errors', () => {
      const error = new Error('timeout of 10000ms exceeded');
      const handled = handleAPIError(error);

      expect(handled.severity).toBe('warning');
      expect(handled.shouldRetry).toBe(true);
      expect(handled.originalError).toBeInstanceOf(TimeoutError);
      expect(handled.userMessage).toContain('try again');
    });

    it('should handle 401 Unauthorized', () => {
      const axiosError = {
        isAxiosError: true,
        response: {
          status: 401,
          data: {
            type: 'https://problems.waooaw.com/unauthorized',
            title: 'Unauthorized',
            status: 401,
            detail: 'Token expired',
          },
        },
        message: 'Request failed with status code 401',
      } as AxiosError;

      const handled = handleAPIError(axiosError);

      expect(handled.severity).toBe('warning');
      expect(handled.shouldRetry).toBe(false);
      expect(handled.userMessage).toContain('sign in again');
    });

    it('should handle 404 Not Found', () => {
      const axiosError = {
        isAxiosError: true,
        response: {
          status: 404,
          data: {
            type: 'https://problems.waooaw.com/not-found',
            title: 'Not Found',
            status: 404,
            detail: 'Agent not found',
          },
        },
        message: 'Request failed with status code 404',
      } as AxiosError;

      const handled = handleAPIError(axiosError);

      expect(handled.severity).toBe('info');
      expect(handled.shouldRetry).toBe(false);
      expect(handled.userMessage).toContain('not found');
    });

    it('should handle 500 Internal Server Error', () => {
      const axiosError = {
        isAxiosError: true,
        response: {
          status: 500,
          data: {
            type: 'https://problems.waooaw.com/internal-error',
            title: 'Internal Server Error',
            status: 500,
            detail: 'Database connection failed',
          },
        },
        message: 'Request failed with status code 500',
      } as AxiosError;

      const handled = handleAPIError(axiosError);

      expect(handled.severity).toBe('error');
      expect(handled.shouldRetry).toBe(true);
      expect(handled.userMessage).toContain('try again later');
    });

    it('should handle 429 Rate Limit', () => {
      const axiosError = {
        isAxiosError: true,
        response: {
          status: 429,
          data: {
            type: 'https://problems.waooaw.com/rate-limit',
            title: 'Too Many Requests',
            status: 429,
            detail: 'Rate limit exceeded',
          },
        },
        message: 'Request failed with status code 429',
      } as AxiosError;

      const handled = handleAPIError(axiosError);

      expect(handled.severity).toBe('warning');
      expect(handled.shouldRetry).toBe(true);
      expect(handled.userMessage).toContain('Too many requests');
    });

    it('should handle unknown errors', () => {
      const error = new Error('Something went wrong');
      const handled = handleAPIError(error);

      expect(handled.severity).toBe('error');
      expect(handled.originalError).toBeInstanceOf(Error);
      expect(handled.userMessage).toContain('unexpected error');
    });
  });

  describe('getUserMessage', () => {
    it('should extract user-friendly message', () => {
      const error = new Error('Network request failed');
      const message = getUserMessage(error);

      expect(typeof message).toBe('string');
      expect(message.length).toBeGreaterThan(0);
      expect(message).toContain('internet connection');
    });
  });

  describe('shouldRetry', () => {
    it('should recommend retry for network errors', () => {
      const error = new Error('Network request failed');
      expect(shouldRetry(error)).toBe(true);
    });

    it('should not recommend retry for 401 errors', () => {
      const axiosError = {
        isAxiosError: true,
        response: {
          status: 401,
          data: { title: 'Unauthorized', status: 401, type: '', detail: '' },
        },
      } as AxiosError;

      expect(shouldRetry(axiosError)).toBe(false);
    });

    it('should recommend retry for 500 errors', () => {
      const axiosError = {
        isAxiosError: true,
        response: {
          status: 500,
          data: { title: 'Server Error', status: 500, type: '', detail: '' },
        },
      } as AxiosError;

      expect(shouldRetry(axiosError)).toBe(true);
    });
  });

  describe('logError', () => {
    it('should log error without throwing', () => {
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation();
      
      const error = new Error('Test error');
      const handled = handleAPIError(error);
      
      expect(() => logError(handled, 'TestContext')).not.toThrow();
      
      consoleSpy.mockRestore();
    });
  });
});
