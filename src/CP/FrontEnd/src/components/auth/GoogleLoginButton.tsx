/**
 * Google Login Button Component
 * Uses Google's official button SDK
 */

import { GoogleLogin } from '@react-oauth/google'
import { jwtDecode } from 'jwt-decode'
import { useAuth } from '../../hooks/useAuth'

interface GoogleLoginButtonProps {
  mode?: 'signin' | 'prefill'
  onSuccess?: () => void
  onError?: (error: string) => void
  onPrefill?: (payload: { name?: string; email?: string }) => void
}

export default function GoogleLoginButton({ mode = 'signin', onSuccess, onError, onPrefill }: GoogleLoginButtonProps) {
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
    <GoogleLogin
      onSuccess={handleSuccess}
      onError={handleError}
      theme="filled_blue"
      size="large"
      text="signin_with"
      shape="rectangular"
      logo_alignment="left"
      width="350"
    />
  )
}
