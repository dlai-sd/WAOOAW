import { useEffect, useMemo, useRef, useState } from 'react'
import { Body1, Button, Card, CardHeader, Field, Input, Spinner, Text } from '@fluentui/react-components'
import { useNavigate, useSearchParams } from 'react-router-dom'

import ApiErrorPanel from '../components/ApiErrorPanel'
import { gatewayApiClient } from '../services/gatewayApiClient'

type DeliverablePreview = {
  batch_id?: string | null
  post_id?: string | null
  brand_name?: string | null
  theme?: string | null
  channel?: string | null
  text_preview?: string | null
}

type RuntimeDeliverable = {
  deliverable_id: string
  approval_id?: string | null
  review_status?: string | null
  execution_status?: string | null
  created_at?: string | null
  updated_at?: string | null
  payload?: Record<string, unknown> | null
}

type PlatformConnection = {
  platform_key: string
  status?: string | null
  last_verified_at?: string | null
}

type PublishRuntimeState = {
  readinessLabel: string
  readinessMessage: string
  channelLabel: string
  blockOwner: string
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

function getChannelTarget(deliverable: RuntimeDeliverable, fallbackPlatformKey?: string | null): {
  platformKey: string
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
      || fallbackPlatformKey
      || 'youtube',
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

function getPlatformConnectionLabel(connections: PlatformConnection[], platformKey: string): { label: string; isReady: boolean } {
  const normalized = String(platformKey || '').trim().toLowerCase()
  const baseLabel = normalized ? `${normalized[0].toUpperCase()}${normalized.slice(1)}` : 'Channel'
  const connection = connections.find((item) => String(item.platform_key || '').trim().toLowerCase() === normalized)
  if (!connection) {
    return { label: `${baseLabel} not connected`, isReady: false }
  }
  const status = String(connection.status || '').trim().toLowerCase()
  if (status === 'connected' || status === 'active') {
    return { label: `${baseLabel} connected`, isReady: true }
  }
  return { label: `${baseLabel} pending verification`, isReady: false }
}

function selectDeliverableForApproval(
  deliverables: RuntimeDeliverable[],
  approvalId: string,
): RuntimeDeliverable | null {
  const exact = deliverables.find((item) => String(item.approval_id || '').trim() === approvalId)
  if (exact) return exact
  if (!deliverables.length) return null
  return [...deliverables].sort((left, right) => {
    const leftTs = new Date(left.updated_at || left.created_at || 0).getTime()
    const rightTs = new Date(right.updated_at || right.created_at || 0).getTime()
    return rightTs - leftTs
  })[0]
}

function buildPublishRuntimeState(
  deliverable: RuntimeDeliverable | null,
  connections: PlatformConnection[],
  previewChannel?: string | null,
): PublishRuntimeState {
  if (!deliverable) {
    return {
      readinessLabel: 'Waiting for runtime detail',
      readinessMessage: 'No deliverable detail was returned for this approval yet, so PP should open the runtime context before acting on publish assumptions.',
      channelLabel: previewChannel ? `${previewChannel} not verified` : 'Channel unknown',
      blockOwner: 'Runtime detail still loading',
    }
  }

  const reviewStatus = String(deliverable.review_status || '').trim().toLowerCase() || 'pending_review'
  const executionStatus = String(deliverable.execution_status || '').trim().toLowerCase()
  const target = getChannelTarget(deliverable, previewChannel)
  const connection = getPlatformConnectionLabel(connections, target.platformKey)
  const platformLabel = target.platformKey[0]?.toUpperCase()
    ? `${target.platformKey[0].toUpperCase()}${target.platformKey.slice(1)}`
    : 'Publishing channel'
  const publishStatus = String(target.publishStatus || '').trim().toLowerCase()

  if (publishStatus === 'published' || target.platformPostId) {
    return {
      readinessLabel: 'Published',
      readinessMessage: `This approval already maps to a live ${platformLabel} publish receipt.`,
      channelLabel: connection.label,
      blockOwner: 'Already published',
    }
  }

  if (publishStatus === 'failed') {
    return {
      readinessLabel: 'Publish failed',
      readinessMessage: `The last ${platformLabel} publish attempt failed, so this is platform-blocked until the runtime is corrected.`,
      channelLabel: connection.label,
      blockOwner: 'Platform action required',
    }
  }

  if (reviewStatus === 'rejected') {
    return {
      readinessLabel: 'Blocked by customer rejection',
      readinessMessage: 'This draft was rejected, so a revised deliverable must be approved before anything can publish.',
      channelLabel: connection.label,
      blockOwner: 'Customer action required',
    }
  }

  if (reviewStatus !== 'approved') {
    return {
      readinessLabel: 'Waiting on customer approval',
      readinessMessage: 'The deliverable exists, but publish is still customer-blocked until the exact draft is approved.',
      channelLabel: connection.label,
      blockOwner: 'Customer action required',
    }
  }

  if (!connection.isReady) {
    return {
      readinessLabel: 'Blocked by channel connection',
      readinessMessage: `Customer approval is complete, but ${platformLabel} still needs a verified connection before upload can happen.`,
      channelLabel: connection.label,
      blockOwner: 'Platform action required',
    }
  }

  if (executionStatus === 'executed' && target.visibility !== 'public') {
    return {
      readinessLabel: 'Uploaded as non-public',
      readinessMessage: `The content reached ${platformLabel}, but it is still ${target.visibility} and not publicly released.`,
      channelLabel: connection.label,
      blockOwner: 'Platform release pending',
    }
  }

  if (target.publicReleaseRequested || target.visibility === 'public') {
    return {
      readinessLabel: 'Ready for public release',
      readinessMessage: `Approval and ${platformLabel} readiness are satisfied. The next publish step can make this public.`,
      channelLabel: connection.label,
      blockOwner: 'Ready for next runtime step',
    }
  }

  return {
    readinessLabel: 'Ready for upload',
    readinessMessage: `Approval is in place and ${platformLabel} is ready. The next step can upload this without implying automatic public release.`,
    channelLabel: connection.label,
    blockOwner: 'Ready for next runtime step',
  }
}

type ReviewQueueApproval = {
  approval_id: string
  customer_id: string
  customer_label: string
  agent_id: string
  agent_label: string
  action: string
  requested_by: string
  correlation_id?: string | null
  purpose?: string | null
  notes?: string | null
  created_at?: string
  expires_at?: string | null
  hired_instance_id?: string | null
  review_state: string
  deliverable_preview: DeliverablePreview
}

function preferredCustomerLabel(item: ReviewQueueApproval | null, fallbackCustomerId: string): string {
  return String(item?.customer_label || '').trim() || fallbackCustomerId.trim() || 'not set'
}

function preferredAgentLabel(item: ReviewQueueApproval | null, fallbackAgentId: string): string {
  return String(item?.agent_label || '').trim() || fallbackAgentId.trim() || 'not set'
}

function buildReviewQueueSearch(customerId: string, agentId: string, correlationId: string): URLSearchParams {
  const params = new URLSearchParams()
  const normalizedCustomerId = customerId.trim()
  const normalizedAgentId = agentId.trim()
  const normalizedCorrelationId = correlationId.trim()

  if (normalizedCustomerId) params.set('customer_id', normalizedCustomerId)
  if (normalizedAgentId) params.set('agent_id', normalizedAgentId)
  if (normalizedCorrelationId) params.set('correlation_id', normalizedCorrelationId)

  return params
}

function getDecisionTone(reviewState: string): 'brand' | 'warning' | 'danger' {
  if (reviewState === 'approved') return 'brand'
  if (reviewState === 'rejected') return 'danger'
  return 'warning'
}

export default function ReviewQueue() {
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  const initialContextLoadRef = useRef(Boolean(searchParams.get('customer_id') || searchParams.get('agent_id') || searchParams.get('correlation_id')))

  const [customerId, setCustomerId] = useState(() => searchParams.get('customer_id') || '')
  const [agentId, setAgentId] = useState(() => searchParams.get('agent_id') || '')
  const [correlationId, setCorrelationId] = useState(() => searchParams.get('correlation_id') || '')
  const [approvals, setApprovals] = useState<ReviewQueueApproval[]>([])
  const [selectedApprovalId, setSelectedApprovalId] = useState<string | null>(null)
  const [selectedRuntimeState, setSelectedRuntimeState] = useState<PublishRuntimeState | null>(null)
  const [selectedRuntimeBusy, setSelectedRuntimeBusy] = useState(false)
  const [hasLoaded, setHasLoaded] = useState(false)
  const [isBusy, setIsBusy] = useState(false)
  const [error, setError] = useState<unknown>(null)

  function syncContext(nextCustomerId: string, nextAgentId: string, nextCorrelationId: string) {
    setSearchParams(buildReviewQueueSearch(nextCustomerId, nextAgentId, nextCorrelationId), { replace: true })
  }

  async function handleLoad() {
    syncContext(customerId, agentId, correlationId)
    setIsBusy(true)
    setError(null)
    try {
      const data = await gatewayApiClient.listReviewQueueApprovals({
        customer_id: customerId.trim() || undefined,
        agent_id: agentId.trim() || undefined,
        correlation_id: correlationId.trim() || undefined,
        limit: 20,
      })
      const nextApprovals = (data?.approvals || []) as ReviewQueueApproval[]
      setApprovals(nextApprovals)
      setSelectedApprovalId(current => {
        if (current && nextApprovals.some(item => item.approval_id === current)) return current
        return nextApprovals[0]?.approval_id || null
      })
      setHasLoaded(true)
    } catch (e: any) {
      setError(e)
    } finally {
      setIsBusy(false)
    }
  }

  async function handleApprove(item: ReviewQueueApproval) {
    const postId = item.deliverable_preview?.post_id?.trim()
    if (!postId) return

    setIsBusy(true)
    setError(null)
    try {
      await gatewayApiClient.approveMarketingDraftPost(postId, { approval_id: item.approval_id })
      setApprovals(prev =>
        prev.filter(queueItem => queueItem.approval_id !== item.approval_id)
      )
      setSelectedApprovalId(prev => (prev === item.approval_id ? null : prev))
    } catch (e: any) {
      setError(e)
    } finally {
      setIsBusy(false)
    }
  }

  async function handleReject(item: ReviewQueueApproval) {
    const postId = item.deliverable_preview?.post_id?.trim()
    if (!postId) return

    setIsBusy(true)
    setError(null)
    try {
      await gatewayApiClient.rejectMarketingDraftPost(postId)
      setApprovals(prev =>
        prev.filter(queueItem => queueItem.approval_id !== item.approval_id)
      )
      setSelectedApprovalId(prev => (prev === item.approval_id ? null : prev))
    } catch (e: any) {
      setError(e)
    } finally {
      setIsBusy(false)
    }
  }

  useEffect(() => {
    if (!initialContextLoadRef.current) return
    initialContextLoadRef.current = false
    void handleLoad()
  }, [])

  const reviewQueueContext = buildReviewQueueSearch(customerId, agentId, correlationId)
  const reviewQueueContextString = reviewQueueContext.toString()
  const hasOperatorContext = Boolean(customerId.trim() || agentId.trim() || correlationId.trim())
  const selectedApproval = useMemo(
    () => approvals.find(item => item.approval_id === selectedApprovalId) || approvals[0] || null,
    [approvals, selectedApprovalId]
  )
  const operatorCustomerLabel = preferredCustomerLabel(selectedApproval, customerId)
  const operatorAgentLabel = preferredAgentLabel(selectedApproval, agentId)

  useEffect(() => {
    if (selectedApproval || approvals.length === 0) return
    setSelectedApprovalId(approvals[0].approval_id)
  }, [approvals, selectedApproval])

  useEffect(() => {
    let isActive = true

    async function loadRuntimeState() {
      if (!selectedApproval?.hired_instance_id) {
        setSelectedRuntimeState(null)
        return
      }

      setSelectedRuntimeBusy(true)
      try {
        const [deliverablesResponse, platformConnectionsResponse] = await Promise.all([
          gatewayApiClient.listOpsHiredAgentDeliverables(selectedApproval.hired_instance_id, {
            customer_id: selectedApproval.customer_id,
          }),
          gatewayApiClient.listOpsPlatformConnections(selectedApproval.hired_instance_id),
        ])

        if (!isActive) return

        const deliverables = Array.isArray((deliverablesResponse as { deliverables?: RuntimeDeliverable[] })?.deliverables)
          ? ((deliverablesResponse as { deliverables?: RuntimeDeliverable[] }).deliverables || [])
          : Array.isArray(deliverablesResponse)
            ? deliverablesResponse as RuntimeDeliverable[]
            : []
        const connections = Array.isArray(platformConnectionsResponse)
          ? platformConnectionsResponse as PlatformConnection[]
          : Array.isArray((platformConnectionsResponse as { connections?: PlatformConnection[] })?.connections)
            ? ((platformConnectionsResponse as { connections?: PlatformConnection[] }).connections || [])
            : []
        const runtimeDeliverable = selectDeliverableForApproval(deliverables, selectedApproval.approval_id)

        setSelectedRuntimeState(
          buildPublishRuntimeState(
            runtimeDeliverable,
            connections,
            selectedApproval.deliverable_preview?.channel || null,
          )
        )
      } catch {
        if (!isActive) return
        setSelectedRuntimeState({
          readinessLabel: 'Runtime detail unavailable',
          readinessMessage: 'PP could not load publish state detail for this approval right now. Open the runtime context to continue safely.',
          channelLabel: 'Channel state unavailable',
          blockOwner: 'Runtime detail unavailable',
        })
      } finally {
        if (isActive) setSelectedRuntimeBusy(false)
      }
    }

    void loadRuntimeState()

    return () => {
      isActive = false
    }
  }, [selectedApproval])

  return (
    <div className="page-container" data-testid="pp-review-queue-page">
      <div className="page-header">
        <Text as="h1" size={900} weight="semibold">Review Queue</Text>
        <Body1>Operator decision workspace for enriched approval context</Body1>
      </div>

      <div className="pp-dashboard-grid" style={{ marginBottom: 20 }}>
        <Card className="pp-dashboard-panel pp-dashboard-panel--accent" data-help-box="true">
          <div className="pp-dashboard-kicker">Approval desk</div>
          <Text as="h2" size={700} weight="semibold">Help contributors make a decision with enough customer and runtime context to stand behind it.</Text>
          <p className="pp-dashboard-body-copy">
            The queue should make obvious what needs review, which runtime it belongs to, and which next surface the operator should open after approving or denying it.
          </p>
        </Card>
        <Card className="pp-dashboard-panel" data-help-box="true">
          <Text as="h3" size={600} weight="semibold">Best operator habit</Text>
          <p className="pp-dashboard-body-copy">
            Filter quickly, approve only what is safe, and leave the customer with a cleaner next state than when the ticket arrived.
          </p>
        </Card>
      </div>

      {!!error && <ApiErrorPanel title="Review Queue error" error={error} />}

      <Card>
        <CardHeader header={<Text weight="semibold">Review queue filters</Text>} />
        <div style={{ padding: 16, display: 'flex', gap: 12, flexWrap: 'wrap', alignItems: 'end' }} data-testid="pp-review-queue-filters">
          <Text size={200} style={{ width: '100%', opacity: 0.8 }}>
            Narrow the queue by customer, agent, or correlation id so the operator sees one actionable decision list instead of a noisy backlog.
          </Text>
          <Field label="Customer ID">
            <Input value={customerId} onChange={(_, data) => setCustomerId(data.value)} data-testid="pp-review-queue-customer-id" />
          </Field>
          <Field label="Agent ID">
            <Input value={agentId} onChange={(_, data) => setAgentId(data.value)} data-testid="pp-review-queue-agent-id" />
          </Field>
          <Field label="Correlation ID">
            <Input value={correlationId} onChange={(_, data) => setCorrelationId(data.value)} data-testid="pp-review-queue-correlation-id" />
          </Field>
          <Button appearance="primary" onClick={handleLoad} disabled={isBusy} data-testid="pp-review-queue-load">Load</Button>
        </div>
      </Card>

      {hasOperatorContext && (
        <Card style={{ marginTop: 16 }} data-help-box="true">
          <CardHeader
            header={<Text weight="semibold">Operator handoff context</Text>}
            description={<Text size={200}>{operatorCustomerLabel} • {operatorAgentLabel} • Correlation {correlationId.trim() || 'not set'}</Text>}
          />
          <div style={{ padding: 16, display: 'flex', flexDirection: 'column', gap: 10 }}>
            <Text size={200}>What happened: this queue is already narrowed to the customer or agent the operator came in with.</Text>
            <Text size={200}>What next: decide here, then jump to hired runtime or policy denials without re-entering filters.</Text>
            <Text size={200} style={{ opacity: 0.78 }}>Raw IDs: customer_id {customerId.trim() || 'not set'} • agent_id {agentId.trim() || 'not set'}</Text>
            <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
              <Button
                appearance="secondary"
                disabled={!customerId.trim()}
                onClick={() => navigate(`/hired-agents?${reviewQueueContextString}`)}
                data-testid="pp-review-queue-open-hired-agents"
              >
                Open Hired Agents
              </Button>
              <Button
                appearance="secondary"
                disabled={!customerId.trim() && !agentId.trim()}
                onClick={() => navigate(`/policy-denials?${reviewQueueContextString}`)}
              >
                Open Policy Denials
              </Button>
            </div>
          </div>
        </Card>
      )}

      {isBusy && (
        <div style={{ padding: 16 }}>
          <Spinner label="Loading review queue..." />
        </div>
      )}

      {hasLoaded && !isBusy && !error && approvals.length === 0 && (
        <Card style={{ marginTop: 16, padding: 20 }}>
          <Text weight="semibold">No review items found</Text>
          <Text size={300} style={{ display: 'block', marginTop: 8, opacity: 0.8 }}>
            No matching approval items are waiting right now. Adjust the filters or try again when a new item enters review.
          </Text>
        </Card>
      )}

      {approvals.length > 0 && (
        <div style={{ marginTop: 16, display: 'grid', gap: 16, gridTemplateColumns: 'minmax(320px, 420px) minmax(0, 1fr)' }}>
          <Card>
            <CardHeader
              header={<Text weight="semibold">Decision queue</Text>}
              description={<Text size={200}>{approvals.length} items waiting for review</Text>}
            />
            <div style={{ padding: 16, display: 'flex', flexDirection: 'column', gap: 12 }} data-testid="pp-review-queue-list">
              {approvals.map(item => {
                const isSelected = selectedApproval?.approval_id === item.approval_id
                return (
                  <button
                    key={item.approval_id}
                    type="button"
                    onClick={() => setSelectedApprovalId(item.approval_id)}
                    data-testid={`pp-review-queue-item-${item.approval_id}`}
                    style={{
                      textAlign: 'left',
                      background: isSelected ? 'rgba(0, 242, 254, 0.08)' : 'transparent',
                      border: isSelected ? '1px solid rgba(0, 242, 254, 0.35)' : '1px solid rgba(255,255,255,0.12)',
                      borderRadius: 12,
                      padding: 14,
                      cursor: 'pointer',
                    }}
                  >
                    <Text weight="semibold" style={{ display: 'block' }}>{item.agent_label}</Text>
                    <Text size={200} style={{ display: 'block', opacity: 0.82, marginTop: 4 }}>
                      {item.customer_label} • {item.deliverable_preview?.brand_name || 'Unknown brand'}
                    </Text>
                    <Text size={200} style={{ display: 'block', opacity: 0.72, marginTop: 6 }}>
                      {item.deliverable_preview?.text_preview || item.notes || item.purpose || item.action}
                    </Text>
                  </button>
                )
              })}
            </div>
          </Card>

          {selectedApproval && (
            <Card data-testid="pp-review-queue-workspace">
              <CardHeader
                header={<Text weight="semibold">Decision workspace</Text>}
                description={<Text size={200}>{selectedApproval.customer_label} • {selectedApproval.agent_label}</Text>}
              />
              <div style={{ padding: 16, display: 'flex', flexDirection: 'column', gap: 14 }}>
                <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                  <span className={`fui-Text`} style={{
                    display: 'inline-flex',
                    padding: '4px 10px',
                    borderRadius: 999,
                    background: getDecisionTone(selectedApproval.review_state) === 'brand' ? 'rgba(0, 242, 254, 0.12)' : getDecisionTone(selectedApproval.review_state) === 'danger' ? 'rgba(239, 68, 68, 0.12)' : 'rgba(245, 158, 11, 0.12)',
                    color: getDecisionTone(selectedApproval.review_state) === 'brand' ? '#00f2fe' : getDecisionTone(selectedApproval.review_state) === 'danger' ? '#ef4444' : '#f59e0b',
                  }}>
                    {selectedApproval.review_state}
                  </span>
                  <Text size={200}>approval_id: {selectedApproval.approval_id}</Text>
                  <Text size={200}>customer_id: {selectedApproval.customer_id}</Text>
                  <Text size={200}>agent_id: {selectedApproval.agent_id}</Text>
                  {selectedApproval.correlation_id && <Text size={200}>correlation_id: {selectedApproval.correlation_id}</Text>}
                </div>

                <Card>
                  <CardHeader
                    header={<Text weight="semibold">Deliverable context</Text>}
                    description={<Text size={200}>{selectedApproval.deliverable_preview?.brand_name || 'Unknown brand'} • {selectedApproval.deliverable_preview?.theme || 'No theme'}</Text>}
                  />
                  <div style={{ padding: 16, display: 'flex', flexDirection: 'column', gap: 8 }}>
                    <Text size={300}>{selectedApproval.deliverable_preview?.text_preview || selectedApproval.notes || selectedApproval.purpose || 'No preview available.'}</Text>
                    <Text size={200} style={{ opacity: 0.82 }}>
                      Customer {selectedApproval.customer_label} • Agent {selectedApproval.agent_label}
                    </Text>
                    <Text size={200} style={{ opacity: 0.82 }}>
                      Channel {selectedApproval.deliverable_preview?.channel || 'unknown'} • Post {selectedApproval.deliverable_preview?.post_id || 'missing'} • Batch {selectedApproval.deliverable_preview?.batch_id || 'missing'}
                    </Text>
                    <Text size={200} style={{ opacity: 0.82 }}>
                      Runtime {selectedApproval.hired_instance_id || 'unavailable'} • Requested by {selectedApproval.requested_by}
                    </Text>
                  </div>
                </Card>

                <Card>
                  <CardHeader
                    header={<Text weight="semibold">Publish gate status</Text>}
                    description={<Text size={200}>Review whether this item is customer-blocked or platform-blocked before taking the next operator action.</Text>}
                  />
                  <div style={{ padding: 16, display: 'flex', flexDirection: 'column', gap: 8 }}>
                    {selectedRuntimeBusy ? (
                      <Spinner label="Loading publish gate status..." />
                    ) : (
                      <>
                        <Text data-testid="pp-review-queue-publish-readiness">Publish readiness: {selectedRuntimeState?.readinessLabel || 'Unavailable'}</Text>
                        <Text data-testid="pp-review-queue-publish-message">{selectedRuntimeState?.readinessMessage || 'No runtime status loaded.'}</Text>
                        <Text data-testid="pp-review-queue-channel-status">Channel: {selectedRuntimeState?.channelLabel || 'Unknown'}</Text>
                        <Text data-testid="pp-review-queue-block-owner">Block owner: {selectedRuntimeState?.blockOwner || 'Unknown'}</Text>
                        <Text>Approval lineage: approval_id {selectedApproval.approval_id} should only authorize the exact deliverable version shown in this workspace.</Text>
                      </>
                    )}
                  </div>
                </Card>

                <Card>
                  <CardHeader
                    header={<Text weight="semibold">Operator next move</Text>}
                    description={<Text size={200}>Approve or deny only after checking the customer-facing text and the runtime you may need to inspect next.</Text>}
                  />
                  <div style={{ padding: 16, display: 'flex', gap: 12, flexWrap: 'wrap' }}>
                    <Button
                      appearance="primary"
                      disabled={isBusy || !selectedApproval.deliverable_preview?.post_id}
                      onClick={() => void handleApprove(selectedApproval)}
                      data-testid="pp-review-queue-approve"
                    >
                      Approve and remove
                    </Button>
                    <Button
                      appearance="secondary"
                      disabled={isBusy || !selectedApproval.deliverable_preview?.post_id}
                      onClick={() => void handleReject(selectedApproval)}
                      data-testid="pp-review-queue-deny"
                    >
                      Deny and remove
                    </Button>
                    <Button
                      appearance="subtle"
                      disabled={!selectedApproval.hired_instance_id}
                      onClick={() => navigate(`/hired-agents?${buildReviewQueueSearch(
                        selectedApproval.customer_id,
                        selectedApproval.agent_id,
                        selectedApproval.correlation_id || correlationId
                      ).toString()}&selected_hired_instance_id=${encodeURIComponent(selectedApproval.hired_instance_id || '')}`)}
                      data-testid="pp-review-queue-open-runtime-context"
                    >
                      Open runtime context
                    </Button>
                  </div>
                </Card>
              </div>
            </Card>
          )}
        </div>
      )}
    </div>
  )
}
