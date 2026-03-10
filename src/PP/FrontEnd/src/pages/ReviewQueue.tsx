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

  useEffect(() => {
    if (selectedApproval || approvals.length === 0) return
    setSelectedApprovalId(approvals[0].approval_id)
  }, [approvals, selectedApproval])

  return (
    <div className="page-container">
      <div className="page-header">
        <Text as="h1" size={900} weight="semibold">Review Queue</Text>
        <Body1>Operator decision workspace for enriched approval context</Body1>
      </div>

      <div className="pp-dashboard-grid" style={{ marginBottom: 20 }}>
        <Card className="pp-dashboard-panel pp-dashboard-panel--accent">
          <div className="pp-dashboard-kicker">Approval desk</div>
          <Text as="h2" size={700} weight="semibold">Help contributors make a decision with enough customer and runtime context to stand behind it.</Text>
          <p className="pp-dashboard-body-copy">
            The queue should make obvious what needs review, which runtime it belongs to, and which next surface the operator should open after approving or denying it.
          </p>
        </Card>
        <Card className="pp-dashboard-panel">
          <Text as="h3" size={600} weight="semibold">Best operator habit</Text>
          <p className="pp-dashboard-body-copy">
            Filter quickly, approve only what is safe, and leave the customer with a cleaner next state than when the ticket arrived.
          </p>
        </Card>
      </div>

      {!!error && <ApiErrorPanel title="Review Queue error" error={error} />}

      <Card>
        <CardHeader header={<Text weight="semibold">Review queue filters</Text>} />
        <div style={{ padding: 16, display: 'flex', gap: 12, flexWrap: 'wrap', alignItems: 'end' }}>
          <Text size={200} style={{ width: '100%', opacity: 0.8 }}>
            Narrow the queue by customer, agent, or correlation id so the operator sees one actionable decision list instead of a noisy backlog.
          </Text>
          <Field label="Customer ID">
            <Input value={customerId} onChange={(_, data) => setCustomerId(data.value)} />
          </Field>
          <Field label="Agent ID">
            <Input value={agentId} onChange={(_, data) => setAgentId(data.value)} />
          </Field>
          <Field label="Correlation ID">
            <Input value={correlationId} onChange={(_, data) => setCorrelationId(data.value)} />
          </Field>
          <Button appearance="primary" onClick={handleLoad} disabled={isBusy}>Load</Button>
        </div>
      </Card>

      {hasOperatorContext && (
        <Card style={{ marginTop: 16 }}>
          <CardHeader
            header={<Text weight="semibold">Operator handoff context</Text>}
            description={<Text size={200}>Customer {customerId.trim() || 'not set'} • Agent {agentId.trim() || 'not set'} • Correlation {correlationId.trim() || 'not set'}</Text>}
          />
          <div style={{ padding: 16, display: 'flex', flexDirection: 'column', gap: 10 }}>
            <Text size={200}>What happened: this queue is already narrowed to the customer or agent the operator came in with.</Text>
            <Text size={200}>What next: decide here, then jump to hired runtime or policy denials without re-entering filters.</Text>
            <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
              <Button
                appearance="secondary"
                disabled={!customerId.trim()}
                onClick={() => navigate(`/hired-agents?${reviewQueueContextString}`)}
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
            <div style={{ padding: 16, display: 'flex', flexDirection: 'column', gap: 12 }}>
              {approvals.map(item => {
                const isSelected = selectedApproval?.approval_id === item.approval_id
                return (
                  <button
                    key={item.approval_id}
                    type="button"
                    onClick={() => setSelectedApprovalId(item.approval_id)}
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
            <Card>
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
                      Channel {selectedApproval.deliverable_preview?.channel || 'unknown'} • Post {selectedApproval.deliverable_preview?.post_id || 'missing'} • Batch {selectedApproval.deliverable_preview?.batch_id || 'missing'}
                    </Text>
                    <Text size={200} style={{ opacity: 0.82 }}>
                      Runtime {selectedApproval.hired_instance_id || 'unavailable'} • Requested by {selectedApproval.requested_by}
                    </Text>
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
                    >
                      Approve and remove
                    </Button>
                    <Button
                      appearance="secondary"
                      disabled={isBusy || !selectedApproval.deliverable_preview?.post_id}
                      onClick={() => void handleReject(selectedApproval)}
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
