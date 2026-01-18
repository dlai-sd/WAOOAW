/**
 * Booking Modal - Trial signup flow
 * Collects customer information and creates trial record
 */

import { useState } from 'react'
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
  Spinner
} from '@fluentui/react-components'
import { Dismiss24Regular } from '@fluentui/react-icons'
import type { Agent } from '../types/plant.types'

interface BookingModalProps {
  agent: Agent
  isOpen: boolean
  onClose: () => void
  onSuccess: () => void
}

interface BookingFormData {
  fullName: string
  email: string
  company: string
  phone: string
}

export default function BookingModal({ agent, isOpen, onClose, onSuccess }: BookingModalProps) {
  const [formData, setFormData] = useState<BookingFormData>({
    fullName: '',
    email: '',
    company: '',
    phone: ''
  })
  const [errors, setErrors] = useState<Partial<BookingFormData>>({})
  const [submitting, setSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState<string | null>(null)

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
      // TODO: Call backend API to create trial
      // const response = await fetch('/api/v1/trials', {
      //   method: 'POST',
      //   headers: { 'Content-Type': 'application/json' },
      //   body: JSON.stringify({
      //     agent_id: agent.id,
      //     customer_name: formData.fullName,
      //     customer_email: formData.email,
      //     company: formData.company,
      //     phone: formData.phone
      //   })
      // })
      // if (!response.ok) throw new Error('Failed to create trial')

      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1500))

      console.log('Trial created:', {
        agent_id: agent.id,
        agent_name: agent.name,
        ...formData
      })

      // Success - show confirmation
      onSuccess()
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
      onClose()
    }
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
              Start 7-Day Free Trial
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
                  {agent.industry.charAt(0).toUpperCase() + agent.industry.slice(1)} · 7-Day Trial
                </div>
              </div>

              {/* Form Fields */}
              <Field
                label="Full Name"
                required
                validationMessage={errors.fullName}
                validationState={errors.fullName ? 'error' : undefined}
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
                disabled={submitting}
                icon={submitting ? <Spinner size="tiny" /> : undefined}
              >
                {submitting ? 'Starting Trial...' : 'Start Free Trial'}
              </Button>
            </DialogActions>
          </DialogBody>
        </form>
      </DialogSurface>
    </Dialog>
  )
}
