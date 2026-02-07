import { gatewayRequestJson } from './gatewayApiClient'

export type PlatformCredential = {
  credential_ref: string
  customer_id: string
  platform: string
  posting_identity?: string | null
  created_at: string
  updated_at: string
  metadata?: Record<string, unknown>
}

export async function listPlatformCredentials(): Promise<PlatformCredential[]> {
  return gatewayRequestJson<PlatformCredential[]>('/cp/platform-credentials')
}

export type UpsertPlatformCredentialInput = {
  credential_ref?: string
  platform: string
  posting_identity?: string
  access_token: string
  refresh_token?: string
}

export async function upsertPlatformCredential(
  input: UpsertPlatformCredentialInput
): Promise<PlatformCredential> {
  return gatewayRequestJson<PlatformCredential>('/cp/platform-credentials', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input)
  })
}
