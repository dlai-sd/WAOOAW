import { gatewayRequestJson } from './gatewayApiClient'

export type TradingRunResponse = {
  agent_id: string
  agent_type: string
  status: string
  draft: Record<string, unknown>
  review?: Record<string, unknown> | null
  published?: boolean
}

export type DraftTradePlanInput = {
  agent_id?: string
  exchange_account_id: string
  coin: string
  units: number
  side: 'long' | 'short'
  action: 'enter' | 'exit'
  market?: boolean
  limit_price?: number
}

export async function draftTradePlan(input: DraftTradePlanInput): Promise<TradingRunResponse> {
  return gatewayRequestJson<TradingRunResponse>('/cp/trading/draft-plan', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input)
  })
}

export type ApproveExecuteTradeInput = DraftTradePlanInput & {
  intent_action: 'place_order' | 'close_position'
}

export async function approveAndExecuteTrade(input: ApproveExecuteTradeInput): Promise<TradingRunResponse> {
  return gatewayRequestJson<TradingRunResponse>('/cp/trading/approve-execute', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input)
  })
}
