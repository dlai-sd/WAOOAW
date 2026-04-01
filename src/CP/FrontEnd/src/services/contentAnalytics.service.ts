import { gatewayRequestJson } from './gatewayApiClient'

export interface ContentRecommendation {
  top_dimensions: string[]
  best_posting_hours: number[]
  avg_engagement_rate: number
  total_posts_analyzed: number
  recommendation_text: string
}

export async function getContentRecommendations(hiredInstanceId: string): Promise<ContentRecommendation> {
  return gatewayRequestJson<ContentRecommendation>(
    `/cp/content-recommendations/${encodeURIComponent(hiredInstanceId)}`,
    { method: 'GET' }
  )
}
