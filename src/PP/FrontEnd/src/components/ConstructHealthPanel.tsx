import { useEffect } from 'react'
import { Button, Card, CardHeader, Spinner, Text } from '@fluentui/react-components'
import ApiErrorPanel from './ApiErrorPanel'
import { useConstructHealth } from '../services/useConstructHealth'
import type { ConstructStatus } from '../services/useConstructHealth'

export interface ConstructHealthPanelProps {
  hiredAgentId: string
  isOpen: boolean
  onClose: () => void
}

const CONSTRUCT_CARDS = [
  { key: 'scheduler',  label: 'Scheduler',  icon: '⏱' },
  { key: 'pump',       label: 'Pump',        icon: '⬆' },
  { key: 'processor',  label: 'Processor',   icon: '⚙' },
  { key: 'connector',  label: 'Connector',   icon: '🔗' },
  { key: 'publisher',  label: 'Publisher',   icon: '📤' },
  { key: 'policy',     label: 'Policy',      icon: '🛡' },
] as const

function statusColor(status: string): string {
  if (status === 'healthy') return '#10b981'
  if (status === 'degraded') return '#f59e0b'
  return '#ef4444'
}

function maskSecretRef(secretRef: string): string {
  const last4 = secretRef.slice(-4)
  return `****${last4}`
}

function ConstructCard({
  label,
  icon,
  constructKey,
  construct,
}: {
  label: string
  icon: string
  constructKey: string
  construct: ConstructStatus & { secret_ref?: string }
}) {
  const status = construct.status ?? 'unknown'
  const color = statusColor(status)

  const metrics = Object.entries(construct)
    .filter(([k]) => k !== 'status' && k !== 'secret_ref')
    .slice(0, 3)

  return (
    <Card style={{ padding: 12 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
        <span style={{ fontSize: 18 }}>{icon}</span>
        <Text weight="semibold">{label}</Text>
        <span
          aria-label={`status: ${status}`}
          style={{
            display: 'inline-block',
            width: 10,
            height: 10,
            borderRadius: '50%',
            backgroundColor: color,
            marginLeft: 'auto',
          }}
        />
      </div>
      <Text size={200} style={{ display: 'block', marginBottom: 4 }}>
        {status}
      </Text>
      {metrics.map(([k, v]) => (
        <div key={k} style={{ marginTop: 2 }}>
          <Text size={200}>
            {k}: {String(v)}
          </Text>
        </div>
      ))}
      {constructKey === 'connector' && construct.secret_ref && (
        <div style={{ marginTop: 4 }}>
          <Text size={200}>secret_ref: {maskSecretRef(construct.secret_ref)}</Text>
        </div>
      )}
    </Card>
  )
}

export default function ConstructHealthPanel({
  hiredAgentId,
  isOpen,
  onClose,
}: ConstructHealthPanelProps) {
  const { data, isLoading, error, refetch } = useConstructHealth(hiredAgentId)

  useEffect(() => {
    if (isOpen && hiredAgentId) {
      void refetch()
    }
  }, [isOpen, hiredAgentId, refetch])

  if (!isOpen) return null

  return (
    <div
      role="dialog"
      aria-label="Construct health"
      style={{
        position: 'fixed',
        top: 0,
        right: 0,
        width: 480,
        height: '100vh',
        background: '#18181b',
        borderLeft: '1px solid rgba(255,255,255,0.1)',
        zIndex: 1000,
        overflowY: 'auto',
        padding: 24,
      }}
    >
      <Card style={{ marginBottom: 16 }}>
        <CardHeader
          header={<Text weight="semibold">Construct Health</Text>}
          description={<Text size={200}>{hiredAgentId}</Text>}
          action={
            <div style={{ display: 'flex', gap: 8 }}>
              <Button
                appearance="subtle"
                onClick={() => void refetch()}
                disabled={isLoading}
              >
                Refresh
              </Button>
              <Button appearance="subtle" onClick={onClose}>
                ✕
              </Button>
            </div>
          }
        />
      </Card>

      {isLoading && (
        <div style={{ padding: 16 }}>
          <Spinner label="Loading construct health..." />
        </div>
      )}

      {!!error && (
        <ApiErrorPanel title="Construct health error" error={error} />
      )}

      {!isLoading && data && (
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: '1fr 1fr',
            gap: 12,
          }}
        >
          {CONSTRUCT_CARDS.map(({ key, label, icon }) => {
            const construct = (data as unknown as Record<string, unknown>)[key] as
              | (ConstructStatus & { secret_ref?: string })
              | undefined
            if (!construct) return null
            return (
              <ConstructCard
                key={key}
                label={label}
                icon={icon}
                constructKey={key}
                construct={construct}
              />
            )
          })}
        </div>
      )}
    </div>
  )
}
