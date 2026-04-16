/**
 * API Client
 * Axios instance configured with interceptors for authentication and error handling.
 *
 * NFR compliance:
 *  - Every request carries a unique X-Correlation-ID so backend traces can be
 *    matched to client-side logs and crash reports.
 *  - Dev-mode request logging never prints the request body (PII risk).
 *  - Retryable errors (429, 5xx, network drop) are retried up to 3 times with
 *    exponential back-off + jitter before surfacing to the caller.
 *  - 401 responses trigger a silent token refresh (via refresh token) before
 *    propagating the error. Tokens are only cleared when the refresh itself
 *    fails, preventing post-login token wipe from unrelated 401s (e.g. the
 *    FCM registration-key check on /api/v1/customers/fcm-token).
 */

import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse, AxiosError } from 'axios';
import { getAPIConfig } from '../config/api.config';
import { handleAPIError, logError } from './errorHandler';
import secureStorage from './secureStorage';

// ---------------------------------------------------------------------------
// Token-response shape expected from /auth/refresh
// ---------------------------------------------------------------------------
interface RefreshTokenResponse {
  access_token: string;
  refresh_token?: string;
  token_type: string;
  expires_in: number;
}

// ---------------------------------------------------------------------------
// Correlation ID — RFC 4122 UUID v4, generated per-request
// ---------------------------------------------------------------------------
function generateCorrelationId(): string {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === 'x' ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

// ---------------------------------------------------------------------------
// Retry policy — only for transient/server-side errors
// ---------------------------------------------------------------------------
const RETRYABLE_STATUSES = new Set([429, 500, 502, 503, 504]);
const MAX_RETRIES = 3;

type RetryableConfig = AxiosRequestConfig & { _retry?: boolean; _retryCount?: number };

/**
 * Create axios instance with base configuration
 */
function createAxiosInstance(): AxiosInstance {
  const config = getAPIConfig();

  const instance = axios.create({
    baseURL: config.apiBaseUrl,
    timeout: config.timeout,
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
    },
  });

  return instance;
}

/**
 * API Client class with interceptors
 */
class APIClient {
  private axiosInstance: AxiosInstance;
  private isRefreshing = false;
  private refreshSubscribers: ((token: string) => void)[] = [];

  constructor() {
    this.axiosInstance = createAxiosInstance();
    this.setupInterceptors();
  }

