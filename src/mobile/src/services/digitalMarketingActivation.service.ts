import apiClient from '@/lib/apiClient'

function generateCorrelationId(): string {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0
    const v = c === 'x' ? r : (r & 0x3) | 0x8
    return v.toString(16)
  })
}

export type DigitalMarketingPlatformKey =
  | 'youtube'
  | 'instagram'
  | 'facebook'
  | 'linkedin'
  | 'whatsapp'
  | 'x'
  | 'twitter'

export type DigitalMarketingPlatformBinding = {
  skill_id?: string
  credential_id?: string
  credential_ref?: string
  customer_platform_credential_id?: string
  connected?: boolean
}

export type DigitalMarketingDerivedTheme = {
  title: string
  description?: string
  frequency?: string
}

export type DigitalMarketingPlatformStep = {
  platform_key: string
  complete: boolean
  status?: string
}

export type DigitalMarketingCampaignSchedule = {
  start_date: string
  posts_per_week: number
  preferred_days: string[]
  preferred_hours_utc: number[]
}

export type DigitalMarketingStrategyWorkshopMessage = {
  role: 'assistant' | 'user'
  content: string
}

export type DigitalMarketingStrategyWorkshopSummary = {
  profession_name?: string
  location_focus?: string
  customer_profile?: string
  service_focus?: string
  signature_differentiator?: string
  business_goal?: string
  first_content_direction?: string
  business_focus?: string
  audience?: string
  positioning?: string
  tone?: string
  content_pillars?: string[]
  youtube_angle?: string
  cta?: string
}

export type DigitalMarketingStrategyWorkshop = {
  status?: 'not_started' | 'discovery' | 'approval_ready' | 'approved'
  assistant_message?: string
  checkpoint_summary?: string
  current_focus_question?: string
  next_step_options?: string[]
  time_saving_note?: string
  follow_up_questions?: string[]
  messages?: DigitalMarketingStrategyWorkshopMessage[]
  summary?: DigitalMarketingStrategyWorkshopSummary
  approved_at?: string | null
  brief_progress?: {
    filled: number
    total: number
    missing_fields: string[]
    locked_fields: Record<string, string>
  }
  performance_insights?: {
    top_performing_dimensions: string[]
    best_posting_hours: number[]
    avg_engagement_rate: number
    recommendation_summary: string
  }
}

export type DigitalMarketingCampaignSetup = {
  campaign_id?: string | null
  master_theme?: string
  derived_themes?: DigitalMarketingDerivedTheme[]
  schedule?: Partial<DigitalMarketingCampaignSchedule>
  strategy_workshop?: DigitalMarketingStrategyWorkshop
}

export type DigitalMarketingLegacyWorkspace = {
  hired_instance_id: string
  help_visible?: boolean
  activation_complete?: boolean
  induction?: {
    nickname?: string
    theme?: string
    primary_language?: string
    timezone?: string
    brand_name?: string
    offerings_services?: string[]
    location?: string
    target_audience?: string
    notes?: string
  }
  prepare_agent?: {
    selected_platforms?: string[]
    platform_steps?: DigitalMarketingPlatformStep[]
    all_selected_platforms_completed?: boolean
  }
  campaign_setup?: {
    campaign_id?: string | null
    master_theme?: string
    derived_themes?: DigitalMarketingDerivedTheme[]
    schedule?: Partial<DigitalMarketingCampaignSchedule>
  }
  updated_at: string
}

export type DigitalMarketingThemePlanResponse = {
  campaign_id?: string | null
  master_theme: string
  derived_themes: DigitalMarketingDerivedTheme[]
  workspace: DigitalMarketingLegacyWorkspace | DigitalMarketingActivationResponse
}

export type DigitalMarketingActivationWorkspace = {
  help_visible?: boolean
  activation_complete?: boolean
  brand_name?: string
  location?: string
  primary_language?: string
  timezone?: string
  business_context?: string
  offerings_services?: string[]
  platforms_enabled?: string[]
  selected_platforms?: string[]
  platform_bindings?: Record<string, DigitalMarketingPlatformBinding>
  campaign_setup?: DigitalMarketingCampaignSetup
}

export type DigitalMarketingActivationReadiness = {
  brief_complete: boolean
  youtube_selected: boolean
  youtube_connection_ready: boolean
  configured: boolean
  can_finalize: boolean
  missing_requirements: string[]
}

export type DigitalMarketingActivationResponse = {
  hired_instance_id: string
  customer_id?: string | null
  agent_type_id: string
  workspace: DigitalMarketingActivationWorkspace
  readiness: DigitalMarketingActivationReadiness
  updated_at: string
}

export type UpsertDigitalMarketingActivationInput = {
  workspace: DigitalMarketingActivationWorkspace
}

export async function getDigitalMarketingActivationWorkspace(
  hiredInstanceId: string
): Promise<DigitalMarketingActivationResponse> {
  const resp = await apiClient.get(
    `/api/v1/hired-agents/${encodeURIComponent(hiredInstanceId)}/digital-marketing-activation`
  )
  return resp.data
}

export async function upsertDigitalMarketingActivationWorkspace(
  hiredInstanceId: string,
  input: UpsertDigitalMarketingActivationInput
): Promise<DigitalMarketingActivationResponse> {
  const resp = await apiClient.put(
    `/api/v1/hired-agents/${encodeURIComponent(hiredInstanceId)}/digital-marketing-activation`,
    input,
    { headers: { 'X-Correlation-ID': generateCorrelationId(), 'Content-Type': 'application/json' } }
  )
  return resp.data
}

export async function patchDigitalMarketingActivationWorkspace(
  hiredInstanceId: string,
  patch: Record<string, unknown>
): Promise<DigitalMarketingActivationResponse> {
  const resp = await apiClient.patch(
    `/api/v1/hired-agents/${encodeURIComponent(hiredInstanceId)}/digital-marketing-activation`,
    patch,
    { headers: { 'X-Correlation-ID': generateCorrelationId(), 'Content-Type': 'application/json' } }
  )
  return resp.data
}

export async function generateDigitalMarketingThemePlan(
  hiredInstanceId: string,
  patch: Record<string, unknown> = {}
): Promise<DigitalMarketingThemePlanResponse> {
  const resp = await apiClient.post(
    `/api/v1/digital-marketing-activation/${encodeURIComponent(hiredInstanceId)}/generate-theme-plan`,
    patch,
    { headers: { 'X-Correlation-ID': generateCorrelationId(), 'Content-Type': 'application/json' } }
  )
  return resp.data
}
