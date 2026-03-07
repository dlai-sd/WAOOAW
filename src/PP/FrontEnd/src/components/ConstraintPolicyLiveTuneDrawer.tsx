import { useState } from 'react'
import {
  Button,
  Card,
  CardHeader,
  Checkbox,
  Field,
  Input,
  Spinner,
  Text,
} from '@fluentui/react-components'
import ApiErrorPanel from './ApiErrorPanel'
import { gatewayRequestJson } from '../services/gatewayApiClient'

export interface ConstraintPolicy {
  approval_mode?: string
  max_tasks_per_day?: number
  max_position_size_inr?: number
  trial_task_limit?: number
  [key: string]: unknown
}

export interface ConstraintPolicyLiveTuneDrawerProps {
  agentSetupId: string
  currentPolicy: ConstraintPolicy
  isOpen: boolean
  onClose: () => void
  onSuccess: (updatedPolicy: ConstraintPolicy) => void
}

export default function ConstraintPolicyLiveTuneDrawer({
  agentSetupId,
  currentPolicy,
  isOpen,
  onClose,
  onSuccess,
}: ConstraintPolicyLiveTuneDrawerProps) {
  const [approvalMode, setApprovalMode] = useState<'manual' | 'auto'>(
    (currentPolicy.approval_mode as 'manual' | 'auto') ?? 'manual'
  )
  const [maxTasksPerDay, setMaxTasksPerDay] = useState<number>(
    currentPolicy.max_tasks_per_day ?? 10
  )
  const [auditAck, setAuditAck] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<unknown>(null)

  if (!isOpen) return null

  async function handleSubmit() {
    if (!auditAck) return
    setIsSubmitting(true)
    setError(null)
    try {
      const result = await gatewayRequestJson<{ agent_setup_id: string; constraint_policy: ConstraintPolicy }>(
        `/pp/agent-setups/${encodeURIComponent(agentSetupId)}/constraint-policy`,
        {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ approval_mode: approvalMode, max_tasks_per_day: maxTasksPerDay }),
        }
      )
      onSuccess(result.constraint_policy)
      onClose()
    } catch (e: unknown) {
      setError(e)
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div
      role="dialog"
      aria-label="Constraint policy live tune"
      style={{
        position: 'fixed',
        top: 0,
        right: 0,
        width: 400,
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
          header={<Text weight="semibold">Live Tune Policy</Text>}
          description={<Text size={200}>{agentSetupId}</Text>}
          action={
            <Button appearance="subtle" onClick={onClose} aria-label="Close">
              ✕
            </Button>
          }
        />
      </Card>

      {!!error && <ApiErrorPanel title="Policy update error" error={error} />}

      <Card>
        <div style={{ padding: 16, display: 'flex', flexDirection: 'column', gap: 16 }}>
          <div>
            <Text size={200} style={{ display: 'block', marginBottom: 8, opacity: 0.85 }}>
              Approval mode
            </Text>
            <div style={{ display: 'flex', gap: 8 }}>
              <Button
                appearance={approvalMode === 'manual' ? 'primary' : 'secondary'}
                size="small"
                onClick={() => setApprovalMode('manual')}
                aria-label="Set manual approval mode"
              >
                Manual
              </Button>
              <Button
                appearance={approvalMode === 'auto' ? 'primary' : 'secondary'}
                size="small"
                onClick={() => setApprovalMode('auto')}
                aria-label="Set auto approval mode"
              >
                Auto
              </Button>
            </div>
          </div>

          <Field label="Max tasks per day (0 = unlimited)">
            <Input
              type="number"
              value={String(maxTasksPerDay)}
              onChange={(_, d) => setMaxTasksPerDay(Number(d.value) || 0)}
            />
          </Field>

          <div
            style={{
              padding: 12,
              background: 'rgba(245,158,11,0.1)',
              borderRadius: 6,
              border: '1px solid rgba(245,158,11,0.3)',
            }}
          >
            <Checkbox
              label='I understand this change takes effect on the next goal run and is audit-logged.'
              checked={auditAck}
              onChange={(_, d) => setAuditAck(!!d.checked)}
            />
          </div>

          <Button
            appearance="primary"
            onClick={() => void handleSubmit()}
            disabled={!auditAck || isSubmitting}
          >
            {isSubmitting ? <Spinner size="tiny" /> : 'Apply Policy Change'}
          </Button>
        </div>
      </Card>
    </div>
  )
}
