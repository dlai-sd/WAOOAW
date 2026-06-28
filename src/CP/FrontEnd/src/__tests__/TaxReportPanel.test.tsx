import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { FluentProvider } from '@fluentui/react-components'
import { waooawLightTheme } from '../theme'
import { TaxReportPanel } from '../components/TaxReportPanel'
import type { TaxReportResponse } from '../services/tradingSetup.service'

vi.mock('../services/tradingSetup.service', () => ({
  getTaxReport: vi.fn(),
}))

const makeReport = (overrides: Partial<TaxReportResponse> = {}): TaxReportResponse => ({
  hired_instance_id: 'HIRED-1',
  period: 'monthly',
  year: 2026,
  total_trades: 15,
  total_pnl_pct: 3.2,
  profitable_trades: 10,
  loss_trades: 5,
  stop_loss_exits: 3,
  trades: [
    {
      date: '2026-06-01',
      skill_id: 'trading.delta.v1',
      trades_count: 5,
      pnl_pct: 1.1,
      win_rate: 0.6,
      stop_loss_count: 1,
    },
  ],
  ...overrides,
})

const renderPanel = (hiredInstanceId = 'HIRED-1') =>
  render(
    <FluentProvider theme={waooawLightTheme}>
      <TaxReportPanel hiredInstanceId={hiredInstanceId} />
    </FluentProvider>
  )

describe('TaxReportPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  it('T1: month selector visible for monthly period, hidden for quarterly', async () => {
    renderPanel()

    // Default period is monthly — month selector should be visible
    await waitFor(() => {
      expect(screen.getByTestId('month-selector')).toBeInTheDocument()
    })
    expect(screen.queryByTestId('quarter-selector')).not.toBeInTheDocument()
  })

  it('T2: quarter selector visible for quarterly period', async () => {
    renderPanel()

    // Switch to quarterly
    const periodSelect = screen.getByTestId('period-type-selector')
    fireEvent.change(periodSelect, { target: { value: 'quarterly' } })

    await waitFor(() => {
      expect(screen.getByTestId('quarter-selector')).toBeInTheDocument()
    })
    expect(screen.queryByTestId('month-selector')).not.toBeInTheDocument()
  })

  it('T3: summary card shows correct total_trades after generate', async () => {
    const { getTaxReport } = await import('../services/tradingSetup.service')
    vi.mocked(getTaxReport).mockResolvedValue(makeReport())

    renderPanel()

    const generateBtn = screen.getByTestId('generate-report-btn')
    fireEvent.click(generateBtn)

    await waitFor(() => {
      expect(screen.getByTestId('summary-total-trades')).toBeInTheDocument()
    })
    expect(screen.getByTestId('summary-total-trades').textContent).toBe('15')
  })

  it('T4: Download CSV button triggers anchor click', async () => {
    const { getTaxReport } = await import('../services/tradingSetup.service')
    vi.mocked(getTaxReport).mockResolvedValue(makeReport())

    // Mock DOM methods used in CSV download
    const mockClick = vi.fn()
    const mockCreateObjectURL = vi.fn().mockReturnValue('blob:test-url')
    const mockRevokeObjectURL = vi.fn()
    const mockAppendChild = vi.fn()
    const mockRemoveChild = vi.fn()

    const originalCreateObjectURL = URL.createObjectURL
    const originalRevokeObjectURL = URL.revokeObjectURL
    URL.createObjectURL = mockCreateObjectURL
    URL.revokeObjectURL = mockRevokeObjectURL

    const origCreateElement = document.createElement.bind(document)
    vi.spyOn(document, 'createElement').mockImplementation((tag) => {
      if (tag === 'a') {
        const el = origCreateElement('a')
        el.click = mockClick
        return el
      }
      return origCreateElement(tag)
    })
    vi.spyOn(document.body, 'appendChild').mockImplementation(mockAppendChild)
    vi.spyOn(document.body, 'removeChild').mockImplementation(mockRemoveChild)

    renderPanel()

    fireEvent.click(screen.getByTestId('generate-report-btn'))

    await waitFor(() => {
      expect(screen.getByTestId('download-csv-btn')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByTestId('download-csv-btn'))

    expect(mockCreateObjectURL).toHaveBeenCalled()
    expect(mockClick).toHaveBeenCalled()

    // Restore
    URL.createObjectURL = originalCreateObjectURL
    URL.revokeObjectURL = originalRevokeObjectURL
    vi.restoreAllMocks()
  })

  it('shows empty report message when total_trades is 0', async () => {
    const { getTaxReport } = await import('../services/tradingSetup.service')
    vi.mocked(getTaxReport).mockResolvedValue(makeReport({ total_trades: 0, trades: [] }))

    renderPanel()
    fireEvent.click(screen.getByTestId('generate-report-btn'))

    await waitFor(() => {
      expect(screen.getByText('No trades recorded for this period.')).toBeInTheDocument()
    })
  })

  it('shows error when API fails', async () => {
    const { getTaxReport } = await import('../services/tradingSetup.service')
    vi.mocked(getTaxReport).mockRejectedValue(new Error('network'))

    renderPanel()
    fireEvent.click(screen.getByTestId('generate-report-btn'))

    await waitFor(() => {
      expect(screen.getByText('Failed to load tax report.')).toBeInTheDocument()
    })
  })
})
