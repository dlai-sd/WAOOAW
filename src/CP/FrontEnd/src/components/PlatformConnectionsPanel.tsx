// src/CP/FrontEnd/src/components/PlatformConnectionsPanel.tsx
//
// Lists all platform connections for a hired agent with status badges.
// Shows "Connect" buttons for unconnected required platforms.
// Accepts credentials through password fields — never logged after submit.
//
// PLANT-SKILLS-1 It3 E7-S1: extracted from SkillsPanel.tsx so it can be wired
// independently into the Configure tab of MyAgents.tsx.

import { useState, useEffect, useCallback, type FormEvent } from 'react'
import { Button, Badge, Input } from '@fluentui/react-components'
import { LoadingIndicator, FeedbackMessage } from './FeedbackIndicators'
import {
  listPlatformConnections,
  createPlatformConnection,
  deletePlatformConnection,
  type PlatformConnection,
} from '../services/platformConnections.service'

// ── Helpers ──────────────────────────────────────────────────────────────────

function statusColor(
  status: string | undefined
): 'success' | 'warning' | 'danger' | 'informative' {
  switch ((status ?? '').toLowerCase()) {
    case 'connected':
    case 'active':
      return 'success'
    case 'pending':
      return 'warning'
    case 'error':
    case 'failed':
      return 'danger'
    default:
      return 'informative'
  }
}

// ── ConnectForm ───────────────────────────────────────────────────────────────
// Inline form for a single platform. Clears credential state after successful
// submission so no plaintext tokens linger in React state.

interface ConnectFormProps {
  platformKey: string
  skillId: string
  hiredInstanceId: string
  onConnected: (conn: PlatformConnection) => void
  onCancel: () => void
}

function ConnectForm({ platformKey, skillId, hiredInstanceId, onConnected, onCancel }: ConnectFormProps) {
  const [apiKey, setApiKey] = useState('')
  const [apiSecret, setApiSecret] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [formError, setFormError] = useState<string | null>(null)

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    if (!apiKey.trim()) {
      setFormError('API key is required')
      return
    }
    setSubmitting(true)
    setFormError(null)
    try {
      const credentials: Record<string, string> = { api_key: apiKey }
      if (apiSecret) credentials['api_secret'] = apiSecret
      const conn = await createPlatformConnection(hiredInstanceId, {
        skill_id: skillId,
        platform_key: platformKey,
        credentials,
      })
      // Clear credentials from state immediately after successful save.
      setApiKey('')
      setApiSecret('')
      onConnected(conn)
    } catch (e: unknown) {
      setFormError(e instanceof Error ? e.message : 'Failed to connect platform')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      style={{
        marginTop: '0.5rem',
        padding: '0.75rem',
        borderRadius: '8px',
        background: 'var(--colorNeutralBackground2)',
        border: '1px solid var(--colorNeutralStroke2)',
      }}
    >
      <div style={{ fontWeight: 600, marginBottom: '0.5rem', fontSize: '0.9rem' }}>
        Connect {platformKey}
      </div>
      {formError && (
        <div style={{ color: 'var(--colorPaletteRedForeground1)', fontSize: '0.85rem', marginBottom: '0.5rem' }}>
          {formError}
        </div>
      )}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem', marginBottom: '0.5rem' }}>
        <Input
          placeholder="API Key *"
          type="password"
          value={apiKey}
          autoComplete="new-password"
          onChange={(_, data) => setApiKey(String(data.value || ''))}
          style={{ width: '100%' }}
        />
        <Input
          placeholder="API Secret (if required)"
          type="password"
          value={apiSecret}
          autoComplete="new-password"
          onChange={(_, data) => setApiSecret(String(data.value || ''))}
          style={{ width: '100%' }}
        />
      </div>
      <div style={{ display: 'flex', gap: '0.5rem' }}>
        <Button type="submit" appearance="primary" size="small" disabled={submitting}>
          {submitting ? 'Connecting…' : 'Connect'}
        </Button>
        <Button type="button" appearance="outline" size="small" onClick={onCancel} disabled={submitting}>
          Cancel
        </Button>
      </div>
    </form>
  )
}

// ── PlatformConnectionsPanel (main export) ───────────────────────────────────

export interface PlatformConnectionsPanelProps {
  hiredInstanceId: string
  /**
   * Platform keys the agent requires (from goal_schema.platform_connection_keys
   * aggregated across all skills). When provided, un-connected platforms show a
   * prominent "Connect" call-to-action.
   */
  requiredPlatformKeys?: string[]
  /**
   * Skill ID to attach when creating a new connection from the Configure tab.
   * Defaults to 'default' if not supplied (backend accepts this for agent-level
   * connections that are not tied to a specific skill).
   */
  defaultSkillId?: string
  readOnly?: boolean
}

