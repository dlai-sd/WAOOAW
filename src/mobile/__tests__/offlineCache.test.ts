/**
 * Offline Cache Service Tests
 */

import { offlineCache } from '../src/lib/offlineCache';
import AsyncStorage from '@react-native-async-storage/async-storage';

// Mock AsyncStorage
jest.mock('@react-native-async-storage/async-storage', () => ({
  setItem: jest.fn(() => Promise.resolve()),
  getItem: jest.fn(() => Promise.resolve(null)),
  removeItem: jest.fn(() => Promise.resolve()),
  clear: jest.fn(() => Promise.resolve()),
  getAllKeys: jest.fn(() => Promise.resolve([])),
  multiGet: jest.fn(() => Promise.resolve([])),
  multiRemove: jest.fn(() => Promise.resolve()),
}));

describe('Offline Cache Service', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('set', () => {
    it('should cache data with default TTL', async () => {
      const key = 'test-key';
      const data = { id: 1, name: 'Test' };

      await offlineCache.set(key, data);

      expect(AsyncStorage.setItem).toHaveBeenCalledWith(
        `offline:${key}`,
        expect.stringContaining('"id":1')
      );
    });

    it('should cache data with custom TTL', async () => {
      const key = 'test-key';
      const data = { id: 1, name: 'Test' };
      const ttl = 1000 * 60 * 10; // 10 minutes

      await offlineCache.set(key, data, ttl);

      expect(AsyncStorage.setItem).toHaveBeenCalledWith(
        `offline:${key}`,
        expect.stringContaining('"id":1')
      );
    });

    it('should serialize complex objects', async () => {
      const key = 'complex-key';
      const data = {
        id: 1,
        nested: { value: 'test' },
        array: [1, 2, 3],
        date: new Date().toISOString(),
      };

      await offlineCache.set(key, data);

      expect(AsyncStorage.setItem).toHaveBeenCalled();
    });
  });

  describe('get', () => {
    it('should retrieve cached data', async () => {
      const key = 'test-key';
      const data = { id: 1, name: 'Test' };
      const cachedItem = {
        data,
        expiresAt: Date.now() + 1000 * 60 * 60, // 1 hour from now
      };

      (AsyncStorage.getItem as jest.Mock).mockResolvedValueOnce(
        JSON.stringify(cachedItem)
      );

      const result = await offlineCache.get(key);

      expect(result).toEqual(data);
      expect(AsyncStorage.getItem).toHaveBeenCalledWith(`offline:${key}`);
    });

    it('should return null for non-existent key', async () => {
      const key = 'non-existent';

      (AsyncStorage.getItem as jest.Mock).mockResolvedValueOnce(null);

      const result = await offlineCache.get(key);

      expect(result).toBeNull();
    });

    it('should return null for expired data', async () => {
      const key = 'expired-key';
      const data = { id: 1, name: 'Test' };
      const cachedItem = {
        data,
        expiresAt: Date.now() - 1000, // Expired 1 second ago
      };

      (AsyncStorage.getItem as jest.Mock).mockResolvedValueOnce(
        JSON.stringify(cachedItem)
      );

      const result = await offlineCache.get(key);

      expect(result).toBeNull();
      // Should also remove expired item
      expect(AsyncStorage.removeItem).toHaveBeenCalledWith(`offline:${key}`);
    });

    it('should handle corrupted cache data', async () => {
      const key = 'corrupted-key';

      (AsyncStorage.getItem as jest.Mock).mockResolvedValueOnce('invalid json');

      const result = await offlineCache.get(key);

      expect(result).toBeNull();
    });
  });

  describe('remove', () => {
    it('should remove cached item', async () => {
      const key = 'test-key';

      await offlineCache.remove(key);

      expect(AsyncStorage.removeItem).toHaveBeenCalledWith(`offline:${key}`);
    });
  });

  describe('clear', () => {
    it('should clear all cached items', async () => {
      const keys = ['offline:key1', 'offline:key2', 'other:key'];
      
      (AsyncStorage.getAllKeys as jest.Mock).mockResolvedValueOnce(keys);

      await offlineCache.clear();

      expect(AsyncStorage.multiRemove).toHaveBeenCalledWith([
        'offline:key1',
        'offline:key2',
      ]);
    });

    it('should handle empty cache', async () => {
      (AsyncStorage.getAllKeys as jest.Mock).mockResolvedValueOnce([]);

      await offlineCache.clear();

      expect(AsyncStorage.multiRemove).toHaveBeenCalledWith([]);
    });
  });

  describe('pruneExpired', () => {
    it('should remove expired items', async () => {
      const now = Date.now();
      const keys = ['offline:valid', 'offline:expired', 'other:key'];
      
      (AsyncStorage.getAllKeys as jest.Mock).mockResolvedValueOnce(keys);
      (AsyncStorage.multiGet as jest.Mock).mockResolvedValueOnce([
        [
          'offline:valid',
          JSON.stringify({ data: {}, expiresAt: now + 1000 * 60 }),
        ],
        [
          'offline:expired',
          JSON.stringify({ data: {}, expiresAt: now - 1000 }),
        ],
      ]);

      await offlineCache.pruneExpired();

      expect(AsyncStorage.multiRemove).toHaveBeenCalledWith(['offline:expired']);
    });
  });

  describe('getStats', () => {
    it('should return cache statistics', async () => {
      const keys = [
        'offline:key1',
        'offline:key2',
        'offline:key3',
        'other:key',
      ];
      
      (AsyncStorage.getAllKeys as jest.Mock).mockResolvedValueOnce(keys);
      (AsyncStorage.multiGet as jest.Mock).mockResolvedValueOnce([
        ['offline:key1', JSON.stringify({ data: { test: 'a' }, expiresAt: Date.now() + 1000 })],
        ['offline:key2', JSON.stringify({ data: { test: 'bb' }, expiresAt: Date.now() + 1000 })],
        ['offline:key3', JSON.stringify({ data: { test: 'ccc' }, expiresAt: Date.now() - 1000 })],
      ]);

      const stats = await offlineCache.getStats();

      expect(stats.totalItems).toBe(2); // One is expired
      expect(stats.totalSize).toBeGreaterThan(0);
    });
  });
});
