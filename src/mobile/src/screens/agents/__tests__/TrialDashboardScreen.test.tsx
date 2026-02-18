/**
 * Trial Dashboard Screen Tests (Story 2.13)
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react-native';
import { TrialDashboardScreen } from '../TrialDashboardScreen';
import { useHiredAgent } from '@/hooks/useHiredAgents';
import type { HiredAgentInstance } from '@/types/hiredAgents.types';

// Mock hooks
jest.mock('@/hooks/useHiredAgents');
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

// Mock navigation
const mockNavigate = jest.fn();
const mockGoBack = jest.fn();
const mockNavigation = {
  navigate: mockNavigate,
  goBack: mockGoBack,
};

// Mock route
const createRoute = (trialId: string) => ({
  params: { trialId },
  key: 'trial-dashboard',
  name: 'TrialDashboard' as const,
});

// Create mock agent data
const createMockAgent = (overrides: Partial<HiredAgentInstance> = {}): HiredAgentInstance => {
  const now = new Date();
  const trialStart = new Date(now.getTime() - 2 * 24 * 60 * 60 * 1000); // 2 days ago
  const trialEnd = new Date(now.getTime() + 5 * 24 * 60 * 60 * 1000); // 5 days from now
  
  return {
    hired_instance_id: 'hired_123',
    subscription_id: 'sub_123',
    agent_id: 'agent_123',
    agent_type_id: 'type_123',
    customer_id: 'cust_123',
    nickname: 'My Test Agent',
    theme: null,
    config: {},
    configured: true,
    goals_completed: true,
    trial_status: 'active',
    trial_start_at: trialStart.toISOString(),
    trial_end_at: trialEnd.toISOString(),
    subscription_status: 'active',
    subscription_ended_at: null,
    retention_expires_at: null,
    active: true,
    created_at: trialStart.toISOString(),
    updated_at: now.toISOString(),
    ...overrides,
  };
};

describe('TrialDashboardScreen', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Loading State', () => {
    it('should show loading spinner while fetching data', () => {
      (useHiredAgent as jest.Mock).mockReturnValue({
        data: undefined,
        isLoading: true,
        error: null,
        refetch: jest.fn(),
      });

      render(
        <TrialDashboardScreen
          navigation={mockNavigation as any}
          route={createRoute('sub_123') as any}
        />
      );

      expect(screen.getByText('Loading trial details...')).toBeTruthy();
    });
  });

  describe('Error State', () => {
    it('should show error view when fetch fails', () => {
      const mockRefetch = jest.fn();
      (useHiredAgent as jest.Mock).mockReturnValue({
        data: undefined,
        isLoading: false,
        error: new Error('Network error'),
        refetch: mockRefetch,
      });

      render(
        <TrialDashboardScreen
          navigation={mockNavigation as any}
          route={createRoute('sub_123') as any}
        />
      );

      expect(screen.getByText('Network error')).toBeTruthy();
    });

    it('should call refetch when retry button pressed', () => {
      const mockRefetch = jest.fn();
      (useHiredAgent as jest.Mock).mockReturnValue({
        data: undefined,
        isLoading: false,
        error: new Error('Network error'),
        refetch: mockRefetch,
      });

      render(
        <TrialDashboardScreen
          navigation={mockNavigation as any}
          route={createRoute('sub_123') as any}
        />
      );

      const retryButton = screen.getByText('Try Again');
      fireEvent.press(retryButton);

      expect(mockRefetch).toHaveBeenCalledTimes(1);
    });
  });

  describe('Empty State', () => {
    it('should show trial not found when no agent data', () => {
      (useHiredAgent as jest.Mock).mockReturnValue({
        data: null,
        isLoading: false,
        error: null,
        refetch: jest.fn(),
      });

      render(
        <TrialDashboardScreen
          navigation={mockNavigation as any}
          route={createRoute('sub_123') as any}
        />
      );

      expect(screen.getByText('Trial not found')).toBeTruthy();
      expect(screen.getByText('Back to My Agents')).toBeTruthy();
    });

    it('should navigate back when back button pressed in empty state', () => {
      (useHiredAgent as jest.Mock).mockReturnValue({
        data: null,
        isLoading: false,
        error: null,
        refetch: jest.fn(),
      });

      render(
        <TrialDashboardScreen
          navigation={mockNavigation as any}
          route={createRoute('sub_123') as any}
        />
      );

      const backButton = screen.getByText('Back to My Agents');
      fireEvent.press(backButton);

      expect(mockGoBack).toHaveBeenCalledTimes(1);
    });
  });

  describe('Active Trial State', () => {
    it('should render trial dashboard with all sections', () => {
      const agent = createMockAgent();
      (useHiredAgent as jest.Mock).mockReturnValue({
        data: agent,
        isLoading: false,
        error: null,
        refetch: jest.fn(),
      });

      render(
        <TrialDashboardScreen
          navigation={mockNavigation as any}
          route={createRoute('sub_123') as any}
        />
      );

      expect(screen.getByText('Trial Dashboard')).toBeTruthy();
      expect(screen.getByText('Trial Progress')).toBeTruthy();
      expect(screen.getByText('Agent Information')).toBeTruthy();
    });

    it('should show active trial status badge', () => {
      const agent = createMockAgent({ trial_status: 'active' });
      (useHiredAgent as jest.Mock).mockReturnValue({
        data: agent,
        isLoading: false,
        error: null,
        refetch: jest.fn(),
      });

      render(
        <TrialDashboardScreen
          navigation={mockNavigation as any}
          route={createRoute('sub_123') as any}
        />
      );

      expect(screen.getByText(/Active Trial/)).toBeTruthy();
    });

    it('should display agent nickname', () => {
      const agent = createMockAgent({ nickname: 'Marketing Bot' });
      (useHiredAgent as jest.Mock).mockReturnValue({
        data: agent,
        isLoading: false,
        error: null,
        refetch: jest.fn(),
      });

      render(
        <TrialDashboardScreen
          navigation={mockNavigation as any}
          route={createRoute('sub_123') as any}
        />
      );

      expect(screen.getAllByText('Marketing Bot').length).toBeGreaterThan(0);
    });

    it('should show trial progress bar', () => {
      const agent = createMockAgent();
      (useHiredAgent as jest.Mock).mockReturnValue({
        data: agent,
        isLoading: false,
        error: null,
        refetch: jest.fn(),
      });

      render(
        <TrialDashboardScreen
          navigation={mockNavigation as any}
          route={createRoute('sub_123') as any}
        />
      );

      expect(screen.getByText('Days Remaining')).toBeTruthy();
      expect(screen.getByText('out of 7 days')).toBeTruthy();
    });

    it('should display configured status', () => {
      const agent = createMockAgent({ configured: true });
      (useHiredAgent as jest.Mock).mockReturnValue({
        data: agent,
        isLoading: false,
        error: null,
        refetch: jest.fn(),
      });

      render(
        <TrialDashboardScreen
          navigation={mockNavigation as any}
          route={createRoute('sub_123') as any}
        />
      );

      expect(screen.getByText('✓ Configured')).toBeTruthy();
    });

    it('should display needs setup when not configured', () => {
      const agent = createMockAgent({ configured: false });
      (useHiredAgent as jest.Mock).mockReturnValue({
        data: agent,
        isLoading: false,
        error: null,
        refetch: jest.fn(),
      });

      render(
        <TrialDashboardScreen
          navigation={mockNavigation as any}
          route={createRoute('sub_123') as any}
        />
      );

      expect(screen.getByText('⚠ Needs Setup')).toBeTruthy();
    });

    it('should show goals completed status', () => {
      const agent = createMockAgent({ goals_completed: true });
      (useHiredAgent as jest.Mock).mockReturnValue({
        data: agent,
        isLoading: false,
        error: null,
        refetch: jest.fn(),
      });

      render(
        <TrialDashboardScreen
          navigation={mockNavigation as any}
          route={createRoute('sub_123') as any}
        />
      );

      expect(screen.getByText('✓ Yes')).toBeTruthy();
    });

    it('should show trial benefits info', () => {
      const agent = createMockAgent();
      (useHiredAgent as jest.Mock).mockReturnValue({
        data: agent,
        isLoading: false,
        error: null,
        refetch: jest.fn(),
      });

      render(
        <TrialDashboardScreen
          navigation={mockNavigation as any}
          route={createRoute('sub_123') as any}
        />
      );

      expect(screen.getByText('💡 Trial Benefits')).toBeTruthy();
      expect(screen.getByText(/Keep all deliverables even if you cancel/)).toBeTruthy();
    });
  });

  describe('Expired Trial State', () => {
    it('should show expired status badge', () => {
      const agent = createMockAgent({ trial_status: 'expired' });
      (useHiredAgent as jest.Mock).mockReturnValue({
        data: agent,
        isLoading: false,
        error: null,
        refetch: jest.fn(),
      });

      render(
        <TrialDashboardScreen
          navigation={mockNavigation as any}
          route={createRoute('sub_123') as any}
        />
      );

      expect(screen.getByText(/Trial Expired/)).toBeTruthy();
    });

    it('should not show trial progress card for expired trial', () => {
      const agent = createMockAgent({ trial_status: 'expired' });
      (useHiredAgent as jest.Mock).mockReturnValue({
        data: agent,
        isLoading: false,
        error: null,
        refetch: jest.fn(),
      });

      render(
        <TrialDashboardScreen
          navigation={mockNavigation as any}
          route={createRoute('sub_123') as any}
        />
      );

      expect(screen.queryByText('Trial Progress')).toBeNull();
    });

    it('should not show trial benefits for expired trial', () => {
      const agent = createMockAgent({ trial_status: 'expired' });
      (useHiredAgent as jest.Mock).mockReturnValue({
        data: agent,
        isLoading: false,
        error: null,
        refetch: jest.fn(),
      });

      render(
        <TrialDashboardScreen
          navigation={mockNavigation as any}
          route={createRoute('sub_123') as any}
        />
      );

      expect(screen.queryByText('💡 Trial Benefits')).toBeNull();
    });
  });

  describe('Converted Trial State', () => {
    it('should show converted status badge', () => {
      const agent = createMockAgent({ trial_status: 'converted' });
      (useHiredAgent as jest.Mock).mockReturnValue({
        data: agent,
        isLoading: false,
        error: null,
        refetch: jest.fn(),
      });

      render(
        <TrialDashboardScreen
          navigation={mockNavigation as any}
          route={createRoute('sub_123') as any}
        />
      );

      expect(screen.getByText(/Converted to Paid/)).toBeTruthy();
    });
  });

  describe('Canceled Trial State', () => {
    it('should show canceled status badge', () => {
      const agent = createMockAgent({ trial_status: 'canceled' });
      (useHiredAgent as jest.Mock).mockReturnValue({
        data: agent,
        isLoading: false,
        error: null,
        refetch: jest.fn(),
      });

      render(
        <TrialDashboardScreen
          navigation={mockNavigation as any}
          route={createRoute('sub_123') as any}
        />
      );

      expect(screen.getByText(/Trial Canceled/)).toBeTruthy();
    });
  });

  describe('Navigation', () => {
    it('should navigate to agent detail when view agent pressed', () => {
      const agent = createMockAgent({ agent_id: 'agent_456' });
      (useHiredAgent as jest.Mock).mockReturnValue({
        data: agent,
        isLoading: false,
        error: null,
        refetch: jest.fn(),
      });

      render(
        <TrialDashboardScreen
          navigation={mockNavigation as any}
          route={createRoute('sub_123') as any}
        />
      );

      const viewButton = screen.getByText('View Agent Details');
      fireEvent.press(viewButton);

      expect(mockNavigate).toHaveBeenCalledWith('AgentDetail', { agentId: 'agent_456' });
    });

    it('should navigate back when back button pressed', () => {
      const agent = createMockAgent();
      (useHiredAgent as jest.Mock).mockReturnValue({
        data: agent,
        isLoading: false,
        error: null,
        refetch: jest.fn(),
      });

      render(
        <TrialDashboardScreen
          navigation={mockNavigation as any}
          route={createRoute('sub_123') as any}
        />
      );

      const backButton = screen.getByText('← Back');
      fireEvent.press(backButton);

      expect(mockGoBack).toHaveBeenCalledTimes(1);
    });

    it('should navigate back when bottom back button pressed', () => {
      const agent = createMockAgent();
      (useHiredAgent as jest.Mock).mockReturnValue({
        data: agent,
        isLoading: false,
        error: null,
        refetch: jest.fn(),
      });

      render(
        <TrialDashboardScreen
          navigation={mockNavigation as any}
          route={createRoute('sub_123') as any}
        />
      );

      const buttons = screen.getAllByText('Back to My Agents');
      const bottomButton = buttons[buttons.length - 1];
      fireEvent.press(bottomButton);

      expect(mockGoBack).toHaveBeenCalledTimes(1);
    });
  });

  describe('Pull-to-Refresh', () => {
    it('should support pull-to-refresh', async () => {
      const mockRefetch = jest.fn().mockResolvedValue({});
      const agent = createMockAgent();
      (useHiredAgent as jest.Mock).mockReturnValue({
        data: agent,
        isLoading: false,
        error: null,
        refetch: mockRefetch,
      });

      render(
        <TrialDashboardScreen
          navigation={mockNavigation as any}
          route={createRoute('sub_123') as any}
        />
      );

      // Find ScrollView and trigger refresh
      const scrollView = screen.getByTestId('scroll-view');
      const refreshControl = scrollView.props.refreshControl;
      
      await waitFor(() => {
        refreshControl.props.onRefresh();
      });

      expect(mockRefetch).toHaveBeenCalled();
    });
  });
});

