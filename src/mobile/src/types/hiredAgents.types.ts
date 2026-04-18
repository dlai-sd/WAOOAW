/**
 * Hired Agents Types
 * Types for hired agents, subscriptions, and trial management
 * Aligned with CP Backend API schemas
 */

/**
 * Trial status for hired agent instances
 */
export type TrialStatus =
  | 'not_started'
  | 'active'
  | 'expired'
  | 'converted'
  | 'canceled';

/**
 * Subscription status from payment system
 */
export type SubscriptionStatus =
  | 'active'
  | 'inactive'
  | 'past_due'
  | 'canceled'
  | 'paused';

/**
 * Subscription duration types
 */
export type SubscriptionDuration = 'monthly' | 'quarterly' | 'yearly';

/**
 * Deliverable types for agents
 */
export type DeliverableType = 'pdf' | 'image' | 'report' | 'link' | 'document';

/**
 * Deliverable review status
 */
export type DeliverableReviewStatus = 
  | 'pending_review'
  | 'approved'
  | 'rejected'
  | 'revision_requested';

/**
 * Scheduled post created by an agent for a campaign
 */
export interface ScheduledPost {
  id: string;
  title?: string;
  content_preview?: string;
  target_platform?: string;
  status: 'queued' | 'published' | 'failed';
  scheduled_at?: string;
  published_at?: string;
}

/**
 * Deliverable from agent execution
 * Represents work output from hired agents
 */
export interface Deliverable {
  deliverable_id: string;
  hired_instance_id: string;
  agent_id: string;
  goal_instance_id?: string | null;
  
  // Content
  title: string;
  description?: string | null;
  type: DeliverableType;
  url?: string | null;
  file_path?: string | null;
  payload?: Record<string, unknown> | null;
  
  // Status
  review_status: DeliverableReviewStatus;
  review_notes?: string | null;
  approval_id?: string | null;
  execution_status?: string | null;
  executed_at?: string | null;
  
  // Metadata
  goal_template_id?: string | null;
  frequency?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
}

/**
 * Hired agent instance from Plant backend
 * Represents a customer's hired agent with configuration and trial status
 */
export interface HiredAgentInstance {
  hired_instance_id: string;
  subscription_id: string;
  agent_id: string;
  agent_type_id?: string | null;
  customer_id?: string | null;

  // Configuration
  nickname?: string | null;
  theme?: string | null;
  config?: Record<string, unknown>;

  // Setup status
  configured?: boolean;
  goals_completed?: boolean;

  // Trial status
  trial_status?: TrialStatus | null;
  trial_start_at?: string | null;
  trial_end_at?: string | null;

  // Subscription status
  subscription_status?: SubscriptionStatus | null;
  subscription_ended_at?: string | null;
  retention_expires_at?: string | null;

  // Metadata
  active?: boolean;
  created_at: string;
  updated_at: string;
}

/**
 * Trial status record from Plant backend
 * Lightweight view of trial status for a hired agent
 */
export interface TrialStatusRecord {
  subscription_id: string;
  hired_instance_id: string;

  // Trial status
  trial_status: TrialStatus;
  trial_start_at?: string | null;
  trial_end_at?: string | null;

  // Setup status
  configured?: boolean;
  goals_completed?: boolean;
}

/**
 * My agent instance summary from CP Backend
 * Combines subscription data with hired agent instance details
 * This is the primary list view for "My Agents" screen
 */
export interface MyAgentInstanceSummary {
  // Subscription data
  subscription_id: string;
  agent_id: string;
  duration?: SubscriptionDuration | null;
  status: SubscriptionStatus;
  current_period_start?: string | null;
  current_period_end?: string | null;
  cancel_at_period_end?: boolean | null;

  // Hired agent instance data (enriched from Plant)
  hired_instance_id?: string | null;
  agent_type_id?: string | null;
  nickname?: string | null;

  // Setup status
  configured?: boolean;
  goals_completed?: boolean;

  // Trial status
  trial_status?: TrialStatus | null;
  trial_start_at?: string | null;
  trial_end_at?: string | null;

  // Subscription status
  subscription_status?: SubscriptionStatus | null;
  subscription_ended_at?: string | null;
  retention_expires_at?: string | null;
}

/**
 * Response from CP Backend /cp/my-agents/summary endpoint
 */
export interface MyAgentsSummaryResponse {
  instances: MyAgentInstanceSummary[];
}

/**
 * Response from Plant Backend /v1/trial-status endpoint
 */
export interface TrialStatusListResponse {
  trials?: TrialStatusRecord[];
}

/**
 * Query parameters for listing hired agents
 */
export interface HiredAgentsListParams {
  status?: SubscriptionStatus;
  trial_status?: TrialStatus;
  limit?: number;
  offset?: number;
}
