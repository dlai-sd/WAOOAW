import { gatewayRequestJson } from './gatewayApiClient'

export type DigitalMarketingPlatformKey = 'youtube' | 'instagram' | 'facebook' | 'linkedin' | 'whatsapp' | 'x' | 'twitter'

export type DigitalMarketingPlatformBinding = {
  skill_id?: string
  credential_id?: string
  credential_ref?: string
  customer_platform_credential_id?: string
  connected?: boolean
}

export type DigitalMarketingActivationWorkspace = {
  brand_name?: string
  location?: string
  primary_language?: string
  timezone?: string
  business_context?: string
  offerings_services?: string[]
  platforms_enabled?: string[]
  selected_platforms?: string[]
  platform_bindings?: Record<string, DigitalMarketingPlatformBinding>
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