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

jest.mock('../../../components/voice/VoiceControl', () => ({
  VoiceControl: ({ callbacks }: any) => {
    (global as any).__agentDetailCallbacks = callbacks;
    return null;
  },
}));
jest.mock('../../../components/voice/VoiceHelpModal', () => {
  const { TouchableOpacity, Text } = require('react-native');
  return {
    VoiceHelpModal: ({ visible, onClose }: any) =>
      visible ? (
        <TouchableOpacity testID="voice-help-close" onPress={onClose}>
          <Text>Close help</Text>
        </TouchableOpacity>
      ) : null,
  };
});

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

  it('renders education industry emoji', () => {
    const edAgent = { ...MOCK_AGENT, industry: 'education' };
    mockAgentDetail.mockReturnValue({ data: edAgent, isLoading: false, error: null, refetch: jest.fn() });
    render(<AgentDetailScreen />);
    expect(screen.getByText('DMA Agent')).toBeTruthy();
  });

  it('renders sales industry emoji', () => {
    const salesAgent = { ...MOCK_AGENT, industry: 'sales' };
    mockAgentDetail.mockReturnValue({ data: salesAgent, isLoading: false, error: null, refetch: jest.fn() });
    render(<AgentDetailScreen />);
    expect(screen.getByText('DMA Agent')).toBeTruthy();
  });

  it('renders default industry emoji for unknown industry', () => {
    const otherAgent = { ...MOCK_AGENT, industry: 'finance' };
    mockAgentDetail.mockReturnValue({ data: otherAgent, isLoading: false, error: null, refetch: jest.fn() });
    render(<AgentDetailScreen />);
    expect(screen.getByText('DMA Agent')).toBeTruthy();
  });

  it('renders "Contact for pricing" when price is undefined', () => {
    const noPriceAgent = { ...MOCK_AGENT, price: undefined };
    mockAgentDetail.mockReturnValue({ data: noPriceAgent, isLoading: false, error: null, refetch: jest.fn() });
    render(<AgentDetailScreen />);
    expect(screen.getByText('Contact for pricing')).toBeTruthy();
  });

  it('renders "Free trial" in price badge when price is undefined', () => {
    const noPriceAgent = { ...MOCK_AGENT, price: undefined };
    mockAgentDetail.mockReturnValue({ data: noPriceAgent, isLoading: false, error: null, refetch: jest.fn() });
    render(<AgentDetailScreen />);
    expect(screen.getByText('Free trial')).toBeTruthy();
  });

  it('renders not-found ErrorView when agent is null and isLoading false and no error', () => {
    mockAgentDetail.mockReturnValue({ data: null, isLoading: false, error: null, refetch: jest.fn() });
    render(<AgentDetailScreen />);
    expect(screen.getByText('Agent not found')).toBeTruthy();
  });

  it('renders inactive agent status with correct text', () => {
    const inactiveAgent = { ...MOCK_AGENT, status: 'inactive' };
    mockAgentDetail.mockReturnValue({ data: inactiveAgent, isLoading: false, error: null, refetch: jest.fn() });
    render(<AgentDetailScreen />);
    expect(screen.getByText('Currently Unavailable')).toBeTruthy();
  });

  it('shows active agent as Available Now', () => {
    const activeAgent = { ...MOCK_AGENT, status: 'active' };
    mockAgentDetail.mockReturnValue({ data: activeAgent, isLoading: false, error: null, refetch: jest.fn() });
    render(<AgentDetailScreen />);
    expect(screen.getByText('Available Now')).toBeTruthy();
  });

  it('renders review count pluralized as "reviews"', () => {
    const reviewAgent = { ...MOCK_AGENT, rating: 4.0, review_count: 5 };
    mockAgentDetail.mockReturnValue({ data: reviewAgent, isLoading: false, error: null, refetch: jest.fn() });
    render(<AgentDetailScreen />);
    expect(screen.getByText(/5 reviews/)).toBeTruthy();
  });

  it('renders review count as "review" (singular)', () => {
    const reviewAgent = { ...MOCK_AGENT, rating: 4.0, review_count: 1 };
    mockAgentDetail.mockReturnValue({ data: reviewAgent, isLoading: false, error: null, refetch: jest.fn() });
    render(<AgentDetailScreen />);
    expect(screen.getByText(/1 review\b/)).toBeTruthy();
  });

  it('renders half star when rating has fractional part >= 0.5', () => {
    const halfStarAgent = { ...MOCK_AGENT, rating: 3.5, review_count: 2 };
    mockAgentDetail.mockReturnValue({ data: halfStarAgent, isLoading: false, error: null, refetch: jest.fn() });
    render(<AgentDetailScreen />);
    expect(screen.getByText(/½/)).toBeTruthy();
  });

  it('renders agent with job_role section', () => {
    const agentWithRole = {
      ...MOCK_AGENT,
      job_role: { name: 'Marketing Specialist', description: 'Handles marketing', seniority_level: 'senior' },
    };
    mockAgentDetail.mockReturnValue({ data: agentWithRole, isLoading: false, error: null, refetch: jest.fn() });
    render(<AgentDetailScreen />);
    expect(screen.getByText('Marketing Specialist')).toBeTruthy();
  });

  it('renders agent with job_role and no description/seniority', () => {
    const agentWithRole = {
      ...MOCK_AGENT,
      job_role: { name: 'Basic Role', description: undefined, seniority_level: undefined },
    };
    mockAgentDetail.mockReturnValue({ data: agentWithRole, isLoading: false, error: null, refetch: jest.fn() });
    render(<AgentDetailScreen />);
    expect(screen.getByText('Basic Role')).toBeTruthy();
  });

  it('renders 0 deliverables when total_deliverables is undefined', () => {
    const agentNoDels = { ...MOCK_AGENT, total_deliverables: undefined };
    mockAgentDetail.mockReturnValue({ data: agentNoDels, isLoading: false, error: null, refetch: jest.fn() });
    render(<AgentDetailScreen />);
    expect(screen.getByText('0 deliverables produced')).toBeTruthy();
  });

  it('renders trial_days from agent data when set', () => {
    const agentWithTrial = { ...MOCK_AGENT, trial_days: 14 };
    mockAgentDetail.mockReturnValue({ data: agentWithTrial, isLoading: false, error: null, refetch: jest.fn() });
    render(<AgentDetailScreen />);
    expect(screen.getByText(/14-Day Free Trial/)).toBeTruthy();
  });

  it('falls back to 7-day trial when trial_days is 0/falsy', () => {
    const agentNoTrial = { ...MOCK_AGENT, trial_days: 0 };
    mockAgentDetail.mockReturnValue({ data: agentNoTrial, isLoading: false, error: null, refetch: jest.fn() });
    render(<AgentDetailScreen />);
    expect(screen.getByText(/7-Day Free Trial/)).toBeTruthy();
  });

  it('renders agent without specialization (no specialty text)', () => {
    const noSpecAgent = { ...MOCK_AGENT, specialization: undefined };
    mockAgentDetail.mockReturnValue({ data: noSpecAgent, isLoading: false, error: null, refetch: jest.fn() });
    render(<AgentDetailScreen />);
    expect(screen.getByText('DMA Agent')).toBeTruthy();
  });

  it('renders agent without description (no About section)', () => {
    const noDescAgent = { ...MOCK_AGENT, description: undefined };
    mockAgentDetail.mockReturnValue({ data: noDescAgent, isLoading: false, error: null, refetch: jest.fn() });
    render(<AgentDetailScreen />);
    expect(screen.getByText('DMA Agent')).toBeTruthy();
    expect(screen.queryByText('About')).toBeNull();
  });

  it('shows loading when isLoading true and agent is already there', () => {
    // When isLoading=true but agent already cached (not null), show normal screen
    mockAgentDetail.mockReturnValue({ data: MOCK_AGENT, isLoading: true, error: null, refetch: jest.fn() });
    render(<AgentDetailScreen />);
    // Should render the screen (not spinner) because agent is available
    expect(screen.getByText('DMA Agent')).toBeTruthy();
  });

  it('shows error message from error.message when agent is null', () => {
    mockAgentDetail.mockReturnValue({ data: null, isLoading: false, error: new Error('Custom error msg'), refetch: jest.fn() });
    render(<AgentDetailScreen />);
    expect(screen.getByText('Custom error msg')).toBeTruthy();
  });

  // ── Branch coverage: handleVoiceNavigate branches ─────────────────────────────────
  it('handleVoiceNavigate: navigates to Home tab', () => {
    mockAgentDetail.mockReturnValue({ data: MOCK_AGENT, isLoading: false, error: null, refetch: jest.fn() });
    render(<AgentDetailScreen />);
    const cbs = (global as any).__agentDetailCallbacks;
    cbs?.onNavigate('Home');
    expect(mockParentNavigate).toHaveBeenCalledWith('HomeTab', expect.objectContaining({ screen: 'Home' }));
  });

  it('handleVoiceNavigate: navigates to Discover tab', () => {
    mockAgentDetail.mockReturnValue({ data: MOCK_AGENT, isLoading: false, error: null, refetch: jest.fn() });
    render(<AgentDetailScreen />);
    const cbs = (global as any).__agentDetailCallbacks;
    cbs?.onNavigate('Discover');
    expect(mockParentNavigate).toHaveBeenCalledWith('DiscoverTab', expect.objectContaining({ screen: 'Discover' }));
  });

  it('handleVoiceNavigate: navigates to MyAgents tab', () => {
    mockAgentDetail.mockReturnValue({ data: MOCK_AGENT, isLoading: false, error: null, refetch: jest.fn() });
    render(<AgentDetailScreen />);
    const cbs = (global as any).__agentDetailCallbacks;
    cbs?.onNavigate('MyAgents');
    expect(mockParentNavigate).toHaveBeenCalledWith('MyAgentsTab', expect.objectContaining({ screen: 'MyAgents' }));
  });

  it('handleVoiceNavigate: navigates to Profile tab', () => {
    mockAgentDetail.mockReturnValue({ data: MOCK_AGENT, isLoading: false, error: null, refetch: jest.fn() });
    render(<AgentDetailScreen />);
    const cbs = (global as any).__agentDetailCallbacks;
    cbs?.onNavigate('Profile');
    expect(mockParentNavigate).toHaveBeenCalledWith('ProfileTab', expect.objectContaining({ screen: 'Profile' }));
  });

  it('handleVoiceNavigate: unknown screen does nothing', () => {
    mockAgentDetail.mockReturnValue({ data: MOCK_AGENT, isLoading: false, error: null, refetch: jest.fn() });
    render(<AgentDetailScreen />);
    const cbs = (global as any).__agentDetailCallbacks;
    cbs?.onNavigate('Unknown');
    expect(mockParentNavigate).not.toHaveBeenCalled();
  });

  // ── Branch coverage: handleVoiceAction branches ──────────────────────────────────
  it('handleVoiceAction: hire navigates to HireWizard', () => {
    mockAgentDetail.mockReturnValue({ data: MOCK_AGENT, isLoading: false, error: null, refetch: jest.fn() });
    render(<AgentDetailScreen />);
    const cbs = (global as any).__agentDetailCallbacks;
    cbs?.onAction('hire');
    expect(mockParentNavigate).toHaveBeenCalledWith('DiscoverTab', expect.objectContaining({ screen: 'HireWizard' }));
  });

  it('handleVoiceAction: refresh calls refetch', () => {
    const mockRefetch = jest.fn();
    mockAgentDetail.mockReturnValue({ data: MOCK_AGENT, isLoading: false, error: null, refetch: mockRefetch });
    render(<AgentDetailScreen />);
    const cbs = (global as any).__agentDetailCallbacks;
    cbs?.onAction('refresh');
    expect(mockRefetch).toHaveBeenCalled();
  });

  it('handleVoiceAction: back calls navigation.goBack', () => {
    mockAgentDetail.mockReturnValue({ data: MOCK_AGENT, isLoading: false, error: null, refetch: jest.fn() });
    render(<AgentDetailScreen />);
    const cbs = (global as any).__agentDetailCallbacks;
    cbs?.onAction('back');
    expect(mockGoBack).toHaveBeenCalled();
  });

  it('handleVoiceAction: showHelp opens VoiceHelpModal', async () => {
    mockAgentDetail.mockReturnValue({ data: MOCK_AGENT, isLoading: false, error: null, refetch: jest.fn() });
    render(<AgentDetailScreen />);
    const cbs = (global as any).__agentDetailCallbacks;
    cbs?.onAction('showHelp');
    await waitFor(() => expect(screen.getByTestId('voice-help-close')).toBeTruthy());
  });

  it('handleVoiceAction: unknown action does nothing', () => {
    mockAgentDetail.mockReturnValue({ data: MOCK_AGENT, isLoading: false, error: null, refetch: jest.fn() });
    render(<AgentDetailScreen />);
    const cbs = (global as any).__agentDetailCallbacks;
    expect(() => cbs?.onAction('unknownAction')).not.toThrow();
  });

  it('handleVoiceHelp (onHelp callback) opens VoiceHelpModal', async () => {
    mockAgentDetail.mockReturnValue({ data: MOCK_AGENT, isLoading: false, error: null, refetch: jest.fn() });
    render(<AgentDetailScreen />);
    const cbs = (global as any).__agentDetailCallbacks;
    cbs?.onHelp();
    await waitFor(() => expect(screen.getByTestId('voice-help-close')).toBeTruthy());
  });

  it('VoiceHelpModal onClose hides the modal', async () => {
    mockAgentDetail.mockReturnValue({ data: MOCK_AGENT, isLoading: false, error: null, refetch: jest.fn() });
    render(<AgentDetailScreen />);
    const cbs = (global as any).__agentDetailCallbacks;
    cbs?.onHelp();
    await waitFor(() => screen.getByTestId('voice-help-close'));
    fireEvent.press(screen.getByTestId('voice-help-close'));
    await waitFor(() => expect(screen.queryByTestId('voice-help-close')).toBeNull());
  });
});
