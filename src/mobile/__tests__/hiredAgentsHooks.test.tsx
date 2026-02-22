/**
 * Hired Agents Hooks Tests
 * Tests for React Query hooks for hired agents
 */

import React from 'react';
import { describe, it, expect, beforeEach, jest } from '@jest/globals';
import { renderHook, waitFor } from '@testing-library/react-native';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import {
  useHiredAgents,
  useHiredAgent,
  useTrialStatus,
  useTrialStatusBySubscription,
  useActiveHiredAgents,
  useAgentsInTrial,
  useAgentsNeedingSetup,
} from '../src/hooks/useHiredAgents';
import { hiredAgentsService } from '../src/services/hiredAgents/hiredAgents.service';
import type {
  MyAgentInstanceSummary,
  HiredAgentInstance,
  TrialStatusRecord,
} from '../src/types/hiredAgents.types';

// Mock hired agents service
jest.mock('../src/services/hiredAgents/hiredAgents.service');

// Helper to create QueryClient wrapper
const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false, // Disable retries for faster tests
        gcTime: 0, // Disable cache for cleaner tests
      },
    },
  });

  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
};

describe('useHiredAgents Hook', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should fetch hired agents successfully', async () => {
    const mockHiredAgents: MyAgentInstanceSummary[] = [
      {
        subscription_id: 'SUB-123',
        agent_id: 'AGT-MKT-001',
        duration: 'monthly',
        status: 'active',
        current_period_start: '2024-01-01T00:00:00Z',
        current_period_end: '2024-02-01T00:00:00Z',
        cancel_at_period_end: false,
        hired_instance_id: 'HIRE-123',
        nickname: 'Content Bot',
        trial_status: 'active',
      },
    ];

    (hiredAgentsService.listMyAgents as any).mockResolvedValue(mockHiredAgents);

    const { result } = renderHook(() => useHiredAgents(), {
      wrapper: createWrapper(),
    });

    // Initially loading
    expect(result.current.isLoading).toBe(true);
    expect(result.current.data).toBeUndefined();

    // Wait for query to resolve
    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    // Check final state
    expect(result.current.data).toEqual(mockHiredAgents);
    expect(result.current.isLoading).toBe(false);
    expect(hiredAgentsService.listMyAgents).toHaveBeenCalledTimes(1);
  });

  it('should handle error state', async () => {
    const mockError = new Error('Failed to fetch hired agents');

    (hiredAgentsService.listMyAgents as any).mockRejectedValue(mockError);

    const { result } = renderHook(() => useHiredAgents(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });

    expect(result.current.error).toEqual(mockError);
    expect(result.current.data).toBeUndefined();
  });

  it('should refetch hired agents on refetch call', async () => {
    const mockHiredAgents: MyAgentInstanceSummary[] = [];

    (hiredAgentsService.listMyAgents as any).mockResolvedValue(mockHiredAgents);

    const { result } = renderHook(() => useHiredAgents(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    // Refetch
    await result.current.refetch();

    expect(hiredAgentsService.listMyAgents).toHaveBeenCalledTimes(2);
  });
});

describe('useHiredAgent Hook', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should fetch hired agent by subscription ID', async () => {
    const mockHiredAgent: HiredAgentInstance = {
      hired_instance_id: 'HIRE-123',
      subscription_id: 'SUB-123',
      agent_id: 'AGT-MKT-001',
      agent_type_id: 'marketing.content.v1',
      nickname: 'Content Bot',
      configured: true,
      goals_completed: true,
      trial_status: 'active',
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    };

    (hiredAgentsService.getHiredAgentBySubscription as any).mockResolvedValue(
      mockHiredAgent
    );

    const { result } = renderHook(() => useHiredAgent('SUB-123'), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data).toEqual(mockHiredAgent);
    expect(hiredAgentsService.getHiredAgentBySubscription).toHaveBeenCalledWith('SUB-123');
  });

  it('should not fetch when subscriptionId is undefined', async () => {
    const { result } = renderHook(() => useHiredAgent(undefined), {
      wrapper: createWrapper(),
    });

    // Should remain idle (not loading, not fetching)
    expect(result.current.isLoading).toBe(false);
    expect(result.current.data).toBeUndefined();
    expect(hiredAgentsService.getHiredAgentBySubscription).not.toHaveBeenCalled();
  });

  it('should handle error state', async () => {
    const mockError = new Error('Hired agent not found');

    (hiredAgentsService.getHiredAgentBySubscription as any).mockRejectedValue(mockError);

    const { result } = renderHook(() => useHiredAgent('SUB-999'), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });

    expect(result.current.error).toEqual(mockError);
  });
});

