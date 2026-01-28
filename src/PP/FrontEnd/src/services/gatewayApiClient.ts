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
  listAgents: () => gatewayRequestJson<unknown[]>('/v1/agents')
}
