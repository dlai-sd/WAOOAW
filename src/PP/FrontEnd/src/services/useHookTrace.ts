import { useState, useCallback } from 'react'
import { gatewayRequestJson } from './gatewayApiClient'

export interface HookTraceEntry {
  event_id: string
  stage: string
  hired_agent_id: string
  agent_type: string
  result: 'proceed' | 'halt' | string
  reason: string
  emitted_at: string
  payload_summary: string
  hook_class?: string | null
}

export function useHookTrace(hiredAgentId: string) {
  const [data, setData] = useState<HookTraceEntry[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<unknown>(null)

  const refetch = useCallback(
    async (filters?: { stage?: string; result?: string; limit?: number }) => {
      if (!hiredAgentId) return
      setIsLoading(true)
      setError(null)
      try {
        const params = new URLSearchParams()
        if (filters?.stage) params.set('stage', filters.stage)
        if (filters?.result) params.set('result', filters.result)
        params.set('limit', String(filters?.limit ?? 50))
        const result = await gatewayRequestJson<HookTraceEntry[]>(
          `/pp/ops/hired-agents/${encodeURIComponent(hiredAgentId)}/hook-trace?${params.toString()}`
        )
        setData(result)
      } catch (e: unknown) {
        setError(e)
      } finally {
        setIsLoading(false)
      }
    },
    [hiredAgentId]
  )

  return { data, isLoading, error, refetch }
}
