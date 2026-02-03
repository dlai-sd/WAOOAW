import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Card, CardHeader, Text, Body1, Button } from '@fluentui/react-components'
import ApiErrorPanel from '../components/ApiErrorPanel'
import { gatewayApiClient } from '../services/gatewayApiClient'

export default function AgentData() {
  const [isSeeding, setIsSeeding] = useState(false)
  const [seedResult, setSeedResult] = useState<unknown | null>(null)
  const [error, setError] = useState<unknown | null>(null)

  const runSeed = async () => {
    setIsSeeding(true)
    setError(null)
    setSeedResult(null)
    try {
      const res = await gatewayApiClient.seedDefaultAgentData()
      setSeedResult(res)
    } catch (e) {
      setError(e)
    } finally {
      setIsSeeding(false)
    }
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <Text as="h1" size={900} weight="semibold">Agent Management</Text>
        <Body1>Seed baseline master data (dev-only)</Body1>
      </div>

      <div style={{ display: 'flex', gap: 12, marginBottom: 16 }}>
        <Link to="/agents" style={{ textDecoration: 'none' }}>
          <Button appearance="secondary">Agents</Button>
        </Link>
        <Link to="/agents/data" style={{ textDecoration: 'none' }}>
          <Button appearance="primary">Agent Data</Button>
        </Link>
      </div>

      <Card>
        <CardHeader header={<Text weight="semibold">Seed Default Catalog</Text>} />
        <div style={{ padding: 16, display: 'flex', flexDirection: 'column', gap: 12 }}>
          <Text size={200} style={{ opacity: 0.9 }}>
            Seeds Skills → Job Roles → Agents through Plant APIs. This avoids direct DB migrations and is safe to re-run.
          </Text>

          <div style={{ display: 'flex', gap: 12 }}>
            <Button appearance="primary" onClick={runSeed} disabled={isSeeding}>
              {isSeeding ? 'Seeding…' : 'Seed Default Agents'}
            </Button>
            <Link to="/agents" style={{ textDecoration: 'none' }}>
              <Button appearance="secondary">View Agents</Button>
            </Link>
          </div>

          {error ? <ApiErrorPanel title="Seed error" error={error} /> : null}

          {seedResult !== null ? (
            <pre style={{ margin: 0, padding: 12, borderRadius: 8, background: 'rgba(255,255,255,0.06)', overflowX: 'auto' }}>
              {JSON.stringify(seedResult, null, 2)}
            </pre>
          ) : null}
        </div>
      </Card>
    </div>
  )
}
