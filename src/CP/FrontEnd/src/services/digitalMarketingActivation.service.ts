import { gatewayRequestJson } from './gatewayApiClient'
import type { PlatformConnection } from './platformConnections.service'

export type DigitalMarketingPlatformKey = 'youtube' | 'instagram' | 'facebook' | 'linkedin' | 'whatsapp' | 'x' | 'twitter'

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
  follow_up_questions?: string[]
  messages?: DigitalMarketingStrategyWorkshopMessage[]
  summary?: DigitalMarketingStrategyWorkshopSummary
  approved_at?: string | null
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
  return gatewayRequestJson<DigitalMarketingActivationResponse>(
    `/cp/digital-marketing-activation/${encodeURIComponent(hiredInstanceId)}`,
    { method: 'GET' }
  )
}

export async function upsertDigitalMarketingActivationWorkspace(
  hiredInstanceId: string,
  input: UpsertDigitalMarketingActivationInput
): Promise<DigitalMarketingActivationResponse> {
  return gatewayRequestJson<DigitalMarketingActivationResponse>(
    `/cp/digital-marketing-activation/${encodeURIComponent(hiredInstanceId)}`,
    {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(input),
    }
  )
}

export async function patchDigitalMarketingActivationWorkspace(
  hiredInstanceId: string,
  patch: Partial<DigitalMarketingLegacyWorkspace> | Record<string, unknown>
): Promise<DigitalMarketingActivationResponse> {
  return gatewayRequestJson<DigitalMarketingActivationResponse>(
    `/cp/digital-marketing-activation/${encodeURIComponent(hiredInstanceId)}`,
    {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(patch),
    }
  )
}

export async function generateDigitalMarketingThemePlan(
  hiredInstanceId: string,
  patch: Record<string, unknown> = {}
): Promise<DigitalMarketingThemePlanResponse> {
  return gatewayRequestJson<DigitalMarketingThemePlanResponse>(
    `/cp/digital-marketing-activation/${encodeURIComponent(hiredInstanceId)}/generate-theme-plan`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(patch),
    }
  )
}

export async function patchDigitalMarketingThemePlan(
  hiredInstanceId: string,
  patch: Record<string, unknown>
): Promise<DigitalMarketingThemePlanResponse> {
  return gatewayRequestJson<DigitalMarketingThemePlanResponse>(
    `/cp/digital-marketing-activation/${encodeURIComponent(hiredInstanceId)}/theme-plan`,
    {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(patch),
    }
  )
}

export function getSelectedMarketingPlatforms(
  workspace: DigitalMarketingActivationWorkspace | null | undefined
): string[] {
  const raw = workspace?.platforms_enabled || workspace?.selected_platforms || []
  if (!Array.isArray(raw)) return []
  return raw
    .map((value) => String(value || '').trim().toLowerCase())
    .filter(Boolean)
}

export function buildMarketingPlatformBindings(
  selectedPlatforms: string[],
  existingBindings: Record<string, DigitalMarketingPlatformBinding> | null | undefined,
  defaultSkillId = 'default'
): Record<string, DigitalMarketingPlatformBinding> {
  const current = existingBindings && typeof existingBindings === 'object' ? existingBindings : {}
  return selectedPlatforms.reduce<Record<string, DigitalMarketingPlatformBinding>>((acc, platform) => {
    const normalized = String(platform || '').trim().toLowerCase()
    if (!normalized) return acc
    const existing = current[normalized] || {}
    acc[normalized] = {
      ...existing,
      skill_id: String(existing.skill_id || defaultSkillId).trim() || defaultSkillId,
    }
    return acc
  }, {})
}

export function getActivationMilestoneCount(readiness: DigitalMarketingActivationReadiness): number {
  let complete = 0
  if (readiness.configured) complete += 1
  if (readiness.brief_complete) complete += 1
  if (!readiness.youtube_selected || readiness.youtube_connection_ready) complete += 1
  return complete
}

export function getNextPendingPlatform(
  selectedPlatforms: string[],
  platformSteps: DigitalMarketingPlatformStep[]
): string | null {
  const stepMap = new Map(
    (platformSteps || []).map((step) => [String(step.platform_key || '').trim().toLowerCase(), Boolean(step.complete)])
  )
  for (const platform of selectedPlatforms || []) {
    const normalized = String(platform || '').trim().toLowerCase()
    if (!normalized) continue
    if (!stepMap.get(normalized)) return normalized
  }
  return null
}

export function getPlatformPreparationState(
  platformKey: string,
  workspace: Partial<DigitalMarketingLegacyWorkspace> | null | undefined,
  connections: PlatformConnection[] = []
) {
  const normalizedKey = String(platformKey || '').trim().toLowerCase()
  const selectedPlatforms = Array.isArray(workspace?.prepare_agent?.selected_platforms)
    ? workspace?.prepare_agent?.selected_platforms || []
    : []
  const platformSteps = Array.isArray(workspace?.prepare_agent?.platform_steps)
    ? workspace?.prepare_agent?.platform_steps || []
    : []
  const step = platformSteps.find(
    (item) => String(item.platform_key || '').trim().toLowerCase() === normalizedKey
  )
  const connection = (connections || []).find(
    (item) => String(item.platform_key || '').trim().toLowerCase() === normalizedKey
  ) || null

  return {
    platformKey: normalizedKey,
    selected: selectedPlatforms.includes(normalizedKey),
    connected: Boolean(connection),
    complete: Boolean(step?.complete),
    ready: Boolean(connection) && Boolean(step?.complete),
  }
}