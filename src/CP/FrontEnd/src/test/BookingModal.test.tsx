import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { FluentProvider } from '@fluentui/react-components'

import { waooawLightTheme } from '../theme'
import BookingModal from '../components/BookingModal'

vi.mock('../services/couponCheckout.service', () => ({
  couponCheckout: vi.fn().mockResolvedValue({ order_id: 'ORDER-1', subscription_id: 'SUB-1' })
}))

vi.mock('../services/razorpayCheckout.service', () => ({
  createRazorpayOrder: vi.fn().mockResolvedValue({
    order_id: 'ORDER-rzp-1',
    subscription_id: 'SUB-rzp-1',
    payment_provider: 'razorpay',
    currency: 'INR',
    amount: 12000,
    razorpay_key_id: 'rzp_test_key',
    razorpay_order_id: 'order_rzp_1'
  }),
  confirmRazorpayPayment: vi.fn().mockResolvedValue({
    order_id: 'ORDER-rzp-1',
    subscription_id: 'SUB-rzp-1',
    payment_provider: 'razorpay',
    subscription_status: 'active'
  })
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
  beforeEach(() => {
    vi.clearAllMocks()
    mockUsePaymentsConfig.mockReset()

    ;(window as any).Razorpay = undefined
  })

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

    fireEvent.change(screen.getByRole('combobox', { name: 'Duration' }), { target: { value: 'quarterly' } })

    fireEvent.change(screen.getByPlaceholderText('Enter your full name'), { target: { value: 'A User' } })
    fireEvent.change(screen.getByPlaceholderText('you@company.com'), { target: { value: 'a@b.com' } })
    fireEvent.change(screen.getByPlaceholderText('Your company name'), { target: { value: 'ACME' } })

    fireEvent.click(screen.getByRole('button', { name: 'Start Free Trial' }))

    await waitFor(() => {
      expect(couponCheckout).toHaveBeenCalledTimes(1)
    })

    expect(couponCheckout).toHaveBeenCalledWith(
      expect.objectContaining({ agentId: 'agent-123', duration: 'quarterly' })
    )

    await waitFor(() => {
      expect(onSuccess).toHaveBeenCalledTimes(1)
    })

    expect(onSuccess).toHaveBeenCalledWith({ order_id: 'ORDER-1', subscription_id: 'SUB-1' })
  })

  it('shows error and allows safe retry (HIRE-2.8)', async () => {
    const onSuccess = vi.fn()

    mockUsePaymentsConfig.mockReturnValue({
      config: { mode: 'coupon', coupon_code: 'WAOOAW100', coupon_unlimited: true },
      isLoading: false,
      error: null,
      refresh: vi.fn()
    })

    const { couponCheckout } = await import('../services/couponCheckout.service')

    ;(couponCheckout as any)
      .mockRejectedValueOnce(new Error('Payment failed'))
      .mockResolvedValueOnce({ order_id: 'ORDER-2', subscription_id: 'SUB-2' })

    renderWithProvider(<BookingModal agent={agent} isOpen onClose={vi.fn()} onSuccess={onSuccess} />)

    fireEvent.change(screen.getByPlaceholderText('Enter your full name'), { target: { value: 'A User' } })
    fireEvent.change(screen.getByPlaceholderText('you@company.com'), { target: { value: 'a@b.com' } })
    fireEvent.change(screen.getByPlaceholderText('Your company name'), { target: { value: 'ACME' } })

    fireEvent.click(screen.getByRole('button', { name: 'Start Free Trial' }))

    await waitFor(() => {
      expect(couponCheckout).toHaveBeenCalledTimes(1)
    })

    expect(await screen.findByText('Payment failed')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Retry Payment' })).toBeInTheDocument()

    const firstCallArg = (couponCheckout as any).mock.calls[0]?.[0]
    expect(firstCallArg?.idempotencyKey).toBeTruthy()

    fireEvent.click(screen.getByRole('button', { name: 'Retry Payment' }))

    await waitFor(() => {
      expect(couponCheckout).toHaveBeenCalledTimes(2)
    })

    const secondCallArg = (couponCheckout as any).mock.calls[1]?.[0]
    expect(secondCallArg?.idempotencyKey).toBe(firstCallArg?.idempotencyKey)

    await waitFor(() => {
      expect(onSuccess).toHaveBeenCalledWith({ order_id: 'ORDER-2', subscription_id: 'SUB-2' })
    })
  })

  it('submits Razorpay checkout in razorpay mode', async () => {
    const onSuccess = vi.fn()

    mockUsePaymentsConfig.mockReturnValue({
      config: { mode: 'razorpay' },
      isLoading: false,
      error: null,
      refresh: vi.fn()
    })

    const { createRazorpayOrder, confirmRazorpayPayment } = await import('../services/razorpayCheckout.service')

    class FakeRazorpay {
      options: any

      constructor(options: any) {
        this.options = options
      }

      on() {
        // no-op
      }

      open() {
        this.options.handler({
          razorpay_payment_id: 'pay_1',
          razorpay_order_id: 'order_rzp_1',
          razorpay_signature: 'sig_1'
        })
      }
    }

    ;(window as any).Razorpay = FakeRazorpay

    renderWithProvider(<BookingModal agent={agent} isOpen onClose={vi.fn()} onSuccess={onSuccess} />)

    fireEvent.change(screen.getByPlaceholderText('Enter your full name'), { target: { value: 'A User' } })
    fireEvent.change(screen.getByPlaceholderText('you@company.com'), { target: { value: 'a@b.com' } })
    fireEvent.change(screen.getByPlaceholderText('Your company name'), { target: { value: 'ACME' } })

    fireEvent.click(screen.getByRole('button', { name: 'Start Free Trial' }))

    await waitFor(() => {
      expect(createRazorpayOrder).toHaveBeenCalledTimes(1)
    })

    await waitFor(() => {
      expect(confirmRazorpayPayment).toHaveBeenCalledTimes(1)
    })

    await waitFor(() => {
      expect(onSuccess).toHaveBeenCalledWith({ order_id: 'ORDER-rzp-1', subscription_id: 'SUB-rzp-1' })
    })
  })
})
