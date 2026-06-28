import { Badge, Button, Card, Spinner } from '@fluentui/react-components'
import { useState } from 'react'
import { reviewHiredAgentDeliverable, type Deliverable } from '../services/hiredAgentDeliverables.service'

interface Props {
  deliverable: Deliverable
  onActionComplete: (id: string) => void
}

function signalAgeMinutes(createdAt: string): number {
  return Math.floor((Date.now() - new Date(createdAt).getTime()) / 60000)
}

export function TradingApprovalCard({ deliverable, onActionComplete }: Props) {
  const [acting, setActing] = useState<'approving' | 'rejecting' | null>(null)
  const payload = (deliverable.payload ?? {}) as Record<string, unknown>
  const action = String(payload.side ?? payload.action ?? '').toUpperCase()
  const isBuy = action === 'LONG' || action === 'BUY' || action === 'ENTER'
  const ageMin = signalAgeMinutes(deliverable.created_at ?? '')

  const handle = async (decision: 'approved' | 'rejected') => {
    setActing(decision === 'approved' ? 'approving' : 'rejecting')
    try {
      await reviewHiredAgentDeliverable(deliverable.deliverable_id, { decision })
      onActionComplete(deliverable.deliverable_id)
    } finally {
      setActing(null)
    }
  }

  return (
    <Card style={{ background: '#18181b', border: '1px solid #27272a', borderRadius: 12, padding: 16 }}
      data-testid={`trade-approval-card-${deliverable.deliverable_id}`}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
        <span style={{ color: '#f4f4f5', fontWeight: 700, fontSize: 16 }}>
          {String(payload.coin ?? payload.symbol ?? '—')}
        </span>
        <Badge appearance="filled" color={isBuy ? 'success' : 'danger'} size="medium">
          {isBuy ? 'BUY' : 'SELL'}
        </Badge>
      </div>
      {ageMin > 15 && (
        <div style={{ color: '#f59e0b', fontSize: 12, marginBottom: 8 }}>
          ⚠️ Signal is {ageMin} min old — market may have moved
        </div>
      )}
      <div style={{ display: 'flex', gap: 16, fontSize: 13, color: '#a1a1aa', marginBottom: 16 }}>
        {payload.units != null && <span>Qty: <strong style={{ color: '#f4f4f5' }}>{String(payload.units)}</strong></span>}
        {payload.stop_loss_price != null && <span>SL: <strong style={{ color: '#ef4444' }}>₹{Number(payload.stop_loss_price).toLocaleString('en-IN')}</strong></span>}
        {payload.take_profit_price != null && <span>TP: <strong style={{ color: '#10b981' }}>₹{Number(payload.take_profit_price).toLocaleString('en-IN')}</strong></span>}
      </div>
      <div style={{ display: 'flex', gap: 8 }}>
        <Button
          appearance="primary"
          onClick={() => handle('approved')}
          disabled={acting !== null}
          data-testid={`approve-btn-${deliverable.deliverable_id}`}
          style={{ background: '#10b981' }}
        >
          {acting === 'approving' ? <Spinner size="tiny" /> : '✓ Approve'}
        </Button>
        <Button
          appearance="subtle"
          onClick={() => handle('rejected')}
          disabled={acting !== null}
          data-testid={`reject-btn-${deliverable.deliverable_id}`}
          style={{ borderColor: '#ef444455', color: '#ef4444' }}
        >
          {acting === 'rejecting' ? <Spinner size="tiny" /> : '✗ Reject'}
        </Button>
      </div>
    </Card>
  )
}
