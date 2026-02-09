import { gatewayRequestJson } from './gatewayApiClient'

export type HireWizardDraft = {
  hired_instance_id: string
  subscription_id: string
  agent_id: string
  nickname?: string | null
  theme?: string | null
  config: Record<string, unknown>
  configured: boolean
  goals_completed: boolean
  subscription_status?: string | null
  trial_status: 'not_started' | 'active' | 'ended_converted' | 'ended_not_converted'
  trial_start_at?: string | null
  trial_end_at?: string | null
}

export type UpsertHireWizardDraftInput = {
  subscription_id: string
  agent_id: string
  nickname?: string
  theme?: string
  config?: Record<string, unknown>
}

export type FinalizeHireWizardInput = {
  hired_instance_id: string
  goals_completed: boolean
}

export async function upsertHireWizardDraft(input: UpsertHireWizardDraftInput): Promise<HireWizardDraft> {
  return gatewayRequestJson<HireWizardDraft>('/cp/hire/wizard/draft', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input)
  })
}

export async function getHireWizardDraftBySubscription(subscriptionId: string): Promise<HireWizardDraft> {
  return gatewayRequestJson<HireWizardDraft>(`/cp/hire/wizard/by-subscription/${encodeURIComponent(subscriptionId)}`)
}

export async function finalizeHireWizard(input: FinalizeHireWizardInput): Promise<HireWizardDraft> {
  return gatewayRequestJson<HireWizardDraft>('/cp/hire/wizard/finalize', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input)
  })
}
