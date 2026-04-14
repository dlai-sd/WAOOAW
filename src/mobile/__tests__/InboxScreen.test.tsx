/**
 * InboxScreen Tests (MOB-PARITY-1 E1-S1)
 */

import React from 'react';
import { render, fireEvent } from '@testing-library/react-native';

// ─── Shared mock theme ────────────────────────────────────────────────────────

const mockTheme = {
  colors: {
    black: '#0a0a0a',
    neonCyan: '#00f2fe',
    neonPurple: '#667eea',
    textPrimary: '#ffffff',
    textSecondary: '#a1a1aa',
    card: '#18181b',
    error: '#ef4444',
    success: '#10b981',
    warning: '#f59e0b',
    border: '#374151',
    background: '#0a0a0a',
  },
  spacing: {
    xs: 4,
    sm: 8,
    md: 16,
    lg: 24,
    xl: 32,
    xxl: 48,
    screenPadding: { horizontal: 20, vertical: 20 },
  },
  typography: {
    fontFamily: {
      display: 'SpaceGrotesk_700Bold',
      body: 'Inter_400Regular',
      bodyBold: 'Inter_600SemiBold',
    },
  },
};

// ─── Mocks ────────────────────────────────────────────────────────────────────

jest.mock('../src/hooks/useTheme', () => ({ useTheme: () => mockTheme }));

const mockApprove = jest.fn(() => Promise.resolve());
const mockReject = jest.fn(() => Promise.resolve());
const mockRefetch = jest.fn();

const mockUseAllDeliverables = jest.fn();
jest.mock('../src/hooks/useAllDeliverables', () => ({
  useAllDeliverables: () => mockUseAllDeliverables(),
}));

const mockToggle = jest.fn();
jest.mock('../src/hooks/useAgentVoiceOverlay', () => ({
  useAgentVoiceOverlay: () => ({
    isListening: false,
    toggle: mockToggle,
    lastCommand: null,
    isAvailable: true,
  }),
}));

jest.mock('@shopify/flash-list', () => {
  const { FlatList } = require('react-native');
  return { FlashList: FlatList };
});

import { InboxScreen } from '../src/screens/agents/InboxScreen';

// ─── Tests ────────────────────────────────────────────────────────────────────

describe('InboxScreen', () => {
  const deliverables = [
    {
      id: 'd1',
      hired_agent_id: 'ha1',
      type: 'content_draft',
      title: 'Monthly report',
      status: 'pending' as const,
      created_at: '2026-01-01T00:00:00Z',
    },
    {
      id: 'd2',
      hired_agent_id: 'ha1',
      type: 'content_draft',
      title: 'Q2 summary',
      status: 'approved' as const,
      created_at: '2026-01-02T00:00:00Z',
    },
    {
      id: 'd3',
      hired_agent_id: 'ha2',
      type: 'trade_plan',
      title: 'Trade idea',
      status: 'rejected' as const,
      created_at: '2026-01-03T00:00:00Z',
    },
  ];

  beforeEach(() => {
    jest.clearAllMocks();
    mockUseAllDeliverables.mockReturnValue({
      deliverables,
      isLoading: false,
      error: null,
      approve: mockApprove,
      reject: mockReject,
      refetch: mockRefetch,
    });
  });

  it('renders all deliverable cards', () => {
    const { getByTestId } = render(<InboxScreen />);
    expect(getByTestId('inbox-screen')).toBeTruthy();
    expect(getByTestId('deliverable-card-d1')).toBeTruthy();
    expect(getByTestId('deliverable-card-d2')).toBeTruthy();
    expect(getByTestId('deliverable-card-d3')).toBeTruthy();
  });

  it('filters deliverables to Pending only', () => {
    const { getByTestId, queryByTestId } = render(<InboxScreen />);
    fireEvent.press(getByTestId('filter-chip-pending'));
    // Only pending card should be visible
    expect(getByTestId('deliverable-card-d1')).toBeTruthy();
    expect(queryByTestId('deliverable-card-d2')).toBeNull();
    expect(queryByTestId('deliverable-card-d3')).toBeNull();
  });

  it('renders LoadingSpinner when loading', () => {
    mockUseAllDeliverables.mockReturnValue({
      deliverables: [],
      isLoading: true,
      error: null,
      approve: mockApprove,
      reject: mockReject,
      refetch: mockRefetch,
    });
    const { UNSAFE_getByType } = render(<InboxScreen />);
    const { LoadingSpinner } = require('../src/components/LoadingSpinner');
    expect(UNSAFE_getByType(LoadingSpinner)).toBeTruthy();
  });

  it('renders ErrorView when error occurs', () => {
    mockUseAllDeliverables.mockReturnValue({
      deliverables: [],
      isLoading: false,
      error: new Error('Network error'),
      approve: mockApprove,
      reject: mockReject,
      refetch: mockRefetch,
    });
    const { UNSAFE_getByType } = render(<InboxScreen />);
    const { ErrorView } = require('../src/components/ErrorView');
    expect(UNSAFE_getByType(ErrorView)).toBeTruthy();
  });

  it('renders EmptyState when deliverables is empty', () => {
    mockUseAllDeliverables.mockReturnValue({
      deliverables: [],
      isLoading: false,
      error: null,
      approve: mockApprove,
      reject: mockReject,
      refetch: mockRefetch,
    });
    const { UNSAFE_getByType } = render(<InboxScreen />);
    const { EmptyState } = require('../src/components/EmptyState');
    expect(UNSAFE_getByType(EmptyState)).toBeTruthy();
  });

  it('calls approve when Approve button is pressed', () => {
    const { getByTestId } = render(<InboxScreen />);
    fireEvent.press(getByTestId('approve-btn-d1'));
    expect(mockApprove).toHaveBeenCalledWith('ha1', 'd1');
  });

  it('renders VoiceFAB when voice is available', () => {
    const { getByTestId } = render(<InboxScreen />);
    expect(getByTestId('voice-fab')).toBeTruthy();
  });
});
