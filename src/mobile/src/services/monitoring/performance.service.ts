/**
 * Firebase Performance Monitoring Service  
 * Tracks app performance metrics (API calls, screen rendering, custom traces)
 */

import perf from '@react-native-firebase/perf';
import { config } from '../../config/environment.config';

export class PerformanceMonitoringService {
  private initialized = false;

  /**
   * Initialize Performance Monitoring
   */
  async initialize(): Promise<void> {
    if (this.initialized) return;

    try {
      // Disable in development (optional, Firebase auto-disables debug builds)
      if (!config.features.analytics) {
        await perf().setPerformanceCollectionEnabled(false);
        console.log('[Performance] Disabled in development mode');
        return;
      }

      await perf().setPerformanceCollectionEnabled(true);
      this.initialized = true;
      console.log('[Performance] Initialized successfully');
    } catch (error) {
      console.error('[Performance] Initialization failed:', error);
    }
  }

  /**
   * Trace an API call
   */
  async traceAPICall<T>(
    url: string,
    method: string,
    apiCall: () => Promise<T>
  ): Promise<T> {
    const traceName = `api_${method}_${url.replace(/\//g, '_')}`.substring(0, 100);
    const trace = await perf().startTrace(traceName);

    trace.putAttribute('method', method);
    trace.putAttribute('url', url);

    const startTime = Date.now();

    try {
      const result = await apiCall();
      const duration = Date.now() - startTime;

      trace.putMetric('response_time_ms', duration);
      trace.putAttribute('status', 'success');
      await trace.stop();

      return result;
    } catch (error) {
      const duration = Date.now() - startTime;

      trace.putMetric('response_time_ms', duration);
      trace.putAttribute('status', 'error');
      trace.putAttribute('error_message', error instanceof Error ? error.message : 'Unknown error');
      await trace.stop();

      throw error;
    }
  }

  /**
   * Trace screen rendering performance
   */
  async traceScreenLoad(screenName: string, renderFunction: () => Promise<void>): Promise<void> {
    const traceName = `screen_${screenName}`.substring(0, 100);
    const trace = await perf().startTrace(traceName);

    try {
      await renderFunction();
      await trace.stop();
    } catch (error) {
      await trace.stop();
      throw error;
    }
  }

  /**
   * Start a custom trace
   * Use this for measuring specific operations
   */
  async startTrace(name: string): Promise<any> {
    try {
      const traceName = name.substring(0, 100); // Firebase limit
      return await perf().startTrace(traceName);
    } catch (error) {
      console.error(`[Performance] Failed to start trace ${name}:`, error);
      return null;
    }
  }

  /**
   * Stop a custom trace
   */
  async stopTrace(trace: any): Promise<void> {
    try {
      if (trace) {
        await trace.stop();
      }
    } catch (error) {
      console.error('[Performance] Failed to stop trace:', error);
    }
  }

  /**
   * Create an HTTP metric (for manual network call tracking)
   */
  async createHttpMetric(url: string, method: string): Promise<any> {
    try {
      return await perf().newHttpMetric(url, method);
    } catch (error) {
      console.error('[Performance] Failed to create HTTP metric:', error);
      return null;
    }
  }
}

// Export singleton instance
export const performanceService = new PerformanceMonitoringService();
