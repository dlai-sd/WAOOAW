import { Card, Text } from '@fluentui/react-components'
import { GatewayApiError } from '../services/gatewayApiClient'

export default function ApiErrorPanel({ title, error }: { title?: string; error: unknown }) {
  const heading = title || 'Error'

  if (error instanceof GatewayApiError) {
    const status = error.status
    const detail = error.problem?.detail || error.message
    const correlationId = error.correlationId || error.problem?.correlation_id

    return (
      <Card style={{ padding: 16 }}>
        <Text weight="semibold">{heading}</Text>
        <div style={{ marginTop: 8 }}>
          <Text>{status ? `${status}: ${detail}` : detail}</Text>
        </div>
        {correlationId && (
          <div style={{ marginTop: 8 }}>
            <Text size={200}>Correlation: {correlationId}</Text>
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
