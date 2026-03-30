import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { FluentProvider } from '@fluentui/react-components'
import { MemoryRouter, Routes, Route } from 'react-router-dom'

import { waooawLightTheme } from '../theme'
import YouTubeConnectionCallback from '../pages/YouTubeConnectionCallback'
import { AuthProvider } from '../context/AuthContext'
import {
  beginYouTubeOAuthFlow,
  clearPendingYouTubeOAuthContext,
  clearYouTubeOAuthResult,
  readYouTubeOAuthResult,
} from '../utils/youtubeOAuthFlow'

vi.mock('../services/youtubeConnections.service', () => ({
  finalizeYouTubeConnection: vi.fn(),
  attachYouTubeConnection: vi.fn(),
}))

describe('YouTubeConnectionCallback', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
    sessionStorage.clear()
    clearPendingYouTubeOAuthContext()
    clearYouTubeOAuthResult()
  })

  it('restores auth, finalizes the connection, and stores the resume result', async () => {
    const authModule = await import('../services/auth.service')
    const youtubeModule = await import('../services/youtubeConnections.service')

    vi.spyOn(authModule.authService, 'isAuthenticated').mockReturnValue(false)
    vi.spyOn(authModule.authService, 'silentRefresh').mockResolvedValue('restored-token')

    vi.spyOn(globalThis, 'fetch' as any).mockImplementation(async (input: any) => {
      const url = String(input)
      if (url.endsWith('/auth/me')) {
        return new Response(JSON.stringify({
          id: 'user-1',
          email: 'test@example.com',
          provider: 'google',
          created_at: '2026-03-30T00:00:00Z',
        }), { status: 200, headers: { 'Content-Type': 'application/json' } })
      }
      return new Response(JSON.stringify({ detail: 'not found' }), {
        status: 404,
        headers: { 'Content-Type': 'application/json' },
      })
    })

    vi.mocked(youtubeModule.finalizeYouTubeConnection).mockResolvedValue({
      id: 'cred-yt-1',
      customer_id: 'cust-1',
      platform_key: 'youtube',
      display_name: 'Clinic Channel',
      granted_scopes: ['youtube.upload'],
      verification_status: 'verified',
      connection_status: 'connected',
      created_at: '2026-03-30T00:00:00Z',
      updated_at: '2026-03-30T00:00:00Z',
    })

    beginYouTubeOAuthFlow({
      state: 'oauth-state-1',
      source: 'hire-setup',
      returnTo: '/hire/setup/SUB-1?step=3&focus=youtube',
      redirectUri: 'http://localhost/auth/youtube/callback',
      subscriptionId: 'SUB-1',
    })

    render(
      <FluentProvider theme={waooawLightTheme}>
        <MemoryRouter initialEntries={['/auth/youtube/callback?code=auth-code-1&state=oauth-state-1']}>
          <AuthProvider>
            <Routes>
              <Route path="/auth/youtube/callback" element={<YouTubeConnectionCallback />} />
              <Route path="/hire/setup/:subscriptionId" element={<div data-testid="resume-target">Resume target</div>} />
            </Routes>
          </AuthProvider>
        </MemoryRouter>
      </FluentProvider>
    )

    await waitFor(() => {
      expect(youtubeModule.finalizeYouTubeConnection).toHaveBeenCalledWith({
        state: 'oauth-state-1',
        code: 'auth-code-1',
        redirect_uri: 'http://localhost/auth/youtube/callback',
      })
    })

    await waitFor(() => {
      expect(screen.getByTestId('resume-target')).toBeInTheDocument()
    })

    const result = readYouTubeOAuthResult()
    expect(result?.source).toBe('hire-setup')
    expect(result?.connection.display_name).toBe('Clinic Channel')
    expect(result?.message).toContain('Connected Clinic Channel')
  })
})