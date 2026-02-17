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

  it('should navigate to Step 2 when "Continue" is pressed in Step 1', async () => {
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
    await waitFor(() => {
      expect(getByText(/Configure your 7-day trial period/)).toBeTruthy();
      expect(getByText('Start Date *')).toBeTruthy();
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

    const { getByText, getByPlaceholderText } = render(<HireWizardScreen />, {
      wrapper: createWrapper(),
    });

    // Go to Step 2
    fireEvent.press(getByText('Continue to Trial Details'));

    await waitFor(() => {
      expect(getByText('Continue to Payment')).toBeTruthy();
    });

    // Fill in form
    fireEvent.changeText(getByPlaceholderText(/YYYY-MM-DD/), '2026-02-20');
    fireEvent.changeText(getByPlaceholderText('What do you want to achieve during the trial?'), 'Test marketing strategies');
    fireEvent.changeText(getByPlaceholderText('What specific deliverables do you expect?'), '3 blog posts and SEO report');

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

    const { getByText, getByPlaceholderText } = render(<HireWizardScreen />, {
      wrapper: createWrapper(),
    });

    // Navigate to Step 3
    fireEvent.press(getByText('Continue to Trial Details'));
    await waitFor(() => {
      expect(getByText('Continue to Payment')).toBeTruthy();
    });
    
    // Fill in form
    fireEvent.changeText(getByPlaceholderText(/YYYY-MM-DD/), '2026-02-20');
    fireEvent.changeText(getByPlaceholderText('What do you want to achieve during the trial?'), 'Test marketing strategies');
    fireEvent.changeText(getByPlaceholderText('What specific deliverables do you expect?'), '3 blog posts and SEO report');
    
    fireEvent.press(getByText('Continue to Payment'));

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

    const { getByText, getByPlaceholderText } = render(<HireWizardScreen />, {
      wrapper: createWrapper(),
    });

    // Navigate to Step 3
    fireEvent.press(getByText('Continue to Trial Details'));
    await waitFor(() => {
      expect(getByText('Continue to Payment')).toBeTruthy();
    });
    
    // Fill form
    fireEvent.changeText(getByPlaceholderText(/YYYY-MM-DD/), '2026-02-20');
    fireEvent.changeText(getByPlaceholderText('What do you want to achieve during the trial?'), 'Test marketing strategies');
    fireEvent.changeText(getByPlaceholderText('What specific deliverables do you expect?'), '3 blog posts and SEO report');
    
    fireEvent.press(getByText('Continue to Payment'));

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

  // Story 2.7 - Trial Details Form Tests
  describe('Trial Details Form (Step 2)', () => {
    it('should display form fields in Step 2', async () => {
      (useAgentDetail as jest.Mock).mockReturnValue({
        data: mockAgent,
        isLoading: false,
        error: null,
        refetch: jest.fn(),
      });

      const { getByText, getByPlaceholderText } = render(<HireWizardScreen />, {
        wrapper: createWrapper(),
      });

      // Navigate to Step 2
      fireEvent.press(getByText('Continue to Trial Details'));

      await waitFor(() => {
        expect(getByText('Start Date *')).toBeTruthy();
        expect(getByText('Trial Goals *')).toBeTruthy();
        expect(getByText('Expected Deliverables *')).toBeTruthy();
      });

      // Verify placeholders
      expect(getByPlaceholderText(/YYYY-MM-DD/)).toBeTruthy();
      expect(getByPlaceholderText('What do you want to achieve during the trial?')).toBeTruthy();
      expect(getByPlaceholderText('What specific deliverables do you expect?')).toBeTruthy();
    });

    it('should show validation errors when fields are empty', async () => {
      (useAgentDetail as jest.Mock).mockReturnValue({
        data: mockAgent,
        isLoading: false,
        error: null,
        refetch: jest.fn(),
      });

      const { getByText } = render(<HireWizardScreen />, {
        wrapper: createWrapper(),
      });

      // Navigate to Step 2
      fireEvent.press(getByText('Continue to Trial Details'));

      await waitFor(() => {
        expect(getByText('Continue to Payment')).toBeTruthy();
      });

      // Try to continue without filling form
      fireEvent.press(getByText('Continue to Payment'));

      // Verify validation errors
      await waitFor(() => {
        expect(getByText('Start date is required')).toBeTruthy();
        expect(getByText('Trial goals are required')).toBeTruthy();
        expect(getByText('Expected deliverables are required')).toBeTruthy();
      });
    });

    it('should show validation error for short goals text', async () => {
      (useAgentDetail as jest.Mock).mockReturnValue({
        data: mockAgent,
        isLoading: false,
        error: null,
        refetch: jest.fn(),
      });

      const { getByText, getByPlaceholderText } = render(<HireWizardScreen />, {
        wrapper: createWrapper(),
      });

      // Navigate to Step 2
      fireEvent.press(getByText('Continue to Trial Details'));

      await waitFor(() => {
        expect(getByText('Continue to Payment')).toBeTruthy();
      });

      // Fill in short text
      const startDateInput = getByPlaceholderText(/YYYY-MM-DD/);
      const goalsInput = getByPlaceholderText('What do you want to achieve during the trial?');
      const deliverablesInput = getByPlaceholderText('What specific deliverables do you expect?');

      fireEvent.changeText(startDateInput, '2026-02-20');
      fireEvent.changeText(goalsInput, 'Test');
      fireEvent.changeText(deliverablesInput, 'Short');

      // Try to continue
      fireEvent.press(getByText('Continue to Payment'));

      // Verify validation errors
      await waitFor(() => {
        expect(getByText('Please provide more detailed goals (at least 10 characters)')).toBeTruthy();
        expect(getByText('Please provide more details (at least 10 characters)')).toBeTruthy();
      });
    });

    it('should accept valid form data and navigate to Step 3', async () => {
      (useAgentDetail as jest.Mock).mockReturnValue({
        data: mockAgent,
        isLoading: false,
        error: null,
        refetch: jest.fn(),
      });

      const { getByText, getByPlaceholderText } = render(<HireWizardScreen />, {
        wrapper: createWrapper(),
      });

      // Navigate to Step 2
      fireEvent.press(getByText('Continue to Trial Details'));

      await waitFor(() => {
        expect(getByText('Continue to Payment')).toBeTruthy();
      });

      // Fill in valid data
      const startDateInput = getByPlaceholderText(/YYYY-MM-DD/);
      const goalsInput = getByPlaceholderText('What do you want to achieve during the trial?');
      const deliverablesInput = getByPlaceholderText('What specific deliverables do you expect?');

      fireEvent.changeText(startDateInput, '2026-02-20');
      fireEvent.changeText(goalsInput, 'Test content marketing strategies for our product launch');
      fireEvent.changeText(deliverablesInput, '3 blog posts, 5 social media campaigns, SEO audit report');

      // Continue to Step 3
      fireEvent.press(getByText('Continue to Payment'));

      // Verify navigation to Step 3
      await waitFor(() => {
        expect(getByText('Payment Details')).toBeTruthy();
      });
    });

    it('should clear error when user starts typing', async () => {
      (useAgentDetail as jest.Mock).mockReturnValue({
        data: mockAgent,
        isLoading: false,
        error: null,
        refetch: jest.fn(),
      });

      const { getByText, getByPlaceholderText, queryByText } = render(<HireWizardScreen />, {
        wrapper: createWrapper(),
      });

      // Navigate to Step 2
      fireEvent.press(getByText('Continue to Trial Details'));

      await waitFor(() => {
        expect(getByText('Continue to Payment')).toBeTruthy();
      });

      // Try to continue without filling (to show error)
      fireEvent.press(getByText('Continue to Payment'));

      await waitFor(() => {
        expect(getByText('Start date is required')).toBeTruthy();
      });

      // Start typing in the field
      const startDateInput = getByPlaceholderText(/YYYY-MM-DD/);
      fireEvent.changeText(startDateInput, '2026-02-20');

      // Error should be cleared
      await waitFor(() => {
        expect(queryByText('Start date is required')).toBeNull();
      });
    });

    it('should preserve form data when going back and forth between steps', async () => {
      (useAgentDetail as jest.Mock).mockReturnValue({
        data: mockAgent,
        isLoading: false,
        error: null,
        refetch: jest.fn(),
      });

      const { getByText, getByPlaceholderText } = render(<HireWizardScreen />, {
        wrapper: createWrapper(),
      });

      // Navigate to Step 2
      fireEvent.press(getByText('Continue to Trial Details'));

      await waitFor(() => {
        expect(getByText('Continue to Payment')).toBeTruthy();
      });

      // Fill in form
      const startDateInput = getByPlaceholderText(/YYYY-MM-DD/);
      const goalsInput = getByPlaceholderText('What do you want to achieve during the trial?');

      fireEvent.changeText(startDateInput, '2026-02-20');
      fireEvent.changeText(goalsInput, 'Test our marketing strategies');

      // Go back to Step 1
      fireEvent.press(getByText('Back'));

      await waitFor(() => {
        expect(getByText('Confirm Agent Selection')).toBeTruthy();
      });

      // Go forward to Step 2 again
      fireEvent.press(getByText('Continue to Trial Details'));

      await waitFor(() => {
        expect(getByText('Continue to Payment')).toBeTruthy();
      });

      // Verify form data is preserved
      const startDateInputAgain = getByPlaceholderText(/YYYY-MM-DD/);
      expect(startDateInputAgain.props.value).toBe('2026-02-20');
    });

    it('should display field hints below inputs', async () => {
      (useAgentDetail as jest.Mock).mockReturnValue({
        data: mockAgent,
        isLoading: false,
        error: null,
        refetch: jest.fn(),
      });

      const { getByText } = render(<HireWizardScreen />, {
        wrapper: createWrapper(),
      });

      // Navigate to Step 2
      fireEvent.press(getByText('Continue to Trial Details'));

      await waitFor(() => {
        expect(getByText(/When would you like to start the trial/)).toBeTruthy();
        expect(getByText(/Describe your objectives for the 7-day trial period/)).toBeTruthy();
        expect(getByText(/List the outputs you expect at the end of the trial/)).toBeTruthy();
      });
    });
  });

  describe('Payment Form (Step 3)', () => {
    it('should display payment form fields in Step 3', async () => {
      (useAgentDetail as jest.Mock).mockReturnValue({
        data: mockAgent,
        isLoading: false,
        error: null,
        refetch: jest.fn(),
      });

      const { getByText, getByPlaceholderText } = render(<HireWizardScreen />, {
        wrapper: createWrapper(),
      });

      // Navigate to Step 2
      fireEvent.press(getByText('Continue to Trial Details'));

      await waitFor(() => {
        expect(getByText('Continue to Payment')).toBeTruthy();
      });

      // Fill trial form
      fireEvent.changeText(getByPlaceholderText(/YYYY-MM-DD/), '2026-02-20');
      fireEvent.changeText(getByPlaceholderText('What do you want to achieve during the trial?'), 'Test marketing strategies');
      fireEvent.changeText(getByPlaceholderText('What specific deliverables do you expect?'), '3 blog posts and SEO report');

      // Navigate to Step 3
      fireEvent.press(getByText('Continue to Payment'));

      await waitFor(() => {
        expect(getByText('Payment Details')).toBeTruthy();
        expect(getByText('Pricing Summary')).toBeTruthy();
        expect(getByText('Billing Information')).toBeTruthy();
        expect(getByText('Payment Method')).toBeTruthy();
        expect(getByPlaceholderText('John Doe')).toBeTruthy();
        expect(getByPlaceholderText('john@example.com')).toBeTruthy();
        expect(getByPlaceholderText('9876543210')).toBeTruthy();
      });
    });

    it('should show validation errors when payment fields are empty', async () => {
      (useAgentDetail as jest.Mock).mockReturnValue({
        data: mockAgent,
        isLoading: false,
        error: null,
        refetch: jest.fn(),
      });

      const { getByText, getByPlaceholderText } = render(<HireWizardScreen />, {
        wrapper: createWrapper(),
      });

      // Navigate to Step 3
      fireEvent.press(getByText('Continue to Trial Details'));
      
      await waitFor(() => {
        expect(getByText('Continue to Payment')).toBeTruthy();
      });

      // Fill trial form
      fireEvent.changeText(getByPlaceholderText(/YYYY-MM-DD/), '2026-02-20');
      fireEvent.changeText(getByPlaceholderText('What do you want to achieve during the trial?'), 'Test marketing strategies');
      fireEvent.changeText(getByPlaceholderText('What specific deliverables do you expect?'), '3 blog posts and SEO report');

      fireEvent.press(getByText('Continue to Payment'));

      await waitFor(() => {
        expect(getByText('Start Trial')).toBeTruthy();
      });

      // Try to submit empty form
      fireEvent.press(getByText('Start Trial'));

      await waitFor(() => {
        expect(getByText('Full name is required')).toBeTruthy();
        expect(getByText('Email is required')).toBeTruthy();
        expect(getByText('Phone number is required')).toBeTruthy();
        expect(getByText('Please select a payment method')).toBeTruthy();
        expect(getByText('You must accept the terms and conditions')).toBeTruthy();
      });
    });

    it('should show validation error for invalid email format', async () => {
      (useAgentDetail as jest.Mock).mockReturnValue({
        data: mockAgent,
        isLoading: false,
        error: null,
        refetch: jest.fn(),
      });

      const { getByText, getByPlaceholderText } = render(<HireWizardScreen />, {
        wrapper: createWrapper(),
      });

      // Navigate to Step 3
      fireEvent.press(getByText('Continue to Trial Details'));
      
      await waitFor(() => {
        expect(getByText('Continue to Payment')).toBeTruthy();
      });

      // Fill trial form
      fireEvent.changeText(getByPlaceholderText(/YYYY-MM-DD/), '2026-02-20');
      fireEvent.changeText(getByPlaceholderText('What do you want to achieve during the trial?'), 'Test marketing strategies');
      fireEvent.changeText(getByPlaceholderText('What specific deliverables do you expect?'), '3 blog posts and SEO report');

      fireEvent.press(getByText('Continue to Payment'));

      await waitFor(() => {
        expect(getByText('Start Trial')).toBeTruthy();
      });

      // Fill with invalid email
      fireEvent.changeText(getByPlaceholderText('John Doe'), 'John Doe');
      fireEvent.changeText(getByPlaceholderText('john@example.com'), 'invalid-email');
      fireEvent.changeText(getByPlaceholderText('9876543210'), '1234567890');

      fireEvent.press(getByText('Start Trial'));

      await waitFor(() => {
        expect(getByText('Please enter a valid email address')).toBeTruthy();
      });
    });

    it('should show validation error for invalid phone number', async () => {
      (useAgentDetail as jest.Mock).mockReturnValue({
        data: mockAgent,
        isLoading: false,
        error: null,
        refetch: jest.fn(),
      });

      const { getByText, getByPlaceholderText } = render(<HireWizardScreen />, {
        wrapper: createWrapper(),
      });

      // Navigate to Step 3
      fireEvent.press(getByText('Continue to Trial Details'));
      
      await waitFor(() => {
        expect(getByText('Continue to Payment')).toBeTruthy();
      });

      // Fill trial form
      fireEvent.changeText(getByPlaceholderText(/YYYY-MM-DD/), '2026-02-20');
      fireEvent.changeText(getByPlaceholderText('What do you want to achieve during the trial?'), 'Test marketing strategies');
      fireEvent.changeText(getByPlaceholderText('What specific deliverables do you expect?'), '3 blog posts and SEO report');

      fireEvent.press(getByText('Continue to Payment'));

      await waitFor(() => {
        expect(getByText('Start Trial')).toBeTruthy();
      });

      // Fill with invalid phone
      fireEvent.changeText(getByPlaceholderText('John Doe'), 'John Doe');
      fireEvent.changeText(getByPlaceholderText('john@example.com'), 'john@example.com');
      fireEvent.changeText(getByPlaceholderText('9876543210'), '123');

      fireEvent.press(getByText('Start Trial'));

      await waitFor(() => {
        expect(getByText('Please enter a valid 10-digit phone number')).toBeTruthy();
      });
    });

    it('should allow selecting payment method', async () => {
      (useAgentDetail as jest.Mock).mockReturnValue({
        data: mockAgent,
        isLoading: false,
        error: null,
        refetch: jest.fn(),
      });

      const { getByText, getByPlaceholderText } = render(<HireWizardScreen />, {
        wrapper: createWrapper(),
      });

      // Navigate to Step 3
      fireEvent.press(getByText('Continue to Trial Details'));
      
      await waitFor(() => {
        expect(getByText('Continue to Payment')).toBeTruthy();
      });

      // Fill trial form
      fireEvent.changeText(getByPlaceholderText(/YYYY-MM-DD/), '2026-02-20');
      fireEvent.changeText(getByPlaceholderText('What do you want to achieve during the trial?'), 'Test marketing strategies');
      fireEvent.changeText(getByPlaceholderText('What specific deliverables do you expect?'), '3 blog posts and SEO report');

      fireEvent.press(getByText('Continue to Payment'));

      await waitFor(() => {
        expect(getByText('Credit / Debit Card')).toBeTruthy();
        expect(getByText('UPI')).toBeTruthy();
        expect(getByText('Net Banking')).toBeTruthy();
      });

      // Select UPI
      fireEvent.press(getByText('UPI'));

      // Form should not show payment method error after selection
      fireEvent.press(getByText('Start Trial'));

      await waitFor(() => {
        // Should see other errors but not payment method error
        expect(getByText('Full name is required')).toBeTruthy();
      });
    });

    it('should allow accepting terms and conditions', async () => {
      (useAgentDetail as jest.Mock).mockReturnValue({
        data: mockAgent,
        isLoading: false,
        error: null,
        refetch: jest.fn(),
      });

      const { getByText, getByPlaceholderText } = render(<HireWizardScreen />, {
        wrapper: createWrapper(),
      });

      // Navigate to Step 3
      fireEvent.press(getByText('Continue to Trial Details'));
      
      await waitFor(() => {
        expect(getByText('Continue to Payment')).toBeTruthy();
      });

      // Fill trial form
      fireEvent.changeText(getByPlaceholderText(/YYYY-MM-DD/), '2026-02-20');
      fireEvent.changeText(getByPlaceholderText('What do you want to achieve during the trial?'), 'Test marketing strategies');
      fireEvent.changeText(getByPlaceholderText('What specific deliverables do you expect?'), '3 blog posts and SEO report');

      fireEvent.press(getByText('Continue to Payment'));

      await waitFor(() => {
        expect(getByText(/I accept the/)).toBeTruthy();
      });

      // Click terms checkbox
      fireEvent.press(getByText(/I accept the/));

      // Should not show terms error after accepting
      fireEvent.press(getByText('Start Trial'));

      await waitFor(() => {
        expect(getByText('Full name is required')).toBeTruthy();
      });
    });

    it('should display pricing summary correctly', async () => {
      (useAgentDetail as jest.Mock).mockReturnValue({
        data: mockAgent,
        isLoading: false,
        error: null,
        refetch: jest.fn(),
      });

      const { getByText, getByPlaceholderText } = render(<HireWizardScreen />, {
        wrapper: createWrapper(),
      });

      // Navigate to Step 3
      fireEvent.press(getByText('Continue to Trial Details'));
      
      await waitFor(() => {
        expect(getByText('Continue to Payment')).toBeTruthy();
      });

      // Fill trial form
      fireEvent.changeText(getByPlaceholderText(/YYYY-MM-DD/), '2026-02-20');
      fireEvent.changeText(getByPlaceholderText('What do you want to achieve during the trial?'), 'Test marketing strategies');
      fireEvent.changeText(getByPlaceholderText('What specific deliverables do you expect?'), '3 blog posts and SEO report');

      fireEvent.press(getByText('Continue to Payment'));

      await waitFor(() => {
        expect(getByText('Pricing Summary')).toBeTruthy();
        expect(getByText('Monthly Rate')).toBeTruthy();
        expect(getByText('₹15,000')).toBeTruthy();
        expect(getByText('Trial Period')).toBeTruthy();
        expect(getByText('7 days FREE')).toBeTruthy();
        expect(getByText('Due Today')).toBeTruthy();
        expect(getByText('₹0')).toBeTruthy();
      });
    });

    it('should complete hire wizard with valid payment data', async () => {
      (useAgentDetail as jest.Mock).mockReturnValue({
        data: mockAgent,
        isLoading: false,
        error: null,
        refetch: jest.fn(),
      });

      const { getByText, getByPlaceholderText } = render(<HireWizardScreen />, {
        wrapper: createWrapper(),
      });

      // Navigate to Step 2
      fireEvent.press(getByText('Continue to Trial Details'));
      
      await waitFor(() => {
        expect(getByText('Continue to Payment')).toBeTruthy();
      });

      // Fill trial form
      fireEvent.changeText(getByPlaceholderText(/YYYY-MM-DD/), '2026-02-20');
      fireEvent.changeText(getByPlaceholderText('What do you want to achieve during the trial?'), 'Test marketing strategies');
      fireEvent.changeText(getByPlaceholderText('What specific deliverables do you expect?'), '3 blog posts and SEO report');

      fireEvent.press(getByText('Continue to Payment'));

      await waitFor(() => {
        expect(getByText('Start Trial')).toBeTruthy();
      });

      // Fill payment form
      fireEvent.changeText(getByPlaceholderText('John Doe'), 'John Doe');
      fireEvent.changeText(getByPlaceholderText('john@example.com'), 'john@example.com');
      fireEvent.changeText(getByPlaceholderText('9876543210'), '9876543210');
      
      // Select payment method
      fireEvent.press(getByText('UPI'));
      
      // Accept terms
      fireEvent.press(getByText(/I accept the/));

      // Submit
      fireEvent.press(getByText('Start Trial'));

      // Verify navigation to confirmation
      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith('HireConfirmation', {
          agentId: 'agent-123',
          trialData: {
            startDate: '2026-02-20',
            goals: 'Test marketing strategies',
            deliverables: '3 blog posts and SEO report',
          },
          paymentData: {
            fullName: 'John Doe',
            email: 'john@example.com',
            phone: '9876543210',
            paymentMethod: 'upi',
            acceptedTerms: true,
          },
        });
      });
    });

    it('should clear errors when user starts typing in payment fields', async () => {
      (useAgentDetail as jest.Mock).mockReturnValue({
        data: mockAgent,
        isLoading: false,
        error: null,
        refetch: jest.fn(),
      });

      const { getByText, getByPlaceholderText, queryByText } = render(<HireWizardScreen />, {
        wrapper: createWrapper(),
      });

      // Navigate to Step 3
      fireEvent.press(getByText('Continue to Trial Details'));
      
      await waitFor(() => {
        expect(getByText('Continue to Payment')).toBeTruthy();
      });

      // Fill trial form
      fireEvent.changeText(getByPlaceholderText(/YYYY-MM-DD/), '2026-02-20');
      fireEvent.changeText(getByPlaceholderText('What do you want to achieve during the trial?'), 'Test marketing strategies');
      fireEvent.changeText(getByPlaceholderText('What specific deliverables do you expect?'), '3 blog posts and SEO report');

      fireEvent.press(getByText('Continue to Payment'));

      await waitFor(() => {
        expect(getByText('Start Trial')).toBeTruthy();
      });

      // Try to submit empty form
      fireEvent.press(getByText('Start Trial'));

      await waitFor(() => {
        expect(getByText('Full name is required')).toBeTruthy();
      });

      // Start typing in name field
      fireEvent.changeText(getByPlaceholderText('John Doe'), 'J');

      // Error should be cleared
      await waitFor(() => {
        expect(queryByText('Full name is required')).toBeNull();
      });
    });
  });
});
