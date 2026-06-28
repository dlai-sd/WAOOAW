import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { FluentProvider } from '@fluentui/react-components'
import { waooawLightTheme } from '../theme'
import { TradingDashboardPanel } from '../components/TradingDashboardPanel'
import type { TradePerformanceSummary, TradeRecommendation } from '../services/tradingSetup.service'

vi.mock('../services/tradingSetup.service', () => ({
  getTradePerformance: vi.fn(),
  getRecommendations: vi.fn(),
}))

const makePerf = (overrides: Partial<TradePerformanceSummary> = {}): TradePerformanceSummary => ({
  hired_instance_id: 'HIRED-1',
  period_days: 90,
  trades_count: 42,
  pnl_pct_avg: 1.8,
  win_rate: 0.62,
  stop_loss_count: 5,
  profit_count: 26,
  last_stat_date: '2026-06-01',
  ...overrides,
})

const makeRec = (overrides: Partial<TradeRecommendation> = {}): TradeRecommendation => ({
  hired_instance_id: 'HIRED-1',
  current_rsi_buy_threshold: 30,
  current_rsi_sell_threshold: 70,
  suggested_rsi_buy_threshold: 28,
  suggested_rsi_sell_threshold: 72,
  confidence: 0.85,
  rationale: 'Based on 42 trades in the period.',
  sample_size: 42,
  engine: 'v1',
  ...overrides,
})

const renderPanel = (hiredInstanceId = 'HIRED-1') =>
  render(
    <FluentProvider theme={waooawLightTheme}>
      <TradingDashboardPanel hiredInstanceId={hiredInstanceId} />
    </FluentProvider>
  )

describe('TradingDashboardPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('T1: three stat cards render with correct values', async () => {
    const { getTradePerformance, getRecommendations } = await import('../services/tradingSetup.service')
    vi.mocked(getTradePerformance).mockResolvedValue(makePerf())
    vi.mocked(getRecommendations).mockResolvedValue(makeRec({ confidence: 0.5 }))

    renderPanel()

    await waitFor(() => {
      expect(screen.getByTestId('stat-trades')).toBeInTheDocument()
    })
    expect(screen.getByTestId('stat-trades').textContent).toBe('42')
    expect(screen.getByTestId('stat-pnl').textContent).toBe('1.8%')
    expect(screen.getByTestId('stat-winrate').textContent).toBe('62%')
  })

  it('T2: RSI recommendation shown only when confidence >= 0.7', async () => {
    const { getTradePerformance, getRecommendations } = await import('../services/tradingSetup.service')
    vi.mocked(getTradePerformance).mockResolvedValue(makePerf())

    // confidence < 0.7 — should NOT show
    vi.mocked(getRecommendations).mockResolvedValue(makeRec({ confidence: 0.65 }))
    const { unmount } = renderPanel()

    await waitFor(() => {
      expect(screen.getByTestId('trading-dashboard')).toBeInTheDocument()
    })
    expect(screen.queryByTestId('rec-text')).not.toBeInTheDocument()
    unmount()

    // confidence >= 0.7 — should show
    vi.mocked(getTradePerformance).mockResolvedValue(makePerf())
    vi.mocked(getRecommendations).mockResolvedValue(makeRec({ confidence: 0.85 }))
    renderPanel()

    await waitFor(() => {
      expect(screen.getByTestId('rec-text')).toBeInTheDocument()
    })
    expect(screen.getByTestId('rec-text').textContent).toContain('28')
    expect(screen.getByTestId('rec-text').textContent).toContain('72')
  })

  it('T3: period change to 30d triggers re-fetch', async () => {
    const { getTradePerformance, getRecommendations } = await import('../services/tradingSetup.service')
    vi.mocked(getTradePerformance).mockResolvedValue(makePerf())
    vi.mocked(getRecommendations).mockResolvedValue(makeRec({ confidence: 0.5 }))

    renderPanel()

    await waitFor(() => {
      expect(screen.getByTestId('stat-trades')).toBeInTheDocument()
    })

    expect(getTradePerformance).toHaveBeenCalledWith('HIRED-1', 90)

    // Change period selector to 30
    const select = screen.getByRole('combobox')
    fireEvent.change(select, { target: { value: '30' } })

    await waitFor(() => {
      expect(getTradePerformance).toHaveBeenCalledWith('HIRED-1', 30)
    })
  })

  it('T4: zero trades shows empty state text', async () => {
    const { getTradePerformance, getRecommendations } = await import('../services/tradingSetup.service')
    vi.mocked(getTradePerformance).mockResolvedValue(makePerf({ trades_count: 0 }))
    vi.mocked(getRecommendations).mockResolvedValue(makeRec({ confidence: 0.5 }))

    renderPanel()

    await waitFor(() => {
      expect(screen.getByText(/No performance data yet/)).toBeInTheDocument()
    })
  })

  it('shows error state when API fails', async () => {
    const { getTradePerformance, getRecommendations } = await import('../services/tradingSetup.service')
    vi.mocked(getTradePerformance).mockRejectedValue(new Error('network'))
    vi.mocked(getRecommendations).mockRejectedValue(new Error('network'))

    renderPanel()

    await waitFor(() => {
      expect(screen.getByText('Failed to load trading performance.')).toBeInTheDocument()
    })
  })
})
