import { useState, useCallback } from 'react'
import { gatewayRequestJson } from './gatewayApiClient'

const DEFAULT_AGENT_TYPE_VERSION = '1.0.0'

const INDUSTRY_SKILL_KEYS: Record<string, string[]> = {
  marketing: ['marketing.multichannel-post-v1'],
}

export interface ConstraintPolicy {
  approval_mode?: string
  max_tasks_per_day?: number
  max_position_size_inr?: number
  trial_task_limit?: number
  [key: string]: unknown
}

export interface AgentTypeSetupFormData {
  // Section 1: Identity
  agent_type: string
  display_name: string
  description: string
  industry: string
  // Section 2: ConstructBindings
  processor_class: string
  pump_class: string
  connector_class: string
  publisher_class: string
  // Section 3: ConstraintPolicy
  approval_mode: 'manual' | 'auto'
  max_tasks_per_day: number
  max_position_size_inr: number
  trial_task_limit: number
  // Section 4: Hook Checklist
  hooks: Record<string, boolean>
}

export interface ClassOption {
  value: string
  label: string
}

export const HOOK_LIST = [
  { key: 'AuditHook', label: 'Audit Hook', description: 'Records every goal run event for compliance.' },
  { key: 'BudgetGuardHook', label: 'Budget Guard Hook', description: 'Halts runs that would exceed spending limits.' },
  { key: 'ContentSafetyHook', label: 'Content Safety Hook', description: 'Screens content against safety policy before publishing.' },
  { key: 'ApprovalGateHook', label: 'Approval Gate Hook', description: 'Pauses runs requiring manual approval before proceeding.' },
  { key: 'RateLimitHook', label: 'Rate Limit Hook', description: 'Enforces per-day task caps defined in ConstraintPolicy.' },
]

export function useAgentTypeSetup() {
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<unknown>(null)
  const [savedAt, setSavedAt] = useState<string | null>(null)

  const [processorOptions, setProcessorOptions] = useState<ClassOption[]>([])
  const [pumpOptions, setPumpOptions] = useState<ClassOption[]>([])
  const [isLoadingOptions, setIsLoadingOptions] = useState(false)

  const loadClassOptions = useCallback(async () => {
    setIsLoadingOptions(true)
    setError(null)
    try {
      const [processors, pumps] = await Promise.all([
        gatewayRequestJson<ClassOption[]>('/v1/agent-mold/processors').catch(() => [] as ClassOption[]),
        gatewayRequestJson<ClassOption[]>('/v1/agent-mold/pumps').catch(() => [] as ClassOption[]),
      ])
      setProcessorOptions(processors)
      setPumpOptions(pumps)
    } catch (e: unknown) {
      setError(e)
    } finally {
      setIsLoadingOptions(false)
    }
  }, [])

  const submit = useCallback(async (
    form: AgentTypeSetupFormData,
    agentSetupId?: string
  ): Promise<unknown> => {
    setIsSubmitting(true)
    setError(null)
    setSavedAt(null)
    try {
      const agentTypeId = form.agent_type.trim() || agentSetupId?.trim()
      if (!agentTypeId) {
        throw new Error('agent_type is required to publish to Plant')
      }

      const payload = {
        agent_type_id: agentTypeId,
        version: DEFAULT_AGENT_TYPE_VERSION,
        required_skill_keys: INDUSTRY_SKILL_KEYS[form.industry] ?? [],
        config_schema: {
          fields: [
            {
              key: 'display_name',
              label: 'Display name',
              type: 'text',
              required: true,
              description: form.display_name,
            },
            {
              key: 'description',
              label: 'Description',
              type: 'text',
              required: false,
              description: form.description || 'Base agent contract draft authored in PP.',
            },
            {
              key: 'industry',
              label: 'Industry',
              type: 'enum',
              required: true,
              description: `PP authoring default industry: ${form.industry}`,
              options: ['marketing', 'education', 'sales'],
            },
          ],
        },
        goal_templates: [],
        enforcement_defaults: {
          approval_required: form.approval_mode !== 'auto',
          deterministic: false,
        },
      }

      const result = await gatewayRequestJson<unknown>(`/pp/agent-types/${encodeURIComponent(agentTypeId)}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })

      setSavedAt(new Date().toISOString())
      return result
    } catch (e: unknown) {
      setError(e)
      throw e
    } finally {
      setIsSubmitting(false)
    }
  }, [])

  return {
    isSubmitting,
    error,
    savedAt,
    processorOptions,
    pumpOptions,
    isLoadingOptions,
    loadClassOptions,
    submit,
  }
}
