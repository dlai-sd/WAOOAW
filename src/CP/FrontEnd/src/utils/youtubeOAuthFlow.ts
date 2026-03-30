import type { YouTubeConnection } from '../services/youtubeConnections.service'

const YOUTUBE_OAUTH_STATE_KEY = 'yt_oauth_state'
const YOUTUBE_OAUTH_CONTEXT_KEY = 'yt_oauth_context'
const YOUTUBE_OAUTH_RESULT_KEY = 'yt_oauth_result'
const YOUTUBE_CALLBACK_PATH = '/auth/youtube/callback'

export type YouTubeOAuthSource = 'hire-setup' | 'activation-wizard'

export type PendingYouTubeOAuthContext = {
  state: string
  source: YouTubeOAuthSource
  returnTo: string
  redirectUri: string
  subscriptionId?: string
  hiredInstanceId?: string
  skillId?: string
}

export type CompletedYouTubeOAuthResult = {
  source: YouTubeOAuthSource
  returnTo: string
  subscriptionId?: string
  hiredInstanceId?: string
  connection: YouTubeConnection
  message: string
}

function readJsonFromSessionStorage<T>(key: string): T | null {
  if (typeof window === 'undefined') return null

  try {
    const raw = window.sessionStorage.getItem(key)
    if (!raw) return null
    return JSON.parse(raw) as T
  } catch {
    return null
  }
}

function writeJsonToSessionStorage<T>(key: string, value: T): void {
  if (typeof window === 'undefined') return

  window.sessionStorage.setItem(key, JSON.stringify(value))
}

export function getYouTubeOAuthCallbackUri(): string {
  if (typeof window === 'undefined') return ''
  return `${window.location.origin}${YOUTUBE_CALLBACK_PATH}`
}

export function beginYouTubeOAuthFlow(context: PendingYouTubeOAuthContext): void {
  if (typeof window === 'undefined') return

  window.sessionStorage.setItem(YOUTUBE_OAUTH_STATE_KEY, context.state)
  writeJsonToSessionStorage(YOUTUBE_OAUTH_CONTEXT_KEY, context)
}

export function readPendingYouTubeOAuthContext(): PendingYouTubeOAuthContext | null {
  return readJsonFromSessionStorage<PendingYouTubeOAuthContext>(YOUTUBE_OAUTH_CONTEXT_KEY)
}

export function clearPendingYouTubeOAuthContext(): void {
  if (typeof window === 'undefined') return

  window.sessionStorage.removeItem(YOUTUBE_OAUTH_STATE_KEY)
  window.sessionStorage.removeItem(YOUTUBE_OAUTH_CONTEXT_KEY)
}

export function getStoredYouTubeOAuthState(): string | null {
  if (typeof window === 'undefined') return null
  return window.sessionStorage.getItem(YOUTUBE_OAUTH_STATE_KEY)
}

export function storeYouTubeOAuthResult(result: CompletedYouTubeOAuthResult): void {
  writeJsonToSessionStorage(YOUTUBE_OAUTH_RESULT_KEY, result)
}

export function readYouTubeOAuthResult(): CompletedYouTubeOAuthResult | null {
  return readJsonFromSessionStorage<CompletedYouTubeOAuthResult>(YOUTUBE_OAUTH_RESULT_KEY)
}

export function clearYouTubeOAuthResult(): void {
  if (typeof window === 'undefined') return
  window.sessionStorage.removeItem(YOUTUBE_OAUTH_RESULT_KEY)
}