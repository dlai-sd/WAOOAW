import { useEffect, useRef, useState } from 'react'
import { Body1, Button, Card, CardHeader, Field, Input, Text } from '@fluentui/react-components'
import { useNavigate, useSearchParams } from 'react-router-dom'

import ApiErrorPanel from '../components/ApiErrorPanel'
import { gatewayApiClient } from '../services/gatewayApiClient'

type DraftPost = {
  post_id: string
  channel: string
  text: string
  hashtags?: string[]
  review_status?: string
  approval_id?: string | null
  scheduled_at?: string | null
  execution_status?: string | null
}

type DraftBatch = {
  batch_id: string
  agent_id: string
  customer_id?: string | null
  theme: string
  brand_name: string
  status?: string
  created_at?: string
  posts: DraftPost[]
}

function buildReviewQueueSearch(customerId: string, agentId: string): URLSearchParams {
  const params = new URLSearchParams()
  const normalizedCustomerId = customerId.trim()
  const normalizedAgentId = agentId.trim()

  if (normalizedCustomerId) params.set('customer_id', normalizedCustomerId)
  if (normalizedAgentId) params.set('agent_id', normalizedAgentId)

  return params
}

export default function ReviewQueue() {
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  const initialContextLoadRef = useRef(Boolean(searchParams.get('customer_id') || searchParams.get('agent_id')))

  const [customerId, setCustomerId] = useState(() => searchParams.get('customer_id') || '')
  const [agentId, setAgentId] = useState(() => searchParams.get('agent_id') || '')
  const [batches, setBatches] = useState<DraftBatch[]>([])
  const [hasLoaded, setHasLoaded] = useState(false)
  const [scheduledAtByPostId, setScheduledAtByPostId] = useState<Record<string, string>>({})
  const [isBusy, setIsBusy] = useState(false)
  const [error, setError] = useState<unknown>(null)

  function syncContext(nextCustomerId: string, nextAgentId: string) {
    setSearchParams(buildReviewQueueSearch(nextCustomerId, nextAgentId), { replace: true })
  }

  async function handleLoad() {
    syncContext(customerId, agentId)
    setIsBusy(true)
    setError(null)
    try {
      const data = await gatewayApiClient.listMarketingDraftBatches({ customer_id: customerId, agent_id: agentId, limit: 20 })
      setBatches((data || []) as DraftBatch[])
      setHasLoaded(true)
    } catch (e: any) {
      setError(e)
    } finally {
      setIsBusy(false)
    }
  }

  async function handleApprove(postId: string) {
    setIsBusy(true)
    setError(null)
    try {
      const res = await gatewayApiClient.approveMarketingDraftPost(postId)
      setBatches(prev =>
        prev.map(batch => ({
          ...batch,
          posts: (batch.posts || []).map(p =>
            p.post_id === postId
              ? { ...p, review_status: res.review_status, approval_id: res.approval_id }
              : p
          )
        }))
      )
    } catch (e: any) {
      setError(e)
    } finally {
      setIsBusy(false)
    }
  }

  async function handleSchedule(postId: string) {
    const scheduledAt = (scheduledAtByPostId[postId] || '').trim()
    if (!scheduledAt) return

    setIsBusy(true)
    setError(null)
    try {
      const res = await gatewayApiClient.scheduleMarketingDraftPost(postId, { scheduled_at: scheduledAt })
      setBatches(prev =>
        prev.map(batch => ({
          ...batch,
          posts: (batch.posts || []).map(p =>
            p.post_id === postId
              ? { ...p, review_status: p.review_status, approval_id: p.approval_id, scheduled_at: res.scheduled_at, execution_status: res.execution_status }
              : p
          )
        }))
      )
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

  const reviewQueueContext = buildReviewQueueSearch(customerId, agentId)
  const reviewQueueContextString = reviewQueueContext.toString()
  const hasOperatorContext = Boolean(customerId.trim() || agentId.trim())

  return (
    <div className="page-container">
      <div className="page-header">
        <Text as="h1" size={900} weight="semibold">Review Queue</Text>
        <Body1>Ops-assisted approvals for marketing draft batches</Body1>
      </div>

      <div className="pp-dashboard-grid" style={{ marginBottom: 20 }}>
        <Card className="pp-dashboard-panel pp-dashboard-panel--accent">
          <div className="pp-dashboard-kicker">Approval desk</div>
          <Text as="h2" size={700} weight="semibold">Help contributors move customer work, not just read draft rows.</Text>
          <p className="pp-dashboard-body-copy">
            The queue should make obvious what needs review, what is already approved, and what is still blocking publish or schedule.
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
        <CardHeader header={<Text weight="semibold">Draft batches</Text>} />
        <div style={{ padding: 16, display: 'flex', gap: 12, flexWrap: 'wrap', alignItems: 'end' }}>
          <Text size={200} style={{ width: '100%', opacity: 0.8 }}>
            Narrow the queue by customer or agent so approvals feel operationally precise instead of noisy.
          </Text>
          <Field label="Customer ID">
            <Input value={customerId} onChange={(_, data) => setCustomerId(data.value)} />
          </Field>
          <Field label="Agent ID">
            <Input value={agentId} onChange={(_, data) => setAgentId(data.value)} />
          </Field>
          <Button appearance="primary" onClick={handleLoad} disabled={isBusy}>Load</Button>
        </div>
      </Card>

      {hasOperatorContext && (
        <Card style={{ marginTop: 16 }}>
          <CardHeader
            header={<Text weight="semibold">Operator handoff context</Text>}
            description={<Text size={200}>Customer {customerId.trim() || 'not set'} • Agent {agentId.trim() || 'not set'}</Text>}
          />
          <div style={{ padding: 16, display: 'flex', flexDirection: 'column', gap: 10 }}>
            <Text size={200}>What happened: this queue is already narrowed to the customer or agent the operator came in with.</Text>
            <Text size={200}>What next: approve or schedule here, then jump to hired runtime or policy denials without re-entering filters.</Text>
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

      {hasLoaded && !isBusy && !error && batches.length === 0 && (
        <Card style={{ marginTop: 16, padding: 20 }}>
          <Text weight="semibold">No draft batches found</Text>
          <Text size={300} style={{ display: 'block', marginTop: 8, opacity: 0.8 }}>
            No matching customer or agent drafts are waiting right now. Adjust the filters or try again when a batch enters review.
          </Text>
        </Card>
      )}

      {batches.map(batch => (
        <Card key={batch.batch_id} style={{ marginTop: 16 }}>
          <CardHeader
            header={<Text weight="semibold">Batch {batch.batch_id}</Text>}
            description={<Text size={200} style={{ opacity: 0.85 }}>{batch.brand_name} • {batch.theme} • {batch.status || 'pending_review'}</Text>}
          />
          <div style={{ padding: 16, display: 'flex', flexDirection: 'column', gap: 12 }}>
            <Text size={200} style={{ opacity: 0.85 }}>
              Customer {batch.customer_id || customerId.trim() || 'unknown'} • Agent {batch.agent_id || agentId.trim() || 'unknown'}
            </Text>
            <Text size={200} style={{ opacity: 0.85 }}>
              Next operator move: approve safe draft content, schedule approved content, or open hired runtime if the customer asks what happens after publish.
            </Text>
            {(batch.posts || []).map(post => (
              <Card key={post.post_id}>
                <CardHeader
                  header={<Text weight="semibold">{post.channel}</Text>}
                  description={<Text size={200} style={{ opacity: 0.85 }}>{post.review_status || 'pending_review'}</Text>}
                />
                <div style={{ padding: 16, display: 'flex', flexDirection: 'column', gap: 8 }}>
                  <Text size={300}>{post.text}</Text>
                  {post.approval_id && (
                    <Text size={200} style={{ opacity: 0.85 }}>approval_id: {String(post.approval_id)}</Text>
                  )}
                  <Field label="scheduled_at (ISO 8601, e.g. 2026-02-06T00:00:00+00:00)">
                    <Input
                      value={scheduledAtByPostId[post.post_id] || ''}
                      onChange={(_, data) => setScheduledAtByPostId(prev => ({ ...prev, [post.post_id]: data.value }))}
                    />
                  </Field>
                  <div style={{ display: 'flex', gap: 12 }}>
                    <Button
                      appearance="secondary"
                      disabled={isBusy || post.review_status === 'approved'}
                      onClick={() => handleApprove(post.post_id)}
                    >
                      Approve
                    </Button>
                    <Button
                      appearance="primary"
                      disabled={
                        isBusy ||
                        post.review_status !== 'approved' ||
                        !(scheduledAtByPostId[post.post_id] || '').trim()
                      }
                      onClick={() => handleSchedule(post.post_id)}
                    >
                      Schedule
                    </Button>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        </Card>
      ))}
    </div>
  )
}