  /**
   * Setup request and response interceptors
   */
  private setupInterceptors(): void {
    // Request interceptor - add Authorization header + Correlation ID
    this.axiosInstance.interceptors.request.use(
      async (config) => {
        let token = await this.getAccessToken();

        // Proactively refresh if the token expires within 60 seconds.
        if (token) {
          const isAboutToExpire = await secureStorage.isTokenExpired(60);
          if (isAboutToExpire && !this.isRefreshing) {
            const refreshed = await this.refreshAuthToken();
            if (refreshed) {
              token = refreshed;
            }
          }
        }

        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }

        // NFR: propagate a unique correlation ID so every backend log entry
        // for this request carries the same ID as the client trace.
        config.headers['X-Correlation-ID'] = generateCorrelationId();

        // NFR: log method + URL only — never log request body or params
        // (may contain email, phone, registration data).
        if (__DEV__) {
          console.log(`[API] ${config.method?.toUpperCase()} ${config.url}`);
        }

        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Response interceptor - handle errors, token refresh, and retry
    this.axiosInstance.interceptors.response.use(
      (response) => {
        // NFR: log status only — never log response body (may contain PII).
        if (__DEV__) {
          console.log(`[API] ${response.status} ${response.config.url}`);
        }
        return response;
      },
      async (error: AxiosError) => {
        const originalRequest = error.config as RetryableConfig;

        // NFR: retry transient server errors and network drops with
        // exponential back-off (1s, 2s, 4s) + up to 500ms random jitter.
        const status = error.response?.status ?? 0;
        const isNetworkDrop = !error.response && error.code !== 'ERR_CANCELED';
        const isRetryable = RETRYABLE_STATUSES.has(status) || isNetworkDrop;
        const retryCount = originalRequest._retryCount ?? 0;

        if (isRetryable && retryCount < MAX_RETRIES) {
          originalRequest._retryCount = retryCount + 1;
          const backoff = Math.min(1000 * Math.pow(2, retryCount), 10000);
          const jitter = Math.random() * 500;
          if (__DEV__) {
            console.log(
              `[API] Retry ${originalRequest._retryCount}/${MAX_RETRIES} ` +
              `for ${originalRequest.url} after ${Math.round(backoff + jitter)}ms`
            );
          }
          await new Promise((resolve) => setTimeout(resolve, backoff + jitter));
          return this.axiosInstance(originalRequest);
        }

        // Handle 401 Unauthorized — attempt silent token refresh before giving up.
        // IMPORTANT: do NOT wipe tokens here. An unrelated 401 (e.g. missing
        // X-CP-Registration-Key on /api/v1/customers/fcm-token) would otherwise
        // destroy the session token and break every subsequent authenticated request.
        if (status === 401 && !originalRequest._retry) {
          originalRequest._retry = true;

          if (!this.isRefreshing) {
            this.isRefreshing = true;
            let newToken: string | null = null;

            try {
              newToken = await this.refreshAuthToken();
            } catch {
              // refreshAuthToken already cleared tokens on failure
            }

            this.isRefreshing = false;

            if (newToken) {
              // Replay all queued requests with the fresh token.
              this.refreshSubscribers.forEach((cb) => cb(newToken!));
              this.refreshSubscribers = [];
              // Retry the original request.
              if (originalRequest.headers) {
                originalRequest.headers['Authorization'] = `Bearer ${newToken}`;
              }
              return this.axiosInstance(originalRequest);
            } else {
              // Refresh failed — signal all queued requests to fail.
              this.refreshSubscribers.forEach((cb) => cb(''));
              this.refreshSubscribers = [];
              // Fall through to propagate the error.
            }
          } else {
            // Another refresh is already in flight — queue this retry.
            return new Promise<AxiosResponse>((resolve, reject) => {
              this.refreshSubscribers.push((token: string) => {
                if (token && originalRequest.headers) {
                  originalRequest.headers['Authorization'] = `Bearer ${token}`;
                  resolve(this.axiosInstance(originalRequest));
                } else {
                  reject(error);
                }
              });
            });
          }
        }

        // Handle and log error
        const handledError = handleAPIError(error);
        logError(handledError, 'APIClient');

        return Promise.reject(error);
      }
    );
  }

  /**
   * Get access token from secure storage
   */
  private async getAccessToken(): Promise<string | null> {
    try {
      return await secureStorage.getAccessToken();
    } catch (error) {
      console.error('[APIClient] Failed to get access token:', error);
      return null;
    }
  }

  /**
   * Silently refresh the access token using the stored refresh token.
   * Uses a raw axios call (no interceptors) to avoid circular 401 handling.
   * Clears all tokens and returns null when the refresh endpoint itself fails.
   */
  private async refreshAuthToken(): Promise<string | null> {
    try {
      const refreshToken = await secureStorage.getRefreshToken();
      if (!refreshToken) {
        await this.clearTokens();
        return null;
      }

      const config = getAPIConfig();
      const response = await axios.post<RefreshTokenResponse>(
        `${config.apiBaseUrl}/auth/refresh`,
        { refresh_token: refreshToken },
        {
          headers: { 'Content-Type': 'application/json' },
          timeout: config.timeout,
        }
      );

      const { access_token, refresh_token, expires_in } = response.data;

      await secureStorage.setTokens({
        accessToken: access_token,
        refreshToken: refresh_token ?? refreshToken,
        expiresAt: Math.floor(Date.now() / 1000) + expires_in,
      });

      if (__DEV__) {
        console.log('[APIClient] Token refreshed successfully');
      }

      return access_token;
    } catch (err) {
      if (__DEV__) {
        console.warn('[APIClient] Silent token refresh failed — clearing session', err);
      }
      await this.clearTokens();
      return null;
    }
  }

  /**
   * Store access token in secure storage
   */
  async setAccessToken(token: string): Promise<void> {
    try {
      await secureStorage.setAccessToken(token);
    } catch (error) {
      console.error('[APIClient] Failed to set access token:', error);
      throw error;
    }
  }

  /**
   * Remove tokens from secure storage
   */
  async clearTokens(): Promise<void> {
    try {
      await secureStorage.clearTokens();
    } catch (error) {
      console.error('[APIClient] Failed to clear tokens:', error);
    }
  }

  /**
   * Get axios instance
   */
  getInstance(): AxiosInstance {
    return this.axiosInstance;
  }

  /**
   * Generic GET request
   */
  async get<T = any>(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return this.axiosInstance.get<T>(url, config);
  }

  /**
   * Generic POST request
   */
  async post<T = any>(
    url: string,
    data?: any,
    config?: AxiosRequestConfig
  ): Promise<AxiosResponse<T>> {
    return this.axiosInstance.post<T>(url, data, config);
  }

  /**
   * Generic PUT request
   */
  async put<T = any>(
    url: string,
    data?: any,
    config?: AxiosRequestConfig
  ): Promise<AxiosResponse<T>> {
    return this.axiosInstance.put<T>(url, data, config);
  }

  /**
   * Generic PATCH request
   */
  async patch<T = any>(
    url: string,
    data?: any,
    config?: AxiosRequestConfig
  ): Promise<AxiosResponse<T>> {
    return this.axiosInstance.patch<T>(url, data, config);
  }

  /**
   * Generic DELETE request
   */
  async delete<T = any>(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return this.axiosInstance.delete<T>(url, config);
  }
}

/**
 * Singleton instance
 */
const apiClient = new APIClient();

/**
 * Export singleton instance
 */
export default apiClient;

/**
 * Export class for testing
 */
export { APIClient };
