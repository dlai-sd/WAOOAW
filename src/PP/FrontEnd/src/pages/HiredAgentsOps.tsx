import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import {
  Body1,
  Button,
  Card,
  CardHeader,
  Field,
  Input,
  Spinner,
  Table,
  TableBody,
  TableCell,
  TableHeader,
  TableHeaderCell,
  TableRow,
  Text
} from '@fluentui/react-components'
import { useNavigate, useSearchParams } from 'react-router-dom'

import ApiErrorPanel from '../components/ApiErrorPanel'
import ConstructHealthPanel from '../components/ConstructHealthPanel'
import SchedulerDiagnosticsPanel from '../components/SchedulerDiagnosticsPanel'
import HookTracePanel from '../components/HookTracePanel'
import { gatewayApiClient } from '../services/gatewayApiClient'

type Subscription = {
  subscription_id: string
  agent_id?: string | null
  status?: string | null
  duration?: string | null
}

type GoalInstance = {
  goal_instance_id: string
  goal_template_id: string
  frequency: string
  settings?: Record<string, unknown>
  created_at?: string
  updated_at?: string
}

type GoalsListResponse = {
  hired_instance_id: string
  goals: GoalInstance[]
}

type HiredAgentInstance = {
  hired_instance_id: string
  subscription_id: string
  agent_id: string
  agent_type_id?: string | null
  configured?: boolean
  goals_completed?: boolean
  active?: boolean
  trial_status?: string
  nickname?: string | null
  theme?: string | null
  config?: Record<string, unknown>
  created_at?: string
  updated_at?: string
}

type Deliverable = {
  deliverable_id: string
  created_at?: string
  goal_template_id?: string | null
  frequency?: string | null
  review_status?: string | null
  approval_id?: string | null
  execution_status?: string | null
}

type DeliverablesListResponse = {
  hired_instance_id: string
  deliverables: Deliverable[]
}

type ApprovalRecord = {
  approval_id: string
  customer_id: string
  agent_id: string
  action: string
  correlation_id?: string | null
  created_at?: string
  expires_at?: string | null
}

type ApprovalListResponse = {
  count: number
  approvals: ApprovalRecord[]
}

type PolicyDenialRecord = {
  created_at?: string
  correlation_id: string
  decision_id?: string | null
  agent_id?: string | null
  customer_id?: string | null
  action?: string | null
  reason?: string | null
  path?: string | null
  details?: Record<string, unknown>
}

type PolicyDenialsResponse = {
  count: number
  records: PolicyDenialRecord[]
}

type HiredRow = {
  subscription_id: string
  hired: HiredAgentInstance
  goals: GoalInstance[]
}

function buildHiredAgentsSearch(filters: {
  customerId?: string
  email?: string
  asOf?: string
  agentId?: string
  correlationId?: string
  selectedHiredInstanceId?: string
}): URLSearchParams {
  const params = new URLSearchParams()
  const values: Record<string, string | undefined> = {
    customer_id: filters.customerId?.trim(),
    email: filters.email?.trim(),
    as_of: filters.asOf?.trim(),
    agent_id: filters.agentId?.trim(),
    correlation_id: filters.correlationId?.trim(),
    selected_hired_instance_id: filters.selectedHiredInstanceId?.trim(),
  }

  Object.entries(values).forEach(([key, value]) => {
    if (value) params.set(key, value)
  })

  return params
}

