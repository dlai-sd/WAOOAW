import {
  Button,
  Checkbox,
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
    gap: '10px',
    alignItems: 'center',
    padding: '4px 0'
  },
  contentCompact: {
    gap: '10px',
    padding: '4px 0'
  },
  formShell: {
    width: '100%',
    display: 'flex',
    flexDirection: 'column',
    gap: '18px'
  },
  formIntro: {
    width: '100%',
    display: 'flex',
    flexDirection: 'column',
    gap: '6px'
  },
  formEyebrow: {
    textTransform: 'uppercase',
    letterSpacing: '0.12em',
    fontSize: '11px',
    fontWeight: '700',
    color: tokens.colorBrandForeground1,
  },
  formHeading: {
    fontSize: '24px',
    lineHeight: '1.15',
    fontWeight: '700',
    color: tokens.colorNeutralForeground1,
    margin: 0,
  },
  formBody: {
    fontSize: '13px',
    lineHeight: '1.65',
    color: tokens.colorNeutralForeground2,
    margin: 0,
  },
  stageCard: {
    width: '100%',
    display: 'flex',
    flexDirection: 'column',
    gap: '14px',
    padding: '18px',
    borderRadius: '20px',
    border: `1px solid ${tokens.colorNeutralStroke2}`,
    backgroundColor: tokens.colorNeutralBackground2,
    boxShadow: tokens.shadow4,
  },
  stageCardTight: {
    gap: '12px',
  },
  stageCardHeader: {
    display: 'flex',
    flexDirection: 'column',
    gap: '4px',
  },
  stageCardEyebrow: {
    fontSize: '11px',
    fontWeight: '700',
    letterSpacing: '0.1em',
    textTransform: 'uppercase',
    color: tokens.colorBrandForeground1,
  },
  stageCardTitle: {
    fontSize: '16px',
    lineHeight: '1.35',
    fontWeight: '700',
    color: tokens.colorNeutralForeground1,
  },
  stageCardBody: {
    fontSize: '12px',
    lineHeight: '1.6',
    color: tokens.colorNeutralForeground2,
  },
  dividerRow: {
    width: '100%',
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
  },
  dividerLine: {
    flex: 1,
    height: '1px',
    backgroundColor: tokens.colorNeutralStroke2,
  },
  dividerText: {
    fontSize: '11px',
    fontWeight: '700',
    letterSpacing: '0.08em',
    textTransform: 'uppercase',
    color: tokens.colorNeutralForeground3,
  },
  otpPanel: {
    width: '100%',
    display: 'flex',
    flexDirection: 'column',
    gap: '12px',
    padding: '14px',
    borderRadius: '16px',
    border: `1px solid ${tokens.colorNeutralStroke2}`,
    backgroundColor: tokens.colorNeutralBackground1,
  },
  otpMeta: {
    display: 'flex',
    flexDirection: 'column',
    gap: '4px',
  },
  otpTitle: {
    fontSize: '14px',
    fontWeight: '700',
    color: tokens.colorNeutralForeground1,
  },
  otpSubtitle: {
    fontSize: '12px',
    lineHeight: '1.5',
    color: tokens.colorNeutralForeground2,
  },
  successBadge: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    padding: '10px 12px',
    borderRadius: '14px',
    border: `1px solid ${tokens.colorStatusSuccessBorder1}`,
    backgroundColor: tokens.colorStatusSuccessBackground1,
    color: tokens.colorStatusSuccessForeground1,
    fontSize: '13px',
    fontWeight: '600',
  },
  actionRow: {
    width: '100%',
    display: 'flex',
    gap: '10px',
    alignItems: 'center',
    '@media (max-width: 640px)': {
      flexDirection: 'column',
      alignItems: 'stretch',
    }
  },
  inlineActions: {
    width: '100%',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    gap: '10px',
    flexWrap: 'wrap',
  },
  ghostButton: {
    color: tokens.colorNeutralForeground2,
    paddingLeft: 0,
    paddingRight: 0,
  },
  legalText: {
    fontSize: '11px',
    lineHeight: '1.6',
    color: tokens.colorNeutralForeground3,
    textAlign: 'left',
  },
  otpGrid: {
    display: 'flex',
    gap: '8px',
    justifyContent: 'flex-start',
    flexWrap: 'nowrap',
    '@media (max-width: 420px)': {
      gap: '6px',
    }
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
    margin: '-2px 0'
  },
  dividerCompact: {
    margin: '-2px 0'
  },
  helperText: {
    width: '100%',
    marginTop: '-10px',
    fontSize: '12px',
    lineHeight: '1.4',
    color: tokens.colorNeutralForeground2
  },
  errorText: {
    width: '100%',
    textAlign: 'left',
    fontSize: tokens.fontSizeBase200,
    lineHeight: tokens.lineHeightBase200,
    fontFamily: tokens.fontFamilyBase,
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
  const [otpDigits, setOtpDigits] = useState<string[]>(['', '', '', '', '', ''])
  const otpCode = otpDigits.join('')
  const [otpHint, setOtpHint] = useState<string | null>(null)
  const [otpError, setOtpError] = useState<string | null>(null)
  const [registerResendSecondsLeft, setRegisterResendSecondsLeft] = useState(0)

  const [signinEmail, setSigninEmail] = useState('')
  const [signinOtpId, setSigninOtpId] = useState<string | null>(null)
  const [signinOtpDigits, setSigninOtpDigits] = useState<string[]>(['', '', '', '', '', ''])
  const signinOtpCode = signinOtpDigits.join('')
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
    setOtpDigits(['', '', '', '', '', ''])
    setOtpHint(null)
    setOtpError(null)
    setRegisterResendSecondsLeft(0)
    setRegStep(1)

    setSigninEmail('')
    setSigninOtpId(null)
    setSigninOtpDigits(['', '', '', '', '', ''])
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
      setOtpDigits(['', '', '', '', '', ''])
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
    setOtpDigits(['', '', '', '', '', ''])
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
        setOtpDigits(['', '', '', '', '', ''])
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
      setOtpDigits(['', '', '', '', '', ''])
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
      setSigninOtpDigits(['', '', '', '', '', ''])
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

  const handleSigninChangeEmail = () => {
    setSigninOtpId(null)
    setSigninOtpDigits(['', '', '', '', '', ''])
    setSigninOtpHint(null)
    setSigninOtpError(null)
    setSigninResendSecondsLeft(0)
  }

  const requestSignUp = () => {
    if (onRequestSignUp) return onRequestSignUp()
    setMode('register')
  }

  const requestSignIn = () => {
    if (onRequestSignIn) return onRequestSignIn()
    setMode('signin')
  }

  const handleRegisterPrimaryAction = () => {
    if (duplicateEmailDetected) {
      setDuplicateEmailDetected(false)
      requestSignIn()
      return
    }

    if (step1State === 'otp-pending') {
      handleStep1VerifyOtp()
      return
    }

    if (step1State === 'verified') {
      setRegStep(2)
      return
    }

    handleStep1Continue()
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
          <div className={styles.formShell}>
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

            <div className={styles.formIntro}>
              <div className={styles.formEyebrow}>Fast entry</div>
              <h2 className={styles.formHeading}>Sign in without the usual auth friction.</h2>
              <p className={styles.formBody}>
                Pick the fastest route in. Use Google for instant access, or verify your work email and continue in one clean flow.
              </p>
            </div>

            <div className={`${styles.stageCard} ${styles.stageCardTight}`}>
              <div className={styles.stageCardHeader}>
                <div className={styles.stageCardEyebrow}>Instant option</div>
                <div className={styles.stageCardTitle}>Continue with Google</div>
                <div className={styles.stageCardBody}>Best for founders and operators who just want to get to the portal immediately.</div>
              </div>
              <GoogleLoginButton onSuccess={handleSuccess} onError={handleError} />
            </div>

            <div className={styles.dividerRow}>
              <div className={styles.dividerLine} />
              <div className={styles.dividerText}>or use your work email</div>
              <div className={styles.dividerLine} />
            </div>

            <div className={styles.stageCard}>
              <div className={styles.stageCardHeader}>
                <div className={styles.stageCardEyebrow}>Email OTP</div>
                <div className={styles.stageCardTitle}>Passwordless sign in for your team</div>
                <div className={styles.stageCardBody}>We will send a 6-digit code to verify your identity. No password reset loops.</div>
              </div>

              <div className="form-group">
                <label>Work email *</label>
                <Input
                  className={styles.fullWidth}
                  type="email"
                  value={signinEmail}
                  placeholder="you@company.com"
                  disabled={Boolean(signinOtpId)}
                  onChange={(e) => setSigninEmail(e.target.value)}
                  onKeyDown={(e) => { if (e.key === 'Enter' && !signinOtpId) handleSigninStartOtp() }}
                />
              </div>

              {!signinOtpId ? (
                <Button
                  appearance="primary"
                  onClick={handleSigninStartOtp}
                  disabled={signinSubmitting || signinEmail.trim().length === 0}
                  className={styles.fullWidth}
                >
                  {signinSubmitting ? 'Sending…' : 'Send OTP'}
                </Button>
              ) : (
                <div className={styles.otpPanel}>
                  <div className={styles.otpMeta}>
                    <div className={styles.otpTitle}>Verification code</div>
                    <div className={styles.otpSubtitle}>Enter the code we sent to {signinEmail} to unlock your workspace.</div>
                  </div>
                  <div className={styles.otpGrid}>
                    {signinOtpDigits.map((digit, i) => (
                      <input
                        key={i}
                        aria-label={`OTP digit ${i + 1}`}
                        className="auth-otp-digit"
                        type="text"
                        inputMode="numeric"
                        maxLength={1}
                        value={digit}
                        disabled={!signinOtpId}
                        autoFocus={signinOtpId !== null && i === 0}
                        onChange={(e) => {
                          const val = e.target.value.replace(/\D/g, '').slice(-1)
                          const next = [...signinOtpDigits]
                          next[i] = val
                          setSigninOtpDigits(next)
                          if (val && i < 5) {
                            const nextBox = document.querySelector<HTMLInputElement>(`[data-signin-otp="${i + 1}"]`)
                            nextBox?.focus()
                          }
                        }}
                        onKeyDown={(e) => {
                          if (e.key === 'Backspace' && !signinOtpDigits[i] && i > 0) {
                            const prevBox = document.querySelector<HTMLInputElement>(`[data-signin-otp="${i - 1}"]`)
                            prevBox?.focus()
                          }
                          if (e.key === 'Enter' && signinOtpId) handleSigninVerifyOtp()
                        }}
                        onPaste={(e) => {
                          const paste = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, 6)
                          if (paste) {
                            const next = ['', '', '', '', '', '']
                            for (let j = 0; j < paste.length; j++) next[j] = paste[j]
                            setSigninOtpDigits(next)
                            const focusIdx = Math.min(paste.length, 5)
                            const box = document.querySelector<HTMLInputElement>(`[data-signin-otp="${focusIdx}"]`)
                            box?.focus()
                            e.preventDefault()
                          }
                        }}
                        data-signin-otp={i}
                      />
                    ))}
                  </div>

                  <div style={{ minHeight: '18px', width: '100%' }}>
                    {signinOtpError ? (
                      <div className={styles.errorText}>{signinOtpError}</div>
                    ) : signinOtpHint ? (
                      <div className={styles.helperText} style={{ marginTop: 0 }}>{signinOtpHint}</div>
                    ) : null}
                  </div>

                  <div className={styles.actionRow}>
                    <Button
                      appearance="primary"
                      onClick={handleSigninVerifyOtp}
                      disabled={signinSubmitting || signinOtpCode.trim().length === 0}
                      className={styles.fullWidth}
                    >
                      {signinSubmitting ? 'Verifying…' : 'Verify & Sign in'}
                    </Button>
                    <Button appearance="subtle" onClick={handleSigninChangeEmail} className={styles.ghostButton}>
                      Change email
                    </Button>
                  </div>
                </div>
              )}
            </div>

            <div className={styles.inlineActions}>
              <Button
                appearance="subtle"
                onClick={handleSigninResendOtp}
                disabled={signinSubmitting || !signinOtpId || signinResendSecondsLeft > 0}
                className={styles.ghostButton}
              >
                {signinResendSecondsLeft > 0 ? `Resend OTP (${signinResendSecondsLeft}s)` : 'Resend OTP'}
              </Button>

              <Button appearance="subtle" onClick={requestSignUp} className={styles.ghostButton}>
                Don’t have an account? Sign up
              </Button>
            </div>

            <div className={styles.legalText}>
              By signing in, you agree to our Terms of Service and Privacy Policy.
            </div>
          </div>
        ) : (
          <div className={styles.formShell}>
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

            <div className={styles.formIntro}>
              <div className={styles.formEyebrow}>Startup onboarding</div>
              <h2 className={styles.formHeading}>
                {regStep === 1 ? 'Launch your first trial with a cleaner setup flow.' : regStep === 2 ? 'Tell us enough to personalise the first agent shortlist.' : 'Finish setup and unlock your workspace.'}
              </h2>
              <p className={styles.formBody}>
                {regStep === 1 ? 'We start with fast verification so you can move from curiosity to trial without losing momentum.' : regStep === 2 ? 'This business context helps WAOOAW feel more like a modern operating system than a generic lead form.' : 'One last contact step, then your account is ready for live agent trials and deliverables.'}
              </p>
            </div>

            {regStep === 1 ? (
              /* ── Step 1 : Email → OTP verify ─────────────────────────── */
              <>
                {/* Google prefill shortcut */}
                {step1State === 'email' && (
                  <div className={`${styles.stageCard} ${styles.stageCardTight}`}>
                    <div className={styles.stageCardHeader}>
                      <div className={styles.stageCardEyebrow}>Shortcut</div>
                      <div className={styles.stageCardTitle}>Prefill with Google</div>
                      <div className={styles.stageCardBody}>Useful when you want your name and work email dropped into the flow instantly.</div>
                    </div>
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
                  </div>
                )}

                {step1State === 'email' && (
                  <div className={styles.dividerRow}>
                    <div className={styles.dividerLine} />
                    <div className={styles.dividerText}>or verify with work email</div>
                    <div className={styles.dividerLine} />
                  </div>
                )}

                <div className={styles.stageCard}>
                  <div className={styles.stageCardHeader}>
                    <div className={styles.stageCardEyebrow}>Step 1 of 3</div>
                    <div className={styles.stageCardTitle}>
                      {step1State === 'otp-pending' ? 'Check your inbox' : step1State === 'verified' ? "Let's get started" : "Let's get started"}
                    </div>
                    <div className={styles.stageCardBody}>
                      {step1State === 'otp-pending'
                        ? `Enter the code we sent to ${formData.email}.`
                        : step1State === 'verified'
                        ? 'Your email is ready. Continue into business setup or change it if needed.'
                        : 'Use the email you want tied to your trial account and future deliverables.'}
                    </div>
                  </div>

                  <div className="form-group">
                    <label>Work email *</label>
                    <Input
                      className={styles.fullWidth}
                      type="email"
                      value={formData.email}
                      placeholder="you@company.com"
                      autoFocus={step1State === 'email'}
                      disabled={step1State === 'otp-pending' || step1State === 'verified'}
                      onChange={(e) => {
                        setFormData((p) => ({ ...p, email: e.target.value }))
                        if (step1State === 'verified') handleChangeEmail()
                      }}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' && step1State === 'email') handleStep1Continue()
                      }}
                    />
                  </div>

                  <div style={{ minHeight: '20px', width: '100%' }}>
                    {errors.email ? (
                      <div className={styles.errorText}>{errors.email}</div>
                    ) : step1State === 'verified' ? (
                      <div className={styles.successBadge}>
                        <span>✅</span>
                        <span style={{ flex: 1 }}>Email verified</span>
                        <Button appearance="subtle" size="small" onClick={handleChangeEmail}>Change</Button>
                      </div>
                    ) : (
                      <div className={styles.helperText}>
                        We’ll send a 6-digit code before creating your account.
                      </div>
                    )}
                  </div>

                  {step1State === 'email' && (
                    <>
                      {turnstileSiteKey ? (
                        <div className="form-group">
                          <CaptchaWidget key={captchaResetKey} siteKey={turnstileSiteKey} onToken={handleCaptchaToken} onError={handleCaptchaError} />
                          {captchaError && <div className="field-error">{captchaError}</div>}
                        </div>
                      ) : (
                        !isProduction && <div style={{ fontSize: '0.75rem', color: 'var(--colorNeutralForeground3)' }}>CAPTCHA not configured (dev mode)</div>
                      )}
                    </>
                  )}

                  {step1State === 'otp-pending' && (
                    <div className={styles.otpPanel}>
                      <div className={styles.otpMeta}>
                        <div className={styles.otpTitle}>Verification code</div>
                        <div className={styles.otpSubtitle}>Paste the code from your inbox to unlock the next onboarding step.</div>
                      </div>
                      <div className={styles.otpGrid}>
                      {otpDigits.map((digit, i) => (
                        <input
                          key={i}
                          aria-label={`OTP digit ${i + 1}`}
                          className="auth-otp-digit"
                          type="text"
                          inputMode="numeric"
                          maxLength={1}
                          value={digit}
                          disabled={step1State !== 'otp-pending'}
                          autoFocus={step1State === 'otp-pending' && i === 0}
                          onChange={(e) => {
                            const val = e.target.value.replace(/\D/g, '').slice(-1)
                            const next = [...otpDigits]
                            next[i] = val
                            setOtpDigits(next)
                            if (val && i < 5) {
                              const nextBox = document.querySelector<HTMLInputElement>(`[data-reg-otp="${i + 1}"]`)
                              nextBox?.focus()
                            }
                            if (otpError) setOtpError(null)
                          }}
                          onKeyDown={(e) => {
                            if (e.key === 'Backspace' && !otpDigits[i] && i > 0) {
                              const prevBox = document.querySelector<HTMLInputElement>(`[data-reg-otp="${i - 1}"]`)
                              prevBox?.focus()
                            }
                            if (e.key === 'Enter' && step1State === 'otp-pending') handleStep1VerifyOtp()
                          }}
                          onPaste={(e) => {
                            const paste = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, 6)
                            if (paste) {
                              const next = ['', '', '', '', '', '']
                              for (let j = 0; j < paste.length; j++) next[j] = paste[j]
                              setOtpDigits(next)
                              const focusIdx = Math.min(paste.length, 5)
                              const box = document.querySelector<HTMLInputElement>(`[data-reg-otp="${focusIdx}"]`)
                              box?.focus()
                              e.preventDefault()
                            }
                          }}
                          data-reg-otp={i}
                        />
                      ))}
                      </div>
                    </div>
                  )}

                  <div style={{ minHeight: '18px', width: '100%' }}>
                  {otpError ? (
                    <div className={styles.errorText}>{otpError}</div>
                  ) : otpHint ? (
                    <div className={styles.helperText} style={{ marginTop: 0 }}>{otpHint}</div>
                  ) : registerError ? (
                    <div className={styles.errorText}>{registerError}</div>
                  ) : null}
                  </div>

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

                  <div className={styles.actionRow}>
                    <Button
                      appearance="primary"
                      onClick={handleRegisterPrimaryAction}
                      disabled={registerSubmitting || (step1State === 'otp-pending' && otpCode.trim().length === 0)}
                      className={styles.fullWidth}
                    >
                      {duplicateEmailDetected ? 'Sign in instead' : registerSubmitting
                        ? (step1State === 'otp-pending' ? 'Verifying…' : 'Sending code…')
                        : step1State === 'otp-pending' ? 'Verify email →'
                        : 'Continue →'}
                    </Button>

                    {step1State === 'otp-pending' ? (
                      <Button appearance="subtle" onClick={handleChangeEmail} className={styles.ghostButton}>
                        Change email
                      </Button>
                    ) : null}
                  </div>
                </div>

                <div className={styles.inlineActions}>
                  <Button
                    appearance="subtle"
                    onClick={handleResendRegisterOtp}
                    disabled={registerSubmitting || step1State !== 'otp-pending' || registerResendSecondsLeft > 0}
                    className={styles.ghostButton}
                  >
                    {registerResendSecondsLeft > 0 ? `Resend code in ${registerResendSecondsLeft}s` : 'Resend code'}
                  </Button>

                  <Button appearance="subtle" onClick={requestSignIn} className={styles.ghostButton}>
                    Already have an account? Sign in
                  </Button>
                </div>
              </>

            ) : regStep === 2 ? (
              /* ── Step 2 : Name · Business · Industry ─────────────────── */
              <>
                <div className={styles.stageCard}>
                  <div className={styles.stageCardHeader}>
                    <div className={styles.stageCardEyebrow}>Step 2 of 3</div>
                    <div className={styles.stageCardTitle}>Tell us about you</div>
                    <div className={styles.stageCardBody}>Enough context to make the agent marketplace feel curated instead of generic.</div>
                  </div>

                  <div className={styles.twoColGrid}>
                    <div className="form-group">
                      <label>Your full name *</label>
                      <Input
                        className={styles.fullWidth}
                        value={formData.fullName}
                        placeholder="Jane Smith"
                        autoFocus
                        onChange={(e) => setFormData((p) => ({ ...p, fullName: e.target.value }))}
                      />
                      {errors.fullName && <div className="field-error">{errors.fullName}</div>}
                    </div>

                    <div className="form-group">
                      <label>Business name *</label>
                      <Input
                        className={styles.fullWidth}
                        value={formData.businessName}
                        placeholder="Acme Inc."
                        onChange={(e) => setFormData((p) => ({ ...p, businessName: e.target.value }))}
                      />
                      {errors.businessName && <div className="field-error">{errors.businessName}</div>}
                    </div>

                    <div className="form-group">
                      <label>Industry *</label>
                      <Select
                        value={formData.businessIndustry}
                        onChange={(_, data) => setFormData((p) => ({ ...p, businessIndustry: String(data.value || '') }))}
                      >
                        <option value="">Select your industry</option>
                        {INDUSTRY_OPTIONS.map((opt) => (
                          <option key={opt.value} value={opt.value}>{opt.label}</option>
                        ))}
                      </Select>
                      {errors.businessIndustry && <div className="field-error">{errors.businessIndustry}</div>}
                    </div>

                    <div className="form-group">
                      <label>Business address (optional)</label>
                      <Input
                        className={styles.fullWidth}
                        value={formData.businessAddress}
                        placeholder="City, State, Country"
                        onChange={(e) => setFormData((p) => ({ ...p, businessAddress: e.target.value }))}
                      />
                    </div>
                  </div>

                  <div className={styles.navRow}>
                    <Button appearance="secondary" onClick={() => { setErrors({}); setRegStep(1) }} style={{ flex: 1 }}>
                      ← Back
                    </Button>
                    <Button
                      appearance="primary"
                      onClick={() => { if (validateStep2()) setRegStep(3) }}
                      style={{ flex: 1 }}
                    >
                      Continue →
                    </Button>
                  </div>
                </div>
              </>

            ) : (
              /* ── Step 3 : Phone · Contact · Consent ───────────────────── */
              <>
                <div className={styles.stageCard}>
                  <div className={styles.stageCardHeader}>
                    <div className={styles.stageCardEyebrow}>Step 3 of 3</div>
                    <div className={styles.stageCardTitle}>Almost done!</div>
                    <div className={styles.stageCardBody}>This keeps the first trial responsive once your workspace goes live.</div>
                  </div>

                  <div className={styles.twoColGrid}>
                    <div className="form-group">
                      <label>Country *</label>
                      <Select
                        value={formData.phoneCountry}
                        onChange={(_, data) => setFormData((p) => ({ ...p, phoneCountry: String(data.value || 'IN') }))}
                      >
                        {PHONE_COUNTRY_OPTIONS.map((opt) => (
                          <option key={opt.code} value={opt.code}>{opt.label}</option>
                        ))}
                      </Select>
                      {errors.phoneCountry && <div className="field-error">{errors.phoneCountry}</div>}
                    </div>

                    <div className="form-group">
                      <label>Mobile number *</label>
                      <Input
                        className={styles.fullWidth}
                        type="tel"
                        value={formData.phoneNationalNumber}
                        placeholder={formData.phoneCountry === 'IN' ? '9876543210' : 'Mobile number'}
                        autoFocus
                        onChange={(e) => setFormData((p) => ({ ...p, phoneNationalNumber: e.target.value }))}
                      />
                      {errors.phoneNationalNumber && <div className="field-error">{errors.phoneNationalNumber}</div>}
                    </div>

                    <div className={`form-group ${styles.spanTwo}`}>
                      <label>Preferred contact *</label>
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
                      {errors.preferredContactMethod && <div className="field-error">{errors.preferredContactMethod}</div>}
                    </div>

                    <div className={`form-group ${styles.spanTwo}`}>
                      <Checkbox
                        checked={formData.consent}
                        onChange={(_, data) => setFormData((p) => ({ ...p, consent: Boolean(data.checked) }))}
                        label="I agree to the Terms of Service and Privacy Policy"
                      />
                      {errors.consent && <div className="field-error">{errors.consent}</div>}
                    </div>
                  </div>

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
                      appearance="primary"
                      onClick={() => { if (validateStep3()) handleRegisterSubmit() }}
                      disabled={registerSubmitting || !formData.consent}
                      style={{ flex: 1 }}
                    >
                      {registerSubmitting ? 'Creating account…' : 'Create account 🚀'}
                    </Button>
                  </div>
                </div>
              </>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
