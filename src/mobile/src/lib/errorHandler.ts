/**
 * API Error Handler
 * Centralized error handling for API requests
 */

import { AxiosError } from 'axios';
import {
  APIError,
  NetworkError,
  TimeoutError,
  ProblemDetails,
} from '../types/api.types';

/**
 * Error severity levels
 */
export type ErrorSeverity = 'info' | 'warning' | 'error' | 'critical';

/**
 * Handled error result
 */
export interface HandledError {
  message: string;
  severity: ErrorSeverity;
  originalError: Error;
  shouldRetry: boolean;
  userMessage: string;
}

/**
 * Check if error is an Axios error
 */
function isAxiosError(error: unknown): error is AxiosError {
  return (error as AxiosError).isAxiosError === true;
}

/**
 * Check if error response is Problem Details format
 */
function isProblemDetails(data: unknown): data is ProblemDetails {
  return (
    typeof data === 'object' &&
    data !== null &&
    'type' in data &&
    'title' in data &&
    'status' in data &&
    'detail' in data
  );
}

/**
 * Handle API errors with RFC 7807 Problem Details support
 */
export function handleAPIError(error: unknown): HandledError {
  // Network/timeout errors
  if (error instanceof Error && error.message.includes('Network request failed')) {
    return {
      message: 'Network connection failed',
      severity: 'error',
      originalError: new NetworkError(),
      shouldRetry: true,
      userMessage: 'Unable to connect to server. Please check your internet connection.',
    };
  }

  if (error instanceof Error && error.message.includes('timeout')) {
    return {
      message: 'Request timeout',
      severity: 'warning',
      originalError: new TimeoutError(),
      shouldRetry: true,
      userMessage: 'Request took too long. Please try again.',
    };
  }

  // Axios errors
  if (isAxiosError(error)) {
    const status = error.response?.status;
    const data = error.response?.data;

    // RFC 7807 Problem Details
    if (isProblemDetails(data)) {
      const apiError = new APIError(data);
      return handleStatusCode(status || 500, apiError, data.detail);
    }

    // Generic status code handling
    return handleStatusCode(
      status || 500,
      error,
      error.message || 'An error occurred'
    );
  }

  // Unknown errors
  if (error instanceof Error) {
    return {
      message: error.message,
      severity: 'error',
      originalError: error,
      shouldRetry: false,
      userMessage: 'An unexpected error occurred. Please try again.',
    };
  }

  // Fallback
  return {
    message: 'Unknown error',
    severity: 'error',
    originalError: new Error(String(error)),
    shouldRetry: false,
    userMessage: 'Something went wrong. Please try again.',
  };
}

/**
 * Handle specific HTTP status codes
 */
function handleStatusCode(
  status: number,
  error: Error,
  detail: string
): HandledError {
  switch (status) {
    case 400:
      return {
        message: `Bad Request: ${detail}`,
        severity: 'warning',
        originalError: error,
        shouldRetry: false,
        userMessage: detail || 'Invalid request. Please check your input.',
      };

    case 401:
      return {
        message: 'Unauthorized - token expired or invalid',
        severity: 'warning',
        originalError: error,
        shouldRetry: false,
        userMessage: 'Your session has expired. Please sign in again.',
      };

    case 403:
      return {
        message: 'Forbidden - insufficient permissions',
        severity: 'warning',
        originalError: error,
        shouldRetry: false,
        userMessage: 'You do not have permission to access this resource.',
      };

    case 404:
      return {
        message: `Not Found: ${detail}`,
        severity: 'info',
        originalError: error,
        shouldRetry: false,
        userMessage: 'The requested resource was not found.',
      };

    case 409:
      return {
        message: `Conflict: ${detail}`,
        severity: 'warning',
        originalError: error,
        shouldRetry: false,
        userMessage: detail || 'A conflict occurred. Please try again.',
      };

    case 422:
      return {
        message: `Validation Error: ${detail}`,
        severity: 'warning',
        originalError: error,
        shouldRetry: false,
        userMessage: detail || 'Validation failed. Please check your input.',
      };

    case 429:
      return {
        message: 'Too Many Requests - rate limit exceeded',
        severity: 'warning',
        originalError: error,
        shouldRetry: true,
        userMessage: 'Too many requests. Please wait a moment and try again.',
      };

    case 500:
      return {
        message: 'Internal Server Error',
        severity: 'error',
        originalError: error,
        shouldRetry: true,
        userMessage: 'Server error occurred. Please try again later.',
      };

    case 502:
    case 503:
    case 504:
      return {
        message: 'Service Unavailable',
        severity: 'error',
        originalError: error,
        shouldRetry: true,
        userMessage: 'Service is temporarily unavailable. Please try again later.',
      };

    default:
      return {
        message: `HTTP ${status}: ${detail}`,
        severity: status >= 500 ? 'error' : 'warning',
        originalError: error,
        shouldRetry: status >= 500,
        userMessage: detail || 'An error occurred. Please try again.',
      };
  }
}

/**
 * Log error to console (development) or analytics (production)
 */
export function logError(error: HandledError, context?: string): void {
  const prefix = context ? `[${context}]` : '[API Error]';
  
  if (__DEV__) {
    console.error(prefix, {
      message: error.message,
      severity: error.severity,
      shouldRetry: error.shouldRetry,
      userMessage: error.userMessage,
      originalError: error.originalError,
    });
  } else {
    // In production, send to analytics/monitoring service
    // Example: Sentry, Firebase Crashlytics, etc.
    console.warn(prefix, error.message);
  }
}

/**
 * Get user-friendly error message
 */
export function getUserMessage(error: unknown): string {
  const handled = handleAPIError(error);
  return handled.userMessage;
}

/**
 * Check if error should trigger retry
 */
export function shouldRetry(error: unknown): boolean {
  const handled = handleAPIError(error);
  return handled.shouldRetry;
}
