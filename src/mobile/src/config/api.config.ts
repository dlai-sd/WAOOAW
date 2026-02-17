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
 * Priority: ENV variable > release channel > default (development)
 */
export function detectEnvironment(): Environment {
  // 1. Check explicit ENV variable (set in eas.json or .env)
  const explicitEnv = Constants.expoConfig?.extra?.ENVIRONMENT || 
                      process.env.EXPO_PUBLIC_ENVIRONMENT;
  
  if (explicitEnv && isValidEnvironment(explicitEnv)) {
    return explicitEnv as Environment;
  }

  // 2. Check Expo release channel
  const releaseChannel = Constants.expoConfig?.updates?.releaseChannel;
  if (releaseChannel) {
    if (releaseChannel.includes('prod')) return 'prod';
    if (releaseChannel.includes('uat')) return 'uat';
    if (releaseChannel.includes('demo')) return 'demo';
  }

  // 3. Default to development
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
 * API configuration by environment
 */
const API_CONFIGS: Record<Environment, APIConfig> = {
  development: {
    apiBaseUrl: getLocalhostUrl(),
    timeout: 30000, // Longer timeout for local debugging
  },
  demo: {
    apiBaseUrl: 'https://cp.demo.waooaw.com',
    timeout: 10000,
  },
  uat: {
    apiBaseUrl: 'https://cp.uat.waooaw.com',
    timeout: 10000,
  },
  prod: {
    apiBaseUrl: 'https://cp.waooaw.com',
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
