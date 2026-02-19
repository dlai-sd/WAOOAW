/**
 * Network Status Service
 * Detects and monitors network connectivity
 * 
 * Features:
 * - Online/offline detection
 * - Network type detection (wifi, cellular, etc.)
 * - Connection quality monitoring
 * - Event listeners for connectivity changes
 */

import NetInfo, {
  NetInfoState,
  NetInfoSubscription,
} from '@react-native-community/netinfo';

export type NetworkType = 'wifi' | 'cellular' | 'ethernet' | 'bluetooth' | 'unknown' | 'none';
export type ConnectionQuality = 'excellent' | 'good' | 'poor' | 'offline';

export interface NetworkStatus {
  isConnected: boolean;
  isInternetReachable: boolean | null;
  type: NetworkType;
  quality: ConnectionQuality;
}

type NetworkChangeCallback = (status: NetworkStatus) => void;

class NetworkStatusService {
  private currentStatus: NetworkStatus = {
    isConnected: false,
    isInternetReachable: null,
    type: 'unknown',
    quality: 'offline',
  };
  private listeners: NetworkChangeCallback[] = [];
  private subscription: NetInfoSubscription | null = null;

  constructor() {
    this.initialize();
  }

  /**
   * Initialize network monitoring
   */
  private async initialize(): Promise<void> {
    // Get initial state
    const state = await NetInfo.fetch();
    this.updateStatus(state);

    // Subscribe to network state changes
    this.subscription = NetInfo.addEventListener((state) => {
      this.updateStatus(state);
    });
  }

  /**
   * Update network status from NetInfo state
   */
  private updateStatus(state: NetInfoState): void {
    const previousStatus = { ...this.currentStatus };

    this.currentStatus = {
      isConnected: state.isConnected ?? false,
      isInternetReachable: state.isInternetReachable,
      type: this.mapNetworkType(state.type),
      quality: this.determineQuality(state),
    };

    // Notify listeners if status changed
    if (this.hasStatusChanged(previousStatus, this.currentStatus)) {
      this.notifyListeners();
    }
  }

  /**
   * Map NetInfo type to our NetworkType
   */
  private mapNetworkType(type: string): NetworkType {
    switch (type) {
      case 'wifi':
        return 'wifi';
      case 'cellular':
        return 'cellular';
      case 'ethernet':
        return 'ethernet';
      case 'bluetooth':
        return 'bluetooth';
      case 'none':
        return 'none';
      default:
        return 'unknown';
    }
  }

  /**
   * Determine connection quality
   */
  private determineQuality(state: NetInfoState): ConnectionQuality {
    if (!state.isConnected) {
      return 'offline';
    }

    // Check if internet is reachable
    if (state.isInternetReachable === false) {
      return 'poor';
    }

    // Determine quality based on connection details
    if (state.type === 'wifi') {
      return 'excellent';
    }

    if (state.type === 'cellular') {
      // Check cellular generation if available
      const details = state.details as any;
      if (details?.cellularGeneration) {
        const generation = details.cellularGeneration;
        if (generation === '5g') return 'excellent';
        if (generation === '4g') return 'good';
        return 'poor';
      }
      return 'good';
    }

    return 'good';
  }

  /**
   * Check if status has changed
   */
  private hasStatusChanged(prev: NetworkStatus, current: NetworkStatus): boolean {
    return (
      prev.isConnected !== current.isConnected ||
      prev.isInternetReachable !== current.isInternetReachable ||
      prev.type !== current.type ||
      prev.quality !== current.quality
    );
  }

  /**
   * Notify all listeners
   */
  private notifyListeners(): void {
    this.listeners.forEach((callback) => {
      try {
        callback(this.currentStatus);
      } catch (error) {
        console.error('Error in network status listener:', error);
      }
    });
  }

  /**
   * Get current network status
   */
  getStatus(): NetworkStatus {
    return { ...this.currentStatus };
  }

  /**
   * Check if online
   */
  isOnline(): boolean {
    return this.currentStatus.isConnected && this.currentStatus.isInternetReachable !== false;
  }

  /**
   * Check if offline
   */
  isOffline(): boolean {
    return !this.isOnline();
  }

  /**
   * Get network type
   */
  getNetworkType(): NetworkType {
    return this.currentStatus.type;
  }

  /**
   * Get connection quality
   */
  getQuality(): ConnectionQuality {
    return this.currentStatus.quality;
  }

  /**
   * Add listener for network changes
   */
  addListener(callback: NetworkChangeCallback): () => void {
    this.listeners.push(callback);

    // Return unsubscribe function
    return () => {
      const index = this.listeners.indexOf(callback);
      if (index > -1) {
        this.listeners.splice(index, 1);
      }
    };
  }

  /**
   * Remove all listeners
   */
  removeAllListeners(): void {
    this.listeners = [];
  }

  /**
   * Refresh network status
   */
  async refresh(): Promise<NetworkStatus> {
    const state = await NetInfo.fetch();
    this.updateStatus(state);
    return this.getStatus();
  }

  /**
   * Cleanup resources
   */
  destroy(): void {
    if (this.subscription) {
      this.subscription();
      this.subscription = null;
    }
    this.removeAllListeners();
  }
}

// Export singleton instance
export const networkStatus = new NetworkStatusService();
export default networkStatus;
