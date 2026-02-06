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

type PolicyDenialRecord = {
  created_at?: string
  correlation_id: string
  decision_id?: string | null
  agent_id?: string | null
  customer_id?: string | null
  stage?: string | null
  action?: string | null
  reason?: string | null
  path?: string | null
  details?: Record<string, unknown>
}

type PolicyDenialsResponse = {
  count: number
  records: PolicyDenialRecord[]
}

export default function PolicyDenials() {
  const [correlationId, setCorrelationId] = useState('')
  const [customerId, setCustomerId] = useState('')
  const [agentId, setAgentId] = useState('')
  const [limit, setLimit] = useState('100')

  const [selected, setSelected] = useState<PolicyDenialRecord | null>(null)

  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<unknown>(null)
  const [data, setData] = useState<PolicyDenialsResponse | null>(null)

  const load = useCallback(async (signal?: AbortSignal) => {
    setIsLoading(true)
    setError(null)
    try {
      const response = (await gatewayApiClient.listPolicyDenials({
        correlation_id: correlationId.trim() || undefined,
        customer_id: customerId.trim() || undefined,
        agent_id: agentId.trim() || undefined,
        limit: Number(limit) || 100
      })) as PolicyDenialsResponse
      setData(response)
      setSelected(null)
    } catch (e: any) {
      if (e?.name === 'AbortError' || signal?.aborted) return
      setError(e)
      setData(null)
      setSelected(null)
    } finally {
      setIsLoading(false)
    }
  }, [correlationId, customerId, agentId, limit])

  const recommendedNextAction = (rec: PolicyDenialRecord): string => {
    const reason = (rec.reason || '').toLowerCase()
    if (reason.includes('approval_required')) return 'Provide approval_id and retry the action.'
    if (reason.includes('autopublish_not_allowed')) return 'Disable autopublish (or update policy/spec if intended) and retry.'
    if (reason.includes('metering_envelope')) return 'Verify trusted metering envelope is present/valid for budgeted calls.'
    if (reason.includes('monthly_budget_exceeded')) return 'Wait for the budget window reset or increase the plan budget.'
    return 'Review details + correlation_id, then retry with corrected inputs/policy.'
  }

  useEffect(() => {
    const abortController = new AbortController()
    void load(abortController.signal)
    return () => abortController.abort()
  }, [load])

  return (
    <div className="page-container">
      <div className="page-header">
        <Text as="h1" size={900} weight="semibold">Policy Denials</Text>
        <Body1>Audit log of Plant policy enforcement denials</Body1>
      </div>

      <Card>
        <CardHeader
          header={<Text weight="semibold">Denials</Text>}
          description={<Text size={200}>{isLoading ? 'Loading…' : data ? `${data.count} records` : '—'}</Text>}
          action={
            <Button appearance="subtle" size="small" onClick={() => void load()} disabled={isLoading}>
              Refresh
            </Button>
          }
        />

        <div style={{ padding: 16, display: 'grid', gap: 12, gridTemplateColumns: '1fr 1fr' }}>
          <div>
            <Text size={200} style={{ display: 'block', marginBottom: 6, opacity: 0.85 }}>Correlation ID</Text>
            <Input value={correlationId} onChange={(_, d) => setCorrelationId(d.value)} placeholder="corr-..." />
          </div>
          <div>
            <Text size={200} style={{ display: 'block', marginBottom: 6, opacity: 0.85 }}>Limit</Text>
            <Input value={limit} onChange={(_, d) => setLimit(d.value)} placeholder="100" />
          </div>
          <div>
            <Text size={200} style={{ display: 'block', marginBottom: 6, opacity: 0.85 }}>Customer ID</Text>
            <Input value={customerId} onChange={(_, d) => setCustomerId(d.value)} placeholder="CUST-..." />
          </div>
          <div>
            <Text size={200} style={{ display: 'block', marginBottom: 6, opacity: 0.85 }}>Agent ID</Text>
            <Input value={agentId} onChange={(_, d) => setAgentId(d.value)} placeholder="AGT-..." />
          </div>
        </div>

        {error && <div style={{ padding: 16 }}><ApiErrorPanel title="Policy denials error" error={error} /></div>}

        {!error && isLoading && (
          <div style={{ padding: 16 }}>
            <Spinner label="Loading policy denials..." />
          </div>
        )}

        <Table>
          <TableHeader>
            <TableRow>
              <TableHeaderCell>Created</TableHeaderCell>
              <TableHeaderCell>Correlation</TableHeaderCell>
              <TableHeaderCell>Decision</TableHeaderCell>
              <TableHeaderCell>Action</TableHeaderCell>
              <TableHeaderCell>Reason</TableHeaderCell>
              <TableHeaderCell>Path</TableHeaderCell>
            </TableRow>
          </TableHeader>
          <TableBody>
            {(data?.records || []).map((r, idx) => (
              <TableRow
                key={`${r.correlation_id}-${r.decision_id || 'no-decision'}-${idx}`}
                onClick={() => setSelected(r)}
                style={{ cursor: 'pointer' }}
              >
                <TableCell>{r.created_at ? new Date(r.created_at).toLocaleString() : '-'}</TableCell>
                <TableCell>{r.correlation_id}</TableCell>
                <TableCell>{r.decision_id || '-'}</TableCell>
                <TableCell>{r.action || '-'}</TableCell>
                <TableCell>{r.reason || '-'}</TableCell>
                <TableCell>{r.path || '-'}</TableCell>
              </TableRow>
            ))}

            {!isLoading && !error && (data?.records || []).length === 0 && (
              <TableRow>
                <TableCell colSpan={6}>
                  <Text>No policy denials returned.</Text>
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </Card>

      {selected && (
        <Card style={{ marginTop: 16 }}>
          <CardHeader header={<Text weight="semibold">Denial Details</Text>} />
          <div style={{ padding: 16, display: 'grid', gap: 10 }}>
            <Text size={200}>Correlation: {selected.correlation_id}</Text>
            <Text size={200}>Recommended next action: {recommendedNextAction(selected)}</Text>
            <div>
              <Text size={200} style={{ display: 'block', marginBottom: 6, opacity: 0.85 }}>Details JSON</Text>
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
                {JSON.stringify(selected.details || {}, null, 2)}
              </pre>
            </div>
          </div>
        </Card>
      )}
    </div>
  )
}
