import { useEffect, useState } from 'react'
import { Spinner } from '@fluentui/react-components'
import { FeedbackMessage } from './FeedbackIndicators'
import { TradingApprovalCard } from './TradingApprovalCard'
import { listHiredAgentDeliverables, type Deliverable } from '../services/hiredAgentDeliverables.service'

interface Props {
  hiredInstanceId: string
}

export function TradingApprovalPanel({ hiredInstanceId }: Props) {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [pendingDeliverables, setPendingDeliverables] = useState<Deliverable[]>([])

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(null)

    listHiredAgentDeliverables(hiredInstanceId)
      .then((resp) => {
        if (cancelled) return
        const pending = (resp.deliverables ?? []).filter(
          (d) => d.review_status === 'pending_review'
        )
        setPendingDeliverables(pending)
      })
      .catch((e: unknown) => {
        if (!cancelled) setError(e instanceof Error ? e.message : 'Failed to load trade approvals.')
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })

    return () => {
      cancelled = true
    }
  }, [hiredInstanceId])

  const handleActionComplete = (deliverableId: string) => {
    setPendingDeliverables((prev) => prev.filter((d) => d.deliverable_id !== deliverableId))
  }

  if (loading) return <Spinner label="Loading trade approvals…" />
  if (error) return <FeedbackMessage intent="error" message={error} />

  if (pendingDeliverables.length === 0) {
    return (
      <p style={{ color: '#71717a', padding: '24px 0' }} data-testid="approval-empty-state">
        No pending trade approvals — your agent will notify you when a signal fires.
      </p>
    )
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }} data-testid="trading-approval-panel">
      {pendingDeliverables.map((d) => (
        <TradingApprovalCard
          key={d.deliverable_id}
          deliverable={d}
          onActionComplete={handleActionComplete}
        />
      ))}
    </div>
  )
}
