/**
 * Environment Configuration Manager
 * 
 * Manages environment-specific settings across development, demo, uat, and prod.
 * Aligns with platform-wide environments defined in CONTEXT_AND_INDEX.md.
 * Automatically detects environment from EXPO_PUBLIC_ENVIRONMENT (set in eas.json).
 * 
 * Usage:
 *   import { config } from '@/config/environment.config';
 *   const apiUrl = config.API_BASE_URL;
 */

export type Environment = 'development' | 'demo' | 'uat' | 'prod';

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
 * Get current environment from EXPO_PUBLIC_ENVIRONMENT (set in eas.json per profile)
 */
function getCurrentEnvironment(): Environment {
  // EAS Build sets EXPO_PUBLIC_ENVIRONMENT via the env block in eas.json
  const env = process.env.EXPO_PUBLIC_ENVIRONMENT as Environment | undefined;
  
  if (env === 'demo' || env === 'uat' || env === 'prod') {
    return env;
  }
  
  if (env === 'development') {
    return 'development';
  }
  
  // Fallback for local development (expo start without EAS)
  if (typeof __DEV__ !== 'undefined' && __DEV__) {
    return 'development';
  }
  
  return 'demo'; // Safe default (avoids accidentally hitting prod)
}

/**
 * Get API base URL - handles Codespace URLs
 */
function getApiBaseUrl(): string {
  // If explicitly set via environment variable, use it
  const envUrl = process.env.EXPO_PUBLIC_API_URL;
  if (envUrl) {
    return envUrl;
  }

  // For GitHub Codespace, construct the URL
  // Codespace format: https://${CODESPACE_NAME}-{PORT}.app.github.dev
  const codespaceName = process.env.CODESPACE_NAME || process.env.GITHUB_CODESPACE_NAME;
  if (codespaceName) {
    return `https://${codespaceName}-8000.app.github.dev/api`;
  }

  // Default to localhost for local development
  return 'http://localhost:8000/api';
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
      baseUrl: getApiBaseUrl(),
      timeout: 30000, // Longer for local debugging
      retryAttempts: 2,
    },
    features: {
      analytics: false,
      crashReporting: false,
      performance: true,
      payments: false,
    },
    monitoring: {
      sentryDsn: undefined,
    },
    ENV: 'development',
    API_BASE_URL: getApiBaseUrl(),
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

  demo: {
    app: {
      name: 'WAOOAW Demo',
      env: 'demo',
    },
    api: {
      baseUrl: 'https://plant.demo.waooaw.com',
      timeout: 15000, // Longer for Cloud Run cold starts
      retryAttempts: 2,
    },
    features: {
      analytics: true,
      crashReporting: true,
      performance: true,
      payments: false, // Payments disabled in demo
    },
    monitoring: {
      sentryDsn: undefined,
    },
    ENV: 'demo',
    API_BASE_URL: 'https://plant.demo.waooaw.com',
    WEB_APP_URL: 'https://cp.demo.waooaw.com',
    RAZORPAY_KEY_ID: '',
    RAZORPAY_KEY_SECRET: '',
    GOOGLE_OAUTH_CLIENT_ID: '',
    SENTRY_DSN: '',
    FIREBASE_CONFIG: {
      apiKey: '',
      authDomain: '',
      projectId: '',
      storageBucket: '',
      messagingSenderId: '',
      appId: '',
      measurementId: '',
    },
    ENABLE_ANALYTICS: true,
    ENABLE_ERROR_REPORTING: true,
    ENABLE_PERFORMANCE_MONITORING: true,
    LOG_LEVEL: 'info',
    CACHE_TTL_MINUTES: 10,
  },

  uat: {
    app: {
      name: 'WAOOAW UAT',
      env: 'uat',
    },
    api: {
      baseUrl: 'https://plant.uat.waooaw.com',
      timeout: 10000,
      retryAttempts: 2,
    },
    features: {
      analytics: true,
      crashReporting: true,
      performance: true,
      payments: true,
    },
    monitoring: {
      sentryDsn: undefined,
    },
    ENV: 'uat',
    API_BASE_URL: 'https://plant.uat.waooaw.com',
    WEB_APP_URL: 'https://cp.uat.waooaw.com',
    RAZORPAY_KEY_ID: 'rzp_test_UAT_KEY_ID',
    RAZORPAY_KEY_SECRET: 'test_secret_UAT_SECRET',
    GOOGLE_OAUTH_CLIENT_ID: '',
    SENTRY_DSN: '',
    FIREBASE_CONFIG: {
      apiKey: '',
      authDomain: '',
      projectId: '',
      storageBucket: '',
      messagingSenderId: '',
      appId: '',
      measurementId: '',
    },
    ENABLE_ANALYTICS: true,
    ENABLE_ERROR_REPORTING: true,
    ENABLE_PERFORMANCE_MONITORING: true,
    LOG_LEVEL: 'info',
    CACHE_TTL_MINUTES: 15,
  },

  prod: {
    app: {
      name: 'WAOOAW',
      env: 'prod',
    },
    api: {
      baseUrl: 'https://plant.waooaw.com',
      timeout: 10000,
      retryAttempts: 3,
    },
    features: {
      analytics: true,
      crashReporting: true,
      performance: true,
      payments: true,
    },
    monitoring: {
      sentryDsn: undefined,
    },
    ENV: 'prod',
    API_BASE_URL: 'https://plant.waooaw.com',
    WEB_APP_URL: 'https://cp.waooaw.com',
    RAZORPAY_KEY_ID: 'rzp_live_PROD_KEY_ID',
    RAZORPAY_KEY_SECRET: 'live_secret_PROD_SECRET',
    GOOGLE_OAUTH_CLIENT_ID: '',
    SENTRY_DSN: '',
    FIREBASE_CONFIG: {
      apiKey: '',
      authDomain: '',
      projectId: '',
      storageBucket: '',
      messagingSenderId: '',
      appId: '',
      measurementId: '',
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
export const isDemo = config.ENV === 'demo';
export const isUat = config.ENV === 'uat';
export const isProduction = config.ENV === 'prod';

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
