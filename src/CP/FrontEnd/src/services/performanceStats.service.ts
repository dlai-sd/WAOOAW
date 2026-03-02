// src/CP/FrontEnd/src/services/performanceStats.service.ts
// Calls CP BackEnd /api/cp/... routes added in CP-SKILLS-1 Iteration 1.
// Uses gatewayRequestJson for auth header injection + correlation ID.

import { gatewayRequestJson } from './gatewayApiClient'

export interface PerformanceStat {
  stat_id?: string
  stat_date: string         // ISO date e.g. "2026-03-01"
  metric_key: string        // e.g. "posts_published", "emails_sent"
  metric_value: number
  metadata?: Record<string, unknown>
}

/**
 * Fetch performance stats for a hired agent.
 * Calls: GET /api/cp/hired-agents/{hired_instance_id}/performance-stats
 */
export async function listPerformanceStats(hiredInstanceId: string): Promise<PerformanceStat[]> {
  const data = await gatewayRequestJson<unknown>(
    `/cp/hired-agents/${encodeURIComponent(hiredInstanceId)}/performance-stats`
  )
  if (Array.isArray(data)) return data as PerformanceStat[]
  if (Array.isArray((data as any)?.stats)) return (data as any).stats as PerformanceStat[]
  if (Array.isArray((data as any)?.items)) return (data as any).items as PerformanceStat[]
  return []
}
