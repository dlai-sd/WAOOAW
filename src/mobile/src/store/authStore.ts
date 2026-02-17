/**
 * Authentication Store
 * 
 * Zustand store for managing authentication state
 */

import { create } from 'zustand';
import TokenManagerService from '../services/TokenManagerService';
import userDataService from '../services/userDataService';

export interface AuthUser {
  customer_id: string;
  email: string;
  full_name?: string;
  phone?: string;
  business_name?: string;
}

interface AuthState {
  // State
  isAuthenticated: boolean;
  user: AuthUser | null;
  isLoading: boolean;

  // Actions
  login: (user: AuthUser) => void;
  logout: () => Promise<void>;
  updateUser: (user: Partial<AuthUser>) => void;
  initialize: () => Promise<void>;
}

/**
 * Auth Store
 * 
 * Manages authentication state across the app.
 * Syncs with TokenManagerService and userDataService.
 */
export const useAuthStore = create<AuthState>((set) => ({
  // Initial state
  isAuthenticated: false,
  user: null,
  isLoading: true,

  /**
   * Login user
   * Sets authenticated state and stores user data
   */
  login: (user: AuthUser) => {
    set({
      isAuthenticated: true,
      user,
      isLoading: false,
    });
  },

  /**
   * Logout user
   * Clears tokens, user data, and resets auth state
   */
  logout: async () => {
    try {
      // Clear tokens
      await TokenManagerService.clearTokens();
      
      // Clear user data
      await userDataService.clearUserData();
      
      // Reset state
      set({
        isAuthenticated: false,
        user: null,
        isLoading: false,
      });
    } catch (error) {
      console.error('Logout error:', error);
      // Still reset state even if clearing fails
      set({
        isAuthenticated: false,
        user: null,
        isLoading: false,
      });
    }
  },

  /**
   * Update user data
   * Partially updates user object and persists to storage
   */
  updateUser: (updates: Partial<AuthUser>) => {
    set((state) => {
      if (!state.user) return state;

      const updatedUser = { ...state.user, ...updates };
      
      // Persist to storage
      userDataService.saveUserData(updatedUser).catch((error) => {
        console.error('Failed to persist user data:', error);
      });

      return {
        user: updatedUser,
      };
    });
  },

  /**
   * Initialize auth state
   * Checks for existing tokens and loads user data
   * Call this on app startup
   */
  initialize: async () => {
    try {
      set({ isLoading: true });

      // Check if tokens exist
      const hasTokens = await TokenManagerService.getAccessToken();
      
      if (!hasTokens) {
        set({
          isAuthenticated: false,
          user: null,
          isLoading: false,
        });
        return;
      }

      // Load user data
      const userData = await userDataService.getUserData();
      
      if (!userData || !userData.customer_id) {
        // Tokens exist but no user data - clear tokens and logout
        await TokenManagerService.clearTokens();
        set({
          isAuthenticated: false,
          user: null,
          isLoading: false,
        });
        return;
      }

      // Valid session found
      set({
        isAuthenticated: true,
        user: userData,
        isLoading: false,
      });
    } catch (error) {
      console.error('Auth initialization error:', error);
      // On error, assume not authenticated
      set({
        isAuthenticated: false,
        user: null,
        isLoading: false,
      });
    }
  },
}));

/**
 * Hook to check if user is authenticated
 */
export const useIsAuthenticated = () =>
  useAuthStore((state) => state.isAuthenticated);

/**
 * Hook to get current user
 */
export const useCurrentUser = () =>
  useAuthStore((state) => state.user);

/**
 * Hook to check if auth is loading
 */
export const useAuthLoading = () =>
  useAuthStore((state) => state.isLoading);
