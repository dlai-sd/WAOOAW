/**
 * AgentOperations Voice Tests (MOB-PARITY-1 E5-S1)
 * Validates VoiceFAB presence and voice navigation on AgentOperationsScreen.
 */

import React from 'react';
import { render } from '@testing-library/react-native';

// ─── Mock theme ───────────────────────────────────────────────────────────────

const mockTheme = {
  colors: {
    black: '#0a0a0a', neonCyan: '#00f2fe', neonPurple: '#667eea',
    textPrimary: '#ffffff', textSecondary: '#a1a1aa', card: '#18181b',
    error: '#ef4444', success: '#10b981', warning: '#f59e0b',
    border: '#374151', background: '#0a0a0a',
  },
  spacing: {
    xs: 4, sm: 8, md: 16, lg: 24, xl: 32, xxl: 48,
    screenPadding: { horizontal: 16, vertical: 20 },
  },
  typography: {
    fontFamily: {
      display: 'SpaceGrotesk_700Bold',
      body: 'Inter_400Regular',
      bodyBold: 'Inter_600SemiBold',
    },
  },
};

jest.mock('@/hooks/useTheme', () => ({ useTheme: () => mockTheme }));

// ─── Mock hooks ───────────────────────────────────────────────────────────────

jest.mock('@/hooks/useHiredAgents', () => ({
  useHiredAgentById: jest.fn(() => ({
    data: { agent_id: 'AGT-MKT-DMA-001', agent_type_id: 'marketing.digital_marketing.v1', nickname: 'My Agent', hired_instance_id: 'ha1' },
    isLoading: false,
    error: null,
  })),
}));

jest.mock('@/hooks/useApprovalQueue', () => ({
  useApprovalQueue: jest.fn(() => ({
    deliverables: [],
    isLoading: false,
    error: null,
    approve: jest.fn(),
    reject: jest.fn(),
  })),
}));

const mockNavigate = jest.fn();
jest.mock('@react-navigation/native', () => ({
  useNavigation: () => ({ navigate: mockNavigate, goBack: jest.fn() }),
}));

const mockToggle = jest.fn();
jest.mock('@/hooks/useAgentVoiceOverlay', () => ({
  useAgentVoiceOverlay: jest.fn(() => ({
    isListening: false,
    toggle: mockToggle,
    lastCommand: null,
    isAvailable: true,
  })),
}));

const mockCpPost = jest.fn(() => Promise.resolve({ data: {} }));
const mockCpGet = jest.fn(() => Promise.resolve({ data: [] }));
const mockCpPatch = jest.fn(() => Promise.resolve({ data: {} }));

jest.mock('@/lib/cpApiClient', () => ({
  __esModule: true,
  default: {
    get: (...args: unknown[]) => mockCpGet(...args),
    patch: (...args: unknown[]) => mockCpPatch(...args),
    post: (...args: unknown[]) => mockCpPost(...args),
  },
}));

jest.mock('@/components/voice/VoiceFAB', () => {
  const React = require('react');
  const { View } = require('react-native');
  return {
    VoiceFAB: (props: any) => React.createElement(View, { testID: props.testID }),
  };
});

import { AgentOperationsScreen } from '@/screens/agents/AgentOperationsScreen';
import { useAgentVoiceOverlay } from '@/hooks/useAgentVoiceOverlay';

// ─── Tests ────────────────────────────────────────────────────────────────────

const mockNavigation = { navigate: mockNavigate, goBack: jest.fn() };
const mockRoute = { params: { hiredAgentId: 'ha1' } };

describe('AgentOperationsScreen voice navigation', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (useAgentVoiceOverlay as jest.Mock).mockReturnValue({
      isListening: false,
      toggle: mockToggle,
      lastCommand: null,
      isAvailable: true,
    });
    mockCpGet.mockResolvedValue({ data: [] });
  });

  it('renders VoiceFAB when speech recognition is available', () => {
    const { getByTestId } = render(
      <AgentOperationsScreen navigation={mockNavigation as any} route={mockRoute as any} />
    );
    expect(getByTestId('voice-fab-agent-ops')).toBeTruthy();
  });

  it('does not render VoiceFAB when speech recognition is unavailable', () => {
    (useAgentVoiceOverlay as jest.Mock).mockReturnValue({
      isListening: false,
      toggle: jest.fn(),
      lastCommand: null,
      isAvailable: false,
    });
    const { queryByTestId } = render(
      <AgentOperationsScreen navigation={mockNavigation as any} route={mockRoute as any} />
    );
    expect(queryByTestId('voice-fab-agent-ops')).toBeNull();
  });

  it('wires voice overlay with navigation commands', () => {
    render(
      <AgentOperationsScreen navigation={mockNavigation as any} route={mockRoute as any} />
    );
    // Verify overlay was initialized with navigation command keys
    const callArgs = (useAgentVoiceOverlay as jest.Mock).mock.calls[0][0];
    expect(callArgs).toHaveProperty('go to inbox');
    expect(callArgs).toHaveProperty('go to analytics');
    expect(callArgs).toHaveProperty('go to connections');
  });
});
