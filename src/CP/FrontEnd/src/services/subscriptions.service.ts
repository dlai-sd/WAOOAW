import { gatewayRequestJson } from './gatewayApiClient'

export type Subscription = {
  subscription_id: string
  agent_id: string
  duration: string
  status: string
  current_period_start: string
  current_period_end: string
  cancel_at_period_end: boolean
}

export async function listSubscriptions(): Promise<Subscription[]> {
  return gatewayRequestJson<Subscription[]>('/cp/subscriptions/', { method: 'GET' })
}

export async function cancelSubscription(subscriptionId: string): Promise<Subscription> {
  return gatewayRequestJson<Subscription>(`/cp/subscriptions/${encodeURIComponent(subscriptionId)}/cancel`, {
    method: 'POST'
  })
}
