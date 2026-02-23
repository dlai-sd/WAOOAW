/**
 * Auth Store Tests
 */

import { renderHook, act, waitFor } from '@testing-library/react-native';
import { useAuthStore } from '../src/store/authStore';
import TokenManagerService from '../src/services/TokenManagerService';
import userDataService from '../src/services/userDataService';

// Mock dependencies
jest.mock('../src/services/TokenManagerService');
jest.mock('../src/services/userDataService');

describe('authStore', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    // Reset store to initial state
    useAuthStore.setState({
      isAuthenticated: false,
      user: null,
      isLoading: true,
    });
  });

  describe('initial state', () => {
    it('should have correct initial values', () => {
      const { result } = renderHook(() => useAuthStore());

      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.user).toBeNull();
      expect(result.current.isLoading).toBe(true);
    });
  });

  describe('login', () => {
    it('should set user and authenticated state', () => {
      const { result } = renderHook(() => useAuthStore());

      const mockUser = {
        customer_id: 'CUST-123',
        email: 'test@example.com',
        full_name: 'Test User',
        phone: '+919876543210',
      };

      act(() => {
        result.current.login(mockUser);
      });

      expect(result.current.isAuthenticated).toBe(true);
      expect(result.current.user).toEqual(mockUser);
      expect(result.current.isLoading).toBe(false);
    });
  });

  describe('logout', () => {
    it('should clear tokens, user data, and reset state', async () => {
      const { result } = renderHook(() => useAuthStore());

      // Set up authenticated state
      act(() => {
        result.current.login({
          customer_id: 'CUST-123',
          email: 'test@example.com',
        });
      });

      // Mock successful clearing
      (TokenManagerService.clearTokens as jest.Mock).mockResolvedValue(undefined);
      (userDataService.clearUserData as jest.Mock).mockResolvedValue(undefined);

      // Logout
      await act(async () => {
        await result.current.logout();
      });

      expect(TokenManagerService.clearTokens).toHaveBeenCalled();
      expect(userDataService.clearUserData).toHaveBeenCalled();
      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.user).toBeNull();
      expect(result.current.isLoading).toBe(false);
    });

    it('should reset state even if clearing fails', async () => {
      const { result } = renderHook(() => useAuthStore());

      // Set up authenticated state
      act(() => {
        result.current.login({
          customer_id: 'CUST-123',
          email: 'test@example.com',
        });
      });

      // Mock clearing failure
      (TokenManagerService.clearTokens as jest.Mock).mockRejectedValue(
        new Error('Clear failed')
      );

      // Logout should still work
      await act(async () => {
        await result.current.logout();
      });

      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.user).toBeNull();
    });
  });

  describe('updateUser', () => {
    it('should update user data and persist to storage', async () => {
      const { result } = renderHook(() => useAuthStore());

      const mockUser = {
        customer_id: 'CUST-123',
        email: 'test@example.com',
        full_name: 'Test User',
      };

      (userDataService.saveUserData as jest.Mock).mockResolvedValue(undefined);

      // Set initial user
      act(() => {
        result.current.login(mockUser);
      });

      // Update user
      act(() => {
        result.current.updateUser({
          full_name: 'Updated Name',
          phone: '+919876543210',
        });
      });

      // Wait for async persistence
      await waitFor(() => {
        expect(result.current.user).toEqual({
          ...mockUser,
          full_name: 'Updated Name',
          phone: '+919876543210',
        });
      });

      expect(userDataService.saveUserData).toHaveBeenCalledWith({
        ...mockUser,
        full_name: 'Updated Name',
        phone: '+919876543210',
      });
    });

    it('should not update if user is null', () => {
      const { result } = renderHook(() => useAuthStore());

      act(() => {
        result.current.updateUser({ full_name: 'Test' });
      });

      expect(result.current.user).toBeNull();
      expect(userDataService.saveUserData).not.toHaveBeenCalled();
    });

    it('should continue even if persistence fails', async () => {
      const { result } = renderHook(() => useAuthStore());

      const mockUser = {
        customer_id: 'CUST-123',
        email: 'test@example.com',
      };

      (userDataService.saveUserData as jest.Mock).mockRejectedValue(
        new Error('Save failed')
      );

      act(() => {
        result.current.login(mockUser);
      });

      act(() => {
        result.current.updateUser({ full_name: 'Updated' });
      });

      // User should still be updated in memory
      expect(result.current.user?.full_name).toBe('Updated');
    });
  });

  describe('initialize', () => {
    it('should set authenticated state when tokens and user data exist', async () => {
      const { result } = renderHook(() => useAuthStore());

      const mockUser = {
        customer_id: 'CUST-123',
        email: 'test@example.com',
        full_name: 'Test User',
      };

      (TokenManagerService.getAccessToken as jest.Mock).mockResolvedValue('token-123');
      (userDataService.getUserData as jest.Mock).mockResolvedValue(mockUser);

      await act(async () => {
        await result.current.initialize();
      });

      expect(result.current.isAuthenticated).toBe(true);
      expect(result.current.user).toEqual(mockUser);
      expect(result.current.isLoading).toBe(false);
    });

    it('should set unauthenticated state when no tokens exist', async () => {
      const { result } = renderHook(() => useAuthStore());

      (TokenManagerService.getAccessToken as jest.Mock).mockResolvedValue(null);

      await act(async () => {
        await result.current.initialize();
      });

      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.user).toBeNull();
      expect(result.current.isLoading).toBe(false);
    });

    it('should clear tokens and logout when tokens exist but no user data', async () => {
      const { result } = renderHook(() => useAuthStore());

      (TokenManagerService.getAccessToken as jest.Mock).mockResolvedValue('token-123');
      (userDataService.getUserData as jest.Mock).mockResolvedValue(null);
      (TokenManagerService.clearTokens as jest.Mock).mockResolvedValue(undefined);

      await act(async () => {
        await result.current.initialize();
      });

      expect(TokenManagerService.clearTokens).toHaveBeenCalled();
      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.user).toBeNull();
      expect(result.current.isLoading).toBe(false);
    });

    it('should clear tokens when user data is missing customer_id', async () => {
      const { result } = renderHook(() => useAuthStore());

      (TokenManagerService.getAccessToken as jest.Mock).mockResolvedValue('token-123');
      (userDataService.getUserData as jest.Mock).mockResolvedValue({
        email: 'test@example.com',
        // Missing customer_id
      });
      (TokenManagerService.clearTokens as jest.Mock).mockResolvedValue(undefined);

      await act(async () => {
        await result.current.initialize();
      });

      expect(TokenManagerService.clearTokens).toHaveBeenCalled();
      expect(result.current.isAuthenticated).toBe(false);
    });

    it('should handle initialization errors gracefully', async () => {
      const { result } = renderHook(() => useAuthStore());

      (TokenManagerService.getAccessToken as jest.Mock).mockRejectedValue(
        new Error('Token error')
      );

      await act(async () => {
        await result.current.initialize();
      });

      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.user).toBeNull();
      expect(result.current.isLoading).toBe(false);
    });
  });

  // Test hooks
  describe('hooks', () => {
    it('useIsAuthenticated should return authentication status', () => {
      const { result: storeResult } = renderHook(() => useAuthStore());
      const { result: hookResult } = renderHook(() =>
        useAuthStore((state) => state.isAuthenticated)
      );

      expect(hookResult.current).toBe(false);

      act(() => {
        storeResult.current.login({
          customer_id: 'CUST-123',
          email: 'test@example.com',
        });
      });

      expect(hookResult.current).toBe(true);
    });

    it('useCurrentUser should return current user', () => {
      const { result: storeResult } = renderHook(() => useAuthStore());
      const { result: hookResult } = renderHook(() =>
        useAuthStore((state) => state.user)
      );

      expect(hookResult.current).toBeNull();

      const mockUser = {
        customer_id: 'CUST-123',
        email: 'test@example.com',
      };

      act(() => {
        storeResult.current.login(mockUser);
      });

      expect(hookResult.current).toEqual(mockUser);
    });

    it('useAuthLoading should return loading status', () => {
      const { result } = renderHook(() =>
        useAuthStore((state) => state.isLoading)
      );

      // Initial state is loading
      expect(result.current).toBe(true);
    });
  });
});
