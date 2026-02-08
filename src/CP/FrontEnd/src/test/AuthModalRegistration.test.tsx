import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { FluentProvider } from '@fluentui/react-components'

import { waooawLightTheme } from '../theme'
import AuthModal from '../components/auth/AuthModal'

vi.mock('../components/auth/GoogleLoginButton', () => ({
  default: () => <button>Mock Google Login</button>
}))

describe('AuthModal registration (REG-1.1)', () => {
  beforeEach(() => {
    // Provide a dummy site key so the UI doesn’t block on missing config.
    // AuthModal supports a safe process.env fallback for Vitest.
    process.env.VITE_TURNSTILE_SITE_KEY = 'test-site-key'

    ;(window as any).turnstile = {
      render: vi.fn((_container: any, options: any) => {
        // Immediately emit a token to simulate a completed CAPTCHA.
        options.callback('test-captcha-token')
        return 'widget-1'
      })
    }

    vi.spyOn(global, 'fetch').mockImplementation(async (input: any, init?: any) => {
      const url = String(input)

      if (url.endsWith('/cp/auth/register') && init?.method === 'POST') {
        return new Response(
          JSON.stringify({ registration_id: 'REG-1', email: 'test@example.com', phone: '+919876543210' }),
          { status: 201, headers: { 'Content-Type': 'application/json' } }
        )
      }

      if (url.endsWith('/cp/auth/otp/start') && init?.method === 'POST') {
        return new Response(
          JSON.stringify({ otp_id: 'OTP-1', channel: 'email', destination_masked: 't***t@example.com', expires_in_seconds: 300, otp_code: '123456' }),
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
  })

  afterEach(() => {
    delete (window as any).turnstile
    delete process.env.VITE_TURNSTILE_SITE_KEY

    ;(global.fetch as any).mockRestore?.()
    localStorage.clear()
  })

  const renderModal = () =>
    render(
      <FluentProvider theme={waooawLightTheme}>
        <AuthModal open onClose={vi.fn()} onSuccess={vi.fn()} theme="light" />
      </FluentProvider>
    )

  it('shows registration form and requires consent', async () => {
    renderModal()

    fireEvent.click(screen.getByRole('button', { name: 'Create account' }))

    expect(screen.getByText('Create your WAOOAW account')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('Your full name')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('Your business name')).toBeInTheDocument()

    fireEvent.change(screen.getByPlaceholderText('Your full name'), { target: { value: 'Test User' } })
    fireEvent.change(screen.getByPlaceholderText('Your business name'), { target: { value: 'ACME' } })
    fireEvent.change(screen.getByPlaceholderText('City, State, Country'), { target: { value: 'Bengaluru, India' } })
    fireEvent.change(screen.getByPlaceholderText('you@company.com'), { target: { value: 'test@example.com' } })
    fireEvent.change(screen.getByPlaceholderText('+91 98765 43210'), { target: { value: '+919876543210' } })

    const selects = screen.getAllByRole('combobox')
    fireEvent.change(selects[0], { target: { value: 'marketing' } })
    fireEvent.change(selects[1], { target: { value: 'email' } })

    expect(screen.queryByText('CAPTCHA is not configured.')).not.toBeInTheDocument()

    // Consent + CAPTCHA are required: button remains disabled until both satisfied.
    expect(screen.getByRole('button', { name: 'Create account' })).toBeDisabled()

    const consent = screen.getByRole('checkbox', { name: 'I agree to the Terms of Service and Privacy Policy' })
    fireEvent.click(consent)
    await waitFor(() => expect(consent).toBeChecked())

    // CAPTCHA token is set via the stubbed window.turnstile render callback.
    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Create account' })).not.toBeDisabled()
    })

    fireEvent.click(screen.getByRole('button', { name: 'Create account' }))

    expect(await screen.findByText('OTP code')).toBeInTheDocument()
    expect(screen.getByText(/Dev OTP: 123456/)).toBeInTheDocument()

    fireEvent.change(screen.getByPlaceholderText('Enter 6-digit OTP'), { target: { value: '123456' } })
    fireEvent.click(screen.getByRole('button', { name: 'Verify OTP' }))

    await waitFor(() => {
      expect(localStorage.getItem('cp_access_token')).toBe('ACCESS')
    })
  })

  it('cancel exits registration flow', () => {
    const onClose = vi.fn()

    render(
      <FluentProvider theme={waooawLightTheme}>
        <AuthModal open onClose={onClose} onSuccess={vi.fn()} theme="light" />
      </FluentProvider>
    )

    fireEvent.click(screen.getByRole('button', { name: 'Create account' }))
    fireEvent.click(screen.getByRole('button', { name: 'Cancel' }))

    expect(onClose).toHaveBeenCalledTimes(1)
  })
})
