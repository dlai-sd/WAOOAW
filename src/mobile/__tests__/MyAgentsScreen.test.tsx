/**
 * Tests for MyAgentsScreen (Story 2.12)
 * 
 * Coverage:
 * - Tab switching (Active Trials vs Hired)
 * - Empty states for both tabs
 * - Agent card rendering with trial and hired agents
 * - Pull-to-refresh functionality
 * - Navigation to trial dashboard and agent detail
 * - Loading and error states
 */

import React from 'react';
import { render, fireEvent, waitFor } from '@testing-library/react-native';
import { MyAgentsScreen } from '@/screens/agents/MyAgentsScreen';
import * as useHiredAgentsModule from '@/hooks/useHiredAgents';
import type { MyAgentInstanceSummary } from '@/types/hiredAgents.types';

// Mock NavigationContainer
jest.mock('@react-navigation/native', () => ({
  ...jest.requireActual('@react-navigation/native'),
  NavigationContainer: ({ children }: { children: React.ReactNode }) => children,
}));

// Mock hooks
jest.mock('@/hooks/useHiredAgents');

// Mock useTheme
jest.mock('@/hooks/useTheme', () => ({
  useTheme: () => ({
    colors: {
      black: '#0a0a0a',
      neonCyan: '#00f2fe',
      success: '#10b981',
      warning: '#f59e0b',
      textPrimary: '#ffffff',
      textSecondary: '#9ca3af',
      card: '#18181b',
      border: '#374151',
    },
    spacing: {
      xs: 8,
      sm: 12,
      md: 16,
      lg: 20,
      xl: 24,
      xxl: 32,
      screenPadding: {
        horizontal: 16,
        vertical: 20,
      },
    },
    typography: {
      fontFamily: {
        display: 'SpaceGrotesk_700Bold',
        heading: 'Outfit_600SemiBold',
        body: 'Inter_400Regular',
        bodyBold: 'Inter_600SemiBold',
      },
    },
  }),
}));
jest.mock('@/components/LoadingSpinner', () => {
  // eslint-disable-next-line @typescript-eslint/no-require-imports
  const React = require('react');
  // eslint-disable-next-line @typescript-eslint/no-require-imports
  const { Text } = require('react-native');
  return {
    LoadingSpinner: ({ message }: { message: string }) => (
      <Text testID="loading-spinner">{message}</Text>
    ),
  };
});
jest.mock('@/components/ErrorView', () => {
  // eslint-disable-next-line @typescript-eslint/no-require-imports
  const React = require('react');
  // eslint-disable-next-line @typescript-eslint/no-require-imports
  const { View, Text, TouchableOpacity } = require('react-native');
  return {
    ErrorView: ({ message, onRetry }: { message: string; onRetry: () => void }) => (
      <View testID="error-view">
        <Text>{message}</Text>
        <TouchableOpacity testID="retry-button" onPress={onRetry}>
          <Text>Retry</Text>
        </TouchableOpacity>
      </View>
    ),
  };
});

// Mock navigation
const mockNavigate = jest.fn();
const mockNavigation = {
  navigate: mockNavigate,
  goBack: jest.fn(),
  setOptions: jest.fn(),
  addListener: jest.fn(() => jest.fn()),
  removeListener: jest.fn(),
  canGoBack: jest.fn(() => true),
  dispatch: jest.fn(),
  isFocused: jest.fn(() => true),
  getParent: jest.fn(),
  getState: jest.fn(),
  reset: jest.fn(),
  setParams: jest.fn(),
};

// Test data
const mockTrialAgent: MyAgentInstanceSummary = {
  subscription_id: 'sub_trial_123',
  agent_id: 'content_marketing',
  duration: 'monthly',
  status: 'active',
  trial_status: 'active',
  nickname: 'My Content Agent',
  hired_instance_id: 'hire_123',
  current_period_start: '2024-01-01T00:00:00Z',
  current_period_end: '2024-02-01T00:00:00Z',
  cancel_at_period_end: false,
  trial_start_at: '2024-01-01T00:00:00Z',
  trial_end_at: '2024-01-08T00:00:00Z',
  configured: false,
  goals_completed: false,
};

const mockHiredAgent: MyAgentInstanceSummary = {
  subscription_id: 'sub_hired_456',
  agent_id: 'seo_specialist',
  duration: 'monthly',
  status: 'active',
  trial_status: 'converted',
  nickname: 'SEO Pro',
  hired_instance_id: 'hire_456',
  current_period_start: '2023-12-01T00:00:00Z',
  current_period_end: '2024-01-01T00:00:00Z',
  cancel_at_period_end: false,
  trial_start_at: '2023-11-24T00:00:00Z',
  trial_end_at: '2023-12-01T00:00:00Z',
  configured: true,
  goals_completed: true,
};

