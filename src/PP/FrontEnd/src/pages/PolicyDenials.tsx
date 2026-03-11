import { useCallback, useEffect, useRef, useState } from 'react'
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
import { useNavigate, useSearchParams } from 'react-router-dom'
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

function buildPolicyDenialsSearch(filters: {
  correlationId?: string
  customerId?: string
  agentId?: string
  limit?: string
}): URLSearchParams {
  const params = new URLSearchParams()
  const values: Record<string, string | undefined> = {
    correlation_id: filters.correlationId?.trim(),
    customer_id: filters.customerId?.trim(),
    agent_id: filters.agentId?.trim(),
    limit: filters.limit?.trim(),
  }

  Object.entries(values).forEach(([key, value]) => {
    if (value) params.set(key, value)
  })

  return params
}

export default function PolicyDenials() {
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  const initialContextLoadRef = useRef(
    Boolean(searchParams.get('correlation_id') || searchParams.get('customer_id') || searchParams.get('agent_id'))
  )

  const [correlationId, setCorrelationId] = useState(() => searchParams.get('correlation_id') || '')
  const [customerId, setCustomerId] = useState(() => searchParams.get('customer_id') || '')
  const [agentId, setAgentId] = useState(() => searchParams.get('agent_id') || '')
  const [limit, setLimit] = useState(() => searchParams.get('limit') || '100')

  const [selected, setSelected] = useState<PolicyDenialRecord | null>(null)
  const [hasLoaded, setHasLoaded] = useState(false)

  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<unknown>(null)
  const [data, setData] = useState<PolicyDenialsResponse | null>(null)

  const syncFilters = useCallback((overrides?: Partial<{
    correlationId: string
    customerId: string
    agentId: string
    limit: string
  }>) => {
    setSearchParams(buildPolicyDenialsSearch({
      correlationId: overrides?.correlationId ?? correlationId,
      customerId: overrides?.customerId ?? customerId,
      agentId: overrides?.agentId ?? agentId,
      limit: overrides?.limit ?? limit,
    }), { replace: true })
  }, [agentId, correlationId, customerId, limit, setSearchParams])

  const load = useCallback(async (signal?: AbortSignal) => {
    syncFilters()
    setIsLoading(true)
    setError(null)
    try {
      const response = (await gatewayApiClient.listPolicyDenials({
        correlation_id: correlationId.trim() || undefined,
        customer_id: customerId.trim() || undefined,
        agent_id: agentId.trim() || undefined,
        limit: Number(limit) || 100
      })) as PolicyDenialsResponse
      setHasLoaded(true)
      setData(response)
      setSelected(null)
    } catch (e: any) {
      if (e?.name === 'AbortError' || signal?.aborted) return
      setError(e)
      setData(null)
      setSelected(null)
      setHasLoaded(true)
    } finally {
      setIsLoading(false)
    }
  }, [agentId, correlationId, customerId, limit, syncFilters])

  useEffect(() => {
    if (!initialContextLoadRef.current) return
    initialContextLoadRef.current = false
    void load()
  }, [load])

  const recommendedNextAction = (rec: PolicyDenialRecord): string => {
    const reason = (rec.reason || '').toLowerCase()
    if (reason.includes('approval_required')) return 'Provide approval_id and retry the action.'
    if (reason.includes('autopublish_not_allowed')) return 'Disable autopublish (or update policy/spec if intended) and retry.'
    if (reason.includes('metering_envelope')) return 'Verify trusted metering envelope is present/valid for budgeted calls.'
    if (reason.includes('monthly_budget_exceeded')) return 'Wait for the budget window reset or increase the plan budget.'
    return 'Review details + correlation_id, then retry with corrected inputs/policy.'
  }

  const denialContext = buildPolicyDenialsSearch({ correlationId, customerId, agentId, limit })
  const denialContextString = denialContext.toString()
  const activeContext = selected || (customerId.trim() || agentId.trim() || correlationId.trim()
    ? {
        correlation_id: correlationId.trim(),
        customer_id: customerId.trim(),
        agent_id: agentId.trim(),
      }
    : null)

  return (
    <div className="page-container">
      <div className="page-header">
        <Text as="h1" size={900} weight="semibold">Policy Denials</Text>
        <Body1>Audit log of Plant policy enforcement denials</Body1>
      </div>

      <div className="pp-dashboard-grid" style={{ marginBottom: 20 }}>
        <Card className="pp-dashboard-panel pp-dashboard-panel--accent">
          <div className="pp-dashboard-kicker">Governance signal</div>
          <Text as="h2" size={700} weight="semibold">Explain why the platform said no.</Text>
          <p className="pp-dashboard-body-copy">
            Policy denials should help ops, infra, and governance contributors diagnose intent, policy, and input mistakes fast enough to unblock the right action.
          </p>
        </Card>
        <Card className="pp-dashboard-panel">
          <Text as="h3" size={600} weight="semibold">Useful denial UX</Text>
          <p className="pp-dashboard-body-copy">
            Show the denial, the likely fix, and the correlation path clearly enough that a helpdesk person can route or explain it without escalation roulette.
          </p>
        </Card>
      </div>

      <Card>
        <CardHeader
          header={<Text weight="semibold">Denials</Text>}
          description={<Text size={200}>{isLoading ? 'Loading…' : data ? `${data.count} records` : '—'}</Text>}
          action={
            <Button appearance="subtle" size="small" onClick={() => void load()} disabled={isLoading}>
              {hasLoaded ? 'Refresh' : 'Load denials'}
            </Button>
          }
        />

        <div style={{ padding: 16, display: 'grid', gap: 12, gridTemplateColumns: '1fr 1fr' }}>
          <Text size={200} style={{ gridColumn: '1 / -1', opacity: 0.8 }}>
            Search by correlation, customer, or agent to reconstruct the denial storyline before recommending a retry.
          </Text>
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

        {activeContext && (
          <div style={{ padding: 16, paddingTop: 0 }}>
            <Card className="pp-agent-setup-card">
              <Text weight="semibold">Operator handoff context</Text>
              <Text size={200} style={{ display: 'block', marginTop: 8, opacity: 0.8 }}>
                What happened: this denial search is scoped to correlation {activeContext.correlation_id || 'not set'}, customer {activeContext.customer_id || 'not set'}, and agent {activeContext.agent_id || 'not set'}.
              </Text>
              <Text size={200} style={{ display: 'block', marginTop: 8, opacity: 0.8 }}>
                What next: inspect the denial details here, then jump straight to hired runtime or the draft review queue with the same filters.
              </Text>
              <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginTop: 12 }}>
                <Button
                  appearance="secondary"
                  disabled={!activeContext.customer_id}
                  onClick={() => navigate(`/hired-agents?${denialContextString}`)}
                >
                  Open Hired Agents
                </Button>
                <Button
                  appearance="secondary"
                  disabled={!activeContext.customer_id && !activeContext.agent_id}
                  onClick={() => navigate(`/review-queue?${buildPolicyDenialsSearch({ customerId, agentId }).toString()}`)}
                >
                  Open Draft Review
                </Button>
              </div>
            </Card>
          </div>
        )}

        {!error && !isLoading && !hasLoaded && (
          <div style={{ padding: 16 }}>
            <Card className="pp-agent-setup-card">
              <Text weight="semibold">Run a targeted denial search</Text>
              <Text size={200} style={{ display: 'block', marginTop: 8, opacity: 0.8 }}>
                Start with a correlation id, customer, or agent when possible so the first result set is operationally useful instead of noisy.
              </Text>
            </Card>
          </div>
        )}

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
                onClick={() => {
                  setSelected(r)
                  syncFilters({
                    correlationId: r.correlation_id || correlationId,
                    customerId: r.customer_id || customerId,
                    agentId: r.agent_id || agentId,
                  })
                }}
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

            {!isLoading && !error && hasLoaded && (data?.records || []).length === 0 && (
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
            <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
              <Button
                appearance="secondary"
                disabled={!((selected.customer_id || customerId).trim())}
                onClick={() => navigate(`/hired-agents?${buildPolicyDenialsSearch({
                  customerId: selected.customer_id || customerId,
                  agentId: selected.agent_id || agentId,
                  correlationId: selected.correlation_id,
                }).toString()}`)}
              >
                Open hired agent runtime
              </Button>
              <Button
                appearance="secondary"
                disabled={!((selected.customer_id || customerId).trim()) && !((selected.agent_id || agentId).trim())}
                onClick={() => navigate(`/review-queue?${buildPolicyDenialsSearch({
                  customerId: selected.customer_id || customerId,
                  agentId: selected.agent_id || agentId,
                }).toString()}`)}
              >
                Open draft review
              </Button>
            </div>
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
