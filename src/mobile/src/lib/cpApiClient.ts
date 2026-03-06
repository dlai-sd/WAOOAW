/**
 * CP API Client
 *
 * Lightweight Axios instance targeting the CP Backend (separate service from Plant Gateway).
 * Used by screens that call CP-specific routes like PATCH /api/cp/profile.
 *
 * Base URL per environment:
 *   development  http://localhost:8020/api  (iOS) | http://10.0.2.2:8020/api (Android)
 *   demo         https://cp.demo.waooaw.com/api
 *   uat          https://cp.uat.waooaw.com/api
 *   prod         https://cp.waooaw.com/api
 *
 * NFR compliance:
 *  - Bearer token injected from secureStorage on every request
 *  - X-Correlation-ID propagated (platform NFR)
 *  - Dev-mode logging: method + URL only (never body — PII risk)
 */

import axios, { AxiosInstance, InternalAxiosRequestConfig } from 'axios';
import { getAPIConfig } from '../config/api.config';
import secureStorage from './secureStorage';

function generateCorrelationId(): string {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === 'x' ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

function createCpAxiosInstance(): AxiosInstance {
  const { cpApiBaseUrl, timeout } = getAPIConfig();

  const instance = axios.create({
    baseURL: cpApiBaseUrl,
    timeout,
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
    },
  });

  // Request interceptor — auth + correlation
  instance.interceptors.request.use(async (config) => {
    try {
      const token = await secureStorage.getAccessToken();
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    } catch {
      // If secure storage fails, proceed unauthenticated (backend will 401)
    }

    config.headers['X-Correlation-ID'] = generateCorrelationId();

    if (__DEV__) {
      // eslint-disable-next-line no-console
      console.log(`[CP API] ${config.method?.toUpperCase()} ${config.url}`);
    }

    return config;
  });

  // Response interceptor — retry 429/5xx/network-drop up to 2 times with exponential back-off
  const RETRYABLE_STATUSES = new Set([429, 500, 502, 503, 504]);

  type RetryableConfig = InternalAxiosRequestConfig & { _retryCount?: number };

  instance.interceptors.response.use(
    (response) => response,
    async (error) => {
      const originalRequest = error.config as RetryableConfig;
      const status = error.response?.status ?? 0;
      const isNetworkDrop = !error.response && error.code !== 'ERR_CANCELED';
      const isRetryable = RETRYABLE_STATUSES.has(status) || isNetworkDrop;
      const retryCount = originalRequest._retryCount ?? 0;

      if (isRetryable && retryCount < 2) {
        originalRequest._retryCount = retryCount + 1;
        const backoff = Math.min(1000 * Math.pow(2, retryCount), 10000);
        await new Promise((resolve) => setTimeout(resolve, backoff));
        return instance(originalRequest);
      }

      return Promise.reject(error);
    }
  );

  return instance;
}

const cpAxios = createCpAxiosInstance();
export default cpAxios;
