// src/CP/FrontEnd/src/services/agentSkills.service.ts
// Calls CP BackEnd /api/cp/... routes added in CP-SKILLS-1 Iteration 1.
// Uses gatewayRequestJson for auth header injection + correlation ID.

import { gatewayRequestJson } from './gatewayApiClient'

export interface GoalSchemaField {
  key: string
  label: string
  type: 'text' | 'number' | 'boolean' | 'enum' | 'list' | 'object'
  required?: boolean
  description?: string
  options?: string[]
  item_type?: string
  min?: number
  max?: number
  max_plan_gate?: string
}

export interface GoalSchema {
  fields: GoalSchemaField[]
  requires_platform_connections?: boolean
}

export interface AgentSkill {
  skill_id: string
  name: string
  display_name: string
  description?: string
  category?: string
  goal_schema?: GoalSchema
}

/**
 * Fetch all skills assigned to a hired agent.
 * Calls: GET /api/cp/hired-agents/{hired_instance_id}/skills
 */
export async function listHiredAgentSkills(hiredInstanceId: string): Promise<AgentSkill[]> {
  const data = await gatewayRequestJson<unknown>(
    `/cp/hired-agents/${encodeURIComponent(hiredInstanceId)}/skills`
  )
  if (Array.isArray(data)) return data as AgentSkill[]
  if (Array.isArray((data as any)?.skills)) return (data as any).skills as AgentSkill[]
  if (Array.isArray((data as any)?.items)) return (data as any).items as AgentSkill[]
  return []
}

/**
 * Fetch a single skill (including its full goal_schema).
 * Calls: GET /api/cp/skills/{skill_id}
 */
export async function getSkill(skillId: string): Promise<AgentSkill> {
  return gatewayRequestJson<AgentSkill>(`/cp/skills/${encodeURIComponent(skillId)}`)
}
