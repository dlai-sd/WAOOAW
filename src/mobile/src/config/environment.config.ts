/**
 * Environment Configuration Manager
 * 
 * Manages environment-specific settings across development, staging, and production.
 * Automatically detects environment from APP_ENV or __DEV__ flags.
 * 
 * Usage:
 *   import { config } from '@/config/environment.config';
 *   const apiUrl = config.API_BASE_URL;
 */

export type Environment = 'development' | 'staging' | 'production';

export interface EnvironmentConfig {
  app: {
    name: string;
    env: Environment;
  };
  api: {
    baseUrl: string;
    timeout: number;
    retryAttempts: number;
  };
  features: {
    analytics: boolean;
    crashReporting: boolean;
    performance: boolean;
    payments: boolean; // Enable/disable Razorpay integration
  };
  monitoring: {
    sentryDsn?: string;
  };
  ENV: Environment;
  API_BASE_URL: string;
  WEB_APP_URL: string;
  RAZORPAY_KEY_ID: string;
  RAZORPAY_KEY_SECRET: string;
  GOOGLE_OAUTH_CLIENT_ID: string;
  SENTRY_DSN: string;
  FIREBASE_CONFIG: {
    apiKey: string;
    authDomain: string;
    projectId: string;
    storageBucket: string;
    messagingSenderId: string;
    appId: string;
    measurementId: string;
  };
  ENABLE_ANALYTICS: boolean;
  ENABLE_ERROR_REPORTING: boolean;
  ENABLE_PERFORMANCE_MONITORING: boolean;
  LOG_LEVEL: 'debug' | 'info' | 'warn' | 'error';
  CACHE_TTL_MINUTES: number;
}

/**
 * Get current environment from APP_ENV or fallback to __DEV__
 */
function getCurrentEnvironment(): Environment {
  // EAS Build sets process.env.APP_ENV via eas.json
  const appEnv = process.env.APP_ENV as Environment | undefined;
  
  if (appEnv === 'production' || appEnv === 'staging' || appEnv === 'development') {
    return appEnv;
  }
  
  // Fallback for local development
  if (typeof __DEV__ !== 'undefined' && __DEV__) {
    return 'development';
  }
  
  return 'production'; // Safe default
}

/**
 * Environment-Specific Configurations
 */
