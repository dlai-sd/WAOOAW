/**
 * Hire Wizard Screen Tests (Story 2.6)
 */

import React from 'react';
import { describe, it, expect, jest, beforeEach } from '@jest/globals';
import { render, fireEvent, waitFor } from '@testing-library/react-native';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { HireWizardScreen } from '@/screens/hire/HireWizardScreen';
import { useAgentDetail } from '@/hooks/useAgentDetail';
import type { Agent } from '@/types/agent.types';

// Mock useAgentDetail hook
jest.mock('@/hooks/useAgentDetail');

// Mock components
jest.mock('@/components/LoadingSpinner', () => ({
  LoadingSpinner: ({ message }: { message?: string }) => {
    const React = require('react');
    const { Text } = require('react-native');
    return React.createElement(Text, {}, message || 'Loading...');
  },
}));

jest.mock('@/components/ErrorView', () => ({
  ErrorView: ({ message, onRetry }: { message: string; onRetry?: () => void }) => {
    const React = require('react');
    const { View, Text, TouchableOpacity } = require('react-native');
    return React.createElement(
      View,
      {},
      React.createElement(Text, {}, 'Oops! An error occurred'),
      React.createElement(Text, {}, message),
      onRetry && React.createElement(TouchableOpacity, { onPress: onRetry }, React.createElement(Text, {}, 'Try Again'))
    );
  },
}));

// Mock useTheme
jest.mock('@/hooks/useTheme', () => ({
  useTheme: () => ({
    colors: {
      black: '#0a0a0a',
      card: '#18181b',
      textPrimary: '#ffffff',
      textSecondary: '#a1a1aa',
      neonCyan: '#00f2fe',
    },
    spacing: {
      xs: 4,
      sm: 8,
      md: 16,
      lg: 24,
      xl: 32,
      screenPadding: 20,
    },
    typography: {
      fontFamily: {
        display: 'SpaceGrotesk_700Bold',
        displayBold: 'SpaceGrotesk_700Bold',
        body: 'Inter_400Regular',
        bodyBold: 'Inter_600SemiBold',
      },
    },
  }),
}));

// Mock navigation
const mockNavigate = jest.fn();
const mockGoBack = jest.fn();
jest.mock('@react-navigation/native', () => ({
  useNavigation: () => ({
    navigate: mockNavigate,
    goBack: mockGoBack,
  }),
  useRoute: () => ({
    params: { agentId: 'agent-123' },
  }),
}));

// Helper to create QueryClient wrapper
const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
};

