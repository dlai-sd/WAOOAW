/**
 * useHiredAgents Hook
 * React Query hooks for fetching and managing hired agents and trial status
 */

import { useQuery, UseQueryResult } from '@tanstack/react-query';
import { hiredAgentsService } from '../services/hiredAgents/hiredAgents.service';
import type {
  MyAgentInstanceSummary,
  HiredAgentInstance,
  TrialStatusRecord,
} from '../types/hiredAgents.types';

/**
 * Hook for fetching all hired agents for current customer
 * This is the primary hook for "My Agents" screen
 * 
 * Features:
 * - Automatic caching (2 minute stale time for fresh data)
 * - Automatic refetching on window focus
 * - Loading and error states
 * - Query invalidation support
 * 
 * @returns UseQueryResult with hired agents data
 * 
 * @example
 * ```tsx
 * const { data: hiredAgents, isLoading, error, refetch } = useHiredAgents();
 * ```
 */
export function useHiredAgents(): UseQueryResult<MyAgentInstanceSummary[], Error> {
  return useQuery({
    queryKey: ['hiredAgents'],
    queryFn: () => hiredAgentsService.listMyAgents(),
    staleTime: 1000 * 60 * 2, // 2 minutes (shorter than agents list for freshness)
    gcTime: 1000 * 60 * 15, // 15 minutes
    refetchOnWindowFocus: true,
    retry: 2,
  });
}

/**
 * Hook for fetching a specific hired agent by subscription ID
 * Returns full hired agent details including configuration
 * 
 * @param subscriptionId - Subscription ID (required)
 * @returns UseQueryResult with hired agent instance
 * 
 * @example
 * ```tsx
 * const { data: hiredAgent, isLoading } = useHiredAgent('SUB-123');
 * ```
 */
export function useHiredAgent(
  subscriptionId: string | undefined
): UseQueryResult<HiredAgentInstance, Error> {
  return useQuery({
    queryKey: ['hiredAgent', subscriptionId],
    queryFn: () => hiredAgentsService.getHiredAgentBySubscription(subscriptionId!),
    staleTime: 1000 * 60 * 2, // 2 minutes
    gcTime: 1000 * 60 * 10, // 10 minutes
    enabled: !!subscriptionId, // Only fetch if subscriptionId is provided
    retry: 2,
  });
}

/**
 * Hook for fetching all trial statuses for current customer
 * Lightweight view without full hired agent data
 * 
 * @returns UseQueryResult with trial status records
 * 
 * @example
 * ```tsx
 * const { data: trials, isLoading } = useTrialStatus();
 * ```
 */
export function useTrialStatus(): UseQueryResult<TrialStatusRecord[], Error> {
  return useQuery({
    queryKey: ['trialStatus'],
    queryFn: () => hiredAgentsService.listTrialStatus(),
    staleTime: 1000 * 60 * 1, // 1 minute (very fresh for trial status)
    gcTime: 1000 * 60 * 5, // 5 minutes
    refetchOnWindowFocus: true,
    retry: 2,
  });
}

/**
 * Hook for fetching trial status by subscription ID
 * 
 * @param subscriptionId - Subscription ID (required)
 * @returns UseQueryResult with trial status record
 * 
 * @example
 * ```tsx
 * const { data: trialStatus, isLoading } = useTrialStatusBySubscription('SUB-123');
 * ```
 */
export function useTrialStatusBySubscription(
  subscriptionId: string | undefined
): UseQueryResult<TrialStatusRecord, Error> {
  return useQuery({
    queryKey: ['trialStatus', subscriptionId],
    queryFn: () => hiredAgentsService.getTrialStatusBySubscription(subscriptionId!),
    staleTime: 1000 * 60 * 1, // 1 minute
    gcTime: 1000 * 60 * 5, // 5 minutes
    enabled: !!subscriptionId,
    retry: 2,
  });
}

/**
 * Hook for fetching only active hired agents
 * Filters to show agents with active subscription status
 * 
 * @returns UseQueryResult with active hired agents
 * 
 * @example
 * ```tsx
 * const { data: activeAgents, isLoading } = useActiveHiredAgents();
 * ```
 */
export function useActiveHiredAgents(): UseQueryResult<MyAgentInstanceSummary[], Error> {
  return useQuery({
    queryKey: ['hiredAgents', 'active'],
    queryFn: () => hiredAgentsService.listActiveHiredAgents(),
    staleTime: 1000 * 60 * 2, // 2 minutes
    gcTime: 1000 * 60 * 15, // 15 minutes
    refetchOnWindowFocus: true,
    retry: 2,
  });
}

/**
 * Hook for fetching agents currently in trial
 * Shows only agents with active trial status
 * 
 * @returns UseQueryResult with agents in trial
 * 
 * @example
 * ```tsx
 * const { data: trialAgents, isLoading } = useAgentsInTrial();
 * ```
 */
export function useAgentsInTrial(): UseQueryResult<MyAgentInstanceSummary[], Error> {
  return useQuery({
    queryKey: ['hiredAgents', 'trial'],
    queryFn: () => hiredAgentsService.listAgentsInTrial(),
    staleTime: 1000 * 60 * 1, // 1 minute (fresh for trial tracking)
    gcTime: 1000 * 60 * 10, // 10 minutes
    refetchOnWindowFocus: true,
    retry: 2,
  });
}

/**
 * Hook for fetching agents requiring setup
 * Shows agents where configured=false or goals_completed=false
 * Useful for onboarding flows
 * 
 * @returns UseQueryResult with agents needing setup
 * 
 * @example
 * ```tsx
 * const { data: needsSetup, isLoading } = useAgentsNeedingSetup();
 * ```
 */
export function useAgentsNeedingSetup(): UseQueryResult<MyAgentInstanceSummary[], Error> {
  return useQuery({
    queryKey: ['hiredAgents', 'needsSetup'],
    queryFn: () => hiredAgentsService.listAgentsNeedingSetup(),
    staleTime: 1000 * 60 * 2, // 2 minutes
    gcTime: 1000 * 60 * 10, // 10 minutes
    refetchOnWindowFocus: true,
    retry: 2,
  });
}
