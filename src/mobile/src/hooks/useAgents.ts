/**
 * useAgents Hook
 * React Query hook for fetching and managing agent list
 */

import { useQuery, UseQueryResult } from '@tanstack/react-query';
import { agentService } from '../services/agents/agent.service';
import type { Agent, AgentListParams } from '../types/agent.types';

/**
 * Hook for fetching list of agents with optional filters
 * 
 * Features:
 * - Automatic caching (5 minute stale time)
 * - Automatic refetching on window focus
 * - Loading and error states
 * - Query invalidation support
 * 
 * @param params - Optional filter parameters (industry, job_role_id, status, q, limit, offset)
 * @returns UseQueryResult with agents data
 * 
 * @example
 * ```tsx
 * const { data: agents, isLoading, error, refetch } = useAgents({ industry: 'marketing' });
 * ```
 */
export function useAgents(
  params?: AgentListParams
): UseQueryResult<Agent[], Error> {
  return useQuery({
    queryKey: ['agents', params],
    queryFn: () => agentService.listAgents(params),
    staleTime: 1000 * 60 * 5, // 5 minutes
    gcTime: 1000 * 60 * 30, // 30 minutes (formerly cacheTime)
    refetchOnWindowFocus: true,
    retry: 2, // Retry failed requests twice
  });
}

/**
 * Hook for searching agents with a query string
 * 
 * @param query - Search query string
 * @param params - Optional filter parameters
 * @returns UseQueryResult with search results
 * 
 * @example
 * ```tsx
 * const { data: results, isLoading } = useSearchAgents('marketing', { industry: 'marketing' });
 * ```
 */
export function useSearchAgents(
  query: string,
  params?: AgentListParams
): UseQueryResult<Agent[], Error> {
  return useQuery({
    queryKey: ['agents', 'search', query, params],
    queryFn: () => agentService.searchAgents(query, params),
    staleTime: 1000 * 60 * 2, // 2 minutes (shorter for search results)
    gcTime: 1000 * 60 * 10, // 10 minutes
    enabled: query.trim().length > 0, // Only run if query is not empty
    retry: 1,
  });
}
