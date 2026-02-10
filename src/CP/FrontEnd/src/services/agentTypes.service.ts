import { gatewayRequestJson } from './gatewayApiClient'

export type FieldType = 'text' | 'enum' | 'list' | 'object' | 'boolean' | 'number'

export type SchemaFieldDefinition = {
  key: string
  label: string
  type: FieldType
  required?: boolean
  description?: string | null
  options?: string[] | null
  item_type?: FieldType | null
}

export type JsonSchemaDefinition = {
  fields: SchemaFieldDefinition[]
}

export type GoalTemplateDefinition = {
  goal_template_id: string
  name: string
  default_frequency: string
  settings_schema: JsonSchemaDefinition
  skill_binding?: string | null
}

export type EnforcementDefaults = {
  approval_required?: boolean
  deterministic?: boolean
}

export type AgentTypeDefinition = {
  agent_type_id: string
  version: string
  config_schema: JsonSchemaDefinition

  goal_templates?: GoalTemplateDefinition[]
  enforcement_defaults?: EnforcementDefaults
}

export async function getAgentTypeDefinition(agentTypeId: string): Promise<AgentTypeDefinition> {
  return gatewayRequestJson<AgentTypeDefinition>(`/v1/agent-types/${encodeURIComponent(agentTypeId)}`, { method: 'GET' })
}
