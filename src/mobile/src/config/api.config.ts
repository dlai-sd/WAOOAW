/**
 * API Configuration
 * Environment-based API URLs and settings
 */

import Constants from 'expo-constants';
import { Platform } from 'react-native';

/**
 * Environment types
 */
export type Environment = 'development' | 'demo' | 'uat' | 'prod';

/**
 * API configuration per environment
 */
interface APIConfig {
  apiBaseUrl: string;
  timeout: number;
}

/**
 * Environment detection
 * Priority: ENV variable > APP_ENV from eas.json > release channel > default (development)
 */
export function detectEnvironment(): Environment {
  // 1. Check explicit ENV variable (set in eas.json or .env)
  const explicitEnv = Constants.expoConfig?.extra?.ENVIRONMENT || 
                      process.env.EXPO_PUBLIC_ENVIRONMENT;
  
  if (explicitEnv && isValidEnvironment(explicitEnv)) {
    console.log('[API Config] Environment from EXPO_PUBLIC_ENVIRONMENT:', explicitEnv);
    return explicitEnv as Environment;
  }

  // 2. Check APP_ENV from eas.json build profile (legacy fallback)
  const appEnv = process.env.APP_ENV;
  if (appEnv) {
    console.log('[API Config] Environment from APP_ENV:', appEnv);
    if (appEnv === 'development') return 'development';
    // All other APP_ENV values fall through to release channel check
  }

  // 3. Check Expo release channel
  const releaseChannel = (Constants.expoConfig?.updates as any)?.releaseChannel;
  if (releaseChannel) {
    console.log('[API Config] Environment from release channel:', releaseChannel);
    if (releaseChannel.includes('prod')) return 'prod';
    if (releaseChannel.includes('uat')) return 'uat';
    if (releaseChannel.includes('demo')) return 'demo';
  }

  // 4. Default to development
  console.log('[API Config] Using default environment: development');
  return 'development';
}

/**
 * Validate environment string
 */
function isValidEnvironment(env: string): env is Environment {
  return ['development', 'demo', 'uat', 'prod'].includes(env);
}

/**
 * Get localhost URL for development
 * iOS Simulator: localhost
 * Android Emulator: 10.0.2.2
 * Physical Device: Use your machine's local IP
 */
function getLocalhostUrl(): string {
  if (Platform.OS === 'android') {
    // Android emulator localhost proxy
    return 'http://10.0.2.2:8020';
  } else if (Platform.OS === 'ios') {
    // iOS simulator can use localhost
    return 'http://localhost:8020';
  }
  // Web fallback
  return 'http://localhost:8020';
}

/**
 * Get API URL from environment variable or use defaults
 * This ensures EXPO_PUBLIC_API_URL from eas.json is respected
 */
function getApiUrlForEnvironment(env: Environment, defaultUrl: string): string {
  const explicitUrl = process.env.EXPO_PUBLIC_API_URL;
  
  // Use explicit URL if provided and matches environment
  if (explicitUrl) {
    console.log(`[API Config] Using EXPO_PUBLIC_API_URL for ${env}:`, explicitUrl);
    return explicitUrl;
  }
  
  console.log(`[API Config] Using default URL for ${env}:`, defaultUrl);
  return defaultUrl;
}

/**
 * API configuration by environment
 */
const API_CONFIGS: Record<Environment, APIConfig> = {
  development: {
    apiBaseUrl: getApiUrlForEnvironment('development', getLocalhostUrl()),
    timeout: 30000, // Longer timeout for local debugging
  },
  demo: {
    apiBaseUrl: getApiUrlForEnvironment('demo', 'https://plant.demo.waooaw.com'),
    timeout: 15000, // Longer timeout for Cloud Run cold starts
  },
  uat: {
    apiBaseUrl: getApiUrlForEnvironment('uat', 'https://plant.uat.waooaw.com'),
    timeout: 10000,
  },
  prod: {
    apiBaseUrl: getApiUrlForEnvironment('prod', 'https://plant.waooaw.com'),
    timeout: 10000,
  },
};

/**
 * Get current API configuration
 */
export function getAPIConfig(): APIConfig {
  const env = detectEnvironment();
  return API_CONFIGS[env];
}

/**
 * Get current environment name
 */
export function getCurrentEnvironment(): Environment {
  return detectEnvironment();
}

/**
 * Check if running in development
 */
export function isDevelopment(): boolean {
  return detectEnvironment() === 'development';
}

/**
 * Check if running in production
 */
export function isProduction(): boolean {
  return detectEnvironment() === 'prod';
}

/**
 * API endpoints
 */
export const API_ENDPOINTS = {
  // Auth
  AUTH_GOOGLE: '/auth/google',
  AUTH_CHECK: '/auth/check',
  AUTH_LOGOUT: '/auth/logout',
  
  // Users
  USER_PROFILE: '/users/me',
  USER_UPDATE: '/users/me',
  
  // Agents
  AGENTS_LIST: '/agents',
  AGENTS_DETAIL: (id: string) => `/agents/${id}`,
  AGENTS_SEARCH: '/agents/search',
  
  // Skills
  SKILLS_LIST: '/skills',
  SKILLS_DETAIL: (id: string) => `/skills/${id}`,
  
  // Job Roles
  JOB_ROLES_LIST: '/job-roles',
  JOB_ROLES_DETAIL: (id: string) => `/job-roles/${id}`,
  
  // Trials
  TRIALS_LIST: '/trials',
  TRIALS_CREATE: '/trials',
  TRIALS_DETAIL: (id: string) => `/trials/${id}`,
  
  // Subscriptions
  SUBSCRIPTIONS_LIST: '/subscriptions',
  SUBSCRIPTIONS_CREATE: '/subscriptions',
  SUBSCRIPTIONS_DETAIL: (id: string) => `/subscriptions/${id}`,
  SUBSCRIPTIONS_CANCEL: (id: string) => `/subscriptions/${id}/cancel`,
} as const;

export default {
  getAPIConfig,
  getCurrentEnvironment,
  isDevelopment,
  isProduction,
  API_ENDPOINTS,
};
