/**
 * useHiredAgents Hook Tests
 */

import { renderHook, waitFor } from '@testing-library/react-native';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React from 'react';

const mockListMyAgents = jest.fn();
const mockGetHiredAgentBySubscription = jest.fn();
const mockGetHiredAgentById = jest.fn();
const mockListTrialStatus = jest.fn();
const mockGetTrialStatusBySubscription = jest.fn();
const mockGetDeliverables = jest.fn();
const mockListActiveHiredAgents = jest.fn();
const mockListAgentsInTrial = jest.fn();
const mockListAgentsNeedingSetup = jest.fn();

jest.mock('../../src/services/hiredAgents/hiredAgents.service', () => ({
  hiredAgentsService: {
    listMyAgents: (...args: unknown[]) => mockListMyAgents(...args),
    getHiredAgentBySubscription: (...args: unknown[]) => mockGetHiredAgentBySubscription(...args),
    getHiredAgentById: (...args: unknown[]) => mockGetHiredAgentById(...args),
    listTrialStatus: () => mockListTrialStatus(),
    getTrialStatusBySubscription: (...args: unknown[]) => mockGetTrialStatusBySubscription(...args),
    getDeliverablesByHiredAgent: (...args: unknown[]) => mockGetDeliverables(...args),
    listActiveHiredAgents: () => mockListActiveHiredAgents(),
    listAgentsInTrial: () => mockListAgentsInTrial(),
    listAgentsNeedingSetup: () => mockListAgentsNeedingSetup(),
  },
}));

jest.mock('../../src/store/authStore', () => ({
  useCurrentUser: jest.fn(() => ({ customer_id: 'cust-001' })),
}));

import {
  useHiredAgents,
  useHiredAgent,
  useHiredAgentById,
  useTrialStatus,
  useTrialStatusBySubscription,
  useDeliverables,
  useActiveHiredAgents,
  useAgentsInTrial,
  useAgentsNeedingSetup,
} from '../../src/hooks/useHiredAgents';

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  });
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
}

const MOCK_AGENT_SUMMARY = [
  { hired_instance_id: 'hi1', agent_id: 'agt1', nickname: 'My Agent' },
];

describe('useHiredAgents', () => {
  beforeEach(() => jest.clearAllMocks());

  it('fetches hired agents for current user', async () => {
    mockListMyAgents.mockResolvedValue(MOCK_AGENT_SUMMARY);
    const { result } = renderHook(() => useHiredAgents(), { wrapper: createWrapper() });

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.data).toHaveLength(1);
    expect(mockListMyAgents).toHaveBeenCalledWith('cust-001');
  });

});

describe('useHiredAgent', () => {
  beforeEach(() => jest.clearAllMocks());

  it('does not fetch when subscriptionId is undefined', () => {
    const { result } = renderHook(() => useHiredAgent(undefined), { wrapper: createWrapper() });
    expect(mockGetHiredAgentBySubscription).not.toHaveBeenCalled();
  });

  it('fetches hired agent by subscription id', async () => {
    mockGetHiredAgentBySubscription.mockResolvedValue({ hired_instance_id: 'hi1' });
    const { result } = renderHook(() => useHiredAgent('sub-1'), { wrapper: createWrapper() });

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(mockGetHiredAgentBySubscription).toHaveBeenCalledWith('sub-1');
  });
});

describe('useHiredAgentById', () => {
  beforeEach(() => jest.clearAllMocks());

  it('does not fetch when hiredAgentId is undefined', () => {
    renderHook(() => useHiredAgentById(undefined), { wrapper: createWrapper() });
    expect(mockGetHiredAgentById).not.toHaveBeenCalled();
  });

  it('fetches hired agent by id', async () => {
    mockGetHiredAgentById.mockResolvedValue({ hired_instance_id: 'hi1' });
    const { result } = renderHook(() => useHiredAgentById('hi1'), { wrapper: createWrapper() });

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(mockGetHiredAgentById).toHaveBeenCalledWith('hi1');
  });
});

describe('useTrialStatus', () => {
  beforeEach(() => jest.clearAllMocks());

  it('fetches trial statuses', async () => {
    mockListTrialStatus.mockResolvedValue([{ subscription_id: 'sub1', status: 'trial' }]);
    const { result } = renderHook(() => useTrialStatus(), { wrapper: createWrapper() });

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.data).toHaveLength(1);
  });
});

