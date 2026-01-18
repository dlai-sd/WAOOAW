/**
 * Auth Callback Page
 * Handles OAuth redirect from backend
 */

import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Spinner } from '@fluentui/react-components'
import authService from '../services/auth.service'
import { useAuth } from '../context/AuthContext'

export default function AuthCallback() {
  const navigate = useNavigate()
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading')
  const [error, setError] = useState<string>('')
  const { refreshUser } = useAuth()

  useEffect(() => {
    const handleCallback = async () => {
      try {
        // Check for error in URL
        const params = new URLSearchParams(window.location.search)
        const errorParam = params.get('error')
        
        if (errorParam) {
          setStatus('error')
          setError(errorParam)
          return
        }

        // Try to get tokens from URL
        const tokens = authService.handleOAuthCallback()
        
        if (tokens) {
          // Load user data
          await refreshUser()
          setStatus('success')
          
          // Redirect to portal after 1 second
          setTimeout(() => {
            navigate('/portal')
          }, 1000)
        } else {
          setStatus('error')
          setError('No tokens received')
        }
      } catch (err) {
        console.error('Auth callback error:', err)
        setStatus('error')
        setError(err instanceof Error ? err.message : 'Authentication failed')
      }
    }

    handleCallback()
  }, [refreshUser])

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      height: '100vh',
      gap: '20px'
    }}>
      {status === 'loading' && (
        <>
          <Spinner size="extra-large" />
          <p>Completing sign in...</p>
        </>
      )}
      
      {status === 'success' && (
        <>
          <div style={{ fontSize: '48px' }}>✅</div>
          <p>Sign in successful! Redirecting...</p>
        </>
      )}
      
      {status === 'error' && (
        <>
          <div style={{ fontSize: '48px' }}>❌</div>
          <p>Authentication failed: {error}</p>
          <a href="/">Return to home</a>
        </>
      )}
    </div>
  )
}
