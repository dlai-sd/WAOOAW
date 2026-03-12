/**
 * Google Login Button Component
 *
 * Uses Google's official button SDK but with `theme="outline"` so it renders
 * as a neutral white/bordered button (no Google blue fill) — matches Brevo /
 * Linear sign-in aesthetics. The SDK iframe handles all OAuth state safely.
 */

import { makeStyles } from '@fluentui/react-components'
import { GoogleLogin } from '@react-oauth/google'
import { jwtDecode } from 'jwt-decode'
import { useAuth } from '../../hooks/useAuth'

interface GoogleLoginButtonProps {
  mode?: 'signin' | 'prefill'
  onSuccess?: () => void
  onError?: (error: string) => void
  onPrefill?: (payload: { name?: string; email?: string }) => void
}

const useStyles = makeStyles({
  // Wrapper only controls sizing — no border or radius of its own.
  // The Google SDK button (theme="outline") renders its own border,
  // so adding a second border here creates visible double-border artefacts.
  frame: {
    width: '100%',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    overflow: 'hidden',
  },
})

export default function GoogleLoginButton({ mode = 'signin', onSuccess, onError, onPrefill }: GoogleLoginButtonProps) {
  const styles = useStyles()
  const { login } = useAuth()

  const handleSuccess = async (credentialResponse: any) => {
    try {
      if (credentialResponse.credential) {
        if (mode === 'prefill') {
          const decoded: any = jwtDecode(credentialResponse.credential)
          onPrefill?.({ name: decoded?.name, email: decoded?.email })
          onSuccess?.()
          return
        }
        await login(credentialResponse.credential)
        onSuccess?.()
      }
    } catch (error) {
      console.error('Google login error:', error)
      onError?.(error instanceof Error ? error.message : 'Login failed')
    }
  }

  const handleError = () => {
    console.error('Google login failed')
    onError?.('Google login failed')
  }

  return (
    <div className={`${styles.frame} auth-google-frame`}>
      <GoogleLogin
        onSuccess={handleSuccess}
        onError={handleError}
        // "outline" = white background + thin border + coloured G logo
        // No Google-blue fill, no drop shadow — blends with the form
        theme="outline"
        size="large"
        text={mode === 'prefill' ? 'continue_with' : 'continue_with'}
        shape="rectangular"
        logo_alignment="left"
        width="480"
      />
    </div>
  )
}
