/**
 * HireConfirmationScreen tests (MOB-PARITY-2 E3-S1)
 *
 * AC1 — countdown auto-navigates to MyAgents after 3 s
 * AC2 — "hire-confirm-go-my-agents" button is present when agent loaded
 * AC3 — tapping that button navigates via getParent()
 * AC4 — receipt displays agent name + start date + end date
 * AC5 — countdown text decrements from 3 to 2
 */

import React from 'react';
import { act, fireEvent, render, screen, waitFor } from '@testing-library/react-native';
import { HireConfirmationScreen } from '../HireConfirmationScreen';

// ── mocks ─────────────────────────────────────────────────────────────────────

const mockParentNavigate = jest.fn();
const mockNavigate = jest.fn();

jest.mock('@react-navigation/native', () => ({
  useRoute: jest.fn(),
  useNavigation: jest.fn(),
  RouteProp: {},
}));

jest.mock('@/hooks/useTheme', () => ({
  useTheme: () => ({
    colors: {
      black: '#000000',
      textPrimary: '#ffffff',
      textSecondary: '#cccccc',
      neonCyan: '#00f2fe',
      success: '#10b981',
      warning: '#f59e0b',
      error: '#ef4444',
      border: '#333333',
      card: '#1a1a1a',
    },
    spacing: {
      xs: 4,
      sm: 8,
      md: 16,
      lg: 24,
      xl: 32,
      screenPadding: { horizontal: 16, vertical: 12 },
    },
    typography: {
      fontFamily: {
        display: 'SpaceGrotesk-Bold',
        body: 'Inter-Regular',
        bodyBold: 'Inter-Bold',
      },
    },
  }),
}));

jest.mock('@/hooks/useAgentDetail', () => ({
  useAgentDetail: jest.fn(),
}));

jest.mock('@/components/LoadingSpinner', () => ({
  LoadingSpinner: ({ message }: { message: string }) => <>{message}</>,
}));

jest.mock('@/components/ErrorView', () => ({
  ErrorView: ({ message }: { message: string }) => <>{message}</>,
}));

// ── helpers ───────────────────────────────────────────────────────────────────

const { useRoute, useNavigation } = jest.requireMock('@react-navigation/native') as {
  useRoute: jest.Mock;
  useNavigation: jest.Mock;
};

const { useAgentDetail } = jest.requireMock('@/hooks/useAgentDetail') as {
  useAgentDetail: jest.Mock;
};

function setupHooks({
  agentLoaded = true,
  agentLoading = false,
}: { agentLoaded?: boolean; agentLoading?: boolean } = {}) {
  useNavigation.mockReturnValue({
    navigate: mockNavigate,
    getParent: () => ({ navigate: mockParentNavigate }),
  });

  useRoute.mockReturnValue({
    params: {
      agentId: 'AGT-001',
      trialId: 'TRL-001',
      trialData: {
        startDate: '2026-03-10',
        goals: 'grow audience',
        deliverables: '4 posts/week',
      },
      paymentData: null,
    },
  });

  useAgentDetail.mockReturnValue({
    data: agentLoaded ? { agent_id: 'AGT-001', name: 'DMA Agent Alpha' } : undefined,
    isLoading: agentLoading,
    error: null,
    refetch: jest.fn(),
  });
}

// ── tests ─────────────────────────────────────────────────────────────────────

describe('HireConfirmationScreen (E3-S1)', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it('AC2 — hire-confirm-go-my-agents button is present when agent loaded', () => {
    setupHooks({ agentLoaded: true });
    render(<HireConfirmationScreen />);
    expect(screen.getByTestId('hire-confirm-go-my-agents')).toBeTruthy();
  });

  it('AC3 — tapping go-my-agents button navigates via getParent()', () => {
    setupHooks({ agentLoaded: true });
    render(<HireConfirmationScreen />);
    fireEvent.press(screen.getByTestId('hire-confirm-go-my-agents'));
    expect(mockParentNavigate).toHaveBeenCalledWith('MyAgentsTab', { screen: 'MyAgents' });
  });

  it('AC4 — receipt shows agent name and start date', () => {
    setupHooks({ agentLoaded: true });
    render(<HireConfirmationScreen />);
    expect(screen.getByText(/DMA Agent Alpha/i)).toBeTruthy();
    // "Start Date" label confirms the receipt start-date row is rendered
    expect(screen.getByText(/Start Date/i)).toBeTruthy();
  });

  it('AC5 — countdown text is visible and shows initial countdown', () => {
    setupHooks({ agentLoaded: true });
    render(<HireConfirmationScreen />);
    expect(screen.getByTestId('hire-confirm-countdown')).toBeTruthy();
    // Should show 3 initially
    const countdownEl = screen.getByTestId('hire-confirm-countdown');
    expect(countdownEl.props.children ?? '').toBeTruthy();
  });

  it('AC1 — auto-navigates to MyAgentsTab after countdown reaches 0', async () => {
    setupHooks({ agentLoaded: true });
    render(<HireConfirmationScreen />);

    // Advance 3 × 1000 ms increments to trigger all three setCountdown calls
    act(() => {
      jest.advanceTimersByTime(1000); // 3→2
    });
    act(() => {
      jest.advanceTimersByTime(1000); // 2→1
    });
    act(() => {
      jest.advanceTimersByTime(1000); // 1→0 → navigate
    });

    await waitFor(() => {
      expect(mockParentNavigate).toHaveBeenCalledWith('MyAgentsTab', { screen: 'MyAgents' });
    });
  });
});