export function PlatformConnectionsPanel({
  hiredInstanceId,
  requiredPlatformKeys = [],
  defaultSkillId = 'default',
  readOnly = false,
}: PlatformConnectionsPanelProps) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [connections, setConnections] = useState<PlatformConnection[]>([])
  /** Which platform key currently has its ConnectForm expanded. */
  const [connectingKey, setConnectingKey] = useState<string | null>(null)

  const loadConnections = useCallback(async () => {
    if (!hiredInstanceId) return
    setLoading(true)
    setError(null)
    try {
      const data = await listPlatformConnections(hiredInstanceId)
      setConnections(data)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to load connections')
    } finally {
      setLoading(false)
    }
  }, [hiredInstanceId])

  useEffect(() => {
    loadConnections()
  }, [loadConnections])

  const handleConnected = (conn: PlatformConnection) => {
    setConnections((prev) => [...prev, conn])
    setConnectingKey(null)
  }

  const handleDelete = async (connectionId: string) => {
    setError(null)
    try {
      await deletePlatformConnection(hiredInstanceId, connectionId)
      setConnections((prev) => prev.filter((c) => c.id !== connectionId))
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to remove connection')
    }
  }

  const connectedKeys = new Set(connections.map((c) => c.platform_key.toLowerCase()))

  /** Required platforms not yet connected. */
  const missingKeys = requiredPlatformKeys.filter(
    (k) => !connectedKeys.has(k.toLowerCase())
  )

  if (!hiredInstanceId) return null

  return (
    <div>
      {loading && <LoadingIndicator message="Loading connections…" size="small" />}
      {error && <FeedbackMessage intent="error" title="Error" message={error} />}

      {/* Existing connections list */}
      {!loading && connections.length === 0 && missingKeys.length === 0 && (
        <div style={{ opacity: 0.6, fontSize: '0.9rem' }}>No platforms connected yet.</div>
      )}

      {connections.map((conn) => (
        <div
          key={conn.id}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            marginBottom: '0.4rem',
            padding: '0.5rem 0.75rem',
            borderRadius: '8px',
            border: '1px solid var(--colorNeutralStroke2)',
          }}
        >
          <Badge
            appearance="tint"
            color={statusColor(conn.status)}
            size="small"
          >
            {conn.platform_key}
          </Badge>
          <span style={{ flex: 1, fontSize: '0.85rem', opacity: 0.8, textTransform: 'capitalize' }}>
            {conn.status ?? 'connected'}
          </span>
          {conn.connected_at && (
            <span style={{ fontSize: '0.75rem', opacity: 0.55 }}>
              {new Date(conn.connected_at).toLocaleDateString()}
            </span>
          )}
          {!readOnly && (
            <Button
              appearance="subtle"
              size="small"
              onClick={() => handleDelete(conn.id)}
            >
              Remove
            </Button>
          )}
        </div>
      ))}

      {/* Required but missing platforms */}
      {!readOnly && missingKeys.map((key) => (
        <div key={key}>
          {connectingKey === key ? (
            <ConnectForm
              platformKey={key}
              skillId={defaultSkillId}
              hiredInstanceId={hiredInstanceId}
              onConnected={handleConnected}
              onCancel={() => setConnectingKey(null)}
            />
          ) : (
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                marginBottom: '0.4rem',
                padding: '0.5rem 0.75rem',
                borderRadius: '8px',
                border: '1px dashed var(--colorNeutralStroke2)',
                opacity: 0.85,
              }}
            >
              <Badge appearance="tint" color="warning" size="small">
                {key}
              </Badge>
              <span style={{ flex: 1, fontSize: '0.85rem' }}>Not connected</span>
              <Button
                appearance="outline"
                size="small"
                onClick={() => setConnectingKey(key)}
              >
                Connect {key}
              </Button>
            </div>
          )}
        </div>
      ))}

      {/* Add arbitrary platform (not in required list) */}
      {!readOnly && (
        <div style={{ marginTop: '0.5rem' }}>
          {connectingKey === '__new__' ? (
            <ConnectForm
              platformKey="New platform"
              skillId={defaultSkillId}
              hiredInstanceId={hiredInstanceId}
              onConnected={handleConnected}
              onCancel={() => setConnectingKey(null)}
            />
          ) : (
            <Button
              appearance="subtle"
              size="small"
              onClick={() => setConnectingKey('__new__')}
            >
              + Add platform connection
            </Button>
          )}
        </div>
      )}
    </div>
  )
}

export default PlatformConnectionsPanel
