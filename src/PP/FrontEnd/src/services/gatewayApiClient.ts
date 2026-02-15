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
const RETRY_BACKOFF_DELAYS_MS = [1_000, 2_000, 4_000] as const
const RETRYABLE_HTTP_STATUS = new Set([429, 500, 502, 503, 504])
const DEBUG_TRACE_STORAGE_KEY = 'waooaw_debug_trace'
const AUTH_CHANGED_EVENT = 'waooaw:auth-changed'
const AUTH_EXPIRED_FLAG = 'waooaw:auth-expired'
const DB_UPDATES_TOKEN_STORAGE_KEY = 'pp_db_access_token'

function shouldRetryStatus(status: number): boolean {
  return RETRYABLE_HTTP_STATUS.has(status)
}

function isRetryableFetchError(err: unknown): boolean {
  const e = err as any
  // Fetch network errors often surface as TypeError.
  return e?.name === 'AbortError' || e?.name === 'TypeError'
}

function looksLikeStackTrace(value: string): boolean {
  const raw = (value || '').toLowerCase()
  return raw.includes('traceback') || raw.includes('\n  file "') || raw.includes('stack trace')
}

function sanitizeUserMessage(message: string): string {
  const trimmed = (message || '').trim()
  if (!trimmed) return 'Request failed. Please try again.'
  if (looksLikeStackTrace(trimmed)) return 'Request failed. Please try again.'
  return trimmed
}

async function sleep(ms: number, signal?: AbortSignal): Promise<void> {
  if (ms <= 0) return
  await new Promise<void>((resolve, reject) => {
    const timeoutId = setTimeout(resolve, ms)
    const onAbort = () => {
      clearTimeout(timeoutId)
      reject(new DOMException('Aborted', 'AbortError'))
    }

    if (!signal) return
    if (signal.aborted) {
      onAbort()
      return
    }
    signal.addEventListener('abort', onAbort, { once: true })
  })
}

function isTokenExpiredProblem(problem?: ApiProblemDetails): boolean {
  const type = String(problem?.type || '').toLowerCase()
  const title = String(problem?.title || '').toLowerCase()
  const detail = String(problem?.detail || '').toLowerCase()
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

  for (let attempt = 0; attempt <= RETRY_BACKOFF_DELAYS_MS.length; attempt += 1) {
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

      if (res.ok) {
        return (await res.json()) as T
      }

      const problem = await parseProblemDetails(res)

      // Never retry 401s: browser tokens are invalid; mark auth-expired.
      if (res.status === 401) {
        if (isTokenExpiredProblem(problem)) {
          markAuthExpiredAndBroadcast()
        }
        const detail = problem?.detail || `${res.status} ${res.statusText}`
        throw new GatewayApiError(sanitizeUserMessage(detail), {
          status: res.status,
          problem,
          correlationId: res.headers.get('x-correlation-id') || correlationId
        })
      }

      const shouldRetry = shouldRetryStatus(res.status) && attempt < RETRY_BACKOFF_DELAYS_MS.length
      if (shouldRetry) {
        await sleep(RETRY_BACKOFF_DELAYS_MS[attempt], opts.signal)
        continue
      }

      const detail = problem?.detail || `${res.status} ${res.statusText}`
      throw new GatewayApiError(sanitizeUserMessage(detail), {
        status: res.status,
        problem,
        correlationId: res.headers.get('x-correlation-id') || correlationId
      })
    } catch (e: any) {
      clearTimeout(timeoutId)

      const shouldRetry = isRetryableFetchError(e) && attempt < RETRY_BACKOFF_DELAYS_MS.length
      if (shouldRetry) {
        await sleep(RETRY_BACKOFF_DELAYS_MS[attempt], opts.signal)
        continue
      }

      if (e?.name === 'AbortError') {
        throw new GatewayApiError('Request timed out', { correlationId })
      }
      throw e
    }
  }

  // Unreachable, but keeps TS happy.
  throw new GatewayApiError('Request failed', { correlationId })
}

