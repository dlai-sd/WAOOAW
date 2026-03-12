import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { FluentProvider } from '@fluentui/react-components'

import { waooawLightTheme } from '../theme'
import AuthModal from '../components/auth/AuthModal'

vi.mock('../components/auth/GoogleLoginButton', () => ({
  default: (props: any) => (
    <button
      onClick={() => {
        if (props?.mode === 'prefill') {
          props?.onPrefill?.({ name: 'Google User', email: 'google@example.com' })
          return
        }
        props?.onSuccess?.()
      }}
    >
      Mock Google Login
    </button>
  )
}))

// ── Shared fetch mock factory ───────────────────────────────────────────────
function buildFetch(otpCodeFn?: () => string) {
  let otpStartCalls = 0
  return vi.fn(async (input: any, init?: any): Promise<Response> => {
    const url = String(input)

    if (url.includes('/cp/auth/register/otp/start') && init?.method === 'POST') {
      otpStartCalls += 1
      const code = otpCodeFn ? otpCodeFn() : '123456'
      return new Response(
        JSON.stringify({ otp_id: `OTP-${otpStartCalls}`, destination_masked: 't***t@example.com', expires_in_seconds: 300, otp_code: code }),
        { status: 200, headers: { 'Content-Type': 'application/json' } }
      )
    }

    if (url.includes('/cp/auth/register') && init?.method === 'POST') {
      return new Response(
        JSON.stringify({ registration_id: 'REG-1', email: 'test@example.com', access_token: 'ACCESS', refresh_token: 'REFRESH', token_type: 'bearer', expires_in: 900 }),
        { status: 201, headers: { 'Content-Type': 'application/json' } }
      )
    }

    // Sign-in OTP (for the passing sign-in test)
    if (url.includes('/cp/auth/otp/login/start') && init?.method === 'POST') {
      otpStartCalls += 1
      const code = otpCodeFn ? otpCodeFn() : '111111'
      return new Response(
        JSON.stringify({ otp_id: `OTP-L-${otpStartCalls}`, channel: 'email', destination_masked: 't***t@example.com', expires_in_seconds: 300, otp_code: code }),
        { status: 200, headers: { 'Content-Type': 'application/json' } }
      )
    }

    if (url.includes('/cp/auth/otp/verify') && init?.method === 'POST') {
      return new Response(
        JSON.stringify({ access_token: 'ACCESS', refresh_token: 'REFRESH', token_type: 'bearer', expires_in: 900 }),
        { status: 200, headers: { 'Content-Type': 'application/json' } }
      )
    }

    return new Response(JSON.stringify({ detail: 'Not found' }), { status: 404, headers: { 'Content-Type': 'application/json' } })
  })
}

