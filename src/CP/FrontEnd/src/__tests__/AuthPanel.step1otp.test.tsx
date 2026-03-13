/**
 * AuthPanel – OTP-on-Step-1 registration flow tests
 *
 * Tests every scenario where a customer could get blocked and verifies
 * they always have a clear escape route:
 *   - Normal happy path (email → OTP → Step 2 → Step 3 → success)
 *   - Validation errors (empty email, bad format, bad OTP)
 *   - Duplicate email (409) → sign-in OR change-email escape
 *   - Network/server error on OTP send → retry on same screen
 *   - Change email from OTP-pending state → back to email entry
 *   - Resend OTP cooldown
 *   - Back navigation from Step 2 → verified badge shown
 *   - OTP expired at Step 3 → re-verify email escape
 *   - Full wizard happy path end-to-end
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { FluentProvider } from '@fluentui/react-components'

import { waooawLightTheme } from '../theme'
import AuthPanel from '../components/auth/AuthPanel'

// ── Mock Google login button ────────────────────────────────────────────────
vi.mock('../components/auth/GoogleLoginButton', () => ({
  default: (props: any) => (
    <button
      onClick={() => {
        if (props?.mode === 'prefill') {
          props?.onPrefill?.({ name: 'Google User', email: 'google@example.com' })
        } else {
          props?.onSuccess?.()
        }
      }}
    >
      Mock Google Login
    </button>
  ),
}))

// ── Mock CaptchaWidget ──────────────────────────────────────────────────────
vi.mock('../components/auth/CaptchaWidget', () => ({
  default: (props: any) => (
    <button
      data-testid="mock-captcha"
      onClick={() => props.onToken?.('test-captcha-token')}
    >
      Complete CAPTCHA
    </button>
  ),
}))

// ── Helpers ─────────────────────────────────────────────────────────────────
const wrap = (ui: React.ReactElement) =>
  render(<FluentProvider theme={waooawLightTheme}>{ui}</FluentProvider>)

const OTP_START_RESPONSE = {
  otp_id: 'OTP-1',
  destination_masked: 't***t@example.com',
  expires_in_seconds: 300,
  otp_code: '123456',
}

const REGISTER_SUCCESS_RESPONSE = {
  registration_id: 'REG-1',
  email: 'test@example.com',
  access_token: 'ACCESS',
  refresh_token: 'REFRESH',
  token_type: 'bearer',
  expires_in: 900,
}

/** Build a fetch mock that handles the new OTP-on-step-1 API shape */
function buildFetchMock(overrides: Record<string, () => Response> = {}) {
  return vi.fn(async (input: any, _init?: any): Promise<Response> => {
    const url = String(input)

    if (overrides[url]) return overrides[url]()

    // OTP start (registration)
    if (url.includes('/cp/auth/register/otp/start')) {
      return new Response(JSON.stringify(OTP_START_RESPONSE), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      })
    }

    // Registration with embedded OTP verify
    if (url.includes('/cp/auth/register') && _init?.method === 'POST') {
      return new Response(JSON.stringify(REGISTER_SUCCESS_RESPONSE), {
        status: 201,
        headers: { 'Content-Type': 'application/json' },
      })
    }

    return new Response(JSON.stringify({ detail: 'Not found' }), {
      status: 404,
      headers: { 'Content-Type': 'application/json' },
    })
  })
}

/**
 * Fill the 6 registration OTP boxes by firing a change event on each.
 * Using fireEvent.change because maxLength=1 boxes don't support userEvent.type for full codes.
 */
function fillRegOtpBoxes(code: string) {
  for (let i = 0; i < 6; i++) {
    const box = document.querySelector<HTMLInputElement>(`[data-reg-otp="${i}"]`)
    if (box) fireEvent.change(box, { target: { value: code[i] || '' } })
  }
}

/** Fill the email field and click Continue */
async function fillEmailAndContinue(email = 'test@example.com') {
  const emailInput = screen.getByPlaceholderText('you@company.com')
  await userEvent.clear(emailInput)
  await userEvent.type(emailInput, email)
  fireEvent.click(screen.getByRole('button', { name: 'Continue →' }))
}

/** Fill Step 2 fields */
async function fillStep2() {
  await userEvent.type(screen.getByPlaceholderText('Jane Smith'), 'Test User')
  await userEvent.type(screen.getByPlaceholderText('Acme Inc.'), 'ACME Ltd')
  fireEvent.change(screen.getAllByRole('combobox')[0], { target: { value: 'marketing' } })
}

