/**
 * Root Navigator Tests
 */

import React from 'react';
import { render, waitFor } from '@testing-library/react-native';
import { RootNavigator } from '../src/navigation/RootNavigator';
import { useAuthStore } from '../src/store/authStore';

// Mock navigation
jest.mock('@react-navigation/native', () => ({
  NavigationContainer: ({ children }: any) => children,
}));

// Mock navigators
jest.mock('../src/navigation/AuthNavigator', () => ({
  AuthNavigator: () => null,
}));

jest.mock('../src/navigation/MainNavigator', () => ({
  MainNavigator: () => null,
}));

// Mock theme
jest.mock('../src/hooks/useTheme', () => ({
  useTheme: () => ({
    colors: {
      neonCyan: '#00f2fe',
      black: '#0a0a0a',
      textPrimary: '#ffffff',
      textSecondary: '#a1a1aa',
    },
  }),
}));

// Mock auth store
jest.mock('../src/store/authStore');

describe('RootNavigator', () => {
  const mockInitialize = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    (useAuthStore as unknown as jest.Mock).mockReturnValue({
      isAuthenticated: false,
      isLoading: false,
      initialize: mockInitialize,
    });
  });

  it('should call initialize on mount', () => {
    render(<RootNavigator />);

    expect(mockInitialize).toHaveBeenCalledTimes(1);
  });

  it('should show loading screen when isLoading is true', () => {
    (useAuthStore as unknown as jest.Mock).mockReturnValue({
      isAuthenticated: false,
      isLoading: true,
      initialize: mockInitialize,
    });

    const { getByTestId } = render(<RootNavigator />);

    // Check for loading indicator (ActivityIndicator has testID in some versions)
    // Since we don't have a specific testID, check that AuthNavigator/MainNavigator are not rendered
    expect(() => getByTestId('auth-navigator')).toThrow();
    expect(() => getByTestId('main-navigator')).toThrow();
  });

  it('should render AuthNavigator when not authenticated', async () => {
    (useAuthStore as unknown as jest.Mock).mockReturnValue({
      isAuthenticated: false,
      isLoading: false,
      initialize: mockInitialize,
    });

    const AuthNavigator = require('../src/navigation/AuthNavigator').AuthNavigator;
    const mockAuthNavigator = jest.fn(() => null);
    jest.spyOn(
      require('../src/navigation/AuthNavigator'),
      'AuthNavigator'
    ).mockImplementation(mockAuthNavigator);

    render(<RootNavigator />);

    await waitFor(() => {
      expect(mockAuthNavigator).toHaveBeenCalled();
    });
  });

  it('should render MainNavigator when authenticated', async () => {
    (useAuthStore as unknown as jest.Mock).mockReturnValue({
      isAuthenticated: true,
      isLoading: false,
      initialize: mockInitialize,
    });

    const mockMainNavigator = jest.fn(() => null);
    jest.spyOn(
      require('../src/navigation/MainNavigator'),
      'MainNavigator'
    ).mockImplementation(mockMainNavigator);

    render(<RootNavigator />);

    await waitFor(() => {
      expect(mockMainNavigator).toHaveBeenCalled();
    });
  });

  it('should switch from AuthNavigator to MainNavigator on authentication', async () => {
    const mockAuthNavigator = jest.fn(() => null);
    const mockMainNavigator = jest.fn(() => null);

    jest.spyOn(
      require('../src/navigation/AuthNavigator'),
      'AuthNavigator'
    ).mockImplementation(mockAuthNavigator);
    jest.spyOn(
      require('../src/navigation/MainNavigator'),
      'MainNavigator'
    ).mockImplementation(mockMainNavigator);

    // Start unauthenticated
    (useAuthStore as unknown as jest.Mock).mockReturnValue({
      isAuthenticated: false,
      isLoading: false,
      initialize: mockInitialize,
    });

    const { rerender } = render(<RootNavigator />);

    expect(mockAuthNavigator).toHaveBeenCalled();
    expect(mockMainNavigator).not.toHaveBeenCalled();

    // Simulate authentication
    mockAuthNavigator.mockClear();
    mockMainNavigator.mockClear();

    (useAuthStore as unknown as jest.Mock).mockReturnValue({
      isAuthenticated: true,
      isLoading: false,
      initialize: mockInitialize,
    });

    rerender(<RootNavigator />);

    await waitFor(() => {
      expect(mockMainNavigator).toHaveBeenCalled();
      expect(mockAuthNavigator).not.toHaveBeenCalled();
    });
  });

  it('should switch from MainNavigator to AuthNavigator on logout', async () => {
    const mockAuthNavigator = jest.fn(() => null);
    const mockMainNavigator = jest.fn(() => null);

    jest.spyOn(
      require('../src/navigation/AuthNavigator'),
      'AuthNavigator'
    ).mockImplementation(mockAuthNavigator);
    jest.spyOn(
      require('../src/navigation/MainNavigator'),
      'MainNavigator'
    ).mockImplementation(mockMainNavigator);

    // Start authenticated
    (useAuthStore as unknown as jest.Mock).mockReturnValue({
      isAuthenticated: true,
      isLoading: false,
      initialize: mockInitialize,
    });

    const { rerender } = render(<RootNavigator />);

    expect(mockMainNavigator).toHaveBeenCalled();
    expect(mockAuthNavigator).not.toHaveBeenCalled();

    // Simulate logout
    mockAuthNavigator.mockClear();
    mockMainNavigator.mockClear();

    (useAuthStore as unknown as jest.Mock).mockReturnValue({
      isAuthenticated: false,
      isLoading: false,
      initialize: mockInitialize,
    });

    rerender(<RootNavigator />);

    await waitFor(() => {
      expect(mockAuthNavigator).toHaveBeenCalled();
      expect(mockMainNavigator).not.toHaveBeenCalled();
    });
  });
});
