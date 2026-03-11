import { gatewayRequestJson } from './gatewayApiClient'

export type Deliverable = {
  deliverable_id: string
  hired_instance_id: string
  goal_instance_id: string
  goal_template_id: string

  title: string
  payload: Record<string, unknown>

  review_status: 'pending_review' | 'approved' | 'rejected' | string
  review_notes?: string | null
  approval_id?: string | null

  execution_status: 'not_executed' | 'executed' | string
  executed_at?: string | null

  created_at?: string | null
  updated_at?: string | null
}

export type DeliverableChannelTarget = {
  platformKey: string | null
  handle: string | null
  visibility: string
  publicReleaseRequested: boolean
  credentialRef: string | null
  publishStatus: string
  platformPostId: string | null
}

export type DeliverablePublishReadiness = {
  key:
    | 'already_published'
    | 'publish_failed'
    | 'blocked_missing_approval'
    | 'blocked_rejected'
    | 'blocked_missing_channel_connection'
    | 'uploaded_non_public'
    | 'ready_for_public_release'
    | 'ready_for_upload'
  label: string
  message: string
  tone: 'success' | 'warning' | 'danger' | 'informative'
}

export type DeliverablesListResponse = {
  hired_instance_id: string
  deliverables: Deliverable[]
}

export type ReviewDeliverableInput = {
  decision: 'approved' | 'rejected'
  notes?: string | null
  approval_id?: string | null
}

export type ReviewDeliverableResponse = {
  deliverable_id: string
  review_status: string
  approval_id?: string | null
  updated_at?: string | null
}

function asRecord(value: unknown): Record<string, unknown> | null {
  if (!value || typeof value !== 'object' || Array.isArray(value)) {
    return null
  }
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

export function getDeliverableChannelTarget(deliverable: Deliverable): DeliverableChannelTarget {
  const payload = asRecord(deliverable.payload) || {}
  const destination = asRecord(payload.destination) || asRecord(payload.destination_ref) || {}
  const metadata = asRecord(destination.metadata) || asRecord(payload.metadata) || {}
  const publishReceipt = asRecord(payload.publish_receipt) || {}

  const platformKey =
    stringOrNull(destination.destination_type) ||
    stringOrNull(payload.destination_type) ||
    stringOrNull(payload.channel) ||
    stringOrNull(payload.platform) ||
    stringOrNull(payload.primary_destination)

  const visibility =
    stringOrNull(metadata.visibility) ||
    stringOrNull(payload.visibility) ||
    'private'

  const publishStatus =
    stringOrNull(payload.publish_status) ||
    stringOrNull((publishReceipt as Record<string, unknown>).status) ||
    'not_published'

  return {
    platformKey,
    handle: stringOrNull(destination.handle) || stringOrNull(payload.channel_handle),
    visibility,
    publicReleaseRequested:
      booleanFromUnknown(metadata.public_release_requested) ||
      booleanFromUnknown(payload.public_release_requested),
    credentialRef:
      stringOrNull(metadata.credential_ref) ||
      stringOrNull(payload.credential_ref),
    publishStatus,
    platformPostId:
      stringOrNull((publishReceipt as Record<string, unknown>).platform_post_id) ||
      stringOrNull(payload.platform_post_id),
  }
}

export function getDeliverablePublishReadiness(
  deliverable: Deliverable,
  options?: { hasPlatformConnection?: boolean | null; platformLabel?: string | null }
): DeliverablePublishReadiness {
  const reviewStatus = String(deliverable.review_status || '').trim().toLowerCase() || 'pending_review'
  const executionStatus = String(deliverable.execution_status || '').trim().toLowerCase()
  const channel = getDeliverableChannelTarget(deliverable)
  const platformLabel = options?.platformLabel || channel.platformKey || 'the publishing channel'
  const publishStatus = String(channel.publishStatus || '').trim().toLowerCase()
  const hasPlatformConnection = options?.hasPlatformConnection

  if (publishStatus === 'published' || channel.platformPostId) {
    return {
      key: 'already_published',
      label: 'Already published',
      message: `This deliverable already has a live ${platformLabel} publish receipt.`,
      tone: 'success',
    }
  }

  if (publishStatus === 'failed') {
    return {
      key: 'publish_failed',
      label: 'Publish failed',
      message: `The last ${platformLabel} publish attempt failed. Review the channel state before retrying.`,
      tone: 'danger',
    }
  }

  if (reviewStatus === 'rejected') {
    return {
      key: 'blocked_rejected',
      label: 'Blocked by rejection',
      message: 'This draft was rejected, so nothing will upload until a revised deliverable is approved.',
      tone: 'danger',
    }
  }

  if (reviewStatus !== 'approved') {
    return {
      key: 'blocked_missing_approval',
      label: 'Blocked by approval',
      message: 'This draft is review-ready, but nothing can publish until you approve the exact deliverable.',
      tone: 'warning',
    }
  }

  if (hasPlatformConnection === false) {
    return {
      key: 'blocked_missing_channel_connection',
      label: 'Blocked by missing channel connection',
      message: `Approve is complete, but ${platformLabel} still needs a verified connection before upload can happen.`,
      tone: 'danger',
    }
  }

  if (executionStatus === 'executed' && channel.visibility !== 'public') {
    return {
      key: 'uploaded_non_public',
      label: 'Uploaded as non-public',
      message: `The content has been uploaded to ${platformLabel} with ${channel.visibility} visibility and is not public yet.`,
      tone: 'informative',
    }
  }

  if (channel.publicReleaseRequested || channel.visibility === 'public') {
    return {
      key: 'ready_for_public_release',
      label: 'Ready for public release',
      message: `Approval and channel readiness are satisfied. The next ${platformLabel} step can release this publicly.`,
      tone: 'success',
    }
  }

  return {
    key: 'ready_for_upload',
    label: 'Ready for upload',
    message: `Approval is in place and ${platformLabel} is ready. The next step can upload this without making it public automatically.`,
    tone: 'success',
  }
}

export async function listHiredAgentDeliverables(hiredInstanceId: string): Promise<DeliverablesListResponse> {
  return gatewayRequestJson<DeliverablesListResponse>(
    `/cp/hired-agents/${encodeURIComponent(hiredInstanceId)}/deliverables`,
    { method: 'GET' }
  )
}

export async function reviewHiredAgentDeliverable(
  deliverableId: string,
  input: ReviewDeliverableInput
): Promise<ReviewDeliverableResponse> {
  return gatewayRequestJson<ReviewDeliverableResponse>(
    `/cp/hired-agents/deliverables/${encodeURIComponent(deliverableId)}/review`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(input)
    }
  )
}