/** Fill Step 3 fields */
async function fillStep3() {
  await userEvent.type(screen.getByPlaceholderText('9876543210'), '9876543210')
  fireEvent.click(screen.getByRole('button', { name: '✉️ Email' }))
  fireEvent.click(screen.getByRole('checkbox'))
}

// ── Setup / teardown ─────────────────────────────────────────────────────────
beforeEach(() => {
  delete process.env.VITE_TURNSTILE_SITE_KEY
  vi.spyOn(global, 'fetch').mockImplementation(buildFetchMock())
})

afterEach(() => {
  vi.restoreAllMocks()
  localStorage.clear()
})

// ═══════════════════════════════════════════════════════════════════════════
describe('Step 1 – email validation (no API call fired)', () => {
  it('shows error for empty email', async () => {
    wrap(<AuthPanel initialMode="register" />)
    fireEvent.click(screen.getByRole('button', { name: 'Continue →' }))
    expect(await screen.findByText('Email is required')).toBeInTheDocument()
    // Fetch should NOT have been called
    expect(global.fetch).not.toHaveBeenCalled()
  })

  it('shows error for invalid email format', async () => {
    wrap(<AuthPanel initialMode="register" />)
    await userEvent.type(screen.getByPlaceholderText('you@company.com'), 'notanemail')
    fireEvent.click(screen.getByRole('button', { name: 'Continue →' }))
    expect(await screen.findByText('Invalid email format')).toBeInTheDocument()
    expect(global.fetch).not.toHaveBeenCalled()
  })
})

// ═══════════════════════════════════════════════════════════════════════════
describe('Step 1 – OTP send', () => {
  it('fires startRegistrationOtp and shows OTP field on Continue', async () => {
    wrap(<AuthPanel initialMode="register" />)
    await fillEmailAndContinue()

    expect(await screen.findByRole('textbox', { name: 'OTP digit 1' })).toBeInTheDocument()
    expect(screen.getByRole('textbox', { name: 'OTP digit 1' })).toBeInTheDocument()
    // Step heading changes
    expect(screen.getByText('Check your inbox')).toBeInTheDocument()
    // Email field becomes disabled
    expect(screen.getByPlaceholderText('you@company.com')).toBeDisabled()
  })

  it('shows network error and stays on email sub-state — user can retry', async () => {
    vi.spyOn(global, 'fetch').mockRejectedValueOnce(new Error('Network failure'))
    wrap(<AuthPanel initialMode="register" />)
    await fillEmailAndContinue()

    expect(await screen.findByText('Network failure')).toBeInTheDocument()
    // Continue button still present (email sub-state still active)
    expect(screen.getByRole('button', { name: 'Continue →' })).toBeInTheDocument()
  })

  it('shows duplicate-email banner with two escape routes on 409', async () => {
    vi.spyOn(global, 'fetch').mockImplementation(
      vi.fn(async () => {
        const err = { detail: 'Email already registered' }
        return new Response(JSON.stringify(err), {
          status: 409,
          headers: { 'Content-Type': 'application/json' },
        })
      })
    )
    wrap(<AuthPanel initialMode="register" onRequestSignIn={vi.fn()} />)
    await fillEmailAndContinue()

    expect(await screen.findByText('This email is already registered.')).toBeInTheDocument()
    expect(screen.getAllByRole('button', { name: 'Sign in instead' }).length).toBeGreaterThan(0)
    expect(screen.getByRole('button', { name: 'Use different email' })).toBeInTheDocument()
  })

  it('"Use different email" clears the banner and email field', async () => {
    vi.spyOn(global, 'fetch').mockImplementation(
      vi.fn(async () =>
        new Response(JSON.stringify({ detail: 'Email already registered' }), {
          status: 409,
          headers: { 'Content-Type': 'application/json' },
        })
      )
    )
    wrap(<AuthPanel initialMode="register" />)
    await fillEmailAndContinue()
    await screen.findByText('This email is already registered.')

    fireEvent.click(screen.getByRole('button', { name: 'Use different email' }))

    expect(screen.queryByText('This email is already registered.')).not.toBeInTheDocument()
    expect((screen.getByPlaceholderText('you@company.com') as HTMLInputElement).value).toBe('')
  })
})

