/**
 * Auth Modal Component
 * Modal dialog for Google Sign-In with account selection
 */

import {
  Dialog,
  DialogSurface,
  DialogTitle,
  DialogBody,
  DialogContent,
  Button,
  Checkbox,
  Field,
  Input,
  makeStyles
} from '@fluentui/react-components'
import { Dismiss24Regular } from '@fluentui/react-icons'
import GoogleLoginButton from './GoogleLoginButton'
import { useMemo, useState } from 'react'
import CaptchaWidget from './CaptchaWidget'
import authService from '../../services/auth.service'
import { createRegistration } from '../../services/registration.service'
import { startOtp, verifyOtp } from '../../services/otp.service'

const useStyles = makeStyles({
  surface: {
    maxWidth: '450px',
    padding: '32px',
    borderRadius: '16px'
  },
  surfaceDark: {
    backgroundColor: '#18181b',
    border: '1px solid rgba(0, 242, 254, 0.2)',
    boxShadow: '0 0 40px rgba(0, 242, 254, 0.15), 0 20px 60px rgba(0, 0, 0, 0.5)'
  },
  surfaceLight: {
    backgroundColor: '#ffffff',
    border: '1px solid rgba(102, 126, 234, 0.2)',
    boxShadow: '0 0 40px rgba(102, 126, 234, 0.1), 0 20px 60px rgba(0, 0, 0, 0.1)'
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '28px',
    paddingBottom: '20px'
  },
  headerDark: {
    borderBottom: '1px solid rgba(255, 255, 255, 0.1)'
  },
  headerLight: {
    borderBottom: '1px solid rgba(0, 0, 0, 0.1)'
  },
  title: {
    fontSize: '32px',
    fontWeight: '700',
    background: 'linear-gradient(135deg, #00f2fe 0%, #667eea 100%)',
    WebkitBackgroundClip: 'text',
    WebkitTextFillColor: 'transparent',
    backgroundClip: 'text',
    margin: '0',
    fontFamily: "'Space Grotesk', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
    letterSpacing: '-0.02em'
  },
  closeButton: {
    color: '#a1a1aa',
    transition: 'all 0.2s ease',
    ':hover': {
      color: '#00f2fe',
      backgroundColor: 'rgba(0, 242, 254, 0.1)',
      boxShadow: '0 0 20px rgba(0, 242, 254, 0.3)'
    }
  },
  content: {
    display: 'flex',
    flexDirection: 'column',
    gap: '28px',
    alignItems: 'center',
    padding: '20px 0'
  },
  subtitle: {
    textAlign: 'center',
    color: '#d4d4d8',
    marginBottom: '10px',
    lineHeight: '1.6'
  },
  subtitleStrong: {
    fontSize: '18px',
    fontWeight: '600'
  },
  subtitleStrongDark: {
    color: '#f5f5f5'
  },
  subtitleStrongLight: {
    color: '#18181b'
  },
  subtitleDark: {
    color: '#d4d4d8'
  },
  subtitleLight: {
    color: '#52525b'
  },
  logo: {
    fontSize: '56px',
    marginBottom: '10px',
    filter: 'drop-shadow(0 0 10px rgba(0, 242, 254, 0.3))'
  },
  divider: {
    width: '100%',
    height: '1px',
    background: 'linear-gradient(90deg, transparent 0%, rgba(0, 242, 254, 0.3) 50%, transparent 100%)',
    margin: '24px 0'
  },
  footer: {
    textAlign: 'center',
    fontSize: '11px',
    marginTop: '24px',
    lineHeight: '1.5'
  },
  footerDark: {
    color: '#71717a'
  },
  footerLight: {
    color: '#a1a1aa'
  }
})

interface AuthModalProps {
  open: boolean
  onClose: () => void
  onSuccess?: () => void
  theme?: 'light' | 'dark'
}

type AuthMode = 'signin' | 'register'

type RegistrationFormData = {
  fullName: string
  businessName: string
  businessIndustry: string
  businessAddress: string
  email: string
  phone: string
  website: string
  gstNumber: string
  preferredContactMethod: 'email' | 'phone' | ''
  consent: boolean
}

