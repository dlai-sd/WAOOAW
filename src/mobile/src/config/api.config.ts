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
  /** CP Backend base URL — separate service from Plant Gateway */
  cpApiBaseUrl: string;
  timeout: number;
}

/**
 * Environment detection
 * Priority: ENV variable > APP_ENV from eas.json > release channel > default (development)
 */
export function detectEnvironment(): Environment {
  // 1. EXPO_PUBLIC_ENVIRONMENT is baked into the bundle at build time by
  //    `expo export`.  Always check it first — it is explicitly set by the
  //    person running the build and must beat the app.config.js default which
  //    falls back to 'development' when EAS_BUILD_PROFILE is not set.
  const pubEnv = process.env.EXPO_PUBLIC_ENVIRONMENT;
  if (pubEnv && isValidEnvironment(pubEnv)) {
    console.log('[API Config] Environment from EXPO_PUBLIC_ENVIRONMENT:', pubEnv);
    return pubEnv as Environment;
  }

  // 2. Fall back to Constants.expoConfig.extra.ENVIRONMENT (set by EAS build
  //    profiles via app.config.js).
  const extraEnv = Constants.expoConfig?.extra?.ENVIRONMENT;
  if (extraEnv && isValidEnvironment(extraEnv)) {
    console.log('[API Config] Environment from app.config extra.ENVIRONMENT:', extraEnv);
    return extraEnv as Environment;
  }

  // 3. Check APP_ENV from eas.json build profile (legacy fallback)
  const appEnv = process.env.APP_ENV;
  if (appEnv) {
    console.log('[API Config] Environment from APP_ENV:', appEnv);
    if (appEnv === 'development') return 'development';
    // All other APP_ENV values fall through to release channel check
  }

  // 4. Check Expo release channel
  const releaseChannel = (Constants.expoConfig?.updates as any)?.releaseChannel;
  if (releaseChannel) {
    console.log('[API Config] Environment from release channel:', releaseChannel);
    if (releaseChannel.includes('prod')) return 'prod';
    if (releaseChannel.includes('uat')) return 'uat';
    if (releaseChannel.includes('demo')) return 'demo';
  }

  // 5. Default to development
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
    cpApiBaseUrl: Platform.OS === 'android'
      ? 'http://10.0.2.2:8020/api'
      : 'http://localhost:8020/api',
    timeout: 30000, // Longer timeout for local debugging
  },
  demo: {
    apiBaseUrl: getApiUrlForEnvironment('demo', 'https://plant.demo.waooaw.com'),
    cpApiBaseUrl: 'https://cp.demo.waooaw.com/api',
    timeout: 15000, // Longer timeout for Cloud Run cold starts
  },
  uat: {
    apiBaseUrl: getApiUrlForEnvironment('uat', 'https://plant.uat.waooaw.com'),
    cpApiBaseUrl: 'https://cp.uat.waooaw.com/api',
    timeout: 10000,
  },
  prod: {
    apiBaseUrl: getApiUrlForEnvironment('prod', 'https://plant.waooaw.com'),
    cpApiBaseUrl: 'https://cp.waooaw.com/api',
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
