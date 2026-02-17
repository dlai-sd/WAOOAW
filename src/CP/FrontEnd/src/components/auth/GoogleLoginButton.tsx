/**
 * Google Login Button Component
 * Uses Google's official button SDK
 */

import { makeStyles, tokens } from '@fluentui/react-components'
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
  container: {
    width: '100%',
    display: 'flex',
    justifyContent: 'center'
  },
  frame: {
    width: 'min(360px, 100%)',
    height: '48px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: '10px',
    overflow: 'hidden',
    backgroundColor: tokens.colorNeutralBackground1,
    border: `1px solid ${tokens.colorNeutralStroke2}`,
    boxShadow: tokens.shadow4,
    selectors: {
      '& > div': {
        width: '100% !important',
        height: '100% !important'
      },
      '& iframe': {
        width: '100% !important',
        height: '100% !important'
      }
    }
  }
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
    <div className={styles.container}>
      <div className={styles.frame}>
        <GoogleLogin
          onSuccess={handleSuccess}
          onError={handleError}
          theme="filled_blue"
          size="large"
          text="signin_with"
          shape="rectangular"
          logo_alignment="left"
          width="360"
        />
      </div>
    </div>
  )
}
