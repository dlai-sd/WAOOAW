import { gatewayRequestJson } from './gatewayApiClient'

export type GoalInstance = {
  goal_instance_id: string
  hired_instance_id: string
  goal_template_id: string
  frequency: string
  settings?: Record<string, unknown> | null
  created_at?: string | null
  updated_at?: string | null
}

export type GoalsListResponse = {
  hired_instance_id: string
  goals: GoalInstance[]
}

export type UpsertGoalInput = {
  goal_instance_id?: string | null
  goal_template_id: string
  frequency: string
  settings: Record<string, unknown>
}

export async function listHiredAgentGoals(hiredInstanceId: string): Promise<GoalsListResponse> {
  return gatewayRequestJson<GoalsListResponse>(
    `/cp/hired-agents/${encodeURIComponent(hiredInstanceId)}/goals`,
    { method: 'GET' }
  )
}

export async function upsertHiredAgentGoal(hiredInstanceId: string, input: UpsertGoalInput): Promise<GoalInstance> {
  return gatewayRequestJson<GoalInstance>(
    `/cp/hired-agents/${encodeURIComponent(hiredInstanceId)}/goals`,
    {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(input)
    }
  )
}

export async function deleteHiredAgentGoal(
  hiredInstanceId: string,
  goalInstanceId: string
): Promise<{ deleted: boolean; goal_instance_id: string }> {
  const qs = new URLSearchParams({ goal_instance_id: goalInstanceId })
  return gatewayRequestJson<{ deleted: boolean; goal_instance_id: string }>(
    `/cp/hired-agents/${encodeURIComponent(hiredInstanceId)}/goals?${qs.toString()}`,
    { method: 'DELETE' }
  )
}
