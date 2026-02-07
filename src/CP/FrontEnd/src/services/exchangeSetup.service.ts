import { gatewayRequestJson } from './gatewayApiClient'

export type RiskLimits = {
  max_units_per_order: number
  max_notional_inr?: number | null
}

export type ExchangeSetup = {
  credential_ref: string
  customer_id: string
  exchange_provider: string
  default_coin: string
  allowed_coins: string[]
  risk_limits: RiskLimits
  created_at: string
  updated_at: string
  metadata?: Record<string, unknown>
}

export type UpsertExchangeSetupInput = {
  credential_ref?: string
  exchange_provider: string
  api_key: string
  api_secret: string
  default_coin: string
  allowed_coins?: string[]
  max_units_per_order: number
  max_notional_inr?: number
}

export async function listExchangeSetups(): Promise<ExchangeSetup[]> {
  return gatewayRequestJson<ExchangeSetup[]>('/cp/exchange-setup')
}

export async function upsertExchangeSetup(input: UpsertExchangeSetupInput): Promise<ExchangeSetup> {
  return gatewayRequestJson<ExchangeSetup>('/cp/exchange-setup', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input)
  })
}
