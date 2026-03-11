import { useState, useCallback } from 'react'
import { gatewayRequestJson } from './gatewayApiClient'

export interface DlqEntry {
  dlq_id: string
  hired_agent_id: string
  failed_at: string
  hook_stage: string
  error_message: string
  retry_count: number
}

export interface SchedulerDiagnosticsResponse {
  hired_agent_id: string
  cron_expression: string
  next_run?: string | null
  next_run_at?: string | null
  last_run?: string | null
  last_run_at?: string | null
  lag_seconds?: number | null
  dlq_depth: number
  dlq_entries?: DlqEntry[]
  tasks_used_today?: number | null
  trial_task_limit?: number | null
  is_paused?: boolean
  pause_state?: string | null
  latest_failure_reason?: string | null
  latest_approval_id?: string | null
  latest_deliverable_id?: string | null
}

export function useSchedulerDiagnostics(hiredAgentId: string) {
  const [data, setData] = useState<SchedulerDiagnosticsResponse | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<unknown>(null)

  const refetch = useCallback(async () => {
    if (!hiredAgentId) return
    setIsLoading(true)
    setError(null)
    try {
      const result = await gatewayRequestJson<SchedulerDiagnosticsResponse>(
        `/pp/ops/hired-agents/${encodeURIComponent(hiredAgentId)}/scheduler-diagnostics`
      )
      setData(result)
    } catch (e: unknown) {
      setError(e)
    } finally {
      setIsLoading(false)
    }
  }, [hiredAgentId])

  return { data, isLoading, error, refetch }
}
