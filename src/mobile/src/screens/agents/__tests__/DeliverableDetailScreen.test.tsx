/**
 * DeliverableDetailScreen tests (MOB-PARITY-2 E7-S1)
 *
 * AC1 — testID="deliverable-detail-screen" present
 * AC2 — Full content text visible (not truncated)
 * AC3 — testID="detail-platform", "detail-type", "detail-created-at" present
 * AC4 — testID="detail-approve-btn" calls approve mutation (POST .../approve)
 * AC5 — testID="detail-reject-btn" shows reject-with-reason flow
 * AC6 — (navigation) Tapping deliverable row in Inbox navigates to DeliverableDetail
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react-native';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { DeliverableDetailScreen } from '@/screens/agents/DeliverableDetailScreen';

// ── mocks ─────────────────────────────────────────────────────────────────────

const mockCpGet = jest.fn();
const mockCpPost = jest.fn();

jest.mock('@/lib/cpApiClient', () => ({
  __esModule: true,
  default: {
    get: (...args: unknown[]) => mockCpGet(...args),
    post: (...args: unknown[]) => mockCpPost(...args),
  },
}));

jest.mock('@/hooks/useTheme', () => ({
  useTheme: () => ({
    colors: {
      black: '#0a0a0a',
      textPrimary: '#ffffff',
      textSecondary: '#a1a1aa',
      neonCyan: '#00f2fe',
      card: '#18181b',
      error: '#ef4444',
    },
    typography: {
      fontFamily: { body: 'Inter_400Regular', bodyBold: 'Inter_600SemiBold', display: 'SpaceGrotesk_700Bold' },
    },
    spacing: { xs: 4, sm: 8, md: 16, lg: 24 },
  }),
}));

jest.mock('@/components/LoadingSpinner', () => ({
  LoadingSpinner: ({ testID }: { testID?: string }) => {
    const { View } = require('react-native');
    return <View testID={testID ?? 'loading-spinner'} />;
  },
}));

jest.mock('@/components/ErrorView', () => ({
  ErrorView: ({ testID, onRetry }: { testID?: string; onRetry?: () => void }) => {
    const { View, TouchableOpacity, Text } = require('react-native');
    return (
      <View testID={testID ?? 'error-view'}>
        <TouchableOpacity testID="error-retry" onPress={onRetry}><Text>Retry</Text></TouchableOpacity>
      </View>
    );
  },
}));

// ── helpers ───────────────────────────────────────────────────────────────────

const mockNavigate = jest.fn();
const mockGoBack = jest.fn();
const mockNavigation = { navigate: mockNavigate, goBack: mockGoBack } as any;
const mockRoute = {
  params: { deliverableId: 'DEL-001', hiredAgentId: 'HIRE-001' },
  key: 'DeliverableDetail-1',
  name: 'DeliverableDetail',
} as any;

const MOCK_DELIVERABLE = {
  id: 'DEL-001',
  hired_agent_id: 'HIRE-001',
  type: 'content_draft',
  title: 'Instagram Reel Script',
  content_preview: 'This is the FULL content of the deliverable. It goes into great detail about the topic and should not be truncated in any way.',
  target_platform: 'Instagram',
  created_at: '2025-03-01T10:00:00Z',
  status: 'pending',
};

function renderWithQuery(overrides: { navigation?: any; route?: any } = {}) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false, gcTime: 0 } } });
  return render(
    <QueryClientProvider client={qc}>
      <DeliverableDetailScreen
        navigation={overrides.navigation ?? mockNavigation}
        route={overrides.route ?? mockRoute}
      />
    </QueryClientProvider>
  );
}

// ── tests ─────────────────────────────────────────────────────────────────────

describe('DeliverableDetailScreen (E7-S1)', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockCpGet.mockResolvedValue({ data: MOCK_DELIVERABLE });
    mockCpPost.mockResolvedValue({ data: {} });
  });

  it('AC1 — renders testID="deliverable-detail-screen"', async () => {
    renderWithQuery();
    await waitFor(() => {
      expect(screen.getByTestId('deliverable-detail-screen')).toBeTruthy();
    });
  });

  it('AC2 — shows full content text without truncation', async () => {
    renderWithQuery();
    await waitFor(() => {
      expect(screen.getByText(MOCK_DELIVERABLE.content_preview)).toBeTruthy();
    });
  });

  it('AC3 — shows detail-platform, detail-type, detail-created-at elements', async () => {
    renderWithQuery();
    await waitFor(() => {
      expect(screen.getByTestId('detail-platform')).toBeTruthy();
      expect(screen.getByTestId('detail-type')).toBeTruthy();
      expect(screen.getByTestId('detail-created-at')).toBeTruthy();
    });
  });

  it('AC4 — tapping detail-approve-btn calls POST .../approve', async () => {
    renderWithQuery();
    await waitFor(() => expect(screen.getByTestId('detail-approve-btn')).toBeTruthy());
    fireEvent.press(screen.getByTestId('detail-approve-btn'));
    await waitFor(() => {
      expect(mockCpPost).toHaveBeenCalledWith(
        expect.stringContaining('/approve')
      );
    });
  });

  it('AC5 — tapping detail-reject-btn shows reject-reason-input', async () => {
    renderWithQuery();
    await waitFor(() => expect(screen.getByTestId('detail-reject-btn')).toBeTruthy());
    expect(screen.queryByTestId('reject-reason-input')).toBeNull();
    fireEvent.press(screen.getByTestId('detail-reject-btn'));
    expect(screen.getByTestId('reject-reason-input')).toBeTruthy();
  });

  it('AC5b — Confirm rejection calls POST .../reject with {reason}', async () => {
    renderWithQuery();
    await waitFor(() => expect(screen.getByTestId('detail-reject-btn')).toBeTruthy());
    fireEvent.press(screen.getByTestId('detail-reject-btn'));
    fireEvent.changeText(screen.getByTestId('reject-reason-input'), 'Wrong platform');
    fireEvent.press(screen.getByTestId('reject-reason-confirm'));
    await waitFor(() => {
      expect(mockCpPost).toHaveBeenCalledWith(
        expect.stringContaining('/reject'),
        { reason: 'Wrong platform' }
      );
    });
  });

  it('shows loading state while fetching', () => {
    mockCpGet.mockReturnValue(new Promise(() => {}));
    renderWithQuery();
    expect(screen.getByTestId('detail-loading')).toBeTruthy();
  });

  it('shows error state on fetch failure', async () => {
    mockCpGet.mockRejectedValue(new Error('Network error'));
    renderWithQuery();
    await waitFor(() => {
      expect(screen.getByTestId('detail-error')).toBeTruthy();
    });
  });
});
