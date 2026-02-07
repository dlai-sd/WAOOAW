import { gatewayRequestJson } from './gatewayApiClient'

export type TradingStrategyConfig = {
  config_ref: string
  customer_id: string
  agent_id: string
  interval_seconds?: number | null
  active_window?: { start: string; end: string } | null
  metadata?: Record<string, unknown>
  created_at: string
  updated_at: string
}

export type UpsertTradingStrategyConfigInput = {
  config_ref?: string
  agent_id?: string
  interval_seconds?: number
  active_window_start?: string
  active_window_end?: string
  strategy_params?: Record<string, unknown>
}

export async function listTradingStrategyConfigs(agentId?: string): Promise<TradingStrategyConfig[]> {
  const qs = agentId ? `?agent_id=${encodeURIComponent(agentId)}` : ''
  return gatewayRequestJson<TradingStrategyConfig[]>(`/cp/trading-strategy${qs}`)
}

export async function upsertTradingStrategyConfig(
  input: UpsertTradingStrategyConfigInput
): Promise<TradingStrategyConfig> {
  return gatewayRequestJson<TradingStrategyConfig>('/cp/trading-strategy', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input)
  })
}
