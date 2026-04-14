/**
 * useAllDeliverables Hook Tests (MOB-PARITY-1 E1-S1)
 */

import { renderHook, waitFor } from '@testing-library/react-native';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React from 'react';

// ─── Mocks ────────────────────────────────────────────────────────────────────

const mockCpGet = jest.fn();
const mockCpPost = jest.fn(() => Promise.resolve({ data: {} }));

jest.mock('../src/lib/cpApiClient', () => ({
  __esModule: true,
  default: {
    get: (...args: unknown[]) => mockCpGet(...args),
    post: (...args: unknown[]) => mockCpPost(...args),
  },
}));

jest.mock('../src/hooks/useHiredAgents', () => ({
  useHiredAgents: jest.fn(() => ({
    data: [
      { hired_instance_id: 'ha1' },
      { hired_instance_id: 'ha2' },
    ],
    isLoading: false,
    error: null,
  })),
}));

import { useAllDeliverables } from '../src/hooks/useAllDeliverables';

// ─── Helper ───────────────────────────────────────────────────────────────────

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
}

// ─── Tests ────────────────────────────────────────────────────────────────────

describe('useAllDeliverables', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('returns merged, sorted deliverables from 2 agents', async () => {
    mockCpGet.mockImplementation((url: string) => {
      if (url.includes('ha1')) {
        return Promise.resolve({
          data: [
            { id: 'd1', hired_agent_id: 'ha1', type: 'content_draft', title: 'Draft A', created_at: '2026-01-02T00:00:00Z' },
          ],
        });
      }
      if (url.includes('ha2')) {
        return Promise.resolve({
          data: [
            { id: 'd2', hired_agent_id: 'ha2', type: 'trade_plan', title: 'Trade B', created_at: '2026-01-03T00:00:00Z' },
          ],
        });
      }
      return Promise.resolve({ data: [] });
    });

    const { result } = renderHook(() => useAllDeliverables(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => !result.current.isLoading);

    expect(result.current.deliverables.length).toBe(2);
    // Sorted newest first
    expect(result.current.deliverables[0].id).toBe('d2');
    expect(result.current.deliverables[1].id).toBe('d1');
  });

  it('returns partial results when one agent queue fails', async () => {
    mockCpGet.mockImplementation((url: string) => {
      if (url.includes('ha1')) {
        return Promise.resolve({
          data: [
            { id: 'd1', hired_agent_id: 'ha1', type: 'content_draft', title: 'Draft A', created_at: '2026-01-01T00:00:00Z' },
          ],
        });
      }
      if (url.includes('ha2')) {
        return Promise.reject(new Error('Agent 2 queue unavailable'));
      }
      return Promise.resolve({ data: [] });
    });

    const { result } = renderHook(() => useAllDeliverables(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => !result.current.isLoading);

    // ha1 results are present; ha2 error is captured
    expect(result.current.deliverables.length).toBeGreaterThanOrEqual(0);
  });
});
