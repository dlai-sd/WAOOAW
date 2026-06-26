import apiClient from '@/lib/apiClient'

function generateCorrelationId(): string {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0
    const v = c === 'x' ? r : (r & 0x3) | 0x8
    return v.toString(16)
  })
}

export type TradingSetupMessage = {
  role: 'assistant' | 'user'
  content: string
  masked?: boolean
}

export type TradingSetupReadiness = {
  configured: boolean
  step: string
  has_credentials: boolean
  credentials_valid: boolean
  has_instrument: boolean
  has_rsi_period: boolean
  has_risk_limits: boolean
}

export type TradingSetupState = {
  step: string
  messages: TradingSetupMessage[]
  collected: Record<string, unknown>
  validation_status: 'pending' | 'valid' | 'invalid'
  configured: boolean
  updated_at: string
}

export type TradingSetupResponse = {
  hired_instance_id: string
  state: TradingSetupState
  readiness: TradingSetupReadiness
}

const HEADERS = () => ({
  'X-Correlation-ID': generateCorrelationId(),
  'Content-Type': 'application/json',
})

export async function getTradingSetup(
  hiredInstanceId: string
): Promise<TradingSetupResponse> {
  const resp = await apiClient.get(
    `/api/cp/trading-setup/${encodeURIComponent(hiredInstanceId)}`
  )
  return resp.data
}

export async function sendTradingSetupMessage(
  hiredInstanceId: string,
  content: string
): Promise<TradingSetupResponse> {
  const resp = await apiClient.post(
    `/api/cp/trading-setup/${encodeURIComponent(hiredInstanceId)}/message`,
    { content },
    { headers: HEADERS() }
  )
  return resp.data
}
