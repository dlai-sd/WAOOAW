/**
 * InboxScreen tests
 */
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react-native';
import { InboxScreen } from '@/screens/agents/InboxScreen';

// ─── Mocks ─────────────────────────────────────────────────────────────────

const mockNavigate = jest.fn();
const mockGoBack = jest.fn();
const mockNavigation: any = { navigate: mockNavigate, goBack: mockGoBack };

jest.mock('@/hooks/useTheme', () => ({
  useTheme: () => ({
    colors: {
      primary: '#667eea', textPrimary: '#fff', textSecondary: '#a1a1aa',
      background: '#0a0a0a', surface: '#18181b', border: '#27272a',
      error: '#ef4444', success: '#10b981', warning: '#f59e0b',
      neonCyan: '#00f2fe', card: '#18181b', black: '#0a0a0a',
    },
    spacing: {
      xs: 4, sm: 8, md: 16, lg: 24, xl: 32,
      screenPadding: { horizontal: 20, vertical: 16 },
    },
    typography: {
      fontSize: { xs: 10, sm: 12, md: 14, lg: 16, xl: 20, xxl: 24 },
      fontFamily: { body: 'Inter', bodyBold: 'Inter-Bold', heading: 'Outfit', display: 'Space Grotesk' },
    },
  }),
}));

const mockApprove = jest.fn();
const mockReject = jest.fn();
const mockRefetch = jest.fn();
const mockUseAllDeliverables = jest.fn();

jest.mock('@/hooks/useAllDeliverables', () => ({
  useAllDeliverables: () => mockUseAllDeliverables(),
}));

jest.mock('@/hooks/useAgentVoiceOverlay', () => ({
  useAgentVoiceOverlay: () => ({ isListening: false, toggle: jest.fn(), isAvailable: false }),
}));

jest.mock('@/components/LoadingSpinner', () => {
  const { Text } = require('react-native');
  return { LoadingSpinner: () => <Text>Loading…</Text> };
});