const environments: Record<Environment, EnvironmentConfig> = {
  development: {
    app: {
      name: 'WAOOAW Dev',
      env: 'development',
    },
    api: {
      baseUrl: 'http://localhost:8000/api',
      timeout: 10000,
      retryAttempts: 2,
    },
    features: {
      analytics: false,
      crashReporting: false,
      performance: true,
      payments: false, // Disabled for demo - no Razorpay needed
    },
    monitoring: {
      sentryDsn: undefined,
    },
    ENV: 'development',
    API_BASE_URL: 'http://localhost:8000/api',
    WEB_APP_URL: 'http://localhost:3000',
    RAZORPAY_KEY_ID: '', // Not needed for demo
    RAZORPAY_KEY_SECRET: '', // Not needed for demo
    GOOGLE_OAUTH_CLIENT_ID: 'YOUR_DEV_CLIENT_ID.apps.googleusercontent.com',
    SENTRY_DSN: '',
    FIREBASE_CONFIG: {
      apiKey: 'DEV_FIREBASE_API_KEY',
      authDomain: 'waooaw-dev.firebaseapp.com',
      projectId: 'waooaw-dev',
      storageBucket: 'waooaw-dev.appspot.com',
      messagingSenderId: '123456789012',
      appId: '1:123456789012:ios:abcdef1234567890',
      measurementId: 'G-XXXXXXXXXX',
    },
    ENABLE_ANALYTICS: false,
    ENABLE_ERROR_REPORTING: false,
    ENABLE_PERFORMANCE_MONITORING: true,
    LOG_LEVEL: 'debug',
    CACHE_TTL_MINUTES: 5,
  },
  
  staging: {
    app: {
      name: 'WAOOAW Staging',
      env: 'staging',
    },
    api: {
      baseUrl: 'https://api-staging.waooaw.com/api',
      timeout: 10000,
      retryAttempts: 2,
    },
    features: {
      analytics: true,
      crashReporting: true,
      performance: true,
    },
    monitoring: {
      sentryDsn: 'https://YOUR_SENTRY_DSN@sentry.io/STAGING_PROJECT_ID',
    },
    ENV: 'staging',
    API_BASE_URL: 'https://api-staging.waooaw.com/api',
    WEB_APP_URL: 'https://staging.waooaw.com',
    RAZORPAY_KEY_ID: 'rzp_test_STAGING_KEY_ID',
    RAZORPAY_KEY_SECRET: 'test_secret_STAGING_SECRET',
    GOOGLE_OAUTH_CLIENT_ID: 'YOUR_STAGING_CLIENT_ID.apps.googleusercontent.com',
    SENTRY_DSN: 'https://YOUR_SENTRY_DSN@sentry.io/STAGING_PROJECT_ID',
    FIREBASE_CONFIG: {
      apiKey: 'STAGING_FIREBASE_API_KEY',
      authDomain: 'waooaw-staging.firebaseapp.com',
      projectId: 'waooaw-staging',
      storageBucket: 'waooaw-staging.appspot.com',
      messagingSenderId: '234567890123',
      appId: '1:234567890123:ios:bcdef1234567890a',
      measurementId: 'G-YYYYYYYYYY',
    },
    ENABLE_ANALYTICS: true,
    ENABLE_ERROR_REPORTING: true,
    ENABLE_PERFORMANCE_MONITORING: true,
    LOG_LEVEL: 'info',
    CACHE_TTL_MINUTES: 10,
  },
  
  production: {
    app: {
      name: 'WAOOAW',
      env: 'production',
    },
    api: {
      baseUrl: 'https://api.waooaw.com/api',
      timeout: 10000,
      retryAttempts: 2,
    },
    features: {
      analytics: true,
      crashReporting: true,
      performance: true,
      payments: true, // Enable payments in production
    },
    monitoring: {
      sentryDsn: 'https://YOUR_SENTRY_DSN@sentry.io/PROD_PROJECT_ID',
    },
    ENV: 'production',
    API_BASE_URL: 'https://api.waooaw.com/api',
    WEB_APP_URL: 'https://waooaw.com',
    RAZORPAY_KEY_ID: 'rzp_live_PROD_KEY_ID',
    RAZORPAY_KEY_SECRET: 'live_secret_PROD_SECRET',
    GOOGLE_OAUTH_CLIENT_ID: 'YOUR_PROD_CLIENT_ID.apps.googleusercontent.com',
    SENTRY_DSN: 'https://YOUR_SENTRY_DSN@sentry.io/PROD_PROJECT_ID',
    FIREBASE_CONFIG: {
      apiKey: 'PROD_FIREBASE_API_KEY',
      authDomain: 'waooaw-prod.firebaseapp.com',
      projectId: 'waooaw-prod',
      storageBucket: 'waooaw-prod.appspot.com',
      messagingSenderId: '345678901234',
      appId: '1:345678901234:ios:cdef1234567890ab',
      measurementId: 'G-ZZZZZZZZZZ',
    },
    ENABLE_ANALYTICS: true,
    ENABLE_ERROR_REPORTING: true,
    ENABLE_PERFORMANCE_MONITORING: true,
    LOG_LEVEL: 'warn',
    CACHE_TTL_MINUTES: 30,
  },
};

/**
 * Current Active Configuration
 * Import this throughout the app
 */
export const config: EnvironmentConfig = environments[getCurrentEnvironment()];

/**
 * Helper to check current environment
 */
export const isDevelopment = config.ENV === 'development';
export const isStaging = config.ENV === 'staging';
export const isProduction = config.ENV === 'production';

/**
 * Log current configuration on startup (non-sensitive only)
 */
if (isDevelopment) {
  console.log('🔧 Environment Configuration Loaded:', {
    ENV: config.ENV,
    API_BASE_URL: config.API_BASE_URL,
    ENABLE_ANALYTICS: config.ENABLE_ANALYTICS,
    LOG_LEVEL: config.LOG_LEVEL,
  });
}
