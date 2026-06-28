import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { FluentProvider } from '@fluentui/react-components'
import { waooawLightTheme } from '../theme'
import { TradeHistoryPanel } from '../components/TradeHistoryPanel'
import type { TradeHistoryRow } from '../services/tradingSetup.service'

vi.mock('../services/tradingSetup.service', () => ({
  getTradeHistory: vi.fn(),
}))

const makeRow = (i: number, pnl: number = 1.5): TradeHistoryRow => ({
  stat_date: `2026-06-${String(i).padStart(2, '0')}`,
  skill_id: 'trading.delta.v1',
  trades_count: 3 + i,
  pnl_pct_avg: pnl,
  win_rate: 0.6,
  stop_loss_count: 1,
})

const makeResponse = (rows: TradeHistoryRow[], total = rows.length, page = 1, pageSize = 20) => ({
  hired_instance_id: 'HIRED-1',
  trades: rows,
  total,
  page,
  page_size: pageSize,
})

const renderPanel = (hiredInstanceId = 'HIRED-1') =>
  render(
    <FluentProvider theme={waooawLightTheme}>
      <TradeHistoryPanel hiredInstanceId={hiredInstanceId} />
    </FluentProvider>
  )

describe('TradeHistoryPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('T1: rows render in table with correct column data', async () => {
    const { getTradeHistory } = await import('../services/tradingSetup.service')
    const rows = Array.from({ length: 5 }, (_, i) => makeRow(i + 1))
    vi.mocked(getTradeHistory).mockResolvedValue(makeResponse(rows, 5))

    renderPanel()

    await waitFor(() => {
      expect(screen.getByTestId('trade-history-panel')).toBeInTheDocument()
    })
    expect(screen.getByText('2026-06-01')).toBeInTheDocument()
    expect(screen.getByText('2026-06-05')).toBeInTheDocument()
    // check column headers
    expect(screen.getByText('Date')).toBeInTheDocument()
    expect(screen.getByText('Trades')).toBeInTheDocument()
    expect(screen.getByText('Avg P&L%')).toBeInTheDocument()
  })

  it('T2: positive P&L shown in green; negative in red', async () => {
    const { getTradeHistory } = await import('../services/tradingSetup.service')
    const rows = [makeRow(1, 2.5), makeRow(2, -1.3)]
    vi.mocked(getTradeHistory).mockResolvedValue(makeResponse(rows, 2))

    renderPanel()

    await waitFor(() => {
      expect(screen.getByText('2.5%')).toBeInTheDocument()
    })

    const greenCell = screen.getByText('2.5%')
    expect(greenCell).toHaveStyle({ color: '#10b981' })

    const redCell = screen.getByText('-1.3%')
    expect(redCell).toHaveStyle({ color: '#ef4444' })
  })

  it('T3: Next → button disabled on last page', async () => {
    const { getTradeHistory } = await import('../services/tradingSetup.service')
    const rows = Array.from({ length: 5 }, (_, i) => makeRow(i + 1))
    // total=5, pageSize=20 => 1 page, both prev and next disabled
    vi.mocked(getTradeHistory).mockResolvedValue(makeResponse(rows, 5, 1, 20))

    renderPanel()

    await waitFor(() => {
      expect(screen.getByTestId('trade-history-panel')).toBeInTheDocument()
    })

    // With total=5 and pageSize=20, pagination is hidden (total <= pageSize)
    expect(screen.queryByText('Next →')).not.toBeInTheDocument()
  })

  it('shows Next button disabled when on last page with multiple pages', async () => {
    const { getTradeHistory } = await import('../services/tradingSetup.service')
    const rows = Array.from({ length: 10 }, (_, i) => makeRow(i + 1))
    // total=25, pageSize=10, page=3 (last page: ceil(25/10)=3)
    vi.mocked(getTradeHistory).mockResolvedValue(makeResponse(rows, 25, 3, 10))

    renderPanel()

    await waitFor(() => {
      expect(screen.getByText('Page 3 of 3')).toBeInTheDocument()
    })

    const nextBtn = screen.getByText('Next →')
    expect(nextBtn.closest('button')).toBeDisabled()
  })

  it('T4: empty state shown when trades.length === 0', async () => {
    const { getTradeHistory } = await import('../services/tradingSetup.service')
    vi.mocked(getTradeHistory).mockResolvedValue(makeResponse([], 0))

    renderPanel()

    await waitFor(() => {
      expect(screen.getByText('No trade history yet.')).toBeInTheDocument()
    })
  })

  it('shows error state when API fails', async () => {
    const { getTradeHistory } = await import('../services/tradingSetup.service')
    vi.mocked(getTradeHistory).mockRejectedValue(new Error('network'))

    renderPanel()

    await waitFor(() => {
      expect(screen.getByText('Failed to load trade history.')).toBeInTheDocument()
    })
  })

  it('Prev button fetches previous page', async () => {
    const { getTradeHistory } = await import('../services/tradingSetup.service')
    const rows = Array.from({ length: 10 }, (_, i) => makeRow(i + 1))
    // Start on page 2 of 3
    vi.mocked(getTradeHistory).mockResolvedValue(makeResponse(rows, 25, 2, 10))

    renderPanel()

    await waitFor(() => {
      expect(screen.getByText('Page 2 of 3')).toBeInTheDocument()
    })

    vi.mocked(getTradeHistory).mockResolvedValue(makeResponse(rows, 25, 1, 10))
    fireEvent.click(screen.getByText('← Prev'))

    await waitFor(() => {
      expect(getTradeHistory).toHaveBeenCalledWith('HIRED-1', 1, 10)
    })
  })
})
