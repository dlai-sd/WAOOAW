/**
 * TypeScript types for Plant API entities
 * Mirrors Plant backend Pydantic models
 */

/**
 * Skill category types
 */
export type SkillCategory = 'technical' | 'soft_skill' | 'domain_expertise'

/**
 * Seniority levels for job roles
 */
export type SeniorityLevel = 'entry' | 'mid' | 'senior' | 'expert'

/**
 * Entity status (Genesis certification)
 */
export type EntityStatus = 'pending_certification' | 'certified' | 'rejected'

/**
 * Agent status
 */
export type AgentStatus = 'active' | 'inactive' | 'suspended'

/**
 * Industry types
 */
export type Industry = 'marketing' | 'education' | 'sales' | 'healthcare' | 'finance' | 'general'

/**
 * Skill entity from Plant backend
 */
export interface Skill {
  id: string
  name: string
  description: string
  category: SkillCategory
  entity_type: string
  status: EntityStatus
  created_at: string
  updated_at?: string
  l0_compliance_status?: Record<string, boolean>
}

/**
 * Job role entity from Plant backend
 */
export interface JobRole {
  id: string
  name: string
  description: string
  required_skills: string[]  // Array of skill IDs
  seniority_level: SeniorityLevel
  entity_type: string
  status: EntityStatus
  created_at: string
  updated_at?: string
  l0_compliance_status?: Record<string, boolean>
}

/**
 * Agent entity from Plant backend
 */
export interface Agent {
  id: string
  name: string
  description?: string
  job_role_id: string
  industry: Industry
  entity_type: string
  status: AgentStatus
  team_id?: string
  created_at: string
  updated_at?: string
  l0_compliance_status?: Record<string, boolean>
  
  // Computed fields for frontend display
  job_role?: JobRole  // Populated by join
  rating?: number      // Future: average rating
  trial_days?: number
  allowed_durations?: string[]
  price?: number       // Monthly price (INR)
  specialization?: string  // Future: agent specialty
}

/**
 * Request body for creating a skill
 */
export interface SkillCreateRequest {
  name: string
  description: string
  category: SkillCategory
  governance_agent_id?: string
}

/**
 * Request body for creating a job role
 */
export interface JobRoleCreateRequest {
  name: string
  description: string
  required_skills: string[]
  seniority_level: SeniorityLevel
  governance_agent_id?: string
}

/**
 * Request body for creating an agent
 */
export interface AgentCreateRequest {
  name: string
  description: string
  job_role_id: string
  industry: Industry
  team_id?: string
  governance_agent_id?: string
}

/**
 * Query parameters for listing skills
 */
export interface SkillListParams {
  category?: SkillCategory
  limit?: number
  offset?: number
}

/**
 * Query parameters for listing job roles
 */
export interface JobRoleListParams {
  limit?: number
  offset?: number
}

/**
 * Query parameters for listing agents
 */
export interface AgentListParams {
  industry?: Industry
  job_role_id?: string
  status?: AgentStatus
  q?: string
  limit?: number
  offset?: number
}

/**
 * Audit report from Plant backend
 */
export interface AuditReport {
  compliance_score: number
  total_entities: number
  total_violations: number
  timestamp: string
  l0_breakdown: Record<string, {
    description: string
    violations: number
    passed: boolean
  }>
  l1_breakdown: Record<string, {
    description: string
    violations: number
    passed: boolean
  }>
}

/**
 * Tampering detection report
 */
export interface TamperingReport {
  entity_id: string
  tampering_detected: boolean
  hash_chain_valid: boolean
  broken_links: number
  details: string
}

/**
 * RFC 7807 Problem Details error response
 */
export interface ProblemDetails {
  type: string
  title: string
  status: number
  detail: string
  instance?: string
  correlation_id?: string
  timestamp?: string
}

/**
 * API error class
 */
export class PlantAPIError extends Error {
  status: number
  type: string
  detail: string
  correlationId?: string

  constructor(problem: ProblemDetails) {
    super(problem.title)
    this.name = 'PlantAPIError'
    this.status = problem.status
    this.type = problem.type
    this.detail = problem.detail
    this.correlationId = problem.correlation_id
  }
}
