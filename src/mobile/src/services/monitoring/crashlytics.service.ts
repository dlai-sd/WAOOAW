/**
 * Firebase Crashlytics Service
 * Real-time crash reporting and non-fatal error tracking
 */

import crashlytics from '@react-native-firebase/crashlytics';
import { config } from '../../config/environment.config';

export class CrashlyticsService {
  private initialized = false;

  /**
   * Initialize Crashlytics
   * Call this once in App.tsx on mount
   */
  async initialize(): Promise<void> {
    if (this.initialized) return;

    try {
      // Disable in development mode to avoid polluting crash reports
      if (!config.features.crashReporting) {
        await crashlytics().setCrashlyticsCollectionEnabled(false);
        console.log('[Crashlytics] Disabled in development mode');
        return;
      }

      await crashlytics().setCrashlyticsCollectionEnabled(true);
      this.initialized = true;
      console.log('[Crashlytics] Initialized successfully');

      // Check if app crashed last time
      const didCrash = await crashlytics().didCrashOnPreviousExecution();
      if (didCrash) {
        console.log('[Crashlytics] App crashed on previous execution');
      }
    } catch (error) {
      console.error('[Crashlytics] Initialization failed:', error);
    }
  }

  /**
   * Set user context for crash reports
   * Call this when user signs in
   */
  async setUser(userId: string, email?: string, name?: string): Promise<void> {
    try {
      await crashlytics().setUserId(userId);

      if (email) {
        await crashlytics().setAttribute('email', email);
      }

      if (name) {
        await crashlytics().setAttribute('name', name);
      }

      console.log(`[Crashlytics] User context set: ${userId}`);
    } catch (error) {
      console.error('[Crashlytics] Failed to set user:', error);
    }
  }

  /**
   * Clear user context (on sign out)
   */
  async clearUser(): Promise<void> {
    try {
      await crashlytics().setUserId('');
      await crashlytics().setAttribute('email', '');
      await crashlytics().setAttribute('name', '');
      console.log('[Crashlytics] User context cleared');
    } catch (error) {
      console.error('[Crashlytics] Failed to clear user:', error);
    }
  }

  /**
   * Set custom attributes for crash context
   */
  async setAttribute(key: string, value: string): Promise<void> {
    try {
      await crashlytics().setAttribute(key, value);
    } catch (error) {
      console.error(`[Crashlytics] Failed to set attribute ${key}:`, error);
    }
  }

  /**
   * Set multiple attributes at once
   */
  async setAttributes(attributes: Record<string, string>): Promise<void> {
    try {
      await crashlytics().setAttributes(attributes);
    } catch (error) {
      console.error('[Crashlytics] Failed to set attributes:', error);
    }
  }

  /**
   * Log a message for crash debugging
   * These logs appear in crash reports
   */
  async log(message: string): Promise<void> {
    try {
      await crashlytics().log(message);
    } catch (error) {
      console.error('[Crashlytics] Failed to log message:', error);
    }
  }

  /**
   * Record a non-fatal error
   * Use this for caught errors that should be tracked
   */
  async recordError(error: Error, context?: Record<string, any>): Promise<void> {
    try {
      // Set context attributes if provided
      if (context) {
        const attributes: Record<string, string> = {};
        Object.entries(context).forEach(([key, value]) => {
          attributes[key] = String(value);
        });
        await this.setAttributes(attributes);
      }

      // Record the error
      await crashlytics().recordError(error);
      console.log(`[Crashlytics] Recorded error: ${error.message}`);
    } catch (err) {
      console.error('[Crashlytics] Failed to record error:', err);
    }
  }

  /**
   * Record a non-fatal error from JS exception
   */
  async recordException(
    message: string,
    stack?: string,
    context?: Record<string, any>
  ): Promise<void> {
    try {
      const error = new Error(message);
      if (stack) {
        error.stack = stack;
      }
      await this.recordError(error, context);
    } catch (err) {
      console.error('[Crashlytics] Failed to record exception:', err);
    }
  }

  /**
   * Test crash reporting (use only in testing/staging)
   * WARNING: This will crash the app!
   */
  async testCrash(): Promise<void> {
    if (!config.features.crashReporting) {
      console.warn('[Crashlytics] Test crash disabled in development mode');
      return;
    }

    console.warn('[Crashlytics] Triggering test crash in 2 seconds...');
    setTimeout(() => {
      crashlytics().crash();
    }, 2000);
  }

  /**
   * Check if app crashed on previous execution
   */
  async didCrashOnPreviousExecution(): Promise<boolean> {
    try {
      return await crashlytics().didCrashOnPreviousExecution();
    } catch (error) {
      console.error('[Crashlytics] Failed to check previous crash:', error);
      return false;
    }
  }
}

// Export singleton instance
export const crashlyticsService = new CrashlyticsService();