describe('useTrialStatus Hook', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should fetch trial status list successfully', async () => {
    const mockTrialStatus: TrialStatusRecord[] = [
      {
        subscription_id: 'SUB-123',
        hired_instance_id: 'HIRE-123',
        trial_status: 'active',
        trial_start_at: '2024-01-01T00:00:00Z',
        trial_end_at: '2024-01-08T00:00:00Z',
        configured: true,
        goals_completed: true,
      },
    ];

    (hiredAgentsService.listTrialStatus as any).mockResolvedValue(mockTrialStatus);

    const { result } = renderHook(() => useTrialStatus(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data).toEqual(mockTrialStatus);
    expect(hiredAgentsService.listTrialStatus).toHaveBeenCalledTimes(1);
  });

  it('should handle error state', async () => {
    const mockError = new Error('Failed to fetch trial status');

    (hiredAgentsService.listTrialStatus as any).mockRejectedValue(mockError);

    const { result } = renderHook(() => useTrialStatus(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });

    expect(result.current.error).toEqual(mockError);
  });
});

describe('useTrialStatusBySubscription Hook', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should fetch trial status by subscription ID', async () => {
    const mockTrialStatus: TrialStatusRecord = {
      subscription_id: 'SUB-123',
      hired_instance_id: 'HIRE-123',
      trial_status: 'active',
      trial_start_at: '2024-01-01T00:00:00Z',
      trial_end_at: '2024-01-08T00:00:00Z',
      configured: true,
      goals_completed: true,
    };

    (hiredAgentsService.getTrialStatusBySubscription as any).mockResolvedValue(
      mockTrialStatus
    );

    const { result } = renderHook(() => useTrialStatusBySubscription('SUB-123'), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data).toEqual(mockTrialStatus);
    expect(hiredAgentsService.getTrialStatusBySubscription).toHaveBeenCalledWith('SUB-123');
  });

  it('should not fetch when subscriptionId is undefined', async () => {
    const { result } = renderHook(() => useTrialStatusBySubscription(undefined), {
      wrapper: createWrapper(),
    });

    expect(result.current.isLoading).toBe(false);
    expect(result.current.data).toBeUndefined();
    expect(hiredAgentsService.getTrialStatusBySubscription).not.toHaveBeenCalled();
  });
});

describe('useActiveHiredAgents Hook', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should fetch active hired agents successfully', async () => {
    const mockActiveAgents: MyAgentInstanceSummary[] = [
      {
        subscription_id: 'SUB-123',
        agent_id: 'AGT-MKT-001',
        duration: 'monthly',
        status: 'active',
        current_period_start: '2024-01-01T00:00:00Z',
        current_period_end: '2024-02-01T00:00:00Z',
        cancel_at_period_end: false,
      },
    ];

    (hiredAgentsService.listActiveHiredAgents as any).mockResolvedValue(mockActiveAgents);

    const { result } = renderHook(() => useActiveHiredAgents(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data).toEqual(mockActiveAgents);
    expect(hiredAgentsService.listActiveHiredAgents).toHaveBeenCalledTimes(1);
  });
});

describe('useAgentsInTrial Hook', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should fetch agents in trial successfully', async () => {
    const mockTrialAgents: MyAgentInstanceSummary[] = [
      {
        subscription_id: 'SUB-123',
        agent_id: 'AGT-MKT-001',
        duration: 'monthly',
        status: 'active',
        current_period_start: '2024-01-01T00:00:00Z',
        current_period_end: '2024-02-01T00:00:00Z',
        cancel_at_period_end: false,
        trial_status: 'active',
      },
    ];

    (hiredAgentsService.listAgentsInTrial as any).mockResolvedValue(mockTrialAgents);

    const { result } = renderHook(() => useAgentsInTrial(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data).toEqual(mockTrialAgents);
    expect(hiredAgentsService.listAgentsInTrial).toHaveBeenCalledTimes(1);
  });
});

describe('useAgentsNeedingSetup Hook', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should fetch agents needing setup successfully', async () => {
    const mockNeedsSetup: MyAgentInstanceSummary[] = [
      {
        subscription_id: 'SUB-123',
        agent_id: 'AGT-MKT-001',
        duration: 'monthly',
        status: 'active',
        current_period_start: '2024-01-01T00:00:00Z',
        current_period_end: '2024-02-01T00:00:00Z',
        cancel_at_period_end: false,
        configured: false,
        goals_completed: false,
      },
    ];

    (hiredAgentsService.listAgentsNeedingSetup as any).mockResolvedValue(mockNeedsSetup);

    const { result } = renderHook(() => useAgentsNeedingSetup(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data).toEqual(mockNeedsSetup);
    expect(hiredAgentsService.listAgentsNeedingSetup).toHaveBeenCalledTimes(1);
  });
});
