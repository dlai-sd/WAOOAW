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
  })

  afterEach(() => {
    delete (window as any).turnstile
    delete process.env.VITE_TURNSTILE_SITE_KEY
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
