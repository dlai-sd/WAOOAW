import { Spinner } from '@fluentui/react-components'
import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { useAuth } from '../context/AuthContext'
import { authService } from '../services/auth.service'
import { attachYouTubeConnection, finalizeYouTubeConnection } from '../services/youtubeConnections.service'
import {
  clearPendingYouTubeOAuthContext,
  getStoredYouTubeOAuthState,
  readPendingYouTubeOAuthContext,
  storeYouTubeOAuthResult,
} from '../utils/youtubeOAuthFlow'

export default function YouTubeConnectionCallback() {
  const navigate = useNavigate()
  const { refreshUser } = useAuth()
  const [status, setStatus] = useState('Restoring your session...')
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false

    const finalizeCallback = async () => {
      const params = new URLSearchParams(window.location.search)
      const oauthError = params.get('error')
      const code = params.get('code')
      const state = params.get('state')

      if (oauthError) {
        setError('Google did not complete the YouTube connection. Please try again.')
        clearPendingYouTubeOAuthContext()
        return
      }

      const context = readPendingYouTubeOAuthContext()
      const storedState = getStoredYouTubeOAuthState()

      if (!code || !state || !context || !storedState || storedState !== state || context.state !== state) {
        setError('The YouTube connection could not be matched to your current setup. Please try again.')
        clearPendingYouTubeOAuthContext()
        return
      }

      setStatus('Restoring your account...')
      const restoredToken = authService.isAuthenticated() ? authService.getAccessToken() : await authService.silentRefresh(true)
      if (!restoredToken) {
        navigate(`/signin?next=${encodeURIComponent(window.location.pathname + window.location.search)}`, { replace: true })
        return
      }

      await refreshUser()

      try {
        setStatus('Finishing your YouTube connection...')
        const connection = await finalizeYouTubeConnection({
          state,
          code,
          redirect_uri: context.redirectUri,
        })

        if (context.hiredInstanceId && context.skillId) {
          setStatus('Attaching your channel...')
          await attachYouTubeConnection(connection.id, {
            hired_instance_id: context.hiredInstanceId,
            skill_id: context.skillId,
          })
        }

        if (cancelled) return

        storeYouTubeOAuthResult({
          source: context.source,
          returnTo: context.returnTo,
          subscriptionId: context.subscriptionId,
          hiredInstanceId: context.hiredInstanceId,
          connection,
          message: `Connected ${connection.display_name || 'YouTube channel'}`,
        })
        clearPendingYouTubeOAuthContext()
        navigate(context.returnTo, { replace: true })
      } catch (caughtError: any) {
        if (cancelled) return
        setError(caughtError?.message || 'The YouTube connection could not be completed. Please try again.')
      }
    }

    void finalizeCallback()

    return () => {
      cancelled = true
    }
  }, [navigate, refreshUser])

  return (
    <div
      style={{
        minHeight: '70vh',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        gap: '1rem',
        padding: '2rem 1rem',
      }}
      data-testid="cp-youtube-callback-page"
    >
      <Spinner size="large" />
      <div style={{ fontSize: '1rem', fontWeight: 600 }}>{error ? 'Connection interrupted' : 'Connecting YouTube'}</div>
      <div style={{ color: 'var(--colorNeutralForeground2)', textAlign: 'center', maxWidth: '40rem' }}>
        {error || status}
      </div>
    </div>
  )
}