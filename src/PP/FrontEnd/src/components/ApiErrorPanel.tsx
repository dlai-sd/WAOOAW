import { Card, Text } from '@fluentui/react-components'
import { GatewayApiError } from '../services/gatewayApiClient'

export default function ApiErrorPanel({ title, error }: { title?: string; error: unknown }) {
  const heading = title || 'Error'

  if (error instanceof GatewayApiError) {
    const status = error.status
    const detail = error.problem?.detail || error.message
    const correlationId = error.correlationId || error.problem?.correlation_id
    const reason = (error.problem as any)?.reason as string | undefined
    const details = ((error.problem as any)?.details ?? (error.problem as any)?.violations) as unknown

    return (
      <Card style={{ padding: 16 }}>
        <Text weight="semibold">{heading}</Text>
        <div style={{ marginTop: 8 }}>
          <Text>{status ? `${status}: ${detail}` : detail}</Text>
        </div>
        {reason && (
          <div style={{ marginTop: 8 }}>
            <Text size={200}>Reason: {reason}</Text>
          </div>
        )}
        {correlationId && (
          <div style={{ marginTop: 8 }}>
            <Text size={200}>Correlation: {correlationId}</Text>
          </div>
        )}
        {details !== undefined && details !== null && (
          <div style={{ marginTop: 8 }}>
            <Text size={200} style={{ display: 'block', marginBottom: 6, opacity: 0.85 }}>Details</Text>
            <pre
              style={{
                margin: 0,
                padding: 12,
                background: 'rgba(255,255,255,0.04)',
                border: '1px solid rgba(255,255,255,0.08)',
                borderRadius: 8,
                overflowX: 'auto'
              }}
            >
              {JSON.stringify(details, null, 2)}
            </pre>
          </div>
        )}
      </Card>
    )
  }

  const message = error instanceof Error ? error.message : String(error)
  return (
    <Card style={{ padding: 16 }}>
      <Text weight="semibold">{heading}</Text>
      <div style={{ marginTop: 8 }}>
        <Text>{message}</Text>
      </div>
    </Card>
  )
}
