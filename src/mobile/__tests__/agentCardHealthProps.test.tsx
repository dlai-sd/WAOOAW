/**
 * AgentCard — health / trial / approval props tests (CP-MOULD-1 E3-S1)
 *
 * Coverage:
 * - Renders without new props (backward-compat)
 * - Health dot renders green / yellow / red
 * - Cadence label displays alongside health dot
 * - Trial gauge fills proportionally
 * - Approval badge hidden when count is 0 or undefined
 * - Approval badge shows when count > 0
 */

import React from 'react';
import { describe, it, expect, jest, beforeEach } from '@jest/globals';
import { render } from '@testing-library/react-native';
import { AgentCard } from '@/components/AgentCard';
import type { Agent } from '@/types/agent.types';

jest.mock('@react-navigation/native', () => ({
  useNavigation: () => ({ navigate: jest.fn() }),
}));

jest.mock('@/hooks/useTheme', () => ({
  useTheme: () => ({
    colors: {
      card: '#18181b',
      textPrimary: '#ffffff',
      textSecondary: '#a1a1aa',
      neonCyan: '#00f2fe',
      black: '#0a0a0a',
    },
    spacing: {
      xs: 4,
      sm: 8,
      md: 16,
      lg: 24,
      xl: 32,
      screenPadding: 20,
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

const mockAgent: Agent = {
  id: 'agent-1',
  name: 'Marketing Expert',
  description: 'Content marketing specialist',
  specialization: 'Content Marketing',
  job_role_id: 'role-1',
  industry: 'marketing',
  entity_type: 'agent',
  status: 'active',
  created_at: '2024-01-01T00:00:00Z',
  rating: 4.5,
  price: 12000,
  trial_days: 7,
};

describe('AgentCard — health, trial gauge and approval badge (CP-MOULD-1 E3-S1)', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders without new props (backward compatible)', () => {
    const { getByText } = render(<AgentCard agent={mockAgent} />);
    expect(getByText('Marketing Expert')).toBeTruthy();
  });

  it('renders health dot label for "healthy" status', () => {
    const { getByText } = render(
      <AgentCard agent={mockAgent} healthStatus="healthy" />
    );
    expect(getByText('healthy')).toBeTruthy();
  });

  it('renders health dot label for "degraded" status', () => {
    const { getByText } = render(
      <AgentCard agent={mockAgent} healthStatus="degraded" />
    );
    expect(getByText('degraded')).toBeTruthy();
  });

  it('renders health dot label for "offline" status', () => {
    const { getByText } = render(
      <AgentCard agent={mockAgent} healthStatus="offline" />
    );
    expect(getByText('offline')).toBeTruthy();
  });

  it('renders cadence label alongside health dot', () => {
    const { getByText } = render(
      <AgentCard agent={mockAgent} healthStatus="healthy" cadenceLabel="Posts 3x daily" />
    );
    expect(getByText('Posts 3x daily')).toBeTruthy();
  });

  it('does not render health row when healthStatus is undefined', () => {
    const { queryByText } = render(<AgentCard agent={mockAgent} />);
    expect(queryByText('healthy')).toBeNull();
    expect(queryByText('degraded')).toBeNull();
    expect(queryByText('offline')).toBeNull();
  });

  it('renders trial gauge with used / limit counts', () => {
    const { getByText } = render(
      <AgentCard agent={mockAgent} trialTasksUsed={3} trialTaskLimit={10} />
    );
    expect(getByText('3/10 trial tasks used')).toBeTruthy();
  });

  it('renders trial gauge with 0 used when trialTasksUsed is undefined', () => {
    const { getByText } = render(
      <AgentCard agent={mockAgent} trialTaskLimit={10} />
    );
    expect(getByText('0/10 trial tasks used')).toBeTruthy();
  });

  it('does not render trial gauge when trialTaskLimit is undefined', () => {
    const { queryByText } = render(
      <AgentCard agent={mockAgent} trialTasksUsed={3} />
    );
    expect(queryByText(/trial tasks used/)).toBeNull();
  });

  it('does not render trial gauge when trialTaskLimit is 0', () => {
    const { queryByText } = render(
      <AgentCard agent={mockAgent} trialTasksUsed={3} trialTaskLimit={0} />
    );
    expect(queryByText(/trial tasks used/)).toBeNull();
  });

  it('does not render approval badge when approvalQueueCount is undefined', () => {
    const { queryByText } = render(<AgentCard agent={mockAgent} />);
    expect(queryByText(/pending/)).toBeNull();
  });

  it('does not render approval badge when approvalQueueCount is 0', () => {
    const { queryByText } = render(
      <AgentCard agent={mockAgent} approvalQueueCount={0} />
    );
    expect(queryByText(/pending/)).toBeNull();
  });

  it('renders approval badge with count when approvalQueueCount > 0', () => {
    const { getByText } = render(
      <AgentCard agent={mockAgent} approvalQueueCount={3} />
    );
    expect(getByText('3 pending')).toBeTruthy();
  });

  it('renders approval badge with count 1', () => {
    const { getByText } = render(
      <AgentCard agent={mockAgent} approvalQueueCount={1} />
    );
    expect(getByText('1 pending')).toBeTruthy();
  });
});
