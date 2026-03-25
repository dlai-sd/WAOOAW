/**
 * HireWizardScreen — 4-step wizard tests (MOBILE-COMP-1 E1-S2)
 *
 * Coverage:
 * - Shows 4 named step labels in progress indicator
 * - Step 1 shows "Choose Agent" / "Confirm Agent Selection"
 * - Step 2 shows "Connect Platform" preflight guidance card (no fake toggle)
 * - Step 3 shows "Set Goals" form
 * - Step 4 shows "Start Trial" payment form
 * - Successful trial start navigates using the returned subscription identifier
 */

import React from 'react';
import { describe, it, expect, jest, beforeEach } from '@jest/globals';
import { render, fireEvent, waitFor } from '@testing-library/react-native';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { HireWizardScreen } from '@/screens/hire/HireWizardScreen';
import { useAgentDetail } from '@/hooks/useAgentDetail';
import type { Agent } from '@/types/agent.types';

jest.mock('@/hooks/useAgentDetail');

const mockNavigate = jest.fn();
const mockGetParent = jest.fn();
jest.mock('@/hooks/useRazorpay', () => ({
  useRazorpay: () => ({
    processPayment: jest.fn().mockResolvedValue({
      subscription_id: 'sub-123',
      payment_id: 'pay-123',
    }),
    isProcessing: false,
  }),
}));

jest.mock('@/components/LoadingSpinner', () => ({
  LoadingSpinner: ({ message }: { message?: string }) => {
    const React = require('react');
    const { Text } = require('react-native');
    return React.createElement(Text, {}, message || 'Loading...');
  },
}));

jest.mock('@/components/ErrorView', () => ({
  ErrorView: ({ message }: { message: string }) => {
    const React = require('react');
    const { Text } = require('react-native');
    return React.createElement(Text, {}, message);
  },
}));

jest.mock('@/hooks/useTheme', () => ({
  useTheme: () => ({
    colors: {
      black: '#0a0a0a',
      card: '#18181b',
      textPrimary: '#ffffff',
      textSecondary: '#a1a1aa',
      neonCyan: '#00f2fe',
    },
    spacing: { xs: 4, sm: 8, md: 16, lg: 24, xl: 32, screenPadding: 20 },
    typography: {
      fontFamily: {
        display: 'SpaceGrotesk_700Bold',
        body: 'Inter_400Regular',
        bodyBold: 'Inter_600SemiBold',
      },
    },
  }),
}));

jest.mock('@react-navigation/native', () => ({
  useNavigation: () => ({
    navigate: mockNavigate,
    goBack: jest.fn(),
    getParent: mockGetParent,
  }),
  useRoute: () => ({ params: { agentId: 'agent-123' } }),
}));

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

const createWrapper = () => {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
};

