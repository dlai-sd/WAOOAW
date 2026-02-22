/**
 * useAgentDetail Hook
 * React Query hook for fetching single agent details
 */

import { useQuery, UseQueryResult } from '@tanstack/react-query';
import { agentService } from '../services/agents/agent.service';
import type { Agent } from '../types/agent.types';

/**
 * Hook for fetching single agent detail by ID
 * 
 * Features:
 * - Automatic caching (10 minute stale time)
 * - Only fetches when agentId is provided
 * - Loading and error states
 * - Automatic refetching on window focus
 * 
 * @param agentId - Agent ID (UUID)
 * @returns UseQueryResult with agent data
 * 
 * @example
 * ```tsx
 * const { data: agent, isLoading, error } = useAgentDetail('agent-uuid');
 * ```
 */
export function useAgentDetail(
  agentId: string | undefined
): UseQueryResult<Agent, Error> {
  return useQuery({
    queryKey: ['agent', agentId],
    queryFn: () => {
      if (!agentId) {
        throw new Error('Agent ID is required');
      }
      return agentService.getAgent(agentId);
    },
    enabled: !!agentId, // Only run when agentId is truthy
    staleTime: 1000 * 60 * 10, // 10 minutes
    gcTime: 1000 * 60 * 30, // 30 minutes (formerly cacheTime)
    refetchOnWindowFocus: true,
    retry: 2,
  });
}

/**
 * Hook for fetching agent detail with manual control
 * Use this when you want to fetch on demand rather than automatically
 * 
 * @param agentId - Agent ID (UUID)
 * @returns UseQueryResult with agent data (initially disabled)
 * 
 * @example
 * ```tsx
 * const { data: agent, refetch } = useAgentDetailManual('agent-uuid');
 * // Later trigger fetch manually
 * await refetch();
 * ```
 */
export function useAgentDetailManual(
  agentId: string | undefined
): UseQueryResult<Agent, Error> {
  return useQuery({
    queryKey: ['agent', agentId],
    queryFn: () => {
      if (!agentId) {
        throw new Error('Agent ID is required');
      }
      return agentService.getAgent(agentId);
    },
    enabled: false, // Start disabled, user must call refetch()
    staleTime: 1000 * 60 * 10,
    gcTime: 1000 * 60 * 30,
    retry: 2,
  });
}
