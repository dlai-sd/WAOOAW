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
import { render, fireEvent, waitFor } from '@testing-library/react-native';
import { AgentOperationsScreen } from '@/screens/agents/AgentOperationsScreen';

const mockCpGet = jest.fn();
const mockCpPatch = jest.fn();
const mockCpPost = jest.fn(() => Promise.resolve({ data: {} }));

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
    data: {
      agent_id: 'AGT-MKT-DMA-001',
      agent_type_id: 'marketing.digital_marketing.v1',
      nickname: 'My Agent',
      hired_instance_id: 'hi-1'
    },
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
  __esModule: true,
  default: {
    get: (...args: unknown[]) => mockCpGet(...args),
    patch: (...args: unknown[]) => mockCpPatch(...args),
    post: (...args: unknown[]) => mockCpPost(...args),
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
    mockCpGet.mockResolvedValue({
      data: [
        {
          skill_id: 'skill-theme-discovery',
          name: 'theme_discovery',
          display_name: 'Theme Discovery',
          goal_schema: {
            fields: [
              { key: 'business_background', label: 'Business Background', type: 'text', required: true },
              { key: 'industry', label: 'Industry', type: 'text', required: true },
              { key: 'locality', label: 'Locality', type: 'text', required: true },
              { key: 'target_audience', label: 'Target Audience', type: 'text', required: true },
              { key: 'persona', label: 'Persona', type: 'text', required: true },
              { key: 'offer', label: 'Offer', type: 'text', required: true },
              { key: 'objective', label: 'Objective', type: 'text', required: true },
              { key: 'channel_intent', label: 'YouTube Intent', type: 'text', required: true },
              { key: 'posting_cadence', label: 'Posting Cadence', type: 'text', required: true },
              { key: 'tone', label: 'Tone', type: 'text', required: true },
              { key: 'success_metrics', label: 'Success Metrics', type: 'text', required: true },
            ],
          },
          goal_config: {},
        },
      ],
    });
    mockCpPatch.mockResolvedValue({ data: { goal_config: {} } });
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
    (useApprovalQueue as jest.Mock).mockReturnValue({
      deliverables: [{ id: 'd-1', hired_agent_id: 'hi-1', type: 'content_draft' }],
      isLoading: false,
      error: null,
      approve: jest.fn(),
      reject: jest.fn(),
    });
    const { getByText } = render(
      <AgentOperationsScreen navigation={mockNavigation} route={mockRoute as any} />
    );
    expect(getByText('1 approvals')).toBeTruthy();
  });

  it('shows approval-gated DMA publish copy in the approvals section', async () => {
    const useApprovalQueue = require('@/hooks/useApprovalQueue').useApprovalQueue;
    (useApprovalQueue as jest.Mock).mockReturnValue({
      deliverables: [
        {
          id: 'd-yt-1',
          hired_agent_id: 'hi-1',
          type: 'content_draft',
          title: 'YouTube explainer draft',
          target_platform: 'YouTube',
          content_preview: 'Draft explainer awaiting exact customer approval before upload.',
          review_status: 'pending_review',
          approval_id: null,
          payload: {
            destination: {
              destination_type: 'youtube',
              metadata: {
                visibility: 'private',
                public_release_requested: false,
              },
            },
          },
        },
      ],
      isLoading: false,
      error: null,
      approve: jest.fn(),
      reject: jest.fn(),
    });

    const routeWithFocus = {
      ...mockRoute,
      params: { hiredAgentId: 'hi-1', focusSection: 'approvals' },
    };

    const { getByText } = render(
      <AgentOperationsScreen navigation={mockNavigation} route={routeWithFocus as any} />
    );

    await waitFor(() => {
      expect(getByText(/Approve exact deliverable/)).toBeTruthy();
    });

    expect(getByText('Exact approval required before YouTube action')).toBeTruthy();
    expect(getByText('YouTube')).toBeTruthy();
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

  it('resumes Theme Discovery in the goals section from saved brief progress', async () => {
    mockCpGet.mockResolvedValueOnce({
      data: [
        {
          skill_id: 'skill-theme-discovery',
          name: 'theme_discovery',
          display_name: 'Theme Discovery',
          goal_schema: {
            fields: [
              { key: 'business_background', label: 'Business Background', type: 'text', required: true },
              { key: 'industry', label: 'Industry', type: 'text', required: true },
              { key: 'locality', label: 'Locality', type: 'text', required: true },
              { key: 'target_audience', label: 'Target Audience', type: 'text', required: true },
              { key: 'persona', label: 'Persona', type: 'text', required: true },
              { key: 'offer', label: 'Offer', type: 'text', required: true },
              { key: 'objective', label: 'Objective', type: 'text', required: true },
              { key: 'channel_intent', label: 'YouTube Intent', type: 'text', required: true },
              { key: 'posting_cadence', label: 'Posting Cadence', type: 'text', required: true },
              { key: 'tone', label: 'Tone', type: 'text', required: true },
              { key: 'success_metrics', label: 'Success Metrics', type: 'text', required: true },
            ],
          },
          goal_config: {
            business_background: 'Dental clinic with two branches',
            industry: 'Healthcare',
            locality: 'Bengaluru',
          },
        },
      ],
    });

    const routeWithFocus = {
      ...mockRoute,
      params: { hiredAgentId: 'hi-1', focusSection: 'goals' },
    };

    const { getByText } = render(
      <AgentOperationsScreen navigation={mockNavigation} route={routeWithFocus as any} />
    );

    await waitFor(() => {
      expect(getByText('Define the audience and promise')).toBeTruthy();
      expect(getByText('Structured brief summary')).toBeTruthy();
      expect(getByText('Dental clinic with two branches')).toBeTruthy();
    });
  });

  it('saves the Theme Discovery brief from mobile', async () => {
    mockCpPatch.mockResolvedValueOnce({
      data: {
        goal_config: {
          business_background: 'Dental clinic with two branches',
          industry: 'Healthcare',
          locality: 'Bengaluru',
          target_audience: 'Working parents',
          persona: 'Care-seeking parent',
          offer: 'Free first consultation',
          objective: 'Drive qualified appointment requests',
          channel_intent: 'Educational shorts and explainers',
          posting_cadence: 'Three videos per week',
          tone: 'Clear and reassuring',
          success_metrics: 'Consult bookings and watch-through rate',
        },
      },
    });

    const routeWithFocus = {
      ...mockRoute,
      params: { hiredAgentId: 'hi-1', focusSection: 'goals' },
    };

    const { getByText, getByLabelText } = render(
      <AgentOperationsScreen navigation={mockNavigation} route={routeWithFocus as any} />
    );

    await waitFor(() => {
      expect(getByText('Map the business context')).toBeTruthy();
    });

    fireEvent.changeText(getByLabelText('Business Background *'), 'Dental clinic with two branches');
    fireEvent.changeText(getByLabelText('Industry *'), 'Healthcare');
    fireEvent.changeText(getByLabelText('Locality *'), 'Bengaluru');
    fireEvent.press(getByText('Continue'));

    await waitFor(() => expect(getByText('Define the audience and promise')).toBeTruthy());

    fireEvent.changeText(getByLabelText('Target Audience *'), 'Working parents');
    fireEvent.changeText(getByLabelText('Persona *'), 'Care-seeking parent');
    fireEvent.changeText(getByLabelText('Offer *'), 'Free first consultation');
    fireEvent.press(getByText('Continue'));

    await waitFor(() => expect(getByText('Shape the YouTube angle')).toBeTruthy());

    fireEvent.changeText(getByLabelText('Objective *'), 'Drive qualified appointment requests');
    fireEvent.changeText(getByLabelText('YouTube Intent *'), 'Educational shorts and explainers');
    fireEvent.changeText(getByLabelText('Posting Cadence *'), 'Three videos per week');
    fireEvent.press(getByText('Continue'));

    await waitFor(() => expect(getByText('Lock the voice and proof signal')).toBeTruthy());

    fireEvent.changeText(getByLabelText('Tone *'), 'Clear and reassuring');
    fireEvent.changeText(getByLabelText('Success Metrics *'), 'Consult bookings and watch-through rate');
    fireEvent.press(getByText('Save Theme Discovery brief'));

    await waitFor(() => {
      expect(mockCpPatch).toHaveBeenCalledWith(
        '/cp/hired-agents/hi-1/skills/skill-theme-discovery/goal-config',
        expect.objectContaining({
          goal_config: expect.objectContaining({
            objective: 'Drive qualified appointment requests',
            success_metrics: 'Consult bookings and watch-through rate',
          }),
        })
      );
    });

    await waitFor(() => {
      expect(getByText('Theme Discovery saved')).toBeTruthy();
    });
  });
});
