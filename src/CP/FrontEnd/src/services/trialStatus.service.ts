import { gatewayRequestJson } from './gatewayApiClient'

export type TrialStatusRecord = {
  subscription_id: string
  hired_instance_id: string

  trial_status: string
  trial_start_at?: string | null
  trial_end_at?: string | null

  configured?: boolean
  goals_completed?: boolean
}

type TrialStatusListResponse = {
  trials?: TrialStatusRecord[]
}

export async function listTrialStatus(): Promise<TrialStatusRecord[]> {
  const res = await gatewayRequestJson<TrialStatusListResponse>('/v1/trial-status', { method: 'GET' })
  return res.trials || []
}
