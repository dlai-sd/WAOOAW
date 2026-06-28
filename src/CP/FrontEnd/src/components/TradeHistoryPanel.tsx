import { useEffect, useState } from 'react'
import { Button, Card, Select, Spinner } from '@fluentui/react-components'
import { FeedbackMessage } from './FeedbackIndicators'
import { getTradeHistory, type TradeHistoryRow } from '../services/tradingSetup.service'

interface Props {
  hiredInstanceId: string
}

export function TradeHistoryPanel({ hiredInstanceId }: Props) {
  const [rows, setRows] = useState<TradeHistoryRow[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    setLoading(true)
    getTradeHistory(hiredInstanceId, page, pageSize)
      .then((resp) => {
        setRows(resp.trades)
        setTotal(resp.total)
      })
      .catch(() => setError('Failed to load trade history.'))
      .finally(() => setLoading(false))
  }, [hiredInstanceId, page, pageSize])

  const totalPages = Math.max(1, Math.ceil(total / pageSize))

  if (error) return <FeedbackMessage intent="error" message={error} />

  return (
    <div data-testid="trade-history-panel">
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: 12,
        }}
      >
        <span style={{ color: '#f4f4f5', fontWeight: 600 }}>Trade History</span>
        <Select
          value={String(pageSize)}
          onChange={(_, d) => {
            setPageSize(Number(d.value))
            setPage(1)
          }}
        >
          {[10, 20, 50].map((n) => (
            <option key={n} value={n}>
              {n} per page
            </option>
          ))}
        </Select>
      </div>
      {loading ? (
        <Spinner label="Loading…" />
      ) : rows.length === 0 ? (
        <p style={{ color: '#71717a', textAlign: 'center', padding: 32 }}>No trade history yet.</p>
      ) : (
        <Card
          style={{
            background: '#18181b',
            border: '1px solid #27272a',
            borderRadius: 12,
            overflow: 'hidden',
          }}
        >
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid #27272a' }}>
                {['Date', 'Trades', 'Avg P&L%', 'Win Rate', 'Stop-Losses'].map((h) => (
                  <th
                    key={h}
                    style={{
                      padding: '10px 16px',
                      textAlign: 'left',
                      color: '#71717a',
                      fontSize: 12,
                      fontWeight: 500,
                    }}
                  >
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((row, i) => (
                <tr key={i} style={{ borderBottom: '1px solid #27272a22' }}>
                  <td style={{ padding: '10px 16px', color: '#f4f4f5', fontSize: 13 }}>
                    {row.stat_date}
                  </td>
                  <td style={{ padding: '10px 16px', color: '#f4f4f5', fontSize: 13 }}>
                    {row.trades_count}
                  </td>
                  <td
                    style={{
                      padding: '10px 16px',
                      fontSize: 13,
                      color: row.pnl_pct_avg >= 0 ? '#10b981' : '#ef4444',
                      fontWeight: 600,
                    }}
                  >
                    {row.pnl_pct_avg.toFixed(1)}%
                  </td>
                  <td style={{ padding: '10px 16px', color: '#00f2fe', fontSize: 13 }}>
                    {(row.win_rate * 100).toFixed(0)}%
                  </td>
                  <td style={{ padding: '10px 16px', color: '#f4f4f5', fontSize: 13 }}>
                    {row.stop_loss_count}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}
      {total > pageSize && (
        <div
          style={{
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            gap: 16,
            marginTop: 12,
          }}
        >
          <Button
            appearance="subtle"
            disabled={page <= 1}
            onClick={() => setPage((p) => p - 1)}
          >
            ← Prev
          </Button>
          <span
            style={{ color: '#71717a', fontSize: 12 }}
            data-testid="page-indicator"
          >
            Page {page} of {totalPages}
          </span>
          <Button
            appearance="subtle"
            disabled={page >= totalPages}
            onClick={() => setPage((p) => p + 1)}
          >
            Next →
          </Button>
        </div>
      )}
    </div>
  )
}
