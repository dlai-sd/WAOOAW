import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { FluentProvider } from '@fluentui/react-components'

import { waooawLightTheme } from '../theme'
import AuthModal from '../components/auth/AuthModal'

vi.mock('../components/auth/GoogleLoginButton', () => ({
  default: () => <button>Mock Google Login</button>
}))

describe('AuthModal registration (REG-1.1)', () => {
  const renderModal = () =>
    render(
      <FluentProvider theme={waooawLightTheme}>
        <AuthModal open onClose={vi.fn()} onSuccess={vi.fn()} theme="light" />
      </FluentProvider>
    )

  it('shows registration form and requires consent', () => {
    renderModal()

    fireEvent.click(screen.getByRole('button', { name: 'Create account' }))

    expect(screen.getByText('Create your WAOOAW account')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('Your full name')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('Your business name')).toBeInTheDocument()

    // Consent is required: button remains disabled until checked.
    expect(screen.getByRole('button', { name: 'Create account' })).toBeDisabled()

    fireEvent.click(screen.getByText('I agree to the Terms of Service and Privacy Policy'))
    expect(screen.getByRole('button', { name: 'Create account' })).not.toBeDisabled()
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
