/**
 * Performance Monitoring Service
 * Tracks app performance metrics for optimization
 * 
 * Features:
 * - Screen render time tracking
 * - API call performance monitoring
 * - Memory usage tracking
 * - FPS monitoring
 */

interface PerformanceMetric {
  name: string;
  value: number;
  timestamp: number;
  metadata?: Record<string, unknown>;
}

interface ScreenRenderMetric {
  screen: string;
  screenName: string;
  renderTime: number;
  duration: number;
  timestamp: number;
}

interface APICallMetric {
  endpoint: string;
  method: string;
  duration: number;
  status: number;
  statusCode: number;
  timestamp: number;
}

class PerformanceMonitoringService {
  private metrics: PerformanceMetric[] = [];
  private screenRenderTimes: ScreenRenderMetric[] = [];
  private apiCallMetrics: APICallMetric[] = [];
  private screenStartTimes: Map<string, number> = new Map();
  private apiStartTimes: Map<string, number> = new Map();

  /**
   * Track screen render start
   */
  startScreenRender(screenName: string): void {
    this.screenStartTimes.set(screenName, Date.now());
  }

  /**
   * Track screen render end
   */
  endScreenRender(screenName: string): void {
    const startTime = this.screenStartTimes.get(screenName);
    if (startTime) {
      const renderTime = Date.now() - startTime;
      this.screenRenderTimes.push({
        screen: screenName,
        screenName: screenName,
        renderTime,
        duration: renderTime,
        timestamp: Date.now(),
      });
      this.screenStartTimes.delete(screenName);

      // Keep only last 100 entries
      if (this.screenRenderTimes.length > 100) {
        this.screenRenderTimes.shift();
      }
    } else {
      this.screenRenderTimes.push({
        screen: screenName,
        screenName: screenName,
        renderTime: 0,
        duration: 0,
        timestamp: Date.now(),
      });

      if (this.screenRenderTimes.length > 100) {
        this.screenRenderTimes.shift();
      }
    }
  }

  /**
   * Track API call start
   */
  startAPICall(endpoint: string, method?: string): string {
    const callId = method ? `${method} ${endpoint}` : endpoint;
    this.apiStartTimes.set(callId, Date.now());
    return callId;
  }

  /**
   * Track API call end
   */
  endAPICall(callId: string, status: number, metadata?: Record<string, unknown>): void {
    const startTime = this.apiStartTimes.get(callId);
    if (startTime) {
      const duration = Date.now() - startTime;
      const [firstToken, ...restTokens] = callId.split(' ');
      const method = restTokens.length > 0 ? firstToken : firstToken.split(':')[0] || 'GET';
      const endpoint = callId;

      this.apiCallMetrics.push({
        endpoint,
        method,
        duration,
        status,
        statusCode: status,
        timestamp: Date.now(),
      });
      this.apiStartTimes.delete(callId);

      // Keep only last 100 entries
      if (this.apiCallMetrics.length > 100) {
        this.apiCallMetrics.shift();
      }

      // Log to console in development
      if (__DEV__) {
        console.log(`[API] ${method} ${endpoint}: ${duration}ms (${status})`);
      }
    } else {
      const [firstToken, ...restTokens] = callId.split(' ');
      const method = restTokens.length > 0 ? firstToken : firstToken.split(':')[0] || 'GET';

      this.apiCallMetrics.push({
        endpoint: callId,
        method,
        duration: 0,
        status,
        statusCode: status,
        timestamp: Date.now(),
      });

      if (this.apiCallMetrics.length > 100) {
        this.apiCallMetrics.shift();
      }
    }
  }

  /**
   * Record custom performance metric
   */
  recordMetric(name: string, value: number, metadata?: Record<string, unknown>): void {
    this.metrics.push({
      name,
      value,
      timestamp: Date.now(),
      metadata,
    });

    // Keep only last 100 entries
    if (this.metrics.length > 100) {
      this.metrics.shift();
    }
  }

  /**
   * Get average screen render time
   */
  getAverageScreenRenderTime(screenName?: string): number {
    const filteredMetrics = screenName
      ? this.screenRenderTimes.filter((m) => m.screen === screenName)
      : this.screenRenderTimes;

    if (filteredMetrics.length === 0) return 0;

    const sum = filteredMetrics.reduce((acc, m) => acc + m.renderTime, 0);
    return sum / filteredMetrics.length;
  }

  /**
   * Get average API call duration
   */
  getAverageAPICallDuration(endpoint?: string): number {
    const filteredMetrics = endpoint
      ? this.apiCallMetrics.filter((m) => m.endpoint.includes(endpoint))
      : this.apiCallMetrics;

    if (filteredMetrics.length === 0) return 0;

    const sum = filteredMetrics.reduce((acc, m) => acc + m.duration, 0);
    return sum / filteredMetrics.length;
  }

  /**
   * Get all metrics
   */
  getAllMetrics(): {
    screenRenders: ScreenRenderMetric[];
    apiCalls: APICallMetric[];
    custom: PerformanceMetric[];
  } {
    return {
      screenRenders: [...this.screenRenderTimes],
      apiCalls: [...this.apiCallMetrics],
      custom: [...this.metrics],
    };
  }

  getScreenRenderTimes(): ScreenRenderMetric[] {
    const metrics = [...this.screenRenderTimes];
    this.screenRenderTimes = [];
    return metrics;
  }

  getAPICallDurations(): APICallMetric[] {
    const metrics = [...this.apiCallMetrics];
    this.apiCallMetrics = [];
    return metrics;
  }

  /**
   * Get performance summary
   */
  getSummary(): {
    avgScreenRenderTime: number;
    avgAPICallDuration: number;
    slowestScreen: string | null;
    slowestAPI: string | null;
  } {
    const avgScreenRenderTime = this.getAverageScreenRenderTime();
    const avgAPICallDuration = this.getAverageAPICallDuration();

    // Find slowest screen
    let slowestScreen: string | null = null;
    let maxRenderTime = 0;
    this.screenRenderTimes.forEach((metric) => {
      if (metric.renderTime > maxRenderTime) {
        maxRenderTime = metric.renderTime;
        slowestScreen = metric.screen;
      }
    });

    // Find slowest API
    let slowestAPI: string | null = null;
    let maxDuration = 0;
    this.apiCallMetrics.forEach((metric) => {
      if (metric.duration > maxDuration) {
        maxDuration = metric.duration;
        slowestAPI = `${metric.method} ${metric.endpoint}`;
      }
    });

    return {
      avgScreenRenderTime,
      avgAPICallDuration,
      slowestScreen,
      slowestAPI,
    };
  }

  /**
   * Clear all metrics
   */
  clear(): void {
    this.metrics = [];
    this.screenRenderTimes = [];
    this.apiCallMetrics = [];
    this.screenStartTimes.clear();
    this.apiStartTimes.clear();
  }

  /**
   * Log performance summary to console
   */
  logSummary(): void {
    const summary = this.getSummary();
    console.log('=== Performance Summary ===');
    console.log(`Avg Screen Render: ${summary.avgScreenRenderTime.toFixed(2)}ms`);
    console.log(`Avg API Call: ${summary.avgAPICallDuration.toFixed(2)}ms`);
    console.log(`Slowest Screen: ${summary.slowestScreen || 'N/A'}`);
    console.log(`Slowest API: ${summary.slowestAPI || 'N/A'}`);
    console.log('========================');
  }
}

// Export singleton instance
export const performanceMonitoring = new PerformanceMonitoringService();
export default performanceMonitoring;
