import React, { useState } from 'react'
import { Button, Card, CardHeader, Text, Spinner } from '@fluentui/react-components'
import { gatewayApiClient } from '../services/gatewayApiClient'

export const Dashboard: React.FC = () => {
  const [agentCount, setAgentCount] = useState<number | null>(null)
  const [hasLoadedAgentCount, setHasLoadedAgentCount] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const loadAgentCount = async () => {
    setLoading(true)
    setError(null)
    try {
      const agents = await gatewayApiClient.listAgents()
      setAgentCount(agents.length)
      setHasLoadedAgentCount(true)
    } catch {
      setAgentCount(null)
      setHasLoadedAgentCount(true)
      setError('Failed to load live count')
    } finally {
      setLoading(false)
    }
  }

  const priorities = [
    'Review blocked approvals before they affect customer-visible delivery.',
    'Check hired-agent health before support tickets become incidents.',
    'Validate newly authored agent definitions before publishing them for hire.',
  ]

  return (
    <div className="page-container" data-testid="pp-dashboard-page">
      <div className="pp-dashboard-grid">
        <Card className="pp-dashboard-panel pp-dashboard-panel--accent">
          <div className="pp-dashboard-kicker">Contributor priorities</div>
          <Text as="h2" size={700} weight="semibold">Keep the platform calm and shippable.</Text>
          <div className="pp-dashboard-priority-list">
            {priorities.map((item) => (
              <div key={item} className="pp-dashboard-priority-item">• {item}</div>
            ))}
          </div>
        </Card>

        <div className="dashboard-grid">
          <Card className="metric-card">
            <CardHeader
              header={<Text weight="semibold">Active agent definitions</Text>}
              action={
                <Button appearance="subtle" size="small" onClick={() => void loadAgentCount()} disabled={loading}>
                  {loading ? 'Loading…' : hasLoadedAgentCount ? 'Refresh' : 'Load live count'}
                </Button>
              }
            />
            {loading ? (
              <Spinner size="tiny" />
            ) : error ? (
              <Text size={700}>Unavailable</Text>
            ) : !hasLoadedAgentCount ? (
              <Text size={700}>Not loaded</Text>
            ) : (
              <Text size={700}>{agentCount ?? '—'}</Text>
            )}
            <Text size={200}>
              {error
                ? 'The live count request failed. Retry when the API path is healthy.'
                : hasLoadedAgentCount
                  ? 'Live authored supply loaded on demand.'
                  : 'Load the current authored supply only when you need a live count.'}
            </Text>
          </Card>
          <Card className="metric-card">
            <CardHeader header={<Text weight="semibold">Approval posture</Text>} />
            <Text size={700}>Check live queues</Text>
            <Text size={200}>Draft Review and Hired Agents Ops hold the real queue state. This dashboard does not preload those counts.</Text>
          </Card>
          <Card className="metric-card">
            <CardHeader header={<Text weight="semibold">Incident posture</Text>} />
            <Text size={700}>Needs verification</Text>
            <Text size={200}>Use Audit Console or runtime ops to confirm failures. No global incident rollup is implied here.</Text>
          </Card>
          <Card className="metric-card">
            <CardHeader header={<Text weight="semibold">Operator focus</Text>} />
            <Text size={700}>Choose a surface</Text>
            <Text size={200}>Open the screen that matches the job: review drafts, inspect denials, or audit a scoped entity.</Text>
          </Card>
        </div>
      </div>

      <div className="pp-dashboard-grid">
        <Card className="pp-dashboard-panel">
          <Text as="h3" size={600} weight="semibold">Who this portal serves</Text>
          <div className="pp-dashboard-role-grid">
            <div>
              <strong>Tech staff</strong>
              <p>Agent, skill, and component authoring with clear publish gates.</p>
            </div>
            <div>
              <strong>Infra</strong>
              <p>Runtime health, environment confidence, and controlled rollout surfaces.</p>
            </div>
            <div>
              <strong>Helpdesk</strong>
              <p>Faster incident context when customers ask why a run, approval, or bill changed.</p>
            </div>
            <div>
              <strong>Ops</strong>
              <p>One cockpit for approvals, policy denials, hired-agent monitoring, and governance.</p>
            </div>
          </div>
        </Card>

        <Card className="pp-dashboard-panel">
          <Text as="h3" size={600} weight="semibold">Why the UX changed</Text>
          <p className="pp-dashboard-body-copy">
            The portal should feel like a real control plane, not a set of disconnected admin screens.
            Contributors need honest entry states, clear next actions, and deliberate loading before they trust the data in front of them.
          </p>
        </Card>
      </div>
    </div>
  )
}

export default Dashboard
