/**
 * useContentAnalytics Hook (MOB-PARITY-1 E3-S1)
 *
 * React Query wrapper for content analytics / recommendations.
 */

import { useQuery } from '@tanstack/react-query';
import { getContentRecommendations, ContentRecommendation } from '../services/contentAnalytics.service';

export interface UseContentAnalyticsResult {
  data: ContentRecommendation | null;
  isLoading: boolean;
  error: Error | null;
  refetch: () => void;
}

export function useContentAnalytics(hiredAgentId: string | undefined): UseContentAnalyticsResult {
  const query = useQuery<ContentRecommendation>({
    queryKey: ['contentAnalytics', hiredAgentId],
    queryFn: () => getContentRecommendations(hiredAgentId!),
    enabled: !!hiredAgentId,
    staleTime: 1000 * 60 * 5,
    retry: 2,
    retryDelay: (attemptIndex) => Math.min(1000 * Math.pow(2, attemptIndex), 10000),
  });

  return {
    data: query.data ?? null,
    isLoading: query.isLoading,
    error: query.error as Error | null,
    refetch: query.refetch,
  };
}
