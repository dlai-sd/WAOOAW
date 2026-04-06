import { gatewayRequestJson } from './gatewayApiClient'

export type YouTubeConnection = {
  id: string
  customer_id: string
  platform_key: string
  provider_account_id?: string | null
  display_name?: string | null
  granted_scopes: string[]
  verification_status: string
  connection_status: string
  token_expires_at?: string | null
  last_verified_at?: string | null
  created_at: string
  updated_at: string
}

export type StartYouTubeConnectionResponse = {
  state: string
  authorization_url: string
  expires_at: string
}

export type FinalizeYouTubeConnectionInput = {
  state: string
  code: string
  redirect_uri: string
}

export type AttachYouTubeConnectionInput = {
  hired_instance_id: string
  skill_id: string
  platform_key?: string
}

export type AttachYouTubeConnectionResponse = {
  id: string
  hired_instance_id: string
  skill_id: string
  customer_platform_credential_id?: string | null
  platform_key: string
  status: string
  connected_at?: string | null
  last_verified_at?: string | null
  created_at: string
  updated_at: string
}

export type RecentUploadPreview = {
  video_id: string
  title: string
  published_at: string
  duration_seconds: number
}

export type ValidateYouTubeConnectionResponse = {
  id: string
  customer_id: string
  platform_key: string
  provider_account_id?: string | null
  display_name?: string | null
  verification_status: string
  connection_status: string
  token_expires_at?: string | null
  last_verified_at?: string | null
  channel_count: number
  total_video_count: number
  recent_short_count: number
  recent_long_video_count: number
  subscriber_count: number
  view_count: number
  recent_uploads: RecentUploadPreview[]
  next_action_hint: string
}

export async function startYouTubeConnection(redirectUri: string): Promise<StartYouTubeConnectionResponse> {
  return gatewayRequestJson<StartYouTubeConnectionResponse>('/cp/youtube-connections/connect/start', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ redirect_uri: redirectUri }),
  })
}

export async function finalizeYouTubeConnection(
  input: FinalizeYouTubeConnectionInput
): Promise<YouTubeConnection> {
  return gatewayRequestJson<YouTubeConnection>('/cp/youtube-connections/connect/finalize', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
  })
}

export async function listYouTubeConnections(): Promise<YouTubeConnection[]> {
  return gatewayRequestJson<YouTubeConnection[]>('/cp/youtube-connections')
}

export async function getYouTubeConnection(credentialId: string): Promise<YouTubeConnection> {
  return gatewayRequestJson<YouTubeConnection>(`/cp/youtube-connections/${encodeURIComponent(credentialId)}`)
}

export async function attachYouTubeConnection(
  credentialId: string,
  input: AttachYouTubeConnectionInput
): Promise<AttachYouTubeConnectionResponse> {
  return gatewayRequestJson<AttachYouTubeConnectionResponse>(
    `/cp/youtube-connections/${encodeURIComponent(credentialId)}/attach`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        hired_instance_id: input.hired_instance_id,
        skill_id: input.skill_id,
        platform_key: input.platform_key || 'youtube',
      }),
    }
  )
}

export async function validateYouTubeConnection(
  credentialId: string
): Promise<ValidateYouTubeConnectionResponse> {
  return gatewayRequestJson<ValidateYouTubeConnectionResponse>(
    `/cp/youtube-connections/${encodeURIComponent(credentialId)}/validate`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({}),
    }
  )
}