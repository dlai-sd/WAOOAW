/**
 * Booking Modal - Trial signup flow
 * Collects customer information and creates trial record
 */

import { useMemo, useState } from 'react'
import {
  Dialog,
  DialogSurface,
  DialogTitle,
  DialogBody,
  DialogActions,
  DialogContent,
  Button,
  Input,
  Label,
  Field,
  Select,
  Spinner
} from '@fluentui/react-components'
import { Dismiss24Regular } from '@fluentui/react-icons'
import type { Agent } from '../types/plant.types'
import { usePaymentsConfig } from '../context/PaymentsConfigContext'
import { couponCheckout } from '../services/couponCheckout.service'
import { confirmRazorpayPayment, createRazorpayOrder, type RazorpayOrderCreateResponse } from '../services/razorpayCheckout.service'

function generateIdempotencyKey(): string {
  try {
    return crypto.randomUUID()
  } catch {
    return `${Date.now()}-${Math.random().toString(16).slice(2)}`
  }
}

async function ensureRazorpayLoaded(): Promise<void> {
  if (typeof window !== 'undefined' && (window as any).Razorpay) return

  await new Promise<void>((resolve, reject) => {
    const existing = document.querySelector('script[data-razorpay-checkout="true"]') as HTMLScriptElement | null
    if (existing) {
      existing.addEventListener('load', () => resolve())
      existing.addEventListener('error', () => reject(new Error('Failed to load Razorpay checkout')))
      return
    }

    const script = document.createElement('script')
    script.src = 'https://checkout.razorpay.com/v1/checkout.js'
    script.async = true
    script.dataset.razorpayCheckout = 'true'
    script.onload = () => resolve()
    script.onerror = () => reject(new Error('Failed to load Razorpay checkout'))
    document.body.appendChild(script)
  })

  if (!(window as any).Razorpay) {
    throw new Error('Razorpay checkout is unavailable')
  }
}

async function openRazorpayCheckout(order: RazorpayOrderCreateResponse): Promise<{ razorpay_payment_id: string; razorpay_order_id: string; razorpay_signature: string }> {
  await ensureRazorpayLoaded()

  return new Promise((resolve, reject) => {
    const RazorpayCtor = (window as any).Razorpay
    if (!RazorpayCtor) {
      reject(new Error('Razorpay checkout is unavailable'))
      return
    }

    const instance = new RazorpayCtor({
      key: order.razorpay_key_id,
      order_id: order.razorpay_order_id,
      currency: order.currency,
      name: 'WAOOAW',
      description: 'Agent subscription',
      handler: (response: any) => {
        resolve({
          razorpay_payment_id: String(response?.razorpay_payment_id || ''),
          razorpay_order_id: String(response?.razorpay_order_id || ''),
          razorpay_signature: String(response?.razorpay_signature || '')
        })
      },
      modal: {
        ondismiss: () => reject(new Error('Payment cancelled'))
      }
    })

    if (typeof instance?.on === 'function') {
      instance.on('payment.failed', (resp: any) => {
        const description = resp?.error?.description
        reject(new Error(description || 'Payment failed'))
      })
    }

    if (typeof instance?.open !== 'function') {
      reject(new Error('Razorpay checkout is unavailable'))
      return
    }

    instance.open()
  })
}

interface BookingModalProps {
  agent: Agent
  isOpen: boolean
  onClose: () => void
  onSuccess: (result: { order_id: string; subscription_id?: string | null }) => void
}

interface BookingFormData {
  fullName: string
  email: string
  company: string
  phone: string
}

