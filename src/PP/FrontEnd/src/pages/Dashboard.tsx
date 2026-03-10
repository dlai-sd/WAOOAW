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

  return (
    <div style={{ padding: 24 }} data-testid="pp-dashboard-page">
      <Text as="h1" size={900} weight="semibold" style={{ marginBottom: 24 }}>
        Dashboard
      </Text>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16 }}>
        <Card>
          <CardHeader header={<Text weight="semibold">MRR</Text>} />
          <Text size={700}>N/A</Text>
          <Text size={200} style={{ color: '#888' }}>Coming soon</Text>
        </Card>
        <Card>
          <CardHeader header={<Text weight="semibold">Active Agents</Text>} />
          {loading ? (
            <Spinner size="tiny" />
          ) : error ? (
            <Text style={{ color: 'red' }}>—</Text>
          ) : (
            <Text size={700}>{agentCount ?? '—'}</Text>
          )}
        </Card>
        <Card>
          <CardHeader header={<Text weight="semibold">Customers</Text>} />
          <Text size={700}>N/A</Text>
          <Text size={200} style={{ color: '#888' }}>Coming soon</Text>
        </Card>
        <Card>
          <CardHeader header={<Text weight="semibold">Churn Rate</Text>} />
          <Text size={700}>N/A</Text>
          <Text size={200} style={{ color: '#888' }}>Coming soon</Text>
        </Card>
      </div>
    </div>
  )
}

export default Dashboard
