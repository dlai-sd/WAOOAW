import config from '../config/oauth.config'

export type RegistrationCreatePayload = {
  fullName: string
  businessName: string
  businessIndustry: string
  businessAddress: string
  email: string
  phoneCountry: string
  phoneNationalNumber: string
  /** OTP session from /register/otp/start — required (OTP-first flow) */
  otpSessionId: string
  /** OTP code entered by the user — required (OTP-first flow) */
  otpCode: string
  website?: string
  gstNumber?: string
  preferredContactMethod: 'email' | 'phone'
  consent: boolean
}

export type RegistrationResponse = {
  registration_id: string
  email: string
  phone: string
  // JWT tokens — present when registration also authenticates the new user
  access_token?: string
  refresh_token?: string
  token_type?: string
  expires_in?: number
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
