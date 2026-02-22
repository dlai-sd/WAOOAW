/**
 * API Client
 * Axios instance configured with interceptors for authentication and error handling
 */

import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse, AxiosError } from 'axios';
import { getAPIConfig } from '../config/api.config';
import { handleAPIError, logError } from './errorHandler';
import secureStorage from './secureStorage';

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
    // Request interceptor - add Authorization header
    this.axiosInstance.interceptors.request.use(
      async (config) => {
        const token = await this.getAccessToken();
        
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }

        // Log request in development
        if (__DEV__) {
          console.log(`[API] ${config.method?.toUpperCase()} ${config.url}`, {
            params: config.params,
            data: config.data,
          });
        }

        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Response interceptor - handle errors and token refresh
    this.axiosInstance.interceptors.response.use(
      (response) => {
        // Log successful response in development
        if (__DEV__) {
          console.log(`[API] Response ${response.config.url}`, {
            status: response.status,
            data: response.data,
          });
        }
        return response;
      },
      async (error: AxiosError) => {
        const originalRequest = error.config as AxiosRequestConfig & { _retry?: boolean };

        // Handle 401 Unauthorized
        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true;

          try {
            // Clear expired token
            await this.clearTokens();
            
            // TODO: Trigger navigation to login screen
            // This will be handled by AuthContext in Story 1.8
            
            // Note: Refresh token flow not implemented yet
            // Will be added in Story 1.7 (JWT Token Management)
            
          } catch (refreshError) {
            // Refresh failed, clear all tokens and redirect to login
            await this.clearTokens();
            return Promise.reject(refreshError);
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
