import { useEffect, useState } from 'react'
import { Card, CardHeader, Text, Body1, Button } from '@fluentui/react-components'
import ApiErrorPanel from '../components/ApiErrorPanel'
import { gatewayApiClient } from '../services/gatewayApiClient'
import { GatewayApiError } from '../services/gatewayApiClient'

const DB_UPDATES_TOKEN_STORAGE_KEY = 'pp_db_access_token'

function base64UrlDecodeToString(input: string): string {
  const normalized = input.replace(/-/g, '+').replace(/_/g, '/')
  const padded = normalized.padEnd(normalized.length + ((4 - (normalized.length % 4)) % 4), '=')
  return atob(padded)
}

function isJwtExpired(token: string, skewSeconds: number = 30): boolean {
  try {
    const parts = token.split('.')
    if (parts.length < 2) return false
    const payloadJson = base64UrlDecodeToString(parts[1])
    const payload = JSON.parse(payloadJson) as { exp?: number }
    if (!payload?.exp) return false
    const nowSeconds = Math.floor(Date.now() / 1000)
    return payload.exp <= nowSeconds + skewSeconds
  } catch {
    return false
  }
}

type ConnectionInfo = {
  environment: string
  database_url: string
}

export default function DbUpdates() {
  const [connectionInfo, setConnectionInfo] = useState<ConnectionInfo | null>(null)
  const [dbToken, setDbToken] = useState<string | null>(null)
  const [sql, setSql] = useState('')
  const [isLoading, setIsLoading] = useState(true)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<unknown | null>(null)
  const [result, setResult] = useState<unknown | null>(null)

  const canRunSql = Boolean(connectionInfo)
  const isFeatureDisabled = !isLoading && !connectionInfo && !error

  useEffect(() => {
    const abort = new AbortController()

    async function ensureDbToken(): Promise<string | null> {
      try {
        const existing = sessionStorage.getItem(DB_UPDATES_TOKEN_STORAGE_KEY)
        if (existing && !isJwtExpired(existing)) {
          setDbToken(existing)
          return existing
        }
      } catch {
        // ignore
      }

      try {
        const minted = await gatewayApiClient.mintDbUpdatesToken()
        const token = minted?.access_token
        if (token) {
          try {
            sessionStorage.setItem(DB_UPDATES_TOKEN_STORAGE_KEY, token)
          } catch {
            // ignore
          }
          setDbToken(token)
          return token
        }
        return null
      } catch (e) {
        // In demo/uat/prod the backend intentionally returns 404 when DB updates are disabled.
        if (e instanceof GatewayApiError && e.status === 404) {
          return null
        }
        throw e
      }
    }

    async function load() {
      setIsLoading(true)
      setError(null)
      try {
        const token = await ensureDbToken()
        if (!token) {
          setConnectionInfo(null)
          setError(null)
          return
        }

        const info = await gatewayApiClient.getDbConnectionInfo({ bearerToken: token })
        setConnectionInfo(info)
      } catch (e) {
        // In demo/uat/prod the backend intentionally returns 404 when DB updates are disabled.
        if (e instanceof GatewayApiError && e.status === 404) {
          setConnectionInfo(null)
          setError(null)
        } else {
          setError(e)
        }
      } finally {
        setIsLoading(false)
      }
    }

    void load()
    return () => abort.abort()
  }, [])

  const submit = async () => {
    setIsSubmitting(true)
    setError(null)
    setResult(null)
    try {
      const token = dbToken || sessionStorage.getItem(DB_UPDATES_TOKEN_STORAGE_KEY)
      if (!token || isJwtExpired(token)) {
        const minted = await gatewayApiClient.mintDbUpdatesToken()
        const newToken = minted?.access_token
        if (!newToken) {
          throw new Error('DB updates token unavailable')
        }
        try {
          sessionStorage.setItem(DB_UPDATES_TOKEN_STORAGE_KEY, newToken)
        } catch {
          // ignore
        }
        setDbToken(newToken)
        const res = await gatewayApiClient.executeDbSql({ sql, confirm: true }, { bearerToken: newToken })
        setResult(res)
        return
      }

      const res = await gatewayApiClient.executeDbSql({ sql, confirm: true }, { bearerToken: token })
      setResult(res)
    } catch (e) {
      setError(e)
    } finally {
      setIsSubmitting(false)
    }
  }

  const cancel = () => {
    setSql('')
    setResult(null)
    setError(null)
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <Text as="h1" size={900} weight="semibold">Database Schema and Data Management</Text>
        <Body1>Admin-only tools for controlled schema and data updates (dev-only)</Body1>
      </div>

      <Card>
        <CardHeader header={<Text weight="semibold">Database Connection</Text>} />
        <div style={{ padding: 16 }}>
          {isLoading ? (
            <Text>Loading…</Text>
          ) : connectionInfo ? (
            <>
              <Text size={200} style={{ display: 'block', marginBottom: 8, opacity: 0.85 }}>
                Environment: <strong>{connectionInfo.environment}</strong>
              </Text>
              <textarea
                value={connectionInfo.database_url}
                readOnly
                style={{ width: '100%', minHeight: 64, padding: 12, borderRadius: 8 }}
              />
              <Text size={200} style={{ display: 'block', marginTop: 8, opacity: 0.8 }}>
                Password is redacted for display.
              </Text>
            </>
          ) : isFeatureDisabled ? (
            <Text>DB Updates are not enabled for this environment.</Text>
          ) : (
            <ApiErrorPanel title="DB updates auth/error" error={error} />
          )}
        </div>
      </Card>

      <div style={{ height: 16 }} />

      <Card>
        <CardHeader header={<Text weight="semibold">Run SQL</Text>} />
        <div style={{ padding: 16, display: 'flex', flexDirection: 'column', gap: 12 }}>
          {canRunSql ? (
            <>
              <Text size={200} style={{ opacity: 0.9 }}>
                Submit a single SQL statement. Use with care.
              </Text>
              <textarea
                value={sql}
                onChange={e => setSql(e.target.value)}
                placeholder="e.g. SELECT * FROM agents LIMIT 10"
                style={{ width: '100%', minHeight: 160, padding: 12, borderRadius: 8, fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace' }}
              />

              <div style={{ display: 'flex', gap: 12 }}>
                <Button appearance="primary" onClick={submit} disabled={isSubmitting || !sql.trim()}>
                  {isSubmitting ? 'Submitting…' : 'Submit'}
                </Button>
                <Button appearance="secondary" onClick={cancel} disabled={isSubmitting}>
                  Cancel
                </Button>
              </div>

              {error ? <ApiErrorPanel title="DB update error" error={error} /> : null}

              {result !== null ? (
                <pre style={{ margin: 0, padding: 12, borderRadius: 8, background: 'rgba(255,255,255,0.06)', overflowX: 'auto' }}>
                  {JSON.stringify(result, null, 2)}
                </pre>
              ) : null}
            </>
          ) : isFeatureDisabled ? (
            <Text>DB Updates are not enabled for this environment.</Text>
          ) : (
            <ApiErrorPanel title="DB updates auth/error" error={error} />
          )}
        </div>
      </Card>
    </div>
  )
}
