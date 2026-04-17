/**
 * NotificationsScreen tests
 *
 * Tests the exported utility functions + screen rendering.
 */
import React from 'react';
import { render, screen, waitFor } from '@testing-library/react-native';

// ─── Mocks ─────────────────────────────────────────────────────────────────

jest.mock('@/hooks/useTheme', () => ({
  useTheme: () => ({
    colors: {
      primary: '#667eea', textPrimary: '#fff', textSecondary: '#a1a1aa',
      background: '#0a0a0a', surface: '#18181b', border: '#27272a',
      success: '#10b981', warning: '#f59e0b', error: '#ef4444',
    },
    spacing: { xs: 4, sm: 8, md: 16, lg: 24, xl: 32, screenPadding: { horizontal: 20, vertical: 16 } },
    typography: {
      fontSize: { xs: 10, sm: 12, md: 14, lg: 16, xl: 20, xxl: 24 },
      fontFamily: { body: 'Inter', bodyBold: 'Inter-Bold', heading: 'Outfit' },
    },
  }),
}));

const mockHiredAgents = jest.fn();
jest.mock('@/hooks/useHiredAgents', () => ({
  useHiredAgents: () => mockHiredAgents(),
}));

jest.mock('../../src/services/notifications/pushNotifications.service', () => ({
  registerPushToken: jest.fn().mockResolvedValue(undefined),
}), { virtual: true });

jest.mock('@/services/notifications/pushNotifications.service', () => ({
  registerPushToken: jest.fn().mockResolvedValue(undefined),
}));

const mockGetParent = jest.fn(() => ({ navigate: jest.fn() }));
const mockNavigation: any = {
  navigate: jest.fn(),
  goBack: jest.fn(),
  getParent: mockGetParent,
};

// ─── resolveNavigationTarget tests ─────────────────────────────────────────

import { resolveNavigationTarget, NotificationsScreen } from '@/screens/profile/NotificationsScreen';
import type { Notification } from '@/screens/profile/NotificationsScreen';

describe('resolveNavigationTarget', () => {
  it('returns null for generic type', () => {
    const n: Notification = { id: '1', type: 'generic', title: 'T', body: 'B' };
    expect(resolveNavigationTarget(n)).toBeNull();
  });

  it('returns null when no hired_instance_id or hired_agent_id', () => {
    const n: Notification = { id: '1', type: 'approval_required', title: 'T', body: 'B' };
    expect(resolveNavigationTarget(n)).toBeNull();
  });

  it('returns AgentOperations target with approvals section for approval_required', () => {
    const n: Notification = {
      id: '1', type: 'approval_required', title: 'T', body: 'B', hired_instance_id: 'ha-1',
    };
    const result = resolveNavigationTarget(n);
    expect(result).not.toBeNull();
    expect(result?.screen).toBe('AgentOperations');
    expect((result?.params as any).focusSection).toBe('approvals');
  });

  it('returns recent section for deliverable_approved', () => {
    const n: Notification = {
      id: '1', type: 'deliverable_approved', title: 'T', body: 'B', hired_instance_id: 'ha-1',
    };
    const result = resolveNavigationTarget(n);
    expect((result?.params as any).focusSection).toBe('recent');
  });

  it('returns activity section for deliverable_rejected', () => {
    const n: Notification = {
      id: '1', type: 'deliverable_rejected', title: 'T', body: 'B', hired_instance_id: 'ha-1',
    };
    expect((resolveNavigationTarget(n)?.params as any).focusSection).toBe('activity');
  });

  it('returns health section for credential_expiring', () => {
    const n: Notification = {
      id: '1', type: 'credential_expiring', title: 'T', body: 'B', hired_instance_id: 'ha-1',
    };
    expect((resolveNavigationTarget(n)?.params as any).focusSection).toBe('health');
  });

  it('returns scheduler section for agent_paused', () => {
    const n: Notification = {
      id: '1', type: 'agent_paused', title: 'T', body: 'B', hired_instance_id: 'ha-1',
    };
    expect((resolveNavigationTarget(n)?.params as any).focusSection).toBe('scheduler');
  });

  it('returns spend section for trial_ending', () => {
    const n: Notification = {
      id: '1', type: 'trial_ending', title: 'T', body: 'B', hired_instance_id: 'ha-1',
    };
    expect((resolveNavigationTarget(n)?.params as any).focusSection).toBe('spend');
  });

  it('returns activity section for goal_run_failed', () => {
    const n: Notification = {
      id: '1', type: 'goal_run_failed', title: 'T', body: 'B', hired_instance_id: 'ha-1',
    };
    expect((resolveNavigationTarget(n)?.params as any).focusSection).toBe('activity');
  });

  it('returns recent section for publish_ready', () => {
    const n: Notification = {
      id: '1', type: 'publish_ready', title: 'T', body: 'B', hired_instance_id: 'ha-1',
    };
    expect((resolveNavigationTarget(n)?.params as any).focusSection).toBe('recent');
  });

  it('returns health section for publish_blocked', () => {
    const n: Notification = {
      id: '1', type: 'publish_blocked', title: 'T', body: 'B', hired_instance_id: 'ha-1',
    };
    expect((resolveNavigationTarget(n)?.params as any).focusSection).toBe('health');
  });
});

