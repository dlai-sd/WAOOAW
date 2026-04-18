/**
 * AgentOperationsScreen tests (MOB-PARITY-2 E4-S1 / E4-S3 / E4-S4)
 *
 * E4-S1 ACs:
 *   AC1 — pause button shown when agent status is "active"
 *   AC2 — resume button shown when agent status is "paused"
 *   AC3 — pause button has correct testID "ops-pause-btn"
 *   AC4 — resume button has correct testID "ops-resume-btn"
 *   AC5 — tapping pause calls POST /cp/hired-agents/:id/pause
 *   AC6 — tapping resume calls POST /cp/hired-agents/:id/resume
 *
 * E4-S3 ACs:
 *   AC7  — ops-weekly-output tile is present
 *   AC8  — tile shows correct non-zero weekly count
 *   AC9  — tile shows "0 this week" when no deliverables in current week
 *   AC10 — no crash when deliverables list is empty
 *
 * E4-S4 parity ACs:
 *   AC11 — screen renders with testID="mobile-agent-operations-screen"
 *   AC12 — all 8 section headers are rendered by id
 *   AC13 — agent name appears in header
 *   AC14 — scheduler section body renders ScheduledPostsSection
 *   AC15 — weekly-output tile and section count both visible in header
 */

import React from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react-native';
import { AgentOperationsScreen } from '../AgentOperationsScreen';

// ── mocks ─────────────────────────────────────────────────────────────────────

const mockCpApiClientPost = jest.fn().mockResolvedValue({ data: {} });
const mockApiClientPost = jest.fn().mockResolvedValue({ data: {} });
const mockApiClientGet = jest.fn().mockResolvedValue({ data: [] });

jest.mock('@/lib/cpApiClient', () => ({
  __esModule: true,
  default: {
    get: jest.fn().mockResolvedValue({ data: {} }),
    post: (...args: unknown[]) => mockCpApiClientPost(...args),
  },
}));

jest.mock('@/lib/apiClient', () => ({
  __esModule: true,
  default: {
    get: (...args: unknown[]) => mockApiClientGet(...args),
    post: (...args: unknown[]) => mockApiClientPost(...args),
    patch: jest.fn().mockResolvedValue({ data: {} }),
  },
}));

