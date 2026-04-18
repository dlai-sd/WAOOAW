/**
 * useApprovalQueue Hook Tests
 */

import { renderHook, waitFor, act } from '@testing-library/react-native';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React from 'react';

const mockApiGet = jest.fn();
const mockApiPost = jest.fn(() => Promise.resolve({ data: {} }));

jest.mock('../../src/lib/apiClient', () => ({
  __esModule: true,
  default: {
    get: (...args: unknown[]) => mockApiGet(...args),
    post: (...args: unknown[]) => mockApiPost(...args),
  },
}));

import { useApprovalQueue } from '../../src/hooks/useApprovalQueue';

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 }, mutations: { retry: false } },
  });
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
}

const MOCK_DELIVERABLES = [
  { id: 'd1', hired_agent_id: 'ha1', type: 'content_draft', title: 'Draft A', created_at: '2026-01-01' },
  { id: 'd2', hired_agent_id: 'ha1', type: 'trade_plan', title: 'Trade B', created_at: '2026-01-02' },
];

describe('useApprovalQueue', () => {
  beforeEach(() => jest.clearAllMocks());

  it('returns empty deliverables when hiredAgentId is undefined', async () => {
    const { result } = renderHook(() => useApprovalQueue(undefined), { wrapper: createWrapper() });
    expect(result.current.deliverables).toEqual([]);
    expect(result.current.isLoading).toBe(false);
  });

  it('fetches deliverables for a given hiredAgentId', async () => {
    mockApiGet.mockResolvedValue({ data: MOCK_DELIVERABLES });
    const { result } = renderHook(() => useApprovalQueue('ha1'), { wrapper: createWrapper() });

    await waitFor(() => expect(result.current.isLoading).toBe(false));

    expect(result.current.deliverables).toHaveLength(2);
    expect(mockApiGet).toHaveBeenCalledWith(
      '/api/v1/hired-agents/ha1/deliverables?status=pending_review'
    );
  });

  it('approve mutation calls correct endpoint', async () => {
    mockApiGet.mockResolvedValue({ data: MOCK_DELIVERABLES });
    mockApiPost.mockResolvedValue({ data: {} });

    const { result } = renderHook(() => useApprovalQueue('ha1'), { wrapper: createWrapper() });
    await waitFor(() => expect(result.current.isLoading).toBe(false));

    await act(async () => {
      await result.current.approve('d1');
    });

    expect(mockApiPost).toHaveBeenCalledWith(
      '/api/v1/deliverables/d1/review',
      { decision: 'approved' }
    );
  });

  it('reject mutation calls correct endpoint', async () => {
    mockApiGet.mockResolvedValue({ data: MOCK_DELIVERABLES });
    mockApiPost.mockResolvedValue({ data: {} });

    const { result } = renderHook(() => useApprovalQueue('ha1'), { wrapper: createWrapper() });
    await waitFor(() => expect(result.current.isLoading).toBe(false));

    await act(async () => {
      await result.current.reject('d1');
    });

    expect(mockApiPost).toHaveBeenCalledWith(
      '/api/v1/deliverables/d1/review',
      { decision: 'rejected' }
    );
  });

  it('rejectWithReason mutation calls correct endpoint with reason', async () => {
    mockApiGet.mockResolvedValue({ data: MOCK_DELIVERABLES });
    mockApiPost.mockResolvedValue({ data: {} });

    const { result } = renderHook(() => useApprovalQueue('ha1'), { wrapper: createWrapper() });
    await waitFor(() => expect(result.current.isLoading).toBe(false));

    await act(async () => {
      await result.current.rejectWithReason('d1', 'Off-brand content');
    });

    expect(mockApiPost).toHaveBeenCalledWith(
      '/api/v1/deliverables/d1/review',
      { decision: 'rejected', reason: 'Off-brand content' }
    );
  });
});
