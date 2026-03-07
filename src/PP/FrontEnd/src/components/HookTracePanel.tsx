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

function stageColor(stage: string): string {
  if (stage === 'pre_pump' || stage === 'post_pump') return '#00f2fe'
  if (stage === 'pre_processor' || stage === 'post_processor') return '#667eea'
  if (stage === 'pre_publish' || stage === 'post_publish') return '#f093fb'
  if (stage.includes('tool_use')) return '#f59e0b'
  return 'rgba(255,255,255,0.6)'
}

export default function HookTracePanel({ hiredAgentId }: HookTracePanelProps) {
  const [stageFilter, setStageFilter] = useState('All')
  const [resultFilter, setResultFilter] = useState('All')
  const { data, isLoading, error, refetch } = useHookTrace(hiredAgentId)

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
                <TableCell colSpan={5}>
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
