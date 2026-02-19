/**
 * Integration Test: Monitoring Services
 * 
 * Validates that monitoring service stubs work correctly.
 * Would have caught the missing async methods issue.
 */

import { crashlyticsService } from '../../src/services/monitoring/crashlytics.service';
import { analyticsService } from '../../src/services/analytics/firebase.analytics';
import { performanceService } from '../../src/services/monitoring/performance.service';

describe('Monitoring Services Integration', () => {
  /**
   * CRITICAL: All async methods must be properly stubbed
   */
  describe('Crashlytics Service', () => {
    it('should have all required async methods', () => {
      expect(typeof crashlyticsService.initialize).toBe('function');
      expect(typeof crashlyticsService.recordError).toBe('function');
      expect(typeof crashlyticsService.setUser).toBe('function');
      expect(typeof crashlyticsService.log).toBe('function');
      expect(typeof crashlyticsService.setCrashlyticsCollectionEnabled).toBe('function');
      expect(typeof crashlyticsService.didCrashOnPreviousExecution).toBe('function');
    });

    it('should initialize without errors', async () => {
      await expect(crashlyticsService.initialize()).resolves.toBeUndefined();
    });

    it('should handle setCrashlyticsCollectionEnabled', async () => {
      await expect(crashlyticsService.setCrashlyticsCollectionEnabled(true)).resolves.toBeUndefined();
    });

    it('should handle didCrashOnPreviousExecution', async () => {
      const result = await crashlyticsService.didCrashOnPreviousExecution();
      expect(typeof result).toBe('boolean');
    });

    it('should record errors without crashing', () => {
      expect(() => {
        crashlyticsService.recordError(new Error('Test error'));
      }).not.toThrow();
    });

    it('should set user without crashing', () => {
      expect(() => {
        crashlyticsService.setUser('user123', 'test@example.com', 'Test User');
      }).not.toThrow();
    });

    it('should log messages without crashing', () => {
      expect(() => {
        crashlyticsService.log('Test log message');
      }).not.toThrow();
    });
  });

  describe('Analytics Service', () => {
    it('should have all required async methods', () => {
      expect(typeof analyticsService.initialize).toBe('function');
      expect(typeof analyticsService.setUserId).toBe('function');
      expect(typeof analyticsService.logEvent).toBe('function');
      expect(typeof analyticsService.setAnalyticsCollectionEnabled).toBe('function');
    });

    it('should initialize without errors', async () => {
      await expect(analyticsService.initialize()).resolves.toBeUndefined();
    });

    it('should handle setAnalyticsCollectionEnabled', async () => {
      await expect(analyticsService.setAnalyticsCollectionEnabled(true)).resolves.toBeUndefined();
    });

    it('should set user ID without crashing', () => {
      expect(() => {
        analyticsService.setUserId('user123');
      }).not.toThrow();
    });

    it('should log events without crashing', () => {
      expect(() => {
        analyticsService.logEvent('test_event', { key: 'value' });
      }).not.toThrow();
    });
  });

  describe('Performance Service', () => {
    it('should have all required async methods', () => {
      expect(typeof performanceService.initialize).toBe('function');
      expect(typeof performanceService.startTrace).toBe('function');
      expect(typeof performanceService.stopTrace).toBe('function');
      expect(typeof performanceService.setPerformanceCollectionEnabled).toBe('function');
    });

    it('should initialize without errors', async () => {
      await expect(performanceService.initialize()).resolves.toBeUndefined();
    });

    it('should handle setPerformanceCollectionEnabled', async () => {
      await expect(performanceService.setPerformanceCollectionEnabled(true)).resolves.toBeUndefined();
    });

    it('should start traces without crashing', () => {
      expect(() => {
        performanceService.startTrace('test_trace');
      }).not.toThrow();
    });

    it('should stop traces without crashing', () => {
      expect(() => {
        performanceService.stopTrace('test_trace', { metric: 123 });
      }).not.toThrow();
    });
  });

  /**
   * Integration test: All services work together
   */
  it('should initialize all services without errors', async () => {
    await expect(
      Promise.all([
        crashlyticsService.initialize(),
        analyticsService.initialize(),
        performanceService.initialize(),
      ])
    ).resolves.toBeDefined();
  });

  /**
   * Integration test: Services accept monitoring setup from App.tsx
   */
  it('should accept user setup like App.tsx does', async () => {
    const mockCustomerId = 'cust_123';
    const mockEmail = 'test@example.com';
    const mockFullName = 'Test User';

    // This is what App.tsx does after skip sign-in
    await expect(async () => {
      await crashlyticsService.setCrashlyticsCollectionEnabled(true);
      await analyticsService.setAnalyticsCollectionEnabled(true);
      await performanceService.setPerformanceCollectionEnabled(true);

      crashlyticsService.setUser(mockCustomerId, mockEmail, mockFullName);
      analyticsService.setUserId(mockCustomerId);
    }).not.toThrow();
  });
});
