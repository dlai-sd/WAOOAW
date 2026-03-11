/**
 * Hired Agents Service
 * Handles all hired agent and subscription-related API calls
 * Interfaces with CP Backend for customer-specific hired agent data
 */

import apiClient from '../../lib/apiClient';
import cpApiClient from '../../lib/cpApiClient';
import type {
  Deliverable,
  HiredAgentInstance,
  MyAgentInstanceSummary,
  MyAgentsSummaryResponse,
  TrialStatusRecord,
  TrialStatusListResponse,
  HiredAgentsListParams,
} from '../../types/hiredAgents.types';

export interface PlatformConnection {
  id: string;
  hired_instance_id: string;
  skill_id: string;
  platform_key: string;
  status?: string;
  connected_at?: string | null;
  last_verified_at?: string | null;
  created_at: string;
  updated_at: string;
}

export type PlatformConnectionSummary = {
  platformKey: string;
  label: string;
  message: string;
  tone: 'success' | 'warning' | 'danger' | 'informative';
  isReady: boolean;
  connection: PlatformConnection | null;
}

export type DeliverableChannelTarget = {
  platformKey: string | null;
  handle: string | null;
  visibility: string;
  publicReleaseRequested: boolean;
  credentialRef: string | null;
  publishStatus: string;
  platformPostId: string | null;
}

export type DeliverablePublishReadiness = {
  key:
    | 'already_published'
    | 'publish_failed'
    | 'blocked_missing_approval'
    | 'blocked_rejected'
    | 'blocked_missing_channel_connection'
    | 'uploaded_non_public'
    | 'ready_for_public_release'
    | 'ready_for_upload';
  label: string;
  message: string;
  tone: 'success' | 'warning' | 'danger' | 'informative';
};

function asRecord(value: unknown): Record<string, unknown> | null {
  if (!value || typeof value !== 'object' || Array.isArray(value)) {
    return null;
  }
  return value as Record<string, unknown>;
}

function stringOrNull(value: unknown): string | null {
  const normalized = String(value ?? '').trim();
  return normalized ? normalized : null;
}

function booleanFromUnknown(value: unknown): boolean {
  if (typeof value === 'boolean') return value;
  const normalized = String(value ?? '').trim().toLowerCase();
  return normalized === 'true' || normalized === '1' || normalized === 'yes';
}

export function getDeliverableChannelTarget(deliverable: Deliverable): DeliverableChannelTarget {
  const payload = asRecord(deliverable.payload) || {};
  const destination = asRecord(payload.destination) || asRecord(payload.destination_ref) || {};
  const metadata = asRecord(destination.metadata) || asRecord(payload.metadata) || {};
  const publishReceipt = asRecord(payload.publish_receipt) || {};

  const platformKey =
    stringOrNull(destination.destination_type) ||
    stringOrNull(payload.destination_type) ||
    stringOrNull(payload.channel) ||
    stringOrNull(payload.platform) ||
    stringOrNull(payload.primary_destination);

  const visibility =
    stringOrNull(metadata.visibility) ||
    stringOrNull(payload.visibility) ||
    'private';

  const publishStatus =
    stringOrNull(payload.publish_status) ||
    stringOrNull((publishReceipt as Record<string, unknown>).status) ||
    'not_published';

  return {
    platformKey,
    handle: stringOrNull(destination.handle) || stringOrNull(payload.channel_handle),
    visibility,
    publicReleaseRequested:
      booleanFromUnknown(metadata.public_release_requested) || booleanFromUnknown(payload.public_release_requested),
    credentialRef:
      stringOrNull(metadata.credential_ref) || stringOrNull(payload.credential_ref),
    publishStatus,
    platformPostId:
      stringOrNull((publishReceipt as Record<string, unknown>).platform_post_id) ||
      stringOrNull(payload.platform_post_id),
  };
}

