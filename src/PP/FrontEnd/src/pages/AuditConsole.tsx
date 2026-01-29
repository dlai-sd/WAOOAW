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
