/**
 * Agent Service
 * Handles all agent-related API calls to Plant backend
 * Ported from CP FrontEnd plant.service.ts
 */

import apiClient from "../../lib/apiClient";
import { getAPIConfig } from "../../config/api.config";
import type {
  Agent,
  AgentListParams,
  AgentTypeDefinition,
  Skill,
  SkillListParams,
  JobRole,
  JobRoleListParams,
} from "../../types/agent.types";

/**
 * Shape returned by Plant Backend /api/v1/catalog/agents
 */
interface CatalogAgentResponse {
  release_id: string;
  id: string;
  public_name: string;
  short_description: string;
  industry_name: string;
  job_role_label: string;
  monthly_price_inr: number;
  trial_days: number;
  allowed_durations: string[];
  supported_channels: string[];
  agent_type_id: string;
  lifecycle_state: string;
  approved_for_new_hire: boolean;
  retired_from_catalog_at: string | null;
}

/**
 * Map a catalog release record → mobile Agent shape
 */
function catalogToAgent(c: CatalogAgentResponse): Agent {
  return {
    id: c.id,
    name: c.public_name,
    description: c.short_description,
    industry: (c.industry_name || "").toLowerCase() as Agent["industry"],
    job_role_id: "", // not in catalog; not used by AgentCard
    entity_type: "agent",
    status: c.lifecycle_state === "live" ? "active" : "inactive",
    specialization: c.job_role_label,
    price: c.monthly_price_inr,
    trial_days: c.trial_days,
    allowed_durations: c.allowed_durations,
    created_at: new Date().toISOString(),
  };
}

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
      .map(
        ([key, value]) =>
          `${encodeURIComponent(key)}=${encodeURIComponent(String(value))}`,
      )
      .join("&");

    return filtered ? `?${filtered}` : "";
  }

  // ========== AGENT TYPE ENDPOINTS ==========

  /**
   * List agent types (Phase-1 catalog)
   *
   * @returns Promise<AgentTypeDefinition[]>
   */
  async listAgentTypes(): Promise<AgentTypeDefinition[]> {
    const response = await apiClient.get<AgentTypeDefinition[]>(
      "/api/v1/agent-types",
    );
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
    // Use the catalog endpoint — it returns live marketplace releases with pricing,
    // trial config, and display names. The raw /api/v1/agents table is for PP admin.
    const response = await apiClient.get<CatalogAgentResponse[]>(
      "/api/v1/catalog/agents",
    );
    const all = response.data.map(catalogToAgent);

    // Apply client-side filters that the catalog endpoint doesn't support directly
    return all.filter((agent) => {
      if (params.industry && agent.industry !== params.industry) return false;
      if (params.q) {
        const needle = params.q.trim().toLowerCase();
        if (
          needle &&
          !(
            agent.name.toLowerCase().includes(needle) ||
            (agent.description || "").toLowerCase().includes(needle) ||
            (agent.specialization || "").toLowerCase().includes(needle) ||
            agent.industry.toLowerCase().includes(needle)
          )
        )
          return false;
      }
      return true;
    });
  }

  /**
   * Get single agent by ID
   * Used for agent detail page
   *
   * @param agentId - Agent ID
   * @returns Promise<Agent>
   */
  async getAgent(agentId: string): Promise<Agent> {
    const response = await apiClient.get<CatalogAgentResponse>(
      `/api/v1/catalog/agents/${encodeURIComponent(agentId)}`,
    );
    return catalogToAgent(response.data);
  }

  /**
   * Search agents using backend catalog search (q=...)
   *
   * @param query - Search query string
   * @param params - Optional filter parameters
   * @returns Promise<Agent[]>
   */
  async searchAgents(
    query: string,
    params: AgentListParams = {},
  ): Promise<Agent[]> {
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
    const response = await apiClient.get<Skill[]>(`/api/v1/skills${query}`);
    return response.data;
  }

  /**
   * Get single skill by ID
   *
   * @param skillId - Skill ID
   * @returns Promise<Skill>
   */
  async getSkill(skillId: string): Promise<Skill> {
    const response = await apiClient.get<Skill>(`/api/v1/skills/${skillId}`);
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
    const response = await apiClient.get<JobRole[]>(
      `/api/v1/job-roles${query}`,
    );
    return response.data;
  }

  /**
   * Get single job role by ID
   *
   * @param jobRoleId - Job role ID
   * @returns Promise<JobRole>
   */
  async getJobRole(jobRoleId: string): Promise<JobRole> {
    const response = await apiClient.get<JobRole>(
      `/api/v1/job-roles/${jobRoleId}`,
    );
    return response.data;
  }
}

// Export singleton instance
export const agentService = new AgentService();
export default agentService;
