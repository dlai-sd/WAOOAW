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

const mockGetDeliverablesByHiredAgent = jest.fn();
const mockListPlatformConnections = jest.fn();

// Mock NavigationContainer
jest.mock('@react-navigation/native', () => ({
  ...jest.requireActual('@react-navigation/native'),
  NavigationContainer: ({ children }: { children: React.ReactNode }) => children,
}));

// Mock hooks
jest.mock('@/hooks/useHiredAgents');
jest.mock('@/services/hiredAgents/hiredAgents.service', () => {
  const actual = jest.requireActual('@/services/hiredAgents/hiredAgents.service');
  return {
    ...actual,
    hiredAgentsService: {
      ...actual.hiredAgentsService,
      getDeliverablesByHiredAgent: (...args: unknown[]) => mockGetDeliverablesByHiredAgent(...args),
      listPlatformConnections: (...args: unknown[]) => mockListPlatformConnections(...args),
    },
  };
});

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
const mockParentNavigate = jest.fn();
const mockNavigation = {
  navigate: mockNavigate,
  goBack: jest.fn(),
  setOptions: jest.fn(),
  addListener: jest.fn(() => jest.fn()),
  removeListener: jest.fn(),
  canGoBack: jest.fn(() => true),
  dispatch: jest.fn(),
  isFocused: jest.fn(() => true),
  getParent: jest.fn(() => ({
    navigate: mockParentNavigate,
  })),
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

const mockDigitalMarketingAgent: MyAgentInstanceSummary = {
  subscription_id: 'sub_dma_321',
  agent_id: 'AGT-MKT-DMA-001',
  agent_type_id: 'marketing.digital_marketing.v1',
  duration: 'monthly',
  status: 'active',
  trial_status: 'converted',
  nickname: 'YouTube Growth Agent',
  hired_instance_id: 'hire_dma_321',
  current_period_start: '2024-01-01T00:00:00Z',
  current_period_end: '2024-02-01T00:00:00Z',
  cancel_at_period_end: false,
  configured: true,
  goals_completed: false,
};

describe('MyAgentsScreen', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockNavigate.mockClear();
    mockParentNavigate.mockClear();
    mockGetDeliverablesByHiredAgent.mockResolvedValue([]);
    mockListPlatformConnections.mockResolvedValue([]);
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

      const { getAllByText, getByText } = renderScreen();

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

      const { getAllByText, getByText } = renderScreen();

      // Switch to hired tab
      const hiredTab = getByText(/Hired \(\d+\)/);
      fireEvent.press(hiredTab);

      expect(getByText('No agents hired yet')).toBeTruthy();
      expect(getByText('Your agents will appear here once you hire one. Try a 7-day free trial — keep everything they build.')).toBeTruthy();
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
        expect(mockParentNavigate).toHaveBeenCalledWith('DiscoverTab', {
          screen: 'Discover',
        });
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

      const screenResult = renderScreen();

      // Switch to hired tab
      const hiredTab = screenResult.getByText('Hired (1)');
      fireEvent.press(hiredTab);

      await waitFor(() => {
        expect(screenResult.getAllByText('Subscription ending soon').length).toBeGreaterThan(0);
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
        expect(mockNavigate).toHaveBeenCalledWith('AgentOperations', {
          hiredAgentId: 'hire_456',
        });
      });
    });

    it('routes digital marketing hires back to Theme Discovery when goals are incomplete', async () => {
      (useHiredAgentsModule.useHiredAgents as jest.Mock).mockReturnValue({
        data: [mockDigitalMarketingAgent],
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

      fireEvent.press(getByText('Hired (1)'));

      await waitFor(() => getByTestId('agent-card-sub_dma_321'));
      expect(getByText('Tap to resume Theme Discovery →')).toBeTruthy();

      fireEvent.press(getByTestId('agent-card-sub_dma_321'));

      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith('AgentOperations', {
          hiredAgentId: 'hire_dma_321',
          focusSection: 'goals',
        });
      });
    });

    it('shows truthful digital marketing publish progress on hired agent cards', async () => {
      mockGetDeliverablesByHiredAgent.mockResolvedValueOnce([
        {
          deliverable_id: 'DEL-1',
          hired_instance_id: 'hire_dma_321',
          agent_id: 'AGT-MKT-DMA-001',
          title: 'YouTube explainer draft',
          type: 'document',
          review_status: 'approved',
          execution_status: 'not_executed',
          payload: {
            destination: {
              destination_type: 'youtube',
              metadata: { visibility: 'private' },
            },
          },
          created_at: '2026-03-11T08:00:00Z',
          updated_at: '2026-03-11T08:30:00Z',
        },
      ]);
      mockListPlatformConnections.mockResolvedValueOnce([]);

      (useHiredAgentsModule.useHiredAgents as jest.Mock).mockReturnValue({
        data: [{ ...mockDigitalMarketingAgent, goals_completed: true }],
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
      fireEvent.press(getByText('Hired (1)'));

      await waitFor(() => {
        expect(getByText('Publish readiness: Blocked by missing channel connection')).toBeTruthy();
        expect(getByText('Channel: Youtube not connected')).toBeTruthy();
      });

      expect(getByText('Approve is complete, but YouTube still needs a verified connection before upload can happen.')).toBeTruthy();
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
      // eslint-disable-next-line @typescript-eslint/no-require-imports
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
        // eslint-disable-next-line @typescript-eslint/no-require-imports
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

  // ── Sort controls (hired tab only) ────────────────────────────────────────

  describe('Sort Controls', () => {
    const setupHiredAgents = () => {
      (useHiredAgentsModule.useHiredAgents as jest.Mock).mockReturnValue({
        data: [mockHiredAgent, mockHiredAgentEnding],
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
    };

    it('shows sort chips in hired tab', async () => {
      setupHiredAgents();
      const { getByText, getByTestId } = renderScreen();
      fireEvent.press(getByText('Hired (2)'));
      await waitFor(() => {
        expect(getByTestId('sort-chip-attention')).toBeTruthy();
        expect(getByTestId('sort-chip-alphabetical')).toBeTruthy();
        expect(getByTestId('sort-chip-recent')).toBeTruthy();
      });
    });

    it('does not show sort chips in trials tab', () => {
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
      const { queryByTestId } = renderScreen();
      expect(queryByTestId('sort-chip-attention')).toBeNull();
    });

    it('switches to alphabetical sort', async () => {
      setupHiredAgents();
      const { getByText, getByTestId } = renderScreen();
      fireEvent.press(getByText('Hired (2)'));
      await waitFor(() => getByTestId('sort-chip-alphabetical'));
      fireEvent.press(getByTestId('sort-chip-alphabetical'));
      await waitFor(() => {
        expect(getByTestId('agent-id-seo_specialist')).toBeTruthy();
      });
    });

    it('switches to recent sort', async () => {
      setupHiredAgents();
      const { getByText, getByTestId } = renderScreen();
      fireEvent.press(getByText('Hired (2)'));
      await waitFor(() => getByTestId('sort-chip-recent'));
      fireEvent.press(getByTestId('sort-chip-recent'));
      await waitFor(() => {
        expect(getByTestId('agent-id-seo_specialist')).toBeTruthy();
      });
    });
  });

  // ── Fallback navigation (no hired_instance_id) ────────────────────────────

  describe('Fallback navigation', () => {
    it('navigates to AgentDetail when agent has no hired_instance_id', async () => {
      const noInstanceAgent: MyAgentInstanceSummary = {
        ...mockHiredAgent,
        subscription_id: 'sub_no_inst',
        agent_id: 'bare_agent',
        nickname: 'Bare Agent',
        trial_status: 'converted',
        hired_instance_id: undefined as unknown as string,
      };
      (useHiredAgentsModule.useHiredAgents as jest.Mock).mockReturnValue({
        data: [noInstanceAgent],
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
      fireEvent.press(getByText('Hired (1)'));
      await waitFor(() => getByTestId('agent-card-sub_no_inst'));
      fireEvent.press(getByTestId('agent-card-sub_no_inst'));

      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith('AgentDetail', { agentId: 'bare_agent' });
      });
    });
  });

  // ── Needs-attention pill ──────────────────────────────────────────────────

  describe('Attention count pill', () => {
    it('shows correct needs-attention count in header pill', () => {
      (useHiredAgentsModule.useHiredAgents as jest.Mock).mockReturnValue({
        data: [mockHiredAgentEnding, mockHiredAgent],
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
      expect(getByText('1 need attention')).toBeTruthy();
    });
  });

  // ── Auto tab switch ───────────────────────────────────────────────────────

  describe('Auto tab switch', () => {
    it('switches to hired tab automatically when no trials but hired agents exist', async () => {
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

      const { getByTestId } = renderScreen();
      // Should auto-switch to hired tab
      await waitFor(() => {
        expect(getByTestId('agent-id-seo_specialist')).toBeTruthy();
      });
    });
  });

  // ── Status tone colour ────────────────────────────────────────────────────

  describe('statusToneColor info/neutral tone', () => {
    it('renders deliverable readiness with info tone (neonCyan) for neutral status', async () => {
      mockGetDeliverablesByHiredAgent.mockResolvedValueOnce([
        {
          deliverable_id: 'DEL-info',
          hired_instance_id: 'hire_dma_321',
          agent_id: 'AGT-MKT-DMA-001',
          title: 'LinkedIn post draft',
          type: 'document',
          review_status: 'pending_review',
          execution_status: 'not_executed',
          payload: {
            destination: {
              destination_type: 'linkedin',
              metadata: {},
            },
          },
          created_at: '2026-03-11T08:00:00Z',
          updated_at: '2026-03-11T08:30:00Z',
        },
      ]);
      mockListPlatformConnections.mockResolvedValueOnce([
        {
          id: 'conn-li',
          hired_instance_id: 'hire_dma_321',
          platform_key: 'linkedin',
          status: 'connected',
          created_at: '2026-01-01',
          updated_at: '2026-01-01',
        },
      ]);

      (useHiredAgentsModule.useHiredAgents as jest.Mock).mockReturnValue({
        data: [{ ...mockDigitalMarketingAgent, goals_completed: true }],
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
      fireEvent.press(getByText('Hired (1)'));

      // Renders without crashing — info tone path exercised via statusToneColor
      await waitFor(() => {
        expect(getByText('YouTube Growth Agent')).toBeTruthy();
      });
    });
  });

  // ── getAttentionReasons branches ─────────────────────────────────────────

  describe('getAttentionReasons', () => {
    it('no attention reasons when hired agent is fully configured with goals complete', async () => {
      const fullyConfiguredHiredAgent: MyAgentInstanceSummary = {
        ...mockHiredAgent,
        subscription_id: 'sub_full',
        agent_id: 'full_agent',
        nickname: 'Full Agent',
        trial_status: 'converted',
        cancel_at_period_end: false,
        configured: true,
        goals_completed: true,
        hired_instance_id: 'hire_full',
      };
      (useHiredAgentsModule.useHiredAgents as jest.Mock).mockReturnValue({
        data: [fullyConfiguredHiredAgent],
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
      fireEvent.press(getByText('Hired (1)'));
      await waitFor(() => expect(getByText('Full Agent')).toBeTruthy());
      // 0 needs attention count — pill should show 0
      expect(getByText('0 need attention')).toBeTruthy();
    });

    it('shows goals-need-review reason for hired agent with goals_completed=false', async () => {
      const incompleteGoalsAgent: MyAgentInstanceSummary = {
        ...mockHiredAgent,
        subscription_id: 'sub_goals',
        agent_id: 'goals_agent',
        nickname: 'Goals Agent',
        trial_status: 'converted',
        hired_instance_id: 'hire_goals',
        cancel_at_period_end: false,
        configured: true,
        goals_completed: false,
      };
      (useHiredAgentsModule.useHiredAgents as jest.Mock).mockReturnValue({
        data: [incompleteGoalsAgent],
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

      const { getByText, getAllByText } = renderScreen();
      fireEvent.press(getByText('Hired (1)'));
      await waitFor(() => expect(getAllByText('Goals need review').length).toBeGreaterThanOrEqual(1));
    });

    it('shows runtime-configuration-incomplete reason for hired unconfigured agent', async () => {
      const unconfiguredHiredAgent: MyAgentInstanceSummary = {
        ...mockHiredAgent,
        subscription_id: 'sub_unconf',
        agent_id: 'unconf_agent',
        nickname: 'Unconf Agent',
        trial_status: 'converted',
        hired_instance_id: 'hire_unconf',
        cancel_at_period_end: false,
        configured: false,
        goals_completed: true,
      };
      (useHiredAgentsModule.useHiredAgents as jest.Mock).mockReturnValue({
        data: [unconfiguredHiredAgent],
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

      const { getByText: getText2, getAllByText: getAll2 } = renderScreen();
      fireEvent.press(getText2('Hired (1)'));
      await waitFor(() => expect(getAll2('Runtime configuration incomplete').length).toBeGreaterThanOrEqual(1));
    });

    it('shows trial-goal-incomplete reason for trial agent with goals_completed=false', async () => {
      const trialGoalIncomplete: MyAgentInstanceSummary = {
        ...mockTrialAgent,
        subscription_id: 'sub_tg',
        agent_id: 'tg_agent',
        nickname: 'TG Agent',
        trial_status: 'active',
        configured: true,
        goals_completed: false,
      };
      (useHiredAgentsModule.useHiredAgents as jest.Mock).mockReturnValue({
        data: [trialGoalIncomplete],
        isLoading: false,
        error: null,
        refetch: jest.fn(),
      });
      (useHiredAgentsModule.useAgentsInTrial as jest.Mock).mockReturnValue({
        data: [trialGoalIncomplete],
        isLoading: false,
        error: null,
        refetch: jest.fn(),
      });

      const { getByText } = renderScreen();
      await waitFor(() => expect(getByText('Goal setup incomplete')).toBeTruthy());
    });
  });

  // ── trial agent without subscription_id press ─────────────────────────────

  describe('Trial agent without subscription_id', () => {
    it('falls through to AgentOperations when trial agent has no subscription_id but has hired_instance_id', async () => {
      const trialNoSubId: MyAgentInstanceSummary = {
        ...mockTrialAgent,
        subscription_id: undefined as unknown as string,
        trial_status: 'active',
        hired_instance_id: 'hire_no_sub',
      };
      (useHiredAgentsModule.useHiredAgents as jest.Mock).mockReturnValue({
        data: [trialNoSubId],
        isLoading: false,
        error: null,
        refetch: jest.fn(),
      });
      (useHiredAgentsModule.useAgentsInTrial as jest.Mock).mockReturnValue({
        data: [trialNoSubId],
        isLoading: false,
        error: null,
        refetch: jest.fn(),
      });

      const { getByTestId } = renderScreen();
      await waitFor(() => getByTestId('agent-card-undefined'));
      fireEvent.press(getByTestId('agent-card-undefined'));

      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith('AgentOperations', {
          hiredAgentId: 'hire_no_sub',
        });
      });
    });
  });
});