export default function AuthModal({ open, onClose, onSuccess, theme = 'light' }: AuthModalProps) {
  const isDark = theme === 'dark'
  const styles = useStyles()

  const [mode, setMode] = useState<AuthMode>('signin')
  const [formData, setFormData] = useState<RegistrationFormData>({
    fullName: '',
    businessName: '',
    businessIndustry: '',
    businessAddress: '',
    email: '',
    phone: '',
    website: '',
    gstNumber: '',
    preferredContactMethod: '',
    consent: false
  })
  const [errors, setErrors] = useState<Partial<Record<keyof RegistrationFormData, string>>>({})

  const [captchaToken, setCaptchaToken] = useState<string | null>(null)
  const [captchaError, setCaptchaError] = useState<string | null>(null)

  const [registerSubmitting, setRegisterSubmitting] = useState(false)
  const [registerError, setRegisterError] = useState<string | null>(null)

  const [otpId, setOtpId] = useState<string | null>(null)
  const [otpCode, setOtpCode] = useState('')
  const [otpHint, setOtpHint] = useState<string | null>(null)
  const [otpError, setOtpError] = useState<string | null>(null)

  const turnstileSiteKey = (
    ((import.meta as any).env?.VITE_TURNSTILE_SITE_KEY as string | undefined) ||
    (typeof process !== 'undefined' ? ((process as any).env?.VITE_TURNSTILE_SITE_KEY as string | undefined) : undefined) ||
    ''
  ).trim()

  const resetRegisterState = () => {
    setMode('signin')
    setFormData({
      fullName: '',
      businessName: '',
      businessIndustry: '',
      businessAddress: '',
      email: '',
      phone: '',
      website: '',
      gstNumber: '',
      preferredContactMethod: '',
      consent: false
    })
    setErrors({})
    setCaptchaToken(null)
    setCaptchaError(null)

    setRegisterSubmitting(false)
    setRegisterError(null)

    setOtpId(null)
    setOtpCode('')
    setOtpHint(null)
    setOtpError(null)
  }

  const handleSuccess = () => {
    onClose()
    onSuccess?.()
  }

  const closeAndReset = () => {
    resetRegisterState()
    onClose()
  }

  const handleError = (error: string) => {
    console.error('Auth error:', error)
  }

  const validateRegistration = (): boolean => {
    const nextErrors: Partial<Record<keyof RegistrationFormData, string>> = {}

    if (!formData.fullName.trim()) nextErrors.fullName = 'Full name is required'
    if (!formData.businessName.trim()) nextErrors.businessName = 'Business name is required'
    if (!formData.businessIndustry.trim()) nextErrors.businessIndustry = 'Business industry is required'
    if (!formData.businessAddress.trim()) nextErrors.businessAddress = 'Business address is required'

    if (!formData.email.trim()) {
      nextErrors.email = 'Email is required'
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      nextErrors.email = 'Invalid email format'
    }

    if (!formData.phone.trim()) {
      nextErrors.phone = 'Phone number is required'
    } else if (!/^\+?[\d\s\-()]{7,}$/.test(formData.phone)) {
      nextErrors.phone = 'Invalid phone format'
    }

    if (formData.website.trim() && !/^https?:\/\//i.test(formData.website.trim())) {
      nextErrors.website = 'Website must start with http:// or https://'
    }

    if (formData.gstNumber.trim() && !/^[0-9A-Z]{15}$/.test(formData.gstNumber.trim().toUpperCase())) {
      nextErrors.gstNumber = 'Invalid GST format (15 chars)'
    }

    if (!formData.preferredContactMethod) nextErrors.preferredContactMethod = 'Select a preferred contact method'
    if (!formData.consent) nextErrors.consent = 'Consent is required'

    if (!turnstileSiteKey) {
      setCaptchaError('CAPTCHA is not configured. Please try again later.')
    } else if (!captchaToken) {
      setCaptchaError('Complete the CAPTCHA to continue')
    } else {
      setCaptchaError(null)
    }

    setErrors(nextErrors)
    return Object.keys(nextErrors).length === 0 && Boolean(turnstileSiteKey) && Boolean(captchaToken)
  }

  const canSubmitRegister = useMemo(() => {
    // Keep simple for now: only used for disabling the button when consent is unchecked.
    return formData.consent && Boolean(turnstileSiteKey) && Boolean(captchaToken) && !registerSubmitting
  }, [formData.consent, turnstileSiteKey, captchaToken])

  const handleRegisterSubmit = async () => {
    if (!validateRegistration()) return

    setRegisterSubmitting(true)
    setRegisterError(null)
    setOtpError(null)

    try {
      const reg = await createRegistration({
        fullName: formData.fullName,
        businessName: formData.businessName,
        businessIndustry: formData.businessIndustry,
        businessAddress: formData.businessAddress,
        email: formData.email,
        phone: formData.phone,
        website: formData.website || undefined,
        gstNumber: formData.gstNumber || undefined,
        preferredContactMethod: formData.preferredContactMethod as any,
        consent: formData.consent
      })

      const otpStart = await startOtp(reg.registration_id)
      setOtpId(otpStart.otp_id)

      const hintParts = [`OTP sent via ${otpStart.channel.toUpperCase()}`, otpStart.destination_masked]
      if (otpStart.otp_code) hintParts.push(`Dev OTP: ${otpStart.otp_code}`)
      setOtpHint(hintParts.join(' • '))
    } catch (e) {
      setRegisterError(e instanceof Error ? e.message : 'Registration failed')
    } finally {
      setRegisterSubmitting(false)
    }
  }

  const handleVerifyOtp = async () => {
    if (!otpId) return
    setOtpError(null)
    setRegisterSubmitting(true)
    try {
      const tokens = await verifyOtp(otpId, otpCode)
      authService.setTokens(tokens)
      try {
        window.dispatchEvent(new Event('waooaw:auth-changed'))
      } catch {
        // ignore
      }
      closeAndReset()
      onSuccess?.()
    } catch (e) {
      setOtpError(e instanceof Error ? e.message : 'OTP verification failed')
    } finally {
      setRegisterSubmitting(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={(_, data) => !data.open && closeAndReset()}>
      <DialogSurface className={`${styles.surface} ${isDark ? styles.surfaceDark : styles.surfaceLight}`}>
        <DialogBody>
          <div className={`${styles.header} ${isDark ? styles.headerDark : styles.headerLight}`}>
            <DialogTitle className={styles.title}>
              {mode === 'signin' ? 'Sign in to WAOOAW' : 'Create your WAOOAW account'}
            </DialogTitle>
            <Button
              appearance="subtle"
              icon={<Dismiss24Regular />}
              onClick={closeAndReset}
              className={styles.closeButton}
            />
          </div>
          
          <DialogContent className={styles.content}>
            {mode === 'signin' ? (
              <>
                <div className={styles.logo}>👋</div>

                <div className={`${styles.subtitle} ${isDark ? styles.subtitleDark : styles.subtitleLight}`}>
                  <strong className={`${styles.subtitleStrong} ${isDark ? styles.subtitleStrongDark : styles.subtitleStrongLight}`}>Welcome to WAOOAW</strong>
                  <br />
                  Agents that make you say WOW!
                </div>

                <GoogleLoginButton onSuccess={handleSuccess} onError={handleError} />

                <Button appearance="subtle" onClick={() => setMode('register')}>
                  Create account
                </Button>

                <div className={`${styles.footer} ${isDark ? styles.footerDark : styles.footerLight}`}>
                  By signing in, you agree to our Terms of Service and Privacy Policy
                </div>
              </>
            ) : (
              <>
                <GoogleLoginButton
                  mode="prefill"
                  onPrefill={({ name, email }) =>
                    setFormData((p) => ({
                      ...p,
                      fullName: name ? String(name) : p.fullName,
                      email: email ? String(email) : p.email
                    }))
                  }
                  onError={(e) => setRegisterError(e)}
                />

                <div className={styles.divider} />

                <Field
                  label="Full name"
                  required
                  validationMessage={errors.fullName}
                  validationState={errors.fullName ? 'error' : undefined}
                >
                  <Input
                    value={formData.fullName}
                    placeholder="Your full name"
                    onChange={(e) => setFormData((p) => ({ ...p, fullName: e.target.value }))}
                  />
                </Field>

                <Field
                  label="Business name"
                  required
                  validationMessage={errors.businessName}
                  validationState={errors.businessName ? 'error' : undefined}
                >
                  <Input
                    value={formData.businessName}
                    placeholder="Your business name"
                    onChange={(e) => setFormData((p) => ({ ...p, businessName: e.target.value }))}
                  />
                </Field>

                <Field
                  label="Business industry"
                  required
                  validationMessage={errors.businessIndustry}
                  validationState={errors.businessIndustry ? 'error' : undefined}
                >
                  <select
                    className="filter-select"
                    value={formData.businessIndustry}
                    onChange={(e) => setFormData((p) => ({ ...p, businessIndustry: e.target.value }))}
                  >
                    <option value="">Select an industry</option>
                    <option value="marketing">Marketing</option>
                    <option value="education">Education</option>
                    <option value="sales">Sales</option>
                  </select>
                </Field>

                <Field
                  label="Business address"
                  required
                  validationMessage={errors.businessAddress}
                  validationState={errors.businessAddress ? 'error' : undefined}
                >
                  <Input
                    value={formData.businessAddress}
                    placeholder="City, State, Country"
                    onChange={(e) => setFormData((p) => ({ ...p, businessAddress: e.target.value }))}
                  />
                </Field>

                <Field
                  label="Email"
                  required
                  validationMessage={errors.email}
                  validationState={errors.email ? 'error' : undefined}
                >
                  <Input
                    type="email"
                    value={formData.email}
                    placeholder="you@company.com"
                    onChange={(e) => setFormData((p) => ({ ...p, email: e.target.value }))}
                  />
                </Field>

                <Field
                  label="Phone number"
                  required
                  validationMessage={errors.phone}
                  validationState={errors.phone ? 'error' : undefined}
                >
                  <Input
                    type="tel"
                    value={formData.phone}
                    placeholder="+91 98765 43210"
                    onChange={(e) => setFormData((p) => ({ ...p, phone: e.target.value }))}
                  />
                </Field>

                <Field
                  label="Website (optional)"
                  validationMessage={errors.website}
                  validationState={errors.website ? 'error' : undefined}
                >
                  <Input
                    value={formData.website}
                    placeholder="https://example.com"
                    onChange={(e) => setFormData((p) => ({ ...p, website: e.target.value }))}
                  />
                </Field>

                <Field
                  label="GST number (optional)"
                  validationMessage={errors.gstNumber}
                  validationState={errors.gstNumber ? 'error' : undefined}
                >
                  <Input
                    value={formData.gstNumber}
                    placeholder="15-character GSTIN"
                    onChange={(e) => setFormData((p) => ({ ...p, gstNumber: e.target.value.toUpperCase() }))}
                  />
                </Field>

                <Field
                  label="Preferred contact method"
                  required
                  validationMessage={errors.preferredContactMethod}
                  validationState={errors.preferredContactMethod ? 'error' : undefined}
                >
                  <select
                    className="filter-select"
                    value={formData.preferredContactMethod}
                    onChange={(e) => setFormData((p) => ({ ...p, preferredContactMethod: e.target.value as any }))}
                  >
                    <option value="">Select</option>
                    <option value="email">Email</option>
                    <option value="phone">Phone</option>
                  </select>
                </Field>

                <Field
                  label=""
                  validationMessage={errors.consent}
                  validationState={errors.consent ? 'error' : undefined}
                >
                  <Checkbox
                    checked={formData.consent}
                    onChange={(_, data) => setFormData((p) => ({ ...p, consent: Boolean(data.checked) }))}
                    label="I agree to the Terms of Service and Privacy Policy"
                  />
                </Field>

                <Field
                  label=""
                  validationMessage={captchaError || undefined}
                  validationState={captchaError ? 'error' : undefined}
                >
                  {turnstileSiteKey ? (
                    <CaptchaWidget
                      siteKey={turnstileSiteKey}
                      onToken={(token) => {
                        setCaptchaToken(token)
                        setCaptchaError(token ? null : 'Complete the CAPTCHA to continue')
                      }}
                    />
                  ) : (
                    <div style={{ fontSize: '0.85rem' }}>
                      CAPTCHA is not configured.
                    </div>
                  )}
                </Field>

                {registerError ? (
                  <div style={{ color: isDark ? '#fca5a5' : '#b91c1c', fontSize: '0.9rem' }}>{registerError}</div>
                ) : null}

                {otpId ? (
                  <>
                    <Field
                      label="OTP code"
                      required
                      validationMessage={otpError || otpHint || undefined}
                      validationState={otpError ? 'error' : undefined}
                    >
                      <Input value={otpCode} placeholder="Enter 6-digit OTP" onChange={(e) => setOtpCode(e.target.value)} />
                    </Field>
                    <div style={{ display: 'flex', gap: '12px', width: '100%', justifyContent: 'center' }}>
                      <Button appearance="secondary" onClick={closeAndReset} disabled={registerSubmitting}>
                        Cancel
                      </Button>
                      <Button appearance="primary" onClick={handleVerifyOtp} disabled={registerSubmitting || otpCode.trim().length === 0}>
                        Verify OTP
                      </Button>
                    </div>
                  </>
                ) : (
                  <div style={{ display: 'flex', gap: '12px', width: '100%', justifyContent: 'center' }}>
                    <Button appearance="secondary" onClick={closeAndReset} disabled={registerSubmitting}>
                      Cancel
                    </Button>
                    <Button appearance="primary" onClick={handleRegisterSubmit} disabled={!canSubmitRegister}>
                      {registerSubmitting ? 'Submitting...' : 'Create account'}
                    </Button>
                  </div>
                )}

                <Button appearance="subtle" onClick={() => setMode('signin')}>
                  Already have an account? Sign in
                </Button>
              </>
            )}
          </DialogContent>
        </DialogBody>
      </DialogSurface>
    </Dialog>
  )
}
