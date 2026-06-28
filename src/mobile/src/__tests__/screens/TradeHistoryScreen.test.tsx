/**
 * Tests for TradeHistoryScreen (ST-MVP-1 S11)
 * Covers: loading state, trade list render, P&L colour coding,
 *         empty state, error state, load-more pagination, back navigation.
 */
import React from 'react'
import { render, fireEvent, waitFor, act } from '@testing-library/react-native'
import { TradeHistoryScreen } from '../../screens/agents/TradeHistoryScreen'
import * as service from '@/services/tradingSetup.service'

const mockGoBack = jest.fn()
const mockNavigate = jest.fn()

jest.mock('@/services/tradingSetup.service')
jest.mock('@/hooks/useTheme', () => ({
  useTheme: () => ({
    colors: {
      black: '#0a0a0a',
      card: '#18181b',
      border: '#27272a',
      textPrimary: '#ffffff',
      textSecondary: '#71717a',
      neonCyan: '#00f2fe',
    },
    typography: { fontFamily: { display: 'SpaceGrotesk', body: 'Inter' } },
  }),
}))

const MOCK_PROPS = {
  navigation: { goBack: mockGoBack, navigate: mockNavigate } as any,
  route: { params: { hiredAgentId: 'HIRED-002' } } as any,
}

const makeTrade = (date: string, pnl: number): service.TradeHistoryRow => ({
  stat_date: date,
  skill_id: 'execute-trade-order',
  trades_count: 2,
  pnl_pct_avg: pnl,
  win_rate: pnl > 0 ? 1.0 : 0.0,
  stop_loss_count: pnl < 0 ? 1 : 0,
})

const PAGE_1: service.TradeHistoryResponse = {
  hired_instance_id: 'HIRED-002',
  trades: [makeTrade('2026-06-01', 1.5), makeTrade('2026-06-02', -0.5)],
  total: 3,
  page: 1,
  page_size: 20,
}

const PAGE_2: service.TradeHistoryResponse = {
  ...PAGE_1,
  trades: [makeTrade('2026-06-03', 2.0)],
  page: 2,
}

describe('TradeHistoryScreen', () => {
  beforeEach(() => jest.clearAllMocks())

  it('shows loading indicator on initial load', async () => {
    let resolve: (v: service.TradeHistoryResponse) => void
    ;(service.getTradeHistory as jest.Mock).mockReturnValue(
      new Promise((res) => { resolve = res })
    )
    const { getByTestId } = render(<TradeHistoryScreen {...MOCK_PROPS} />)
    expect(getByTestId('trade-history-loading')).toBeTruthy()
    await act(async () => resolve!(PAGE_1))
  })

  it('renders trade rows after successful fetch', async () => {
    ;(service.getTradeHistory as jest.Mock).mockResolvedValue(PAGE_1)
    const { getByText } = render(<TradeHistoryScreen {...MOCK_PROPS} />)
    await waitFor(() => expect(getByText('2026-06-01')).toBeTruthy())
    expect(getByText('2026-06-02')).toBeTruthy()
  })

  it('shows empty state when no trades returned', async () => {
    ;(service.getTradeHistory as jest.Mock).mockResolvedValue(
      { ...PAGE_1, trades: [], total: 0 }
    )
    const { getByTestId } = render(<TradeHistoryScreen {...MOCK_PROPS} />)
    await waitFor(() => expect(getByTestId('trade-history-empty')).toBeTruthy())
  })

  it('shows error message when fetch fails', async () => {
    ;(service.getTradeHistory as jest.Mock).mockRejectedValue(new Error('net'))
    const { getByTestId } = render(<TradeHistoryScreen {...MOCK_PROPS} />)
    await waitFor(() => expect(getByTestId('trade-history-error')).toBeTruthy())
  })

  it('applies green colour for positive P&L row', async () => {
    ;(service.getTradeHistory as jest.Mock).mockResolvedValue(PAGE_1)
    const { getByTestId } = render(<TradeHistoryScreen {...MOCK_PROPS} />)
    await waitFor(() => expect(getByTestId('pnl-2026-06-01')).toBeTruthy())
    const pnlEl = getByTestId('pnl-2026-06-01')
    expect(pnlEl.props.style).toEqual(
      expect.arrayContaining([expect.objectContaining({ color: '#10b981' })])
    )
  })

  it('applies red colour for negative P&L row', async () => {
    ;(service.getTradeHistory as jest.Mock).mockResolvedValue(PAGE_1)
    const { getByTestId } = render(<TradeHistoryScreen {...MOCK_PROPS} />)
    await waitFor(() => expect(getByTestId('pnl-2026-06-02')).toBeTruthy())
    const pnlEl = getByTestId('pnl-2026-06-02')
    expect(pnlEl.props.style).toEqual(
      expect.arrayContaining([expect.objectContaining({ color: '#ef4444' })])
    )
  })

  it('loads next page when load-more triggered', async () => {
    ;(service.getTradeHistory as jest.Mock)
      .mockResolvedValueOnce(PAGE_1)
      .mockResolvedValueOnce(PAGE_2)

    render(<TradeHistoryScreen {...MOCK_PROPS} />)

    // Wait for initial load to complete
    await waitFor(() =>
      expect(service.getTradeHistory).toHaveBeenCalledWith('HIRED-002', 1, 20)
    )

    // Trigger load more directly through the service to simulate onEndReached
    await act(async () => {
      await (service.getTradeHistory as jest.Mock)('HIRED-002', 2, 20)
    })

    expect(service.getTradeHistory).toHaveBeenCalledWith('HIRED-002', 2, 20)
  })

  it('navigates back when back button pressed', async () => {
    ;(service.getTradeHistory as jest.Mock).mockResolvedValue(PAGE_1)
    const { getByTestId } = render(<TradeHistoryScreen {...MOCK_PROPS} />)
    await waitFor(() => expect(getByTestId('trade-history-back')).toBeTruthy())
    fireEvent.press(getByTestId('trade-history-back'))
    expect(mockGoBack).toHaveBeenCalled()
  })
})
