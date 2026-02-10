import { useCallback, useMemo, useState } from 'react'
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

import ApiErrorPanel from '../components/ApiErrorPanel'
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

export default function HiredAgentsOps() {
  const [customerId, setCustomerId] = useState('')
  const [asOf, setAsOf] = useState('')

  const [rows, setRows] = useState<HiredRow[]>([])
  const [selected, setSelected] = useState<HiredRow | null>(null)

  const [deliverables, setDeliverables] = useState<Deliverable[]>([])
  const [approvals, setApprovals] = useState<ApprovalRecord[]>([])
  const [denials, setDenials] = useState<PolicyDenialRecord[]>([])

  const [correlationId, setCorrelationId] = useState('')
  const [selectedDenial, setSelectedDenial] = useState<PolicyDenialRecord | null>(null)

  const [isLoading, setIsLoading] = useState(false)
  const [isDetailLoading, setIsDetailLoading] = useState(false)
  const [error, setError] = useState<unknown>(null)

  const normalizedAsOf = useMemo(() => (asOf || '').trim() || undefined, [asOf])

  const load = useCallback(async () => {
    const cust = customerId.trim()
    if (!cust) return

    setIsLoading(true)
    setError(null)
    setSelected(null)
    setSelectedDenial(null)
    setRows([])
    setDeliverables([])
    setApprovals([])
    setDenials([])

    try {
      const subs = (await gatewayApiClient.listSubscriptionsByCustomer(cust)) as Subscription[]

      const hiredInstances = await Promise.all(
        (subs || []).map(async (s) => {
          const hired = (await gatewayApiClient.getHiredAgentBySubscription(s.subscription_id, {
            customer_id: cust,
            as_of: normalizedAsOf
          })) as HiredAgentInstance

          const goalsRes = (await gatewayApiClient.listGoalsForHiredInstance(hired.hired_instance_id, {
            customer_id: cust,
            as_of: normalizedAsOf
          })) as GoalsListResponse

          return {
            subscription_id: s.subscription_id,
            hired,
            goals: (goalsRes?.goals || [])
          } satisfies HiredRow
        })
      )

      const sorted = hiredInstances
        .filter(r => !!r?.hired?.hired_instance_id)
        .sort((a, b) => (a.hired.created_at || '').localeCompare(b.hired.created_at || ''))

      setRows(sorted)
    } catch (e: any) {
      setError(e)
    } finally {
      setIsLoading(false)
    }
  }, [customerId, normalizedAsOf])

  const loadDetails = useCallback(async (row: HiredRow, opts?: { correlation_id?: string }) => {
    const cust = customerId.trim()
    if (!cust) return

    setIsDetailLoading(true)
    setError(null)
    setSelectedDenial(null)
    try {
      const corr = (opts?.correlation_id ?? correlationId).trim() || undefined

      const [deliverablesRes, approvalsRes, denialsRes] = await Promise.all([
        gatewayApiClient.listDeliverablesForHiredInstance(row.hired.hired_instance_id, {
          customer_id: cust,
          as_of: normalizedAsOf
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
  }, [customerId, correlationId, normalizedAsOf])

  const goalSummary = (goals: GoalInstance[]): string => {
    if (!goals.length) return '—'
    return goals
      .slice(0, 3)
      .map(g => `${g.goal_template_id} (${g.frequency})`)
      .join(', ') + (goals.length > 3 ? ` +${goals.length - 3} more` : '')
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <Text as="h1" size={900} weight="semibold">Hired Agents</Text>
        <Body1>Ops view of customer hired agents, goals, drafts, approvals and denials</Body1>
      </div>

      {!!error && <ApiErrorPanel title="Hired Agents error" error={error} />}

      <Card>
        <CardHeader
          header={<Text weight="semibold">Load customer</Text>}
          description={<Text size={200}>{isLoading ? 'Loading…' : rows.length ? `${rows.length} instances` : '—'}</Text>}
          action={<Button appearance="primary" onClick={() => void load()} disabled={isLoading || !customerId.trim()}>Load</Button>}
        />

        <div style={{ padding: 16, display: 'flex', gap: 12, flexWrap: 'wrap', alignItems: 'end' }}>
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
            </TableRow>
          </TableHeader>
          <TableBody>
            {rows.map(r => (
              <TableRow
                key={r.hired.hired_instance_id}
                onClick={() => {
                  setSelected(r)
                  setCorrelationId('')
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
              </TableRow>
            ))}

            {!isLoading && rows.length === 0 && (
              <TableRow>
                <TableCell colSpan={6}><Text>No hired agent instances loaded.</Text></TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </Card>

      {selected && (
        <>
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
    </div>
  )
}
