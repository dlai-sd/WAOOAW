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
const DB_UPDATES_TOKEN_STORAGE_KEY = 'pp_db_access_token'

function isTokenExpiredProblem(problem?: ApiProblemDetails): boolean {
  const type = (problem?.type || '').toLowerCase()
  const title = (problem?.title || '').toLowerCase()
  const detail = (problem?.detail || '').toLowerCase()
  return type.includes('token-expired') || title === 'token expired' || detail.includes('token has expired')
}

function markAuthExpiredAndBroadcast(): void {
  try {
    localStorage.removeItem('pp_access_token')
  } catch {
    // ignore
  }
  try {
    sessionStorage.removeItem(DB_UPDATES_TOKEN_STORAGE_KEY)
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
  const baseTrimmed = base.replace(/\/+$/, '')
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

function withQuery(path: string, query?: Record<string, string | number | boolean | undefined | null>): string {
  if (!query) return path
  const params = new URLSearchParams()
  for (const [key, value] of Object.entries(query)) {
    if (value === undefined || value === null) continue
    params.set(key, String(value))
  }
  const qs = params.toString()
  return qs ? `${path}?${qs}` : path
}

async function parseProblemDetails(res: Response): Promise<ApiProblemDetails | undefined> {
  const contentType = res.headers.get('content-type') || ''
  if (!contentType.includes('application/json')) return undefined

  try {
    const json = (await res.json()) as ApiProblemDetails
    return json
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
  const token = localStorage.getItem('pp_access_token')
  const debugTrace = getDebugTraceHeaderValue()

  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), opts.timeoutMs ?? DEFAULT_TIMEOUT_MS)

  const mergedSignal = opts.signal
    ? AbortSignal.any([opts.signal, controller.signal])
    : controller.signal

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

      if (res.status === 401 && isTokenExpiredProblem(problem)) {
        markAuthExpiredAndBroadcast()
      }

      throw new GatewayApiError(detail, {
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
  // Plant (proxied via PP /api/* passthrough)
  listReferenceAgents: () => gatewayRequestJson<unknown[]>('/v1/reference-agents'),

  runReferenceAgent: (agentId: string, payload: Record<string, unknown>) =>
    gatewayRequestJson<unknown>(`/v1/reference-agents/${encodeURIComponent(agentId)}/run`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    }),

  listUsageEvents: (query?: {
    customer_id?: string
    agent_id?: string
    correlation_id?: string
    event_type?: string
    since?: string
    until?: string
    limit?: number
  }) => gatewayRequestJson<unknown>(withQuery('/v1/usage-events', query)),

  aggregateUsageEvents: (query?: {
    bucket?: 'day' | 'month'
    customer_id?: string
    agent_id?: string
    correlation_id?: string
    event_type?: string
    since?: string
    until?: string
  }) => gatewayRequestJson<unknown>(withQuery('/v1/usage-events/aggregate', query)),

  listPolicyDenials: (query?: {
    correlation_id?: string
    customer_id?: string
    agent_id?: string
    limit?: number
  }) => gatewayRequestJson<unknown>(withQuery('/v1/audit/policy-denials', query)),

  fetchAgentSpecSchema: () => gatewayRequestJson<unknown>('/v1/agent-mold/schema/agent-spec'),

  validateAgentSpec: (payload: unknown) =>
    gatewayRequestJson<{ valid: boolean }>(
      '/v1/agent-mold/spec/validate',
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      }
    ),

  // PP Backend mounts Plant proxy routes under /api/pp
  // (config.apiBaseUrl already includes the /api prefix).
  listAgents: (query?: { industry?: string; job_role_id?: string; status?: string; limit?: number; offset?: number }) =>
    gatewayRequestJson<unknown[]>(withQuery('/pp/agents', query)),

  seedDefaultAgentData: () =>
    gatewayRequestJson<{ message: string; created: { skills: number; job_roles: number; agents: number } }>('/pp/agents/seed-defaults', {
      method: 'POST'
    }),

  // DB updates (dev-only)
  mintDbUpdatesToken: () =>
    gatewayRequestJson<{ access_token: string; token_type: string; expires_in: number; scope: string }>('/auth/db-updates-token', {
      method: 'POST'
    }),

  getDbConnectionInfo: (opts?: { bearerToken?: string }) =>
    gatewayRequestJson<{ environment: string; database_url: string }>('/pp/db/connection-info', {}, {
      headers: opts?.bearerToken ? { Authorization: `Bearer ${opts.bearerToken}` } : undefined
    }),
  executeDbSql: (
    payload: { sql: string; confirm: boolean; max_rows?: number; statement_timeout_ms?: number },
    opts?: { bearerToken?: string }
  ) =>
    gatewayRequestJson<unknown>(
      '/pp/db/execute',
      {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
      },
      {
        headers: opts?.bearerToken ? { Authorization: `Bearer ${opts.bearerToken}` } : undefined
      }
    ),

  // Genesis (skills)
  listSkills: (query?: { category?: string; limit?: number; offset?: number }) =>
    gatewayRequestJson<unknown[]>(withQuery('/pp/genesis/skills', query)),
  getSkill: (skillId: string) => gatewayRequestJson<unknown>(`/pp/genesis/skills/${encodeURIComponent(skillId)}`),
  createSkill: (payload: { name: string; description: string; category: string; governance_agent_id?: string }) =>
    gatewayRequestJson<unknown>('/pp/genesis/skills', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    }),
  certifySkill: (skillId: string, payload: Record<string, unknown> = {}) =>
    gatewayRequestJson<unknown>(`/pp/genesis/skills/${encodeURIComponent(skillId)}/certify`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    }),

  // Genesis (job roles)
  listJobRoles: (query?: { limit?: number; offset?: number }) =>
    gatewayRequestJson<unknown[]>(withQuery('/pp/genesis/job-roles', query)),
  getJobRole: (jobRoleId: string) => gatewayRequestJson<unknown>(`/pp/genesis/job-roles/${encodeURIComponent(jobRoleId)}`),
  createJobRole: (payload: {
    name: string
    description: string
    required_skills: string[]
    seniority_level?: string
    governance_agent_id?: string
  }) =>
    gatewayRequestJson<unknown>('/pp/genesis/job-roles', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    }),
  certifyJobRole: (jobRoleId: string, payload: Record<string, unknown> = {}) =>
    gatewayRequestJson<unknown>(`/pp/genesis/job-roles/${encodeURIComponent(jobRoleId)}/certify`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    }),

  // Audit
  runAudit: (query?: { entity_type?: string; entity_id?: string }) =>
    gatewayRequestJson<unknown>(withQuery('/pp/audit/run', query), { method: 'POST' }),
  detectTampering: (entityId: string) =>
    gatewayRequestJson<unknown>(`/pp/audit/tampering/${encodeURIComponent(entityId)}`),
  exportAuditJson: (query?: { entity_type?: string }) =>
    gatewayRequestJson<unknown>(withQuery('/pp/audit/export', { ...(query || {}), format: 'json' }))
}
