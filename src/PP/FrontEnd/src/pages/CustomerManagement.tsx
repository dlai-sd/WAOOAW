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
type UsageAggregateRow = {
  bucket: 'day' | 'month'
  bucket_start: string
  customer_id?: string | null
  agent_id?: string | null
  event_type?: string | null
  event_count: number
  tokens_in: number
  tokens_out: number
  cost_usd: number
}
type UsageEventsAggregateResponse = {
  count: number
  rows: UsageAggregateRow[]
}

export default function CustomerManagement() {
  const [customerId, setCustomerId] = useState('CUST-1')
  const [agentId, setAgentId] = useState('')
  const [limit, setLimit] = useState('100')
  const [aggregateBucket, setAggregateBucket] = useState<'day' | 'month'>('day')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<unknown>(null)
  const [data, setData] = useState<UsageEventsListResponse | null>(null)
  const [isAggregateLoading, setIsAggregateLoading] = useState(false)
  const [aggregateError, setAggregateError] = useState<unknown>(null)
  const [aggregateData, setAggregateData] = useState<UsageEventsAggregateResponse | null>(null)

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
  const loadAggregates = useCallback(async (signal?: AbortSignal) => {
    setIsAggregateLoading(true)
    setAggregateError(null)
    try {
      const response = (await gatewayApiClient.aggregateUsageEvents({
        bucket: aggregateBucket,
        customer_id: customerId.trim() || undefined,
        agent_id: agentId.trim() || undefined
      })) as UsageEventsAggregateResponse
      setAggregateData(response)
    } catch (e: any) {
      if (e?.name === 'AbortError' || signal?.aborted) return
      setAggregateError(e)
      setAggregateData(null)
    } finally {
      setIsAggregateLoading(false)
    }
  }, [aggregateBucket, customerId, agentId])

  useEffect(() => {
    const abortController = new AbortController()
    void loadUsage(abortController.signal)
    void loadAggregates(abortController.signal)
    return () => abortController.abort()
  }, [loadUsage, loadAggregates])

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
      <Card style={{ marginTop: 16 }}>
        <CardHeader
          header={<Text weight="semibold">Usage Aggregates</Text>}
          description={<Text size={200}>{isAggregateLoading ? 'Loading…' : aggregateData ? `${aggregateData.count} rows` : '—'}</Text>}
          action={
            <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
              <Button
                appearance={aggregateBucket === 'day' ? 'primary' : 'secondary'}
                size="small"
                onClick={() => setAggregateBucket('day')}
                disabled={isAggregateLoading}
              >
                Day
              </Button>
              <Button
                appearance={aggregateBucket === 'month' ? 'primary' : 'secondary'}
                size="small"
                onClick={() => setAggregateBucket('month')}
                disabled={isAggregateLoading}
              >
                Month
              </Button>
              <Button appearance="subtle" size="small" onClick={() => void loadAggregates()} disabled={isAggregateLoading}>
                Refresh
              </Button>
            </div>
          }
        />

        {aggregateError && <div style={{ padding: 16 }}><ApiErrorPanel title="Usage aggregates error" error={aggregateError} /></div>}

        {!aggregateError && isAggregateLoading && (
          <div style={{ padding: 16 }}>
            <Spinner label="Loading usage aggregates..." />
          </div>
        )}

        <Table>
          <TableHeader>
            <TableRow>
              <TableHeaderCell>Bucket Start (UTC)</TableHeaderCell>
              <TableHeaderCell>Type</TableHeaderCell>
              <TableHeaderCell>Count</TableHeaderCell>
              <TableHeaderCell>Tokens</TableHeaderCell>
              <TableHeaderCell>Cost (USD)</TableHeaderCell>
            </TableRow>
          </TableHeader>
          <TableBody>
            {(aggregateData?.rows || []).map((r, idx) => (
              <TableRow key={`${r.bucket_start}-${r.event_type || 'any'}-${idx}`}>
                <TableCell>{r.bucket_start ? new Date(r.bucket_start).toISOString().slice(0, 10) : '-'}</TableCell>
                <TableCell>{r.event_type || '-'}</TableCell>
                <TableCell>{r.event_count}</TableCell>
                <TableCell>{`${r.tokens_in}/${r.tokens_out}`}</TableCell>
                <TableCell>{typeof r.cost_usd === 'number' ? r.cost_usd.toFixed(6) : '-'}</TableCell>
              </TableRow>
            ))}

            {!isAggregateLoading && !aggregateError && (aggregateData?.rows || []).length === 0 && (
              <TableRow>
                <TableCell colSpan={5}>
                  <Text>No aggregate rows returned.</Text>
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </Card>
    </div>
  )
}
