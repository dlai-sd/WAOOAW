/**
 * useApprovalQueue Hook
 *
 * Fetches pending deliverables for a hired agent that need customer approval.
 * Calls GET /cp/hired-agents/{id}/approval-queue
 * Provides approve(deliverableId) and reject(deliverableId) mutations.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import cpApiClient from '../lib/cpApiClient';

export interface DeliverableItem {
  id: string;
  hired_agent_id: string;
  type: 'trade_plan' | 'content_draft' | string;
  title?: string;
  description?: string;
  content_preview?: string;
  // Trade plan specific
  symbol?: string;
  action?: 'BUY' | 'SELL' | string;
  price?: number;
  quantity?: number;
  risk_rating?: 'low' | 'medium' | 'high';
  // Content draft specific
  target_platform?: string;
  created_at?: string;
}

interface ApprovalQueueResult {
  deliverables: DeliverableItem[];
  isLoading: boolean;
  error: Error | null;
  approve: (deliverableId: string) => Promise<void>;
  reject: (deliverableId: string) => Promise<void>;
}

async function fetchApprovalQueue(hiredAgentId: string): Promise<DeliverableItem[]> {
  const response = await cpApiClient.get<DeliverableItem[]>(
    `/cp/hired-agents/${hiredAgentId}/approval-queue`
  );
  return response.data;
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

export function useApprovalQueue(hiredAgentId: string | undefined): ApprovalQueueResult {
  const queryClient = useQueryClient();
  const queryKey = ['approvalQueue', hiredAgentId];

  const { data = [], isLoading, error } = useQuery({
    queryKey,
    queryFn: () => fetchApprovalQueue(hiredAgentId!),
    enabled: !!hiredAgentId,
    staleTime: 1000 * 60, // 1 minute
    retry: 2,
    retryDelay: (attemptIndex) => Math.min(1000 * Math.pow(2, attemptIndex), 10000),
  });

  const approveMutation = useMutation({
    mutationFn: (deliverableId: string) =>
      approveDeliverable(hiredAgentId!, deliverableId),
    onMutate: async (deliverableId) => {
      await queryClient.cancelQueries({ queryKey });
      const previous = queryClient.getQueryData<DeliverableItem[]>(queryKey);
      queryClient.setQueryData<DeliverableItem[]>(queryKey, (old = []) =>
        old.filter((d) => d.id !== deliverableId)
      );
      return { previous };
    },
    onError: (_err, _id, context) => {
      if (context?.previous) {
        queryClient.setQueryData(queryKey, context.previous);
      }
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey });
    },
  });

  const rejectMutation = useMutation({
    mutationFn: (deliverableId: string) =>
      rejectDeliverable(hiredAgentId!, deliverableId),
    onMutate: async (deliverableId) => {
      await queryClient.cancelQueries({ queryKey });
      const previous = queryClient.getQueryData<DeliverableItem[]>(queryKey);
      queryClient.setQueryData<DeliverableItem[]>(queryKey, (old = []) =>
        old.filter((d) => d.id !== deliverableId)
      );
      return { previous };
    },
    onError: (_err, _id, context) => {
      if (context?.previous) {
        queryClient.setQueryData(queryKey, context.previous);
      }
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey });
    },
  });

  return {
    deliverables: data,
    isLoading,
    error: error as Error | null,
    approve: (deliverableId: string) => approveMutation.mutateAsync(deliverableId),
    reject: (deliverableId: string) => rejectMutation.mutateAsync(deliverableId),
  };
}
