/**
 * Agent Hooks Tests
 * Tests for React Query hooks (useAgents, useAgentDetail, useAgentTypes)
 */

import { describe, it, expect, beforeEach, jest } from '@jest/globals';
import { renderHook, waitFor } from '@testing-library/react-native';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useAgents, useSearchAgents } from '../../src/hooks/useAgents';
import { useAgentDetail, useAgentDetailManual } from '../../src/hooks/useAgentDetail';
import { useAgentTypes } from '../../src/hooks/useAgentTypes';
import { agentService } from '../../src/services/agents/agent.service';
import type { Agent, AgentTypeDefinition } from '../../src/types/agent.types';

// Mock agent service
jest.mock('../../src/services/agents/agent.service');

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

describe('useAgents Hook', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should fetch agents successfully', async () => {
    const mockAgents: Agent[] = [
      {
        id: 'agent-1',
        name: 'Marketing Agent',
        description: 'Content marketing specialist',
        job_role_id: 'role-1',
        industry: 'marketing',
        entity_type: 'agent',
        status: 'active',
        created_at: '2024-01-01T00:00:00Z',
        rating: 4.5,
        price: 12000,
      },
      {
        id: 'agent-2',
        name: 'Sales Agent',
        description: 'B2B sales specialist',
        job_role_id: 'role-2',
        industry: 'sales',
        entity_type: 'agent',
        status: 'active',
        created_at: '2024-01-01T00:00:00Z',
        rating: 4.8,
        price: 15000,
      },
    ];

    (agentService.listAgents as jest.Mock).mockResolvedValue(mockAgents);

    const { result } = renderHook(() => useAgents(), {
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
    expect(result.current.data).toEqual(mockAgents);
    expect(result.current.isLoading).toBe(false);
    expect(agentService.listAgents).toHaveBeenCalledWith(undefined);
  });

  it('should fetch agents with filters', async () => {
    const mockAgents: Agent[] = [];

    (agentService.listAgents as jest.Mock).mockResolvedValue(mockAgents);

    const { result } = renderHook(
      () => useAgents({ industry: 'marketing', status: 'active' }),
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(agentService.listAgents).toHaveBeenCalledWith({
      industry: 'marketing',
      status: 'active',
    });
  });

  it('should handle error state', async () => {
    const mockError = new Error('Failed to fetch agents');

    (agentService.listAgents as jest.Mock).mockRejectedValue(mockError);

    const { result } = renderHook(() => useAgents(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });

    expect(result.current.error).toEqual(mockError);
    expect(result.current.data).toBeUndefined();
  });

  it('should refetch agents on refetch call', async () => {
    const mockAgents: Agent[] = [];

    (agentService.listAgents as jest.Mock).mockResolvedValue(mockAgents);

    const { result } = renderHook(() => useAgents(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    // Refetch
    await result.current.refetch();

    expect(agentService.listAgents).toHaveBeenCalledTimes(2);
  });
});

describe('useSearchAgents Hook', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should search agents with query', async () => {
    const mockAgents: Agent[] = [
      {
        id: 'agent-1',
        name: 'Content Marketing Agent',
        description: 'SEO and content',
        job_role_id: 'role-1',
        industry: 'marketing',
        entity_type: 'agent',
        status: 'active',
        created_at: '2024-01-01T00:00:00Z',
      },
    ];

    (agentService.searchAgents as jest.Mock).mockResolvedValue(mockAgents);

    const { result } = renderHook(() => useSearchAgents('marketing'), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data).toEqual(mockAgents);
    expect(agentService.searchAgents).toHaveBeenCalledWith('marketing', undefined);
  });

  it('should not fetch when query is empty', async () => {
    (agentService.searchAgents as jest.Mock).mockResolvedValue([]);

    const { result } = renderHook(() => useSearchAgents('  '), {
      wrapper: createWrapper(),
    });

    // Should not trigger fetch due to enabled: false
    expect(result.current.data).toBeUndefined();
    expect(agentService.searchAgents).not.toHaveBeenCalled();
  });

  it('should search with query and filters', async () => {
    const mockAgents: Agent[] = [];

    (agentService.searchAgents as jest.Mock).mockResolvedValue(mockAgents);

    const { result } = renderHook(
      () => useSearchAgents('content', { industry: 'marketing' }),
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(agentService.searchAgents).toHaveBeenCalledWith('content', {
      industry: 'marketing',
    });
  });
});

