import { Card, Button, Badge, Dialog, DialogBody, DialogContent, DialogSurface, DialogTitle } from '@fluentui/react-components'
import { Star20Filled } from '@fluentui/react-icons'
import { useNavigate } from 'react-router-dom'
import { useEffect, useMemo, useState } from 'react'

import { cancelSubscription, listSubscriptions, type Subscription } from '../../services/subscriptions.service'
import { listTrialStatus, type TrialStatusRecord } from '../../services/trialStatus.service'

export default function MyAgents() {
  const navigate = useNavigate()

  const RETENTION_DAYS_AFTER_END = 30

  const [subscriptions, setSubscriptions] = useState<Subscription[]>([])
  const [trialBySubscription, setTrialBySubscription] = useState<Record<string, TrialStatusRecord>>({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [nowMs, setNowMs] = useState(() => Date.now())

  const [confirmOpen, setConfirmOpen] = useState(false)
  const [selected, setSelected] = useState<Subscription | null>(null)
  const [cancelling, setCancelling] = useState(false)

  const activeCount = useMemo(() => subscriptions.length, [subscriptions])

  useEffect(() => {
    const timer = setInterval(() => setNowMs(Date.now()), 60_000)
    return () => clearInterval(timer)
  }, [])

  useEffect(() => {
    let cancelled = false

    const load = async () => {
      setLoading(true)
      setError(null)
      try {
        const [items, trials] = await Promise.all([
          listSubscriptions(),
          listTrialStatus().catch(() => [] as TrialStatusRecord[])
        ])

        if (cancelled) return
        setSubscriptions(items || [])

        const bySub: Record<string, TrialStatusRecord> = {}
        for (const t of trials || []) {
          if (!t?.subscription_id) continue
          bySub[t.subscription_id] = t
        }
        setTrialBySubscription(bySub)
      } catch (e: any) {
        if (!cancelled) setError(e?.message || 'Failed to load subscriptions')
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    load()
    return () => {
      cancelled = true
    }
  }, [])

  const getStatusBadge = (status: string) => {
    const statusMap = {
      active: { appearance: 'filled' as const, color: 'success' as const, label: 'Active' },
      canceled: { appearance: 'ghost' as const, color: undefined, label: 'Canceled' }
    }
    const config = statusMap[status as keyof typeof statusMap] || statusMap.active
    return <Badge appearance={config.appearance} color={config.color} size="small">{config.label}</Badge>
  }

  const formatDate = (iso: string) => {
    try {
      return new Date(iso).toLocaleDateString()
    } catch {
      return iso
    }
  }

  const formatRemaining = (untilIso: string): string => {
    const untilMs = new Date(untilIso).getTime()
    if (!Number.isFinite(untilMs)) return '—'

    const diffMs = Math.max(0, untilMs - nowMs)
    const totalMinutes = Math.floor(diffMs / 60_000)
    const days = Math.floor(totalMinutes / (60 * 24))
    const hours = Math.floor((totalMinutes - days * 60 * 24) / 60)

    if (days > 0) return `${days}d ${hours}h`
    return `${hours}h`
  }

  const renderTrialBanner = (sub: Subscription) => {
    const record = trialBySubscription[sub.subscription_id]
    if (!record) return null

    const configured = Boolean(record.configured)
    const status = String(record.trial_status || '').toLowerCase()

    if (!configured) {
      return (
        <div style={{ marginTop: '0.75rem', padding: '0.75rem', borderRadius: '10px', border: '1px solid var(--colorNeutralStroke2)' }}>
          <div style={{ fontWeight: 600 }}>Trial will start after setup</div>
          <div style={{ marginTop: '0.25rem', opacity: 0.85 }}>
            Finish your configuration to activate the trial.
          </div>
        </div>
      )
    }

    if (status === 'active' && record.trial_end_at) {
      return (
        <div style={{ marginTop: '0.75rem', padding: '0.75rem', borderRadius: '10px', border: '1px solid var(--colorNeutralStroke2)' }}>
          <div style={{ fontWeight: 600 }}>Trial ends in {formatRemaining(record.trial_end_at)}</div>
        </div>
      )
    }

    return null
  }

  const onOpenCancel = (sub: Subscription) => {
    setSelected(sub)
    setConfirmOpen(true)
  }

  const onConfirmCancel = async () => {
    if (!selected) return
    setCancelling(true)
    setError(null)
    try {
      const updated = await cancelSubscription(selected.subscription_id)
      setSubscriptions((prev) => prev.map((s) => (s.subscription_id === updated.subscription_id ? updated : s)))
      setConfirmOpen(false)
      setSelected(null)
    } catch (e: any) {
      setError(e?.message || 'Failed to schedule cancellation')
    } finally {
      setCancelling(false)
    }
  }

  return (
    <div className="my-agents-page">
      <div className="page-header">
        <h1>My Active Agents ({activeCount})</h1>
        <Button appearance="primary" onClick={() => navigate('/discover')}>+ Hire New Agent</Button>
      </div>

      {loading && <div style={{ padding: '1rem 0' }}>Loading…</div>}
      {error && <div style={{ padding: '1rem 0', color: 'var(--colorPaletteRedForeground1)' }}>{error}</div>}

      <div className="agents-list">
        {subscriptions.map(sub => (
          <Card key={sub.subscription_id} className="agent-detail-card">
            <div className="agent-header">
              <div className="agent-title">
                <h2>{sub.agent_id}</h2>
                {getStatusBadge(sub.status)}
              </div>
              <div className="agent-meta">
                <span className="agent-rating">
                  <Star20Filled style={{ color: '#f59e0b' }} />
                </span>
                <span> | Plan: {sub.duration} | Next billing: {formatDate(sub.current_period_end)}</span>
              </div>
            </div>

            <div className="agent-goals">
              <h3>Subscription:</h3>
              <div className="goal-progress">
                <span style={{ opacity: 0.8 }}>ID: {sub.subscription_id}</span>
              </div>
            </div>

            <div className="agent-performance">
              <h4>Performance Today:</h4>
              <ul>
                <li>Query Budget: $0.75/$1.00 (75%) 🟢</li>
                <li>Approval Response: 4.2 min avg</li>
                <li>Tasks Completed: 8</li>
              </ul>
            </div>

            <div className="agent-actions">
              <Button appearance="outline">View Dashboard</Button>
              <Button appearance="outline">Configure Goals</Button>
              <Button appearance="outline">Settings</Button>
              <Button
                appearance="subtle"
                onClick={() => onOpenCancel(sub)}
                disabled={sub.cancel_at_period_end || sub.status !== 'active'}
              >
                End Hire
              </Button>
            </div>

            {renderTrialBanner(sub)}

            {sub.cancel_at_period_end && (
              <div style={{ marginTop: '0.75rem', opacity: 0.85 }}>
                Scheduled to end on {formatDate(sub.current_period_end)}.
                <div style={{ marginTop: '0.35rem', opacity: 0.9 }}>
                  After it ends: you keep read-only access to deliverables and configuration for {RETENTION_DAYS_AFTER_END} days, and can export your work.
                </div>
              </div>
            )}
          </Card>
        ))}
      </div>

      <Dialog open={confirmOpen} onOpenChange={(_, data) => setConfirmOpen(Boolean(data.open))}>
        <DialogSurface style={{ maxWidth: '520px' }}>
          <DialogBody>
            <DialogTitle>End hire at next billing date?</DialogTitle>
            <DialogContent>
              {selected ? (
                <div>
                  <div style={{ marginBottom: '0.75rem' }}>
                    Plan: <strong>{selected.duration}</strong>
                    <br />
                    Next billing date: <strong>{formatDate(selected.current_period_end)}</strong>
                  </div>
                  <div style={{ opacity: 0.9 }}>
                    Your agent stays active until the billing boundary, then billing stops.
                  </div>

                  <div style={{ marginTop: '1rem' }}>
                    <div style={{ fontWeight: 600, marginBottom: '0.35rem' }}>After your hire ends</div>
                    <div style={{ opacity: 0.9 }}>
                      You keep access to your work — but the agent stops running.
                    </div>
                    <ul style={{ margin: '0.5rem 0 0', paddingLeft: '1.25rem', opacity: 0.9 }}>
                      <li>Deliverables and configuration remain available in read-only.</li>
                      <li>Read-only access remains for {RETENTION_DAYS_AFTER_END} days after the end date.</li>
                      <li>You can export/download your work.</li>
                      <li>No new changes will be made after the end date.</li>
                    </ul>
                  </div>
                </div>
              ) : null}

              <div style={{ display: 'flex', gap: '0.75rem', marginTop: '1.25rem' }}>
                <Button appearance="primary" onClick={onConfirmCancel} disabled={cancelling || !selected}>
                  {cancelling ? 'Scheduling…' : 'Confirm end hire'}
                </Button>
                <Button appearance="outline" onClick={() => setConfirmOpen(false)} disabled={cancelling}>
                  Keep subscription
                </Button>
              </div>
            </DialogContent>
          </DialogBody>
        </DialogSurface>
      </Dialog>
    </div>
  )
}
