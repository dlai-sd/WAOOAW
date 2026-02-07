import { gatewayRequestJson } from './gatewayApiClient'

export type DraftPost = {
  post_id: string
  channel: string
  text: string
  hashtags?: string[]
  review_status: 'pending_review' | 'approved' | 'changes_requested' | 'rejected'
  approval_id?: string | null
  execution_status?: string
  scheduled_at?: string | null
}

export type DraftBatch = {
  batch_id: string
  agent_id: string
  customer_id?: string | null
  theme: string
  brand_name: string
  created_at: string
  status: string
  posts: DraftPost[]
}

export async function listCustomerDraftBatches(): Promise<DraftBatch[]> {
  return gatewayRequestJson<DraftBatch[]>('/cp/marketing/draft-batches')
}

export async function approveDraftPost(postId: string): Promise<{ post_id: string; review_status: string; approval_id: string }> {
  return gatewayRequestJson('/cp/marketing/draft-posts/approve', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ post_id: postId })
  })
}

export async function rejectDraftPost(postId: string, reason?: string): Promise<{ post_id: string; decision: string }> {
  return gatewayRequestJson('/cp/marketing/draft-posts/reject', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ post_id: postId, reason })
  })
}

export async function scheduleDraftPost(
  postId: string,
  scheduledAtIso: string,
  approvalId?: string
): Promise<{ post_id: string; execution_status: string; scheduled_at: string }> {
  return gatewayRequestJson('/cp/marketing/draft-posts/schedule', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ post_id: postId, scheduled_at: scheduledAtIso, approval_id: approvalId })
  })
}
