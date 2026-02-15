import config from '../config/oauth.config'

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
const ACCESS_TOKEN_STORAGE_KEY = 'cp_access_token'
const LEGACY_ACCESS_TOKEN_STORAGE_KEY = 'access_token'

function isTokenExpiredProblem(problem?: ApiProblemDetails): boolean {
  const type = String(problem?.type || '').toLowerCase()
  const title = String(problem?.title || '').toLowerCase()
  const detail = String(problem?.detail || '').toLowerCase()
  return type.includes('token-expired') || title === 'token expired' || detail.includes('token has expired')
}

function markAuthExpiredAndBroadcast(): void {
  try {
    localStorage.removeItem(ACCESS_TOKEN_STORAGE_KEY)
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
  const current = (localStorage.getItem(ACCESS_TOKEN_STORAGE_KEY) || '').trim()
  if (current) return current

  // Backward compatibility: some older sessions used `access_token`.
  const legacy = (localStorage.getItem(LEGACY_ACCESS_TOKEN_STORAGE_KEY) || '').trim()
  if (!legacy) return null
  try {
    localStorage.setItem(ACCESS_TOKEN_STORAGE_KEY, legacy)
    localStorage.removeItem(LEGACY_ACCESS_TOKEN_STORAGE_KEY)
  } catch {
    // ignore
  }
  return legacy
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
  const token = getAccessToken()
  const debugTrace = getDebugTraceHeaderValue()

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
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...(init.headers || {}),
        ...(opts.headers || {})
      }
    })

    clearTimeout(timeoutId)

    if (!res.ok) {
      const problem = await parseProblemDetails(res)
      const detail = problem?.detail || `${res.status} ${res.statusText}`
      let message = detail

      // Fail-closed: any 401 means our browser token is not accepted by the API.
      // This covers rotated secrets, revoked sessions, and other invalid-token cases.
      if (res.status === 401) {
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
  } catch (e: any) {
    clearTimeout(timeoutId)
    if (e?.name === 'AbortError') {
      throw new GatewayApiError('Request timed out', { correlationId })
    }
    throw e
  }
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
