import { useCallback, useEffect, useState } from 'react'
import {
  Card,
  CardHeader,
  Text,
  Body1,
  Table,
  TableHeader,
  TableRow,
  TableHeaderCell,
  TableBody,
  TableCell,
  Button,
  Input,
  Spinner
} from '@fluentui/react-components'
import ApiErrorPanel from '../components/ApiErrorPanel'
import { gatewayApiClient } from '../services/gatewayApiClient'

type UsageEvent = {
  event_type?: string
  correlation_id?: string
  customer_id?: string
  agent_id?: string
  purpose?: string | null
  model?: string | null
  cache_hit?: boolean
  tokens_in?: number
  tokens_out?: number
  cost_usd?: number
  timestamp?: string
}

type UsageEventsListResponse = {
  count: number
  events: UsageEvent[]
}

export default function CustomerManagement() {
  const [customerId, setCustomerId] = useState('CUST-1')
  const [agentId, setAgentId] = useState('')
  const [limit, setLimit] = useState('100')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<unknown>(null)
  const [data, setData] = useState<UsageEventsListResponse | null>(null)

  const loadUsage = useCallback(async (signal?: AbortSignal) => {
    setIsLoading(true)
    setError(null)
    try {
      const response = (await gatewayApiClient.listUsageEvents({
        customer_id: customerId.trim() || undefined,
        agent_id: agentId.trim() || undefined,
        limit: Number(limit) || 100
      })) as UsageEventsListResponse
      setData(response)
    } catch (e: any) {
      if (e?.name === 'AbortError' || signal?.aborted) return
      setError(e)
      setData(null)
    } finally {
      setIsLoading(false)
    }
  }, [customerId, agentId, limit])

  useEffect(() => {
    const abortController = new AbortController()
    void loadUsage(abortController.signal)
    return () => abortController.abort()
  }, [loadUsage])

  return (
    <div className="page-container">
      <div className="page-header">
        <Text as="h1" size={900} weight="semibold">Customer Management</Text>
        <Body1>View customer usage events (Plant)</Body1>
      </div>

      <Card>
        <CardHeader
          header={<Text weight="semibold">Usage Events</Text>}
          description={<Text size={200}>{isLoading ? 'Loading…' : data ? `${data.count} events` : '—'}</Text>}
          action={
            <Button appearance="subtle" size="small" onClick={() => void loadUsage()} disabled={isLoading}>
              Refresh
            </Button>
          }
        />

        <div style={{ padding: 16, display: 'grid', gap: 12, gridTemplateColumns: '1fr 1fr 1fr' }}>
          <div>
            <Text size={200} style={{ display: 'block', marginBottom: 6, opacity: 0.85 }}>Customer ID</Text>
            <Input value={customerId} onChange={(_, d) => setCustomerId(d.value)} placeholder="CUST-1" />
          </div>
          <div>
            <Text size={200} style={{ display: 'block', marginBottom: 6, opacity: 0.85 }}>Agent ID (optional)</Text>
            <Input value={agentId} onChange={(_, d) => setAgentId(d.value)} placeholder="AGT-..." />
          </div>
          <div>
            <Text size={200} style={{ display: 'block', marginBottom: 6, opacity: 0.85 }}>Limit</Text>
            <Input value={limit} onChange={(_, d) => setLimit(d.value)} placeholder="100" />
          </div>
        </div>

        {error && <div style={{ padding: 16 }}><ApiErrorPanel title="Usage events error" error={error} /></div>}

        {!error && isLoading && (
          <div style={{ padding: 16 }}>
            <Spinner label="Loading usage events..." />
          </div>
        )}

        <Table>
          <TableHeader>
            <TableRow>
              <TableHeaderCell>Timestamp</TableHeaderCell>
              <TableHeaderCell>Type</TableHeaderCell>
              <TableHeaderCell>Agent</TableHeaderCell>
              <TableHeaderCell>Model</TableHeaderCell>
              <TableHeaderCell>Tokens</TableHeaderCell>
              <TableHeaderCell>Cost (USD)</TableHeaderCell>
              <TableHeaderCell>Correlation</TableHeaderCell>
            </TableRow>
          </TableHeader>
          <TableBody>
            {(data?.events || []).map((e, idx) => (
              <TableRow key={`${e.correlation_id || 'no-corr'}-${idx}`}>
                <TableCell>{e.timestamp ? new Date(e.timestamp).toLocaleString() : '-'}</TableCell>
                <TableCell>{e.event_type || '-'}</TableCell>
                <TableCell>{e.agent_id || '-'}</TableCell>
                <TableCell>{e.model || '-'}</TableCell>
                <TableCell>{typeof e.tokens_in === 'number' || typeof e.tokens_out === 'number' ? `${e.tokens_in || 0}/${e.tokens_out || 0}` : '-'}</TableCell>
                <TableCell>{typeof e.cost_usd === 'number' ? e.cost_usd.toFixed(6) : '-'}</TableCell>
                <TableCell>{e.correlation_id || '-'}</TableCell>
              </TableRow>
            ))}

            {!isLoading && !error && (data?.events || []).length === 0 && (
              <TableRow>
                <TableCell colSpan={7}>
                  <Text>No usage events returned.</Text>
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </Card>
    </div>
  )
}
