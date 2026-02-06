import { useEffect, useState } from 'react'
import { Card, CardHeader, Text, Body1, Spinner } from '@fluentui/react-components'
import ApiErrorPanel from '../components/ApiErrorPanel'
import { gatewayApiClient } from '../services/gatewayApiClient'

export type PlantReferenceAgent = {
  agent_id: string
  display_name: string
  agent_type: string
  spec: Record<string, unknown>
}

export default function ReferenceAgents() {
  const [agents, setAgents] = useState<PlantReferenceAgent[] | null>(null)
  const [error, setError] = useState<unknown>(null)

  useEffect(() => {
    let cancelled = false

    async function load() {
      try {
        setError(null)
        const data = (await gatewayApiClient.listReferenceAgents()) as PlantReferenceAgent[]
        if (!cancelled) setAgents(data)
      } catch (e) {
        if (!cancelled) setError(e)
      }
    }

    void load()
    return () => {
      cancelled = true
    }
  }, [])

  return (
    <div className="page-container">
      <div className="page-header">
        <Text as="h1" size={900} weight="semibold">Reference Agents</Text>
        <Body1>Demo agents manufactured from AgentSpecs (Plant)</Body1>
      </div>

      {error && <ApiErrorPanel title="Failed to load reference agents" error={error} />}

      {!error && agents === null ? (
        <Card style={{ padding: 16 }}>
          <Spinner label="Loading reference agents..." />
        </Card>
      ) : null}

      {agents && (
        <Card>
          <CardHeader header={<Text weight="semibold">Available Agents ({agents.length})</Text>} />
          <div style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {agents.map((agent) => (
              <Card key={agent.agent_id} appearance="outline">
                <div style={{ padding: 12, display: 'flex', flexDirection: 'column', gap: 8 }}>
                  <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', gap: 12 }}>
                    <Text weight="semibold">{agent.display_name}</Text>
                    <Text size={200} style={{ opacity: 0.85 }}>{agent.agent_type}</Text>
                  </div>
                  <Text size={200} style={{ opacity: 0.9 }}>ID: {agent.agent_id}</Text>
                  <pre style={{ margin: 0, whiteSpace: 'pre-wrap', fontSize: 12, opacity: 0.9 }}>
                    {JSON.stringify(agent.spec, null, 2)}
                  </pre>
                </div>
              </Card>
            ))}
          </div>
        </Card>
      )}
    </div>
  )
}
