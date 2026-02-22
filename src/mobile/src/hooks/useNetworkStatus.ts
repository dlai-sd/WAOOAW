/**
 * useNetworkStatus Hook
 * React hook for monitoring network connectivity
 */

import { useState, useEffect } from 'react';
import { networkStatus, NetworkStatus } from '../lib/networkStatus';

export function useNetworkStatus(): NetworkStatus & {
  isOnline: boolean;
  isOffline: boolean;
  refresh: () => Promise<NetworkStatus>;
} {
  const [status, setStatus] = useState<NetworkStatus>(networkStatus.getStatus());

  useEffect(() => {
    // Subscribe to network status  changes
    const unsubscribe = networkStatus.addListener((newStatus) => {
      setStatus(newStatus);
    });

    // Initial fetch
    networkStatus.refresh();

    return () => {
      unsubscribe();
    };
  }, []);

  return {
    ...status,
    isOnline: networkStatus.isOnline(),
    isOffline: networkStatus.isOffline(),
    refresh: networkStatus.refresh.bind(networkStatus),
  };
}
