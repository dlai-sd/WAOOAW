import { useEffect, useState } from 'react'
import { Card, Spinner, Text } from '@fluentui/react-components'
import { plantAPIService } from '../services/plant.service'
import type { AgentTypeDefinition } from '../types/plant.types'

export default function MarketplaceSection() {
  const [agentTypes, setAgentTypes] = useState<AgentTypeDefinition[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false

    const load = async () => {
      setLoading(true)
      setError(null)
      try {
        const types = await plantAPIService.listAgentTypes()
        if (cancelled) return
        if (!Array.isArray(types)) {
          throw new Error('Unexpected agent type catalog response')
        }
        if (types.length !== 2) {
          throw new Error(`Expected exactly 2 agent types, got ${types.length}`)
        }
        setAgentTypes(types)
      } catch (e: any) {
        if (cancelled) return
        setError(e?.message || 'Failed to load agent types')
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    load()
    return () => {
      cancelled = true
    }
  }, [])

  return (
    <section className="marketplace-section">
      <div className="container">
        <div className="agents-grid">
          {loading && <Spinner label="Loading agents..." />}
          {!loading && error && (
            <Card>
              <div style={{ padding: '1rem' }}>
                <Text weight="semibold">Failed to load agents</Text>
                <div style={{ marginTop: '0.25rem' }}>
                  <Text>{error}</Text>
                </div>
              </div>
            </Card>
          )}
          {!loading && !error && agentTypes.map((t) => (
            <Card key={t.agent_type_id}>
              <div style={{ padding: '1rem' }}>
                <Text weight="semibold">{String(t.display_name || t.agent_type_id)}</Text>
                <div style={{ marginTop: '0.25rem' }}>
                  <Text size={200}>{t.agent_type_id}</Text>
                </div>
              </div>
            </Card>
          ))}
        </div>
      </div>
    </section>
  )
}
