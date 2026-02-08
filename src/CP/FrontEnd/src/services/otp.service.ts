import config from '../config/oauth.config'

export type OtpStartResponse = {
  otp_id: string
  channel: 'email' | 'phone'
  destination_masked: string
  expires_in_seconds: number
  otp_code?: string | null
}

export type TokenResponse = {
  access_token: string
  refresh_token?: string
  token_type: string
  expires_in: number
}

export async function startOtp(registrationId: string): Promise<OtpStartResponse> {
  const response = await fetch(`${config.apiBaseUrl}/cp/auth/otp/start`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ registration_id: registrationId })
  })

  if (!response.ok) {
    const err = await response.json().catch(() => null)
    throw new Error(err?.detail || 'Failed to start OTP')
  }

  return response.json()
}

export async function startLoginOtp(payload: { email?: string; phone?: string; channel?: 'email' | 'phone' }): Promise<OtpStartResponse> {
  const response = await fetch(`${config.apiBaseUrl}/cp/auth/otp/login/start`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      email: payload.email,
      phone: payload.phone,
      channel: payload.channel
    })
  })

  if (!response.ok) {
    const err = await response.json().catch(() => null)
    throw new Error(err?.detail || 'Failed to start OTP')
  }

  return response.json()
}

export async function verifyOtp(otpId: string, code: string): Promise<TokenResponse> {
  const response = await fetch(`${config.apiBaseUrl}/cp/auth/otp/verify`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ otp_id: otpId, code })
  })

  if (!response.ok) {
    const err = await response.json().catch(() => null)
    throw new Error(err?.detail || 'Failed to verify OTP')
  }

  return response.json()
}
