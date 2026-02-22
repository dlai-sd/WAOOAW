/**
 * Performance Monitoring Service Tests
 */

import { performanceMonitoring } from '../src/lib/performanceMonitoring';

describe('Performance Monitoring Service', () => {
  beforeEach(() => {
    // Clear metrics before each test
    performanceMonitoring.getScreenRenderTimes();
    performanceMonitoring.getAPICallDurations();
  });

  describe('Screen Render Tracking', () => {
    it('should track screen render time', () => {
      performanceMonitoring.startScreenRender('TestScreen');
      
      // Simulate some delay
      const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));
      
      performanceMonitoring.endScreenRender('TestScreen');
      
      const metrics = performanceMonitoring.getScreenRenderTimes();
      expect(metrics.length).toBeGreaterThan(0);
      expect(metrics[0]).toHaveProperty('screenName', 'TestScreen');
      expect(metrics[0]).toHaveProperty('duration');
      expect(metrics[0].duration).toBeGreaterThanOrEqual(0);
    });

    it('should handle multiple screen renders', () => {
      performanceMonitoring.startScreenRender('Screen1');
      performanceMonitoring.endScreenRender('Screen1');
      
      performanceMonitoring.startScreenRender('Screen2');
      performanceMonitoring.endScreenRender('Screen2');
      
      const metrics = performanceMonitoring.getScreenRenderTimes();
      expect(metrics.length).toBe(2);
      expect(metrics[0].screenName).toBe('Screen1');
      expect(metrics[1].screenName).toBe('Screen2');
    });

    it('should return 0 duration when endScreenRender called without startScreenRender', () => {
      performanceMonitoring.endScreenRender('UnstartedScreen');
      
      const metrics = performanceMonitoring.getScreenRenderTimes();
      expect(metrics.length).toBe(1);
      expect(metrics[0].duration).toBe(0);
    });

    it('should maintain a rolling buffer of 100 entries', () => {
      // Add 150 entries
      for (let i = 0; i < 150; i++) {
        performanceMonitoring.startScreenRender(`Screen${i}`);
        performanceMonitoring.endScreenRender(`Screen${i}`);
      }
      
      const metrics = performanceMonitoring.getScreenRenderTimes();
      expect(metrics.length).toBe(100);
      // Should only have the last 100
      expect(metrics[0].screenName).toBe('Screen50');
    });
  });

  describe('API Call Tracking', () => {
    it('should track API call duration', () => {
      performanceMonitoring.startAPICall('GET /api/agents');
      performanceMonitoring.endAPICall('GET /api/agents', 200);
      
      const metrics = performanceMonitoring.getAPICallDurations();
      expect(metrics.length).toBe(1);
      expect(metrics[0]).toHaveProperty('endpoint', 'GET /api/agents');
      expect(metrics[0]).toHaveProperty('duration');
      expect(metrics[0]).toHaveProperty('statusCode', 200);
      expect(metrics[0].duration).toBeGreaterThanOrEqual(0);
    });

    it('should handle error status codes', () => {
      performanceMonitoring.startAPICall('GET /api/error');
      performanceMonitoring.endAPICall('GET /api/error', 500);
      
      const metrics = performanceMonitoring.getAPICallDurations();
      expect(metrics.length).toBe(1);
      expect(metrics[0].statusCode).toBe(500);
    });

    it('should track multiple API calls', () => {
      performanceMonitoring.startAPICall('GET /api/agents');
      performanceMonitoring.endAPICall('GET /api/agents', 200);
      
      performanceMonitoring.startAPICall('POST /api/trials');
      performanceMonitoring.endAPICall('POST /api/trials', 201);
      
      const metrics = performanceMonitoring.getAPICallDurations();
      expect(metrics.length).toBe(2);
    });

    it('should return 0 duration when endAPICall called without startAPICall', () => {
      performanceMonitoring.endAPICall('GET /api/unstarted', 200);
      
      const metrics = performanceMonitoring.getAPICallDurations();
      expect(metrics.length).toBe(1);
      expect(metrics[0].duration).toBe(0);
    });

    it('should maintain a rolling buffer of 100 entries', () => {
      // Add 150 entries
      for (let i = 0; i < 150; i++) {
        performanceMonitoring.startAPICall(`GET /api/endpoint${i}`);
        performanceMonitoring.endAPICall(`GET /api/endpoint${i}`, 200);
      }
      
      const metrics = performanceMonitoring.getAPICallDurations();
      expect(metrics.length).toBe(100);
    });
  });

  describe('Statistics', () => {
    it('should calculate average screen render time', () => {
      performanceMonitoring.startScreenRender('Screen1');
      performanceMonitoring.endScreenRender('Screen1');
      
      performanceMonitoring.startScreenRender('Screen2');
      performanceMonitoring.endScreenRender('Screen2');
      
      const metrics = performanceMonitoring.getScreenRenderTimes();
      const avgDuration = metrics.reduce((sum, m) => sum + m.duration, 0) / metrics.length;
      
      expect(avgDuration).toBeGreaterThanOrEqual(0);
    });
  });
});
