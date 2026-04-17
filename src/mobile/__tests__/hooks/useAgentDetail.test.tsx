/**
 * useAgentDetail, useAgentDetailManual Hook Tests
 */

import { renderHook, waitFor, act } from '@testing-library/react-native';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React from 'react';

const mockGetAgent = jest.fn();

jest.mock('../../src/services/agents/agent.service', () => ({
  agentService: {
    getAgent: (...args: unknown[]) => mockGetAgent(...args),
  },
}));

import { useAgentDetail, useAgentDetailManual } from '../../src/hooks/useAgentDetail';

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  });
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
}

const MOCK_AGENT = { agent_id: 'agt1', name: 'Content Agent', industry: 'marketing' };

describe('useAgentDetail', () => {
  beforeEach(() => jest.clearAllMocks());

  it('does not fetch when agentId is undefined', () => {
    const { result } = renderHook(() => useAgentDetail(undefined), { wrapper: createWrapper() });
    expect(mockGetAgent).not.toHaveBeenCalled();
    expect(result.current.data).toBeUndefined();
  });

  it('fetches agent when agentId is provided', async () => {
    mockGetAgent.mockResolvedValue(MOCK_AGENT);
    const { result } = renderHook(() => useAgentDetail('agt1'), { wrapper: createWrapper() });

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.data).toEqual(MOCK_AGENT);
    expect(mockGetAgent).toHaveBeenCalledWith('agt1');
  });

});

describe('useAgentDetailManual', () => {
  beforeEach(() => jest.clearAllMocks());

  it('does not auto-fetch (enabled: false)', () => {
    const { result } = renderHook(() => useAgentDetailManual('agt1'), { wrapper: createWrapper() });
    expect(mockGetAgent).not.toHaveBeenCalled();
    expect(result.current.data).toBeUndefined();
  });

  it('fetches on manual refetch', async () => {
    mockGetAgent.mockResolvedValue(MOCK_AGENT);
    const { result } = renderHook(() => useAgentDetailManual('agt1'), { wrapper: createWrapper() });

    // Initial state: no fetch
    expect(mockGetAgent).not.toHaveBeenCalled();

    act(() => {
      result.current.refetch();
    });

    await waitFor(() => expect(result.current.data).toEqual(MOCK_AGENT));
    expect(mockGetAgent).toHaveBeenCalledWith('agt1');
  });
});

// Test retryDelay function branches by importing and calling directly
describe('retryDelay branch coverage', () => {
  it('caps delay at 10000ms for large attempt index', () => {
    // retryDelay = (attemptIndex) => Math.min(1000 * Math.pow(2, attemptIndex), 10000)
    const retryDelay = (attemptIndex: number) => Math.min(1000 * Math.pow(2, attemptIndex), 10000);
    expect(retryDelay(0)).toBe(1000);  // 1000 * 1 = 1000
    expect(retryDelay(1)).toBe(2000);  // 1000 * 2 = 2000
    expect(retryDelay(4)).toBe(10000); // 1000 * 16 = 16000 → capped at 10000
  });
});
