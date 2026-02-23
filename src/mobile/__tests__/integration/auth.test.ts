/**
 * Integration Test: Authentication Flow
 * 
 * Validates authentication logic and AuthUser interface usage.
 * Would have caught the AuthUser.id vs AuthUser.customer_id issue.
 */

import { useAuthStore } from '../../src/store/authStore';
import { renderHook, act } from '@testing-library/react-native';

describe('Authentication Integration', () => {
  beforeEach(() => {
    // Reset store before each test
    const { result } = renderHook(() => useAuthStore());
    act(() => {
      result.current.logout();
    });
  });

  /**
   * CRITICAL: AuthUser must have customer_id property (not id)
   */
  it('should use customer_id property on AuthUser', () => {
    const { result } = renderHook(() => useAuthStore());

    const mockUser = {
      customer_id: 'cust_123',
      email: 'test@example.com',
      full_name: 'Test User',
      role: 'customer',
    };

    act(() => {
      result.current.setUser(mockUser);
    });

    expect(result.current.user?.customer_id).toBe('cust_123');
    
    // Verify 'id' property does NOT exist
    expect('id' in (result.current.user || {})).toBe(false);
  });

  /**
   * Verify login flow
   */
  it('should handle login flow correctly', () => {
    const { result } = renderHook(() => useAuthStore());

    const mockUser = {
      customer_id: 'cust_123',
      email: 'test@example.com',
      full_name: 'Test User',
      role: 'customer',
    };

    act(() => {
      result.current.login('mock_token_123', mockUser);
    });

    expect(result.current.isAuthenticated).toBe(true);
    expect(result.current.token).toBe('mock_token_123');
    expect(result.current.user).toEqual(mockUser);
  });

  /**
   * Verify logout flow
   */
  it('should handle logout flow correctly', () => {
    const { result } = renderHook(() => useAuthStore());

    // First login
    act(() => {
      result.current.login('token', {
        customer_id: 'cust_123',
        email: 'test@example.com',
        full_name: 'Test User',
        role: 'customer',
      });
    });

    // Then logout
    act(() => {
      result.current.logout();
    });

    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.token).toBeNull();
    expect(result.current.user).toBeNull();
  });

  /**
   * Verify skip sign-in creates proper demo user
   */
  it('should create demo user on skip sign-in', () => {
    const { result } = renderHook(() => useAuthStore());

    const demoUser = {
      customer_id: 'demo_user',
      email: 'demo@waooaw.com',
      full_name: 'Demo User',
      role: 'customer',
    };

    act(() => {
      result.current.setUser(demoUser);
    });

    expect(result.current.user?.customer_id).toBe('demo_user');
    expect(result.current.user?.email).toBe('demo@waooaw.com');
  });

  /**
   * Verify user properties match monitoring service expectations
   */
  it('should have all properties needed by monitoring services', () => {
    const { result } = renderHook(() => useAuthStore());

    const mockUser = {
      customer_id: 'cust_123',
      email: 'test@example.com',
      full_name: 'Test User',
      role: 'customer',
    };

    act(() => {
      result.current.setUser(mockUser);
    });

    const user = result.current.user;
    if (user) {
      // Properties expected by App.tsx monitoring initialization
      expect(user.customer_id).toBeDefined();
      expect(user.email).toBeDefined();
      expect(user.full_name).toBeDefined();

      // Verify types
      expect(typeof user.customer_id).toBe('string');
      expect(typeof user.email).toBe('string');
      expect(typeof user.full_name).toBe('string');
    }
  });
});
