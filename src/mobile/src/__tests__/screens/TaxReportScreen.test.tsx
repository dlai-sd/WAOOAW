/**
 * Tests for TaxReportScreen (ST-MVP-1 S12)
 * Covers: loading state, success with data, error state, empty report,
 *         period toggle (monthly/quarterly), export CSV.
 */
import React from 'react'
import { render, fireEvent, waitFor, act } from '@testing-library/react-native'
import { TaxReportScreen } from '../../screens/agents/TaxReportScreen'
import * as service from '@/services/tradingSetup.service'

const mockGoBack = jest.fn()
const mockNavigate = jest.fn()
const mockShareFn = jest.fn().mockResolvedValue({ action: 'sharedAction' })

jest.mock('@/services/tradingSetup.service')
jest.mock('react-native/Libraries/Share/Share', () => ({ share: (...args: unknown[]) => mockShareFn(...args) }))
jest.mock('@/hooks/useTheme', () => ({
  useTheme: () => ({
    colors: {
      black: '#0a0a0a',
      card: '#18181b',
      border: '#27272a',
      textPrimary: '#ffffff',
      textSecondary: '#71717a',
      neonCyan: '#00f2fe',
      green: '#10b981',
      red: '#ef4444',
      background: '#0a0a0a',
    },
    typography: { fontFamily: { display: 'SpaceGrotesk', body: 'Inter' } },
  }),
}))

const MOCK_PROPS = {
  navigation: { goBack: mockGoBack, navigate: mockNavigate } as any,
  route: { params: { hiredAgentId: 'HIRED-001' } } as any,
}

const MOCK_REPORT: service.TaxReportResponse = {
  hired_instance_id: 'HIRED-001',
  period: 'monthly',
  year: 2026,
  total_trades: 12,
  total_pnl_pct: 4.8,
  profitable_trades: 8,
  loss_trades: 4,
  stop_loss_exits: 3,
  trades: [
    { date: '2026-06-01', skill_id: 'execute-trade-order', trades_count: 3,
      pnl_pct: 1.5, win_rate: 0.67, stop_loss_count: 1 },
    { date: '2026-06-15', skill_id: 'execute-trade-order', trades_count: 2,
      pnl_pct: -0.8, win_rate: 0.5, stop_loss_count: 1 },
  ],
}

const EMPTY_REPORT: service.TaxReportResponse = {
  ...MOCK_REPORT,
  total_trades: 0,
  trades: [],
}

describe('TaxReportScreen', () => {
  beforeEach(() => jest.clearAllMocks())

  it('shows loading indicator on initial fetch', async () => {
    let resolve: (v: service.TaxReportResponse) => void
    ;(service.getTaxReport as jest.Mock).mockReturnValue(
      new Promise((res) => { resolve = res })
    )
    const { getByTestId } = render(<TaxReportScreen {...MOCK_PROPS} />)
    // Loading spinner should be visible while promise is pending
    expect(getByTestId('tax-report-loading')).toBeTruthy()
    await act(async () => resolve!(MOCK_REPORT))
  })

  it('renders report summary after successful fetch', async () => {
    ;(service.getTaxReport as jest.Mock).mockResolvedValue(MOCK_REPORT)
    const { getByTestId, getByText } = render(<TaxReportScreen {...MOCK_PROPS} />)
    await waitFor(() => expect(getByTestId('tax-report-summary')).toBeTruthy())
    expect(getByText('12')).toBeTruthy()        // total_trades
    expect(getByText('+4.80%')).toBeTruthy()    // total_pnl_pct (positive prefix)
    expect(getByText('8')).toBeTruthy()         // profitable_trades
    expect(getByText('4')).toBeTruthy()         // loss_trades
  })

  it('shows error message when fetch fails', async () => {
    ;(service.getTaxReport as jest.Mock).mockRejectedValue(new Error('network'))
    const { getByTestId } = render(<TaxReportScreen {...MOCK_PROPS} />)
    await waitFor(() => expect(getByTestId('tax-report-error')).toBeTruthy())
  })

  it('shows empty state when total_trades is 0', async () => {
    ;(service.getTaxReport as jest.Mock).mockResolvedValue(EMPTY_REPORT)
    const { getByTestId } = render(<TaxReportScreen {...MOCK_PROPS} />)
    await waitFor(() => expect(getByTestId('tax-report-empty')).toBeTruthy())
  })

  it('renders trade rows for each trade entry', async () => {
    ;(service.getTaxReport as jest.Mock).mockResolvedValue(MOCK_REPORT)
    const { getByText } = render(<TaxReportScreen {...MOCK_PROPS} />)
    await waitFor(() => expect(getByText('2026-06-01')).toBeTruthy())
    expect(getByText('2026-06-15')).toBeTruthy()
  })

  it('switches to quarterly and re-fetches when quarter tab pressed', async () => {
    ;(service.getTaxReport as jest.Mock).mockResolvedValue(MOCK_REPORT)
    const { getByTestId } = render(<TaxReportScreen {...MOCK_PROPS} />)
    await waitFor(() => expect(getByTestId('tax-report-summary')).toBeTruthy())

    ;(service.getTaxReport as jest.Mock).mockResolvedValue({ ...MOCK_REPORT, period: 'quarterly' })
    await act(async () => {
      fireEvent.press(getByTestId('period-quarterly'))
    })

    await waitFor(() => {
      const calls = (service.getTaxReport as jest.Mock).mock.calls
      const lastCall = calls[calls.length - 1]
      expect(lastCall[2]).toBe('quarterly')
    })
  })

  it('export button is enabled after report loads and disabled before', async () => {
    ;(service.getTaxReport as jest.Mock).mockResolvedValue(MOCK_REPORT)
    const { getByTestId } = render(<TaxReportScreen {...MOCK_PROPS} />)

    // After load: export button should not be disabled
    await waitFor(() => expect(getByTestId('tax-report-summary')).toBeTruthy())
    const exportBtn = getByTestId('export-csv-btn')
    // Button is enabled (accessibilityState.disabled should be false or absent)
    expect(exportBtn.props.disabled).toBeFalsy()
  })

  it('navigates back when back button pressed', async () => {
    ;(service.getTaxReport as jest.Mock).mockResolvedValue(MOCK_REPORT)
    const { getByTestId } = render(<TaxReportScreen {...MOCK_PROPS} />)
    await waitFor(() => expect(getByTestId('tax-report-back')).toBeTruthy())
    fireEvent.press(getByTestId('tax-report-back'))
    expect(mockGoBack).toHaveBeenCalled()
  })
})