describe('useAgentDetail Hook', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should fetch agent detail by ID', async () => {
    const mockAgent: Agent = {
      id: 'agent-123',
      name: 'Test Agent',
      description: 'Test description',
      job_role_id: 'role-1',
      industry: 'education',
      entity_type: 'agent',
      status: 'active',
      created_at: '2024-01-01T00:00:00Z',
      rating: 4.7,
      price: 14000,
      specialization: 'Math tutoring',
    };

    (agentService.getAgent as jest.Mock).mockResolvedValue(mockAgent);

    const { result } = renderHook(() => useAgentDetail('agent-123'), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data).toEqual(mockAgent);
    expect(agentService.getAgent).toHaveBeenCalledWith('agent-123');
  });

  it('should not fetch when agentId is undefined', async () => {
    (agentService.getAgent as jest.Mock).mockResolvedValue({});

    const { result } = renderHook(() => useAgentDetail(undefined), {
      wrapper: createWrapper(),
    });

    // Should not trigger fetch due to enabled: false
    expect(result.current.data).toBeUndefined();
    expect(agentService.getAgent).not.toHaveBeenCalled();
  });

  it('should handle error state', async () => {
    const mockError = new Error('Agent not found');

    (agentService.getAgent as jest.Mock).mockRejectedValue(mockError);

    const { result } = renderHook(() => useAgentDetail('agent-invalid'), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });

    expect(result.current.error).toEqual(mockError);
  });
});

describe('useAgentDetailManual Hook', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should not fetch automatically', async () => {
    (agentService.getAgent as jest.Mock).mockResolvedValue({});

    const { result } = renderHook(() => useAgentDetailManual('agent-123'), {
      wrapper: createWrapper(),
    });

    // Should not auto-fetch
    expect(result.current.data).toBeUndefined();
    expect(agentService.getAgent).not.toHaveBeenCalled();
  });

  it('should fetch on manual refetch', async () => {
    const mockAgent: Agent = {
      id: 'agent-manual',
      name: 'Manual Agent',
      description: 'Manual fetch test',
      job_role_id: 'role-1',
      industry: 'sales',
      entity_type: 'agent',
      status: 'active',
      created_at: '2024-01-01T00:00:00Z',
    };

    (agentService.getAgent as jest.Mock).mockResolvedValue(mockAgent);

    const { result } = renderHook(() => useAgentDetailManual('agent-manual'), {
      wrapper: createWrapper(),
    });

    // Trigger manual refetch
    await result.current.refetch();

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data).toEqual(mockAgent);
    expect(agentService.getAgent).toHaveBeenCalledWith('agent-manual');
  });
});

describe('useAgentTypes Hook', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should fetch agent types', async () => {
    const mockAgentTypes: AgentTypeDefinition[] = [
      {
        agent_type_id: 'type-1',
        display_name: 'Marketing Agent',
        version: '1.0.0',
      },
      {
        agent_type_id: 'type-2',
        display_name: 'Education Agent',
        version: '1.0.0',
      },
    ];

    (agentService.listAgentTypes as jest.Mock).mockResolvedValue(mockAgentTypes);

    const { result } = renderHook(() => useAgentTypes(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data).toEqual(mockAgentTypes);
    expect(agentService.listAgentTypes).toHaveBeenCalled();
  });

  it('should handle error state', async () => {
    const mockError = new Error('Failed to fetch agent types');

    (agentService.listAgentTypes as jest.Mock).mockRejectedValue(mockError);

    const { result } = renderHook(() => useAgentTypes(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });

    expect(result.current.error).toEqual(mockError);
  });

  it('should cache agent types (long stale time)', async () => {
    const mockAgentTypes: AgentTypeDefinition[] = [
      {
        agent_type_id: 'type-1',
        display_name: 'Agent Type 1',
        version: '1.0.0',
      },
    ];

    (agentService.listAgentTypes as jest.Mock).mockResolvedValue(mockAgentTypes);

    const { result, rerender } = renderHook(() => useAgentTypes(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    // Rerender should not trigger new fetch (cached)
    rerender();

    // Should still only have been called once (from initial render)
    expect(agentService.listAgentTypes).toHaveBeenCalledTimes(1);
  });
});
