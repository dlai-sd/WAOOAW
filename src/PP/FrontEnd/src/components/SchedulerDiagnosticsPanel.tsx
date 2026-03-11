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

type SchedulerSignalTone = 'success' | 'warning' | 'danger' | 'informative'

function toneStyles(tone: SchedulerSignalTone): { background: string; color: string } {
  if (tone === 'success') return { background: 'rgba(16, 185, 129, 0.12)', color: '#10b981' }
  if (tone === 'warning') return { background: 'rgba(245, 158, 11, 0.12)', color: '#f59e0b' }
  if (tone === 'danger') return { background: 'rgba(239, 68, 68, 0.12)', color: '#ef4444' }
  return { background: 'rgba(0, 242, 254, 0.12)', color: '#00f2fe' }
}

function normalizeTimestamp(primary?: string | null, fallback?: string | null): string | null {
  return primary || fallback || null
}

function isPaused(data: { is_paused?: boolean; pause_state?: string | null }): boolean {
  if (typeof data.is_paused === 'boolean') return data.is_paused
  return String(data.pause_state || '').trim().toUpperCase() === 'PAUSED'
}

function classifySchedulerReason(rawReason?: string | null): {
  label: string
  message: string
  action: string
  tone: SchedulerSignalTone
} {
  const reason = String(rawReason || '').trim().toLowerCase()
  if (reason === 'approval_required_for_youtube_publish') {
    return {
      label: 'Missing approval',
      message: 'The scheduler refused to publish because the exact deliverable has no approval id yet.',
      action: 'Customer approval is still required before any YouTube publish can proceed.',
      tone: 'warning',
    }
  }
  if (reason === 'credential_ref_required_for_youtube_publish') {
    return {
      label: 'Missing YouTube credential',
      message: 'The draft is approved, but the YouTube credential reference is still missing.',
      action: 'Reconnect or verify the customer YouTube channel before retrying publish.',
      tone: 'danger',
    }
  }
  if (reason === 'public_release_requires_explicit_customer_action') {
    return {
      label: 'Awaiting public release',
      message: 'The content can stay non-public, but moving it to public still needs explicit customer action.',
      action: 'Keep the upload private or unlisted until the customer requests public release.',
      tone: 'informative',
    }
  }
  if (!reason) {
    return {
      label: 'No blocker recorded',
      message: 'No scheduler blocker or failure reason is present in the latest diagnostic payload.',
      action: 'Inspect hook trace if publish still did not happen.',
      tone: 'success',
    }
  }
  if (reason.includes('policy') || reason.includes('denied') || reason.includes('halt')) {
    return {
      label: 'Scheduler denial',
      message: `The scheduler or a policy hook halted publish with reason: ${reason}.`,
      action: 'Use hook trace and policy denials together to find the enforcing gate.',
      tone: 'danger',
    }
  }
  return {
    label: 'External publish failure',
    message: `The latest publish attempt failed with reason: ${reason}.`,
    action: 'Review the external publish adapter path and retry only after the upstream issue is clear.',
    tone: 'danger',
  }
}

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
  const nextRun = normalizeTimestamp(data.next_run_at, data.next_run)
  const lastRun = normalizeTimestamp(data.last_run_at, data.last_run)
  const paused = isPaused(data)
  const latestDlqReason = data.dlq_entries?.[0]?.error_message || data.latest_failure_reason || null
  const schedulerSignal = paused
    ? {
        label: 'Scheduler paused',
        message: 'This runtime is intentionally paused, so no publish work will move until it is resumed.',
        action: 'Resume the scheduler only after verifying the blocker that caused the pause.',
        tone: 'warning' as SchedulerSignalTone,
      }
    : classifySchedulerReason(latestDlqReason)
  const schedulerTone = toneStyles(schedulerSignal.tone)
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
              <Text>{nextRun ? new Date(nextRun).toLocaleString() : '—'}</Text>
            </div>
            <div>
              <Text size={200} style={{ display: 'block', opacity: 0.7 }}>Last run</Text>
              <Text>{lastRun ? new Date(lastRun).toLocaleString() : '—'}</Text>
            </div>
          </div>

          <div style={{ marginBottom: 12 }}>
            <Text size={200} style={{ display: 'block', opacity: 0.7 }}>Publish blocker summary</Text>
            <div style={{ marginTop: 8, padding: 12, borderRadius: 10, background: schedulerTone.background }}>
              <Text weight="semibold" data-testid="pp-scheduler-blocker-label" style={{ color: schedulerTone.color, display: 'block' }}>
                {schedulerSignal.label}
              </Text>
              <Text data-testid="pp-scheduler-blocker-message" style={{ display: 'block', marginTop: 6 }}>
                {schedulerSignal.message}
              </Text>
              <Text size={200} data-testid="pp-scheduler-blocker-action" style={{ display: 'block', marginTop: 6, opacity: 0.82 }}>
                Next action: {schedulerSignal.action}
              </Text>
              {(data.latest_approval_id || data.latest_deliverable_id) && (
                <Text size={200} data-testid="pp-scheduler-approval-lineage" style={{ display: 'block', marginTop: 6, opacity: 0.82 }}>
                  Approval lineage: {data.latest_approval_id || 'unknown approval'} tied to {data.latest_deliverable_id || 'the current deliverable'}.
                </Text>
              )}
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

          {paused && (
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
