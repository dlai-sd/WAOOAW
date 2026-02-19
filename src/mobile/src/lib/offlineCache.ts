/**
 * Offline Cache Service
 * Manages offline data caching for API responses
 * Works with React Query for seamless offline experience
 * 
 * Features:
 * - Persistent cache storage
 * - TTL (time-to-live) support
 * - Cache invalidation
 * - Size limits
 */

import AsyncStorage from '@react-native-async-storage/async-storage';

interface CacheEntry<T> {
  data: T;
  timestamp: number;
  ttl?: number; // Time to live in milliseconds
}

interface CacheOptions {
  ttl?: number;  // Default TTL in milliseconds
  maxSize?: number; // Maximum cache size in bytes
}

const DEFAULT_TTL = 1000 * 60 * 60; // 1 hour
const DEFAULT_MAX_SIZE = 1024 * 1024 * 10; // 10 MB
const CACHE_PREFIX = '@waooaw_cache:';

class OfflineCacheService {
  private ttl: number;
  private maxSize: number;

  constructor(options: CacheOptions = {}) {
    this.ttl = options.ttl || DEFAULT_TTL;
    this.maxSize = options.maxSize || DEFAULT_MAX_SIZE;
  }

  /**
   * Generate cache key
   */
  private getCacheKey(key: string): string {
    return `${CACHE_PREFIX}${key}`;
  }

  /**
   * Set cache entry
   */
  async set<T>(key: string, data: T, ttl?: number): Promise<void> {
    try {
      const entry: CacheEntry<T> = {
        data,
        timestamp: Date.now(),
        ttl: ttl || this.ttl,
      };

      const cacheKey = this.getCacheKey(key);
      await AsyncStorage.setItem(cacheKey, JSON.stringify(entry));
    } catch (error) {
      console.error(`Failed to set cache for key: ${key}`, error);
    }
  }

  /**
   * Get cache entry
   */
  async get<T>(key: string): Promise<T | null> {
    try {
      const cacheKey = this.getCacheKey(key);
      const item = await AsyncStorage.getItem(cacheKey);

      if (!item) {
        return null;
      }

      const entry: CacheEntry<T> = JSON.parse(item);

      // Check if entry has expired
      if (this.isExpired(entry)) {
        await this.remove(key);
        return null;
      }

      return entry.data;
    } catch (error) {
      console.error(`Failed to get cache for key: ${key}`, error);
      return null;
    }
  }

  /**
   * Check if cache entry has expired
   */
  private isExpired<T>(entry: CacheEntry<T>): boolean {
    if (!entry.ttl) {
      return false;
    }

    const now = Date.now();
    const age = now - entry.timestamp;
    return age > entry.ttl;
  }

  /**
   * Remove cache entry
   */
  async remove(key: string): Promise<void> {
    try {
      const cacheKey = this.getCacheKey(key);
      await AsyncStorage.removeItem(cacheKey);
    } catch (error) {
      console.error(`Failed to remove cache for key: ${key}`, error);
    }
  }

  /**
   * Clear all cache entries
   */
  async clear(): Promise<void> {
    try {
      const keys = await AsyncStorage.getAllKeys();
      const cacheKeys = keys.filter((key) => key.startsWith(CACHE_PREFIX));
      await AsyncStorage.multiRemove(cacheKeys);
    } catch (error) {
      console.error('Failed to clear cache:', error);
    }
  }

  /**
   * Get all cache keys
   */
  async getAllKeys(): Promise<string[]> {
    try {
      const keys = await AsyncStorage.getAllKeys();
      return keys
        .filter((key) => key.startsWith(CACHE_PREFIX))
        .map((key) => key.replace(CACHE_PREFIX, ''));
    } catch (error) {
      console.error('Failed to get cache keys:', error);
      return [];
    }
  }

  /**
   * Get cache size
   */
  async getSize(): Promise<number> {
    try {
      const keys = await AsyncStorage.getAllKeys();
      const cacheKeys = keys.filter((key) => key.startsWith(CACHE_PREFIX));

      if (cacheKeys.length === 0) {
        return 0;
      }

      const items = await AsyncStorage.multiGet(cacheKeys);
      const totalSize = items.reduce((sum, [_, value]) => {
        return sum + (value ? new TextEncoder().encode(value).length : 0);
      }, 0);

      return totalSize;
    } catch (error) {
      console.error('Failed to calculate cache size:', error);
      return 0;
    }
  }

  /**
   * Check if cache has key
   */
  async has(key: string): Promise<boolean> {
    try {
      const data = await this.get(key);
      return data !== null;
    } catch (error) {
      return false;
    }
  }

  /**
   * Prune expired entries
   */
  async pruneExpired(): Promise<number> {
    try {
      const keys = await this.getAllKeys();
      let prunedCount = 0;

      for (const key of keys) {
        const cacheKey = this.getCacheKey(key);
        const item = await AsyncStorage.getItem(cacheKey);

        if (item) {
          const entry: CacheEntry<unknown> = JSON.parse(item);
          if (this.isExpired(entry)) {
            await this.remove(key);
            prunedCount++;
          }
        }
      }

      return prunedCount;
    } catch (error) {
      console.error('Failed to prune expired entries:', error);
      return 0;
    }
  }

  /**
   * Get cache statistics
   */
  async getStats(): Promise<{
    totalKeys: number;
    totalSize: number;
    maxSize: number;
    utilizationPercent: number;
  }> {
    const totalKeys = (await this.getAllKeys()).length;
    const totalSize = await this.getSize();
    const utilizationPercent = (totalSize / this.maxSize) * 100;

    return {
      totalKeys,
      totalSize,
      maxSize: this.maxSize,
      utilizationPercent,
    };
  }
}

// Export singleton instance
export const offlineCache = new OfflineCacheService();
export default offlineCache;
