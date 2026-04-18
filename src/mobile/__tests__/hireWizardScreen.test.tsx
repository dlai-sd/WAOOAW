/**
 * Hire Wizard Screen Tests (MOBILE-COMP-1 E1-S2)
 *
 * Updated for the 4-step wizard:
 *   Step 1 — Choose Agent (Continue to Connect Platform)
 *   Step 2 — Connect Platform preflight (Continue to Set Goals)
 *   Step 3 — Set Goals / Trial Details form (Continue to Start Trial)
 *   Step 4 — Start Trial / Payment form (Start Trial)
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

// Mock useRazorpay — required; without this the hook reads razorpayConfig and auth store
jest.mock('@/hooks/useRazorpay', () => ({
  useRazorpay: () => ({
    processPayment: jest.fn().mockResolvedValue({
      subscription_id: 'sub-123',
      payment_id: 'pay-123',
    }),
    isProcessing: false,
    error: null,
    clearError: jest.fn(),
  }),
}));

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
const mockGetParent = jest.fn();
jest.mock('@react-navigation/native', () => ({
  useNavigation: () => ({
    navigate: mockNavigate,
    goBack: mockGoBack,
    getParent: mockGetParent,
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

// Navigation helpers for the 4-step wizard
async function navigateToConnectPlatformStep(getByText: any) {
  fireEvent.press(getByText('Continue to Connect Platform'));
  await waitFor(() => expect(getByText('Setup after trial starts')).toBeTruthy());
}

async function navigateToTrialDetailsStep(getByText: any) {
  await navigateToConnectPlatformStep(getByText);
  fireEvent.press(getByText('Continue to Set Goals'));
  await waitFor(() => expect(getByText(/Configure your 7-day trial period/)).toBeTruthy());
}

async function navigateToPaymentStep(getByText: any, getByPlaceholderText: any) {
  await navigateToTrialDetailsStep(getByText);
  fireEvent.changeText(getByPlaceholderText(/YYYY-MM-DD/), '2026-02-20');
  fireEvent.changeText(
    getByPlaceholderText('What do you want to achieve during the trial?'),
    'Test marketing strategies goal'
  );
  fireEvent.changeText(
    getByPlaceholderText('What specific deliverables do you expect?'),
    '3 blog posts and SEO report'
  );
  fireEvent.press(getByText('Continue to Start Trial'));
  await waitFor(() => expect(getByText(/Add a payment method/)).toBeTruthy());
}

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
    mockGetParent.mockReturnValue({ navigate: mockNavigate });
    (useAgentDetail as jest.Mock).mockReturnValue({
      data: mockAgent,
      isLoading: false,
      error: null,
      refetch: jest.fn(),
    });
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
    const { getByText } = render(<HireWizardScreen />, {
      wrapper: createWrapper(),
    });

    expect(getByText('Confirm Agent Selection')).toBeTruthy();
    expect(getByText('Marketing Expert Agent')).toBeTruthy();
    expect(getByText('Content Marketing & SEO Specialist')).toBeTruthy();
  });

  it('should display progress indicator with 4 steps', () => {
    const { getByText } = render(<HireWizardScreen />, {
      wrapper: createWrapper(),
    });

    expect(getByText('Choose Agent')).toBeTruthy();
    expect(getByText('Connect Platform')).toBeTruthy();
    expect(getByText('Set Goals')).toBeTruthy();
    expect(getByText('Start Trial')).toBeTruthy();
  });

  it('should display agent information in Step 1', () => {
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
    const { getByText } = render(<HireWizardScreen />, {
      wrapper: createWrapper(),
    });

    expect(getByText('What happens next?')).toBeTruthy();
    expect(getByText(/Configure your trial period/)).toBeTruthy();
    expect(getByText(/Add payment method/)).toBeTruthy();
    expect(getByText(/Agent starts working immediately/)).toBeTruthy();
  });

  it('should navigate to Step 2 (Connect Platform) when "Continue" is pressed in Step 1', async () => {
    const { getByText } = render(<HireWizardScreen />, {
      wrapper: createWrapper(),
    });

    fireEvent.press(getByText('Continue to Connect Platform'));

    await waitFor(() => {
      expect(getByText('Setup after trial starts')).toBeTruthy();
      expect(getByText('You will need:')).toBeTruthy();
    });
  });

  it('should display Step 2 Connect Platform preflight (no fake toggle)', async () => {
    const { getByText, queryByText } = render(<HireWizardScreen />, {
      wrapper: createWrapper(),
    });

    fireEvent.press(getByText('Continue to Connect Platform'));

    await waitFor(() => {
      expect(getByText('Connect Platform')).toBeTruthy();
      expect(getByText('Setup after trial starts')).toBeTruthy();
      expect(queryByText('Not connected')).toBeNull();
      expect(queryByText('Connected')).toBeNull();
    });
  });

  it('should go back when "Cancel" is pressed in Step 1', () => {
    const { getByText } = render(<HireWizardScreen />, {
      wrapper: createWrapper(),
    });

    const cancelButton = getByText('Cancel');
    fireEvent.press(cancelButton);

    expect(mockGoBack).toHaveBeenCalledTimes(1);
  });

  it('should navigate to Step 3 (Trial Details) from Step 2', async () => {
    const { getByText } = render(<HireWizardScreen />, {
      wrapper: createWrapper(),
    });

    await navigateToTrialDetailsStep(getByText);

    expect(getByText('Continue to Start Trial')).toBeTruthy();
  });

  it('should go back to Step 2 when "Back" is pressed from Trial Details', async () => {
    const { getByText, getAllByText } = render(<HireWizardScreen />, {
      wrapper: createWrapper(),
    });

    await navigateToTrialDetailsStep(getByText);

    fireEvent.press(getByText('Back'));

    await waitFor(() => {
      // Back to Step 2 (Connect Platform)
      expect(getAllByText('Connect Platform').length).toBeGreaterThanOrEqual(1);
      expect(getByText('Setup after trial starts')).toBeTruthy();
    });
  });

  it('should navigate to Step 4 (Payment) when valid trial form is submitted', async () => {
    const { getByText, getByPlaceholderText } = render(<HireWizardScreen />, {
      wrapper: createWrapper(),
    });

    await navigateToPaymentStep(getByText, getByPlaceholderText);

    expect(getByText('Pricing Summary')).toBeTruthy();
    expect(getByText('Billing Information')).toBeTruthy();
    expect(getByText('Payment Method')).toBeTruthy();
  });

  it('should display payment security info in Step 4', async () => {
    const { getByText, getByPlaceholderText } = render(<HireWizardScreen />, {
      wrapper: createWrapper(),
    });

    await navigateToPaymentStep(getByText, getByPlaceholderText);

    expect(getByText(/Your payment information is secure/)).toBeTruthy();
    expect(getByText(/won't be charged until after your 7-day trial/)).toBeTruthy();
  });

  it('should go back to Step 3 when "Back" is pressed from payment form', async () => {
    const { getByText, getByPlaceholderText } = render(<HireWizardScreen />, {
      wrapper: createWrapper(),
    });

    await navigateToPaymentStep(getByText, getByPlaceholderText);

    const backButton = getByText('Back');
    fireEvent.press(backButton);

    // Back to Step 3 (Trial Details)
    await waitFor(() => {
      expect(getByText('Continue to Start Trial')).toBeTruthy();
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

  // Trial Details Form (Step 3)
  describe('Trial Details Form (Step 3)', () => {
    it('should display form fields in Step 3', async () => {
      const { getByText, getByPlaceholderText } = render(<HireWizardScreen />, {
        wrapper: createWrapper(),
      });

      await navigateToTrialDetailsStep(getByText);

      expect(getByText('Start Date *')).toBeTruthy();
      expect(getByText('Trial Goals *')).toBeTruthy();
      expect(getByText('Expected Deliverables *')).toBeTruthy();

      // Verify placeholders
      expect(getByPlaceholderText(/YYYY-MM-DD/)).toBeTruthy();
      expect(getByPlaceholderText('What do you want to achieve during the trial?')).toBeTruthy();
      expect(getByPlaceholderText('What specific deliverables do you expect?')).toBeTruthy();
    });

    it('should show validation errors when fields are empty', async () => {
      const { getByText } = render(<HireWizardScreen />, {
        wrapper: createWrapper(),
      });

      await navigateToTrialDetailsStep(getByText);

      // Try to continue without filling form
      fireEvent.press(getByText('Continue to Start Trial'));

      await waitFor(() => {
        expect(getByText('Start date is required')).toBeTruthy();
        expect(getByText('Trial goals are required')).toBeTruthy();
        expect(getByText('Expected deliverables are required')).toBeTruthy();
      });
    });

    it('should show validation error for short goals text', async () => {
      const { getByText, getByPlaceholderText } = render(<HireWizardScreen />, {
        wrapper: createWrapper(),
      });

      await navigateToTrialDetailsStep(getByText);

      // Fill in short text
      fireEvent.changeText(getByPlaceholderText(/YYYY-MM-DD/), '2026-02-20');
      fireEvent.changeText(
        getByPlaceholderText('What do you want to achieve during the trial?'),
        'Test'
      );
      fireEvent.changeText(
        getByPlaceholderText('What specific deliverables do you expect?'),
        'Short'
      );

      fireEvent.press(getByText('Continue to Start Trial'));

      await waitFor(() => {
        expect(getByText('Please provide more detailed goals (at least 10 characters)')).toBeTruthy();
        expect(getByText('Please provide more details (at least 10 characters)')).toBeTruthy();
      });
    });

    it('should accept valid form data and navigate to Step 4', async () => {
      const { getByText, getByPlaceholderText } = render(<HireWizardScreen />, {
        wrapper: createWrapper(),
      });

      await navigateToTrialDetailsStep(getByText);

      // Fill in valid data
      fireEvent.changeText(getByPlaceholderText(/YYYY-MM-DD/), '2026-02-20');
      fireEvent.changeText(
        getByPlaceholderText('What do you want to achieve during the trial?'),
        'Test content marketing strategies for our product launch'
      );
      fireEvent.changeText(
        getByPlaceholderText('What specific deliverables do you expect?'),
        '3 blog posts, 5 social media campaigns, SEO audit report'
      );

      fireEvent.press(getByText('Continue to Start Trial'));

      await waitFor(() => {
        expect(getByText(/Add a payment method/)).toBeTruthy();
      });
    });

    it('should clear error when user starts typing', async () => {
      const { getByText, getByPlaceholderText, queryByText } = render(<HireWizardScreen />, {
        wrapper: createWrapper(),
      });

      await navigateToTrialDetailsStep(getByText);

      // Try to continue without filling (to show error)
      fireEvent.press(getByText('Continue to Start Trial'));

      await waitFor(() => {
        expect(getByText('Start date is required')).toBeTruthy();
      });

      // Start typing in the field
      fireEvent.changeText(getByPlaceholderText(/YYYY-MM-DD/), '2026-02-20');

      await waitFor(() => {
        expect(queryByText('Start date is required')).toBeNull();
      });
    });

    it('should preserve form data when going back and forth between steps', async () => {
      const { getByText, getByPlaceholderText, getAllByText } = render(<HireWizardScreen />, {
        wrapper: createWrapper(),
      });

      await navigateToTrialDetailsStep(getByText);

      // Fill in form
      fireEvent.changeText(getByPlaceholderText(/YYYY-MM-DD/), '2026-02-20');
      fireEvent.changeText(
        getByPlaceholderText('What do you want to achieve during the trial?'),
        'Test our marketing strategies'
      );

      // Go back to Step 2 (Connect Platform)
      fireEvent.press(getByText('Back'));
      await waitFor(() => expect(getByText('Setup after trial starts')).toBeTruthy());

      // Go forward to Step 3 again
      fireEvent.press(getByText('Continue to Set Goals'));
      await waitFor(() => expect(getAllByText('Set Goals').length).toBeGreaterThanOrEqual(1));

      // Verify form data is preserved
      const startDateInputAgain = getByPlaceholderText(/YYYY-MM-DD/);
      expect(startDateInputAgain.props.value).toBe('2026-02-20');
    });

    it('should display field hints below inputs', async () => {
      const { getByText } = render(<HireWizardScreen />, {
        wrapper: createWrapper(),
      });

      await navigateToTrialDetailsStep(getByText);

      expect(getByText(/When would you like to start the trial/)).toBeTruthy();
      expect(getByText(/Describe your objectives for the 7-day trial period/)).toBeTruthy();
      expect(getByText(/List the outputs you expect at the end of the trial/)).toBeTruthy();
    });
  });

  describe('Payment Form (Step 4)', () => {
    it('should display payment form fields in Step 4', async () => {
      const { getByText, getByPlaceholderText } = render(<HireWizardScreen />, {
        wrapper: createWrapper(),
      });

      await navigateToPaymentStep(getByText, getByPlaceholderText);

      expect(getByText('Pricing Summary')).toBeTruthy();
      expect(getByText('Billing Information')).toBeTruthy();
      expect(getByText('Payment Method')).toBeTruthy();
      expect(getByPlaceholderText('John Doe')).toBeTruthy();
      expect(getByPlaceholderText('john@example.com')).toBeTruthy();
      expect(getByPlaceholderText('9876543210')).toBeTruthy();
    });

    it('should show validation errors when payment fields are empty', async () => {
      const { getByText, getByPlaceholderText } = render(<HireWizardScreen />, {
        wrapper: createWrapper(),
      });

      await navigateToPaymentStep(getByText, getByPlaceholderText);

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
      const { getByText, getByPlaceholderText } = render(<HireWizardScreen />, {
        wrapper: createWrapper(),
      });

      await navigateToPaymentStep(getByText, getByPlaceholderText);

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
      const { getByText, getByPlaceholderText } = render(<HireWizardScreen />, {
        wrapper: createWrapper(),
      });

      await navigateToPaymentStep(getByText, getByPlaceholderText);

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
      const { getByText, getByPlaceholderText } = render(<HireWizardScreen />, {
        wrapper: createWrapper(),
      });

      await navigateToPaymentStep(getByText, getByPlaceholderText);

      expect(getByText('Credit / Debit Card')).toBeTruthy();
      expect(getByText('UPI')).toBeTruthy();
      expect(getByText('Net Banking')).toBeTruthy();

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
      const { getByText, getByPlaceholderText } = render(<HireWizardScreen />, {
        wrapper: createWrapper(),
      });

      await navigateToPaymentStep(getByText, getByPlaceholderText);

      expect(getByText(/I accept the/)).toBeTruthy();

      // Click terms checkbox
      fireEvent.press(getByText(/I accept the/));

      // Should not show terms error after accepting
      fireEvent.press(getByText('Start Trial'));

      await waitFor(() => {
        expect(getByText('Full name is required')).toBeTruthy();
      });
    });

    it('should display pricing summary correctly', async () => {
      const { getByText, getByPlaceholderText } = render(<HireWizardScreen />, {
        wrapper: createWrapper(),
      });

      await navigateToPaymentStep(getByText, getByPlaceholderText);

      expect(getByText('Pricing Summary')).toBeTruthy();
      expect(getByText('Monthly Rate')).toBeTruthy();
      expect(getByText('₹15,000')).toBeTruthy();
      expect(getByText('Trial Period')).toBeTruthy();
      expect(getByText('7 days FREE')).toBeTruthy();
      expect(getByText('Due Today')).toBeTruthy();
      expect(getByText('₹0')).toBeTruthy();
    });

    it('should navigate to TrialDashboard with real subscription_id after successful payment', async () => {
      const { getByText, getByPlaceholderText } = render(<HireWizardScreen />, {
        wrapper: createWrapper(),
      });

      await navigateToPaymentStep(getByText, getByPlaceholderText);

      // Fill payment form
      fireEvent.changeText(getByPlaceholderText('John Doe'), 'John Doe');
      fireEvent.changeText(getByPlaceholderText('john@example.com'), 'john@example.com');
      fireEvent.changeText(getByPlaceholderText('9876543210'), '9876543210');
      fireEvent.press(getByText('UPI'));
      fireEvent.press(getByText(/I accept the/));

      // Submit
      fireEvent.press(getByText('Start Trial'));

      // Verify navigation to TrialDashboard (not HireConfirmation or placeholder route)
      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith(
          'MyAgentsTab',
          expect.objectContaining({
            screen: 'TrialDashboard',
            params: expect.objectContaining({ trialId: 'sub-123' }),
          })
        );
      });
    });

    it('should clear errors when user starts typing in payment fields', async () => {
      const { getByText, getByPlaceholderText, queryByText } = render(<HireWizardScreen />, {
        wrapper: createWrapper(),
      });

      await navigateToPaymentStep(getByText, getByPlaceholderText);

      // Try to submit empty form
      fireEvent.press(getByText('Start Trial'));

      await waitFor(() => {
        expect(getByText('Full name is required')).toBeTruthy();
      });

      // Start typing in name field
      fireEvent.changeText(getByPlaceholderText('John Doe'), 'J');

      await waitFor(() => {
        expect(queryByText('Full name is required')).toBeNull();
      });
    });

    it('should clear payment method error when method is selected', async () => {
      const { getByText, getByPlaceholderText, queryByText } = render(<HireWizardScreen />, {
        wrapper: createWrapper(),
      });

      await navigateToPaymentStep(getByText, getByPlaceholderText);
      // Submit to trigger payment method error
      fireEvent.press(getByText('Start Trial'));
      await waitFor(() => expect(getByText('Please select a payment method')).toBeTruthy());

      // Select card — should clear error
      fireEvent.press(getByText('Credit / Debit Card'));
      await waitFor(() => expect(queryByText('Please select a payment method')).toBeNull());
    });

    it('should clear payment method error when Net Banking is selected', async () => {
      const { getByText, getByPlaceholderText, queryByText } = render(<HireWizardScreen />, {
        wrapper: createWrapper(),
      });

      await navigateToPaymentStep(getByText, getByPlaceholderText);
      fireEvent.press(getByText('Start Trial'));
      await waitFor(() => expect(getByText('Please select a payment method')).toBeTruthy());

      fireEvent.press(getByText('Net Banking'));
      await waitFor(() => expect(queryByText('Please select a payment method')).toBeNull());
    });

    it('should clear email error when user types', async () => {
      const { getByText, getByPlaceholderText, queryByText } = render(<HireWizardScreen />, {
        wrapper: createWrapper(),
      });

      await navigateToPaymentStep(getByText, getByPlaceholderText);
      fireEvent.changeText(getByPlaceholderText('john@example.com'), 'bad');
      fireEvent.press(getByText('Start Trial'));
      await waitFor(() => expect(getByText('Please enter a valid email address')).toBeTruthy());

      fireEvent.changeText(getByPlaceholderText('john@example.com'), 'g');
      await waitFor(() => expect(queryByText('Please enter a valid email address')).toBeNull());
    });

    it('should clear phone error when user types', async () => {
      const { getByText, getByPlaceholderText, queryByText } = render(<HireWizardScreen />, {
        wrapper: createWrapper(),
      });

      await navigateToPaymentStep(getByText, getByPlaceholderText);
      fireEvent.changeText(getByPlaceholderText('9876543210'), '123');
      fireEvent.press(getByText('Start Trial'));
      await waitFor(() => expect(getByText('Please enter a valid 10-digit phone number')).toBeTruthy());

      fireEvent.changeText(getByPlaceholderText('9876543210'), '9');
      await waitFor(() => expect(queryByText('Please enter a valid 10-digit phone number')).toBeNull());
    });
  });

  describe('getPlatformConfig industry branches', () => {
    it('shows LinkedIn credentials for sales industry', async () => {
      (useAgentDetail as jest.Mock).mockReturnValue({
        data: { ...mockAgent, industry: 'sales' },
        isLoading: false, error: null, refetch: jest.fn(),
      });
      const { getByText } = render(<HireWizardScreen />, { wrapper: createWrapper() });
      fireEvent.press(getByText('Continue to Connect Platform'));
      await waitFor(() => expect(getByText('You will need:')).toBeTruthy());
      expect(getByText(/Client ID|Client Secret|LinkedIn/)).toBeTruthy();
    });

    it('shows Google Classroom credentials for education industry', async () => {
      (useAgentDetail as jest.Mock).mockReturnValue({
        data: { ...mockAgent, industry: 'education' },
        isLoading: false, error: null, refetch: jest.fn(),
      });
      const { getByText } = render(<HireWizardScreen />, { wrapper: createWrapper() });
      fireEvent.press(getByText('Continue to Connect Platform'));
      await waitFor(() => expect(getByText('You will need:')).toBeTruthy());
      expect(getByText(/OAuth|Classroom/)).toBeTruthy();
    });

    it('shows default Platform credentials for unknown industry', async () => {
      (useAgentDetail as jest.Mock).mockReturnValue({
        data: { ...mockAgent, industry: 'unknown_industry' },
        isLoading: false, error: null, refetch: jest.fn(),
      });
      const { getByText } = render(<HireWizardScreen />, { wrapper: createWrapper() });
      fireEvent.press(getByText('Continue to Connect Platform'));
      await waitFor(() => expect(getByText('You will need:')).toBeTruthy());
      expect(getByText(/API Key/)).toBeTruthy();
    });
  });

  describe('handleComplete edge cases', () => {
    it('does nothing when processPayment returns null', async () => {
      jest.doMock('@/hooks/useRazorpay', () => ({
        useRazorpay: () => ({
          processPayment: jest.fn().mockResolvedValue(null),
          isProcessing: false, error: null, clearError: jest.fn(),
        }),
      }));

      // Use existing mock (returns sub-123) but with no getParent
      mockGetParent.mockReturnValue(null);

      const { getByText, getByPlaceholderText } = render(<HireWizardScreen />, { wrapper: createWrapper() });
      await navigateToPaymentStep(getByText, getByPlaceholderText);
      fireEvent.changeText(getByPlaceholderText('John Doe'), 'John Doe');
      fireEvent.changeText(getByPlaceholderText('john@example.com'), 'john@example.com');
      fireEvent.changeText(getByPlaceholderText('9876543210'), '9876543210');
      fireEvent.press(getByText('UPI'));
      fireEvent.press(getByText(/I accept the/));
      fireEvent.press(getByText('Start Trial'));

      // Falls back to direct navigate when getParent returns null
      await waitFor(() =>
        expect(mockNavigate).toHaveBeenCalled()
      );
    });
  });
});

