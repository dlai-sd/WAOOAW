import config from '../config/oauth.config'
import { authService } from './auth.service'

export type ApiProblemDetails = {
  type?: string
  title?: string
  status?: number
  detail?: string
  instance?: string
  correlation_id?: string
  [key: string]: unknown
}

export class GatewayApiError extends Error {
  status?: number
  problem?: ApiProblemDetails
  correlationId?: string

  constructor(message: string, opts?: { status?: number; problem?: ApiProblemDetails; correlationId?: string }) {
    super(message)
    this.name = 'GatewayApiError'
    this.status = opts?.status
    this.problem = opts?.problem
    this.correlationId = opts?.correlationId
  }
}

type RequestOptions = {
  timeoutMs?: number
  headers?: Record<string, string>
  signal?: AbortSignal
}

const DEFAULT_TIMEOUT_MS = 30_000
const DEBUG_TRACE_STORAGE_KEY = 'waooaw_debug_trace'
const AUTH_CHANGED_EVENT = 'waooaw:auth-changed'
const AUTH_EXPIRED_FLAG = 'waooaw:auth-expired'

function normalizeProblemMessage(detail: unknown, fallback: string): string {
  if (typeof detail === 'string') {
    const normalized = detail.trim()
    return normalized || fallback
  }

  if (Array.isArray(detail)) {
    const messages = detail
      .map((entry) => normalizeProblemMessage(entry, ''))
      .map((entry) => entry.trim())
      .filter(Boolean)
    return messages.length > 0 ? messages.join(' | ') : fallback
  }

  if (detail && typeof detail === 'object') {
    const problemObject = detail as Record<string, unknown>
    const directMessage = [problemObject.detail, problemObject.message, problemObject.msg, problemObject.error]
      .map((entry) => (typeof entry === 'string' ? entry.trim() : ''))
      .find(Boolean)
    if (directMessage) return directMessage

    if (Array.isArray(problemObject.loc) || typeof problemObject.loc === 'string') {
      const location = Array.isArray(problemObject.loc)
        ? problemObject.loc.map((segment) => String(segment || '').trim()).filter(Boolean).join(' -> ')
        : String(problemObject.loc || '').trim()
      const msg = typeof problemObject.msg === 'string' ? problemObject.msg.trim() : ''
      if (location && msg) return `${location}: ${msg}`
      if (msg) return msg
    }

    try {
      const serialized = JSON.stringify(problemObject)
      if (serialized && serialized !== '{}') return serialized
    } catch {
      // Ignore serialization failures and fall through to the fallback.
    }
  }

  return fallback
}

function isTokenExpiredProblem(problem?: ApiProblemDetails): boolean {
  const type = String(problem?.type || '').toLowerCase()
  const title = String(problem?.title || '').toLowerCase()
  const detail = String(problem?.detail || '').toLowerCase()
  return type.includes('token-expired') || title === 'token expired' || detail.includes('token has expired')
}

function isUserInitializationProblem(problem?: ApiProblemDetails): boolean {
  const detail = String(problem?.detail || '').toLowerCase()
  return detail.includes('user not found')
}

function markAuthExpiredAndBroadcast(): void {
  // E1-S4: Clear in-memory token (localStorage no longer holds tokens)
  try {
    authService['accessToken' as keyof typeof authService]  // nominal reference; actual clear done via logout
  } catch {
    // ignore
  }
  try {
    sessionStorage.setItem(AUTH_EXPIRED_FLAG, '1')
  } catch {
    // ignore
  }
  try {
    window.dispatchEvent(new Event(AUTH_CHANGED_EVENT))
  } catch {
    // ignore
  }
}

function joinUrl(base: string, path: string): string {
  const baseTrimmed = base.replace(/\/+$/g, '')
  const pathTrimmed = path.replace(/^\/+/, '')
  return `${baseTrimmed}/${pathTrimmed}`
}

function generateCorrelationId(): string {
  try {
    return crypto.randomUUID()
  } catch {
    return `${Date.now()}-${Math.random().toString(16).slice(2)}`
  }
}

function getDebugTraceHeaderValue(): string | undefined {
  const raw = (localStorage.getItem(DEBUG_TRACE_STORAGE_KEY) || sessionStorage.getItem(DEBUG_TRACE_STORAGE_KEY) || '').trim()
  if (!raw) return undefined
  const normalized = raw.toLowerCase()
  if (['1', 'true', 'yes', 'on'].includes(normalized)) return '1'
  return undefined
}

function getAccessToken(): string | null {
  // E1-S4: Read from memory via authService — never from localStorage
  return authService.getAccessToken()
}

async function parseProblemDetails(res: Response): Promise<ApiProblemDetails | undefined> {
  const contentType = res.headers.get('content-type') || ''
  if (!contentType.includes('application/json')) return undefined

  try {
    return (await res.json()) as ApiProblemDetails
  } catch {
    return undefined
  }
}