const mockHiredAgentEnding: MyAgentInstanceSummary = {
  ...mockHiredAgent,
  subscription_id: 'sub_ending_789',
  agent_id: 'social_media',
  nickname: 'Social Agent',
  cancel_at_period_end: true,
};

describe('MyAgentsScreen', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockNavigate.mockClear();
  });

  const renderScreen = () => {
    return render(
      <MyAgentsScreen 
        navigation={mockNavigation as never} 
        route={{ key: 'my-agents', name: 'MyAgents' } as never} 
      />
    );
  };

  describe('Loading State', () => {
    it('shows loading spinner when fetching trial agents', () => {
      (useHiredAgentsModule.useHiredAgents as jest.Mock).mockReturnValue({
        data: undefined,
        isLoading: true,
        error: null,
        refetch: jest.fn(),
      });
      (useHiredAgentsModule.useAgentsInTrial as jest.Mock).mockReturnValue({
        data: undefined,
        isLoading: true,
        error: null,
        refetch: jest.fn(),
      });

      const { getByTestId, getByText } = renderScreen();

      expect(getByTestId('loading-spinner')).toBeTruthy();
      expect(getByText('Loading your agents...')).toBeTruthy();
    });
  });

  describe('Error State', () => {
    it('shows error view when trial agents fail to load', () => {
      const mockError = new Error('Network error');
      (useHiredAgentsModule.useHiredAgents as jest.Mock).mockReturnValue({
        data: undefined,
        isLoading: false,
        error: mockError,
        refetch: jest.fn(),
      });
      (useHiredAgentsModule.useAgentsInTrial as jest.Mock).mockReturnValue({
        data: undefined,
        isLoading: false,
        error: mockError,
        refetch: jest.fn(),
      });

      const { getByTestId, getByText } = renderScreen();

      expect(getByTestId('error-view')).toBeTruthy();
      expect(getByText('Network error')).toBeTruthy();
    });

    it('calls refetch when retry button is pressed', async () => {
      const mockRefetch = jest.fn();
      (useHiredAgentsModule.useHiredAgents as jest.Mock).mockReturnValue({
        data: undefined,
        isLoading: false,
        error: new Error('Network error'),
        refetch: mockRefetch,
      });
      (useHiredAgentsModule.useAgentsInTrial as jest.Mock).mockReturnValue({
        data: undefined,
        isLoading: false,
        error: new Error('Network error'),
        refetch: mockRefetch,
      });

      const { getByTestId } = renderScreen();
      const retryButton = getByTestId('retry-button');

      fireEvent.press(retryButton);

      await waitFor(() => {
        expect(mockRefetch).toHaveBeenCalled();
      });
    });
  });

  describe('Empty States', () => {
    it('shows empty state for trials tab when no trials', () => {
      (useHiredAgentsModule.useHiredAgents as jest.Mock).mockReturnValue({
        data: [],
        isLoading: false,
        error: null,
        refetch: jest.fn(),
      });
      (useHiredAgentsModule.useAgentsInTrial as jest.Mock).mockReturnValue({
        data: [],
        isLoading: false,
        error: null,
        refetch: jest.fn(),
      });

      const { getByText } = renderScreen();

      expect(getByText('No Active Trials')).toBeTruthy();
      expect(getByText('Start a 7-day trial to see results before hiring')).toBeTruthy();
      expect(getByText('Discover Agents')).toBeTruthy();
    });

    it('shows empty state for hired tab when no hired agents', () => {
      (useHiredAgentsModule.useHiredAgents as jest.Mock).mockReturnValue({
        data: [],
        isLoading: false,
        error: null,
        refetch: jest.fn(),
      });
      (useHiredAgentsModule.useAgentsInTrial as jest.Mock).mockReturnValue({
        data: [],
        isLoading: false,
        error: null,
        refetch: jest.fn(),
      });

      const { getByText } = renderScreen();

      // Switch to hired tab
      const hiredTab = getByText(/Hired \(\d+\)/);
      fireEvent.press(hiredTab);

      expect(getByText('No Hired Agents Yet')).toBeTruthy();
      expect(getByText('Hire agents after successful trials or direct from discovery')).toBeTruthy();
    });

    it('navigates to Discover screen when CTA is pressed', async () => {
      (useHiredAgentsModule.useHiredAgents as jest.Mock).mockReturnValue({
        data: [],
        isLoading: false,
        error: null,
        refetch: jest.fn(),
      });
      (useHiredAgentsModule.useAgentsInTrial as jest.Mock).mockReturnValue({
        data: [],
        isLoading: false,
        error: null,
        refetch: jest.fn(),
      });

      const { getByText } = renderScreen();
      const ctaButton = getByText('Discover Agents');

      fireEvent.press(ctaButton);

      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith('Discover');
      });
    });

    it('shows "How It Works" section in empty state', () => {
      (useHiredAgentsModule.useHiredAgents as jest.Mock).mockReturnValue({
        data: [],
        isLoading: false,
        error: null,
        refetch: jest.fn(),
      });
      (useHiredAgentsModule.useAgentsInTrial as jest.Mock).mockReturnValue({
        data: [],
        isLoading: false,
        error: null,
        refetch: jest.fn(),
      });

      const { getByText } = renderScreen();

      expect(getByText('How It Works')).toBeTruthy();
      expect(getByText('Start a 7-Day Trial')).toBeTruthy();
      expect(getByText('Keep All Deliverables')).toBeTruthy();
      expect(getByText('Hire What Works')).toBeTruthy();
    });
  });

  describe('Tab Switching', () => {
    it('shows correct count in each tab', () => {
      (useHiredAgentsModule.useHiredAgents as jest.Mock).mockReturnValue({
        data: [mockTrialAgent, mockHiredAgent],
        isLoading: false,
        error: null,
        refetch: jest.fn(),
      });
      (useHiredAgentsModule.useAgentsInTrial as jest.Mock).mockReturnValue({
        data: [mockTrialAgent],
        isLoading: false,
        error: null,
        refetch: jest.fn(),
      });

      const { getByText } = renderScreen();

      // Check tab counts
      expect(getByText('Active Trials (1)')).toBeTruthy();
      expect(getByText('Hired (1)')).toBeTruthy();
    });

    it('switches tabs when pressed', async () => {
      (useHiredAgentsModule.useHiredAgents as jest.Mock).mockReturnValue({
        data: [mockTrialAgent, mockHiredAgent],
        isLoading: false,
        error: null,
        refetch: jest.fn(),
      });
      (useHiredAgentsModule.useAgentsInTrial as jest.Mock).mockReturnValue({
        data: [mockTrialAgent],
        isLoading: false,
        error: null,
        refetch: jest.fn(),
      });

      const { getByText, getByTestId } = renderScreen();

      // Default is trials tab, should show trial agent
      expect(getByTestId('agent-id-content_marketing')).toBeTruthy();

      // Switch to hired tab
      const hiredTab = getByText('Hired (1)');
      fireEvent.press(hiredTab);

      await waitFor(() => {
        expect(getByTestId('agent-id-seo_specialist')).toBeTruthy();
      });
    });

    it('filters trial agents correctly in trials tab', () => {
      (useHiredAgentsModule.useHiredAgents as jest.Mock).mockReturnValue({
        data: [mockTrialAgent, mockHiredAgent],
        isLoading: false,
        error: null,
        refetch: jest.fn(),
      });
      (useHiredAgentsModule.useAgentsInTrial as jest.Mock).mockReturnValue({
        data: [mockTrialAgent],
        isLoading: false,
        error: null,
        refetch: jest.fn(),
      });

      const { getByTestId, queryByTestId } = renderScreen();

      // Trials tab should show only trial agent
      expect(getByTestId('agent-id-content_marketing')).toBeTruthy();
      expect(queryByTestId('agent-id-seo_specialist')).toBeNull();
    });

    it('filters hired agents correctly in hired tab', async () => {
      (useHiredAgentsModule.useHiredAgents as jest.Mock).mockReturnValue({
        data: [mockTrialAgent, mockHiredAgent],
        isLoading: false,
        error: null,
        refetch: jest.fn(),
      });
      (useHiredAgentsModule.useAgentsInTrial as jest.Mock).mockReturnValue({
        data: [mockTrialAgent],
        isLoading: false,
        error: null,
        refetch: jest.fn(),
      });

      const { getByText, getByTestId, queryByTestId } = renderScreen();

      // Switch to hired tab
      const hiredTab = getByText('Hired (1)');
      fireEvent.press(hiredTab);

      await waitFor(() => {
        expect(getByTestId('agent-id-seo_specialist')).toBeTruthy();
        expect(queryByTestId('agent-id-content_marketing')).toBeNull();
      });
    });
  });

  describe('Agent Cards', () => {
    it('renders trial agent card with correct information', () => {
      (useHiredAgentsModule.useHiredAgents as jest.Mock).mockReturnValue({
        data: [mockTrialAgent],
        isLoading: false,
        error: null,
        refetch: jest.fn(),
      });
      (useHiredAgentsModule.useAgentsInTrial as jest.Mock).mockReturnValue({
        data: [mockTrialAgent],
        isLoading: false,
        error: null,
        refetch: jest.fn(),
      });

      const { getByText, getByTestId } = renderScreen();

      expect(getByTestId('agent-id-content_marketing')).toBeTruthy();
      expect(getByText('My Content Agent')).toBeTruthy();
      expect(getByText('Trial Active')).toBeTruthy();
      expect(getByText('Trial Period')).toBeTruthy();
    });

    it('renders hired agent card with correct information', async () => {
      (useHiredAgentsModule.useHiredAgents as jest.Mock).mockReturnValue({
        data: [mockHiredAgent],
        isLoading: false,
        error: null,
        refetch: jest.fn(),
      });
      (useHiredAgentsModule.useAgentsInTrial as jest.Mock).mockReturnValue({
        data: [],
        isLoading: false,
        error: null,
        refetch: jest.fn(),
      });

      const { getByText, getByTestId } = renderScreen();

      // Switch to hired tab
      const hiredTab = getByText('Hired (1)');
      fireEvent.press(hiredTab);

      const agentId = await waitFor(() => getByTestId('agent-id-seo_specialist'));
      expect(agentId).toBeTruthy();
      expect(getByText('SEO Pro')).toBeTruthy();
      expect(getByText('Active')).toBeTruthy();
    });

    it('shows "Ending Soon" badge for agents with cancel_at_period_end', async () => {
      (useHiredAgentsModule.useHiredAgents as jest.Mock).mockReturnValue({
        data: [mockHiredAgentEnding],
        isLoading: false,
        error: null,
        refetch: jest.fn(),
      });
      (useHiredAgentsModule.useAgentsInTrial as jest.Mock).mockReturnValue({
        data: [],
        isLoading: false,
        error: null,
        refetch: jest.fn(),
      });

      const { getByText } = renderScreen();

      // Switch to hired tab
      const hiredTab = getByText('Hired (1)');
      fireEvent.press(hiredTab);

      await waitFor(() => {
        expect(getByText('Ending Soon')).toBeTruthy();
      });
    });

    it('shows duration and billing date', () => {
      (useHiredAgentsModule.useHiredAgents as jest.Mock).mockReturnValue({
        data: [mockTrialAgent],
        isLoading: false,
        error: null,
        refetch: jest.fn(),
      });
      (useHiredAgentsModule.useAgentsInTrial as jest.Mock).mockReturnValue({
        data: [mockTrialAgent],
        isLoading: false,
        error: null,
        refetch: jest.fn(),
      });

      const { getByText, getByTestId } = renderScreen();

      expect(getByTestId('agent-id-content_marketing')).toBeTruthy();
      expect(getByText('Duration')).toBeTruthy();
      expect(getByText('Monthly')).toBeTruthy();
      expect(getByText('Next Billing')).toBeTruthy();
    });
  });

  describe('Navigation', () => {
    it('navigates to trial dashboard when trial agent is pressed', async () => {
      (useHiredAgentsModule.useHiredAgents as jest.Mock).mockReturnValue({
        data: [mockTrialAgent],
        isLoading: false,
        error: null,
        refetch: jest.fn(),
      });
      (useHiredAgentsModule.useAgentsInTrial as jest.Mock).mockReturnValue({
        data: [mockTrialAgent],
        isLoading: false,
        error: null,
        refetch: jest.fn(),
      });

      const { getByTestId } = renderScreen();
      const agentCard = getByTestId('agent-card-sub_trial_123');

      fireEvent.press(agentCard);

      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith('TrialDashboard', {
          trialId: 'sub_trial_123',
        });
      });
    });

    it('navigates to agent detail when hired agent is pressed', async () => {
      (useHiredAgentsModule.useHiredAgents as jest.Mock).mockReturnValue({
        data: [mockHiredAgent],
        isLoading: false,
        error: null,
        refetch: jest.fn(),
      });
      (useHiredAgentsModule.useAgentsInTrial as jest.Mock).mockReturnValue({
        data: [],
        isLoading: false,
        error: null,
        refetch: jest.fn(),
      });

      const { getByText, getByTestId } = renderScreen();

      // Switch to hired tab
      const hiredTab = getByText('Hired (1)');
      fireEvent.press(hiredTab);

      await waitFor(() => getByTestId('agent-card-sub_hired_456'));
      
      const agentCard = getByTestId('agent-card-sub_hired_456');
      fireEvent.press(agentCard);

      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith('AgentDetail', {
          agentId: 'seo_specialist',
        });
      });
    });
  });

  describe('Pull-to-Refresh', () => {
    it('refetches trial agents when pulled to refresh', async () => {
      const mockRefetch = jest.fn().mockResolvedValue({});
      (useHiredAgentsModule.useHiredAgents as jest.Mock).mockReturnValue({
        data: [mockTrialAgent],
        isLoading: false,
        error: null,
        refetch: mockRefetch,
      });
      (useHiredAgentsModule.useAgentsInTrial as jest.Mock).mockReturnValue({
        data: [mockTrialAgent],
        isLoading: false,
        error: null,
        refetch: mockRefetch,
      });

      const { UNSAFE_getByType } = renderScreen();
      const flatList = UNSAFE_getByType(require('react-native').FlatList);

      // Trigger refresh
      flatList.props.refreshControl.props.onRefresh();

      await waitFor(() => {
        expect(mockRefetch).toHaveBeenCalled();
      });
    });

    it('refetches hired agents when pulled to refresh on hired tab', async () => {
      const mockRefetchTrials = jest.fn();
      const mockRefetchAll = jest.fn().mockResolvedValue({});
      
      (useHiredAgentsModule.useHiredAgents as jest.Mock).mockReturnValue({
        data: [mockHiredAgent],
        isLoading: false,
        error: null,
        refetch: mockRefetchAll,
      });
      (useHiredAgentsModule.useAgentsInTrial as jest.Mock).mockReturnValue({
        data: [],
        isLoading: false,
        error: null,
        refetch: mockRefetchTrials,
      });

      const { getByText, UNSAFE_getByType } = renderScreen();

      // Switch to hired tab
      const hiredTab = getByText('Hired (1)');
      fireEvent.press(hiredTab);

      await waitFor(() => {
        const flatList = UNSAFE_getByType(require('react-native').FlatList);
        flatList.props.refreshControl.props.onRefresh();
      });

      await waitFor(() => {
        expect(mockRefetchAll).toHaveBeenCalled();
        expect(mockRefetchTrials).not.toHaveBeenCalled();
      });
    });
  });

  describe('Multiple Agents', () => {
    it('renders multiple trial agents', () => {
      const anotherTrialAgent: MyAgentInstanceSummary = {
        ...mockTrialAgent,
        subscription_id: 'sub_trial_999',
        agent_id: 'email_marketing',
        nickname: 'Email Agent',
      };

      (useHiredAgentsModule.useHiredAgents as jest.Mock).mockReturnValue({
        data: [mockTrialAgent, anotherTrialAgent],
        isLoading: false,
        error: null,
        refetch: jest.fn(),
      });
      (useHiredAgentsModule.useAgentsInTrial as jest.Mock).mockReturnValue({
        data: [mockTrialAgent, anotherTrialAgent],
        isLoading: false,
        error: null,
        refetch: jest.fn(),
      });

      const { getByText, getByTestId } = renderScreen();

      expect(getByTestId('agent-id-content_marketing')).toBeTruthy();
      expect(getByTestId('agent-id-email_marketing')).toBeTruthy();
      expect(getByText('Active Trials (2)')).toBeTruthy();
    });

    it('renders multiple hired agents', async () => {
      const anotherHiredAgent: MyAgentInstanceSummary = {
        ...mockHiredAgent,
        subscription_id: 'sub_hired_999',
        agent_id: 'ppc_advertising',
        nickname: 'PPC Agent',
      };

      (useHiredAgentsModule.useHiredAgents as jest.Mock).mockReturnValue({
        data: [mockHiredAgent, anotherHiredAgent],
        isLoading: false,
        error: null,
        refetch: jest.fn(),
      });
      (useHiredAgentsModule.useAgentsInTrial as jest.Mock).mockReturnValue({
        data: [],
        isLoading: false,
        error: null,
        refetch: jest.fn(),
      });

      const { getByText, getByTestId } = renderScreen();

      // Switch to hired tab
      const hiredTab = getByText('Hired (2)');
      fireEvent.press(hiredTab);

      await waitFor(() => {
        expect(getByTestId('agent-id-seo_specialist')).toBeTruthy();
        expect(getByTestId('agent-id-ppc_advertising')).toBeTruthy();
      });
    });
  });
});
