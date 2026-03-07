/**
 * HireWizardScreen — 4-step wizard tests (CP-MOULD-1 E4-S1)
 *
 * Coverage:
 * - Shows 4 named step labels in progress indicator
 * - Step 1 shows "Choose Agent" / "Confirm Agent Selection"
 * - Step 2 shows "Connect Platform" with ConnectorSetupCard
 * - Step 3 shows "Set Goals" form
 * - Step 4 shows "Start Trial" payment form
 * - ConnectorSetupCard shows credentials when not connected
 * - ConnectorSetupCard shows Disconnect when connected
 */

import React from 'react';
import { describe, it, expect, jest, beforeEach } from '@jest/globals';
import { render, fireEvent, waitFor } from '@testing-library/react-native';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { HireWizardScreen } from '@/screens/hire/HireWizardScreen';
import { useAgentDetail } from '@/hooks/useAgentDetail';
import type { Agent } from '@/types/agent.types';

jest.mock('@/hooks/useAgentDetail');

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

const mockNavigate = jest.fn();
const mockGoBack = jest.fn();
jest.mock('@react-navigation/native', () => ({
  useNavigation: () => ({ navigate: mockNavigate, goBack: mockGoBack }),
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

describe('HireWizardScreen — 4-step wizard (CP-MOULD-1 E4-S1)', () => {
  beforeEach(() => {
    jest.clearAllMocks();
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
    const { getByText } = render(<HireWizardScreen />, { wrapper: createWrapper() });

    fireEvent.press(getByText('Continue to Connect Platform'));

    await waitFor(() => {
      expect(getByText('Connect Platform')).toBeTruthy();
    });
  });

  it('shows ConnectorSetupCard with required credentials in step 2', async () => {
    const { getByText } = render(<HireWizardScreen />, { wrapper: createWrapper() });

    fireEvent.press(getByText('Continue to Connect Platform'));

    await waitFor(() => {
      // ConnectorSetupCard should show "Not connected" for marketing agent
      expect(getByText('Not connected')).toBeTruthy();
      // Should show one of the required credentials
      expect(getByText('You\'ll need:')).toBeTruthy();
    });
  });

  it('shows Disconnect after connecting in step 2', async () => {
    const { getByText } = render(<HireWizardScreen />, { wrapper: createWrapper() });

    fireEvent.press(getByText('Continue to Connect Platform'));

    await waitFor(() => expect(getByText('Not connected')).toBeTruthy());

    fireEvent.press(getByText(/Connect Twitter/));

    await waitFor(() => {
      expect(getByText('Connected')).toBeTruthy();
      expect(getByText('Disconnect')).toBeTruthy();
    });
  });

  it('navigates to step 3 (Set Goals) from step 2', async () => {
    const { getByText } = render(<HireWizardScreen />, { wrapper: createWrapper() });

    fireEvent.press(getByText('Continue to Connect Platform'));
    await waitFor(() => expect(getByText('Connect Platform')).toBeTruthy());

    fireEvent.press(getByText('Continue to Set Goals'));

    await waitFor(() => {
      expect(getByText(/Configure your 7-day trial period/)).toBeTruthy();
    });
  });

  it('navigates to step 4 (Start Trial) from step 3', async () => {
    const { getByText, getByPlaceholderText } = render(<HireWizardScreen />, {
      wrapper: createWrapper(),
    });

    // Step 1 → 2
    fireEvent.press(getByText('Continue to Connect Platform'));
    await waitFor(() => expect(getByText('Connect Platform')).toBeTruthy());

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
      expect(getByText('Start Trial')).toBeTruthy();
      expect(getByText(/Add a payment method/)).toBeTruthy();
    });
  });

  it('goes back from step 2 to step 1', async () => {
    const { getByText, getAllByText } = render(<HireWizardScreen />, { wrapper: createWrapper() });

    fireEvent.press(getByText('Continue to Connect Platform'));
    await waitFor(() => expect(getByText('Connect Platform')).toBeTruthy());

    fireEvent.press(getByText('Back'));

    await waitFor(() => {
      expect(getByText('Confirm Agent Selection')).toBeTruthy();
    });
  });
});
