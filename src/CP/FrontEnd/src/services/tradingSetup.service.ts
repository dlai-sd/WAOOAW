import { gatewayRequestJson } from './gatewayApiClient'

// ── Types ─────────────────────────────────────────────────────────────────

export type TradingSetupMessage = {
  role: 'assistant' | 'user'
  content: string
  masked: boolean
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
}

export type TradingSetupResponse = {
  hired_instance_id: string
  state: TradingSetupState
  readiness: TradingSetupReadiness
}

export type TradePerformanceSummary = {
  hired_instance_id: string
  period_days: number
  trades_count: number
  pnl_pct_avg: number
  win_rate: number
  stop_loss_count: number
  profit_count: number
  last_stat_date: string | null
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

export type TaxReportEntry = {
  date: string
  skill_id: string
  trades_count: number
  pnl_pct: number
  win_rate: number
  stop_loss_count: number
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
  trades: TaxReportEntry[]
}

export type TradeRecommendation = {
  hired_instance_id: string
  current_rsi_buy_threshold: number
  current_rsi_sell_threshold: number
  suggested_rsi_buy_threshold: number
  suggested_rsi_sell_threshold: number
  confidence: number
  rationale: string
  sample_size: number
  engine: string
}

// ── API functions ──────────────────────────────────────────────────────────

export async function getTradingSetup(hiredInstanceId: string): Promise<TradingSetupResponse> {
  return gatewayRequestJson<TradingSetupResponse>(
    `/cp/trading-setup/${encodeURIComponent(hiredInstanceId)}`
  )
}

export async function sendTradingSetupMessage(
  hiredInstanceId: string,
  content: string
): Promise<TradingSetupResponse> {
  return gatewayRequestJson<TradingSetupResponse>(
    `/cp/trading-setup/${encodeURIComponent(hiredInstanceId)}/message`,
    { method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content }) }
  )
}

export async function emergencyStop(hiredInstanceId: string): Promise<{ status: string; stopped_at: string }> {
  return gatewayRequestJson<{ status: string; stopped_at: string }>(
    `/cp/trading-setup/${encodeURIComponent(hiredInstanceId)}/emergency-stop`,
    { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}' }
  )
}

export async function getTradePerformance(
  hiredInstanceId: string,
  periodDays = 90
): Promise<TradePerformanceSummary> {
  return gatewayRequestJson<TradePerformanceSummary>(
    `/cp/trading/performance/${encodeURIComponent(hiredInstanceId)}?period_days=${periodDays}`
  )
}

export async function getTradeHistory(
  hiredInstanceId: string,
  page = 1,
  pageSize = 20
): Promise<TradeHistoryResponse> {
  return gatewayRequestJson<TradeHistoryResponse>(
    `/cp/trading/history/${encodeURIComponent(hiredInstanceId)}?page=${page}&page_size=${pageSize}`
  )
}

export async function getTaxReport(
  hiredInstanceId: string,
  year: number,
  period: 'monthly' | 'quarterly',
  month?: number,
  quarter?: string
): Promise<TaxReportResponse> {
  const qs = new URLSearchParams({ year: String(year), period })
  if (period === 'monthly' && month != null) qs.append('month', String(month))
  if (period === 'quarterly' && quarter) qs.append('quarter', quarter)
  return gatewayRequestJson<TaxReportResponse>(
    `/cp/trading/tax-report/${encodeURIComponent(hiredInstanceId)}?${qs}`
  )
}

export async function getRecommendations(hiredInstanceId: string): Promise<TradeRecommendation> {
  return gatewayRequestJson<TradeRecommendation>(
    `/cp/trading/recommendations/${encodeURIComponent(hiredInstanceId)}`
  )
}
