import { useEffect, useState } from 'react'
import { Badge, Card, Select } from '@fluentui/react-components'
import { LoadingIndicator, FeedbackMessage } from './FeedbackIndicators'
import {
  getTradePerformance,
  getRecommendations,
  type TradePerformanceSummary,
  type TradeRecommendation,
} from '../services/tradingSetup.service'

const PERIODS = [
  { label: '30 days', value: 30 },
  { label: '90 days', value: 90 },
  { label: '180 days', value: 180 },
]

interface Props {
  hiredInstanceId: string
}

export function TradingDashboardPanel({ hiredInstanceId }: Props) {
  const [perf, setPerf] = useState<TradePerformanceSummary | null>(null)
  const [rec, setRec] = useState<TradeRecommendation | null>(null)
  const [period, setPeriod] = useState(90)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    setLoading(true)
    setError(null)
    Promise.all([getTradePerformance(hiredInstanceId, period), getRecommendations(hiredInstanceId)])
      .then(([p, r]) => {
        setPerf(p)
        setRec(r)
      })
      .catch(() => setError('Failed to load trading performance.'))
      .finally(() => setLoading(false))
  }, [hiredInstanceId, period])

  if (loading) return <LoadingIndicator message="Loading performance…" />
  if (error) return <FeedbackMessage intent="error" message={error} />

  const pnlColour = (perf?.pnl_pct_avg ?? 0) >= 0 ? '#10b981' : '#ef4444'

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }} data-testid="trading-dashboard">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span style={{ color: '#f4f4f5', fontWeight: 600 }}>Trading Performance</span>
        <Select
          value={String(period)}
          onChange={(_, d) => setPeriod(Number(d.value))}
          style={{ minWidth: 120 }}
        >
          {PERIODS.map((p) => (
            <option key={p.value} value={p.value}>
              {p.label}
            </option>
          ))}
        </Select>
      </div>

      {/* Stat cards */}
      <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
        {[
          {
            label: 'Total Trades',
            value: String(perf?.trades_count ?? 0),
            colour: '#f4f4f5',
            testId: 'stat-trades',
          },
          {
            label: 'Avg P&L',
            value: `${(perf?.pnl_pct_avg ?? 0).toFixed(1)}%`,
            colour: pnlColour,
            testId: 'stat-pnl',
          },
          {
            label: 'Win Rate',
            value: `${((perf?.win_rate ?? 0) * 100).toFixed(0)}%`,
            colour: '#00f2fe',
            testId: 'stat-winrate',
          },
        ].map((stat) => (
          <Card
            key={stat.label}
            style={{
              background: '#18181b',
              border: '1px solid #27272a',
              borderRadius: 12,
              padding: '16px 24px',
              flex: 1,
              minWidth: 120,
              textAlign: 'center',
            }}
          >
            <div
              style={{ fontSize: 24, fontWeight: 700, color: stat.colour }}
              data-testid={stat.testId}
            >
              {stat.value}
            </div>
            <div style={{ fontSize: 12, color: '#71717a', marginTop: 4 }}>{stat.label}</div>
          </Card>
        ))}
      </div>

      {/* RSI recommendations */}
      {rec && rec.confidence >= 0.7 && (
        <Card
          style={{
            background: '#18181b',
            border: '1px solid #667eea55',
            borderRadius: 12,
            padding: 16,
          }}
        >
          <Badge appearance="tint" color="informative" size="small" style={{ marginBottom: 8 }}>
            RSI Recommendation (confidence: {(rec.confidence * 100).toFixed(0)}%)
          </Badge>
          <p
            style={{ color: '#f4f4f5', fontSize: 13, margin: '4px 0' }}
            data-testid="rec-text"
          >
            Suggested: Buy when RSI &lt;{' '}
            <strong>{rec.suggested_rsi_buy_threshold}</strong>, Sell when RSI &gt;{' '}
            <strong>{rec.suggested_rsi_sell_threshold}</strong>
          </p>
          <p style={{ color: '#71717a', fontSize: 12, margin: '4px 0' }}>{rec.rationale}</p>
        </Card>
      )}

      {perf?.trades_count === 0 && (
        <p style={{ color: '#71717a', textAlign: 'center', padding: 32 }}>
          No performance data yet — your agent will appear here after its first trade.
        </p>
      )}
    </div>
  )
}
