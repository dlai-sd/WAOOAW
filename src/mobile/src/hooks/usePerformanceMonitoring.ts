/**
 * usePerformanceMonitoring Hook
 * React hook for tracking component performance
 */

import { useEffect, useRef } from 'react';
import { performanceMonitoring } from '../lib/performanceMonitoring';

export function usePerformanceMonitoring(screenName: string): void {
  const mountTime = useRef(Date.now());

  useEffect(() => {
    // Track screen render start
    performanceMonitoring.startScreenRender(screenName);

    return () => {
      // Track screen render end
      performanceMonitoring.endScreenRender(screenName);

      // Log screen lifetime in dev mode
      if (__DEV__) {
        const lifetime = Date.now() - mountTime.current;
        console.log(`[Performance] ${screenName} lifetime: ${lifetime}ms`);
      }
    };
  }, [screenName]);
}

/**
 * useAPIPerformance Hook
 * Track API call performance
 */
export function useAPIPerformance(): {
  startTracking: (endpoint: string, method: string) => string;
  endTracking: (callId: string, status: number) => void;
} {
  const startTracking = (endpoint: string, method: string = 'GET'): string => {
    return performanceMonitoring.startAPICall(endpoint, method);
  };

  const endTracking = (callId: string, status: number): void => {
    performanceMonitoring.endAPICall(callId, status);
  };

  return {
    startTracking,
    endTracking,
  };
}
