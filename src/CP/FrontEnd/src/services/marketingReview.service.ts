import { gatewayRequestJson } from './gatewayApiClient'

export type DraftArtifactType = 'text' | 'table' | 'image' | 'audio' | 'video' | 'video_audio'

export type DraftArtifactRequest = {
  artifact_type: Exclude<DraftArtifactType, 'text'>
  prompt: string
  metadata?: Record<string, unknown>
}

export type GeneratedArtifact = {
  artifact_type: Exclude<DraftArtifactType, 'text'>
  uri: string
  preview_uri?: string | null
  mime_type?: string | null
  metadata?: Record<string, unknown>
}

export type DraftPost = {
  post_id: string
  channel: string
  text: string
  hashtags?: string[]
  artifact_type?: DraftArtifactType
  artifact_uri?: string | null
  artifact_preview_uri?: string | null
  artifact_mime_type?: string | null
  artifact_metadata?: Record<string, unknown>
  artifact_generation_status?: 'not_requested' | 'queued' | 'running' | 'ready' | 'failed'
  artifact_job_id?: string | null
  generated_artifacts?: GeneratedArtifact[]
  review_status: 'pending_review' | 'approved' | 'changes_requested' | 'rejected'
  approval_id?: string | null
  execution_status?: string
  scheduled_at?: string | null
  credential_ref?: string | null
  provider_post_id?: string | null
  provider_post_url?: string | null
  publish_ready?: boolean
  publish_readiness_hint?: string | null
}

export type DraftBatch = {
  batch_id: string
  batch_type?: string  // 'theme' | 'content' | 'direct'
  parent_batch_id?: string | null
  agent_id: string
  hired_instance_id?: string | null
  customer_id?: string | null
  theme: string
  brand_name: string
  created_at: string
  status: string
  posts: DraftPost[]
}

export type CreateDraftBatchInput = {
  agent_id: string
  hired_instance_id?: string | null
  campaign_id?: string | null
  batch_type?: string  // 'theme' | 'content' | 'direct'
  parent_batch_id?: string | null
  theme: string
  brand_name: string
  brief_summary?: string | null
  offer?: string | null
  location?: string | null
  audience?: string | null
  tone?: string | null
  language?: string | null
  youtube_credential_ref?: string | null
  youtube_visibility?: string
  public_release_requested?: boolean
  channels?: string[] | null
  requested_artifacts?: DraftArtifactRequest[] | null
}

export type CreateContentFromThemeInput = {
  youtube_credential_ref?: string | null
  youtube_visibility?: string
  public_release_requested?: boolean
  requested_artifacts?: DraftArtifactRequest[] | null
}

export type ExecuteDraftPostInput = {
  post_id: string
  agent_id: string
  purpose?: string | null
  intent_action?: string
  approval_id?: string | null
}

export type ExecuteDraftPostResponse = {
  allowed: boolean
  decision_id: string
  post_id: string
  execution_status?: string | null
  provider_post_id?: string | null
  provider_post_url?: string | null
}

export async function listCustomerDraftBatches(): Promise<DraftBatch[]> {
  return gatewayRequestJson<DraftBatch[]>('/cp/marketing/draft-batches')
}

export async function createDraftBatch(input: CreateDraftBatchInput): Promise<DraftBatch> {
  return gatewayRequestJson<DraftBatch>('/cp/marketing/draft-batches', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
  })
}

export async function executeDraftPost(input: ExecuteDraftPostInput): Promise<ExecuteDraftPostResponse> {
  return gatewayRequestJson<ExecuteDraftPostResponse>('/cp/marketing/draft-posts/execute', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
  })
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

export type ArtifactStatus = {
  post_id: string
  artifact_type: string
  artifact_generation_status: 'not_requested' | 'queued' | 'running' | 'ready' | 'failed'
  artifact_uri?: string | null
  artifact_preview_uri?: string | null
  artifact_mime_type?: string | null
  artifact_job_id?: string | null
}

export async function pollDraftPostArtifactStatus(postId: string): Promise<ArtifactStatus> {
  return gatewayRequestJson<ArtifactStatus>(`/cp/marketing/draft-posts/${postId}/artifact-status`)
}

export async function createContentBatchFromTheme(
  themeBatchId: string,
  input: CreateContentFromThemeInput
): Promise<DraftBatch> {
  return gatewayRequestJson<DraftBatch>(
    `/cp/marketing/draft-batches/${themeBatchId}/create-content-batch`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(input),
    }
  )
}
