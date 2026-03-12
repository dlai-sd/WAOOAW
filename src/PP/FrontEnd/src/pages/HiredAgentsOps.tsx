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
  updated_at?: string
  goal_template_id?: string | null
  frequency?: string | null
  review_status?: string | null
  approval_id?: string | null
  execution_status?: string | null
  payload?: Record<string, unknown> | null
}

type DeliverablesListResponse = {
  hired_instance_id: string
  deliverables: Deliverable[]
}

type GoalSchemaField = {
  key: string
  label: string
  required?: boolean
}

type AgentSkill = {
  skill_id: string
  name?: string | null
  display_name?: string | null
  goal_schema?: {
    fields?: GoalSchemaField[]
  } | null
  goal_config?: Record<string, unknown> | null
}

type PlatformConnection = {
  id?: string
  platform_key: string
  status?: string | null
  last_verified_at?: string | null
  created_at?: string | null
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

type PlatformConnectionSummary = {
  label: string
  message: string
  tone: 'success' | 'warning' | 'danger' | 'informative'
  isReady: boolean
}

type PublishReadiness = {
  label: string
  message: string
  tone: 'success' | 'warning' | 'danger' | 'informative'
  owner: 'customer' | 'platform' | 'ready' | 'published'
}

function asRecord(value: unknown): Record<string, unknown> | null {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return null
  return value as Record<string, unknown>
}

function stringOrNull(value: unknown): string | null {
  const normalized = String(value ?? '').trim()
  return normalized ? normalized : null
}

function booleanFromUnknown(value: unknown): boolean {
  if (typeof value === 'boolean') return value
  const normalized = String(value ?? '').trim().toLowerCase()
  return normalized === 'true' || normalized === '1' || normalized === 'yes'
}

function hasValue(value: unknown): boolean {
  if (Array.isArray(value)) return value.length > 0
  if (value && typeof value === 'object') return Object.keys(value as Record<string, unknown>).length > 0
  return String(value ?? '').trim().length > 0
}

function formatBriefValue(value: unknown): string {
  if (Array.isArray(value)) return value.join(', ')
  if (value && typeof value === 'object') {
    try {
      return JSON.stringify(value)
    } catch {
      return 'Structured response captured'
    }
  }
  return String(value ?? '').trim()
}

function isDigitalMarketingAgent(agentId?: string | null, agentTypeId?: string | null): boolean {
  return (
    String(agentId || '').trim().toUpperCase() === 'AGT-MKT-DMA-001'
    || String(agentTypeId || '').trim() === 'marketing.digital_marketing.v1'
  )
}

function getThemeDiscoverySkill(skills: AgentSkill[]): AgentSkill | null {
  return skills.find((skill) => {
    const candidates = [skill.display_name, skill.name]
      .map((value) => String(value || '').trim().toLowerCase())
      .filter(Boolean)
    return candidates.some((value) => value === 'theme discovery' || value === 'theme_discovery')
  }) || null
}

function getDeliverableChannelTarget(deliverable: Deliverable): {
  platformKey: string | null
  visibility: string
  publicReleaseRequested: boolean
  publishStatus: string
  platformPostId: string | null
} {
  const payload = asRecord(deliverable.payload) || {}
  const destination = asRecord(payload.destination) || asRecord(payload.destination_ref) || {}
  const metadata = asRecord(destination.metadata) || asRecord(payload.metadata) || {}
  const publishReceipt = asRecord(payload.publish_receipt) || {}

  return {
    platformKey:
      stringOrNull(destination.destination_type)
      || stringOrNull(payload.destination_type)
      || stringOrNull(payload.channel)
      || stringOrNull(payload.platform),
    visibility: stringOrNull(metadata.visibility) || stringOrNull(payload.visibility) || 'private',
    publicReleaseRequested:
      booleanFromUnknown(metadata.public_release_requested)
      || booleanFromUnknown(payload.public_release_requested),
    publishStatus:
      stringOrNull(payload.publish_status)
      || stringOrNull(publishReceipt.status)
      || 'not_published',
    platformPostId:
      stringOrNull(publishReceipt.platform_post_id)
      || stringOrNull(payload.platform_post_id),
  }
}

function getPlatformConnectionSummary(
  connections: PlatformConnection[],
  platformKey: string | null
): PlatformConnectionSummary {
  const normalized = String(platformKey || '').trim().toLowerCase()
  const labelBase = normalized ? `${normalized[0].toUpperCase()}${normalized.slice(1)}` : 'Channel'
  const connection = connections.find(
    (item) => String(item.platform_key || '').trim().toLowerCase() === normalized
  )

  if (!connection) {
    return {
      label: `${labelBase} not connected`,
      message: `Connect ${labelBase} before the agent can upload anything externally.`,
      tone: 'danger',
      isReady: false,
    }
  }

  const status = String(connection.status || '').trim().toLowerCase()
  if (status === 'connected' || status === 'active') {
    return {
      label: `${labelBase} connected`,
      message: connection.last_verified_at
        ? `${labelBase} was last verified on ${new Date(connection.last_verified_at).toLocaleString()}.`
        : `${labelBase} is connected and available for upload gating.`,
      tone: 'success',
      isReady: true,
    }
  }

  return {
    label: `${labelBase} pending verification`,
    message: `${labelBase} has a saved connection, but it still needs operator attention before uploads should proceed.`,
    tone: 'warning',
    isReady: false,
  }
}

function getDeliverablePublishReadiness(
  deliverable: Deliverable | null,
  connectionSummary: PlatformConnectionSummary,
  platformLabel: string
): PublishReadiness {
  if (!deliverable) {
    return {
      label: 'Waiting for first draft',
      message: 'No deliverable has been created yet, so PP cannot verify approval or publish state.',
      tone: 'informative',
      owner: 'platform',
    }
  }

  const reviewStatus = String(deliverable.review_status || '').trim().toLowerCase() || 'pending_review'
  const executionStatus = String(deliverable.execution_status || '').trim().toLowerCase()
  const channel = getDeliverableChannelTarget(deliverable)
  const publishStatus = String(channel.publishStatus || '').trim().toLowerCase()

  if (publishStatus === 'published' || channel.platformPostId) {
    return {
      label: 'Published',
      message: `This deliverable already has a live ${platformLabel} publish receipt.`,
      tone: 'success',
      owner: 'published',
    }
  }

  if (publishStatus === 'failed') {
    return {
      label: 'Publish failed',
      message: `The last ${platformLabel} publish attempt failed. Review the runtime diagnostics before retrying.`,
      tone: 'danger',
      owner: 'platform',
    }
  }

  if (reviewStatus === 'rejected') {
    return {
      label: 'Blocked by customer rejection',
      message: 'The customer rejected this draft, so a revised deliverable must be approved before anything can upload.',
      tone: 'danger',
      owner: 'customer',
    }
  }

  if (reviewStatus !== 'approved') {
    return {
      label: 'Waiting on customer approval',
      message: 'The draft exists, but publish is still customer-blocked until the exact deliverable is approved.',
      tone: 'warning',
      owner: 'customer',
    }
  }

  if (!connectionSummary.isReady) {
    return {
      label: 'Blocked by channel connection',
      message: `Customer approval is complete, but ${platformLabel} still needs a verified connection before upload can happen.`,
      tone: 'danger',
      owner: 'platform',
    }
  }

  if (executionStatus === 'executed' && channel.visibility !== 'public') {
    return {
      label: 'Uploaded as non-public',
      message: `The content reached ${platformLabel}, but it is still ${channel.visibility} and not publicly released.`,
      tone: 'informative',
      owner: 'platform',
    }
  }

  if (channel.publicReleaseRequested || channel.visibility === 'public') {
    return {
      label: 'Ready for public release',
      message: `Approval and ${platformLabel} readiness are satisfied. The next publish step can make this public.`,
      tone: 'success',
      owner: 'ready',
    }
  }

  return {
    label: 'Ready for upload',
    message: `Approval is in place and ${platformLabel} is ready. The agent can upload this without implying automatic public release.`,
    tone: 'success',
    owner: 'ready',
  }
}

function selectLatestDeliverable(deliverables: Deliverable[]): Deliverable | null {
  if (!deliverables.length) return null
  return [...deliverables].sort((left, right) => {
    const leftTs = new Date(left.updated_at || left.created_at || 0).getTime()
    const rightTs = new Date(right.updated_at || right.created_at || 0).getTime()
    return rightTs - leftTs
  })[0]
}

function toneStyles(tone: 'success' | 'warning' | 'danger' | 'informative'): { background: string; color: string } {
  if (tone === 'success') return { background: 'rgba(16, 185, 129, 0.12)', color: '#10b981' }
  if (tone === 'warning') return { background: 'rgba(245, 158, 11, 0.12)', color: '#f59e0b' }
  if (tone === 'danger') return { background: 'rgba(239, 68, 68, 0.12)', color: '#ef4444' }
  return { background: 'rgba(0, 242, 254, 0.12)', color: '#00f2fe' }
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
  const [skills, setSkills] = useState<AgentSkill[]>([])
  const [platformConnections, setPlatformConnections] = useState<PlatformConnection[]>([])

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
    setSkills([])
    setPlatformConnections([])

    try {
      const hiredRows = (await gatewayApiClient.listOpsHiredAgents({
        customer_id: cust,
        as_of: normalizedAsOf,
      })) as HiredAgentInstance[]

      const rowsWithGoals = await Promise.all(
        (hiredRows || []).map(async (hired) => {
          if (!hired?.hired_instance_id) return null

          let goals: GoalInstance[] = []
          try {
            const goalsRes = (await gatewayApiClient.listOpsHiredAgentGoals(
              hired.hired_instance_id,
              { customer_id: cust, as_of: normalizedAsOf }
            )) as GoalsListResponse
            goals = goalsRes?.goals || []
          } catch {
            goals = []
          }

          return {
            subscription_id: hired.subscription_id,
            hired,
            goals,
          } satisfies HiredRow
        })
      )

      const sorted = rowsWithGoals
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

      const [deliverablesRes, approvalsRes, denialsRes, skillsRes, platformConnectionsRes] = await Promise.all([
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
        }) as Promise<unknown>,
        gatewayApiClient.listOpsHiredAgentSkills(row.hired.hired_instance_id) as Promise<unknown>,
        gatewayApiClient.listOpsPlatformConnections(row.hired.hired_instance_id) as Promise<unknown>
      ])

      const d = (deliverablesRes as DeliverablesListResponse)?.deliverables || []
      setDeliverables(d)

      const a = (approvalsRes as ApprovalListResponse)?.approvals || []
      setApprovals(a)

      const p = (denialsRes as PolicyDenialsResponse)?.records || []
      setDenials(p)

      const runtimeSkills = Array.isArray(skillsRes)
        ? skillsRes as AgentSkill[]
        : Array.isArray((skillsRes as { skills?: AgentSkill[] })?.skills)
          ? ((skillsRes as { skills?: AgentSkill[] }).skills || [])
          : []
      setSkills(runtimeSkills)

      const runtimeConnections = Array.isArray(platformConnectionsRes)
        ? platformConnectionsRes as PlatformConnection[]
        : Array.isArray((platformConnectionsRes as { connections?: PlatformConnection[] })?.connections)
          ? ((platformConnectionsRes as { connections?: PlatformConnection[] }).connections || [])
          : []
      setPlatformConnections(runtimeConnections)
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

  const selectedIsDigitalMarketing = Boolean(
    selected && isDigitalMarketingAgent(selected.hired.agent_id, selected.hired.agent_type_id)
  )
  const themeDiscoverySkill = selectedIsDigitalMarketing ? getThemeDiscoverySkill(skills) : null
  const briefFields = themeDiscoverySkill?.goal_schema?.fields || []
  const briefValues = themeDiscoverySkill?.goal_config || {}
  const requiredFieldCount = briefFields.filter((field) => field.required).length
  const completedRequiredFieldCount = briefFields.filter(
    (field) => field.required && hasValue(briefValues[field.key])
  ).length
  const latestDeliverable = selectLatestDeliverable(deliverables)
  const channelTarget = latestDeliverable ? getDeliverableChannelTarget(latestDeliverable) : null
  const platformLabel = channelTarget?.platformKey
    ? `${channelTarget.platformKey[0].toUpperCase()}${channelTarget.platformKey.slice(1)}`
    : 'Publishing channel'
  const connectionSummary = getPlatformConnectionSummary(platformConnections, channelTarget?.platformKey || 'youtube')
  const publishReadiness = getDeliverablePublishReadiness(latestDeliverable, connectionSummary, platformLabel)
  const readinessTone = toneStyles(publishReadiness.tone)
  const connectionTone = toneStyles(connectionSummary.tone)

  return (
    <div className="page-container" data-testid="pp-hired-agents-page">
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
                  data-testid="pp-hired-agents-email"
                />
              </Field>
              <Button appearance="secondary" onClick={() => void lookupByEmail()} data-testid="pp-hired-agents-lookup">Lookup</Button>
            </div>
            {emailError && <Text style={{ color: 'var(--colorPaletteRedForeground1)', fontSize: 12 }}>{emailError}</Text>}
          </div>
          <Field label="Customer ID">
            <Input value={customerId} onChange={(_, d) => setCustomerId(d.value)} placeholder="CUST-..." data-testid="pp-hired-agents-customer-id" />
          </Field>
          <Field label="as_of (ISO 8601, optional)">
            <Input value={asOf} onChange={(_, d) => setAsOf(d.value)} placeholder="2026-02-10T00:00:00Z" data-testid="pp-hired-agents-as-of" />
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
                data-testid={`pp-hired-agents-row-${r.hired.hired_instance_id}`}
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
                  data-testid="pp-hired-agents-open-review-queue"
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
                  data-testid="pp-hired-agents-correlation-id"
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
                  data-testid="pp-hired-agents-apply-correlation"
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
          {selectedIsDigitalMarketing && (
            <div style={{ marginTop: 16, display: 'grid', gap: 16, gridTemplateColumns: 'minmax(0, 1.1fr) minmax(320px, 0.9fr)' }}>
              <Card data-testid="pp-dma-brief-summary-card">
                <CardHeader
                  header={<Text weight="semibold">Theme Discovery brief</Text>}
                  description={<Text size={200}>{completedRequiredFieldCount}/{requiredFieldCount || briefFields.length} core details captured</Text>}
                />
                <div style={{ padding: 16, display: 'flex', flexDirection: 'column', gap: 12 }}>
                  <Text size={200} style={{ opacity: 0.82 }}>
                    PP sees the customer’s structured brief here so support can explain why drafts or publish states look the way they do without asking the customer to restate their intent.
                  </Text>
                  {briefFields.filter((field) => hasValue(briefValues[field.key])).length === 0 ? (
                    <Card appearance="outline" style={{ padding: 12 }}>
                      <Text>No Theme Discovery brief has been saved yet. This runtime is still missing structured customer intent.</Text>
                    </Card>
                  ) : (
                    <div style={{ display: 'grid', gap: 10 }}>
                      {briefFields.map((field) => {
                        if (!hasValue(briefValues[field.key])) return null
                        return (
                          <Card key={field.key} appearance="outline" style={{ padding: 12 }}>
                            <Text size={200} style={{ display: 'block', opacity: 0.7 }}>{field.label}</Text>
                            <Text style={{ display: 'block', marginTop: 6 }}>{formatBriefValue(briefValues[field.key])}</Text>
                          </Card>
                        )
                      })}
                    </div>
                  )}
                </div>
              </Card>

              <div style={{ display: 'grid', gap: 16 }}>
                <Card data-testid="pp-dma-publish-state-card">
                  <CardHeader
                    header={<Text weight="semibold">Publish state</Text>}
                    description={<Text size={200}>Customer-blocked and platform-blocked states are called out explicitly.</Text>}
                  />
                  <div style={{ padding: 16, display: 'flex', flexDirection: 'column', gap: 12 }}>
                    <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                      <span className="fui-Text" style={{ display: 'inline-flex', padding: '4px 10px', borderRadius: 999, background: readinessTone.background, color: readinessTone.color }}>
                        {publishReadiness.label}
                      </span>
                      <span className="fui-Text" style={{ display: 'inline-flex', padding: '4px 10px', borderRadius: 999, background: connectionTone.background, color: connectionTone.color }}>
                        {connectionSummary.label}
                      </span>
                    </div>
                    <Text data-testid="pp-dma-publish-readiness">Publish readiness: {publishReadiness.label}</Text>
                    <Text data-testid="pp-dma-publish-message">{publishReadiness.message}</Text>
                    <Text data-testid="pp-dma-block-owner">
                      Block owner: {publishReadiness.owner === 'customer' ? 'Customer action required' : publishReadiness.owner === 'platform' ? 'Platform action required' : publishReadiness.owner === 'published' ? 'Already published' : 'Ready for next runtime step'}
                    </Text>
                    <Text data-testid="pp-dma-channel-status">Channel: {connectionSummary.label}</Text>
                    {latestDeliverable?.approval_id ? (
                      <Text>Approval lineage: deliverable is tied to {latestDeliverable.approval_id} and PP should treat that as the exact customer-approved version.</Text>
                    ) : (
                      <Text>Approval lineage: this deliverable does not yet carry an approval id, so nothing should imply publish authorization.</Text>
                    )}
                  </div>
                </Card>
              </div>
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
        </>
      )}
    </div>
  )
}
