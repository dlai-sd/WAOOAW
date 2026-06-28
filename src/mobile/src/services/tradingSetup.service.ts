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

export async function emergencyStop(
  hiredInstanceId: string
): Promise<{ status: string; stopped_at: string }> {
  const resp = await apiClient.post(
    `/api/cp/trading-setup/${encodeURIComponent(hiredInstanceId)}/emergency-stop`,
    {},
    { headers: HEADERS() }
  )
  return resp.data
}

export type TradeHistoryRow = {
  stat_date: string
  skill_id: string
  trades_count: number
  pnl_pct_avg: number
  win_rate: number
  stop_loss_count: number
}

export type TradeHistoryResponse = {
  hired_instance_id: string
  trades: TradeHistoryRow[]
  total: number
  page: number
  page_size: number
}

export async function getTradeHistory(
  hiredInstanceId: string,
  page: number = 1,
  pageSize: number = 20
): Promise<TradeHistoryResponse> {
  const resp = await apiClient.get(
    `/api/cp/trading/history/${encodeURIComponent(hiredInstanceId)}`,
    { params: { page, page_size: pageSize }, headers: HEADERS() }
  )
  return resp.data
}

export type TaxReportResponse = {
  hired_instance_id: string
  period: string
  year: number
  total_trades: number
  total_pnl_pct: number
  profitable_trades: number
  loss_trades: number
  stop_loss_exits: number
  trades: Array<{
    date: string
    skill_id: string
    trades_count: number
    pnl_pct: number
    win_rate: number
    stop_loss_count: number
  }>
}

export async function getTaxReport(
  hiredInstanceId: string,
  year: number,
  period: 'monthly' | 'quarterly',
  month?: number,
  quarter?: string
): Promise<TaxReportResponse> {
  const params: Record<string, string | number> = { year, period }
  if (month !== undefined) params.month = month
  if (quarter !== undefined) params.quarter = quarter
  const resp = await apiClient.get(
    `/api/cp/trading/tax-report/${encodeURIComponent(hiredInstanceId)}`,
    { params, headers: HEADERS() }
  )
  return resp.data
}