jest.mock('@/components/ErrorView', () => {
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

jest.mock('@/components/EmptyState', () => {
  const { Text } = require('react-native');
  return { EmptyState: ({ title }: any) => <Text>{title ?? 'No deliverables'}</Text> };
});

jest.mock('@/components/voice/VoiceFAB', () => {
  const { TouchableOpacity, Text } = require('react-native');
  return { VoiceFAB: ({ onPress }: any) => <TouchableOpacity onPress={onPress}><Text>🎤</Text></TouchableOpacity> };
});

const MOCK_DELIVERABLE = {
  id: 'DEL-1',
  hired_agent_id: 'ha-1',
  title: 'Test Post',
  description: 'Desc',
  status: 'pending' as const,
  type: 'marketing',
  created_at: '2026-01-01T00:00:00Z',
  agentName: 'DMA Agent',
};

// ─── Tests ─────────────────────────────────────────────────────────────────

describe('InboxScreen', () => {
  beforeEach(() => jest.clearAllMocks());

  it('shows loading spinner while fetching', () => {
    mockUseAllDeliverables.mockReturnValue({ isLoading: true, deliverables: [], error: null, approve: mockApprove, reject: mockReject, refetch: mockRefetch });
    render(<InboxScreen navigation={mockNavigation} route={{} as any} />);
    expect(screen.getByText('Loading…')).toBeTruthy();
  });

  it('shows error view on fetch error', () => {
    mockUseAllDeliverables.mockReturnValue({ isLoading: false, deliverables: [], error: new Error('Bang'), approve: mockApprove, reject: mockReject, refetch: mockRefetch });
    render(<InboxScreen navigation={mockNavigation} route={{} as any} />);
    expect(screen.getByText('Failed to load deliverables')).toBeTruthy();
  });

  it('calls refetch when retry pressed', () => {
    mockUseAllDeliverables.mockReturnValue({ isLoading: false, deliverables: [], error: new Error('Bang'), approve: mockApprove, reject: mockReject, refetch: mockRefetch });
    render(<InboxScreen navigation={mockNavigation} route={{} as any} />);
    fireEvent.press(screen.getByText('Retry'));
    expect(mockRefetch).toHaveBeenCalled();
  });

  it('renders Inbox header', () => {
    mockUseAllDeliverables.mockReturnValue({ isLoading: false, deliverables: [], error: null, approve: mockApprove, reject: mockReject, refetch: mockRefetch });
    render(<InboxScreen navigation={mockNavigation} route={{} as any} />);
    expect(screen.getByText('Inbox')).toBeTruthy();
  });

  it('shows pending count in header', () => {
    mockUseAllDeliverables.mockReturnValue({
      isLoading: false,
      deliverables: [MOCK_DELIVERABLE, { ...MOCK_DELIVERABLE, id: 'DEL-2' }],
      error: null, approve: mockApprove, reject: mockReject, refetch: mockRefetch,
    });
    render(<InboxScreen navigation={mockNavigation} route={{} as any} />);
    expect(screen.getByText('Inbox (2)')).toBeTruthy();
  });

  it('renders filter chips', () => {
    mockUseAllDeliverables.mockReturnValue({ isLoading: false, deliverables: [], error: null, approve: mockApprove, reject: mockReject, refetch: mockRefetch });
    render(<InboxScreen navigation={mockNavigation} route={{} as any} />);
    expect(screen.getByText('All')).toBeTruthy();
    expect(screen.getByText('Pending')).toBeTruthy();
    expect(screen.getByText('Approved')).toBeTruthy();
  });

  it('renders deliverable card title', async () => {
    mockUseAllDeliverables.mockReturnValue({
      isLoading: false,
      deliverables: [MOCK_DELIVERABLE],
      error: null, approve: mockApprove, reject: mockReject, refetch: mockRefetch,
    });
    render(<InboxScreen navigation={mockNavigation} route={{} as any} />);
    await waitFor(() => expect(screen.getByText('Test Post')).toBeTruthy());
  });

  it('filters to pending only when Pending chip pressed', async () => {
    const approvedItem = { ...MOCK_DELIVERABLE, id: 'DEL-2', title: 'Approved Post', status: 'approved' as const };
    mockUseAllDeliverables.mockReturnValue({
      isLoading: false,
      deliverables: [MOCK_DELIVERABLE, approvedItem],
      error: null, approve: mockApprove, reject: mockReject, refetch: mockRefetch,
    });
    render(<InboxScreen navigation={mockNavigation} route={{} as any} />);
    fireEvent.press(screen.getByText('Pending'));
    await waitFor(() => {
      expect(screen.getByText('Test Post')).toBeTruthy();
      expect(screen.queryByText('Approved Post')).toBeNull();
    });
  });

  it('calls approve when Approve button pressed', async () => {
    mockUseAllDeliverables.mockReturnValue({
      isLoading: false,
      deliverables: [MOCK_DELIVERABLE],
      error: null, approve: mockApprove, reject: mockReject, refetch: mockRefetch,
    });
    render(<InboxScreen navigation={mockNavigation} route={{} as any} />);
    await waitFor(() => screen.getByTestId('approve-btn-DEL-1'));
    fireEvent.press(screen.getByTestId('approve-btn-DEL-1'));
    expect(mockApprove).toHaveBeenCalledWith('ha-1', 'DEL-1');
  });

  it('calls reject when Reject button pressed', async () => {
    mockUseAllDeliverables.mockReturnValue({
      isLoading: false,
      deliverables: [MOCK_DELIVERABLE],
      error: null, approve: mockApprove, reject: mockReject, refetch: mockRefetch,
    });
    render(<InboxScreen navigation={mockNavigation} route={{} as any} />);
    await waitFor(() => screen.getByTestId('reject-btn-DEL-1'));
    fireEvent.press(screen.getByTestId('reject-btn-DEL-1'));
    expect(mockReject).toHaveBeenCalledWith('ha-1', 'DEL-1');
  });

  it('navigates to DeliverableDetail when card pressed', async () => {
    mockUseAllDeliverables.mockReturnValue({
      isLoading: false,
      deliverables: [MOCK_DELIVERABLE],
      error: null, approve: mockApprove, reject: mockReject, refetch: mockRefetch,
    });
    render(<InboxScreen navigation={mockNavigation} route={{} as any} />);
    await waitFor(() => screen.getByTestId('deliverable-card-DEL-1'));
    fireEvent.press(screen.getByTestId('deliverable-card-DEL-1'));
    expect(mockNavigate).toHaveBeenCalledWith('DeliverableDetail', {
      deliverableId: 'DEL-1',
      hiredAgentId: 'ha-1',
    });
  });
});