jest.mock('@/hooks/useHiredAgents', () => ({
  useHiredAgentById: jest.fn(),
  useDeliverables: jest.fn(),
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

jest.mock('@/hooks/useAgentVoiceOverlay', () => ({
  useAgentVoiceOverlay: jest.fn(() => ({
    isActive: false,
    activate: jest.fn(),
    deactivate: jest.fn(),
    registerCommand: jest.fn(),
  })),
}));

jest.mock('@/components/ContentDraftApprovalCard', () => ({
  ContentDraftApprovalCard: () => null,
}));

jest.mock('@/components/ScheduledPostsSection', () => ({
  ScheduledPostsSection: ({ hiredAgentId }: { hiredAgentId: string }) => {
    const { Text } = require('react-native');
    return <Text testID="scheduled-posts-section-mock">{hiredAgentId}</Text>;
  },
}));

jest.mock('@/components/voice/VoiceFAB', () => ({
  VoiceFAB: () => null,
}));

jest.mock('@/components/DigitalMarketingBriefStepCard', () => ({
  DigitalMarketingBriefStepCard: () => null,
}));

jest.mock('@/components/DigitalMarketingBriefSummaryCard', () => ({
  DigitalMarketingBriefSummaryCard: () => null,
}));

jest.mock('@/hooks/useTheme', () => ({
  useTheme: () => ({
    colors: {
      black: '#000000',
      textPrimary: '#ffffff',
      textSecondary: '#cccccc',
      neonCyan: '#00f2fe',
      card: '#1a1a1a',
      border: '#333333',
    },
    spacing: {
      xs: 4,
      sm: 8,
      md: 16,
      lg: 24,
      xl: 32,
      screenPadding: { horizontal: 16, vertical: 12 },
    },
    typography: {
      fontFamily: {
        display: 'SpaceGrotesk-Bold',
        body: 'Inter-Regular',
        bodyBold: 'Inter-Bold',
      },
    },
  }),
}));

// ── types + helpers ───────────────────────────────────────────────────────────

const { useHiredAgentById, useDeliverables } = jest.requireMock('@/hooks/useHiredAgents') as {
  useHiredAgentById: jest.Mock;
  useDeliverables: jest.Mock;
};

const mockNavigate = jest.fn();
const mockGoBack = jest.fn();

const navigation = {
  navigate: mockNavigate,
  goBack: mockGoBack,
  getParent: () => ({ navigate: jest.fn() }),
  addListener: jest.fn().mockReturnValue(() => {}),
} as any;

function makeRoute(status: 'active' | 'paused' | 'inactive' = 'active', focusSection?: string) {
  return {
    key: 'agent-ops',
    name: 'AgentOperations' as const,
    params: { hiredAgentId: 'HIRE-001', focusSection },
  } as any;
}

const NOW_ISO = new Date().toISOString();

function setupHooks({
  status = 'active' as 'active' | 'paused' | 'inactive',
  deliverables = [] as Array<{ created_at?: string }>,
} = {}) {
  useHiredAgentById.mockReturnValue({
    data: {
      hired_instance_id: 'HIRE-001',
      agent_id: 'AGT-001',
      agent_type_id: 'ops.v1',
      nickname: 'Test Ops Agent',
      subscription_status: status,
    },
    isLoading: false,
    error: null,
  });
  useDeliverables.mockReturnValue({ data: deliverables });
}

function renderScreen(status: 'active' | 'paused' | 'inactive' = 'active', focusSection?: string) {
  setupHooks({ status });
  return render(<AgentOperationsScreen navigation={navigation} route={makeRoute(status, focusSection)} />);
}

// ── tests ─────────────────────────────────────────────────────────────────────

describe('AgentOperationsScreen (E4-S1 / E4-S3 / E4-S4)', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  // ── E4-S4 parity ─────────────────────────────────────────────────────────

  it('AC11 — screen renders with mobile-agent-operations-screen testID', () => {
    renderScreen('active');
    expect(screen.getByTestId('mobile-agent-operations-screen')).toBeTruthy();
  });

  it('AC12 — all 8 section cards are present', () => {
    renderScreen('active');
    const sectionIds = ['activity', 'approvals', 'scheduler', 'health', 'goals', 'spend', 'recent', 'history'];
    for (const id of sectionIds) {
      expect(screen.getByTestId(`agent-ops-section-${id}`)).toBeTruthy();
    }
  });

  it('AC13 — agent name appears in header', () => {
    renderScreen('active');
    expect(screen.getByText('Test Ops Agent')).toBeTruthy();
  });

  // ── E4-S1 — conditional pause/resume ─────────────────────────────────────

  it('AC1/AC3 — pause button shown with correct testID when agent is active', async () => {
    renderScreen('active', 'scheduler');
    // scheduler section is pre-expanded via focusSection
    await waitFor(() => {
      expect(screen.getByTestId('ops-pause-btn')).toBeTruthy();
    });
    expect(screen.queryByTestId('ops-resume-btn')).toBeNull();
  });

  it('AC2/AC4 — resume button shown with correct testID when agent is paused', async () => {
    setupHooks({ status: 'paused' });
    render(<AgentOperationsScreen navigation={navigation} route={makeRoute('paused', 'scheduler')} />);
    await waitFor(() => {
      expect(screen.getByTestId('ops-resume-btn')).toBeTruthy();
    });
    expect(screen.queryByTestId('ops-pause-btn')).toBeNull();
  });

  it('AC5 — tapping pause calls POST /api/v1/hired-agents/:id/pause', async () => {
    renderScreen('active', 'scheduler');
    await waitFor(() => screen.getByTestId('ops-pause-btn'));
    fireEvent.press(screen.getByTestId('ops-pause-btn'));
    await waitFor(() => {
      expect(mockApiClientPost).toHaveBeenCalledWith('/api/v1/hired-agents/HIRE-001/pause');
    });
  });

  it('AC6 — tapping resume calls POST /api/v1/hired-agents/:id/resume', async () => {
    setupHooks({ status: 'paused' });
    render(<AgentOperationsScreen navigation={navigation} route={makeRoute('paused', 'scheduler')} />);
    await waitFor(() => screen.getByTestId('ops-resume-btn'));
    fireEvent.press(screen.getByTestId('ops-resume-btn'));
    await waitFor(() => {
      expect(mockApiClientPost).toHaveBeenCalledWith('/api/v1/hired-agents/HIRE-001/resume');
    });
  });

  // ── E4-S2 — ScheduledPostsSection is rendered ────────────────────────────

  it('AC14 — scheduler section body renders ScheduledPostsSection', async () => {
    renderScreen('active', 'scheduler');
    await waitFor(() => {
      expect(screen.getByTestId('scheduled-posts-section-mock')).toBeTruthy();
    });
  });

  // ── E4-S3 — weekly output tile ────────────────────────────────────────────

  it('AC7 — ops-weekly-output tile is present', () => {
    renderScreen('active');
    expect(screen.getByTestId('ops-weekly-output')).toBeTruthy();
  });

  it('AC9/AC10 — weekly-output tile shows 0 when no deliverables', () => {
    setupHooks({ status: 'active', deliverables: [] });
    render(<AgentOperationsScreen navigation={navigation} route={makeRoute('active')} />);
    const tile = screen.getByTestId('ops-weekly-output');
    expect(tile).toBeTruthy();
    // "0 deliverables this week" — find the number 0 within the tile
    expect(screen.getByText('0')).toBeTruthy();
  });

  it('AC8 — weekly-output tile shows count for deliverables created this week', () => {
    setupHooks({
      status: 'active',
      deliverables: [
        { created_at: NOW_ISO },
        { created_at: NOW_ISO },
      ],
    });
    render(<AgentOperationsScreen navigation={navigation} route={makeRoute('active')} />);
    expect(screen.getByTestId('ops-weekly-output')).toBeTruthy();
    expect(screen.getByText('2')).toBeTruthy();
  });

  it('AC15 — weekly-output tile and approval count pill both visible in header', () => {
    renderScreen('active');
    expect(screen.getByTestId('ops-weekly-output')).toBeTruthy();
    expect(screen.getByText(/0 approvals/i)).toBeTruthy();
  });
});
