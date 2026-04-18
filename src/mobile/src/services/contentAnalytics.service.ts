/**
 * Content Analytics Service (MOB-PARITY-1 E3-S1)
 *
 * Matches CP Frontend contentAnalytics.service.ts — same endpoint contract.
 */

import apiClient from '../lib/apiClient';

export interface ContentRecommendation {
  top_dimensions: string[];
  best_posting_hours: number[];
  avg_engagement_rate: number;
  total_posts_analyzed: number;
  recommendation_text: string;
}

export async function getContentRecommendations(
  hiredAgentId: string
): Promise<ContentRecommendation> {
  const response = await apiClient.get<ContentRecommendation>(
    `/api/v1/hired-agents/${hiredAgentId}/content-recommendations`
  );
  return response.data;
}
