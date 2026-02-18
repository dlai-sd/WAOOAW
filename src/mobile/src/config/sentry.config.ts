/**
 * Sentry Configuration
 * Error tracking and performance monitoring
 */

import * as Sentry from '@sentry/react-native';
import { config } from './environment.config';

/**
 * Initialize Sentry
 * Call this BEFORE App component initialization
 */
export const initSentry = (): void => {
  // Only enable Sentry in staging and production
  const sentryDsn = config.monitoring?.sentryDsn;

  if (!sentryDsn) {
    console.log('[Sentry] No DSN configured, skipping initialization');
    return;
  }

  if (!config.features.crashReporting) {
    console.log('[Sentry] Disabled in development mode');
    return;
  }

  try {
    Sentry.init({
      dsn: sentryDsn,
      environment: config.app.env,

      // Performance monitoring
      tracesSampleRate: config.app.env === 'production' ? 0.1 : 1.0, // 10% in prod, 100% in staging

      // Session tracking
      enableAutoSessionTracking: true,
      sessionTrackingIntervalMillis: 30000, // 30 seconds

      // Integrations
      integrations: [
        new Sentry.ReactNativeTracing({
          tracingOrigins: ['localhost', config.api.baseUrl.replace(/^https?:\/\//, ''), /^\//],
          routingInstrumentation: new Sentry.ReactNavigationInstrumentation(),
        }),
      ],

      // Filter sensitive data
      beforeSend(event, hint) {
        // Remove sensitive user data
        if (event.user) {
          delete event.user.email;
          delete event.user.ip_address;
        }

        // Remove authorization headers
        if (event.request?.headers) {
          delete event.request.headers.Authorization;
          delete event.request.headers.authorization;
        }

        // Filter out development errors if somehow enabled
        if (config.app.env === 'development') {
          return null;
        }

        return event;
      },

      // Enable debug mode in non-production
      debug: config.app.env !== 'production',
    });

    console.log(`[Sentry] Initialized successfully (${config.app.env})`);
  } catch (error) {
    console.error('[Sentry] Initialization failed:', error);
  }
};

/**
 * Set user context for Sentry
 */
export const setSentryUser = (userId: string, email?: string): void => {
  try {
    Sentry.setUser({
      id: userId,
      // Don't include email in production for privacy
      ...(config.app.env !== 'production' && email ? { email } : {}),
    });
  } catch (error) {
    console.error('[Sentry] Failed to set user:', error);
  }
};

/**
 * Clear Sentry user context (on sign out)
 */
export const clearSentryUser = (): void => {
  try {
    Sentry.setUser(null);
  } catch (error) {
    console.error('[Sentry] Failed to clear user:', error);
  }
};

/**
 * Add breadcrumb for debugging
 */
export const addSentryBreadcrumb = (message: string, category: string, data?: any): void => {
  try {
    Sentry.addBreadcrumb({
      message,
      category,
      data,
      level: 'info',
    });
  } catch (error) {
    console.error('[Sentry] Failed to add breadcrumb:', error);
  }
};

/**
 * Capture exception manually
 */
export const captureSentryException = (error: Error, context?: Record<string, any>): void => {
  try {
    if (context) {
      Sentry.setContext('error_context', context);
    }
    Sentry.captureException(error);
  } catch (err) {
    console.error('[Sentry] Failed to capture exception:', err);
  }
};

/**
 * Capture message (non-error event)
 */
export const captureSentryMessage = (message: string, level: Sentry.SeverityLevel = 'info'): void => {
  try {
    Sentry.captureMessage(message, level);
  } catch (error) {
    console.error('[Sentry] Failed to capture message:', error);
  }
};