export function getDeliverablePublishReadiness(
  deliverable: Deliverable,
  options?: { hasPlatformConnection?: boolean | null; platformLabel?: string | null }
): DeliverablePublishReadiness {
  const reviewStatus = String(deliverable.review_status || '').trim().toLowerCase() || 'pending_review';
  const executionStatus = String(deliverable.execution_status || '').trim().toLowerCase();
  const channel = getDeliverableChannelTarget(deliverable);
  const platformLabel = options?.platformLabel || channel.platformKey || 'the publishing channel';
  const publishStatus = String(channel.publishStatus || '').trim().toLowerCase();
  const hasPlatformConnection = options?.hasPlatformConnection;

  if (publishStatus === 'published' || channel.platformPostId) {
    return {
      key: 'already_published',
      label: 'Already published',
      message: `This deliverable already has a live ${platformLabel} publish receipt.`,
      tone: 'success',
    };
  }

  if (publishStatus === 'failed') {
    return {
      key: 'publish_failed',
      label: 'Publish failed',
      message: `The last ${platformLabel} publish attempt failed. Review the channel state before retrying.`,
      tone: 'danger',
    };
  }

  if (reviewStatus === 'rejected') {
    return {
      key: 'blocked_rejected',
      label: 'Blocked by rejection',
      message: 'This draft was rejected, so nothing will upload until a revised deliverable is approved.',
      tone: 'danger',
    };
  }

  if (reviewStatus !== 'approved') {
    return {
      key: 'blocked_missing_approval',
      label: 'Blocked by approval',
      message: 'This draft is review-ready, but nothing can publish until you approve the exact deliverable.',
      tone: 'warning',
    };
  }

  if (hasPlatformConnection === false) {
    return {
      key: 'blocked_missing_channel_connection',
      label: 'Blocked by missing channel connection',
      message: `Approve is complete, but ${platformLabel} still needs a verified connection before upload can happen.`,
      tone: 'danger',
    };
  }

  if (executionStatus === 'executed' && channel.visibility !== 'public') {
    return {
      key: 'uploaded_non_public',
      label: 'Uploaded as non-public',
      message: `The content has been uploaded to ${platformLabel} with ${channel.visibility} visibility and is not public yet.`,
      tone: 'informative',
    };
  }

  if (channel.publicReleaseRequested || channel.visibility === 'public') {
    return {
      key: 'ready_for_public_release',
      label: 'Ready for public release',
      message: `Approval and channel readiness are satisfied. The next ${platformLabel} step can release this publicly.`,
      tone: 'success',
    };
  }

  return {
    key: 'ready_for_upload',
    label: 'Ready for upload',
    message: `Approval is in place and ${platformLabel} is ready. The next step can upload this without making it public automatically.`,
    tone: 'success',
  };
}

export function findPlatformConnection(
  connections: PlatformConnection[],
  platformKey: string
): PlatformConnection | null {
  const normalized = String(platformKey || '').trim().toLowerCase();
  return connections.find((connection) => String(connection.platform_key || '').trim().toLowerCase() === normalized) || null;
}

export function getPlatformConnectionSummary(
  connections: PlatformConnection[],
  platformKey: string
): PlatformConnectionSummary {
  const connection = findPlatformConnection(connections, platformKey);
  const label = platformKey[0]?.toUpperCase() ? `${platformKey[0].toUpperCase()}${platformKey.slice(1)}` : 'Channel';

  if (!connection) {
    return {
      platformKey,
      label: `${label} not connected`,
      message: `Connect ${label} before the agent can upload anything externally.`,
      tone: 'danger',
      isReady: false,
      connection: null,
    };
  }

  const status = String(connection.status || '').trim().toLowerCase();
  if (status === 'connected' || status === 'active') {
    return {
      platformKey,
      label: `${label} connected`,
      message: connection.last_verified_at
        ? `${label} was last verified on ${new Date(connection.last_verified_at).toLocaleString()}.`
        : `${label} is connected and available for upload gating.`,
      tone: 'success',
      isReady: true,
      connection,
    };
  }

  if (status === 'pending') {
    return {
      platformKey,
      label: `${label} pending verification`,
      message: `${label} is connected but still needs verification before uploads should proceed.`,
      tone: 'warning',
      isReady: false,
      connection,
    };
  }

  return {
    platformKey,
    label: `${label} needs attention`,
    message: `${label} has a connection record, but its current state is ${status || 'unknown'}. Review it before upload.`,
    tone: 'warning',
    isReady: false,
    connection,
  };
}

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
    const response = await cpApiClient.get<MyAgentsSummaryResponse>('/cp/my-agents/summary');
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
    const response = await cpApiClient.get<HiredAgentInstance>(
      `/cp/hired-agents/by-subscription/${encodeURIComponent(subscriptionId)}`
    );
    return response.data;
  }

  async getHiredAgentById(hiredAgentId: string): Promise<HiredAgentInstance> {
    const response = await apiClient.get<HiredAgentInstance>(
      `/api/v1/hired-agents/by-id/${encodeURIComponent(hiredAgentId)}`
    );
    return response.data;
  }

  async getDeliverablesByHiredAgent(hiredAgentId: string): Promise<Deliverable[]> {
    const response = await cpApiClient.get<{ deliverables?: Deliverable[] }>(
      `/cp/hired-agents/${encodeURIComponent(hiredAgentId)}/deliverables`
    );
    return response.data.deliverables || [];
  }

  async listPlatformConnections(hiredAgentId: string): Promise<PlatformConnection[]> {
    const response = await cpApiClient.get<{ connections?: PlatformConnection[] } | PlatformConnection[]>(
      `/cp/hired-agents/${encodeURIComponent(hiredAgentId)}/platform-connections`
    );
    if (Array.isArray(response.data)) return response.data;
    return response.data.connections || [];
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
