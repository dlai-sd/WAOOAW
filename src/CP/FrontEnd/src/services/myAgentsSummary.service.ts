import { gatewayRequestJson } from './gatewayApiClient'

export type MyAgentInstanceSummary = {
  subscription_id: string
  agent_id: string
  duration: string
  status: string
  current_period_start: string
  current_period_end: string
  cancel_at_period_end: boolean

  hired_instance_id?: string | null
  agent_type_id?: string | null
  nickname?: string | null

  configured?: boolean
  goals_completed?: boolean

  trial_status?: string | null
  trial_start_at?: string | null
  trial_end_at?: string | null

  subscription_status?: string | null
  subscription_ended_at?: string | null
  retention_expires_at?: string | null
}

export type MyAgentsSummaryResponse = {
  instances: MyAgentInstanceSummary[]
}

export async function getMyAgentsSummary(): Promise<MyAgentsSummaryResponse> {
  return gatewayRequestJson<MyAgentsSummaryResponse>('/cp/my-agents/summary', { method: 'GET' })
}