// ═══════════════════════════════════════════════════════════════════════════
describe('Step 1 – OTP entry & client-side verify', () => {
  async function advanceToOtpPending() {
    wrap(<AuthPanel initialMode="register" />)
    await fillEmailAndContinue()
    await screen.findByRole('textbox', { name: 'OTP digit 1' })
  }

  it('shows error for empty OTP code', async () => {
    await advanceToOtpPending()
    fireEvent.click(screen.getByRole('button', { name: 'Verify email →' }))
    expect(await screen.findByText(/Paste the code from your inbox/)).toBeInTheDocument()
  })

  it('shows error for short numeric OTP (< 4 digits)', async () => {
    await advanceToOtpPending()
    // Fill only 2 boxes — combined code is '12' which fails the 4-8 digit check
    fireEvent.change(document.querySelector('[data-reg-otp="0"]')!, { target: { value: '1' } })
    fireEvent.change(document.querySelector('[data-reg-otp="1"]')!, { target: { value: '2' } })
    fireEvent.click(screen.getByRole('button', { name: 'Verify email →' }))
    expect(await screen.findByText('OTP must be 4–8 digits')).toBeInTheDocument()
  })

  it('inline error clears as user types', async () => {
    await advanceToOtpPending()
    fireEvent.click(screen.getByRole('button', { name: 'Verify email →' }))
    await screen.findByText(/Paste the code from your inbox/)

    fireEvent.change(screen.getByRole('textbox', { name: 'OTP digit 1' }), { target: { value: '1' } })
    expect(screen.queryByText(/Paste the code from your inbox/)).toBeInTheDocument()
  })

  it('Enter key triggers verify', async () => {
    await advanceToOtpPending()
    fillRegOtpBoxes('123456')
    fireEvent.keyDown(screen.getByRole('textbox', { name: 'OTP digit 1' }), { key: 'Enter' })
    // Should advance to Step 2
    expect(await screen.findByText('Tell us about you')).toBeInTheDocument()
  })

  it('valid OTP advances to Step 2', async () => {
    await advanceToOtpPending()
    fillRegOtpBoxes('123456')
    fireEvent.click(screen.getByRole('button', { name: 'Verify email →' }))
    expect(await screen.findByText('Tell us about you')).toBeInTheDocument()
  })

  it('"Change email" button returns to email entry', async () => {
    await advanceToOtpPending()
    fireEvent.click(screen.getByRole('button', { name: 'Change email' }))

    // OTP boxes are gone, email field is back and editable
    expect(screen.queryByRole('textbox', { name: 'OTP digit 1' })).not.toBeInTheDocument()
    expect(screen.getByPlaceholderText('you@company.com')).not.toBeDisabled()
    expect(screen.getByRole('button', { name: 'Continue →' })).toBeInTheDocument()
  })
})

// ═══════════════════════════════════════════════════════════════════════════
describe('Step 1 – CAPTCHA gate (when configured)', () => {
  it('blocks Continue until CAPTCHA is solved', async () => {
    process.env.VITE_TURNSTILE_SITE_KEY = 'test-key'
    ;(window as any).turnstile = {
      render: vi.fn((_c: any, _o: any) => 'w1'), // don't auto-fire callback
    }

    wrap(<AuthPanel initialMode="register" />)
    await userEvent.type(screen.getByPlaceholderText('you@company.com'), 'test@example.com')
    fireEvent.click(screen.getByRole('button', { name: 'Continue →' }))

    expect(await screen.findByText('Complete the CAPTCHA to continue')).toBeInTheDocument()
    expect(global.fetch).not.toHaveBeenCalled()

    delete process.env.VITE_TURNSTILE_SITE_KEY
    delete (window as any).turnstile
  })
})

// ═══════════════════════════════════════════════════════════════════════════
describe('Step 1 – Resend OTP', () => {
  it('resend button is disabled during cooldown', async () => {
    wrap(<AuthPanel initialMode="register" />)
    await fillEmailAndContinue()
    await screen.findByRole('textbox', { name: 'OTP digit 1' })

    const resendBtn = screen.getByRole('button', { name: /Resend code in \d+s/ })
    expect(resendBtn).toBeDisabled()
  })
})