export default function HiredAgentsOps() {
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  const initialContextLoadRef = useRef(Boolean(searchParams.get('customer_id') || searchParams.get('email')))

  const [customerId, setCustomerId] = useState(() => searchParams.get('customer_id') || '')
  const [asOf, setAsOf] = useState(() => searchParams.get('as_of') || '')
  const [email, setEmail] = useState(() => searchParams.get('email') || '')
  const [emailError, setEmailError] = useState<string | null>(null)

  const [rows, setRows] = useState<HiredRow[]>([])
  const [selected, setSelected] = useState<HiredRow | null>(null)

  const [deliverables, setDeliverables] = useState<Deliverable[]>([])
  const [approvals, setApprovals] = useState<ApprovalRecord[]>([])
  const [denials, setDenials] = useState<PolicyDenialRecord[]>([])

  const [correlationId, setCorrelationId] = useState(() => searchParams.get('correlation_id') || '')
  const [selectedDenial, setSelectedDenial] = useState<PolicyDenialRecord | null>(null)

  const [isLoading, setIsLoading] = useState(false)
  const [isDetailLoading, setIsDetailLoading] = useState(false)
  const [error, setError] = useState<unknown>(null)
  const [healthPanelAgentId, setHealthPanelAgentId] = useState<string | null>(null)
  const [detailTab, setDetailTab] = useState<'overview' | 'scheduler' | 'hooks'>('overview')

  const normalizedAsOf = useMemo(() => (asOf || '').trim() || undefined, [asOf])
  const requestedAgentId = (searchParams.get('agent_id') || '').trim()
  const requestedSelectedHiredInstanceId = (searchParams.get('selected_hired_instance_id') || '').trim()

  const syncContext = useCallback((overrides?: Partial<{
    customerId: string
    email: string
    asOf: string
    agentId: string
    correlationId: string
    selectedHiredInstanceId: string
  }>) => {
    setSearchParams(buildHiredAgentsSearch({
      customerId: overrides?.customerId ?? customerId,
      email: overrides?.email ?? email,
      asOf: overrides?.asOf ?? asOf,
      agentId: overrides?.agentId ?? requestedAgentId,
      correlationId: overrides?.correlationId ?? correlationId,
      selectedHiredInstanceId: overrides?.selectedHiredInstanceId ?? requestedSelectedHiredInstanceId,
    }), { replace: true })
  }, [asOf, correlationId, customerId, email, requestedAgentId, requestedSelectedHiredInstanceId, setSearchParams])

  const lookupByEmail = useCallback(async () => {
    const e = email.trim()
    if (!e) return
    setEmailError(null)
    try {
      const result = await gatewayApiClient.lookupCustomerByEmail(e) as { customer_id: string }
      setCustomerId(result.customer_id)
      syncContext({ customerId: result.customer_id, email: e })
    } catch {
      setEmailError('Customer not found for this email address.')
    }
  }, [email, syncContext])

  const load = useCallback(async () => {
    const cust = customerId.trim()
    if (!cust) return

    syncContext({ customerId: cust, email, asOf, selectedHiredInstanceId: '', correlationId: '' })

    setIsLoading(true)
    setError(null)
    setSelected(null)
    setSelectedDenial(null)
    setRows([])
    setDeliverables([])
    setApprovals([])
    setDenials([])

    try {
      // Use new dedicated ops routes (not the catch-all /v1/ proxy)
      const subs = (await gatewayApiClient.listOpsSubscriptions({
        customer_id: cust,
        as_of: normalizedAsOf,
      })) as Subscription[]

      const hiredInstances = await Promise.all(
        (subs || []).map(async (s) => {
          // Ops list endpoint returns an array; take first matching instance
          const hiredArr = (await gatewayApiClient.listOpsHiredAgents({
            subscription_id: s.subscription_id,
            customer_id: cust,
            as_of: normalizedAsOf,
          })) as HiredAgentInstance[]
          const hired = hiredArr?.[0]
          if (!hired?.hired_instance_id) return null

          const goalsRes = (await gatewayApiClient.listOpsHiredAgentGoals(
            hired.hired_instance_id,
            { customer_id: cust, as_of: normalizedAsOf }
          )) as GoalsListResponse

          return {
            subscription_id: s.subscription_id,
            hired,
            goals: goalsRes?.goals || [],
          } satisfies HiredRow
        })
      )

      const sorted = hiredInstances
        .filter((r): r is HiredRow => !!r?.hired?.hired_instance_id)
        .sort((a, b) => (a.hired.created_at || '').localeCompare(b.hired.created_at || ''))

      setRows(sorted)
    } catch (e: any) {
      setError(e)
    } finally {
      setIsLoading(false)
    }
  }, [asOf, customerId, email, normalizedAsOf, syncContext])

  const loadDetails = useCallback(async (row: HiredRow, opts?: { correlation_id?: string }) => {
    const cust = customerId.trim()
    if (!cust) return

    setIsDetailLoading(true)
    setError(null)
    setSelectedDenial(null)
    try {
      const corr = (opts?.correlation_id ?? correlationId).trim() || undefined
      syncContext({
        customerId: cust,
        email,
        asOf,
        agentId: row.hired.agent_id,
        selectedHiredInstanceId: row.hired.hired_instance_id,
        correlationId: corr || '',
      })

      const [deliverablesRes, approvalsRes, denialsRes] = await Promise.all([
        gatewayApiClient.listOpsHiredAgentDeliverables(row.hired.hired_instance_id, {
          customer_id: cust,
          as_of: normalizedAsOf,
        }) as Promise<unknown>,
        gatewayApiClient.listApprovals({
          customer_id: cust,
          agent_id: row.hired.agent_id,
          correlation_id: corr,
          limit: 200
        }) as Promise<unknown>,
        gatewayApiClient.listPolicyDenials({
          correlation_id: corr,
          customer_id: cust,
          agent_id: row.hired.agent_id,
          limit: 200
        }) as Promise<unknown>
      ])

      const d = (deliverablesRes as DeliverablesListResponse)?.deliverables || []
      setDeliverables(d)

      const a = (approvalsRes as ApprovalListResponse)?.approvals || []
      setApprovals(a)

      const p = (denialsRes as PolicyDenialsResponse)?.records || []
      setDenials(p)
    } catch (e: any) {
      setError(e)
    } finally {
      setIsDetailLoading(false)
    }
  }, [asOf, correlationId, customerId, email, normalizedAsOf, syncContext])

  useEffect(() => {
    if (!initialContextLoadRef.current) return
    initialContextLoadRef.current = false
    void load()
  }, [load])

  useEffect(() => {
    if (!rows.length || selected) return

    const rowFromContext = rows.find(r => r.hired.hired_instance_id === requestedSelectedHiredInstanceId)
      || rows.find(r => requestedAgentId && r.hired.agent_id === requestedAgentId)

    if (!rowFromContext) return

    setSelected(rowFromContext)
    void loadDetails(rowFromContext, {
      correlation_id: (searchParams.get('correlation_id') || '').trim() || undefined,
    })
  }, [loadDetails, requestedAgentId, requestedSelectedHiredInstanceId, rows, searchParams, selected])

  const goalSummary = (goals: GoalInstance[]): string => {
    if (!goals.length) return '—'
    return goals
      .slice(0, 3)
      .map(g => `${g.goal_template_id} (${g.frequency})`)
      .join(', ') + (goals.length > 3 ? ` +${goals.length - 3} more` : '')
  }

  const handoffContext = selected
    ? buildHiredAgentsSearch({
        customerId,
        email,
        asOf,
        agentId: selected.hired.agent_id,
        correlationId,
        selectedHiredInstanceId: selected.hired.hired_instance_id,
      }).toString()
    : ''

  return (
    <div className="page-container">
      <div className="page-header">
        <Text as="h1" size={900} weight="semibold">Hired Agents</Text>
        <Body1>Ops view of customer hired agents, goals, drafts, approvals and denials</Body1>
      </div>

      <div className="pp-dashboard-grid" style={{ marginBottom: 20 }}>
        <Card className="pp-dashboard-panel pp-dashboard-panel--accent">
          <div className="pp-dashboard-kicker">Ops mission</div>
          <Text as="h2" size={700} weight="semibold">Find customer risk before it becomes a support incident.</Text>
          <p className="pp-dashboard-body-copy">
            This screen should help helpdesk and ops contributors connect hires, goals, approvals, denials, and runtime health
            without forcing them to mentally stitch five systems together.
          </p>
        </Card>
        <div className="pp-agent-setup-summary-grid">
          <Card className="pp-agent-setup-card">
            <div className="pp-agent-setup-metric">1</div>
            <div className="pp-agent-setup-label">Customer storyline per row</div>
          </Card>
          <Card className="pp-agent-setup-card">
            <div className="pp-agent-setup-metric">Ops</div>
            <div className="pp-agent-setup-label">Approvals, denials, diagnostics</div>
          </Card>
          <Card className="pp-agent-setup-card">
            <div className="pp-agent-setup-metric">Fast</div>
            <div className="pp-agent-setup-label">Email lookup to runtime detail</div>
          </Card>
        </div>
      </div>

      {!!error && <ApiErrorPanel title="Hired Agents error" error={error} />}

      <Card>
        <CardHeader
          header={<Text weight="semibold">Load customer</Text>}
          description={<Text size={200}>{isLoading ? 'Loading…' : rows.length ? `${rows.length} instances` : '—'}</Text>}
          action={<Button appearance="primary" onClick={() => void load()} disabled={isLoading || !customerId.trim()}>Load</Button>}
        />

        <div style={{ padding: 16, display: 'flex', gap: 12, flexWrap: 'wrap', alignItems: 'end' }}>
          <Text size={200} style={{ width: '100%', opacity: 0.8 }}>
            Start from what ops usually has in hand: an email, a customer id, or a point-in-time incident report.
          </Text>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            <div style={{ display: 'flex', gap: 8, alignItems: 'flex-end' }}>
              <Field label="Customer Email">
                <Input
                  placeholder="email@example.com"
                  value={email}
                  onChange={(_, d) => setEmail(d.value)}
                />
              </Field>
              <Button appearance="secondary" onClick={() => void lookupByEmail()}>Lookup</Button>
            </div>
            {emailError && <Text style={{ color: 'var(--colorPaletteRedForeground1)', fontSize: 12 }}>{emailError}</Text>}
          </div>
          <Field label="Customer ID">
            <Input value={customerId} onChange={(_, d) => setCustomerId(d.value)} placeholder="CUST-..." />
          </Field>
          <Field label="as_of (ISO 8601, optional)">
            <Input value={asOf} onChange={(_, d) => setAsOf(d.value)} placeholder="2026-02-10T00:00:00Z" />
          </Field>
        </div>
      </Card>

      <Card style={{ marginTop: 16 }}>
        <CardHeader header={<Text weight="semibold">Instances</Text>} />
        {isLoading && (
          <div style={{ padding: 16 }}>
            <Spinner label="Loading hired agents..." />
          </div>
        )}
        <Table>
          <TableHeader>
            <TableRow>
              <TableHeaderCell>Hired</TableHeaderCell>
              <TableHeaderCell>Agent</TableHeaderCell>
              <TableHeaderCell>Subscription</TableHeaderCell>
              <TableHeaderCell>Trial</TableHeaderCell>
              <TableHeaderCell>Configured</TableHeaderCell>
              <TableHeaderCell>Goals</TableHeaderCell>
              <TableHeaderCell>Actions</TableHeaderCell>
            </TableRow>
          </TableHeader>
          <TableBody>
            {rows.map(r => (
              <TableRow
                key={r.hired.hired_instance_id}
                onClick={() => {
                  setSelected(r)
                  setCorrelationId('')
                  syncContext({
                    customerId,
                    email,
                    asOf,
                    agentId: r.hired.agent_id,
                    selectedHiredInstanceId: r.hired.hired_instance_id,
                    correlationId: '',
                  })
                  void loadDetails(r)
                }}
                style={{ cursor: 'pointer' }}
              >
                <TableCell>{r.hired.hired_instance_id}</TableCell>
                <TableCell>{r.hired.agent_id}</TableCell>
                <TableCell>{r.subscription_id}</TableCell>
                <TableCell>{r.hired.trial_status || '—'}</TableCell>
                <TableCell>{r.hired.configured ? 'yes' : 'no'}</TableCell>
                <TableCell>{goalSummary(r.goals)}</TableCell>
                <TableCell>
                  <Button
                    appearance="subtle"
                    size="small"
                    title="View construct health"
                    aria-label="Construct health"
                    onClick={(e) => {
                      e.stopPropagation()
                      setHealthPanelAgentId(r.hired.hired_instance_id)
                    }}
                  >
                    🩺 Health
                  </Button>
                </TableCell>
              </TableRow>
            ))}

            {!isLoading && rows.length === 0 && (
              <TableRow>
                <TableCell colSpan={7}><Text>No hired agent instances loaded.</Text></TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </Card>

      {!selected && !isLoading && rows.length > 0 && (
        <Card style={{ marginTop: 16, padding: 20 }}>
          <Text weight="semibold">Select an instance to inspect the customer runtime story</Text>
          <Text size={200} style={{ display: 'block', marginTop: 8, opacity: 0.8 }}>
            Pick one hired agent row to inspect config, goals, approvals, denials, scheduler diagnostics, and hook trace in one place.
          </Text>
        </Card>
      )}

      {healthPanelAgentId && (
        <ConstructHealthPanel
          hiredAgentId={healthPanelAgentId}
          isOpen={true}
          onClose={() => setHealthPanelAgentId(null)}
        />
      )}

      {selected && (
        <>
          <Card style={{ marginTop: 16 }}>
            <CardHeader
              header={<Text weight="semibold">Operator handoff context</Text>}
              description={<Text size={200}>Customer {customerId.trim()} • Agent {selected.hired.agent_id} • Runtime {selected.hired.hired_instance_id}</Text>}
            />
            <div style={{ padding: 16, display: 'flex', flexDirection: 'column', gap: 10 }}>
              <Text size={200}>What happened: the hired runtime, approvals, denials, and diagnostics are pinned to the selected customer storyline.</Text>
              <Text size={200}>What next: inspect deliverables here, jump to draft review to unblock content, or open policy denials with the same runtime context.</Text>
              <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
                <Button
                  appearance="secondary"
                  onClick={() => navigate(`/review-queue?${buildHiredAgentsSearch({
                    customerId,
                    agentId: selected.hired.agent_id,
                    correlationId,
                  }).toString()}`)}
                >
                  Open Review Queue
                </Button>
                <Button
                  appearance="secondary"
                  onClick={() => navigate(`/policy-denials?${handoffContext}`)}
                >
                  Open Policy Denials
                </Button>
              </div>
            </div>
          </Card>

          <Card style={{ marginTop: 16 }}>
            <CardHeader
              header={<Text weight="semibold">Selected instance</Text>}
              description={<Text size={200}>{selected.hired.hired_instance_id} • {selected.hired.agent_id}</Text>}
              action={
                <Button
                  appearance="subtle"
                  onClick={() => void loadDetails(selected)}
                  disabled={isDetailLoading}
                >
                  Refresh
                </Button>
              }
            />

            <div style={{ padding: 16, display: 'grid', gap: 12, gridTemplateColumns: '1fr 1fr' }}>
              <div style={{ gridColumn: '1 / -1', display: 'grid', gap: 12, gridTemplateColumns: 'repeat(4, minmax(0, 1fr))' }}>
                <Card className="pp-agent-setup-card">
                  <div className="pp-agent-setup-metric">{selected.goals.length}</div>
                  <div className="pp-agent-setup-label">Goals</div>
                </Card>
                <Card className="pp-agent-setup-card">
                  <div className="pp-agent-setup-metric">{deliverables.length}</div>
                  <div className="pp-agent-setup-label">Deliverables</div>
                </Card>
                <Card className="pp-agent-setup-card">
                  <div className="pp-agent-setup-metric">{approvals.length}</div>
                  <div className="pp-agent-setup-label">Approvals</div>
                </Card>
                <Card className="pp-agent-setup-card">
                  <div className="pp-agent-setup-metric">{denials.length}</div>
                  <div className="pp-agent-setup-label">Policy denials</div>
                </Card>
              </div>
              <div>
                <Text size={200} style={{ display: 'block', marginBottom: 6, opacity: 0.85 }}>Correlation ID (optional)</Text>
                <Input
                  value={correlationId}
                  onChange={(_, d) => setCorrelationId(d.value)}
                  placeholder="corr-..."
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') void loadDetails(selected)
                  }}
                />
              </div>
              <div style={{ display: 'flex', alignItems: 'end', gap: 12 }}>
                <Button
                  appearance="secondary"
                  disabled={isDetailLoading}
                  onClick={() => void loadDetails(selected)}
                >
                  Apply correlation filter
                </Button>
              </div>
            </div>
          </Card>

          {isDetailLoading && (
            <div style={{ padding: 16 }}>
              <Spinner label="Loading instance details..." />
            </div>
          )}

          <div style={{ marginTop: 16, display: 'flex', gap: 8, borderBottom: '1px solid rgba(255,255,255,0.1)', paddingBottom: 8 }}>
            <Button
              appearance={detailTab === 'overview' ? 'primary' : 'subtle'}
              onClick={() => setDetailTab('overview')}
            >
              Overview
            </Button>
            <Button
              appearance={detailTab === 'scheduler' ? 'primary' : 'subtle'}
              onClick={() => setDetailTab('scheduler')}
            >
              Scheduler
            </Button>
            <Button
              appearance={detailTab === 'hooks' ? 'primary' : 'subtle'}
              onClick={() => setDetailTab('hooks')}
            >
              Hook Trace
            </Button>
          </div>

          {detailTab === 'scheduler' && (
            <div style={{ marginTop: 16 }}>
              <SchedulerDiagnosticsPanel
                hiredAgentId={selected.hired.hired_instance_id}
                isAdmin={false}
              />
            </div>
          )}

          {detailTab === 'hooks' && (
            <div style={{ marginTop: 16 }}>
              <HookTracePanel hiredAgentId={selected.hired.hired_instance_id} />
            </div>
          )}

          {detailTab === 'overview' && (
            <>
          <Card style={{ marginTop: 16 }}>
            <CardHeader header={<Text weight="semibold">Config</Text>} />
            <div style={{ padding: 16 }}>
              <pre style={{ margin: 0, overflowX: 'auto' }}>
                {JSON.stringify(selected.hired.config || {}, null, 2)}
              </pre>
            </div>
          </Card>

          <Card style={{ marginTop: 16 }}>
            <CardHeader header={<Text weight="semibold">Goals</Text>} description={<Text size={200}>{selected.goals.length} goals</Text>} />
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHeaderCell>Goal</TableHeaderCell>
                  <TableHeaderCell>Template</TableHeaderCell>
                  <TableHeaderCell>Frequency</TableHeaderCell>
                </TableRow>
              </TableHeader>
              <TableBody>
                {selected.goals.map(g => (
                  <TableRow key={g.goal_instance_id}>
                    <TableCell>{g.goal_instance_id}</TableCell>
                    <TableCell>{g.goal_template_id}</TableCell>
                    <TableCell>{g.frequency}</TableCell>
                  </TableRow>
                ))}
                {selected.goals.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={3}><Text>No goals configured.</Text></TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </Card>

          <Card style={{ marginTop: 16 }}>
            <CardHeader header={<Text weight="semibold">Drafts (Deliverables)</Text>} description={<Text size={200}>{deliverables.length} deliverables</Text>} />
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHeaderCell>Deliverable</TableHeaderCell>
                  <TableHeaderCell>Template</TableHeaderCell>
                  <TableHeaderCell>Review</TableHeaderCell>
                  <TableHeaderCell>Approval</TableHeaderCell>
                  <TableHeaderCell>Execution</TableHeaderCell>
                </TableRow>
              </TableHeader>
              <TableBody>
                {deliverables.map(d => (
                  <TableRow key={d.deliverable_id}>
                    <TableCell>{d.deliverable_id}</TableCell>
                    <TableCell>{d.goal_template_id || '—'}</TableCell>
                    <TableCell>{d.review_status || '—'}</TableCell>
                    <TableCell>{d.approval_id || '—'}</TableCell>
                    <TableCell>{d.execution_status || '—'}</TableCell>
                  </TableRow>
                ))}
                {deliverables.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={5}><Text>No deliverables returned.</Text></TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </Card>

          <Card style={{ marginTop: 16 }}>
            <CardHeader header={<Text weight="semibold">Approvals</Text>} description={<Text size={200}>{approvals.length} approvals</Text>} />
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHeaderCell>Approval</TableHeaderCell>
                  <TableHeaderCell>Action</TableHeaderCell>
                  <TableHeaderCell>Correlation</TableHeaderCell>
                  <TableHeaderCell>Created</TableHeaderCell>
                </TableRow>
              </TableHeader>
              <TableBody>
                {approvals.map(a => (
                  <TableRow key={a.approval_id}>
                    <TableCell>{a.approval_id}</TableCell>
                    <TableCell>{a.action}</TableCell>
                    <TableCell>{a.correlation_id || '—'}</TableCell>
                    <TableCell>{a.created_at ? new Date(a.created_at).toLocaleString() : '—'}</TableCell>
                  </TableRow>
                ))}
                {approvals.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={4}><Text>No approvals returned.</Text></TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </Card>

          <Card style={{ marginTop: 16 }}>
            <CardHeader header={<Text weight="semibold">Policy Denials</Text>} description={<Text size={200}>{denials.length} denials</Text>} />
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHeaderCell>Created</TableHeaderCell>
                  <TableHeaderCell>Correlation</TableHeaderCell>
                  <TableHeaderCell>Action</TableHeaderCell>
                  <TableHeaderCell>Reason</TableHeaderCell>
                  <TableHeaderCell>Path</TableHeaderCell>
                </TableRow>
              </TableHeader>
              <TableBody>
                {denials.map((r, idx) => (
                  <TableRow
                    key={`${r.correlation_id}-${r.decision_id || 'no-decision'}-${idx}`}
                    onClick={() => {
                      setSelectedDenial(r)
                      setCorrelationId(r.correlation_id)
                      void loadDetails(selected, { correlation_id: r.correlation_id })
                    }}
                    style={{ cursor: 'pointer' }}
                  >
                    <TableCell>{r.created_at ? new Date(r.created_at).toLocaleString() : '—'}</TableCell>
                    <TableCell>{r.correlation_id}</TableCell>
                    <TableCell>{r.action || '—'}</TableCell>
                    <TableCell>{r.reason || '—'}</TableCell>
                    <TableCell>{r.path || '—'}</TableCell>
                  </TableRow>
                ))}
                {denials.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={5}><Text>No policy denials returned.</Text></TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </Card>

          {selectedDenial && (
            <Card style={{ marginTop: 16 }}>
              <CardHeader header={<Text weight="semibold">Denial details</Text>} description={<Text size={200}>{selectedDenial.correlation_id}</Text>} />
              <div style={{ padding: 16 }}>
                <pre style={{ margin: 0, overflowX: 'auto' }}>
                  {JSON.stringify(selectedDenial.details || {}, null, 2)}
                </pre>
              </div>
            </Card>
          )}
            </>
          )}
        </>
      )}
    </div>
  )
}
