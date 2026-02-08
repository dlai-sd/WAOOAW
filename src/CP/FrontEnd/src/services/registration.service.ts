import config from '../config/oauth.config'

export type RegistrationCreatePayload = {
  fullName: string
  businessName: string
  businessIndustry: string
  businessAddress: string
  email: string
  phone: string
  website?: string
  gstNumber?: string
  preferredContactMethod: 'email' | 'phone'
  consent: boolean
}

export type RegistrationResponse = {
  registration_id: string
  email: string
  phone: string
}

export async function createRegistration(payload: RegistrationCreatePayload): Promise<RegistrationResponse> {
  const response = await fetch(`${config.apiBaseUrl}/cp/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  })

  if (!response.ok) {
    const err = await response.json().catch(() => null)
    throw new Error(err?.detail || 'Failed to register')
  }

  return response.json()
}
