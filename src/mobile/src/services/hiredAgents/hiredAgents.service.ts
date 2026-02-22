/**
 * Hired Agents Service
 * Handles all hired agent and subscription-related API calls
 * Interfaces with CP Backend for customer-specific hired agent data
 */

import apiClient from '../../lib/apiClient';
import type {
  HiredAgentInstance,
  MyAgentInstanceSummary,
  MyAgentsSummaryResponse,
  TrialStatusRecord,
  TrialStatusListResponse,
  HiredAgentsListParams,
} from '../../types/hiredAgents.types';

/**
 * Hired Agents Service - Type-safe client for hired agent endpoints
 * 
 * This service talks to:
 * 1. CP Backend (/cp/*) - Customer-scoped hired agent summary
 * 2. Plant Backend (/v1/*) - Trial status and hired agent details
 */
class HiredAgentsService {
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

  // ========== MY AGENTS (CP BACKEND) ==========

  /**
   * Get summary of all hired agents for current customer
   * This is the primary endpoint for "My Agents" screen
   * Returns combined subscription + hired instance data
   * 
   * Endpoint: GET /cp/my-agents/summary
   * Authentication: Requires valid session (user must be logged in)
   * 
   * @returns Promise<MyAgentInstanceSummary[]> - List of hired agent summaries
   */
  async listMyAgents(): Promise<MyAgentInstanceSummary[]> {
    const response = await apiClient.get<MyAgentsSummaryResponse>('/cp/my-agents/summary');
    return response.data.instances || [];
  }

  /**
   * Get hired agent instance by subscription ID
   * Returns full hired agent details including configuration
   * 
   * Endpoint: GET /cp/hired-agents/by-subscription/{subscriptionId}
   * Authentication: Requires valid session (customer_id injected by CP Backend)
   * 
   * @param subscriptionId - Subscription ID
   * @returns Promise<HiredAgentInstance> - Full hired agent instance
   */
  async getHiredAgentBySubscription(subscriptionId: string): Promise<HiredAgentInstance> {
    const response = await apiClient.get<HiredAgentInstance>(
      `/cp/hired-agents/by-subscription/${encodeURIComponent(subscriptionId)}`
    );
    return response.data;
  }

  // ========== TRIAL STATUS (PLANT BACKEND) ==========

  /**
   * List all trial statuses for current customer
   * Lightweight view of trial status without full hired instance data
   * 
   * Endpoint: GET /v1/trial-status
   * Note: customer_id is injected by CP Backend proxy based on session
   * 
   * @returns Promise<TrialStatusRecord[]> - List of trial status records
   */
  async listTrialStatus(): Promise<TrialStatusRecord[]> {
    const response = await apiClient.get<TrialStatusListResponse>('/v1/trial-status');
    return response.data.trials || [];
  }

  /**
   * Get trial status by subscription ID
   * Returns trial status for a specific subscription
   * 
   * Endpoint: GET /v1/trial-status/by-subscription/{subscriptionId}
   * Note: customer_id is injected by CP Backend proxy based on session
   * 
   * @param subscriptionId - Subscription ID
   * @returns Promise<TrialStatusRecord> - Trial status record
   */
  async getTrialStatusBySubscription(subscriptionId: string): Promise<TrialStatusRecord> {
    const response = await apiClient.get<TrialStatusRecord>(
      `/v1/trial-status/by-subscription/${encodeURIComponent(subscriptionId)}`
    );
    return response.data;
  }

  // ========== HELPER METHODS ==========

  /**
   * Get active hired agents (subscriptions with active status)
   * Filters the listMyAgents result to show only active hires
   * 
   * @returns Promise<MyAgentInstanceSummary[]> - Active hired agents
   */
  async listActiveHiredAgents(): Promise<MyAgentInstanceSummary[]> {
    const all = await this.listMyAgents();
    return all.filter(agent => agent.status === 'active');
  }

  /**
   * Get agents currently in trial
   * Filters to show only agents with active trial status
   * 
   * @returns Promise<MyAgentInstanceSummary[]> - Agents in trial
   */
  async listAgentsInTrial(): Promise<MyAgentInstanceSummary[]> {
    const all = await this.listMyAgents();
    return all.filter(agent => agent.trial_status === 'active');
  }

  /**
   * Get agents requiring setup (not configured or goals not completed)
   * Useful for onboarding flows
   * 
   * @returns Promise<MyAgentInstanceSummary[]> - Agents needing setup
   */
  async listAgentsNeedingSetup(): Promise<MyAgentInstanceSummary[]> {
    const all = await this.listMyAgents();
    return all.filter(agent => !agent.configured || !agent.goals_completed);
  }
}

// Export singleton instance
export const hiredAgentsService = new HiredAgentsService();
export default hiredAgentsService;
