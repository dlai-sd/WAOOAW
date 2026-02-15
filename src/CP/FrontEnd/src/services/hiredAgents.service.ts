import { gatewayRequestJson } from './gatewayApiClient'

export type HiredAgentInstance = {
  hired_instance_id: string
  subscription_id: string
  agent_id: string

  agent_type_id?: string | null

  nickname?: string | null
  theme?: string | null
  config?: Record<string, unknown>

  configured?: boolean
  goals_completed?: boolean
  trial_status?: string | null
}

export type UpsertHiredAgentDraftInput = {
  subscription_id: string
  agent_id: string
  agent_type_id: string
  nickname?: string
  theme?: string
  config?: Record<string, unknown>
}

export async function getHiredAgentBySubscription(subscriptionId: string): Promise<HiredAgentInstance> {
  return gatewayRequestJson<HiredAgentInstance>(
    `/cp/hired-agents/by-subscription/${encodeURIComponent(subscriptionId)}`,
    { method: 'GET' }
  )
}

export async function upsertHiredAgentDraft(input: UpsertHiredAgentDraftInput): Promise<HiredAgentInstance> {
  return gatewayRequestJson<HiredAgentInstance>('/cp/hired-agents/draft', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input)
  })
}