describe('useTrialStatusBySubscription', () => {
  beforeEach(() => jest.clearAllMocks());

  it('does not fetch when subscriptionId is undefined', () => {
    renderHook(() => useTrialStatusBySubscription(undefined), { wrapper: createWrapper() });
    expect(mockGetTrialStatusBySubscription).not.toHaveBeenCalled();
  });

  it('fetches trial status by subscription id', async () => {
    mockGetTrialStatusBySubscription.mockResolvedValue({ subscription_id: 'sub1', status: 'trial' });
    const { result } = renderHook(() => useTrialStatusBySubscription('sub1'), { wrapper: createWrapper() });

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(mockGetTrialStatusBySubscription).toHaveBeenCalledWith('sub1');
  });
});

describe('useDeliverables', () => {
  beforeEach(() => jest.clearAllMocks());

  it('does not fetch when hiredAgentId is undefined', () => {
    renderHook(() => useDeliverables(undefined), { wrapper: createWrapper() });
    expect(mockGetDeliverables).not.toHaveBeenCalled();
  });

  it('fetches deliverables by hired agent id', async () => {
    mockGetDeliverables.mockResolvedValue([{ id: 'd1' }]);
    const { result } = renderHook(() => useDeliverables('hi1'), { wrapper: createWrapper() });

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.data).toHaveLength(1);
  });
});

describe('useActiveHiredAgents', () => {
  beforeEach(() => jest.clearAllMocks());

  it('fetches active hired agents', async () => {
    mockListActiveHiredAgents.mockResolvedValue(MOCK_AGENT_SUMMARY);
    const { result } = renderHook(() => useActiveHiredAgents(), { wrapper: createWrapper() });

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.data).toHaveLength(1);
  });
});

describe('useAgentsInTrial', () => {
  beforeEach(() => jest.clearAllMocks());

  it('fetches agents in trial', async () => {
    mockListAgentsInTrial.mockResolvedValue(MOCK_AGENT_SUMMARY);
    const { result } = renderHook(() => useAgentsInTrial(), { wrapper: createWrapper() });

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.data).toHaveLength(1);
  });
});

describe('useAgentsNeedingSetup', () => {
  beforeEach(() => jest.clearAllMocks());

  it('fetches agents needing setup', async () => {
    mockListAgentsNeedingSetup.mockResolvedValue(MOCK_AGENT_SUMMARY);
    const { result } = renderHook(() => useAgentsNeedingSetup(), { wrapper: createWrapper() });

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.data).toHaveLength(1);
  });
});

// retryDelay branches — trigger actual retries to hit retryDelay lambdas in source
describe('retryDelay lambda coverage', () => {
  function createRetryWrapper() {
    const qc = new QueryClient({
      defaultOptions: {
        queries: { retry: 1, gcTime: 0, retryDelay: 0 },
      },
    });
    return ({ children }: { children: React.ReactNode }) => (
      <QueryClientProvider client={qc}>{children}</QueryClientProvider>
    );
  }

  it('useHiredAgents retryDelay is invoked on failure', async () => {
    mockListMyAgents.mockRejectedValue(new Error('network error'));
    const wrapper = createRetryWrapper();
    const { result } = renderHook(() => useHiredAgents(), { wrapper });
    await waitFor(() => expect(result.current.isError).toBe(true), { timeout: 5000 });
  });

  it('useHiredAgent retryDelay is invoked on failure', async () => {
    mockGetHiredAgentBySubscription.mockRejectedValue(new Error('fail'));
    const wrapper = createRetryWrapper();
    const { result } = renderHook(() => useHiredAgent('sub-fail'), { wrapper });
    await waitFor(() => expect(result.current.isError).toBe(true), { timeout: 5000 });
  });

  it('useHiredAgentById retryDelay is invoked on failure', async () => {
    mockGetHiredAgentById.mockRejectedValue(new Error('fail'));
    const wrapper = createRetryWrapper();
    const { result } = renderHook(() => useHiredAgentById('id-fail'), { wrapper });
    await waitFor(() => expect(result.current.isError).toBe(true), { timeout: 5000 });
  });

  it('useDeliverables retryDelay is invoked on failure', async () => {
    mockGetDeliverables.mockRejectedValue(new Error('fail'));
    const wrapper = createRetryWrapper();
    const { result } = renderHook(() => useDeliverables('id-fail'), { wrapper });
    await waitFor(() => expect(result.current.isError).toBe(true), { timeout: 5000 });
  });
});
