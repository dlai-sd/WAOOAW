import {
  Button,
  Checkbox,
  Field,
  Input,
  Select,
  makeStyles,
  tokens
} from '@fluentui/react-components'
import { Dismiss24Regular } from '@fluentui/react-icons'
import { useEffect, useMemo, useState } from 'react'
import CaptchaWidget from './CaptchaWidget'
import GoogleLoginButton from './GoogleLoginButton'
import authService from '../../services/auth.service'
import { createRegistration } from '../../services/registration.service'
import { startLoginOtp, startOtp, verifyOtp } from '../../services/otp.service'

const OTP_RESEND_COOLDOWN_SECONDS = 30

const useStyles = makeStyles({
  surface: {
    width: '100%',
    maxWidth: '600px',
    padding: '32px',
    borderRadius: '16px',
    backgroundColor: tokens.colorNeutralBackground1,
    border: `1px solid ${tokens.colorNeutralStroke2}`,
    boxShadow: tokens.shadow16
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '28px',
    paddingBottom: '20px'
  },
  headerCompact: {
    marginBottom: '14px',
    paddingBottom: '10px'
  },
  headerBorder: {
    borderBottom: `1px solid ${tokens.colorNeutralStroke2}`
  },
  title: {
    fontSize: '28px',
    fontWeight: '700',
    color: tokens.colorNeutralForeground1,
    margin: '0',
    letterSpacing: '-0.02em'
  },
  closeButton: {
    color: tokens.colorNeutralForeground2
  },
  content: {
    display: 'flex',
    flexDirection: 'column',
    gap: '28px',
    alignItems: 'center',
    padding: '20px 0'
  },
  contentCompact: {
    gap: '14px',
    padding: '10px 0'
  },
  subtitle: {
    textAlign: 'center',
    color: tokens.colorNeutralForeground2,
    marginBottom: '10px',
    lineHeight: '1.6'
  },
  subtitleStrong: {
    fontSize: '18px',
    fontWeight: '600',
    color: tokens.colorNeutralForeground1
  },
  logo: {
    fontSize: '56px',
    marginBottom: '10px'
  },
  divider: {
    width: '100%',
    height: '1px',
    backgroundColor: tokens.colorNeutralStroke2,
    margin: '24px 0'
  },
  dividerCompact: {
    margin: '12px 0'
  },
  helperText: {
    width: '100%',
    marginTop: '-16px',
    fontSize: '12px',
    lineHeight: '1.4',
    color: tokens.colorNeutralForeground2
  },
  errorText: {
    width: '100%',
    fontSize: '0.9rem',
    color: tokens.colorStatusDangerForeground1
  },
  footer: {
    textAlign: 'center',
    fontSize: '11px',
    marginTop: '24px',
    lineHeight: '1.5'
  },
  footerText: {
    color: tokens.colorNeutralForeground3
  },
  fullWidth: {
    width: '100%'
  },
  twoColGrid: {
    width: '100%',
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    columnGap: '12px',
    rowGap: '12px',
    '@media (max-width: 720px)': {
      gridTemplateColumns: '1fr'
    }
  },
  spanTwo: {
    gridColumn: '1 / -1'
  }
})

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

export type AuthPanelProps = {
  theme?: 'light' | 'dark'
  initialMode?: AuthMode
  showCloseButton?: boolean
  onClose?: () => void
  onSuccess?: () => void
  onRequestSignIn?: () => void
  onRequestSignUp?: () => void
}

