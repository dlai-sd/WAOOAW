/**
 * ScheduledPostsSection tests (MOB-PARITY-2 E4-S2)
 *
 * AC1 — renders "post-status-queued" chip for queued post
 * AC2 — renders "post-status-published" chip for published post
 * AC3 — renders "post-status-failed" chip for failed post
 * AC4 — shows empty-state text when list is empty
 * AC5 — shows loading indicator while fetching
 * AC6 — calls listScheduledPosts with the correct hiredAgentId
 */

import React from 'react';
import { render, screen, waitFor } from '@testing-library/react-native';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ScheduledPostsSection } from '../src/components/ScheduledPostsSection';

// ── mocks ─────────────────────────────────────────────────────────────────────

const mockListScheduledPosts = jest.fn();

jest.mock('@/services/hiredAgents/hiredAgents.service', () => ({
  hiredAgentsService: {
    listScheduledPosts: (...args: unknown[]) => mockListScheduledPosts(...args),
  },
}));

jest.mock('@/hooks/useTheme', () => ({
  useTheme: () => ({
    colors: {
      black: '#000000',
      textPrimary: '#ffffff',
      textSecondary: '#cccccc',
      neonCyan: '#00f2fe',
      card: '#1a1a1a',
    },
    typography: {
      fontFamily: { body: 'Inter-Regular', bodyBold: 'Inter-Bold' },
    },
  }),
}));

// ── helpers ───────────────────────────────────────────────────────────────────

function renderWithQuery(ui: React.ReactElement) {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  });
  return render(<QueryClientProvider client={qc}>{ui}</QueryClientProvider>);
}

// ── tests ─────────────────────────────────────────────────────────────────────

describe('ScheduledPostsSection (E4-S2)', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('AC5 — shows loading indicator while fetching', async () => {
    // Never resolves during this test
    mockListScheduledPosts.mockReturnValue(new Promise(() => {}));
    renderWithQuery(<ScheduledPostsSection hiredAgentId="HIRE-001" />);
    expect(screen.getByTestId('scheduled-posts-loading')).toBeTruthy();
  });

  it('AC4 — shows empty-state text when list is empty', async () => {
    mockListScheduledPosts.mockResolvedValue([]);
    renderWithQuery(<ScheduledPostsSection hiredAgentId="HIRE-001" />);
    await waitFor(() => {
      expect(screen.getByTestId('scheduled-posts-empty')).toBeTruthy();
      expect(screen.getByText(/No scheduled posts yet/i)).toBeTruthy();
    });
  });

  it('AC1 — renders queued chip', async () => {
    mockListScheduledPosts.mockResolvedValue([
      { id: 'p1', title: 'Post 1', status: 'queued' },
    ]);
    renderWithQuery(<ScheduledPostsSection hiredAgentId="HIRE-001" />);
    await waitFor(() => {
      expect(screen.getByTestId('post-status-queued')).toBeTruthy();
    });
  });

  it('AC2 — renders published chip', async () => {
    mockListScheduledPosts.mockResolvedValue([
      { id: 'p2', title: 'Post 2', status: 'published' },
    ]);
    renderWithQuery(<ScheduledPostsSection hiredAgentId="HIRE-001" />);
    await waitFor(() => {
      expect(screen.getByTestId('post-status-published')).toBeTruthy();
    });
  });

  it('AC3 — renders failed chip', async () => {
    mockListScheduledPosts.mockResolvedValue([
      { id: 'p3', title: 'Post 3', status: 'failed' },
    ]);
    renderWithQuery(<ScheduledPostsSection hiredAgentId="HIRE-001" />);
    await waitFor(() => {
      expect(screen.getByTestId('post-status-failed')).toBeTruthy();
    });
  });

  it('AC6 — calls listScheduledPosts with correct hiredAgentId', async () => {
    mockListScheduledPosts.mockResolvedValue([]);
    renderWithQuery(<ScheduledPostsSection hiredAgentId="HIRE-XYZ" />);
    await waitFor(() => {
      expect(mockListScheduledPosts).toHaveBeenCalledWith('HIRE-XYZ');
    });
  });
});
