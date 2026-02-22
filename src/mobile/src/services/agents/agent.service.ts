/**
 * Agent Service
 * Handles all agent-related API calls to Plant backend
 * Ported from CP FrontEnd plant.service.ts
 */

import apiClient from '../../lib/apiClient';
import type {
  Agent,
  AgentListParams,
  AgentTypeDefinition,
  Skill,
  SkillListParams,
  JobRole,
  JobRoleListParams,
} from '../../types/agent.types';

/**
 * Agent Service - Type-safe client for Plant agent endpoints
 */
class AgentService {
  /**
   * Build query string from params
   */
  private buildQueryString(params: Record<string, any>): string {
    const filtered = Object.entries(params)
      .filter(([_, value]) => value !== undefined && value !== null)
      .map(([key, value]) => `${encodeURIComponent(key)}=${encodeURIComponent(String(value))}`)
      .join('&');

    return filtered ? `?${filtered}` : '';
  }

  // ========== AGENT TYPE ENDPOINTS ==========

  /**
   * List agent types (Phase-1 catalog)
   * 
   * @returns Promise<AgentTypeDefinition[]>
   */
  async listAgentTypes(): Promise<AgentTypeDefinition[]> {
    const response = await apiClient.get<AgentTypeDefinition[]>('/v1/agent-types');
    return response.data;
  }

  // ========== AGENT ENDPOINTS ==========

  /**
   * List agents with optional filters
   * Used for agent discovery/marketplace
   * 
   * @param params - Optional filter parameters (industry, job_role_id, status, q, limit, offset)
   * @returns Promise<Agent[]>
   */
  async listAgents(params: AgentListParams = {}): Promise<Agent[]> {
    const query = this.buildQueryString(params);
    const response = await apiClient.get<Agent[]>(`/v1/agents${query}`);
    return response.data;
  }

  /**
   * Get single agent by ID
   * Used for agent detail page
   * 
   * @param agentId - Agent ID
   * @returns Promise<Agent>
   */
  async getAgent(agentId: string): Promise<Agent> {
    const response = await apiClient.get<Agent>(`/v1/agents/${agentId}`);
    return response.data;
  }

  /**
   * Search agents using backend catalog search (q=...)
   * 
   * @param query - Search query string
   * @param params - Optional filter parameters
   * @returns Promise<Agent[]>
   */
  async searchAgents(query: string, params: AgentListParams = {}): Promise<Agent[]> {
    const trimmed = query.trim();
    if (!trimmed) {
      return this.listAgents(params);
    }

    const searchParams = { ...params, q: trimmed };
    return this.listAgents(searchParams);
  }

  // ========== SKILL ENDPOINTS ==========

  /**
   * List skills with optional filters
   * 
   * @param params - Optional filter parameters (category, limit, offset)
   * @returns Promise<Skill[]>
   */
  async listSkills(params: SkillListParams = {}): Promise<Skill[]> {
    const query = this.buildQueryString(params);
    const response = await apiClient.get<Skill[]>(`/v1/skills${query}`);
    return response.data;
  }

  /**
   * Get single skill by ID
   * 
   * @param skillId - Skill ID
   * @returns Promise<Skill>
   */
  async getSkill(skillId: string): Promise<Skill> {
    const response = await apiClient.get<Skill>(`/v1/skills/${skillId}`);
    return response.data;
  }

  // ========== JOB ROLE ENDPOINTS ==========

  /**
   * List job roles with optional filters
   * 
   * @param params - Optional filter parameters (limit, offset)
   * @returns Promise<JobRole[]>
   */
  async listJobRoles(params: JobRoleListParams = {}): Promise<JobRole[]> {
    const query = this.buildQueryString(params);
    const response = await apiClient.get<JobRole[]>(`/v1/job-roles${query}`);
    return response.data;
  }

  /**
   * Get single job role by ID
   * 
   * @param jobRoleId - Job role ID
   * @returns Promise<JobRole>
   */
  async getJobRole(jobRoleId: string): Promise<JobRole> {
    const response = await apiClient.get<JobRole>(`/v1/job-roles/${jobRoleId}`);
    return response.data;
  }
}

// Export singleton instance
export const agentService = new AgentService();
export default agentService;
