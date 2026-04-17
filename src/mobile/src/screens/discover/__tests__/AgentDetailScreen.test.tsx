/**
 * AgentDetailScreen tests
 */
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react-native';

jest.mock('../../../hooks/useTheme', () => ({
  useTheme: () => ({
    colors: {
      primary: '#667eea', textPrimary: '#fff', textSecondary: '#a1a1aa',
      background: '#0a0a0a', surface: '#18181b', border: '#27272a',
      neonCyan: '#00f2fe', card: '#18181b', black: '#0a0a0a',
      success: '#10b981', warning: '#f59e0b', error: '#ef4444',
    },
    spacing: { xs: 4, sm: 8, md: 16, lg: 24, xl: 32, screenPadding: { horizontal: 20, vertical: 16 } },
    typography: {
      fontSize: { xs: 10, sm: 12, md: 14, lg: 16, xl: 20, xxl: 24, xxxl: 32 },
      fontFamily: { body: 'Inter', bodyBold: 'Inter-Bold', heading: 'Outfit', display: 'Space Grotesk' },
    },
  }),
}));

const mockAgentDetail = jest.fn().mockReturnValue({
  data: null, isLoading: false, error: null, refetch: jest.fn(), isRefetching: false,
});
jest.mock('../../../hooks/useAgentDetail', () => ({
  useAgentDetail: () => mockAgentDetail(),
}));

jest.mock('../../../hooks/usePerformanceMonitoring', () => ({
  usePerformanceMonitoring: jest.fn(),
}));

jest.mock('../../../components/LoadingSpinner', () => {
  const { Text } = require('react-native');
  return { LoadingSpinner: ({ message }: any) => <Text>{message ?? 'Loading…'}</Text> };
});

jest.mock('../../../components/ErrorView', () => {
  const { Text, TouchableOpacity } = require('react-native');
  return {
    ErrorView: ({ message, onRetry }: any) => (
      <>
        <Text>{message}</Text>
        <TouchableOpacity onPress={onRetry}><Text>Retry</Text></TouchableOpacity>
      </>
    ),
  };
});

jest.mock('../../../components/voice/VoiceControl', () => ({ VoiceControl: () => null }));
jest.mock('../../../components/voice/VoiceHelpModal', () => ({ VoiceHelpModal: () => null }));

const mockParentNavigate = jest.fn();
const mockNavigate = jest.fn();
const mockGoBack = jest.fn();
jest.mock('@react-navigation/native', () => ({
  useRoute: () => ({ params: { agentId: 'agent-1' } }),
  useNavigation: () => ({
    navigate: mockNavigate,
    goBack: mockGoBack,
    getParent: () => ({ navigate: mockParentNavigate }),
  }),
  RouteProp: jest.fn(),
}));

const MOCK_AGENT = {
  id: 'agent-1',
  name: 'DMA Agent',
  specialization: 'Digital Marketing',
  industry: 'marketing',
  description: 'Handles all your digital marketing needs.',
  skills: ['SEO', 'Content', 'Email'],
  price: 12000,
  rating: 4.5,
  review_count: 23,
  status: 'available',
  trial_days: 7,
};

import { AgentDetailScreen } from '../AgentDetailScreen';

describe('AgentDetailScreen', () => {
  beforeEach(() => jest.clearAllMocks());

  it('shows loading when fetching', () => {
    mockAgentDetail.mockReturnValue({ data: null, isLoading: true, error: null, refetch: jest.fn() });
    render(<AgentDetailScreen />);
    expect(screen.getByText(/loading/i)).toBeTruthy();
  });

  it('shows error view when fetch fails', () => {
    mockAgentDetail.mockReturnValue({ data: null, isLoading: false, error: new Error('Failed'), refetch: jest.fn() });
    render(<AgentDetailScreen />);
    expect(screen.getByText('Failed')).toBeTruthy();
  });

  it('calls refetch on retry', () => {
    const mockRefetch = jest.fn();
    mockAgentDetail.mockReturnValue({ data: null, isLoading: false, error: new Error('Failed'), refetch: mockRefetch });
    render(<AgentDetailScreen />);
    fireEvent.press(screen.getByText('Retry'));
    expect(mockRefetch).toHaveBeenCalled();
  });

  it('renders agent name', () => {
    mockAgentDetail.mockReturnValue({ data: MOCK_AGENT, isLoading: false, error: null, refetch: jest.fn() });
    render(<AgentDetailScreen />);
    expect(screen.getByText('DMA Agent')).toBeTruthy();
  });

  it('renders agent specialty', () => {
    mockAgentDetail.mockReturnValue({ data: MOCK_AGENT, isLoading: false, error: null, refetch: jest.fn() });
    render(<AgentDetailScreen />);
    expect(screen.getByText('Digital Marketing')).toBeTruthy();
  });

  it('renders description', () => {
    mockAgentDetail.mockReturnValue({ data: MOCK_AGENT, isLoading: false, error: null, refetch: jest.fn() });
    render(<AgentDetailScreen />);
    expect(screen.getByText('Handles all your digital marketing needs.')).toBeTruthy();
  });

  it('renders Start Trial button', () => {
    mockAgentDetail.mockReturnValue({ data: MOCK_AGENT, isLoading: false, error: null, refetch: jest.fn() });
    render(<AgentDetailScreen />);
    expect(screen.getByText(/start.*trial|try.*free/i)).toBeTruthy();
  });

  it('Start Trial button is pressable without crash', () => {
    mockAgentDetail.mockReturnValue({ data: MOCK_AGENT, isLoading: false, error: null, refetch: jest.fn(), isRefetching: false });
    render(<AgentDetailScreen />);
    const btn = screen.getByText(/start.*trial|try.*free/i);
    expect(() => fireEvent.press(btn)).not.toThrow();
  });

  it('renders rating stars for agent with rating', () => {
    mockAgentDetail.mockReturnValue({ data: MOCK_AGENT, isLoading: false, error: null, refetch: jest.fn() });
    render(<AgentDetailScreen />);
    // Stars rendered as repeated characters or numeric rating
    expect(screen.getAllByText(/★|4\.5|4,5/).length).toBeGreaterThan(0);
  });

  it('renders "No ratings yet" when agent has no rating', () => {
    const noRating = { ...MOCK_AGENT, rating: undefined, review_count: undefined };
    mockAgentDetail.mockReturnValue({ data: noRating, isLoading: false, error: null, refetch: jest.fn() });
    render(<AgentDetailScreen />);
    expect(screen.getByText(/no ratings yet/i)).toBeTruthy();
  });
});