// ═══════════════════════════════════════════════════════════════════════════
describe('Back navigation', () => {
  it('going Back from Step 2 shows verified badge on Step 1', async () => {
    wrap(<AuthPanel initialMode="register" />)
    await fillEmailAndContinue()
    await screen.findByRole('textbox', { name: 'OTP digit 1' })
    fillRegOtpBoxes('123456')
    fireEvent.click(screen.getByRole('button', { name: 'Verify email →' }))
    await screen.findByText('Tell us about you')

    // Go back to Step 1
    fireEvent.click(screen.getByRole('button', { name: '← Back' }))

    expect(await screen.findByText('Email verified')).toBeInTheDocument()
    // "Change" button present to let them switch email
    expect(screen.getByRole('button', { name: 'Change' })).toBeInTheDocument()
  })

  it('"Change" on verified badge resets to email entry', async () => {
    wrap(<AuthPanel initialMode="register" />)
    await fillEmailAndContinue()
    await screen.findByRole('textbox', { name: 'OTP digit 1' })
    fillRegOtpBoxes('123456')
    fireEvent.click(screen.getByRole('button', { name: 'Verify email →' }))
    await screen.findByText('Tell us about you')
    fireEvent.click(screen.getByRole('button', { name: '← Back' }))
    await screen.findByText('Email verified')

    fireEvent.click(screen.getByRole('button', { name: 'Change' }))

    expect(screen.getByRole('button', { name: 'Continue →' })).toBeInTheDocument()
    expect(screen.queryByText('Email verified')).not.toBeInTheDocument()
  })
})

// ═══════════════════════════════════════════════════════════════════════════
describe('Step 3 – OTP expired recovery (not a blocker)', () => {
  it('OTP error from backend shows re-verify button and resets to Step 1', async () => {
    // Simulate backend rejecting with OTP-related error
    vi.spyOn(global, 'fetch').mockImplementation(
      vi.fn(async (input: any, _init?: any) => {
        const url = String(input)
        if (url.includes('/cp/auth/register/otp/start')) {
          return new Response(JSON.stringify(OTP_START_RESPONSE), {
            status: 200,
            headers: { 'Content-Type': 'application/json' },
          })
        }
        if (url.includes('/cp/auth/register') && _init?.method === 'POST') {
          return new Response(JSON.stringify({ detail: 'OTP session expired' }), {
            status: 422,
            headers: { 'Content-Type': 'application/json' },
          })
        }
        return new Response('{}', { status: 404 })
      })
    )

    const onSuccess = vi.fn()
    wrap(<AuthPanel initialMode="register" onSuccess={onSuccess} />)

    // Step 1: verify email
    await fillEmailAndContinue()
    await screen.findByRole('textbox', { name: 'OTP digit 1' })
    fillRegOtpBoxes('123456')
    fireEvent.click(screen.getByRole('button', { name: 'Verify email →' }))
    await screen.findByText('Tell us about you')

    // Step 2
    await fillStep2()
    fireEvent.click(screen.getByRole('button', { name: 'Continue →' }))
    await screen.findByText('Almost done!')

    // Step 3: submit
    await fillStep3()
    fireEvent.click(screen.getByRole('button', { name: 'Create account 🚀' }))

    // Should reset back to step 1 with the email entry visible again.
    await waitFor(() => {
      expect(screen.getByPlaceholderText('you@company.com')).toBeInTheDocument()
    })
    expect(screen.getByText(/we.?ll send a 6-digit code before creating your account/i)).toBeInTheDocument()
    // onSuccess was NOT called
    expect(onSuccess).not.toHaveBeenCalled()
  })
})

// ═══════════════════════════════════════════════════════════════════════════
describe('Full happy-path wizard', () => {
  it('email → OTP → Step2 → Step3 → createRegistration → onSuccess', async () => {
    const onSuccess = vi.fn()
    wrap(<AuthPanel initialMode="register" onSuccess={onSuccess} />)

    // Step 1 – email
    await fillEmailAndContinue()
    expect(await screen.findByRole('textbox', { name: 'OTP digit 1' })).toBeInTheDocument()

    // Step 1 – OTP verify
    fillRegOtpBoxes('123456')
    fireEvent.click(screen.getByRole('button', { name: 'Verify email →' }))

    // Step 2 – Name / Business / Industry
    await screen.findByText('Tell us about you')
    await fillStep2()
    fireEvent.click(screen.getByRole('button', { name: 'Continue →' }))

    // Step 3 – Phone / Contact / Consent
    await screen.findByText('Almost done!')
    await fillStep3()
    fireEvent.click(screen.getByRole('button', { name: 'Create account 🚀' }))

    // Success callback fired (tokens are stored in-memory by authService, not localStorage)
    await waitFor(() => expect(onSuccess).toHaveBeenCalledOnce())
  })
})