describe('HireWizardScreen Component', () => {
  const mockAgent: Agent = {
    id: 'agent-123',
    name: 'Marketing Expert Agent',
    description: 'Specialized in content marketing and SEO.',
    specialization: 'Content Marketing & SEO Specialist',
    job_role_id: 'role-1',
    industry: 'marketing',
    entity_type: 'agent',
    status: 'active',
    created_at: '2024-01-01T00:00:00Z',
    rating: 4.7,
    price: 15000,
    trial_days: 7,
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should display loading spinner initially', () => {
    (useAgentDetail as jest.Mock).mockReturnValue({
      data: undefined,
      isLoading: true,
      error: null,
      refetch: jest.fn(),
    });

    const { getByText } = render(<HireWizardScreen />, {
      wrapper: createWrapper(),
    });

    expect(getByText('Loading agent details...')).toBeTruthy();
  });

  it('should display error view when API fails', () => {
    const mockError = new Error('Failed to fetch agent');
    (useAgentDetail as jest.Mock).mockReturnValue({
      data: undefined,
      isLoading: false,
      error: mockError,
      refetch: jest.fn(),
    });

    const { getByText } = render(<HireWizardScreen />, {
      wrapper: createWrapper(),
    });

    expect(getByText('Oops! An error occurred')).toBeTruthy();
    expect(getByText('Failed to fetch agent')).toBeTruthy();
  });

  it('should display Step 1 by default', () => {
    (useAgentDetail as jest.Mock).mockReturnValue({
      data: mockAgent,
      isLoading: false,
      error: null,
      refetch: jest.fn(),
    });

    const { getByText } = render(<HireWizardScreen />, {
      wrapper: createWrapper(),
    });

    expect(getByText('Confirm Agent Selection')).toBeTruthy();
    expect(getByText('Marketing Expert Agent')).toBeTruthy();
    expect(getByText('Content Marketing & SEO Specialist')).toBeTruthy();
  });

  it('should display progress indicator with 3 steps', () => {
    (useAgentDetail as jest.Mock).mockReturnValue({
      data: mockAgent,
      isLoading: false,
      error: null,
      refetch: jest.fn(),
    });

    const { getByText } = render(<HireWizardScreen />, {
      wrapper: createWrapper(),
    });

    expect(getByText('Confirm')).toBeTruthy();
    expect(getByText('Trial Details')).toBeTruthy();
    expect(getByText('Payment')).toBeTruthy();
  });

  it('should display agent information in Step 1', () => {
    (useAgentDetail as jest.Mock).mockReturnValue({
      data: mockAgent,
      isLoading: false,
      error: null,
      refetch: jest.fn(),
    });

    const { getByText } = render(<HireWizardScreen />, {
      wrapper: createWrapper(),
    });

    // Agent info
    expect(getByText('Marketing Expert Agent')).toBeTruthy();
    expect(getByText('Content Marketing & SEO Specialist')).toBeTruthy();
    expect(getByText('marketing')).toBeTruthy();

    // Pricing
    expect(getByText('Monthly Rate')).toBeTruthy();
    expect(getByText('₹15,000')).toBeTruthy();

    // Trial info
    expect(getByText(/7-day free trial/)).toBeTruthy();
  });

  it('should display "What happens next?" section in Step 1', () => {
    (useAgentDetail as jest.Mock).mockReturnValue({
      data: mockAgent,
      isLoading: false,
      error: null,
      refetch: jest.fn(),
    });

    const { getByText } = render(<HireWizardScreen />, {
      wrapper: createWrapper(),
    });

    expect(getByText('What happens next?')).toBeTruthy();
    expect(getByText(/Configure your trial period/)).toBeTruthy();
    expect(getByText(/Add payment method/)).toBeTruthy();
    expect(getByText(/Agent starts working immediately/)).toBeTruthy();
  });

  it('should navigate to Step 2 when "Continue" is pressed in Step 1', () => {
    (useAgentDetail as jest.Mock).mockReturnValue({
      data: mockAgent,
      isLoading: false,
      error: null,
      refetch: jest.fn(),
    });

    const { getByText } = render(<HireWizardScreen />, {
      wrapper: createWrapper(),
    });

    const continueButton = getByText('Continue to Trial Details');
    fireEvent.press(continueButton);

    // Should now be on Step 2
    waitFor(() => {
      expect(getByText('Trial Details')).toBeTruthy();
      expect(getByText(/Configure your 7-day trial period/)).toBeTruthy();
    });
  });

  it('should go back when "Cancel" is pressed in Step 1', () => {
    (useAgentDetail as jest.Mock).mockReturnValue({
      data: mockAgent,
      isLoading: false,
      error: null,
      refetch: jest.fn(),
    });

    const { getByText } = render(<HireWizardScreen />, {
      wrapper: createWrapper(),
    });

    const cancelButton = getByText('Cancel');
    fireEvent.press(cancelButton);

    expect(mockGoBack).toHaveBeenCalledTimes(1);
  });

  it('should display Step 2 after navigation from Step 1', async () => {
    (useAgentDetail as jest.Mock).mockReturnValue({
      data: mockAgent,
      isLoading: false,
      error: null,
      refetch: jest.fn(),
    });

    const { getByText } = render(<HireWizardScreen />, {
      wrapper: createWrapper(),
    });

    // Click Continue in Step 1
    const continueButton = getByText('Continue to Trial Details');
    fireEvent.press(continueButton);

    // Verify Step 2 content
    await waitFor(() => {
      expect(getByText(/Configure your 7-day trial period/)).toBeTruthy();
      expect(getByText('Continue to Payment')).toBeTruthy();
    });
  });

  it('should go back to Step 1 when "Back" is pressed in Step 2', async () => {
    (useAgentDetail as jest.Mock).mockReturnValue({
      data: mockAgent,
      isLoading: false,
      error: null,
      refetch: jest.fn(),
    });

    const { getByText } = render(<HireWizardScreen />, {
      wrapper: createWrapper(),
    });

    // Go to Step 2
    const continueButton = getByText('Continue to Trial Details');
    fireEvent.press(continueButton);

    await waitFor(() => {
      expect(getByText('Continue to Payment')).toBeTruthy();
    });

    // Press Back
    const backButton = getByText('Back');
    fireEvent.press(backButton);

    // Verify back to Step 1
    await waitFor(() => {
      expect(getByText('Confirm Agent Selection')).toBeTruthy();
    });
  });

  it('should navigate to Step 3 when "Continue" is pressed in Step 2', async () => {
    (useAgentDetail as jest.Mock).mockReturnValue({
      data: mockAgent,
      isLoading: false,
      error: null,
      refetch: jest.fn(),
    });

    const { getByText } = render(<HireWizardScreen />, {
      wrapper: createWrapper(),
    });

    // Go to Step 2
    fireEvent.press(getByText('Continue to Trial Details'));

    await waitFor(() => {
      expect(getByText('Continue to Payment')).toBeTruthy();
    });

    // Go to Step 3
    fireEvent.press(getByText('Continue to Payment'));

    await waitFor(() => {
      expect(getByText('Payment Details')).toBeTruthy();
      expect(getByText(/Add a payment method/)).toBeTruthy();
    });
  });

  it('should display payment security info in Step 3', async () => {
    (useAgentDetail as jest.Mock).mockReturnValue({
      data: mockAgent,
      isLoading: false,
      error: null,
      refetch: jest.fn(),
    });

    const { getByText } = render(<HireWizardScreen />, {
      wrapper: createWrapper(),
    });

    // Navigate to Step 3
    fireEvent.press(getByText('Continue to Trial Details'));
    await waitFor(() => {
      fireEvent.press(getByText('Continue to Payment'));
    });

    // Verify security info
    await waitFor(() => {
      expect(getByText(/Your payment information is secure/)).toBeTruthy();
      expect(getByText(/won't be charged until after your 7-day trial/)).toBeTruthy();
    });
  });

  it('should go back to Step 2 when "Back" is pressed in Step 3', async () => {
    (useAgentDetail as jest.Mock).mockReturnValue({
      data: mockAgent,
      isLoading: false,
      error: null,
      refetch: jest.fn(),
    });

    const { getByText } = render(<HireWizardScreen />, {
      wrapper: createWrapper(),
    });

    // Navigate to Step 3
    fireEvent.press(getByText('Continue to Trial Details'));
    await waitFor(() => {
      fireEvent.press(getByText('Continue to Payment'));
    });

    await waitFor(() => {
      expect(getByText('Start Trial')).toBeTruthy();
    });

    // Press Back
    const backButton = getByText('Back');
    fireEvent.press(backButton);

    // Verify back to Step 2
    await waitFor(() => {
      expect(getByText('Continue to Payment')).toBeTruthy();
    });
  });

  it('should navigate to confirmation when "Start Trial" is pressed in Step 3', async () => {
    (useAgentDetail as jest.Mock).mockReturnValue({
      data: mockAgent,
      isLoading: false,
      error: null,
      refetch: jest.fn(),
    });

    const { getByText } = render(<HireWizardScreen />, {
      wrapper: createWrapper(),
    });

    // Navigate to Step 3
    fireEvent.press(getByText('Continue to Trial Details'));
    await waitFor(() => {
      fireEvent.press(getByText('Continue to Payment'));
    });

    await waitFor(() => {
      expect(getByText('Start Trial')).toBeTruthy();
    });

    // Press Start Trial
    fireEvent.press(getByText('Start Trial'));

    // Verify navigation to confirmation
    expect(mockNavigate).toHaveBeenCalledWith('HireConfirmation', { agentId: 'agent-123' });
  });

  it('should display custom trial days when specified', () => {
    const agentWithCustomTrial = { ...mockAgent, trial_days: 14 };
    (useAgentDetail as jest.Mock).mockReturnValue({
      data: agentWithCustomTrial,
      isLoading: false,
      error: null,
      refetch: jest.fn(),
    });

    const { getByText } = render(<HireWizardScreen />, {
      wrapper: createWrapper(),
    });

    expect(getByText(/14-day free trial/)).toBeTruthy();
  });

  it('should call refetch on retry button press', () => {
    const mockRefetch = jest.fn();
    const mockError = new Error('Network error');
    (useAgentDetail as jest.Mock).mockReturnValue({
      data: undefined,
      isLoading: false,
      error: mockError,
      refetch: mockRefetch,
    });

    const { getByText } = render(<HireWizardScreen />, {
      wrapper: createWrapper(),
    });

    const retryButton = getByText('Try Again');
    fireEvent.press(retryButton);

    expect(mockRefetch).toHaveBeenCalledTimes(1);
  });
});
