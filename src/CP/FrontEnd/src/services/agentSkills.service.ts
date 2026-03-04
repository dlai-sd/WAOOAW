// src/CP/FrontEnd/src/services/agentSkills.service.ts
// Calls CP BackEnd /api/cp/... routes added in CP-SKILLS-1 Iteration 1.
// Uses gatewayRequestJson for auth header injection + correlation ID.
// CP-SKILLS-2: added goal_config field and saveGoalConfig().

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
  /** Conditional display: this field is only shown when values[show_if.key] === show_if.value. */
  show_if?: { key: string; value: unknown }
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
  /** Persisted customer configuration for this skill's goals. Null until first save. */
  goal_config?: Record<string, unknown>
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

/**
 * Persist the customer's goal configuration for a specific skill on a hired agent.
 * Calls: PATCH /api/cp/hired-agents/{hired_instance_id}/skills/{skill_id}/goal-config
 *
 * CP-SKILLS-2 E3-S1
 *
 * @param hiredInstanceId  The hired_instance_id (from HiredAgent)
 * @param skillId          The skill_id (from AgentSkill)
 * @param goalConfig       Arbitrary key-value config matching the skill's goal_schema
 * @returns                Updated AgentSkillResponse (includes goal_schema + saved goal_config)
 */
export async function saveGoalConfig(
  hiredInstanceId: string,
  skillId: string,
  goalConfig: Record<string, unknown>
): Promise<AgentSkill> {
  return gatewayRequestJson<AgentSkill>(
    `/cp/hired-agents/${encodeURIComponent(hiredInstanceId)}/skills/${encodeURIComponent(skillId)}/goal-config`,
    {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ goal_config: goalConfig }),
    }
  )
}
