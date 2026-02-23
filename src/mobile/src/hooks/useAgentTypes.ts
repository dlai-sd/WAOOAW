/**
 * useAgentTypes Hook
 * React Query hook for fetching agent type definitions
 */

import { useQuery, UseQueryResult } from '@tanstack/react-query';
import { agentService } from '../services/agents/agent.service';
import type { AgentTypeDefinition } from '../types/agent.types';

/**
 * Hook for fetching agent type definitions (Phase-1 catalog)
 * 
 * Features:
 * - Long caching (60 minute stale time) - types rarely change
 * - Automatic refetching on mount
 * - Loading and error states
 * 
 * @returns UseQueryResult with agent types data
 * 
 * @example
 * ```tsx
 * const { data: agentTypes, isLoading, error } = useAgentTypes();
 * ```
 */
export function useAgentTypes(): UseQueryResult<AgentTypeDefinition[], Error> {
  return useQuery({
    queryKey: ['agentTypes'],
    queryFn: () => agentService.listAgentTypes(),
    staleTime: 1000 * 60 * 60, // 60 minutes (types rarely change)
    gcTime: 1000 * 60 * 120, // 120 minutes (formerly cacheTime)
    refetchOnWindowFocus: false, // Don't refetch on focus (static data)
    retry: 2,
  });
}
