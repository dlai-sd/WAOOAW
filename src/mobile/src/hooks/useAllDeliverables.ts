/**
 * useAllDeliverables Hook
 *
 * Aggregates deliverables from all hired agents for the current customer.
 * Fetches the hired agents list first, then fetches each agent's approval queue
 * in parallel using useQueries. Returns a merged, sorted array (newest first).
 */

import { useQueries, useMutation, useQueryClient } from '@tanstack/react-query';
import cpApiClient from '../lib/cpApiClient';
import { useHiredAgents } from './useHiredAgents';
import type { DeliverableItem } from './useApprovalQueue';

export type { DeliverableItem };

export interface DeliverableWithStatus extends DeliverableItem {
  status: 'pending' | 'approved' | 'rejected';
  hired_agent_id: string;
}

export interface UseAllDeliverablesResult {
  deliverables: DeliverableWithStatus[];
  isLoading: boolean;
  error: Error | null;
  approve: (hiredAgentId: string, deliverableId: string) => Promise<void>;
  reject: (hiredAgentId: string, deliverableId: string) => Promise<void>;
  refetch: () => void;
}

async function fetchApprovalQueue(hiredAgentId: string): Promise<DeliverableItem[]> {
  const response = await cpApiClient.get<DeliverableItem[]>(
    `/cp/hired-agents/${hiredAgentId}/approval-queue`
  );
  return response.data ?? [];
}

async function approveDeliverable(hiredAgentId: string, deliverableId: string): Promise<void> {
  await cpApiClient.post(
    `/cp/hired-agents/${hiredAgentId}/approval-queue/${deliverableId}/approve`
  );
}

async function rejectDeliverable(hiredAgentId: string, deliverableId: string): Promise<void> {
  await cpApiClient.post(
    `/cp/hired-agents/${hiredAgentId}/approval-queue/${deliverableId}/reject`
  );
}

function deriveStatus(item: DeliverableItem): 'pending' | 'approved' | 'rejected' {
  const raw = String((item as unknown as Record<string, unknown>).review_status ?? '').toLowerCase();
  if (raw === 'approved') return 'approved';
  if (raw === 'rejected') return 'rejected';
  return 'pending';
}

export function useAllDeliverables(): UseAllDeliverablesResult {
  const queryClient = useQueryClient();

  const { data: hiredAgents = [], isLoading: agentsLoading, error: agentsError } = useHiredAgents();

  const hiredAgentIds: string[] = hiredAgents
    .map((a) => String(a.hired_instance_id ?? a.subscription_id ?? ''))
    .filter(Boolean);

  const queueQueries = useQueries({
    queries: hiredAgentIds.map((hiredAgentId) => ({
      queryKey: ['approvalQueue', hiredAgentId],
      queryFn: () => fetchApprovalQueue(hiredAgentId),
      enabled: !!hiredAgentId,
      staleTime: 1000 * 60,
      retry: 2,
      retryDelay: (attemptIndex: number) => Math.min(1000 * Math.pow(2, attemptIndex), 10000),
    })),
  });

  const isQueuesLoading = queueQueries.some((q) => q.isLoading);
  const queuesError = queueQueries.find((q) => q.error)?.error ?? null;

  const deliverables: DeliverableWithStatus[] = queueQueries
    .flatMap((q, i) => {
      const hiredAgentId = hiredAgentIds[i] ?? '';
      return (q.data ?? []).map((item) => ({
        ...item,
        hired_agent_id: hiredAgentId,
        status: deriveStatus(item),
      }));
    })
    .sort((a, b) => {
      const aDate = a.created_at ? new Date(a.created_at).getTime() : 0;
      const bDate = b.created_at ? new Date(b.created_at).getTime() : 0;
      return bDate - aDate;
    });

  const approveMutation = useMutation({
    mutationFn: ({ hiredAgentId, deliverableId }: { hiredAgentId: string; deliverableId: string }) =>
      approveDeliverable(hiredAgentId, deliverableId),
    onSettled: (_data, _error, variables) => {
      queryClient.invalidateQueries({ queryKey: ['approvalQueue', variables.hiredAgentId] });
    },
  });

  const rejectMutation = useMutation({
    mutationFn: ({ hiredAgentId, deliverableId }: { hiredAgentId: string; deliverableId: string }) =>
      rejectDeliverable(hiredAgentId, deliverableId),
    onSettled: (_data, _error, variables) => {
      queryClient.invalidateQueries({ queryKey: ['approvalQueue', variables.hiredAgentId] });
    },
  });

  const refetch = () => {
    hiredAgentIds.forEach((id) => {
      queryClient.invalidateQueries({ queryKey: ['approvalQueue', id] });
    });
  };

  return {
    deliverables,
    isLoading: agentsLoading || isQueuesLoading,
    error: (agentsError ?? queuesError) as Error | null,
    approve: (hiredAgentId: string, deliverableId: string) =>
      approveMutation.mutateAsync({ hiredAgentId, deliverableId }),
    reject: (hiredAgentId: string, deliverableId: string) =>
      rejectMutation.mutateAsync({ hiredAgentId, deliverableId }),
    refetch,
  };
}
