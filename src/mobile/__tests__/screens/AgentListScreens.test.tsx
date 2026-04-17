/**
 * ActiveTrialsListScreen and HiredAgentsListScreen tests
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react-native';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

const mockUseHiredAgents = jest.fn();

jest.mock('@/hooks/useHiredAgents', () => ({
  useHiredAgents: () => mockUseHiredAgents(),
}));

jest.mock('@/hooks/useTheme', () => ({
  useTheme: () => ({
    colors: {
      black: '#0a0a0a',
      textPrimary: '#ffffff',
      textSecondary: '#a1a1aa',
      neonCyan: '#00f2fe',
      card: '#18181b',
      border: '#374151',
    },
    spacing: {
      xs: 4, sm: 8, md: 16, lg: 24, xl: 32,
      screenPadding: { horizontal: 16, vertical: 20 },
    },
    typography: {
      fontFamily: { display: 'SpaceGrotesk_700Bold', body: 'Inter_400Regular', bodyBold: 'Inter_600SemiBold' },
    },
  }),
}));

jest.mock('@/components/LoadingSpinner', () => ({
  LoadingSpinner: () => {
    const { View } = require('react-native');
    return <View testID="loading-spinner" />;
  },
}));

import { ActiveTrialsListScreen } from '@/screens/agents/ActiveTrialsListScreen';
import { HiredAgentsListScreen } from '@/screens/agents/HiredAgentsListScreen';

const mockNavigation = { navigate: jest.fn(), goBack: jest.fn() } as any;
const mockRoute = { params: {}, key: 'test', name: 'ActiveTrialsList' } as any;

function withQuery(ui: React.ReactElement) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return <QueryClientProvider client={qc}>{ui}</QueryClientProvider>;
}

describe('ActiveTrialsListScreen', () => {
  beforeEach(() => jest.clearAllMocks());

  it('shows loading spinner while fetching', () => {
    mockUseHiredAgents.mockReturnValue({ data: [], isLoading: true });
    render(withQuery(<ActiveTrialsListScreen navigation={mockNavigation} route={mockRoute} />));
    expect(screen.getByTestId('loading-spinner')).toBeTruthy();
  });

  it('shows empty state when no active trials', () => {
    mockUseHiredAgents.mockReturnValue({ data: [], isLoading: false });
    render(withQuery(<ActiveTrialsListScreen navigation={mockNavigation} route={mockRoute} />));
    expect(screen.getByText(/no active trials/i)).toBeTruthy();
  });

  it('lists agents with active trial status', () => {
    mockUseHiredAgents.mockReturnValue({
      data: [
        { hired_instance_id: 'hi1', nickname: 'My Agent', trial_status: 'active', agent_id: 'agt1' },
        { hired_instance_id: 'hi2', nickname: 'Other Agent', trial_status: 'expired', agent_id: 'agt2' },
      ],
      isLoading: false,
    });
    render(withQuery(<ActiveTrialsListScreen navigation={mockNavigation} route={mockRoute} />));
    expect(screen.getByText('My Agent')).toBeTruthy();
    expect(screen.queryByText('Other Agent')).toBeNull();
  });

  it('goBack navigates back on ← Back press', () => {
    mockUseHiredAgents.mockReturnValue({ data: [], isLoading: false });
    render(withQuery(<ActiveTrialsListScreen navigation={mockNavigation} route={mockRoute} />));
    fireEvent.press(screen.getByText('← Back'));
    expect(mockNavigation.goBack).toHaveBeenCalled();
  });
});

describe('HiredAgentsListScreen', () => {
  beforeEach(() => jest.clearAllMocks());

  it('shows loading spinner while fetching', () => {
    mockUseHiredAgents.mockReturnValue({ data: [], isLoading: true });
    render(withQuery(<HiredAgentsListScreen navigation={mockNavigation} route={{ ...mockRoute, name: 'HiredAgentsList' }} />));
    expect(screen.getByTestId('loading-spinner')).toBeTruthy();
  });

  it('shows empty state when no hired agents', () => {
    mockUseHiredAgents.mockReturnValue({ data: [], isLoading: false });
    render(withQuery(<HiredAgentsListScreen navigation={mockNavigation} route={{ ...mockRoute, name: 'HiredAgentsList' }} />));
    expect(screen.getByText(/no hired agents/i)).toBeTruthy();
  });

  it('lists agents not in active trial', () => {
    mockUseHiredAgents.mockReturnValue({
      data: [
        { hired_instance_id: 'hi1', nickname: 'My Agent', trial_status: 'active', agent_id: 'agt1' },
        { hired_instance_id: 'hi2', nickname: 'Hired Agent', trial_status: 'expired', agent_id: 'agt2' },
      ],
      isLoading: false,
    });
    render(withQuery(<HiredAgentsListScreen navigation={mockNavigation} route={{ ...mockRoute, name: 'HiredAgentsList' }} />));
    expect(screen.getByText('Hired Agent')).toBeTruthy();
    expect(screen.queryByText('My Agent')).toBeNull();
  });

  it('goBack navigates back on ← Back press', () => {
    mockUseHiredAgents.mockReturnValue({ data: [], isLoading: false });
    render(withQuery(<HiredAgentsListScreen navigation={mockNavigation} route={{ ...mockRoute, name: 'HiredAgentsList' }} />));
    fireEvent.press(screen.getByText('← Back'));
    expect(mockNavigation.goBack).toHaveBeenCalled();
  });
});
