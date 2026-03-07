import { useEffect } from 'react'
import {
  Button,
  Card,
  CardHeader,
  Spinner,
  Table,
  TableBody,
  TableCell,
  TableHeader,
  TableHeaderCell,
  TableRow,
  Text,
} from '@fluentui/react-components'
import ApiErrorPanel from './ApiErrorPanel'
import { useSchedulerDiagnostics } from '../services/useSchedulerDiagnostics'

export interface SchedulerDiagnosticsPanelProps {
  hiredAgentId: string
  isAdmin: boolean
}

export function describeCron(expr: string): string {
  const parts = expr.split(' ')
  if (parts.length !== 5) return `Custom: ${expr}`
  const [min, hour, dom, month, dow] = parts
  if (dom === '*' && month === '*' && dow === '1-5' && min === '0')
    return `Every weekday at ${hour}:00`
  if (dom === '*' && month === '*' && dow === '*')
    return `Daily at ${hour}:${min.padStart(2, '0')}`
  return `Custom: ${expr}`
}

const LAG_HIGH_THRESHOLD = 3600

export default function SchedulerDiagnosticsPanel({
  hiredAgentId,
  isAdmin,
}: SchedulerDiagnosticsPanelProps) {
  const { data, isLoading, error, refetch } = useSchedulerDiagnostics(hiredAgentId)

  useEffect(() => {
    void refetch()
  }, [hiredAgentId, refetch])

  if (isLoading) {
    return (
      <div style={{ padding: 16 }}>
        <Spinner label="Loading scheduler diagnostics..." />
      </div>
    )
  }

  if (error) {
    return <ApiErrorPanel title="Scheduler diagnostics error" error={error} />
  }

  if (!data) return null

  const lagSeconds = data.lag_seconds ?? 0
  const lagHigh = lagSeconds > LAG_HIGH_THRESHOLD
  const trialPct =
    data.trial_task_limit && data.trial_task_limit > 0
      ? Math.min(100, ((data.tasks_used_today ?? 0) / data.trial_task_limit) * 100)
      : null

  return (
    <div>
      <Card style={{ marginBottom: 16 }}>
        <CardHeader
          header={<Text weight="semibold">Scheduler Diagnostics</Text>}
          description={<Text size={200}>{hiredAgentId}</Text>}
          action={
            <Button appearance="subtle" onClick={() => void refetch()} disabled={isLoading}>
              Refresh
            </Button>
          }
        />

        <div style={{ padding: 16 }}>
          <div style={{ marginBottom: 12 }}>
            <Text size={200} style={{ display: 'block', opacity: 0.7 }}>Cron expression</Text>
            <Text weight="semibold">{data.cron_expression}</Text>
            <Text size={200} style={{ display: 'block', marginTop: 2 }}>
              {describeCron(data.cron_expression)}
            </Text>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 12 }}>
            <div>
              <Text size={200} style={{ display: 'block', opacity: 0.7 }}>Next run</Text>
              <Text>{data.next_run ? new Date(data.next_run).toLocaleString() : '—'}</Text>
            </div>
            <div>
              <Text size={200} style={{ display: 'block', opacity: 0.7 }}>Last run</Text>
              <Text>{data.last_run ? new Date(data.last_run).toLocaleString() : '—'}</Text>
            </div>
          </div>

          <div style={{ marginBottom: 12 }}>
            <Text size={200} style={{ display: 'block', opacity: 0.7 }}>Lag</Text>
            <div
              aria-label={`lag gauge ${lagSeconds} seconds`}
              style={{
                height: 8,
                borderRadius: 4,
                background: 'rgba(255,255,255,0.1)',
                marginTop: 4,
                overflow: 'hidden',
              }}
            >
              <div
                style={{
                  height: '100%',
                  width: `${Math.min(100, (lagSeconds / (LAG_HIGH_THRESHOLD * 2)) * 100)}%`,
                  background: lagHigh ? '#ef4444' : '#10b981',
                  borderRadius: 4,
                  transition: 'width 0.3s',
                }}
              />
            </div>
            <Text size={200} style={{ marginTop: 4, display: 'block', color: lagHigh ? '#ef4444' : undefined }}>
              {lagSeconds}s {lagHigh ? '⚠ High lag' : ''}
            </Text>
          </div>

          {data.is_paused && (
            <div style={{ marginBottom: 12, padding: 8, background: 'rgba(245,158,11,0.1)', borderRadius: 6 }}>
              <Text style={{ color: '#f59e0b' }}>⏸ Scheduler is paused</Text>
            </div>
          )}

          {isAdmin && (
            <div style={{ display: 'flex', gap: 8, marginBottom: 12 }}>
              <Button appearance="secondary" size="small">
                Pause
              </Button>
              <Button appearance="secondary" size="small">
                Resume
              </Button>
            </div>
          )}

          {trialPct !== null && (
            <div style={{ marginBottom: 12 }}>
              <Text size={200} style={{ display: 'block', opacity: 0.7 }}>
                Trial usage ({data.tasks_used_today ?? 0} / {data.trial_task_limit})
              </Text>
              <div
                style={{
                  height: 8,
                  borderRadius: 4,
                  background: 'rgba(255,255,255,0.1)',
                  marginTop: 4,
                  overflow: 'hidden',
                }}
              >
                <div
                  style={{
                    height: '100%',
                    width: `${trialPct}%`,
                    background: trialPct >= 90 ? '#ef4444' : '#667eea',
                    borderRadius: 4,
                  }}
                />
              </div>
            </div>
          )}
        </div>
      </Card>

      {data.dlq_depth > 0 && (
        <Card>
          <CardHeader
            header={<Text weight="semibold">DLQ ({data.dlq_depth} entries)</Text>}
          />
          <Table>
            <TableHeader>
              <TableRow>
                <TableHeaderCell>Failed at</TableHeaderCell>
                <TableHeaderCell>Hook stage</TableHeaderCell>
                <TableHeaderCell>Error</TableHeaderCell>
              </TableRow>
            </TableHeader>
            <TableBody>
              {(data.dlq_entries || []).map((entry) => (
                <TableRow key={entry.dlq_id}>
                  <TableCell>
                    {entry.failed_at ? new Date(entry.failed_at).toLocaleString() : '—'}
                  </TableCell>
                  <TableCell>{entry.hook_stage}</TableCell>
                  <TableCell>{entry.error_message}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Card>
      )}
    </div>
  )
}
