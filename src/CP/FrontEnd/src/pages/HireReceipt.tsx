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
  const agentTypeId = searchParams.get('agentTypeId') || ''
  const catalogReleaseId = searchParams.get('catalogReleaseId') || ''
  const catalogVersion = searchParams.get('catalogVersion') || ''
  const lifecycleState = searchParams.get('lifecycleState') || ''
  const agentName = searchParams.get('agentName') || ''

  const canContinue = useMemo(() => Boolean(subscriptionId && agentId), [subscriptionId, agentId])
  const selectedAgentSummary = useMemo(() => {
    const base = agentName || agentId || 'Agent reference unavailable'
    return catalogVersion ? `${base} · ${catalogVersion}` : base
  }, [agentId, agentName, catalogVersion])

  return (
    <div className="hire-receipt-page" style={{ maxWidth: '920px', margin: '0 auto', padding: '2rem 1rem' }} data-testid="cp-hire-receipt-page">
      <div className="hire-wizard-hero">
        <div>
          <div className="hire-wizard-kicker">Hire Payment</div>
          <h1 style={{ marginTop: 0, marginBottom: '0.6rem' }}>Payment confirmed</h1>
          <p style={{ color: 'var(--colorNeutralForeground2)', maxWidth: '58ch' }}>
            Your order is confirmed. The next step is setup, not guesswork. Keep this reference for support and continue directly into activation.
          </p>
        </div>
        <div className="hire-wizard-proof-grid">
          <div className="hire-wizard-proof-card">
            <div className="hire-wizard-proof-value">Agent</div>
            <div className="hire-wizard-proof-label">{selectedAgentSummary}</div>
          </div>
          <div className="hire-wizard-proof-card">
            <div className="hire-wizard-proof-value">Paid</div>
            <div className="hire-wizard-proof-label">Order captured</div>
          </div>
          <div className="hire-wizard-proof-card">
            <div className="hire-wizard-proof-value">Next</div>
            <div className="hire-wizard-proof-label">Finish setup</div>
          </div>
          <div className="hire-wizard-proof-card">
            <div className="hire-wizard-proof-value">Then</div>
            <div className="hire-wizard-proof-label">Activate and operate</div>
          </div>
        </div>
      </div>

      <Card style={{ padding: '2rem' }}>
        <div className="hire-wizard-step-title">Reference for support</div>
        <div className="hire-receipt-reference-card">
          <div className="hire-receipt-reference-label">Order ID</div>
          <div className="hire-receipt-reference-value">{orderId}</div>
        </div>
        {subscriptionId ? (
          <div className="hire-receipt-reference-card">
            <div className="hire-receipt-reference-label">Subscription ID</div>
            <div className="hire-receipt-reference-value">{subscriptionId}</div>
          </div>
        ) : null}
        <div className="hire-receipt-reference-card">
          <div className="hire-receipt-reference-label">Selected Agent</div>
          <div className="hire-receipt-reference-value">{selectedAgentSummary}</div>
        </div>

        <div className="hire-wizard-bottom-grid" style={{ marginTop: '1.5rem' }}>
          <Card className="hire-wizard-bottom-card">
            <div className="hire-wizard-bottom-title">What happens next</div>
            <p>Continue into My Agents, finish setup inline, and move into trial or runtime operations with fewer surprises.</p>
          </Card>
          <Card className="hire-wizard-bottom-card">
            <div className="hire-wizard-bottom-title">If you stop here</div>
            <p>The payment is confirmed, but the agent is not yet ready to work until setup is completed.</p>
          </Card>
        </div>

        <div style={{ marginTop: '1.5rem', display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
          <Button
            appearance="primary"
            onClick={() =>
              navigate('/portal', {
                state: {
                  portalEntry: {
                    page: 'my-agents',
                    agentId,
                    source: 'payment-confirmed',
                    subscriptionId,
                    lifecycleState,
                    catalogVersion,
                    agentName,
                    studioStep: 'identity',
                    studioFocus: 'identity',
                  },
                },
              })
            }
            disabled={!canContinue}
            data-testid="cp-hire-receipt-continue"
          >
            Open My Agents setup
          </Button>
          {agentTypeId || catalogReleaseId ? (
            <Button appearance="secondary" onClick={() => navigate('/portal')}>
              Save reference and exit
            </Button>
          ) : null}
        </div>
      </Card>
    </div>
  )
}
