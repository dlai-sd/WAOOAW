import { Spinner } from '@fluentui/react-components'
import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { useAuth } from '../context/AuthContext'
import { authService } from '../services/auth.service'
import { finalizeYouTubeConnection } from '../services/youtubeConnections.service'
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

    const buildCompletionMessage = (connection: any) => {
      const statusValue = String(connection?.connection_status || '').trim().toLowerCase()
      const label = connection?.display_name || 'Google account'
      const suggestedChannelName = connection?.suggested_channel_name || 'Empower'

      if (statusValue === 'connected_no_channel') {
        return `Connected ${label}. No YouTube channel exists on this account yet. Create a new channel named ${suggestedChannelName}, then test the connection again when you're ready.`
      }

      return `Connected ${connection.display_name || 'YouTube channel'}. Test the connection before saving it for the agent.`
    }

    const mapFinalizeError = (caughtError: any) => {
      const rawMessage = String(caughtError?.message || '').trim()
      if (rawMessage === 'youtube_channel_not_found') {
        return 'Google account connected, but no YouTube channel exists on this account yet. Create a channel named Empower and then test the connection again.'
      }
      return rawMessage || 'The YouTube connection could not be completed. Please try again.'
    }

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

        if (cancelled) return

        storeYouTubeOAuthResult({
          source: context.source,
          returnTo: context.returnTo,
          subscriptionId: context.subscriptionId,
          hiredInstanceId: context.hiredInstanceId,
          connection,
          message: buildCompletionMessage(connection),
        })
        clearPendingYouTubeOAuthContext()
        navigate(context.returnTo, { replace: true })
      } catch (caughtError: any) {
        if (cancelled) return
        setError(mapFinalizeError(caughtError))
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