export async function gatewayRequestJson<T>(
  path: string,
  init: RequestInit = {},
  opts: RequestOptions = {}
): Promise<T> {
  const url = joinUrl(config.apiBaseUrl, path)
  const correlationId = generateCorrelationId()
  const debugTrace = getDebugTraceHeaderValue()

  const doFetch = async (currentToken: string | null): Promise<Response> => {
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), opts.timeoutMs ?? DEFAULT_TIMEOUT_MS)
    const mergedSignal = opts.signal ? AbortSignal.any([opts.signal, controller.signal]) : controller.signal
    try {
      const res = await fetch(url, {
        ...init,
        signal: mergedSignal,
        headers: {
          Accept: 'application/json',
          'X-Correlation-ID': correlationId,
          ...(debugTrace ? { 'X-Debug-Trace': debugTrace } : {}),
          ...(currentToken ? { Authorization: `Bearer ${currentToken}` } : {}),
          ...(init.headers || {}),
          ...(opts.headers || {})
        }
      })
      clearTimeout(timeoutId)
      return res
    } catch (e: any) {
      clearTimeout(timeoutId)
      if (e?.name === 'AbortError') throw new GatewayApiError('Request timed out', { correlationId })
      throw e
    }
  }

  let res = await doFetch(getAccessToken())

  // E1-S4: on 401, attempt one silent refresh then retry
  if (res.status === 401) {
    const newToken = await authService.silentRefresh(true)
    if (newToken) {
      res = await doFetch(newToken)
    }
  }

  if (!res.ok) {
    const problem = await parseProblemDetails(res)
    const fallbackDetail = `${res.status} ${res.statusText}`
    const detail = normalizeProblemMessage(problem?.detail, fallbackDetail)
    let message = detail

    if (res.status === 401) {
      // Guard: "Customer not found" means the customer record was never created in the
      // Plant Backend — this is an account-setup problem, NOT an expired session.
      // Do NOT broadcast auth-expired (which would cause a silent login redirect).
      const lowerDetail = (problem?.detail || '').toLowerCase()
      if (lowerDetail.includes('customer not found')) {
        throw new GatewayApiError(
          'Your account setup is incomplete. Please contact support to activate your account.',
          {
            status: res.status,
            problem,
            correlationId: res.headers.get('x-correlation-id') || correlationId
          }
        )
      }
      if (isUserInitializationProblem(problem)) {
        throw new GatewayApiError(
          'Your account session is still initializing. Please retry in a moment.',
          {
            status: res.status,
            problem,
            correlationId: res.headers.get('x-correlation-id') || correlationId
          }
        )
      }
      markAuthExpiredAndBroadcast()
      message = isTokenExpiredProblem(problem)
        ? 'Session expired. Please sign in again.'
        : 'Please sign in again.'
    }

    throw new GatewayApiError(message, {
      status: res.status,
      problem,
      correlationId: res.headers.get('x-correlation-id') || correlationId
    })
  }

  return (await res.json()) as T
}

export const gatewayApiClient = {
  listAgents: (query?: Record<string, string | number | boolean | undefined | null>) => {
    const params = new URLSearchParams()
    for (const [key, value] of Object.entries(query || {})) {
      if (value === undefined || value === null) continue
      params.set(key, String(value))
    }
    const qs = params.toString()
    return gatewayRequestJson<unknown[]>(qs ? `/v1/agents?${qs}` : '/v1/agents')
  },

  getAgent: (agentId: string) => gatewayRequestJson<unknown>(`/v1/agents/${encodeURIComponent(agentId)}`),

  listSkills: (query?: Record<string, string | number | boolean | undefined | null>) => {
    const params = new URLSearchParams()
    for (const [key, value] of Object.entries(query || {})) {
      if (value === undefined || value === null) continue
      params.set(key, String(value))
    }
    const qs = params.toString()
    return gatewayRequestJson<unknown[]>(qs ? `/v1/genesis/skills?${qs}` : '/v1/genesis/skills')
  },

  getSkill: (skillId: string) => gatewayRequestJson<unknown>(`/v1/genesis/skills/${encodeURIComponent(skillId)}`),

  listJobRoles: (query?: Record<string, string | number | boolean | undefined | null>) => {
    const params = new URLSearchParams()
    for (const [key, value] of Object.entries(query || {})) {
      if (value === undefined || value === null) continue
      params.set(key, String(value))
    }
    const qs = params.toString()
    return gatewayRequestJson<unknown[]>(qs ? `/v1/genesis/job-roles?${qs}` : '/v1/genesis/job-roles')
  },

  getJobRole: (jobRoleId: string) => gatewayRequestJson<unknown>(`/v1/genesis/job-roles/${encodeURIComponent(jobRoleId)}`)
}
