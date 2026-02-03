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
  // PP Backend mounts Plant proxy routes under /api/pp
  // (config.apiBaseUrl already includes the /api prefix).
  listAgents: (query?: { industry?: string; job_role_id?: string; status?: string; limit?: number; offset?: number }) =>
    gatewayRequestJson<unknown[]>(withQuery('/pp/agents', query)),

  seedDefaultAgentData: () =>
    gatewayRequestJson<{ message: string; created: { skills: number; job_roles: number; agents: number } }>('/pp/agents/seed-defaults', {
      method: 'POST'
    }),

  // DB updates (dev-only)
  getDbConnectionInfo: () =>
    gatewayRequestJson<{ environment: string; database_url: string }>('/pp/db/connection-info'),
  executeDbSql: (payload: { sql: string; confirm: boolean; max_rows?: number; statement_timeout_ms?: number }) =>
    gatewayRequestJson<unknown>('/pp/db/execute', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    }),

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
