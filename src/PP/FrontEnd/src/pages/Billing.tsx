import { useEffect, useState } from 'react'
import { Body1, Card, CardHeader, Spinner, Text } from '@fluentui/react-components'

import { gatewayApiClient } from '../services/gatewayApiClient'

type SubscriptionRecord = {
  subscription_id: string
  status?: string | null
  agent_id?: string | null
  duration?: string | null
}

export default function Billing() {
  const [subscriptions, setSubscriptions] = useState<SubscriptionRecord[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    gatewayApiClient
      .listOpsSubscriptions({})
      .then((data) => setSubscriptions((data as SubscriptionRecord[]) || []))
      .catch(() => setError('Failed to load subscription data. Please try again.'))
      .finally(() => setLoading(false))
  }, [])

  const total = subscriptions.length
  const active = subscriptions.filter((s) => s.status === 'active').length
  const trial = subscriptions.filter((s) => s.status === 'trial').length
  const inactive = total - active - trial

  return (
    <div className="page-container">
      <div className="page-header">
        <Text as="h1" size={900} weight="semibold">
          Subscription Overview
        </Text>
        <Body1>Live subscription data from Plant API</Body1>
      </div>

      {error && (
        <div className="error-banner" style={{ color: '#ef4444', padding: '12px 0' }}>
          {error}
        </div>
      )}

      {loading ? (
        <Spinner label="Loading subscription data..." style={{ marginTop: 32 }} />
      ) : (
        <>
          <div className="dashboard-grid">
            <Card className="metric-card">
              <CardHeader header={<Text weight="semibold">Total Subscriptions</Text>} />
              <Text size={700}>{total}</Text>
            </Card>

            <Card className="metric-card">
              <CardHeader header={<Text weight="semibold">Active Subscriptions</Text>} />
              <Text size={700}>{active}</Text>
            </Card>

            <Card className="metric-card">
              <CardHeader header={<Text weight="semibold">Trial Subscriptions</Text>} />
              <Text size={700}>{trial}</Text>
            </Card>

            <Card className="metric-card">
              <CardHeader header={<Text weight="semibold">Inactive / Other</Text>} />
              <Text size={700}>{inactive}</Text>
            </Card>
          </div>

          {subscriptions.length === 0 ? (
            <Card style={{ marginTop: '24px' }}>
              <div style={{ padding: '16px' }}>
                <Text>No subscriptions found.</Text>
              </div>
            </Card>
          ) : (
            <Card style={{ marginTop: '24px' }}>
              <CardHeader header={<Text weight="semibold">Subscription Status Breakdown</Text>} />
              <div style={{ padding: '16px' }}>
                {Array.from(
                  new Set(subscriptions.map((s) => s.status ?? 'unknown'))
                ).map((status) => (
                  <div key={status} style={{ marginBottom: 4 }}>
                    <Text>
                      {status}:{' '}
                      {subscriptions.filter((s) => (s.status ?? 'unknown') === status).length}
                    </Text>
                  </div>
                ))}
              </div>
            </Card>
          )}
        </>
      )}
    </div>
  )
}