describe('HireWizardScreen — 4-step wizard (MOBILE-COMP-1 E1-S2)', () => {
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

  it('displays 4 named step labels', () => {
    const { getByText } = render(<HireWizardScreen />, { wrapper: createWrapper() });

    expect(getByText('Choose Agent')).toBeTruthy();
    expect(getByText('Connect Platform')).toBeTruthy();
    expect(getByText('Set Goals')).toBeTruthy();
    expect(getByText('Start Trial')).toBeTruthy();
  });

  it('shows step 1 content (Confirm Agent Selection) by default', () => {
    const { getByText } = render(<HireWizardScreen />, { wrapper: createWrapper() });
    expect(getByText('Confirm Agent Selection')).toBeTruthy();
    expect(getByText('Marketing Expert Agent')).toBeTruthy();
  });

  it('navigates to step 2 (Connect Platform) from step 1', async () => {
    const { getByText, getAllByText } = render(<HireWizardScreen />, { wrapper: createWrapper() });

    fireEvent.press(getByText('Continue to Connect Platform'));

    await waitFor(() => {
      // "Connect Platform" appears as step label AND as step 2 title
      const connectTexts = getAllByText('Connect Platform');
      expect(connectTexts.length).toBeGreaterThanOrEqual(2);
    });
  });

  it('shows ConnectorSetupCard as preflight guidance in step 2 (no fake toggle)', async () => {
    const { getByText, queryByText } = render(<HireWizardScreen />, { wrapper: createWrapper() });

    fireEvent.press(getByText('Continue to Connect Platform'));

    await waitFor(() => {
      // Should show guidance status, not fake connected state
      expect(getByText('Setup after trial starts')).toBeTruthy();
      // Should show credentials label
      expect(getByText('You will need:')).toBeTruthy();
      // Must NOT show fake toggle states
      expect(queryByText('Not connected')).toBeNull();
      expect(queryByText('Connected')).toBeNull();
    });
  });

  it('navigates to step 3 (Set Goals) from step 2', async () => {
    const { getByText } = render(<HireWizardScreen />, { wrapper: createWrapper() });

    fireEvent.press(getByText('Continue to Connect Platform'));
    await waitFor(() => expect(getByText('Setup after trial starts')).toBeTruthy());

    fireEvent.press(getByText('Continue to Set Goals'));

    await waitFor(() => {
      expect(getByText(/Configure your 7-day trial period/)).toBeTruthy();
    });
  });

  it('navigates to step 4 (Start Trial) from step 3', async () => {
    const { getByText, getAllByText, getByPlaceholderText } = render(<HireWizardScreen />, {
      wrapper: createWrapper(),
    });

    // Step 1 → 2
    fireEvent.press(getByText('Continue to Connect Platform'));
    await waitFor(() => expect(getAllByText('Connect Platform').length).toBeGreaterThanOrEqual(1));

    // Step 2 → 3
    fireEvent.press(getByText('Continue to Set Goals'));
    await waitFor(() => expect(getByText(/Configure your 7-day trial period/)).toBeTruthy());

    // Fill form
    fireEvent.changeText(getByPlaceholderText(/YYYY-MM-DD/), '2026-02-20');
    fireEvent.changeText(
      getByPlaceholderText('What do you want to achieve during the trial?'),
      'Test marketing strategies'
    );
    fireEvent.changeText(
      getByPlaceholderText('What specific deliverables do you expect?'),
      '3 blog posts and SEO report'
    );

    // Step 3 → 4
    fireEvent.press(getByText('Continue to Start Trial'));

    await waitFor(() => {
      const allStartTrialTexts = getAllByText('Start Trial');
      expect(allStartTrialTexts.length).toBeGreaterThanOrEqual(1);
      expect(getByText(/Add a payment method/)).toBeTruthy();
    });
  });

  it('goes back from step 2 to step 1', async () => {
    const { getByText, getAllByText } = render(<HireWizardScreen />, { wrapper: createWrapper() });

    fireEvent.press(getByText('Continue to Connect Platform'));
    await waitFor(() => expect(getAllByText('Connect Platform').length).toBeGreaterThanOrEqual(1));

    fireEvent.press(getByText('Back'));

    await waitFor(() => {
      expect(getByText('Confirm Agent Selection')).toBeTruthy();
    });
  });

  it('routes to TrialDashboard in MyAgentsTab using the returned subscription_id after successful trial start', async () => {
    const { getByText, getAllByText, getByTestId, getByPlaceholderText } = render(<HireWizardScreen />, {
      wrapper: createWrapper(),
    });

    // Navigate through all steps
    fireEvent.press(getByText('Continue to Connect Platform'));
    await waitFor(() => expect(getAllByText('Connect Platform').length).toBeGreaterThanOrEqual(1));

    fireEvent.press(getByText('Continue to Set Goals'));
    await waitFor(() => expect(getByText(/Configure your 7-day trial period/)).toBeTruthy());

    fireEvent.changeText(getByPlaceholderText(/YYYY-MM-DD/), '2026-02-20');
    fireEvent.changeText(
      getByPlaceholderText('What do you want to achieve during the trial?'),
      'Test marketing strategies longer text here'
    );
    fireEvent.changeText(
      getByPlaceholderText('What specific deliverables do you expect?'),
      '3 blog posts and detailed SEO report'
    );

    fireEvent.press(getByText('Continue to Start Trial'));
    await waitFor(() => expect(getByText(/Add a payment method/)).toBeTruthy());

    // Fill payment form
    fireEvent.changeText(getByPlaceholderText('John Doe'), 'Test User');
    fireEvent.changeText(getByPlaceholderText('john@example.com'), 'test@example.com');
    fireEvent.changeText(getByPlaceholderText('9876543210'), '9876543210');
    fireEvent.press(getByText('Credit / Debit Card'));
    fireEvent.press(getByText(/I accept the/));

    // Press the submit button via its stable testID
    fireEvent.press(getByTestId('submit-trial-btn'));

    await waitFor(() => {
      // Should navigate to MyAgentsTab > TrialDashboard with the real subscription_id
      expect(mockNavigate).toHaveBeenCalledWith(
        'MyAgentsTab',
        expect.objectContaining({
          screen: 'TrialDashboard',
          params: expect.objectContaining({ trialId: 'sub-123' }),
        })
      );
    });
  });
});
