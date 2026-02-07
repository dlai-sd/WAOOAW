import { Card, Button } from '@fluentui/react-components'
import { useEffect, useMemo, useState } from 'react'
import {
  approveDraftPost,
  listCustomerDraftBatches,
  rejectDraftPost,
  scheduleDraftPost,
  type DraftBatch,
  type DraftPost
} from '../../services/marketingReview.service'
import { approveAndExecuteTrade, draftTradePlan } from '../../services/trading.service'

export default function Approvals() {
  const [batches, setBatches] = useState<DraftBatch[]>([])
  const [error, setError] = useState<string | null>(null)
  const [busyPostId, setBusyPostId] = useState<string | null>(null)
  const [scheduleTimes, setScheduleTimes] = useState<Record<string, string>>({})
  const [scheduleOffsetOverride, setScheduleOffsetOverride] = useState('')

  const [tradingError, setTradingError] = useState<string | null>(null)
  const [tradingBusy, setTradingBusy] = useState(false)
  const [tradeAgentId, setTradeAgentId] = useState('AGT-TRD-DELTA-001')
  const [exchangeAccountId, setExchangeAccountId] = useState('')
  const [coin, setCoin] = useState('BTC')
  const [units, setUnits] = useState('1')
  const [side, setSide] = useState<'long' | 'short'>('long')
  const [tradeAction, setTradeAction] = useState<'enter' | 'exit'>('enter')
  const [orderType, setOrderType] = useState<'market' | 'limit'>('market')
  const [limitPrice, setLimitPrice] = useState('')
  const [tradeResult, setTradeResult] = useState<any>(null)

  const pendingPosts = useMemo(() => {
    const posts: Array<{ batch: DraftBatch; post: DraftPost }> = []
    for (const b of batches) {
      for (const p of b.posts || []) {
        if (p.review_status === 'pending_review') posts.push({ batch: b, post: p })
      }
    }
    return posts
  }, [batches])

  const schedulablePosts = useMemo(() => {
    const posts: Array<{ batch: DraftBatch; post: DraftPost }> = []
    for (const b of batches) {
      for (const p of b.posts || []) {
        if (p.review_status === 'approved' && p.execution_status !== 'scheduled' && p.execution_status !== 'posted') {
          posts.push({ batch: b, post: p })
        }
      }
    }
    return posts
  }, [batches])

  const toIsoWithOffset = (localDateTime: string) => {
    // localDateTime is `YYYY-MM-DDTHH:mm` from <input type="datetime-local" />
    const override = scheduleOffsetOverride.trim()
    if (override) {
      const ok = /^[+-]\d{2}:\d{2}$/.test(override)
      if (ok) return `${localDateTime}:00${override}`
    }

    const d = new Date(localDateTime)
    const minutes = -d.getTimezoneOffset()
    const sign = minutes >= 0 ? '+' : '-'
    const abs = Math.abs(minutes)
    const hh = String(Math.floor(abs / 60)).padStart(2, '0')
    const mm = String(abs % 60).padStart(2, '0')
    return `${localDateTime}:00${sign}${hh}:${mm}`
  }

  const load = async () => {
    setError(null)
    try {
      const rows = await listCustomerDraftBatches()
      setBatches(rows)
    } catch (e: any) {
      setError(e?.message || 'Failed to load draft batches')
    }
  }

  useEffect(() => {
    load()
  }, [])

  const onApprove = async (postId: string) => {
    setBusyPostId(postId)
    setError(null)
    try {
      await approveDraftPost(postId)
      await load()
    } catch (e: any) {
      setError(e?.message || 'Approval failed')
    } finally {
      setBusyPostId(null)
    }
  }

  const onReject = async (postId: string) => {
    setBusyPostId(postId)
    setError(null)
    try {
      await rejectDraftPost(postId)
      await load()
    } catch (e: any) {
      setError(e?.message || 'Rejection failed')
    } finally {
      setBusyPostId(null)
    }
  }

  const onSchedule = async (postId: string) => {
    setBusyPostId(postId)
    setError(null)
    try {
      const localValue = scheduleTimes[postId]
      if (!localValue) {
        setError('Please choose a date/time to schedule')
        return
      }
      await scheduleDraftPost(postId, toIsoWithOffset(localValue))
      await load()
    } catch (e: any) {
      setError(e?.message || 'Scheduling failed')
    } finally {
      setBusyPostId(null)
    }
  }

  const onDraftTrade = async () => {
    setTradingBusy(true)
    setTradingError(null)
    try {
      const payload: any = {
        agent_id: tradeAgentId,
        exchange_account_id: exchangeAccountId,
        coin: coin.trim().toUpperCase(),
        units: Number(units || '0'),
        side,
        action: tradeAction,
        market: orderType === 'market'
      }
      if (orderType === 'limit' && limitPrice.trim()) payload.limit_price = Number(limitPrice)

      const res = await draftTradePlan(payload)
      setTradeResult(res)
    } catch (e: any) {
      setTradingError(e?.message || 'Failed to generate trade draft')
    } finally {
      setTradingBusy(false)
    }
  }

  const onApproveExecuteTrade = async () => {
    setTradingBusy(true)
    setTradingError(null)
    try {
      const intent_action = tradeAction === 'enter' ? 'place_order' : 'close_position'
      const payload: any = {
        agent_id: tradeAgentId,
        intent_action,
        exchange_account_id: exchangeAccountId,
        coin: coin.trim().toUpperCase(),
        units: Number(units || '0'),
        side,
        action: tradeAction,
        market: orderType === 'market'
      }
      if (orderType === 'limit' && limitPrice.trim()) payload.limit_price = Number(limitPrice)

      const res = await approveAndExecuteTrade(payload)
      setTradeResult(res)
    } catch (e: any) {
      setTradingError(e?.message || 'Trade execution failed')
    } finally {
      setTradingBusy(false)
    }
  }

  return (
    <div className="approvals-page">
      <div className="page-header">
        <h1>Pending Approvals ({pendingPosts.length})</h1>
        <div className="filter-controls">
          <select className="filter-select">
            <option>All</option>
            <option>Urgent</option>
            <option>Low Risk</option>
          </select>
          <select className="sort-select">
            <option>Newest First</option>
            <option>Oldest First</option>
            <option>By Risk</option>
          </select>
        </div>
      </div>

      {error && <div style={{ color: '#ef4444', marginBottom: '1rem' }}>{error}</div>}

      <div className="approvals-list">
        {pendingPosts.map(({ batch, post }) => (
          <Card key={post.post_id} className="approval-card">
            <div className="approval-header">
              <div className="approval-agent">Content Marketing Agent</div>
              <div className="approval-wait">Batch {batch.batch_id.slice(0, 8)}…</div>
            </div>

            <div className="approval-body">
              <h3>Action Requested:</h3>
              <p className="approval-action">Approve post for {post.channel.toUpperCase()}</p>

              <h4>Draft:</h4>
              <p>{post.text}</p>

              <div className="approval-meta">
                <span>Theme: <strong>{batch.theme}</strong></span>
                <span> | </span>
                <span>Brand: {batch.brand_name}</span>
              </div>
            </div>

            <div className="approval-actions">
              <Button
                appearance="primary"
                style={{ backgroundColor: '#10b981' }}
                onClick={() => onApprove(post.post_id)}
                disabled={busyPostId === post.post_id}
              >
                ✅ APPROVE
              </Button>
              <Button
                appearance="primary"
                style={{ backgroundColor: '#ef4444' }}
                onClick={() => onReject(post.post_id)}
                disabled={busyPostId === post.post_id}
              >
                ❌ REJECT
              </Button>
            </div>
          </Card>
        ))}
      </div>

      <div style={{ marginTop: '1.5rem' }}>
        <h2>Ready to Schedule ({schedulablePosts.length})</h2>
        <div style={{ marginTop: '0.5rem', opacity: 0.9 }}>
          <label style={{ display: 'block', marginBottom: '0.25rem' }}>Timezone offset override (optional)</label>
          <input
            value={scheduleOffsetOverride}
            onChange={(e) => setScheduleOffsetOverride(e.target.value)}
            placeholder={(() => {
              const minutes = -new Date().getTimezoneOffset()
              const sign = minutes >= 0 ? '+' : '-'
              const abs = Math.abs(minutes)
              const hh = String(Math.floor(abs / 60)).padStart(2, '0')
              const mm = String(abs % 60).padStart(2, '0')
              return `e.g., ${sign}${hh}:${mm}`
            })()}
          />
          <div style={{ marginTop: '0.25rem', opacity: 0.75, fontSize: '0.9em' }}>
            Leave blank to use your browser timezone ({Intl.DateTimeFormat().resolvedOptions().timeZone}). Format: +HH:MM
          </div>
        </div>
      </div>

      <div className="approvals-list">
        {schedulablePosts.map(({ batch, post }) => (
          <Card key={post.post_id} className="approval-card">
            <div className="approval-header">
              <div className="approval-agent">Content Marketing Agent</div>
              <div className="approval-wait">Batch {batch.batch_id.slice(0, 8)}…</div>
            </div>

            <div className="approval-body">
              <h3>Schedule post for {post.channel.toUpperCase()}:</h3>
              <p className="approval-action">{post.text}</p>

              <div className="approval-meta">
                <span>Theme: <strong>{batch.theme}</strong></span>
                <span> | </span>
                <span>Brand: {batch.brand_name}</span>
              </div>

              <div style={{ marginTop: '0.75rem' }}>
                <input
                  type="datetime-local"
                  value={scheduleTimes[post.post_id] || ''}
                  onChange={(e) => setScheduleTimes((prev) => ({ ...prev, [post.post_id]: e.target.value }))}
                />
                <span style={{ marginLeft: '0.5rem', opacity: 0.8 }}>
                  ({Intl.DateTimeFormat().resolvedOptions().timeZone})
                </span>
              </div>
            </div>

            <div className="approval-actions">
              <Button
                appearance="primary"
                style={{ backgroundColor: '#10b981' }}
                onClick={() => onSchedule(post.post_id)}
                disabled={busyPostId === post.post_id}
              >
                🗓 SCHEDULE
              </Button>
            </div>
          </Card>
        ))}
      </div>

      <div style={{ marginTop: '1.5rem' }}>
        <h2>Trading Approvals</h2>
      </div>

      {tradingError && <div style={{ color: '#ef4444', marginBottom: '1rem' }}>{tradingError}</div>}

      <Card className="approval-card">
        <div className="approval-header">
          <div className="approval-agent">Trading Agent</div>
          <div className="approval-wait">Delta Exchange India</div>
        </div>

        <div className="approval-body">
          <h3>Propose a trade:</h3>

          <div className="form-group">
            <label>Agent ID</label>
            <input value={tradeAgentId} onChange={(e) => setTradeAgentId(e.target.value)} />
          </div>

          <div className="form-group">
            <label>Exchange credential ref *</label>
            <input value={exchangeAccountId} onChange={(e) => setExchangeAccountId(e.target.value)} placeholder="EXCH-..." />
          </div>

          <div className="form-group">
            <label>Coin *</label>
            <input value={coin} onChange={(e) => setCoin(e.target.value)} placeholder="BTC" />
          </div>

          <div className="form-group">
            <label>Units *</label>
            <input value={units} onChange={(e) => setUnits(e.target.value)} placeholder="1" />
          </div>

          <div className="form-group">
            <label>Side *</label>
            <select value={side} onChange={(e) => setSide(e.target.value as any)} className="filter-select">
              <option value="long">Long</option>
              <option value="short">Short</option>
            </select>
          </div>

          <div className="form-group">
            <label>Action *</label>
            <select value={tradeAction} onChange={(e) => setTradeAction(e.target.value as any)} className="filter-select">
              <option value="enter">Enter</option>
              <option value="exit">Exit</option>
            </select>
          </div>

          <div className="form-group">
            <label>Order type</label>
            <select value={orderType} onChange={(e) => setOrderType(e.target.value as any)} className="filter-select">
              <option value="market">Market</option>
              <option value="limit">Limit</option>
            </select>
          </div>

          {orderType === 'limit' && (
            <div className="form-group">
              <label>Limit price *</label>
              <input value={limitPrice} onChange={(e) => setLimitPrice(e.target.value)} placeholder="e.g., 45000" />
            </div>
          )}

          {tradeResult && (
            <div style={{ marginTop: '0.75rem' }}>
              <h4>Result</h4>
              <pre style={{ whiteSpace: 'pre-wrap', opacity: 0.9 }}>{JSON.stringify(tradeResult, null, 2)}</pre>
            </div>
          )}
        </div>

        <div className="approval-actions">
          <Button appearance="primary" onClick={onDraftTrade} disabled={tradingBusy || !exchangeAccountId}>
            Generate Draft Plan
          </Button>
          <Button appearance="primary" onClick={onApproveExecuteTrade} disabled={tradingBusy || !exchangeAccountId}>
            Approve & Execute
          </Button>
        </div>
      </Card>
    </div>
  )
}
