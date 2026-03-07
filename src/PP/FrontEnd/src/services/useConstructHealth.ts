import { useState, useCallback } from 'react'
import { gatewayRequestJson } from './gatewayApiClient'

export interface ConstructStatus {
  status: 'healthy' | 'degraded' | 'offline' | string
  [key: string]: unknown
}

export interface ConstructHealthResponse {
  hired_agent_id: string
  scheduler: ConstructStatus
  pump: ConstructStatus
  processor: ConstructStatus
  connector: ConstructStatus & { secret_ref?: string }
  publisher: ConstructStatus
  policy: ConstructStatus
}

export function useConstructHealth(hiredAgentId: string) {
  const [data, setData] = useState<ConstructHealthResponse | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<unknown>(null)

  const refetch = useCallback(async () => {
    if (!hiredAgentId) return
    setIsLoading(true)
    setError(null)
    try {
      const result = await gatewayRequestJson<ConstructHealthResponse>(
        `/pp/ops/hired-agents/${encodeURIComponent(hiredAgentId)}/construct-health`
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
