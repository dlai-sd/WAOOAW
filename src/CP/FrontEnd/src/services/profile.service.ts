/**
 * Profile service — E4-S2 (CP-NAV-1 Iteration 2)
 * Handles GET and PATCH /cp/profile API calls
 */

import { gatewayRequestJson } from './gatewayApiClient'

export interface ProfileData {
  id: string
  email: string
  name?: string
  full_name?: string
  phone?: string
  business_name?: string
  industry?: string
  picture?: string
}

export interface ProfileUpdatePayload {
  full_name?: string
  phone?: string
  business_name?: string
  industry?: string
}

export async function getProfile(): Promise<ProfileData> {
  return gatewayRequestJson<ProfileData>('/cp/profile', { method: 'GET' })
}

export async function updateProfile(payload: ProfileUpdatePayload): Promise<ProfileData> {
  return gatewayRequestJson<ProfileData>('/cp/profile', {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}
