import { useEffect, useState } from 'react'
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
import { useHookTrace } from '../services/useHookTrace'

export interface HookTracePanelProps {
  hiredAgentId: string
}

const STAGES = [
  'All',
  'pre_pump',
  'post_pump',
  'pre_processor',
  'post_processor',
  'pre_tool_use',
  'post_tool_use',
  'pre_publish',
  'post_publish',
]

const RESULTS = ['All', 'proceed', 'halt']

type HookSignal = {
  label: string
  message: string
  approvalId: string | null
}

function stageColor(stage: string): string {
  if (stage === 'pre_pump' || stage === 'post_pump') return '#00f2fe'
  if (stage === 'pre_processor' || stage === 'post_processor') return '#667eea'
  if (stage === 'pre_publish' || stage === 'post_publish') return '#f093fb'
  if (stage.includes('tool_use')) return '#f59e0b'
  return 'rgba(255,255,255,0.6)'
}

function extractApprovalId(payloadSummary: string): string | null {
  const match = String(payloadSummary || '').match(/APR-[A-Za-z0-9-]+/)
  return match ? match[0] : null
}

function classifyHookSignal(entry: { reason?: string; result?: string; payload_summary?: string }): HookSignal {
  const reason = String(entry.reason || '').trim().toLowerCase()
  const approvalId = extractApprovalId(String(entry.payload_summary || ''))
  if (reason === 'approval_required_for_youtube_publish') {
    return {
      label: 'Approval gate halted publish',
      message: 'PRE_PUBLISH halted because the exact deliverable still lacks approval.',
      approvalId,
    }
  }
  if (reason === 'credential_ref_required_for_youtube_publish') {
    return {
      label: 'Credential reference missing',
      message: 'The publish path halted after approval because no YouTube credential reference was available.',
      approvalId,
    }
  }
  if (reason === 'public_release_requires_explicit_customer_action') {
    return {
      label: 'Awaiting public release',
      message: 'The content can remain non-public, but public release still needs explicit customer action.',
      approvalId,
    }
  }
  if (String(entry.result || '').trim().toLowerCase() === 'halt') {
    return {
      label: 'Hook halted execution',
      message: reason || 'A hook blocked this runtime step before publish completed.',
      approvalId,
    }
  }
  return {
    label: 'Latest hook state',
    message: reason || 'No blocking hook state is present in the latest event.',
    approvalId,
  }
}

export default function HookTracePanel({ hiredAgentId }: HookTracePanelProps) {
  const [stageFilter, setStageFilter] = useState('All')
  const [resultFilter, setResultFilter] = useState('All')
  const { data, isLoading, error, refetch } = useHookTrace(hiredAgentId)
  const latestBlockingEvent = data.find((entry) => String(entry.result || '').trim().toLowerCase() !== 'proceed') || null
  const latestSignal = latestBlockingEvent ? classifyHookSignal(latestBlockingEvent) : null

  useEffect(() => {
    void refetch({
      stage: stageFilter !== 'All' ? stageFilter : undefined,
      result: resultFilter !== 'All' ? resultFilter : undefined,
    })
  }, [hiredAgentId, stageFilter, resultFilter, refetch])

  return (
    <div>
      <Card style={{ marginBottom: 16 }}>
        <CardHeader
          header={<Text weight="semibold">Hook Trace</Text>}
          description={<Text size={200}>{hiredAgentId}</Text>}
          action={
            <Button
              appearance="subtle"
              onClick={() =>
                void refetch({
                  stage: stageFilter !== 'All' ? stageFilter : undefined,
                  result: resultFilter !== 'All' ? resultFilter : undefined,
                })
              }
              disabled={isLoading}
            >
              Refresh
            </Button>
          }
        />

        <div style={{ padding: '0 16px 16px', display: 'flex', gap: 12 }}>
          <div>
            <Text size={200} style={{ display: 'block', marginBottom: 4 }}>Stage</Text>
            <select
              value={stageFilter}
              onChange={(e) => setStageFilter(e.target.value)}
              style={{ padding: '4px 8px', borderRadius: 4, background: '#18181b', color: '#fff', border: '1px solid rgba(255,255,255,0.2)' }}
            >
              {STAGES.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </div>
          <div>
            <Text size={200} style={{ display: 'block', marginBottom: 4 }}>Result</Text>
            <select
              value={resultFilter}
              onChange={(e) => setResultFilter(e.target.value)}
              style={{ padding: '4px 8px', borderRadius: 4, background: '#18181b', color: '#fff', border: '1px solid rgba(255,255,255,0.2)' }}
            >
              {RESULTS.map((r) => (
                <option key={r} value={r}>
                  {r}
                </option>
              ))}
            </select>
          </div>
        </div>

        {latestSignal && (
          <div style={{ padding: '0 16px 16px' }}>
            <Card appearance="outline" data-testid="pp-hook-trace-signal-card">
              <div style={{ padding: 12, display: 'grid', gap: 6 }}>
                <Text weight="semibold" data-testid="pp-hook-trace-signal-label">{latestSignal.label}</Text>
                <Text data-testid="pp-hook-trace-signal-message">{latestSignal.message}</Text>
                <Text size={200} data-testid="pp-hook-trace-approval-lineage">
                  Approval lineage: {latestSignal.approvalId || 'No approval id visible in the latest hook payload.'}
                </Text>
              </div>
            </Card>
          </div>
        )}
      </Card>

      {isLoading && (
        <div style={{ padding: 16 }}>
          <Spinner label="Loading hook trace..." />
        </div>
      )}

      {!!error && <ApiErrorPanel title="Hook trace error" error={error} />}

      {!isLoading && (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHeaderCell>Emitted at</TableHeaderCell>
              <TableHeaderCell>Stage</TableHeaderCell>
                <TableHeaderCell>Hook class</TableHeaderCell>
              <TableHeaderCell>Result</TableHeaderCell>
              <TableHeaderCell>Reason</TableHeaderCell>
              <TableHeaderCell>Payload summary</TableHeaderCell>
            </TableRow>
          </TableHeader>
          <TableBody>
            {data.map((entry) => (
              <TableRow
                key={entry.event_id}
                style={
                  entry.result === 'halt'
                    ? { background: '#ef444415' }
                    : undefined
                }
              >
                <TableCell>
                  {entry.emitted_at
                    ? new Date(entry.emitted_at).toLocaleString()
                    : '—'}
                </TableCell>
                <TableCell>
                  <span
                    style={{
                      display: 'inline-block',
                      padding: '2px 8px',
                      borderRadius: 12,
                      fontSize: 12,
                      background: `${stageColor(entry.stage)}22`,
                      color: stageColor(entry.stage),
                    }}
                  >
                    {entry.stage}
                  </span>
                </TableCell>
                <TableCell>{entry.hook_class || '—'}</TableCell>
                <TableCell>{entry.result}</TableCell>
                <TableCell>{entry.reason}</TableCell>
                <TableCell>
                  <Text size={200}>
                    {(entry.payload_summary || '').slice(0, 100)}
                  </Text>
                </TableCell>
              </TableRow>
            ))}
            {data.length === 0 && (
              <TableRow>
                <TableCell colSpan={6}>
                  <Text>No hook events found.</Text>
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      )}
    </div>
  )
}
