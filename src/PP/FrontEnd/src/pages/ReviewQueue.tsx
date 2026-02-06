import { useState } from 'react'
import { Body1, Button, Card, CardHeader, Field, Input, Text } from '@fluentui/react-components'

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

export default function ReviewQueue() {
  const [customerId, setCustomerId] = useState('CUST-001')
  const [agentId, setAgentId] = useState('AGT-MKT-HEALTH-001')
  const [batches, setBatches] = useState<DraftBatch[]>([])
  const [scheduledAtByPostId, setScheduledAtByPostId] = useState<Record<string, string>>({})
  const [isBusy, setIsBusy] = useState(false)
  const [error, setError] = useState<unknown>(null)

  async function handleLoad() {
    setIsBusy(true)
    setError(null)
    try {
      const data = await gatewayApiClient.listMarketingDraftBatches({ customer_id: customerId, agent_id: agentId, limit: 20 })
      setBatches((data || []) as DraftBatch[])
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

  return (
    <div className="page-container">
      <div className="page-header">
        <Text as="h1" size={900} weight="semibold">Review Queue</Text>
        <Body1>Ops-assisted approvals for marketing draft batches</Body1>
      </div>

      {!!error && <ApiErrorPanel title="Review Queue error" error={error} />}

      <Card>
        <CardHeader header={<Text weight="semibold">Draft batches</Text>} />
        <div style={{ padding: 16, display: 'flex', gap: 12, flexWrap: 'wrap', alignItems: 'end' }}>
          <Field label="Customer ID">
            <Input value={customerId} onChange={(_, data) => setCustomerId(data.value)} />
          </Field>
          <Field label="Agent ID">
            <Input value={agentId} onChange={(_, data) => setAgentId(data.value)} />
          </Field>
          <Button appearance="primary" onClick={handleLoad} disabled={isBusy}>Load</Button>
        </div>
      </Card>

      {batches.map(batch => (
        <Card key={batch.batch_id} style={{ marginTop: 16 }}>
          <CardHeader
            header={<Text weight="semibold">Batch {batch.batch_id}</Text>}
            description={<Text size={200} style={{ opacity: 0.85 }}>{batch.brand_name} • {batch.theme} • {batch.status || 'pending_review'}</Text>}
          />
          <div style={{ padding: 16, display: 'flex', flexDirection: 'column', gap: 12 }}>
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
