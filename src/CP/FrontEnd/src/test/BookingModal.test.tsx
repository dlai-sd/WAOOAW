import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { FluentProvider } from '@fluentui/react-components'

import { waooawLightTheme } from '../theme'
import BookingModal from '../components/BookingModal'

vi.mock('../services/couponCheckout.service', () => ({
  couponCheckout: vi.fn().mockResolvedValue({ order_id: 'ORDER-1' })
}))

const mockUsePaymentsConfig = vi.fn()
vi.mock('../context/PaymentsConfigContext', () => ({
  usePaymentsConfig: () => mockUsePaymentsConfig()
}))

const renderWithProvider = (component: React.ReactElement) => {
  return render(<FluentProvider theme={waooawLightTheme}>{component}</FluentProvider>)
}

const agent = {
  id: 'agent-123',
  name: 'Test Agent',
  industry: 'marketing'
} as any

describe('BookingModal', () => {
  it('shows coupon field only in coupon mode', () => {
    mockUsePaymentsConfig.mockReturnValue({
      config: { mode: 'coupon', coupon_code: 'WAOOAW100', coupon_unlimited: true },
      isLoading: false,
      error: null,
      refresh: vi.fn()
    })

    renderWithProvider(<BookingModal agent={agent} isOpen onClose={vi.fn()} onSuccess={vi.fn()} />)

    expect(screen.getByPlaceholderText('WAOOAW100')).toBeInTheDocument()
  })

  it('hides coupon field in razorpay mode', () => {
    mockUsePaymentsConfig.mockReturnValue({
      config: { mode: 'razorpay' },
      isLoading: false,
      error: null,
      refresh: vi.fn()
    })

    renderWithProvider(<BookingModal agent={agent} isOpen onClose={vi.fn()} onSuccess={vi.fn()} />)

    expect(screen.queryByPlaceholderText('WAOOAW100')).toBeNull()
  })

  it('submits coupon checkout in coupon mode', async () => {
    const onSuccess = vi.fn()

    mockUsePaymentsConfig.mockReturnValue({
      config: { mode: 'coupon', coupon_code: 'WAOOAW100', coupon_unlimited: true },
      isLoading: false,
      error: null,
      refresh: vi.fn()
    })

    const { couponCheckout } = await import('../services/couponCheckout.service')

    renderWithProvider(<BookingModal agent={agent} isOpen onClose={vi.fn()} onSuccess={onSuccess} />)

    fireEvent.change(screen.getByPlaceholderText('Enter your full name'), { target: { value: 'A User' } })
    fireEvent.change(screen.getByPlaceholderText('you@company.com'), { target: { value: 'a@b.com' } })
    fireEvent.change(screen.getByPlaceholderText('Your company name'), { target: { value: 'ACME' } })

    fireEvent.click(screen.getByRole('button', { name: 'Start Free Trial' }))

    await waitFor(() => {
      expect(couponCheckout).toHaveBeenCalledTimes(1)
    })

    await waitFor(() => {
      expect(onSuccess).toHaveBeenCalledTimes(1)
    })
  })
})
