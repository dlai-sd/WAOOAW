import { Button, Card } from '@fluentui/react-components'
import { useMemo } from 'react'
import { useNavigate, useParams, useSearchParams } from 'react-router-dom'

export default function HireReceipt() {
  const navigate = useNavigate()
  const params = useParams()
  const [searchParams] = useSearchParams()

  const orderId = params.orderId || ''
  const subscriptionId = searchParams.get('subscriptionId') || ''
  const agentId = searchParams.get('agentId') || ''

  const canContinue = useMemo(() => Boolean(subscriptionId && agentId), [subscriptionId, agentId])

  return (
    <div style={{ maxWidth: '800px', margin: '0 auto', padding: '2rem 1rem' }}>
      <Card style={{ padding: '2rem' }}>
        <h1 style={{ marginTop: 0 }}>Payment confirmed</h1>
        <p style={{ color: '#666' }}>
          Your order is confirmed. Keep this reference for support.
        </p>

        <div style={{ marginTop: '1rem', padding: '1rem', background: '#f5f5f5', borderRadius: '0.5rem' }}>
          <div style={{ fontWeight: 600 }}>Order ID</div>
          <div style={{ fontFamily: 'monospace' }}>{orderId}</div>
        </div>

        <div style={{ marginTop: '1.5rem', display: 'flex', gap: '0.75rem' }}>
          <Button appearance="secondary" onClick={() => navigate('/portal')}>Go to Portal</Button>
          <Button appearance="primary" onClick={() => navigate(`/hire/setup/${encodeURIComponent(subscriptionId)}?agentId=${encodeURIComponent(agentId)}`)} disabled={!canContinue}>
            Continue Setup
          </Button>
        </div>
      </Card>
    </div>
  )
}
