import { useCallback, useState } from 'react'
import { Card, CardHeader, Text, Body1, Button, Input } from '@fluentui/react-components'
import ApiErrorPanel from '../components/ApiErrorPanel'
import { gatewayApiClient } from '../services/gatewayApiClient'

export default function AuditConsole() {
  const [entityType, setEntityType] = useState('')
  const [entityId, setEntityId] = useState('')
  const [isRunning, setIsRunning] = useState(false)
  const [result, setResult] = useState<unknown>(null)
  const [error, setError] = useState<unknown>(null)

  const runAudit = useCallback(async () => {
    setIsRunning(true)
    setError(null)
    setResult(null)

    try {
      const data = await gatewayApiClient.runAudit({
        entity_type: entityType.trim() ? entityType.trim() : undefined,
        entity_id: entityId.trim() ? entityId.trim() : undefined
      })
      setResult(data)
    } catch (e) {
      setError(e)
    } finally {
      setIsRunning(false)
    }
  }, [entityId, entityType])

  return (
    <div className="page-container">
      <div className="page-header">
        <Text as="h1" size={900} weight="semibold">Audit Console</Text>
        <Body1>Run constitutional compliance audits via Plant</Body1>
      </div>

      <div className="pp-dashboard-grid" style={{ marginBottom: 20 }}>
        <Card className="pp-dashboard-panel pp-dashboard-panel--accent">
          <div className="pp-dashboard-kicker">Constitutional checks</div>
          <Text as="h2" size={700} weight="semibold">Give governance and infra a clean path to verify the runtime.</Text>
          <p className="pp-dashboard-body-copy">
            This console should feel like a deliberate compliance tool, not an internal debug box. The operator should know what is being audited and why it matters.
          </p>
        </Card>
        <Card className="pp-dashboard-panel">
          <Text as="h3" size={600} weight="semibold">When to use it</Text>
          <p className="pp-dashboard-body-copy">
            Use this during release checks, runtime investigations, or whenever a construct change needs a stronger compliance proof before publish.
          </p>
        </Card>
      </div>

      <Card>
        <CardHeader
          header={<Text weight="semibold">Run Audit</Text>}
          description={<Text size={200}>Calls PP → Plant Gateway with your auth token</Text>}
          action={
            <Button appearance="primary" onClick={() => void runAudit()} disabled={isRunning}>
              {isRunning ? 'Running…' : 'Run'}
            </Button>
          }
        />

        <div style={{ padding: 16, display: 'grid', gap: 12, gridTemplateColumns: '1fr 1fr' }}>
          <Text size={200} style={{ gridColumn: '1 / -1', opacity: 0.8 }}>
            Leave both fields empty for broad checks, or narrow the run when investigating a specific entity or release concern.
          </Text>
          <div>
            <Text size={200} style={{ display: 'block', marginBottom: 6, opacity: 0.85 }}>Entity Type (optional)</Text>
            <Input value={entityType} onChange={(_, data) => setEntityType(data.value)} placeholder="skill | job_role | agent" />
          </div>
          <div>
            <Text size={200} style={{ display: 'block', marginBottom: 6, opacity: 0.85 }}>Entity ID (optional)</Text>
            <Input value={entityId} onChange={(_, data) => setEntityId(data.value)} placeholder="UUID or entity id" />
          </div>
        </div>

        {error && <div style={{ padding: 16 }}><ApiErrorPanel title="Audit error" error={error} /></div>}

        {!result && !error && !isRunning && (
          <div style={{ padding: 16 }}>
            <Card className="pp-agent-setup-card">
              <Text weight="semibold">Choose the audit scope deliberately</Text>
              <Text size={200} style={{ display: 'block', marginTop: 8, opacity: 0.8 }}>
                Leave the fields empty for a broad platform check, or narrow to one entity when investigating a release, incident, or compliance concern.
              </Text>
            </Card>
          </div>
        )}

        {result && (
          <div style={{ padding: 16 }}>
            <Text weight="semibold">Result</Text>
            <pre
              style={{
                marginTop: 8,
                padding: 12,
                background: 'rgba(255,255,255,0.04)',
                border: '1px solid rgba(255,255,255,0.08)',
                borderRadius: 8,
                overflowX: 'auto'
              }}
            >
              {JSON.stringify(result, null, 2)}
            </pre>
          </div>
        )}
      </Card>
    </div>
  )
}
