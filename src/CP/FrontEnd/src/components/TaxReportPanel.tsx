import { useState } from 'react'
import { Badge, Button, Card, Select, Spinner } from '@fluentui/react-components'
import { FeedbackMessage } from './FeedbackIndicators'
import { getTaxReport, type TaxReportResponse } from '../services/tradingSetup.service'

const YEARS = [2024, 2025, 2026, 2027]
const MONTHS = [
  { value: 1, label: 'January' },
  { value: 2, label: 'February' },
  { value: 3, label: 'March' },
  { value: 4, label: 'April' },
  { value: 5, label: 'May' },
  { value: 6, label: 'June' },
  { value: 7, label: 'July' },
  { value: 8, label: 'August' },
  { value: 9, label: 'September' },
  { value: 10, label: 'October' },
  { value: 11, label: 'November' },
  { value: 12, label: 'December' },
]
const QUARTERS = ['Q1', 'Q2', 'Q3', 'Q4']

function downloadCsv(report: TaxReportResponse) {
  const header = 'date,skill_id,trades,pnl_pct,win_rate,stop_losses'
  const rows = report.trades.map(
    (t) =>
      `${t.date},${t.skill_id},${t.trades_count},${t.pnl_pct},${t.win_rate},${t.stop_loss_count}`
  )
  const csv = [header, ...rows].join('\n')
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `waooaw-trade-report-${report.year}-${report.period}.csv`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

interface Props {
  hiredInstanceId: string
}

export function TaxReportPanel({ hiredInstanceId }: Props) {
  const [periodType, setPeriodType] = useState<'monthly' | 'quarterly'>('monthly')
  const [year, setYear] = useState(new Date().getFullYear())
  const [month, setMonth] = useState(new Date().getMonth() + 1)
  const [quarter, setQuarter] = useState('Q1')
  const [report, setReport] = useState<TaxReportResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleGenerate = async () => {
    setLoading(true)
    setError(null)
    setReport(null)
    try {
      const result = await getTaxReport(
        hiredInstanceId,
        year,
        periodType,
        periodType === 'monthly' ? month : undefined,
        periodType === 'quarterly' ? quarter : undefined
      )
      setReport(result)
    } catch {
      setError('Failed to load tax report.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }} data-testid="tax-report-panel">
      {/* Selectors */}
      <Card style={{ background: '#18181b', border: '1px solid #27272a', borderRadius: 12, padding: 16 }}>
        <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', alignItems: 'flex-end' }}>
          {/* Period type */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            <span style={{ color: '#71717a', fontSize: 12 }}>Period type</span>
            <Select
              value={periodType}
              onChange={(_, d) => setPeriodType(d.value as 'monthly' | 'quarterly')}
              data-testid="period-type-selector"
            >
              <option value="monthly">Monthly</option>
              <option value="quarterly">Quarterly</option>
            </Select>
          </div>

          {/* Year */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            <span style={{ color: '#71717a', fontSize: 12 }}>Year</span>
            <Select
              value={String(year)}
              onChange={(_, d) => setYear(Number(d.value))}
              data-testid="year-selector"
            >
              {YEARS.map((y) => (
                <option key={y} value={y}>
                  {y}
                </option>
              ))}
            </Select>
          </div>

          {/* Month selector (monthly only) */}
          {periodType === 'monthly' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
              <span style={{ color: '#71717a', fontSize: 12 }}>Month</span>
              <Select
                value={String(month)}
                onChange={(_, d) => setMonth(Number(d.value))}
                data-testid="month-selector"
              >
                {MONTHS.map((m) => (
                  <option key={m.value} value={m.value}>
                    {m.label}
                  </option>
                ))}
              </Select>
            </div>
          )}

          {/* Quarter selector (quarterly only) */}
          {periodType === 'quarterly' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
              <span style={{ color: '#71717a', fontSize: 12 }}>Quarter</span>
              <Select
                value={quarter}
                onChange={(_, d) => setQuarter(d.value)}
                data-testid="quarter-selector"
              >
                {QUARTERS.map((q) => (
                  <option key={q} value={q}>
                    {q}
                  </option>
                ))}
              </Select>
            </div>
          )}

          <Button
            appearance="primary"
            onClick={handleGenerate}
            disabled={loading}
            data-testid="generate-report-btn"
          >
            {loading ? <Spinner size="tiny" /> : 'Generate Report'}
          </Button>
        </div>
      </Card>

      {/* Error */}
      {error && <FeedbackMessage intent="error" message={error} />}

      {/* Report summary */}
      {report && (
        <>
          {report.total_trades === 0 ? (
            <p style={{ color: '#71717a', textAlign: 'center', padding: 32 }}>
              No trades recorded for this period.
            </p>
          ) : (
            <>
              {/* Summary cards */}
              <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
                {[
                  {
                    label: 'Total Trades',
                    value: String(report.total_trades),
                    colour: '#f4f4f5',
                    testId: 'summary-total-trades',
                  },
                  {
                    label: 'Total P&L%',
                    value: `${report.total_pnl_pct.toFixed(1)}%`,
                    colour: report.total_pnl_pct >= 0 ? '#10b981' : '#ef4444',
                    testId: 'summary-pnl',
                  },
                  {
                    label: 'Profitable',
                    value: String(report.profitable_trades),
                    colour: '#10b981',
                    testId: 'summary-profitable',
                  },
                  {
                    label: 'Loss Trades',
                    value: String(report.loss_trades),
                    colour: '#ef4444',
                    testId: 'summary-loss',
                  },
                  {
                    label: 'Stop-Loss Exits',
                    value: String(report.stop_loss_exits),
                    colour: '#f59e0b',
                    testId: 'summary-stoploss',
                  },
                ].map((stat) => (
                  <Card
                    key={stat.label}
                    style={{
                      background: '#18181b',
                      border: '1px solid #27272a',
                      borderRadius: 12,
                      padding: '16px 20px',
                      flex: 1,
                      minWidth: 100,
                      textAlign: 'center',
                    }}
                  >
                    <div
                      style={{ fontSize: 22, fontWeight: 700, color: stat.colour }}
                      data-testid={stat.testId}
                    >
                      {stat.value}
                    </div>
                    <div style={{ fontSize: 11, color: '#71717a', marginTop: 4 }}>{stat.label}</div>
                  </Card>
                ))}
              </div>

              {/* Period badge */}
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <Badge appearance="tint" color="informative" size="small">
                  {report.year} · {periodType === 'monthly'
                    ? MONTHS.find((m) => m.value === month)?.label ?? `Month ${month}`
                    : quarter}
                </Badge>
                <Button
                  appearance="subtle"
                  size="small"
                  onClick={() => downloadCsv(report)}
                  data-testid="download-csv-btn"
                  style={{ color: '#00f2fe', borderColor: '#00f2fe55' }}
                >
                  ⬇ Download CSV
                </Button>
              </div>
            </>
          )}
        </>
      )}
    </div>
  )
}
