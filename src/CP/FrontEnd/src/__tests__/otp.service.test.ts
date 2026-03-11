import { beforeEach, describe, expect, it, vi } from 'vitest'
import { startLoginOtp } from '../services/otp.service'

vi.mock('../config/oauth.config', () => ({
  default: {
    apiBaseUrl: 'https://cp.demo.waooaw.com/api'
  }
}))

describe('startLoginOtp', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('falls back to /cp/auth/otp/start when /login/start returns 404', async () => {
    const fetchSpy = vi.spyOn(globalThis, 'fetch' as never)
      .mockResolvedValueOnce(new Response(JSON.stringify({ detail: 'not found' }), { status: 404, headers: { 'Content-Type': 'application/json' } }) as never)
      .mockResolvedValueOnce(new Response(JSON.stringify({ otp_id: 'otp-1', channel: 'email', destination_masked: 't***@e***.com', expires_in_seconds: 300 }), { status: 200, headers: { 'Content-Type': 'application/json' } }) as never)

    const result = await startLoginOtp({ email: 'test@example.com', channel: 'email' })

    expect(result.otp_id).toBe('otp-1')
    expect(fetchSpy).toHaveBeenNthCalledWith(
      2,
      'https://cp.demo.waooaw.com/api/cp/auth/otp/start',
      expect.objectContaining({ method: 'POST' })
    )
  })

  it('surfaces the primary route error when /login/start fails with non-404', async () => {
    vi.spyOn(globalThis, 'fetch' as never)
      .mockResolvedValueOnce(new Response(JSON.stringify({ detail: 'Too many OTP requests' }), { status: 429, headers: { 'Content-Type': 'application/json' } }) as never)

    await expect(startLoginOtp({ email: 'test@example.com', channel: 'email' })).rejects.toThrow('Too many OTP requests')
  })
})