import { gatewayRequestJson } from './gatewayApiClient'

export type HiredAgentStudioMode = 'activation' | 'edit'
export type HiredAgentStudioStepKey = 'identity' | 'connection' | 'operating_plan' | 'review'

export type HiredAgentStudioStep = {
  key: HiredAgentStudioStepKey
  title: string
  complete: boolean
  blocked: boolean
  summary: string
}

export type HiredAgentStudioIdentity = {
  nickname?: string | null
  theme?: string | null
  complete: boolean
}

export type HiredAgentStudioConnection = {
  platform_key?: string | null
  skill_id?: string | null
  connection_id?: string | null
  customer_platform_credential_id?: string | null
  status: string
  complete: boolean
  summary: string
}

export type HiredAgentStudioOperatingPlan = {
  complete: boolean
  goals_completed: boolean
  goal_count: number
  skill_config_count: number
  summary: string
}

export type HiredAgentStudioReview = {
  complete: boolean
  summary: string
}

export type HiredAgentStudio = {
  hired_instance_id: string
  subscription_id: string
  agent_id: string
  agent_type_id: string
  customer_id?: string | null
  mode: HiredAgentStudioMode
  selection_required: boolean
  current_step: HiredAgentStudioStepKey
  steps: HiredAgentStudioStep[]
  identity: HiredAgentStudioIdentity
  connection: HiredAgentStudioConnection
  operating_plan: HiredAgentStudioOperatingPlan
  review: HiredAgentStudioReview
  configured: boolean
  goals_completed: boolean
  trial_status: string
  subscription_status?: string | null
  updated_at: string
}

export type HiredAgentStudioUpdate = {
  identity?: {
    nickname?: string | null
    theme?: string | null
  }
  connection?: {
    platform_key?: string
    skill_id?: string
    customer_platform_credential_id?: string | null
    secret_ref?: string | null
    mark_connected?: boolean
  }
  operating_plan?: {
    config_patch?: Record<string, unknown>
    skill_id?: string | null
    customer_fields?: Record<string, unknown>
    goals_completed?: boolean | null
  }
  review?: {
    goals_completed?: boolean | null
    finalize?: boolean
  }
}

export async function getHiredAgentStudio(hiredInstanceId: string): Promise<HiredAgentStudio> {
  return gatewayRequestJson<HiredAgentStudio>(
    `/cp/hired-agents/${encodeURIComponent(hiredInstanceId)}/studio`
  )
}

export async function updateHiredAgentStudio(
  hiredInstanceId: string,
  update: HiredAgentStudioUpdate
): Promise<HiredAgentStudio> {
  return gatewayRequestJson<HiredAgentStudio>(
    `/cp/hired-agents/${encodeURIComponent(hiredInstanceId)}/studio`,
    {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(update),
    }
  )
}