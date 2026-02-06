/**
 * Plant API Service
 * Handles all communication with Plant backend API
 * Provides type-safe methods for agent discovery, skills, job roles
 */

import type {
  Agent,
  AgentListParams,
  Skill,
  SkillListParams,
  JobRole,
  JobRoleListParams,
  AuditReport,
  TamperingReport,
  ProblemDetails,
  PlantAPIError as PlantAPIErrorType
} from '../types/plant.types'
import { PlantAPIError } from '../types/plant.types'
import config from '../config/oauth.config'

/**
 * Configuration for Plant API
 */
interface PlantAPIConfig {
  baseUrl: string
  timeout?: number
  retries?: number
}

/**
 * Default configuration
 */
const DEFAULT_CONFIG: PlantAPIConfig = {
  // Single-door entry: always call through CP backend (/api/*), which proxies to Plant Gateway.
  baseUrl: `${config.apiBaseUrl}/v1`,
  timeout: 30000,  // 30 seconds
  retries: 3
}

/**
 * PlantAPIService - Type-safe client for Plant backend
 */
class PlantAPIService {
  private config: PlantAPIConfig
  private correlationIdGenerator: () => string

  constructor(config: Partial<PlantAPIConfig> = {}) {
    this.config = { ...DEFAULT_CONFIG, ...config }
    this.correlationIdGenerator = () => crypto.randomUUID()
  }

  /**
   * Make HTTP request with retry logic
   */
  private async request<T>(
    endpoint: string,
    options: RequestInit = {},
    retryCount = 0
  ): Promise<T> {
    const url = `${this.config.baseUrl}${endpoint}`
    const correlationId = this.correlationIdGenerator()

    try {
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), this.config.timeout)

      const response = await fetch(url, {
        ...options,
        signal: controller.signal,
        headers: {
          'Content-Type': 'application/json',
          'X-Correlation-ID': correlationId,
          ...options.headers
        }
      })

      clearTimeout(timeoutId)

      // Handle error responses (RFC 7807)
      if (!response.ok) {
        const problem: ProblemDetails = await response.json()
        throw new PlantAPIError({
          ...problem,
          correlation_id: correlationId
        })
      }

      return await response.json()
    } catch (error) {
      // Retry logic for network errors
      if (retryCount < (this.config.retries || 3)) {
        const delay = Math.min(1000 * Math.pow(2, retryCount), 10000)  // Exponential backoff
        await new Promise(resolve => setTimeout(resolve, delay))
        return this.request<T>(endpoint, options, retryCount + 1)
      }

      // Re-throw PlantAPIError as-is
      if (error instanceof PlantAPIError) {
        throw error
      }

      // Wrap other errors
      throw new Error(`Plant API request failed: ${error instanceof Error ? error.message : String(error)}`)
    }
  }

  /**
   * Build query string from params
   */
  private buildQueryString(params: Record<string, any>): string {
    const filtered = Object.entries(params)
      .filter(([_, value]) => value !== undefined && value !== null)
      .map(([key, value]) => `${encodeURIComponent(key)}=${encodeURIComponent(String(value))}`)
      .join('&')
    
    return filtered ? `?${filtered}` : ''
  }

  // ========== AGENT ENDPOINTS ==========

  /**
   * List agents with optional filters
   * Used for agent discovery/marketplace
   */
  async listAgents(params: AgentListParams = {}): Promise<Agent[]> {
    const query = this.buildQueryString(params)
    return this.request<Agent[]>(`/agents${query}`)
  }

  /**
   * Get single agent by ID
   * Used for agent detail page
   */
  async getAgent(agentId: string): Promise<Agent> {
    return this.request<Agent>(`/agents/${agentId}`)
  }

  /**
   * Search agents by name (frontend-only filter for now)
   * TODO: Add backend search endpoint
   */
  async searchAgents(query: string, params: AgentListParams = {}): Promise<Agent[]> {
    const agents = await this.listAgents(params)
    const lowerQuery = query.toLowerCase()
    return agents.filter(agent => 
      agent.name.toLowerCase().includes(lowerQuery) ||
      agent.description.toLowerCase().includes(lowerQuery)
    )
  }

  // ========== SKILL ENDPOINTS ==========

  /**
   * List skills (for displaying agent capabilities)
   */
  async listSkills(params: SkillListParams = {}): Promise<Skill[]> {
    const query = this.buildQueryString(params)
    return this.request<Skill[]>(`/genesis/skills${query}`)
  }

  /**
   * Get single skill by ID
   */
  async getSkill(skillId: string): Promise<Skill> {
    return this.request<Skill>(`/genesis/skills/${skillId}`)
  }

  // ========== JOB ROLE ENDPOINTS ==========

  /**
   * List job roles (for filtering agents)
   */
  async listJobRoles(params: JobRoleListParams = {}): Promise<JobRole[]> {
    const query = this.buildQueryString(params)
    return this.request<JobRole[]>(`/genesis/job-roles${query}`)
  }

  /**
   * Get single job role by ID (with skills populated)
   */
  async getJobRole(jobRoleId: string): Promise<JobRole> {
    return this.request<JobRole>(`/genesis/job-roles/${jobRoleId}`)
  }

  /**
   * Get skills for a job role (helper method)
   */
  async getJobRoleSkills(jobRoleId: string): Promise<Skill[]> {
    const jobRole = await this.getJobRole(jobRoleId)
    const skillPromises = jobRole.required_skills.map(skillId => this.getSkill(skillId))
    return Promise.all(skillPromises)
  }

  // ========== ENRICHMENT METHODS ==========

  /**
   * Get agent with job role details populated
   * Useful for agent detail pages
   */
  async getAgentWithJobRole(agentId: string): Promise<Agent & { job_role: JobRole }> {
    const agent = await this.getAgent(agentId)
    const jobRole = await this.getJobRole(agent.job_role_id)
    return { ...agent, job_role: jobRole }
  }

  /**
   * Get agents with job role details (for marketplace grid)
   * Batch fetches to reduce round-trips
   */
  async listAgentsWithJobRoles(params: AgentListParams = {}): Promise<Array<Agent & { job_role: JobRole }>> {
    const agents = await this.listAgents(params)
    
    // Get unique job role IDs
    const jobRoleIds = [...new Set(agents.map(a => a.job_role_id))]
    
    // Batch fetch job roles
    const jobRolesPromises = jobRoleIds.map(id => this.getJobRole(id))
    const jobRoles = await Promise.all(jobRolesPromises)
    
    // Create lookup map
    const jobRoleMap = new Map(jobRoles.map(jr => [jr.id, jr]))
    
    // Enrich agents with job role data
    return agents.map(agent => ({
      ...agent,
      job_role: jobRoleMap.get(agent.job_role_id)!
    }))
  }

  // ========== AUDIT ENDPOINTS (Future: Admin/Transparency) ==========

  /**
   * Run compliance audit (for transparency page - future)
   */
  async runComplianceAudit(entityType?: string): Promise<AuditReport> {
    const query = entityType ? `?entity_type=${entityType}` : ''
    return this.request<AuditReport>(`/audit/run${query}`, { method: 'POST' })
  }

  /**
   * Check tampering for entity (for trust badge - future)
   */
  async checkTampering(entityId: string): Promise<TamperingReport> {
    return this.request<TamperingReport>(`/audit/tampering/${entityId}`)
  }
}

/**
 * Export singleton instance
 */
export const plantAPIService = new PlantAPIService()

/**
 * Export class for testing
 */
export default PlantAPIService
