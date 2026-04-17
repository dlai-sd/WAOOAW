import apiClient from '@/lib/apiClient'

function generateCorrelationId(): string {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0
    const v = c === 'x' ? r : (r & 0x3) | 0x8
    return v.toString(16)
  })
}

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
  batch_type?: string
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
  batch_type?: string
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

export type ArtifactStatus = {
  post_id: string
  artifact_type: string
  artifact_generation_status: 'not_requested' | 'queued' | 'running' | 'ready' | 'failed'
  artifact_uri?: string | null
  artifact_preview_uri?: string | null
  artifact_mime_type?: string | null
  artifact_job_id?: string | null
}

export async function listCustomerDraftBatches(): Promise<DraftBatch[]> {
  const resp = await apiClient.get('/api/v1/marketing/draft-batches')
  return resp.data
}

export async function createDraftBatch(input: CreateDraftBatchInput): Promise<DraftBatch> {
  const resp = await apiClient.post('/api/v1/marketing/draft-batches', input, {
    headers: { 'X-Correlation-ID': generateCorrelationId(), 'Content-Type': 'application/json' },
  })
  return resp.data
}

export async function approveDraftPost(
  postId: string
): Promise<{ post_id: string; review_status: string; approval_id: string }> {
  const resp = await apiClient.post(
    `/api/v1/marketing/draft-posts/${postId}/approve`,
    {},
    { headers: { 'X-Correlation-ID': generateCorrelationId(), 'Content-Type': 'application/json' } }
  )
  return resp.data
}

export async function rejectDraftPost(
  postId: string,
  reason?: string
): Promise<{ post_id: string; decision: string }> {
  const resp = await apiClient.post(
    `/api/v1/marketing/draft-posts/${postId}/reject`,
    { reason },
    { headers: { 'X-Correlation-ID': generateCorrelationId(), 'Content-Type': 'application/json' } }
  )
  return resp.data
}

export async function pollDraftPostArtifactStatus(postId: string): Promise<ArtifactStatus> {
  const resp = await apiClient.get(`/api/v1/marketing/draft-posts/${postId}/artifact-status`)
  return resp.data
}

export async function createContentBatchFromTheme(
  themeBatchId: string,
  input: CreateContentFromThemeInput
): Promise<DraftBatch> {
  const resp = await apiClient.post(
    `/api/v1/marketing/draft-batches/${themeBatchId}/create-content-batch`,
    input,
    { headers: { 'X-Correlation-ID': generateCorrelationId(), 'Content-Type': 'application/json' } }
  )
  return resp.data
}