export default function AuthPanel({
  theme = 'light',
  initialMode = 'signin',
  showCloseButton = false,
  onClose,
  onSuccess,
  onRequestSignIn,
  onRequestSignUp
}: AuthPanelProps) {
  const styles = useStyles()

  const [mode, setMode] = useState<AuthMode>(initialMode)

  const isRegisterMode = mode === 'register'

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

  const [registrationId, setRegistrationId] = useState<string | null>(null)

  const [otpId, setOtpId] = useState<string | null>(null)
  const [otpCode, setOtpCode] = useState('')
  const [otpHint, setOtpHint] = useState<string | null>(null)
  const [otpError, setOtpError] = useState<string | null>(null)
  const [registerResendSecondsLeft, setRegisterResendSecondsLeft] = useState(0)

  const [signinEmail, setSigninEmail] = useState('')
  const [signinOtpId, setSigninOtpId] = useState<string | null>(null)
  const [signinOtpCode, setSigninOtpCode] = useState('')
  const [signinOtpHint, setSigninOtpHint] = useState<string | null>(null)
  const [signinOtpError, setSigninOtpError] = useState<string | null>(null)
  const [signinSubmitting, setSigninSubmitting] = useState(false)
  const [signinResendSecondsLeft, setSigninResendSecondsLeft] = useState(0)

  const isRegisterCooldownActive = registerResendSecondsLeft > 0
  const isSigninCooldownActive = signinResendSecondsLeft > 0

  useEffect(() => {
    if (!isRegisterCooldownActive) return
    const intervalId = window.setInterval(() => {
      setRegisterResendSecondsLeft((s) => Math.max(0, s - 1))
    }, 1000)
    return () => window.clearInterval(intervalId)
  }, [isRegisterCooldownActive])

  useEffect(() => {
    if (!isSigninCooldownActive) return
    const intervalId = window.setInterval(() => {
      setSigninResendSecondsLeft((s) => Math.max(0, s - 1))
    }, 1000)
    return () => window.clearInterval(intervalId)
  }, [isSigninCooldownActive])

  const turnstileSiteKey = (
    ((import.meta as any).env?.VITE_TURNSTILE_SITE_KEY as string | undefined) ||
    (typeof process !== 'undefined'
      ? ((process as any).env?.VITE_TURNSTILE_SITE_KEY as string | undefined)
      : undefined) ||
    ''
  ).trim()

  const resetState = () => {
    setMode(initialMode)

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

    setRegistrationId(null)

    setOtpId(null)
    setOtpCode('')
    setOtpHint(null)
    setOtpError(null)
    setRegisterResendSecondsLeft(0)

    setSigninEmail('')
    setSigninOtpId(null)
    setSigninOtpCode('')
    setSigninOtpHint(null)
    setSigninOtpError(null)
    setSigninSubmitting(false)
    setSigninResendSecondsLeft(0)
  }

  const handleSuccess = () => {
    onSuccess?.()
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
    return formData.consent && Boolean(turnstileSiteKey) && Boolean(captchaToken) && !registerSubmitting
  }, [formData.consent, turnstileSiteKey, captchaToken, registerSubmitting])

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

      setRegistrationId(reg.registration_id)

      const otpStart = await startOtp(reg.registration_id)
      setOtpId(otpStart.otp_id)
      setRegisterResendSecondsLeft(OTP_RESEND_COOLDOWN_SECONDS)

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
      resetState()
      handleSuccess()
    } catch (e) {
      setOtpError(e instanceof Error ? e.message : 'OTP verification failed')
    } finally {
      setRegisterSubmitting(false)
    }
  }

  const handleResendRegisterOtp = async () => {
    if (!registrationId) return
    if (registerResendSecondsLeft > 0) return
    setOtpError(null)
    setRegisterSubmitting(true)
    try {
      const otpStart = await startOtp(registrationId)
      setOtpId(otpStart.otp_id)
      setOtpCode('')
      setRegisterResendSecondsLeft(OTP_RESEND_COOLDOWN_SECONDS)

      const hintParts = [`OTP sent via ${otpStart.channel.toUpperCase()}`, otpStart.destination_masked]
      if (otpStart.otp_code) hintParts.push(`Dev OTP: ${otpStart.otp_code}`)
      setOtpHint(hintParts.join(' • '))
    } catch (e) {
      setOtpError(e instanceof Error ? e.message : 'Failed to resend OTP')
    } finally {
      setRegisterSubmitting(false)
    }
  }

  const handleSigninStartOtp = async () => {
    const email = signinEmail.trim().toLowerCase()
    setSigninOtpError(null)
    setSigninSubmitting(true)
    try {
      const started = await startLoginOtp({ email, channel: 'email' })
      setSigninOtpId(started.otp_id)
      setSigninResendSecondsLeft(OTP_RESEND_COOLDOWN_SECONDS)

      const hintParts = [`OTP sent via ${started.channel.toUpperCase()}`, started.destination_masked]
      if (started.otp_code) hintParts.push(`Dev OTP: ${started.otp_code}`)
      setSigninOtpHint(hintParts.join(' • '))
    } catch (e) {
      setSigninOtpError(e instanceof Error ? e.message : 'Failed to start OTP')
    } finally {
      setSigninSubmitting(false)
    }
  }

  const handleSigninResendOtp = async () => {
    const email = signinEmail.trim().toLowerCase()
    if (!email) return
    if (signinResendSecondsLeft > 0) return

    setSigninOtpError(null)
    setSigninSubmitting(true)
    try {
      const started = await startLoginOtp({ email, channel: 'email' })
      setSigninOtpId(started.otp_id)
      setSigninOtpCode('')
      setSigninResendSecondsLeft(OTP_RESEND_COOLDOWN_SECONDS)

      const hintParts = [`OTP sent via ${started.channel.toUpperCase()}`, started.destination_masked]
      if (started.otp_code) hintParts.push(`Dev OTP: ${started.otp_code}`)
      setSigninOtpHint(hintParts.join(' • '))
    } catch (e) {
      setSigninOtpError(e instanceof Error ? e.message : 'Failed to resend OTP')
    } finally {
      setSigninSubmitting(false)
    }
  }

  const handleSigninVerifyOtp = async () => {
    if (!signinOtpId) return
    setSigninOtpError(null)
    setSigninSubmitting(true)
    try {
      const tokens = await verifyOtp(signinOtpId, signinOtpCode)
      authService.setTokens(tokens)
      try {
        window.dispatchEvent(new Event('waooaw:auth-changed'))
      } catch {
        // ignore
      }
      resetState()
      handleSuccess()
    } catch (e) {
      setSigninOtpError(e instanceof Error ? e.message : 'OTP verification failed')
    } finally {
      setSigninSubmitting(false)
    }
  }

  const requestSignUp = () => {
    if (onRequestSignUp) return onRequestSignUp()
    setMode('register')
  }

  const requestSignIn = () => {
    if (onRequestSignIn) return onRequestSignIn()
    setMode('signin')
  }

  const handleCancel = () => {
    if (onClose) return onClose()
    requestSignIn()
  }

  return (
    <div className={styles.surface}>
      <div className={`${styles.header} ${styles.headerBorder} ${isRegisterMode ? styles.headerCompact : ''}`}>
        <h1 className={styles.title}>{mode === 'signin' ? 'Sign in to WAOOAW' : 'Create your WAOOAW account'}</h1>
        {showCloseButton ? (
          <Button appearance="subtle" icon={<Dismiss24Regular />} onClick={onClose} className={styles.closeButton} />
        ) : null}
      </div>

      <div className={`${styles.content} ${isRegisterMode ? styles.contentCompact : ''}`}>
        {mode === 'signin' ? (
          <>
            <div className={styles.logo}>👋</div>

            <div className={styles.subtitle}>
              <strong className={styles.subtitleStrong}>Welcome to WAOOAW</strong>
              <br />
              Agents that make you say WOW!
            </div>

            <GoogleLoginButton onSuccess={handleSuccess} onError={handleError} />

            <div className={`${styles.divider} ${isRegisterMode ? styles.dividerCompact : ''}`} />

            <Field
              label="Email"
              required
              validationMessage={signinOtpError || signinOtpHint || undefined}
              validationState={signinOtpError ? 'error' : undefined}
              className={styles.fullWidth}
            >
              <Input
                className={styles.fullWidth}
                type="email"
                value={signinEmail}
                placeholder="you@company.com"
                onChange={(e) => setSigninEmail(e.target.value)}
              />
            </Field>

            <div className={styles.helperText}>
              Email OTP is passwordless sign-in. We send a one-time code so you don’t need to create or remember a password.
            </div>

            {signinOtpId ? (
              <>
                <Field label="OTP code" required className={styles.fullWidth}>
                  <Input
                    className={styles.fullWidth}
                    value={signinOtpCode}
                    placeholder="Enter 6-digit OTP"
                    onChange={(e) => setSigninOtpCode(e.target.value)}
                  />
                </Field>
                <Button
                  appearance="primary"
                  onClick={handleSigninVerifyOtp}
                  disabled={signinSubmitting || signinOtpCode.trim().length === 0}
                  className={styles.fullWidth}
                >
                  Verify OTP
                </Button>
                <Button
                  appearance="subtle"
                  onClick={handleSigninResendOtp}
                  disabled={signinSubmitting || signinResendSecondsLeft > 0}
                  className={styles.fullWidth}
                >
                  {signinResendSecondsLeft > 0 ? `Resend OTP (${signinResendSecondsLeft}s)` : 'Resend OTP'}
                </Button>
              </>
            ) : (
              <Button
                appearance="secondary"
                onClick={handleSigninStartOtp}
                disabled={signinSubmitting || signinEmail.trim().length === 0}
                className={styles.fullWidth}
              >
                Send OTP
              </Button>
            )}

            <div style={{ width: '100%' }}>
              <Button appearance="outline" onClick={requestSignUp} className={styles.fullWidth}>
                Create account
              </Button>
            </div>

            <div className={`${styles.footer} ${styles.footerText}`}>
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

            <div className={`${styles.divider} ${isRegisterMode ? styles.dividerCompact : ''}`} />

            <div className={styles.twoColGrid}>
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
                label="Business industry"
                required
                validationMessage={errors.businessIndustry}
                validationState={errors.businessIndustry ? 'error' : undefined}
              >
                <Select
                  value={formData.businessIndustry}
                  onChange={(_, data) => setFormData((p) => ({ ...p, businessIndustry: String(data.value || '') }))}
                >
                  <option value="">Select an industry</option>
                  <option value="marketing">Marketing</option>
                  <option value="education">Education</option>
                  <option value="sales">Sales</option>
                </Select>
              </Field>

              <Field
                label="Preferred contact method"
                required
                validationMessage={errors.preferredContactMethod}
                validationState={errors.preferredContactMethod ? 'error' : undefined}
              >
                <Select
                  value={formData.preferredContactMethod}
                  onChange={(_, data) =>
                    setFormData((p) => ({
                      ...p,
                      preferredContactMethod: (data.value as any) || ''
                    }))
                  }
                >
                  <option value="">Select</option>
                  <option value="email">Email</option>
                  <option value="phone">Phone</option>
                </Select>
              </Field>

              <Field
                label="Business address"
                required
                validationMessage={errors.businessAddress}
                validationState={errors.businessAddress ? 'error' : undefined}
                className={styles.spanTwo}
              >
                <Input
                  value={formData.businessAddress}
                  placeholder="City, State, Country"
                  onChange={(e) => setFormData((p) => ({ ...p, businessAddress: e.target.value }))}
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
            </div>

            <Field
              label=""
              validationMessage={errors.consent}
              validationState={errors.consent ? 'error' : undefined}
              className={styles.fullWidth}
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
              className={styles.fullWidth}
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
                <div style={{ fontSize: '0.85rem' }}>CAPTCHA is not configured.</div>
              )}
            </Field>

            {registerError ? (
              <div className={styles.errorText}>{registerError}</div>
            ) : null}

            {otpId ? (
              <>
                <Field
                  label="OTP code"
                  required
                  validationMessage={otpError || otpHint || undefined}
                  validationState={otpError ? 'error' : undefined}
                  className={styles.fullWidth}
                >
                  <Input
                    className={styles.fullWidth}
                    value={otpCode}
                    placeholder="Enter 6-digit OTP"
                    onChange={(e) => setOtpCode(e.target.value)}
                  />
                </Field>

                <div style={{ display: 'flex', gap: '12px', width: '100%', justifyContent: 'center' }}>
                  <Button appearance="secondary" onClick={handleCancel} disabled={registerSubmitting}>
                    Cancel
                  </Button>
                  <Button
                    appearance="primary"
                    onClick={handleVerifyOtp}
                    disabled={registerSubmitting || otpCode.trim().length === 0}
                  >
                    Verify OTP
                  </Button>
                </div>

                <Button
                  appearance="subtle"
                  onClick={handleResendRegisterOtp}
                  disabled={registerSubmitting || !registrationId || registerResendSecondsLeft > 0}
                  className={styles.fullWidth}
                >
                  {registerResendSecondsLeft > 0 ? `Resend OTP (${registerResendSecondsLeft}s)` : 'Resend OTP'}
                </Button>
              </>
            ) : (
              <div style={{ display: 'flex', gap: '12px', width: '100%', justifyContent: 'center' }}>
                <Button appearance="secondary" onClick={handleCancel} disabled={registerSubmitting}>
                  Cancel
                </Button>
                <Button appearance="primary" onClick={handleRegisterSubmit} disabled={!canSubmitRegister}>
                  {registerSubmitting ? 'Submitting...' : 'Create account'}
                </Button>
              </div>
            )}

            <Button appearance="subtle" onClick={requestSignIn} className={styles.fullWidth}>
              Already have an account? Sign in
            </Button>
          </>
        )}
      </div>
    </div>
  )
}
