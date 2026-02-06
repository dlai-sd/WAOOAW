import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  Card,
  CardHeader,
  Text,
  Body1,
  Button,
  Spinner
} from '@fluentui/react-components'
import ApiErrorPanel from '../components/ApiErrorPanel'
import { gatewayApiClient } from '../services/gatewayApiClient'

function downloadJson(filename: string, json: unknown) {
  const blob = new Blob([JSON.stringify(json, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

export default function AgentSpecTools() {
  const [schema, setSchema] = useState<unknown>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<unknown>(null)
  const [copyState, setCopyState] = useState<'idle' | 'copied' | 'failed'>('idle')

  const schemaText = useMemo(() => (schema ? JSON.stringify(schema, null, 2) : ''), [schema])

  const load = useCallback(async (signal?: AbortSignal) => {
    setIsLoading(true)
    setError(null)
    try {
      const res = await gatewayApiClient.fetchAgentSpecSchema()
      if (signal?.aborted) return
      setSchema(res)
    } catch (e: any) {
      if (e?.name === 'AbortError' || signal?.aborted) return
      setError(e)
      setSchema(null)
    } finally {
      setIsLoading(false)
      setCopyState('idle')
    }
  }, [])

  useEffect(() => {
    const abortController = new AbortController()
    void load(abortController.signal)
    return () => abortController.abort()
  }, [load])

  const copy = async () => {
    if (!schemaText) return
    try {
      await navigator.clipboard.writeText(schemaText)
      setCopyState('copied')
    } catch {
      setCopyState('failed')
    }
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <Text as="h1" size={900} weight="semibold">AgentSpec Tools</Text>
        <Body1>Fetch and validate AgentSpec schema from Plant</Body1>
      </div>

      <Card>
        <CardHeader
          header={<Text weight="semibold">AgentSpec JSON Schema</Text>}
          description={<Text size={200}>{isLoading ? 'Loading…' : schema ? 'Loaded' : '—'}</Text>}
          action={
            <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
              <Button appearance="subtle" size="small" onClick={() => void load()} disabled={isLoading}>
                Refresh
              </Button>
              <Button appearance="secondary" size="small" onClick={() => void copy()} disabled={isLoading || !schemaText}>
                {copyState === 'copied' ? 'Copied' : 'Copy'}
              </Button>
              <Button
                appearance="secondary"
                size="small"
                onClick={() => downloadJson('agent-spec.schema.json', schema)}
                disabled={isLoading || !schema}
              >
                Download
              </Button>
            </div>
          }
        />

        {error && <div style={{ padding: 16 }}><ApiErrorPanel title="Schema fetch error" error={error} /></div>}

        {!error && isLoading && (
          <div style={{ padding: 16 }}>
            <Spinner label="Loading schema..." />
          </div>
        )}

        {!error && schema && (
          <div style={{ padding: 16 }}>
            {copyState === 'failed' && (
              <Text size={200} style={{ display: 'block', marginBottom: 8 }}>
                Copy failed. Your browser may block clipboard access.
              </Text>
            )}
            <pre
              style={{
                margin: 0,
                padding: 12,
                background: 'rgba(255,255,255,0.04)',
                border: '1px solid rgba(255,255,255,0.08)',
                borderRadius: 8,
                overflowX: 'auto'
              }}
            >
              {schemaText}
            </pre>
          </div>
        )}
      </Card>
    </div>
  )
}