describe('AuthModal registration (REG-1.1)', () => {
  beforeEach(() => {
    delete process.env.VITE_TURNSTILE_SITE_KEY  // no CAPTCHA blocker by default
    vi.spyOn(global, 'fetch').mockImplementation(buildFetch())
  })

  afterEach(() => {
    vi.useRealTimers()
    vi.restoreAllMocks()
    localStorage.clear()
    delete (window as any).turnstile
    delete process.env.VITE_TURNSTILE_SITE_KEY
  })

  const renderModal = () =>
    render(
      <FluentProvider theme={waooawLightTheme}>
        <AuthModal open onClose={vi.fn()} onSuccess={vi.fn()} theme="light" />
      </FluentProvider>
    )

  // ── Helpers that walk the wizard ──────────────────────────────────────────

  /** Fill the 6 registration OTP boxes using fireEvent.change */
  function fillRegOtpBoxes(code: string) {
    for (let i = 0; i < 6; i++) {
      const box = document.querySelector<HTMLInputElement>(`[data-reg-otp="${i}"]`)
      if (box) fireEvent.change(box, { target: { value: code[i] || '' } })
    }
  }

  /** Step 1: fill email → fire OTP → enter code → advance to Step 2 */
  async function completeStep1(email = 'test@example.com', otpCode = '123456') {
    fireEvent.click(screen.getByRole('button', { name: /Don.?t have an account\? Sign up/ }))
    await userEvent.type(screen.getByPlaceholderText('you@company.com'), email)
    fireEvent.click(screen.getByRole('button', { name: 'Continue →' }))
    await screen.findByRole('textbox', { name: 'OTP digit 1' })
    fillRegOtpBoxes(otpCode)
    fireEvent.click(screen.getByRole('button', { name: 'Verify email →' }))
    await screen.findByText('Tell us about you')
  }

  /** Step 2: fill name / business / industry → Continue */
  async function completeStep2(name = 'Test User', business = 'ACME Ltd') {
    await userEvent.type(screen.getByPlaceholderText('Jane Smith'), name)
    await userEvent.type(screen.getByPlaceholderText('Acme Inc.'), business)
    fireEvent.change(screen.getAllByRole('combobox')[0], { target: { value: 'marketing' } })
    fireEvent.click(screen.getByRole('button', { name: 'Continue →' }))
    await screen.findByText('Almost done!')
  }

  /** Step 3: fill phone + contact + consent */
  async function completeStep3() {
    await userEvent.type(screen.getByPlaceholderText('9876543210'), '9876543210')
    fireEvent.click(screen.getByRole('button', { name: '✉️ Email' }))
    fireEvent.click(screen.getByRole('checkbox'))
  }

  // ── Tests ─────────────────────────────────────────────────────────────────

  it('shows registration form and requires consent', async () => {
    renderModal()

    // Modal opens on sign-in by default; switch to register
    fireEvent.click(screen.getByRole('button', { name: /Don.?t have an account\? Sign up/ }))
    expect(screen.getByText('Create your WAOOAW account')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('you@company.com')).toBeInTheDocument()

    // Step 1 → OTP → Step 2
    await userEvent.type(screen.getByPlaceholderText('you@company.com'), 'test@example.com')
    fireEvent.click(screen.getByRole('button', { name: 'Continue →' }))
    await screen.findByRole('textbox', { name: 'OTP digit 1' })
    fillRegOtpBoxes('123456')
    fireEvent.click(screen.getByRole('button', { name: 'Verify email →' }))

    // Step 2 fields visible
    expect(await screen.findByPlaceholderText('Jane Smith')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('Acme Inc.')).toBeInTheDocument()
    await completeStep2()

    // Step 3 — consent required before submit
    const submitBtn = screen.getByRole('button', { name: 'Create account 🚀' })
    expect(submitBtn).toBeDisabled()

    await completeStep3()

    await waitFor(() =>
      expect(screen.getByRole('button', { name: 'Create account 🚀' })).not.toBeDisabled()
    )

    fireEvent.click(screen.getByRole('button', { name: 'Create account 🚀' }))
    await waitFor(() => expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/cp/auth/register'),
      expect.objectContaining({ method: 'POST' })
    ))
  })

  it('prefills name and email from Google', async () => {
    renderModal()

    fireEvent.click(screen.getByRole('button', { name: /Don.?t have an account\? Sign up/ }))
    fireEvent.click(screen.getByRole('button', { name: 'Mock Google Login' }))

    await waitFor(() =>
      expect((screen.getByPlaceholderText('you@company.com') as HTMLInputElement).value).toBe('google@example.com')
    )

    // OTP flow continues with the prefilled email
    fireEvent.click(screen.getByRole('button', { name: 'Continue →' }))
    await screen.findByRole('textbox', { name: 'OTP digit 1' })
    fillRegOtpBoxes('123456')
    fireEvent.click(screen.getByRole('button', { name: 'Verify email →' }))

    // Step 2: name field should be pre-filled from Google
    expect(await screen.findByDisplayValue('Google User')).toBeInTheDocument()
  })

  it('allows resend OTP after cooldown (NOTIF-1.4)', async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true })
    let call = 0
    vi.spyOn(global, 'fetch').mockImplementation(buildFetch(() => (++call === 1 ? '123456' : '654321')))

    renderModal()
    await act(async () => {})

    // Switch to register mode then get into OTP-pending state
    fireEvent.click(screen.getByRole('button', { name: /Don.?t have an account\? Sign up/ }))
    await act(async () => {
      fireEvent.change(screen.getByPlaceholderText('you@company.com'), { target: { value: 'test@example.com' } })
    })
    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: 'Continue →' }))
    })

    // OTP code field appears — flush timers then check synchronously
    await act(async () => { vi.advanceTimersByTime(100) })
    expect(screen.getByRole('textbox', { name: 'OTP digit 1' })).toBeInTheDocument()

    // Resend is disabled during cooldown
    const resendDisabled = screen.getByRole('button', { name: /Resend code in \d+s/ })
    expect(resendDisabled).toBeDisabled()

    // Advance past cooldown
    await act(async () => { vi.advanceTimersByTime(30_000) })

    const resendEnabled = screen.getByRole('button', { name: 'Resend code' })
    expect(resendEnabled).not.toBeDisabled()

    // Click resend → second OTP start call
    await act(async () => { fireEvent.click(resendEnabled) })
    expect(screen.getByRole('textbox', { name: 'OTP digit 1' })).toBeInTheDocument()
  })

  it('cancel exits registration flow', () => {
    const onClose = vi.fn()
    render(
      <FluentProvider theme={waooawLightTheme}>
        <AuthModal open onClose={onClose} onSuccess={vi.fn()} theme="light" />
      </FluentProvider>
    )

    fireEvent.click(screen.getByRole('button', { name: /Don.?t have an account\? Sign up/ }))
    // Close via the × icon button
    fireEvent.click(screen.getByRole('button', { name: 'Close' }))
    expect(onClose).toHaveBeenCalledTimes(1)
  })

  it('allows resend OTP after cooldown in sign-in flow (NOTIF-1.4)', async () => {
    vi.useFakeTimers()

    let startCalls = 0
    ;(global.fetch as any).mockImplementation(async (input: any, init?: any) => {
      const url = String(input)

      if (url.endsWith('/cp/auth/otp/login/start') && init?.method === 'POST') {
        startCalls += 1
        return new Response(
          JSON.stringify({
            otp_id: `OTP-L-${startCalls}`,
            channel: 'email',
            destination_masked: 't***t@example.com',
            expires_in_seconds: 300,
            otp_code: startCalls === 1 ? '111111' : '222222'
          }),
          { status: 200, headers: { 'Content-Type': 'application/json' } }
        )
      }

      if (url.endsWith('/cp/auth/otp/verify') && init?.method === 'POST') {
        return new Response(
          JSON.stringify({ access_token: 'ACCESS', refresh_token: 'REFRESH', token_type: 'bearer', expires_in: 900 }),
          { status: 200, headers: { 'Content-Type': 'application/json' } }
        )
      }

      return new Response(JSON.stringify({ detail: 'Not found' }), {
        status: 404,
        headers: { 'Content-Type': 'application/json' }
      })
    })

    renderModal()
    await act(async () => {})

    fireEvent.change(screen.getByPlaceholderText('you@company.com'), { target: { value: 'test@example.com' } })

    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: 'Send OTP' }))
    })

    expect(startCalls).toBe(1)
    expect(screen.getByRole('textbox', { name: 'OTP digit 1' })).toBeInTheDocument()

    const resendButton = screen.getByRole('button', { name: /Resend OTP/i })
    expect(resendButton).toBeDisabled()

    await act(async () => {
      vi.advanceTimersByTime(30_000)
    })

    expect(screen.getByRole('button', { name: 'Resend OTP' })).not.toBeDisabled()

    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: 'Resend OTP' }))
    })

    expect(startCalls).toBe(2)
    expect(screen.getByRole('textbox', { name: 'OTP digit 1' })).toBeInTheDocument()
  })
})
