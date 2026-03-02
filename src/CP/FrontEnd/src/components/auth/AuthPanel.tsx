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
import { useCallback, useEffect, useMemo, useState } from 'react'
import CaptchaWidget from './CaptchaWidget'
import GoogleLoginButton from './GoogleLoginButton'
import authService from '../../services/auth.service'
import { createRegistration } from '../../services/registration.service'
import { startLoginOtp, startRegistrationOtp, verifyOtp } from '../../services/otp.service'

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
  },
  // ── Wizard styles ──────────────────────────────────────────────────────────
  stepDots: {
    display: 'flex',
    gap: '8px',
    justifyContent: 'center',
    marginBottom: '24px'
  },
  stepDot: {
    width: '8px',
    height: '8px',
    borderRadius: '50%',
    backgroundColor: tokens.colorNeutralStroke1,
    transition: 'all 0.25s ease'
  },
  stepDotActive: {
    width: '24px',
    borderRadius: '4px',
    backgroundColor: tokens.colorBrandBackground
  },
  stepDotDone: {
    backgroundColor: tokens.colorBrandBackground2
  },
  stepHeading: {
    fontSize: '20px',
    fontWeight: '700',
    color: tokens.colorNeutralForeground1,
    margin: '0 0 4px 0'
  },
  stepSubHeading: {
    fontSize: '13px',
    color: tokens.colorNeutralForeground3,
    marginBottom: '20px'
  },
  contactToggle: {
    display: 'flex',
    gap: '10px',
    width: '100%'
  },
  contactBtn: {
    flex: '1',
    padding: '10px',
    borderRadius: '8px',
    border: `2px solid ${tokens.colorNeutralStroke1}`,
    backgroundColor: tokens.colorNeutralBackground1,
    cursor: 'pointer',
    fontSize: '13px',
    fontWeight: '600',
    color: tokens.colorNeutralForeground1,
    transition: 'all 0.2s ease'
  },
  contactBtnActive: {
    border: `2px solid ${tokens.colorBrandBackground}`,
    backgroundColor: tokens.colorBrandBackground2,
    color: tokens.colorBrandForeground1
  },
  navRow: {
    display: 'flex',
    gap: '10px',
    width: '100%',
    marginTop: '4px'
  },
  // When embedded inside auth-unified-card — no card chrome, no title
  embeddedSurface: {
    width: '100%',
    display: 'flex',
    flexDirection: 'column',
  }
})

type AuthMode = 'signin' | 'register'

type RegistrationFormData = {
  fullName: string
  businessName: string
  businessIndustry: string
  businessAddress: string
  email: string
  phoneCountry: string
  phoneNationalNumber: string
  website: string
  gstNumber: string
  preferredContactMethod: 'email' | 'phone' | ''
  consent: boolean
}

const INDUSTRY_OPTIONS: Array<{ value: string; label: string }> = [
  { value: 'marketing',   label: 'Marketing' },
  { value: 'education',   label: 'Education' },
  { value: 'sales',       label: 'Sales' },
  { value: 'technology',  label: 'Technology' },
  { value: 'healthcare',  label: 'Healthcare' },
  { value: 'finance',     label: 'Finance' },
  { value: 'retail',      label: 'Retail' },
  { value: 'real_estate', label: 'Real Estate' },
  { value: 'other',       label: 'Other' },
]

const PHONE_COUNTRY_OPTIONS: Array<{ code: string; label: string }> = [
  { code: 'IN', label: 'India (+91)' },
  { code: 'US', label: 'United States (+1)' },
  { code: 'GB', label: 'United Kingdom (+44)' },
  { code: 'AE', label: 'United Arab Emirates (+971)' },
  { code: 'SG', label: 'Singapore (+65)' },
  { code: 'AU', label: 'Australia (+61)' },
  { code: 'CA', label: 'Canada (+1)' }
]

