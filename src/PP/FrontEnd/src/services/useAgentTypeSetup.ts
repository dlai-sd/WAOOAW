import { useState, useCallback } from 'react'
import { gatewayRequestJson } from './gatewayApiClient'

export type DraftStatus = 'draft' | 'in_review' | 'changes_requested' | 'approved'
export type SectionState = 'missing' | 'ready' | 'needs_review'

export interface ConstraintPolicy {
  approval_mode?: string
  max_tasks_per_day?: number
  max_position_size_inr?: number
  trial_task_limit?: number
  [key: string]: unknown
}

export interface AgentTypeSetupFormData {
  agent_type: string
  display_name: string
  description: string
  industry: string
  target_customer: string
  processor_class: string
  pump_class: string
  connector_class: string
  publisher_class: string
  approval_mode: 'manual' | 'auto'
  max_tasks_per_day: number
  max_position_size_inr: number
  trial_task_limit: number
  primary_outcomes: string
  deliverable_commitments: string
  optional_extensions: string
  handoff_notes: string
  hooks: Record<string, boolean>
}

export interface ReviewerComment {
  section_key: string
  comment: string
  severity: 'info' | 'changes_requested'
  reviewer_id?: string | null
  reviewer_name?: string | null
  created_at?: string | null
}

export interface AgentAuthoringDraft {
  draft_id: string
  candidate_agent_type_id: string
  candidate_agent_label: string
  contract_payload: Record<string, any>
  section_states: Record<string, SectionState>
  constraint_policy: ConstraintPolicy
  reviewer_comments: ReviewerComment[]
  status: DraftStatus
  reviewer_id?: string | null
  reviewer_name?: string | null
  submitted_at?: string | null
  reviewed_at?: string | null
  created_at: string
  updated_at: string
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

const DEFAULT_HOOKS: Record<string, boolean> = Object.fromEntries(
  HOOK_LIST.map(hook => [hook.key, hook.key === 'AuditHook'])
)

export const DEFAULT_AGENT_TYPE_SETUP_FORM: AgentTypeSetupFormData = {
  agent_type: 'marketing.digital_marketing_agent',
  display_name: 'Digital Marketing Agent',
  description: 'Runs approved digital marketing work with a clear human review path.',
  industry: 'marketing',
  target_customer: 'Growth-stage business that needs a dependable digital marketing operator.',
  processor_class: 'ContentProcessor',
  pump_class: 'SocialMediaPump',
  connector_class: '',
  publisher_class: '',
  approval_mode: 'manual',
  max_tasks_per_day: 10,
  max_position_size_inr: 0,
  trial_task_limit: 10,
  primary_outcomes: '',
  deliverable_commitments: '',
  optional_extensions: '',
  handoff_notes: '',
  hooks: { ...DEFAULT_HOOKS },
}

function getSectionState(requiredChecks: boolean[]): SectionState {
  if (requiredChecks.every(Boolean)) return 'ready'
  if (requiredChecks.some(Boolean)) return 'needs_review'
  return 'missing'
}

export function getSectionStates(form: AgentTypeSetupFormData): Record<string, SectionState> {
  return {
    define_agent: getSectionState([
      !!form.agent_type.trim(),
      !!form.display_name.trim(),
      !!form.description.trim(),
      !!form.target_customer.trim(),
    ]),
    operating_contract: getSectionState([
      !!form.processor_class.trim(),
      !!form.pump_class.trim(),
      form.max_tasks_per_day > 0,
      form.trial_task_limit > 0,
    ]),
    deliverables: getSectionState([
      !!form.primary_outcomes.trim(),
      !!form.deliverable_commitments.trim(),
    ]),
    governance: getSectionState([
      !!form.handoff_notes.trim(),
      !!form.hooks.AuditHook,
    ]),
  }
}

function toDraftPayload(form: AgentTypeSetupFormData, draftId?: string) {
  const enabledHooks = Object.entries(form.hooks)
    .filter(([, enabled]) => enabled)
    .map(([hookKey]) => hookKey)

  return {
    draft_id: draftId,
    candidate_agent_type_id: form.agent_type.trim(),
    candidate_agent_label: form.display_name.trim() || 'Digital Marketing Agent',
    contract_payload: {
      identity: {
        display_name: form.display_name,
        description: form.description,
        industry: form.industry,
        target_customer: form.target_customer,
      },
      operating_contract: {
        processor_class: form.processor_class,
        pump_class: form.pump_class,
        connector_class: form.connector_class,
        publisher_class: form.publisher_class,
        approval_mode: form.approval_mode,
        max_tasks_per_day: form.max_tasks_per_day,
        max_position_size_inr: form.max_position_size_inr,
        trial_task_limit: form.trial_task_limit,
      },
      deliverables: {
        primary_outcomes: form.primary_outcomes,
        deliverable_commitments: form.deliverable_commitments,
        optional_extensions: form.optional_extensions,
      },
      governance: {
        handoff_notes: form.handoff_notes,
        hooks: form.hooks,
      },
    },
    section_states: getSectionStates(form),
    constraint_policy: {
      approval_mode: form.approval_mode,
      max_tasks_per_day: form.max_tasks_per_day,
      max_position_size_inr: form.max_position_size_inr,
      trial_task_limit: form.trial_task_limit,
      hooks_enabled: enabledHooks,
    },
  }
}

function draftToFormData(draft: AgentAuthoringDraft): AgentTypeSetupFormData {
  const identity = (draft.contract_payload.identity || {}) as Record<string, any>
  const operatingContract = (draft.contract_payload.operating_contract || {}) as Record<string, any>
  const deliverables = (draft.contract_payload.deliverables || {}) as Record<string, any>
  const governance = (draft.contract_payload.governance || {}) as Record<string, any>

  return {
    agent_type: draft.candidate_agent_type_id || DEFAULT_AGENT_TYPE_SETUP_FORM.agent_type,
    display_name: draft.candidate_agent_label || identity.display_name || DEFAULT_AGENT_TYPE_SETUP_FORM.display_name,
    description: identity.description || DEFAULT_AGENT_TYPE_SETUP_FORM.description,
    industry: identity.industry || DEFAULT_AGENT_TYPE_SETUP_FORM.industry,
    target_customer: identity.target_customer || '',
    processor_class: operatingContract.processor_class || '',
    pump_class: operatingContract.pump_class || '',
    connector_class: operatingContract.connector_class || '',
    publisher_class: operatingContract.publisher_class || '',
    approval_mode: operatingContract.approval_mode === 'auto' ? 'auto' : 'manual',
    max_tasks_per_day: Number(operatingContract.max_tasks_per_day || 0),
    max_position_size_inr: Number(operatingContract.max_position_size_inr || 0),
    trial_task_limit: Number(operatingContract.trial_task_limit || 0),
    primary_outcomes: deliverables.primary_outcomes || '',
    deliverable_commitments: deliverables.deliverable_commitments || '',
    optional_extensions: deliverables.optional_extensions || '',
    handoff_notes: governance.handoff_notes || '',
    hooks: { ...DEFAULT_HOOKS, ...(governance.hooks || {}) },
  }
}

export function useAgentTypeSetup() {
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<unknown>(null)
  const [savedAt, setSavedAt] = useState<string | null>(null)
  const [isLoadingDraft, setIsLoadingDraft] = useState(false)
  const [currentDraft, setCurrentDraft] = useState<AgentAuthoringDraft | null>(null)

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

  const loadDraft = useCallback(async (draftId: string): Promise<AgentTypeSetupFormData> => {
    setIsLoadingDraft(true)
    setError(null)
    try {
      const draft = await gatewayRequestJson<AgentAuthoringDraft>(`/pp/agent-authoring/drafts/${encodeURIComponent(draftId)}`)
      setCurrentDraft(draft)
      setSavedAt(draft.updated_at)
      return draftToFormData(draft)
    } catch (e: unknown) {
      setError(e)
      throw e
    } finally {
      setIsLoadingDraft(false)
    }
  }, [])

  const saveDraft = useCallback(async (
    form: AgentTypeSetupFormData,
    draftId?: string
  ): Promise<AgentAuthoringDraft> => {
    setIsSubmitting(true)
    setError(null)
    setSavedAt(null)
    try {
      const payload = toDraftPayload(form, draftId)
      const result = await gatewayRequestJson<AgentAuthoringDraft>('/pp/agent-authoring/drafts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })

      setCurrentDraft(result)
      setSavedAt(result.updated_at || new Date().toISOString())
      return result
    } catch (e: unknown) {
      setError(e)
      throw e
    } finally {
      setIsSubmitting(false)
    }
  }, [])

  const submitForReview = useCallback(async (draftId: string): Promise<AgentAuthoringDraft> => {
    setIsSubmitting(true)
    setError(null)
    try {
      const result = await gatewayRequestJson<AgentAuthoringDraft>(
        `/pp/agent-authoring/drafts/${encodeURIComponent(draftId)}/submit`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({}),
        }
      )
      setCurrentDraft(result)
      setSavedAt(result.updated_at || new Date().toISOString())
      return result
    } catch (e: unknown) {
      setError(e)
      throw e
    } finally {
      setIsSubmitting(false)
    }
  }, [])

  const clearError = useCallback(() => setError(null), [])

  return {
    isSubmitting,
    isLoadingDraft,
    error,
    savedAt,
    currentDraft,
    processorOptions,
    pumpOptions,
    isLoadingOptions,
    loadClassOptions,
    loadDraft,
    saveDraft,
    submitForReview,
    clearError,
  }
}
