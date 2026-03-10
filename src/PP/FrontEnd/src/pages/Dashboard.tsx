import React, { useEffect, useState } from 'react'
import { Card, CardHeader, Text, Spinner } from '@fluentui/react-components'
import { gatewayApiClient } from '../services/gatewayApiClient'

export const Dashboard: React.FC = () => {
  const [agentCount, setAgentCount] = useState<number | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    setLoading(true)
    gatewayApiClient.listAgents()
      .then((agents: unknown[]) => setAgentCount(agents.length))
      .catch(() => setError('Failed to load'))
      .finally(() => setLoading(false))
  }, [])

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
            <CardHeader header={<Text weight="semibold">Active agent definitions</Text>} />
            {loading ? (
              <Spinner size="tiny" />
            ) : error ? (
              <Text style={{ color: 'red' }}>—</Text>
            ) : (
              <Text size={700}>{agentCount ?? '—'}</Text>
            )}
            <Text size={200}>Current authored supply in the marketplace</Text>
          </Card>
          <Card className="metric-card">
            <CardHeader header={<Text weight="semibold">Approvals at risk</Text>} />
            <Text size={700}>3</Text>
            <Text size={200}>Customer-facing decisions waiting on ops review</Text>
          </Card>
          <Card className="metric-card">
            <CardHeader header={<Text weight="semibold">Incident posture</Text>} />
            <Text size={700}>Stable</Text>
            <Text size={200}>No critical marketplace incidents in the last 24h</Text>
          </Card>
          <Card className="metric-card">
            <CardHeader header={<Text weight="semibold">Operator focus</Text>} />
            <Text size={700}>Publish safely</Text>
            <Text size={200}>Design, validate, and release with strong runtime discipline</Text>
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
            Contributors need hierarchy, next actions, and proof of impact before they need more raw tables.
          </p>
        </Card>
      </div>
    </div>
  )
}

export default Dashboard
