import { gatewayRequestJson } from './gatewayApiClient'
import type { PlatformConnection } from './platformConnections.service'

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

export type DigitalMarketingActivationWorkspace = {
  hired_instance_id: string
  help_visible: boolean
  activation_complete: boolean
  induction: {
    nickname: string
    theme: string
    primary_language: string
    timezone: string
    brand_name: string
    offerings_services: string[]
    location: string
    target_audience: string
    notes: string
  }
  prepare_agent: {
    selected_platforms: string[]
    platform_steps: DigitalMarketingPlatformStep[]
    all_selected_platforms_completed: boolean
  }
  campaign_setup: {
    campaign_id?: string | null
    master_theme: string
    derived_themes: DigitalMarketingDerivedTheme[]
    schedule: DigitalMarketingCampaignSchedule
  }
  updated_at: string
}

export type DigitalMarketingThemePlanResponse = {
  campaign_id?: string | null
  master_theme: string
  derived_themes: DigitalMarketingDerivedTheme[]
  workspace: DigitalMarketingActivationWorkspace
}

export async function getDigitalMarketingActivationWorkspace(hiredInstanceId: string) {
  return gatewayRequestJson<DigitalMarketingActivationWorkspace>(
    `/cp/digital-marketing-activation/${encodeURIComponent(hiredInstanceId)}`
  )
}

export async function patchDigitalMarketingActivationWorkspace(
  hiredInstanceId: string,
  patch: Partial<DigitalMarketingActivationWorkspace> | Record<string, unknown>
) {
  return gatewayRequestJson<DigitalMarketingActivationWorkspace>(
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
) {
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
) {
  return gatewayRequestJson<DigitalMarketingThemePlanResponse>(
    `/cp/digital-marketing-activation/${encodeURIComponent(hiredInstanceId)}/theme-plan`,
    {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(patch),
    }
  )
}

export function getNextPendingPlatform(
  selectedPlatforms: string[],
  platformSteps: DigitalMarketingPlatformStep[]
): string | null {
  const stepMap = new Map(
    (platformSteps || []).map((step) => [String(step.platform_key || '').trim().toLowerCase(), Boolean(step.complete)])
  )
  for (const platform of selectedPlatforms || []) {
    const key = String(platform || '').trim().toLowerCase()
    if (!key) continue
    if (!stepMap.get(key)) return key
  }
  return null
}

export function getPlatformPreparationState(
  platformKey: string,
  workspace: DigitalMarketingActivationWorkspace,
  connections: PlatformConnection[] = []
) {
  const normalizedKey = String(platformKey || '').trim().toLowerCase()
  const step = (workspace.prepare_agent.platform_steps || []).find(
    (item) => String(item.platform_key || '').trim().toLowerCase() === normalizedKey
  )
  const connection = (connections || []).find(
    (item) => String(item.platform_key || '').trim().toLowerCase() === normalizedKey
  ) || null
  return {
    platformKey: normalizedKey,
    selected: workspace.prepare_agent.selected_platforms.includes(normalizedKey),
    connected: Boolean(connection),
    complete: Boolean(step?.complete),
    ready: Boolean(connection) && Boolean(step?.complete),
  }
}