export default function BookingModal({ agent, isOpen, onClose, onSuccess }: BookingModalProps) {
  const { config: paymentsConfig, isLoading: paymentsConfigLoading, error: paymentsConfigError } = usePaymentsConfig()

  const paymentsMode = paymentsConfig?.mode
  const isCouponMode = paymentsMode === 'coupon'

  const [formData, setFormData] = useState<BookingFormData>({
    fullName: '',
    email: '',
    company: '',
    phone: ''
  })
  const [couponCode, setCouponCode] = useState('WAOOAW100')
  const allowedDurations = useMemo(() => {
    return agent.allowed_durations && agent.allowed_durations.length
      ? agent.allowed_durations
      : ['monthly', 'quarterly']
  }, [agent.allowed_durations])

  const trialDays = agent.trial_days ?? 7

  const [duration, setDuration] = useState<string>(() => allowedDurations[0] || 'monthly')
  const [errors, setErrors] = useState<Partial<BookingFormData>>({})
  const [submitting, setSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState<string | null>(null)

  const [couponCheckoutIdempotencyKey, setCouponCheckoutIdempotencyKey] = useState<string | null>(null)
  const [couponCheckoutFingerprint, setCouponCheckoutFingerprint] = useState<string | null>(null)

  const [razorpayOrder, setRazorpayOrder] = useState<RazorpayOrderCreateResponse | null>(null)
  const [razorpayOrderFingerprint, setRazorpayOrderFingerprint] = useState<string | null>(null)

  const canSubmit = useMemo(() => {
    if (submitting) return false
    if (paymentsConfigLoading) return false
    if (paymentsConfigError) return false
    // If the payments config hasn't loaded yet, keep the action disabled.
    if (!paymentsMode) return false
    return true
  }, [submitting, paymentsConfigLoading, paymentsConfigError, paymentsMode])

  const handleChange = (field: keyof BookingFormData, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }))
    // Clear error for this field when user starts typing
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: undefined }))
    }
  }

  const validateForm = (): boolean => {
    const newErrors: Partial<BookingFormData> = {}

    if (!formData.fullName.trim()) {
      newErrors.fullName = 'Full name is required'
    }

    if (!formData.email.trim()) {
      newErrors.email = 'Email is required'
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = 'Invalid email format'
    }

    if (!formData.company.trim()) {
      newErrors.company = 'Company name is required'
    }

    if (formData.phone && !/^\+?[\d\s-()]+$/.test(formData.phone)) {
      newErrors.phone = 'Invalid phone format'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!validateForm()) {
      return
    }

    setSubmitting(true)
    setSubmitError(null)

    try {
      if (isCouponMode) {
        const nextFingerprint = `${agent.id}::${duration}::${couponCode.trim()}`
        let idempotencyKey = couponCheckoutIdempotencyKey
        if (!idempotencyKey || couponCheckoutFingerprint !== nextFingerprint) {
          idempotencyKey = generateIdempotencyKey()
          setCouponCheckoutIdempotencyKey(idempotencyKey)
          setCouponCheckoutFingerprint(nextFingerprint)
        }

        const checkout = await couponCheckout({
          couponCode,
          agentId: agent.id,
          duration,
          idempotencyKey
        })

        console.log('Coupon checkout completed:', checkout)
        onSuccess({ order_id: checkout.order_id, subscription_id: checkout.subscription_id })
      } else {
        const nextFingerprint = `${agent.id}::${duration}`
        let order = razorpayOrder
        if (!order || razorpayOrderFingerprint !== nextFingerprint) {
          order = await createRazorpayOrder({
            agentId: agent.id,
            duration
          })
          setRazorpayOrder(order)
          setRazorpayOrderFingerprint(nextFingerprint)
        }

        const payment = await openRazorpayCheckout(order)
        const confirmed = await confirmRazorpayPayment({
          orderId: order.order_id,
          razorpayOrderId: payment.razorpay_order_id,
          razorpayPaymentId: payment.razorpay_payment_id,
          razorpaySignature: payment.razorpay_signature
        })

        onSuccess({ order_id: confirmed.order_id, subscription_id: confirmed.subscription_id })
      }

      console.log('Trial created:', {
        agent_id: agent.id,
        agent_name: agent.name,
        ...formData
      })

      // Success is handled by the parent (navigation to setup wizard).
    } catch (err) {
      setSubmitError(err instanceof Error ? err.message : 'Failed to start trial. Please try again.')
      console.error('Failed to create trial:', err)
    } finally {
      setSubmitting(false)
    }
  }

  const handleClose = () => {
    if (!submitting) {
      // Reset form
      setFormData({ fullName: '', email: '', company: '', phone: '' })
      setErrors({})
      setSubmitError(null)
      setDuration(allowedDurations[0] || 'monthly')
      setCouponCheckoutIdempotencyKey(null)
      setCouponCheckoutFingerprint(null)
      setRazorpayOrder(null)
      setRazorpayOrderFingerprint(null)
      onClose()
    }
  }

  const durationLabel = (value: string) => {
    if (value === 'monthly') return 'Monthly'
    if (value === 'quarterly') return 'Quarterly'
    return value
  }

  return (
    <Dialog open={isOpen} onOpenChange={(_, data) => data.open || handleClose()}>
      <DialogSurface style={{ maxWidth: '500px' }}>
        <form onSubmit={handleSubmit}>
          <DialogBody>
            <DialogTitle
              action={
                <Button
                  appearance="subtle"
                  aria-label="close"
                  icon={<Dismiss24Regular />}
                  onClick={handleClose}
                  disabled={submitting}
                />
              }
            >
              Start {trialDays}-Day Free Trial
            </DialogTitle>

            <DialogContent>
              {/* Agent Info */}
              <div
                style={{
                  padding: '1rem',
                  backgroundColor: '#f5f5f5',
                  borderRadius: '0.5rem',
                  marginBottom: '1.5rem'
                }}
              >
                <div style={{ fontWeight: 600, marginBottom: '0.25rem' }}>
                  {agent.name}
                </div>
                <div style={{ fontSize: '0.9rem', color: '#666' }}>
                  {agent.industry.charAt(0).toUpperCase() + agent.industry.slice(1)} · {trialDays}-Day Trial
                </div>
              </div>

              <Field label="Duration" required>
                <Select
                  value={duration}
                  onChange={(_, data) => setDuration(String(data.value))}
                  disabled={submitting}
                >
                  {allowedDurations.map((value) => (
                    <option key={value} value={value}>
                      {durationLabel(value)}
                    </option>
                  ))}
                </Select>
              </Field>

              {/* Form Fields */}
              <Field
                label="Full Name"
                required
                validationMessage={errors.fullName}
                validationState={errors.fullName ? 'error' : undefined}
                style={{ marginTop: '1rem' }}
              >
                <Input
                  value={formData.fullName}
                  onChange={(e) => handleChange('fullName', e.target.value)}
                  placeholder="Enter your full name"
                  disabled={submitting}
                />
              </Field>

              <Field
                label="Email"
                required
                validationMessage={errors.email}
                validationState={errors.email ? 'error' : undefined}
                style={{ marginTop: '1rem' }}
              >
                <Input
                  type="email"
                  value={formData.email}
                  onChange={(e) => handleChange('email', e.target.value)}
                  placeholder="you@company.com"
                  disabled={submitting}
                />
              </Field>

              <Field
                label="Company"
                required
                validationMessage={errors.company}
                validationState={errors.company ? 'error' : undefined}
                style={{ marginTop: '1rem' }}
              >
                <Input
                  value={formData.company}
                  onChange={(e) => handleChange('company', e.target.value)}
                  placeholder="Your company name"
                  disabled={submitting}
                />
              </Field>

              <Field
                label="Phone (Optional)"
                validationMessage={errors.phone}
                validationState={errors.phone ? 'error' : undefined}
                style={{ marginTop: '1rem' }}
              >
                <Input
                  type="tel"
                  value={formData.phone}
                  onChange={(e) => handleChange('phone', e.target.value)}
                  placeholder="+91 98765 43210"
                  disabled={submitting}
                />
              </Field>

              {isCouponMode && (
                <Field
                  label="Coupon Code"
                  required
                  style={{ marginTop: '1rem' }}
                >
                  <Input
                    value={couponCode}
                    onChange={(e) => setCouponCode(e.target.value)}
                    placeholder="WAOOAW100"
                    disabled={submitting}
                  />
                </Field>
              )}

              {(paymentsConfigLoading || paymentsConfigError) && (
                <div
                  style={{
                    marginTop: '1rem',
                    padding: '0.75rem',
                    backgroundColor: paymentsConfigError ? '#fee' : '#f5f5f5',
                    borderRadius: '0.5rem',
                    color: paymentsConfigError ? '#c00' : '#666',
                    fontSize: '0.9rem'
                  }}
                >
                  {paymentsConfigLoading ? 'Loading checkout options…' : paymentsConfigError}
                </div>
              )}

              {/* Error Message */}
              {submitError && (
                <div
                  style={{
                    marginTop: '1rem',
                    padding: '0.75rem',
                    backgroundColor: '#fee',
                    borderRadius: '0.5rem',
                    color: '#c00',
                    fontSize: '0.9rem'
                  }}
                >
                  {submitError}
                  <div style={{ marginTop: '0.25rem', color: '#7f1d1d' }}>
                    You can retry safely without creating a duplicate order.
                  </div>
                </div>
              )}

              {/* Terms */}
              <div
                style={{
                  marginTop: '1.5rem',
                  padding: '1rem',
                  backgroundColor: '#f0f9ff',
                  borderRadius: '0.5rem',
                  fontSize: '0.85rem',
                  color: '#666'
                }}
              >
                <strong>Trial Terms:</strong>
                <ul style={{ margin: '0.5rem 0 0 0', paddingLeft: '1.5rem' }}>
                  <li>7-day free trial, no credit card required</li>
                  <li>Keep all deliverables even if you cancel</li>
                  <li>Cancel anytime within 7 days - pay nothing</li>
                  <li>After 7 days: ₹12,000/month (cancel anytime)</li>
                </ul>
              </div>
            </DialogContent>

            <DialogActions>
              <Button
                appearance="secondary"
                onClick={handleClose}
                disabled={submitting}
              >
                Cancel
              </Button>
              <Button
                appearance="primary"
                type="submit"
                disabled={!canSubmit}
                icon={submitting ? <Spinner size="tiny" /> : undefined}
              >
                {submitting ? 'Starting Trial...' : submitError ? 'Retry Payment' : 'Start Free Trial'}
              </Button>
            </DialogActions>
          </DialogBody>
        </form>
      </DialogSurface>
    </Dialog>
  )
}