export type AuthPanelProps = {
  theme?: 'light' | 'dark'
  initialMode?: AuthMode
  showCloseButton?: boolean
  embedded?: boolean          // renders without card chrome or title (for auth-unified-card)
  onClose?: () => void
  onSuccess?: () => void
  onRequestSignIn?: () => void
  onRequestSignUp?: () => void
  onStepChange?: (step: 1 | 2 | 3) => void
}

export default function AuthPanel({
  theme = 'light',
  initialMode = 'signin',
  showCloseButton = false,
  embedded = false,
  onClose,
  onSuccess,
  onRequestSignIn,
  onRequestSignUp,
  onStepChange
}: AuthPanelProps) {
  const styles = useStyles()

  const [mode, setMode] = useState<AuthMode>(initialMode)
  const [regStep, setRegStep] = useState<1 | 2 | 3>(1)

  // Notify parent whenever the visible wizard step changes
  useEffect(() => {
    if (mode === 'register') onStepChange?.(regStep)
  }, [regStep, mode, onStepChange])

  const isRegisterMode = mode === 'register'

  const [formData, setFormData] = useState<RegistrationFormData>({
    fullName: '',
    businessName: '',
    businessIndustry: '',
    businessAddress: '',
    email: '',
    phoneCountry: 'IN',
    phoneNationalNumber: '',
    website: '',
    gstNumber: '',
    preferredContactMethod: '',
    consent: false
  })
  const [errors, setErrors] = useState<Partial<Record<keyof RegistrationFormData, string>>>({})

  const [captchaToken, setCaptchaToken] = useState<string | null>(null)
  const [captchaError, setCaptchaError] = useState<string | null>(null)
  const [captchaResetKey, setCaptchaResetKey] = useState(0)

  const [registerSubmitting, setRegisterSubmitting] = useState(false)
  const [registerError, setRegisterError] = useState<string | null>(null)

  const [registrationId, setRegistrationId] = useState<string | null>(null)

  // Step-1 OTP sub-state: 'email' → 'otp-pending' (code sent) → 'verified' (code accepted client-side)
  const [step1State, setStep1State] = useState<'email' | 'otp-pending' | 'verified'>('email')

  // OTP-first: set when /register/otp/start returns 409 (email already registered)
  const [duplicateEmailDetected, setDuplicateEmailDetected] = useState(false)

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
    ((window as any).__WAOOAW_RUNTIME_CONFIG__?.turnstileSiteKey as string | undefined) ||
    ((import.meta as any).env?.VITE_TURNSTILE_SITE_KEY as string | undefined) ||
    (typeof process !== 'undefined'
      ? ((process as any).env?.VITE_TURNSTILE_SITE_KEY as string | undefined)
      : undefined) ||
    ''
  ).trim()

  const isProduction = (() => {
    const runtimeEnv = String((window as any).__WAOOAW_RUNTIME_CONFIG__?.environment || '').trim().toLowerCase()
    if (runtimeEnv) {
      return ['prod', 'production', 'uat', 'demo'].includes(runtimeEnv)
    }

    const viteEnv = (import.meta as any).env as any | undefined
    const mode = String(
      viteEnv?.MODE ||
        viteEnv?.NODE_ENV ||
        (typeof process !== 'undefined' ? (process as any).env?.NODE_ENV : '') ||
        ''
    ).toLowerCase()
    return mode === 'production'
  })()

  const captchaConfigured = Boolean(turnstileSiteKey)
  // CAPTCHA should only be required when it is configured. If no site key is set,
  // do not block signup (especially in early environments where Turnstile may not be wired).
  const captchaSatisfied = captchaConfigured ? Boolean(captchaToken) : !isProduction

  const resetState = () => {
    setMode(initialMode)

    setFormData({
      fullName: '',
      businessName: '',
      businessIndustry: '',
      businessAddress: '',
      email: '',
      phoneCountry: 'IN',
      phoneNationalNumber: '',
      website: '',
      gstNumber: '',
      preferredContactMethod: '',
      consent: false
    })
    setErrors({})

    resetCaptcha()
    setCaptchaError(null)

    setRegisterSubmitting(false)
    setRegisterError(null)

    setRegistrationId(null)

    setStep1State('email')
    setDuplicateEmailDetected(false)

    setOtpId(null)
    setOtpCode('')
    setOtpHint(null)
    setOtpError(null)
    setRegisterResendSecondsLeft(0)
    setRegStep(1)

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

  const validateStep1 = (): boolean => {
    const nextErrors: Partial<Record<keyof RegistrationFormData, string>> = {}
    if (!formData.email.trim()) {
      nextErrors.email = 'Email is required'
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      nextErrors.email = 'Invalid email format'
    }
    setErrors(nextErrors)
    return Object.keys(nextErrors).length === 0
  }

  const validateStep2 = (): boolean => {
    const nextErrors: Partial<Record<keyof RegistrationFormData, string>> = {}
    if (!formData.fullName.trim()) nextErrors.fullName = 'Full name is required'
    if (!formData.businessName.trim()) nextErrors.businessName = 'Business name is required'
    if (!formData.businessIndustry.trim()) nextErrors.businessIndustry = 'Select an industry'
    setErrors(nextErrors)
    return Object.keys(nextErrors).length === 0
  }

  const validateStep3 = (): boolean => {
    const nextErrors: Partial<Record<keyof RegistrationFormData, string>> = {}
    if (!formData.phoneCountry) nextErrors.phoneCountry = 'Select a country'
    const national = String(formData.phoneNationalNumber || '').trim()
    if (!national) {
      nextErrors.phoneNationalNumber = 'Mobile number is required'
    } else {
      const digits = national.replace(/[^\d]/g, '')
      if (digits !== national) {
        nextErrors.phoneNationalNumber = 'Use digits only'
      } else if (formData.phoneCountry === 'IN' && !/^[6-9]\d{9}$/.test(digits)) {
        nextErrors.phoneNationalNumber = 'Enter a valid Indian mobile number'
      } else if (digits.length < 4 || digits.length > 15) {
        nextErrors.phoneNationalNumber = 'Enter a valid mobile number'
      }
    }
    if (!formData.preferredContactMethod) nextErrors.preferredContactMethod = 'Select a preferred contact method'
    if (!formData.consent) nextErrors.consent = 'You must agree to continue'
    setErrors(nextErrors)
    return Object.keys(nextErrors).length === 0
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

    if (!formData.phoneCountry) {
      nextErrors.phoneCountry = 'Select a country'
    }

    const national = String(formData.phoneNationalNumber || '').trim()
    if (!national) {
      nextErrors.phoneNationalNumber = 'Mobile number is required'
    } else {
      const digits = national.replace(/[^\d]/g, '')
      if (digits !== national) {
        nextErrors.phoneNationalNumber = 'Use digits only'
      } else if (formData.phoneCountry === 'IN' && !/^[6-9]\d{9}$/.test(digits)) {
        nextErrors.phoneNationalNumber = 'Enter a valid Indian mobile number'
      } else if (digits.length < 4 || digits.length > 15) {
        nextErrors.phoneNationalNumber = 'Enter a valid mobile number'
      }
    }

    if (formData.website.trim() && !/^https?:\/\//i.test(formData.website.trim())) {
      nextErrors.website = 'Website must start with http:// or https://'
    }

    if (
      formData.gstNumber.trim() &&
      !/^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][1-9A-Z]Z[0-9A-Z]$/.test(formData.gstNumber.trim().toUpperCase())
    ) {
      nextErrors.gstNumber = 'Invalid GST format (GSTIN)'
    }

    if (!formData.preferredContactMethod) nextErrors.preferredContactMethod = 'Select a preferred contact method'
    if (!formData.consent) nextErrors.consent = 'Consent is required'

    if (captchaConfigured) {
      if (!captchaToken) {
        setCaptchaError('Complete the CAPTCHA to continue')
      } else {
        setCaptchaError(null)
      }
    } else {
      // Missing config should be visible via the UI copy below.
      setCaptchaError(null)
    }

    setErrors(nextErrors)
    return Object.keys(nextErrors).length === 0 && captchaSatisfied
  }

  const canSubmitRegister = useMemo(() => {
    return formData.consent && !registerSubmitting
  }, [formData.consent, registerSubmitting])

  const handleCaptchaToken = useCallback((token: string | null) => {
    setCaptchaToken(token)
    setCaptchaError(token ? null : 'Complete the CAPTCHA to continue')
  }, [])

  const handleCaptchaError = useCallback((message: string) => {
    setCaptchaToken(null)
    setCaptchaResetKey(k => k + 1)
    setCaptchaError(message)
  }, [])

  /** Clears the token AND visually resets the Turnstile widget. */
  const resetCaptcha = useCallback(() => {
    setCaptchaToken(null)
    setCaptchaResetKey(k => k + 1)
  }, [])

  // ── Step 1: fire OTP once email + CAPTCHA are ready ─────────────────────
  const handleStep1Continue = async () => {
    if (!validateStep1()) return
    if (captchaConfigured && !captchaToken) {
      setCaptchaError('Complete the CAPTCHA to continue')
      return
    }
    setRegisterSubmitting(true)
    setRegisterError(null)
    setOtpError(null)
    setDuplicateEmailDetected(false)
    try {
      const otpStart = await startRegistrationOtp(formData.email, captchaToken)
      setOtpId(otpStart.otp_id)
      setOtpCode('')
      setRegisterResendSecondsLeft(OTP_RESEND_COOLDOWN_SECONDS)
      setOtpHint(`A verification code has been sent to ${formData.email}. Please check your inbox and spam/junk folder.`)
      setStep1State('otp-pending')
    } catch (e: any) {
      resetCaptcha()
      if (e?.isDuplicateEmail) {
        setDuplicateEmailDetected(true)
      } else {
        setRegisterError(e instanceof Error ? e.message : 'Failed to send OTP')
      }
    } finally {
      setRegisterSubmitting(false)
    }
  }

  // ── Step 1: client-side OTP accept, real verify happens at Step 3 ────────
  const handleStep1VerifyOtp = () => {
    const code = otpCode.trim()
    if (!code) {
      setOtpError('Enter the OTP sent to your email')
      return
    }
    if (!/^\d{4,8}$/.test(code)) {
      setOtpError('OTP must be 4–8 digits')
      return
    }
    setOtpError(null)
    setStep1State('verified')
    setRegStep(2)
  }

  // ── Step 1: user wants to change email — reset everything ────────────────
  const handleChangeEmail = () => {
    setStep1State('email')
    setOtpId(null)
    setOtpCode('')
    setOtpError(null)
    setOtpHint(null)
    setDuplicateEmailDetected(false)
    setRegisterError(null)
    setErrors({})
    resetCaptcha()
    setCaptchaError(null)
  }

  // ── Step 3: create registration using the OTP already captured on Step 1 ─
  const handleRegisterSubmit = async () => {
    if (!validateStep3()) return
    if (!otpId || !otpCode.trim()) {
      // OTP session missing — rare (page reload mid-wizard). Send user back.
      setRegisterError('Email verification was lost. Please re-verify your email.')
      setStep1State('email')
      setRegStep(1)
      return
    }
    setRegisterSubmitting(true)
    setRegisterError(null)
    try {
      const reg = await createRegistration({
        fullName: formData.fullName,
        businessName: formData.businessName,
        businessIndustry: formData.businessIndustry,
        businessAddress: formData.businessAddress,
        email: formData.email,
        phoneCountry: formData.phoneCountry,
        phoneNationalNumber: formData.phoneNationalNumber,
        website: formData.website || undefined,
        gstNumber: formData.gstNumber || undefined,
        preferredContactMethod: formData.preferredContactMethod as any,
        consent: formData.consent,
        otpSessionId: otpId,
        otpCode: otpCode,
      })
      setRegistrationId(reg.registration_id)
      if (reg.access_token) {
        authService.setTokens({
          access_token: reg.access_token,
          refresh_token: reg.refresh_token,
          token_type: reg.token_type || 'bearer',
          expires_in: reg.expires_in || 3600,
        })
      }
      try { window.dispatchEvent(new Event('waooaw:auth-changed')) } catch { /* ignore */ }
      resetState()
      handleSuccess()
    } catch (e: any) {
      const msg = e instanceof Error ? e.message : 'Registration failed'
      // Detect expired/invalid OTP from backend — send user back to re-verify
      const isOtpError = /otp|expired|invalid.*code|verification/i.test(msg)
      if (isOtpError) {
        setRegisterError('Your email verification expired. Please re-verify your email to continue.')
        setStep1State('email')
        setOtpId(null)
        setOtpCode('')
        setRegStep(1)
      } else {
        setRegisterError(msg)
      }
    } finally {
      setRegisterSubmitting(false)
    }
  }

  // Kept for sign-in OTP verify (login flow — unchanged)
  // Registration no longer uses a post-step-3 OTP screen; see handleRegisterSubmit above.

  const handleResendRegisterOtp = async () => {
    if (registerResendSecondsLeft > 0) return
    setOtpError(null)
    setRegisterSubmitting(true)
    try {
      const otpStart = await startRegistrationOtp(formData.email, captchaToken)
      setOtpId(otpStart.otp_id)
      setOtpCode('')
      setRegisterResendSecondsLeft(OTP_RESEND_COOLDOWN_SECONDS)

      setOtpHint(`A new verification code has been sent to ${formData.email}. Please check your inbox and spam/junk folder.`)
    } catch (e: any) {
      resetCaptcha()
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

      setSigninOtpHint(`A verification code has been sent to ${signinEmail}. Please check your inbox and spam/junk folder.`)
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

      setSigninOtpHint(`A new verification code has been sent to ${signinEmail}. Please check your inbox and spam/junk folder.`)
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
    <div className={embedded ? styles.embeddedSurface : styles.surface}>
      {!embedded && (
        <div className={`${styles.header} ${styles.headerBorder} ${isRegisterMode ? styles.headerCompact : ''}`}>
          <h1 className={styles.title}>{mode === 'signin' ? 'Sign in to WAOOAW' : 'Create your WAOOAW account'}</h1>
          {showCloseButton ? (
            <Button appearance="subtle" aria-label="Close" icon={<Dismiss24Regular />} onClick={onClose} className={styles.closeButton} />
          ) : null}
        </div>
      )}

      <div className={`${styles.content} ${isRegisterMode ? styles.contentCompact : ''}`}>
        {mode === 'signin' ? (
          <>
            {/* Logo + tagline only when rendered standalone (not embedded in unified card) */}
            {!embedded && (
              <>
                <div className={styles.logo}>👋</div>
                <div className={styles.subtitle}>
                  <strong className={styles.subtitleStrong}>Welcome to WAOOAW</strong>
                  <br />
                  Agents that make you say WOW!
                </div>
              </>
            )}

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
            {/* Step dots — only shown standalone (left panel plays this role when embedded) */}
            {!embedded && (
              <div className={styles.stepDots}>
                {([1, 2, 3] as const).map((n) => (
                  <div
                    key={n}
                    className={[
                      styles.stepDot,
                      regStep === n ? styles.stepDotActive : '',
                      regStep > n ? styles.stepDotDone : ''
                    ].join(' ')}
                  />
                ))}
              </div>
            )}

            {regStep === 1 ? (
              /* ── Step 1 : Email → OTP verify ─────────────────────────── */
              <>
                {/* Google prefill shortcut */}
                {step1State === 'email' && (
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
                    <div className={`${styles.divider} ${styles.dividerCompact}`} />
                  </>
                )}

                {!embedded && (
                  <>
                    <div className={styles.stepHeading}>
                      {step1State === 'otp-pending' ? 'Check your inbox' : "Let's get started"}
                    </div>
                    <div className={styles.stepSubHeading}>
                      {step1State === 'otp-pending'
                        ? `Enter the code we sent to ${formData.email}`
                        : step1State === 'verified'
                        ? 'Email verified — continue below or change your email'
                        : 'Enter your work email to create your account'}
                    </div>
                  </>
                )}

                {/* Email field — locked once OTP is pending */}
                <Field
                  label="Work email"
                  required
                  validationMessage={errors.email}
                  validationState={errors.email ? 'error' : undefined}
                  className={styles.fullWidth}
                >
                  <Input
                    className={styles.fullWidth}
                    type="email"
                    value={formData.email}
                    placeholder="you@company.com"
                    autoFocus={step1State === 'email'}
                    disabled={step1State === 'otp-pending'}
                    onChange={(e) => {
                      setFormData((p) => ({ ...p, email: e.target.value }))
                      // Clear verification state if user edits email after verified
                      if (step1State === 'verified') handleChangeEmail()
                    }}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && step1State === 'email') handleStep1Continue()
                    }}
                  />
                </Field>

                {/* ── sub-state: initial email entry ── */}
                {step1State === 'email' && (
                  <>
                    {/* CAPTCHA lives here since OTP call needs it */}
                    {turnstileSiteKey ? (
                      <Field
                        label=""
                        validationMessage={captchaError || undefined}
                        validationState={captchaError ? 'error' : undefined}
                        className={styles.fullWidth}
                      >
                        <CaptchaWidget key={captchaResetKey} siteKey={turnstileSiteKey} onToken={handleCaptchaToken} onError={handleCaptchaError} />
                      </Field>
                    ) : (
                      !isProduction && <div style={{ fontSize: '0.75rem', color: 'var(--colorNeutralForeground3)' }}>CAPTCHA not configured (dev mode)</div>
                    )}

                    {registerError && <div className={styles.errorText}>{registerError}</div>}

                    {/* Duplicate email — NOT a blocker, two escape routes */}
                    {duplicateEmailDetected && (
                      <div className={styles.errorText} style={{ textAlign: 'center' }}>
                        <p style={{ marginBottom: '8px' }}>This email is already registered.</p>
                        <div style={{ display: 'flex', gap: '8px', justifyContent: 'center', flexWrap: 'wrap' }}>
                          <Button appearance="primary" size="small" onClick={() => { setDuplicateEmailDetected(false); requestSignIn() }}>
                            Sign in instead
                          </Button>
                          <Button appearance="secondary" size="small" onClick={() => { setDuplicateEmailDetected(false); setFormData((p) => ({ ...p, email: '' })); setErrors({}) }}>
                            Use different email
                          </Button>
                        </div>
                      </div>
                    )}

                    <Button
                      appearance="secondary"
                      className={styles.fullWidth}
                      disabled={registerSubmitting}
                      onClick={handleStep1Continue}
                    >
                      {registerSubmitting ? 'Sending code…' : 'Continue →'}
                    </Button>

                    <Button appearance="subtle" onClick={requestSignIn} className={styles.fullWidth}>
                      Already have an account? Sign in
                    </Button>
                  </>
                )}

                {/* ── sub-state: OTP code input ── */}
                {step1State === 'otp-pending' && (
                  <>
                    <Field
                      label="Verification code"
                      required
                      validationMessage={otpError || otpHint || undefined}
                      validationState={otpError ? 'error' : undefined}
                      className={styles.fullWidth}
                    >
                      <Input
                        className={styles.fullWidth}
                        type="text"
                        inputMode="numeric"
                        maxLength={8}
                        value={otpCode}
                        placeholder="6-digit code"
                        autoFocus
                        onChange={(e) => {
                          setOtpCode(e.target.value)
                          if (otpError) setOtpError(null) // clear inline error as user types
                        }}
                        onKeyDown={(e) => { if (e.key === 'Enter') handleStep1VerifyOtp() }}
                      />
                    </Field>

                    <div className={styles.navRow}>
                      <Button appearance="secondary" onClick={handleChangeEmail} style={{ flex: 1 }}>
                        ← Change email
                      </Button>
                      <Button
                        appearance="secondary"
                        onClick={handleStep1VerifyOtp}
                        style={{ flex: 1 }}
                      >
                        Verify email →
                      </Button>
                    </div>

                    <Button
                      appearance="subtle"
                      onClick={handleResendRegisterOtp}
                      disabled={registerSubmitting || registerResendSecondsLeft > 0}
                      className={styles.fullWidth}
                    >
                      {registerResendSecondsLeft > 0 ? `Resend code in ${registerResendSecondsLeft}s` : 'Resend code'}
                    </Button>
                  </>
                )}

                {/* ── sub-state: verified (user came back via Back button) ── */}
                {step1State === 'verified' && (
                  <>
                    <div style={{
                      width: '100%', padding: '10px 14px', borderRadius: '8px',
                      background: 'var(--colorStatusSuccessBackground1)',
                      border: '1px solid var(--colorStatusSuccessBorder1)',
                      fontSize: '13px', color: 'var(--colorStatusSuccessForeground1)',
                      display: 'flex', alignItems: 'center', gap: '8px'
                    }}>
                      <span>✅</span>
                      <span style={{ flex: 1 }}>Email verified</span>
                      <Button appearance="subtle" size="small" onClick={handleChangeEmail}>Change</Button>
                    </div>
                    <Button appearance="secondary" className={styles.fullWidth} onClick={() => setRegStep(2)}>
                      Continue →
                    </Button>
                    <Button appearance="subtle" onClick={requestSignIn} className={styles.fullWidth}>
                      Already have an account? Sign in
                    </Button>
                  </>
                )}
              </>

            ) : regStep === 2 ? (
              /* ── Step 2 : Name · Business · Industry ─────────────────── */
              <>
                {!embedded && (
                  <>
                    <div className={styles.stepHeading}>Tell us about you</div>
                    <div className={styles.stepSubHeading}>This helps us personalise your agent recommendations</div>
                  </>
                )}

                <Field
                  label="Your full name"
                  required
                  validationMessage={errors.fullName}
                  validationState={errors.fullName ? 'error' : undefined}
                  className={styles.fullWidth}
                >
                  <Input
                    className={styles.fullWidth}
                    value={formData.fullName}
                    placeholder="Jane Smith"
                    autoFocus
                    onChange={(e) => setFormData((p) => ({ ...p, fullName: e.target.value }))}
                  />
                </Field>

                <Field
                  label="Business name"
                  required
                  validationMessage={errors.businessName}
                  validationState={errors.businessName ? 'error' : undefined}
                  className={styles.fullWidth}
                >
                  <Input
                    className={styles.fullWidth}
                    value={formData.businessName}
                    placeholder="Acme Inc."
                    onChange={(e) => setFormData((p) => ({ ...p, businessName: e.target.value }))}
                  />
                </Field>

                <Field
                  label="Industry"
                  required
                  validationMessage={errors.businessIndustry}
                  validationState={errors.businessIndustry ? 'error' : undefined}
                  className={styles.fullWidth}
                >
                  <Select
                    value={formData.businessIndustry}
                    onChange={(_, data) => setFormData((p) => ({ ...p, businessIndustry: String(data.value || '') }))}
                  >
                    <option value="">Select your industry</option>
                    {INDUSTRY_OPTIONS.map((opt) => (
                      <option key={opt.value} value={opt.value}>{opt.label}</option>
                    ))}
                  </Select>
                </Field>

                <Field
                  label="Business address (optional)"
                  className={styles.fullWidth}
                >
                  <Input
                    className={styles.fullWidth}
                    value={formData.businessAddress}
                    placeholder="City, State, Country"
                    onChange={(e) => setFormData((p) => ({ ...p, businessAddress: e.target.value }))}
                  />
                </Field>

                <div className={styles.navRow}>
                  <Button appearance="secondary" onClick={() => { setErrors({}); setRegStep(1) }} style={{ flex: 1 }}>
                    ← Back
                  </Button>
                  <Button
                    appearance="secondary"
                    onClick={() => { if (validateStep2()) setRegStep(3) }}
                    style={{ flex: 1 }}
                  >
                    Continue →
                  </Button>
                </div>
              </>

            ) : (
              /* ── Step 3 : Phone · Contact · Consent ───────────────────── */
              <>
                {!embedded && (
                  <>
                    <div className={styles.stepHeading}>Almost done!</div>
                    <div className={styles.stepSubHeading}>Add a phone number so agents can reach you faster</div>
                  </>
                )}

                <Field
                  label="Country"
                  required
                  validationMessage={errors.phoneCountry}
                  validationState={errors.phoneCountry ? 'error' : undefined}
                  className={styles.fullWidth}
                >
                  <Select
                    value={formData.phoneCountry}
                    onChange={(_, data) => setFormData((p) => ({ ...p, phoneCountry: String(data.value || 'IN') }))}
                  >
                    {PHONE_COUNTRY_OPTIONS.map((opt) => (
                      <option key={opt.code} value={opt.code}>{opt.label}</option>
                    ))}
                  </Select>
                </Field>

                <Field
                  label="Mobile number"
                  required
                  validationMessage={errors.phoneNationalNumber}
                  validationState={errors.phoneNationalNumber ? 'error' : undefined}
                  className={styles.fullWidth}
                >
                  <Input
                    className={styles.fullWidth}
                    type="tel"
                    value={formData.phoneNationalNumber}
                    placeholder={formData.phoneCountry === 'IN' ? '9876543210' : 'Mobile number'}
                    autoFocus
                    onChange={(e) => setFormData((p) => ({ ...p, phoneNationalNumber: e.target.value }))}
                  />
                </Field>

                <Field
                  label="Preferred contact"
                  required
                  validationMessage={errors.preferredContactMethod}
                  validationState={errors.preferredContactMethod ? 'error' : undefined}
                  className={styles.fullWidth}
                >
                  <div className={styles.contactToggle}>
                    {(['email', 'phone'] as const).map((m) => (
                      <button
                        key={m}
                        type="button"
                        className={[
                          styles.contactBtn,
                          formData.preferredContactMethod === m ? styles.contactBtnActive : ''
                        ].join(' ')}
                        onClick={() => setFormData((p) => ({ ...p, preferredContactMethod: m }))}
                      >
                        {m === 'email' ? '✉️ Email' : '📱 Phone'}
                      </button>
                    ))}
                  </div>
                </Field>

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

                {/* Registration error — OTP-expiry errors are detected in handleRegisterSubmit */}
                {registerError ? (
                  <div className={styles.errorText} style={{ textAlign: 'center' }}>
                    <p style={{ marginBottom: '8px' }}>{registerError}</p>
                    {/re-verify/i.test(registerError) && (
                      <Button appearance="secondary" size="small" onClick={() => { setRegisterError(null); setRegStep(1) }}>
                        ← Re-verify email
                      </Button>
                    )}
                  </div>
                ) : null}

                <div className={styles.navRow}>
                  <Button appearance="secondary" onClick={() => { setErrors({}); setRegStep(2) }} disabled={registerSubmitting} style={{ flex: 1 }}>
                    ← Back
                  </Button>
                  <Button
                    appearance="secondary"
                    onClick={() => { if (validateStep3()) handleRegisterSubmit() }}
                    disabled={registerSubmitting || !formData.consent}
                    style={{ flex: 1 }}
                  >
                    {registerSubmitting ? 'Creating account…' : 'Create account 🚀'}
                  </Button>
                </div>
              </>
            )}
          </>
        )}
      </div>
    </div>
  )
}
