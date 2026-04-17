/**
 * useAgents, useSearchAgents Hook Tests
 */

import { renderHook, waitFor } from '@testing-library/react-native';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React from 'react';

const mockListAgents = jest.fn();
const mockSearchAgents = jest.fn();

jest.mock('../../src/services/agents/agent.service', () => ({
  agentService: {
    listAgents: (...args: unknown[]) => mockListAgents(...args),
    searchAgents: (...args: unknown[]) => mockSearchAgents(...args),
  },
}));

import { useAgents, useSearchAgents } from '../../src/hooks/useAgents';

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  });
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
}

const MOCK_AGENTS = [
  { agent_id: 'agt1', name: 'Content Agent', industry: 'marketing' },
  { agent_id: 'agt2', name: 'Sales Agent', industry: 'sales' },
];

describe('useAgents', () => {
  beforeEach(() => jest.clearAllMocks());

  it('fetches agents list', async () => {
    mockListAgents.mockResolvedValue(MOCK_AGENTS);
    const { result } = renderHook(() => useAgents(), { wrapper: createWrapper() });

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.data).toHaveLength(2);
    expect(mockListAgents).toHaveBeenCalledWith(undefined);
  });

  it('passes filter params to listAgents', async () => {
    mockListAgents.mockResolvedValue([MOCK_AGENTS[0]]);
    const { result } = renderHook(
      () => useAgents({ industry: 'marketing' }),
      { wrapper: createWrapper() }
    );

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(mockListAgents).toHaveBeenCalledWith({ industry: 'marketing' });
  });

});

describe('useSearchAgents', () => {
  beforeEach(() => jest.clearAllMocks());

  it('does not fetch when query is empty', () => {
    const { result } = renderHook(() => useSearchAgents(''), { wrapper: createWrapper() });
    expect(mockSearchAgents).not.toHaveBeenCalled();
    expect(result.current.data).toBeUndefined();
  });

  it('fetches when query is non-empty', async () => {
    mockSearchAgents.mockResolvedValue([MOCK_AGENTS[0]]);
    const { result } = renderHook(() => useSearchAgents('content'), { wrapper: createWrapper() });

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(mockSearchAgents).toHaveBeenCalledWith('content', undefined);
  });

  it('passes filter params with query', async () => {
    mockSearchAgents.mockResolvedValue([MOCK_AGENTS[0]]);
    const { result } = renderHook(
      () => useSearchAgents('marketing', { industry: 'marketing' }),
      { wrapper: createWrapper() }
    );

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(mockSearchAgents).toHaveBeenCalledWith('marketing', { industry: 'marketing' });
  });
});