export const gatewayApiClient = {
  // Plant (proxied via PP /api/* passthrough)
  listReferenceAgents: () => gatewayRequestJson<unknown[]>('/v1/reference-agents'),

  listSubscriptionsByCustomer: (customerId: string) =>
    gatewayRequestJson<unknown[]>(`/v1/payments/subscriptions/by-customer/${encodeURIComponent(customerId)}`),

  getHiredAgentBySubscription: (subscriptionId: string, query: { customer_id: string; as_of?: string }) =>
    gatewayRequestJson<unknown>(withQuery(`/v1/hired-agents/by-subscription/${encodeURIComponent(subscriptionId)}`, query)),

  listGoalsForHiredInstance: (hiredInstanceId: string, query: { customer_id: string; as_of?: string }) =>
    gatewayRequestJson<unknown>(withQuery(`/v1/hired-agents/${encodeURIComponent(hiredInstanceId)}/goals`, query)),

  listDeliverablesForHiredInstance: (hiredInstanceId: string, query: { customer_id: string; as_of?: string }) =>
    gatewayRequestJson<unknown>(withQuery(`/v1/hired-agents/${encodeURIComponent(hiredInstanceId)}/deliverables`, query)),

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

  // Agent type definitions (PP-managed, stored in Plant)
  listAgentTypeDefinitions: () => gatewayRequestJson<any[]>('/pp/agent-types'),

  getAgentTypeDefinition: (agentTypeId: string) =>
    gatewayRequestJson<any>(`/pp/agent-types/${encodeURIComponent(agentTypeId)}`),

  publishAgentTypeDefinition: (agentTypeId: string, payload: any) =>
    gatewayRequestJson<any>(`/pp/agent-types/${encodeURIComponent(agentTypeId)}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    }),

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

  // PP agent setup (post-hire configuration)
  listAgentSetups: (query?: { customer_id?: string; agent_id?: string; limit?: number }) =>
    gatewayRequestJson<{ count: number; setups: any[] }>(withQuery('/pp/agent-setups', query)),

  upsertAgentSetup: (payload: {
    customer_id: string
    agent_id: string
    channels?: string[]
    correlation_id?: string
    posting_identity?: string | null
    credential_refs?: Record<string, string>
  }) =>
    gatewayRequestJson<any>('/pp/agent-setups', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    }),

  // PP exchange credentials (admin-only)
  upsertExchangeCredential: (payload: {
    customer_id: string
    exchange_provider: string
    api_key: string
    api_secret: string
    exchange_account_id?: string | null
  }) =>
    gatewayRequestJson<{
      exchange_account_id: string
      customer_id: string
      exchange_provider: string
      created_at: string
      updated_at: string
    }>('/pp/exchange-credentials', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    }),

  listExchangeCredentials: (query?: { customer_id?: string; limit?: number }) =>
    gatewayRequestJson<{ count: number; credentials: any[] }>(withQuery('/pp/exchange-credentials', query)),

  getExchangeCredentialBundle: (exchangeAccountId: string) =>
    gatewayRequestJson<{ exchange_account_id: string; exchange_provider: string; api_key: string; api_secret: string }>(
      `/pp/exchange-credentials/${encodeURIComponent(exchangeAccountId)}`
    ),

  // PP approvals (admin-only)
  mintApproval: (payload: {
    customer_id: string
    agent_id: string
    action: string
    correlation_id?: string | null
    purpose?: string | null
    notes?: string | null
    expires_in_seconds?: number | null
    approval_id?: string | null
  }) =>
    gatewayRequestJson<{
      approval_id: string
      customer_id: string
      agent_id: string
      action: string
      requested_by: string
      correlation_id?: string | null
      purpose?: string | null
      notes?: string | null
      created_at: string
      expires_at?: string | null
    }>('/pp/approvals', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    }),

  listApprovals: (query?: { customer_id?: string; agent_id?: string; action?: string; correlation_id?: string; limit?: number }) =>
    gatewayRequestJson<{ count: number; approvals: any[] }>(withQuery('/pp/approvals', query)),

  // Marketing draft review (Plant proxied via PP)
  listMarketingDraftBatches: (query?: { agent_id?: string; customer_id?: string; status?: string; limit?: number }) =>
    gatewayRequestJson<any[]>(withQuery('/v1/marketing/draft-batches', query)),

  approveMarketingDraftPost: (postId: string, payload?: { approval_id?: string }) =>
    gatewayRequestJson<{ post_id: string; review_status: string; approval_id: string }>(
      `/v1/marketing/draft-posts/${encodeURIComponent(postId)}/approve`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload || {})
      }
    ),

  scheduleMarketingDraftPost: (postId: string, payload: { scheduled_at: string; approval_id?: string }) =>
    gatewayRequestJson<{ post_id: string; execution_status: string; scheduled_at: string }>(
      `/v1/marketing/draft-posts/${encodeURIComponent(postId)}/schedule`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      }
    ),
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
  createSkill: (payload: {
    name: string
    description: string
    category: string
    skill_key?: string
    governance_agent_id?: string
  }) =>
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
