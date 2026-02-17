/**
 * API Types
 * Authentication and user-related types
 * Ported from CP FrontEnd auth.service.ts
 */

/**
 * User entity
 */
export interface User {
  id: string;
  email: string;
  name?: string;
  picture?: string;
  provider: string;
  created_at: string;
}

/**
 * Token response from auth endpoint
 * Matches backend Token model (CP/PP /auth/google/verify)
 */
export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: 'bearer';
  expires_in: number; // seconds until access token expires (typically 900 = 15 minutes)
}

/**
 * Decoded JWT token payload
 * Matches backend TokenData model + JWT standard claims
 * Issuer: "waooaw.com"
 * Algorithm: HS256 (verified by backend)
 */
export interface DecodedToken {
  user_id: string;
  email: string;
  token_type: 'access' | 'refresh';
  exp: number; // Expiration timestamp (seconds since epoch)
  iat: number; // Issued at timestamp (seconds since epoch)
  roles?: string[]; // User roles (backend includes ["user"])
  iss?: string; // Issuer ("waooaw.com")
  sub?: string; // Subject (same as user_id)
}

/**
 * RFC 7807 Problem Details error response
 */
export interface ProblemDetails {
  type: string;
  title: string;
  status: number;
  detail: string;
  instance?: string;
  correlation_id?: string;
  timestamp?: string;
}

/**
 * Generic API response wrapper
 */
export interface APIResponse<T> {
  data: T;
  message?: string;
  timestamp?: string;
}

/**
 * Paginated response
 */
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
}

/**
 * Query parameters for pagination
 */
export interface PaginationParams {
  limit?: number;
  offset?: number;
}

/**
 * API request configuration
 */
export interface APIRequestConfig {
  headers?: Record<string, string>;
  params?: Record<string, any>;
  timeout?: number;
}

/**
 * API error class
 */
export class APIError extends Error {
  status: number;
  type: string;
  detail: string;
  correlationId?: string;

  constructor(problem: ProblemDetails) {
    super(problem.title);
    this.name = 'APIError';
    this.status = problem.status;
    this.type = problem.type;
    this.detail = problem.detail;
    this.correlationId = problem.correlation_id;
  }
}

/**
 * Network error class
 */
export class NetworkError extends Error {
  constructor(message: string = 'Network request failed') {
    super(message);
    this.name = 'NetworkError';
  }
}

/**
 * Timeout error class
 */
export class TimeoutError extends Error {
  constructor(message: string = 'Request timeout') {
    super(message);
    this.name = 'TimeoutError';
  }
}