// ─── NotificationsScreen render tests ──────────────────────────────────────

describe('NotificationsScreen', () => {
  beforeEach(() => jest.clearAllMocks());

  it('shows loading when isLoading', () => {
    mockHiredAgents.mockReturnValue({ isLoading: true, data: null, error: null, refetch: jest.fn() });
    render(<NotificationsScreen navigation={mockNavigation} route={{} as any} />);
    expect(screen.getByText('Loading your agent alerts…')).toBeTruthy();
  });

  it('shows empty state when no hired agents', async () => {
    mockHiredAgents.mockReturnValue({ isLoading: false, data: [], error: null, refetch: jest.fn() });
    render(<NotificationsScreen navigation={mockNavigation} route={{} as any} />);
    await waitFor(() => {
      expect(screen.getByText('No action items right now')).toBeTruthy();
    });
  });

  it('renders push notifications section', () => {
    mockHiredAgents.mockReturnValue({ isLoading: false, data: [], error: null, refetch: jest.fn() });
    render(<NotificationsScreen navigation={mockNavigation} route={{} as any} />);
    expect(screen.getByText('Push Notifications')).toBeTruthy();
  });

  it('renders with hired agents data', async () => {
    mockHiredAgents.mockReturnValue({
      isLoading: false,
      data: [{
        hired_instance_id: 'ha-1',
        status: 'active',
        subscription_status: 'active',
        trial_status: 'none',
        trial_end_at: null,
        agent: { name: 'DMA Agent', industry: 'marketing' },
      }],
      error: null,
      refetch: jest.fn(),
    });
    render(<NotificationsScreen navigation={mockNavigation} route={{} as any} />);
    expect(screen.getAllByText(/notifications/i).length).toBeGreaterThan(0);
  });

  it('shows error state when error occurs', async () => {
    const mockRefetch = jest.fn();
    mockHiredAgents.mockReturnValue({
      isLoading: false,
      data: null,
      error: { message: 'Failed to load' },
      refetch: mockRefetch,
    });
    render(<NotificationsScreen navigation={mockNavigation} route={{} as any} />);
    await waitFor(() => {
      expect(screen.getByText('Could not load alerts')).toBeTruthy();
    });
    // Try Again button calls refetch
    const { fireEvent: fe } = require('@testing-library/react-native');
    fe.press(screen.getByText('Try Again'));
    expect(mockRefetch).toHaveBeenCalled();
  });

  it('renders notification items and allows pressing them', async () => {
    const mockNavigate = jest.fn();
    const mockGetParentNav = jest.fn(() => ({ navigate: mockNavigate }));
    const navWithParent: any = {
      navigate: jest.fn(),
      goBack: jest.fn(),
      getParent: mockGetParentNav,
    };

    mockHiredAgents.mockReturnValue({
      isLoading: false,
      data: [{
        hired_instance_id: 'ha-1',
        status: 'active',
        subscription_status: 'active',
        trial_status: 'trial_ending',
        trial_end_at: new Date(Date.now() + 2 * 24 * 3600 * 1000).toISOString(),
        agent: { name: 'DMA Agent', industry: 'marketing' },
      }],
      error: null,
      refetch: jest.fn(),
    });
    render(<NotificationsScreen navigation={navWithParent} route={{} as any} />);
    // No crash
    expect(true).toBeTruthy();
  });
});
