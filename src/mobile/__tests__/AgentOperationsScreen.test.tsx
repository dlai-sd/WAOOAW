/**
 * AgentOperationsScreen Tests (CP-MOULD-1 E5-S1)
 *
 * Coverage:
 * - All 8 section cards render (collapsed by default)
 * - Toggle expands / collapses a section
 * - Pause and Resume buttons are present in scheduler section
 * - Approval badge shows count when there are pending approvals
 * - focusSection auto-expands the target section
 */

import React from 'react';
import { describe, it, expect, jest, beforeEach } from '@jest/globals';
import { render, fireEvent } from '@testing-library/react-native';
import { AgentOperationsScreen } from '@/screens/agents/AgentOperationsScreen';

// ─── Mocks ────────────────────────────────────────────────────────────────────

jest.mock('@/hooks/useTheme', () => ({
  useTheme: () => ({
    colors: {
      black: '#0a0a0a',
      neonCyan: '#00f2fe',
      textPrimary: '#ffffff',
      textSecondary: '#a1a1aa',
      card: '#18181b',
      border: '#374151',
      success: '#10b981',
      warning: '#f59e0b',
      error: '#ef4444',
    },
    spacing: {
      xs: 4, sm: 8, md: 16, lg: 24, xl: 32,
      screenPadding: { horizontal: 16, vertical: 20 },
    },
    typography: {
      fontFamily: {
        display: 'SpaceGrotesk_700Bold',
        body: 'Inter_400Regular',
        bodyBold: 'Inter_600SemiBold',
      },
    },
  }),
}));

jest.mock('@/hooks/useHiredAgents', () => ({
  useHiredAgentById: jest.fn(() => ({
    data: { agent_id: 'agent-1', nickname: 'My Agent', hired_instance_id: 'hi-1' },
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

jest.mock('@/lib/cpApiClient', () => ({
  default: {
    post: jest.fn(() => Promise.resolve({ data: {} })),
  },
}));

const mockNavigate = jest.fn();
const mockGoBack = jest.fn();
const mockRoute = {
  params: { hiredAgentId: 'hi-1' },
  key: 'AgentOperations-1',
  name: 'AgentOperations',
};
const mockNavigation = {
  navigate: mockNavigate,
  goBack: mockGoBack,
} as any;

// ─── Tests ────────────────────────────────────────────────────────────────────

describe('AgentOperationsScreen', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders agent name and operations hub heading', () => {
    const { getByText } = render(
      <AgentOperationsScreen navigation={mockNavigation} route={mockRoute as any} />
    );
    expect(getByText('My Agent')).toBeTruthy();
    expect(getByText('Agent Operations Hub')).toBeTruthy();
  });

  it('renders all 8 section cards', () => {
    const { getByText } = render(
      <AgentOperationsScreen navigation={mockNavigation} route={mockRoute as any} />
    );
    expect(getByText("Today's Activity")).toBeTruthy();
    expect(getByText('Pending Approvals')).toBeTruthy();
    expect(getByText('Schedule Controls')).toBeTruthy();
    expect(getByText('Connection Health')).toBeTruthy();
    expect(getByText('Goal Configuration')).toBeTruthy();
    expect(getByText('Trial Usage & Spend')).toBeTruthy();
    expect(getByText('Recent Publications')).toBeTruthy();
    expect(getByText('Performance History')).toBeTruthy();
  });

  it('expands a section on tap and shows its content', () => {
    const { getByText, queryByText } = render(
      <AgentOperationsScreen navigation={mockNavigation} route={mockRoute as any} />
    );
    // Scheduler section content not visible before tap
    expect(queryByText('⏸ Pause')).toBeNull();
    // Tap the scheduler section header
    fireEvent.press(getByText('Schedule Controls'));
    // Now Pause/Resume buttons are visible
    expect(getByText('⏸ Pause')).toBeTruthy();
    expect(getByText('▶ Resume')).toBeTruthy();
  });

  it('collapses a section when tapped again', () => {
    const { getByText, queryByText } = render(
      <AgentOperationsScreen navigation={mockNavigation} route={mockRoute as any} />
    );
    fireEvent.press(getByText('Schedule Controls'));
    expect(getByText('⏸ Pause')).toBeTruthy();
    fireEvent.press(getByText('Schedule Controls'));
    expect(queryByText('⏸ Pause')).toBeNull();
  });

  it('shows approval badge when there are pending approvals', () => {
    const useApprovalQueue = require('@/hooks/useApprovalQueue').useApprovalQueue;
    (useApprovalQueue as jest.Mock).mockReturnValueOnce({
      deliverables: [{ id: 'd-1', hired_agent_id: 'hi-1', type: 'content_draft' }],
      isLoading: false,
      error: null,
      approve: jest.fn(),
      reject: jest.fn(),
    });
    const { getByText } = render(
      <AgentOperationsScreen navigation={mockNavigation} route={mockRoute as any} />
    );
    expect(getByText('1')).toBeTruthy();
  });

  it('auto-expands the focusSection when provided', () => {
    const routeWithFocus = {
      ...mockRoute,
      params: { hiredAgentId: 'hi-1', focusSection: 'scheduler' },
    };
    const { getByText } = render(
      <AgentOperationsScreen navigation={mockNavigation} route={routeWithFocus as any} />
    );
    // Scheduler section is auto-expanded
    expect(getByText('⏸ Pause')).toBeTruthy();
  });

  it('navigates back on ← Back tap', () => {
    const { getByText } = render(
      <AgentOperationsScreen navigation={mockNavigation} route={mockRoute as any} />
    );
    fireEvent.press(getByText('← Back'));
    expect(mockGoBack).toHaveBeenCalled();
  });
});
