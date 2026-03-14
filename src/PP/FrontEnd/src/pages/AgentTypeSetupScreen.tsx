import { useEffect, useMemo, useState } from 'react'
import {
  Body1,
  Button,
  Card,
  CardHeader,
  Checkbox,
  Field,
  Input,
  Spinner,
  Text,
  Textarea,
} from '@fluentui/react-components'
import ApiErrorPanel from '../components/ApiErrorPanel'
import {
  DEFAULT_AGENT_TYPE_SETUP_FORM,
  HOOK_LIST,
  getSectionStates,
  useAgentTypeSetup,
  type AgentTypeSetupFormData,
  type SectionState,
} from '../services/useAgentTypeSetup'

const INDUSTRY_OPTIONS = [
  { value: 'marketing', label: 'Marketing' },
  { value: 'education', label: 'Education' },
  { value: 'sales', label: 'Sales' },
]

const WORKFLOW_STAGES: Array<{
  key: string
  title: string
  guidance: string
  required: boolean
}> = [
  {
    key: 'define_agent',
    title: 'Define agent',
    guidance: 'Name the Digital Marketing Agent, describe the buyer, and make the promise clear.',
    required: true,
  },
  {
    key: 'operating_contract',
    title: 'Set operating contract',
    guidance: 'Explain how the agent should run and what runtime guardrails must hold before release.',
    required: true,
  },
  {
    key: 'deliverables',
    title: 'Review deliverables',
    guidance: 'Call out the outcomes and deliverable commitments the reviewer should expect to approve.',
    required: true,
  },
  {
    key: 'governance',
    title: 'Governance and handoff',
    guidance: 'Record reviewer context, launch notes, and the hooks that make this contract safe to publish.',
    required: true,
  },
]

interface ValidationErrors {
  agent_type?: string
  display_name?: string
  description?: string
  target_customer?: string
  processor_class?: string
  pump_class?: string
  primary_outcomes?: string
  deliverable_commitments?: string
  handoff_notes?: string
}

function validate(form: AgentTypeSetupFormData): ValidationErrors {
  const errors: ValidationErrors = {}
  if (!form.agent_type.trim()) errors.agent_type = 'Agent type is required'
  if (!form.display_name.trim()) errors.display_name = 'Display name is required'
  if (!form.description.trim()) errors.description = 'Description is required'
  if (!form.target_customer.trim()) errors.target_customer = 'Target customer is required'
  if (!form.processor_class.trim()) errors.processor_class = 'Processor class is required'
  if (!form.pump_class.trim()) errors.pump_class = 'Pump class is required'
  if (!form.primary_outcomes.trim()) errors.primary_outcomes = 'Primary outcomes are required'
  if (!form.deliverable_commitments.trim()) errors.deliverable_commitments = 'Deliverable commitments are required'
  if (!form.handoff_notes.trim()) errors.handoff_notes = 'Handoff notes are required'
  return errors
}

const isTradingConnector = (cls: string) => cls.toLowerCase().includes('trading')

function labelForState(state: SectionState): string {
  if (state === 'ready') return 'Ready'
  if (state === 'needs_review') return 'Needs review'
  return 'Missing'
}

function humanizeStatus(status?: string): string {
  if (!status) return 'Draft'
  return status.replace(/_/g, ' ')
}

interface AgentTypeSetupScreenProps {
  agentSetupId?: string
}

export default function AgentTypeSetupScreen({ agentSetupId }: AgentTypeSetupScreenProps) {
  const draftIdFromQuery = useMemo(() => {
    if (typeof window === 'undefined') return undefined
    return new URLSearchParams(window.location.search).get('draft_id') || undefined
  }, [])
  const activeDraftId = agentSetupId || draftIdFromQuery
  const [form, setForm] = useState<AgentTypeSetupFormData>({ ...DEFAULT_AGENT_TYPE_SETUP_FORM })
  const [validationErrors, setValidationErrors] = useState<ValidationErrors>({})
  const [draftId, setDraftId] = useState<string | undefined>(activeDraftId)
  const [isDirty, setIsDirty] = useState(false)
  const [saveState, setSaveState] = useState<'idle' | 'unsaved' | 'saving' | 'saved' | 'error' | 'submitted'>('idle')

  const {
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
  } = useAgentTypeSetup()

  const sectionStates = useMemo(() => getSectionStates(form), [form])
  const readinessSummary = useMemo(() => {
    const values = Object.values(sectionStates)
    return {
      ready: values.filter(value => value === 'ready').length,
      needsReview: values.filter(value => value === 'needs_review').length,
      missing: values.filter(value => value === 'missing').length,
    }
  }, [sectionStates])
  const submitBlocked = readinessSummary.missing > 0

  useEffect(() => {
    void loadClassOptions()
  }, [loadClassOptions])

  useEffect(() => {
    if (!activeDraftId) return

    let cancelled = false

    async function hydrateDraft() {
      try {
        const loadedForm = await loadDraft(activeDraftId)
        if (cancelled) return
        setForm(loadedForm)
        setDraftId(activeDraftId)
        setIsDirty(false)
        setSaveState('saved')
      } catch {
        // hook surfaces the error panel
      }
    }

    void hydrateDraft()
    return () => {
      cancelled = true
    }
  }, [activeDraftId, loadDraft])

  useEffect(() => {
    if (!isDirty) return undefined

    const handleBeforeUnload = (event: BeforeUnloadEvent) => {
      event.preventDefault()
      event.returnValue = 'You have unsaved changes.'
    }

    window.addEventListener('beforeunload', handleBeforeUnload)
    return () => window.removeEventListener('beforeunload', handleBeforeUnload)
  }, [isDirty])

  function setField<K extends keyof AgentTypeSetupFormData>(key: K, value: AgentTypeSetupFormData[K]) {
    clearError()
    setForm(prev => ({ ...prev, [key]: value }))
    setIsDirty(true)
    setSaveState('unsaved')
  }

  function handleReset() {
    clearError()
    setForm({ ...DEFAULT_AGENT_TYPE_SETUP_FORM, hooks: { ...DEFAULT_AGENT_TYPE_SETUP_FORM.hooks } })
    setValidationErrors({})
    setIsDirty(true)
    setSaveState('unsaved')
  }

  async function handleSave() {
    setSaveState('saving')
    try {
      const savedDraft = await saveDraft(form, draftId)
      setDraftId(savedDraft.draft_id)
      setValidationErrors({})
      setIsDirty(false)
      setSaveState('saved')
    } catch {
      setSaveState('error')
    }
  }

  async function handleSubmitForReview() {
    const errors = validate(form)
    setValidationErrors(errors)
    if (Object.keys(errors).length > 0 || submitBlocked) return

    setSaveState('saving')
    try {
      const savedDraft = await saveDraft(form, draftId)
      setDraftId(savedDraft.draft_id)
      const submittedDraft = await submitForReview(savedDraft.draft_id)
      setDraftId(submittedDraft.draft_id)
      setValidationErrors({})
      setIsDirty(false)
      setSaveState('submitted')
    } catch {
      setSaveState('error')
    }
  }

  const showPositionSizeField = isTradingConnector(form.connector_class)
  const reviewerComments = currentDraft?.reviewer_comments || []

  const saveBannerTone = saveState === 'error'
    ? 'var(--colorPaletteRedForeground1)'
    : saveState === 'submitted' || saveState === 'saved'
      ? '#10b981'
      : 'var(--colorNeutralForeground2)'

  const saveBannerText = (() => {
    if (saveState === 'saving' || isSubmitting) return 'Saving draft...'
    if (saveState === 'submitted') return 'Draft sent for review. The reviewer can now inspect completeness and next steps.'
    if (saveState === 'saved' && savedAt) return `Draft saved at ${new Date(savedAt).toLocaleString()}`
    if (saveState === 'error') return 'Save failed. Your draft stays on screen. Check the connection and try again.'
    if (saveState === 'unsaved' || isDirty) return 'Unsaved changes'
    return 'No unsaved changes'
  })()

  return (
    <div className="page-container">
      <div className="page-header">
        <Text as="h1" size={900} weight="semibold">
          {activeDraftId ? 'Edit Base Agent Contract' : 'Base Agent Contract Workflow'}
        </Text>
        <Body1>Guide the Digital Marketing Agent from draft to review-ready without losing clarity, context, or PP theme consistency.</Body1>
      </div>

      <div className="pp-agent-setup-hero">
        <Card className="pp-agent-setup-card pp-agent-setup-card--accent">
          <div className="pp-dashboard-kicker">Base contract</div>
          <Text as="h2" size={700} weight="semibold">Shape a reviewable Digital Marketing Agent contract before anyone touches catalog release.</Text>
          <p className="pp-dashboard-body-copy">
            Keep the operator journey explicit: define the agent, set the operating contract, confirm deliverables, and record governance notes that survive review feedback.
          </p>
        </Card>
        <div className="pp-agent-setup-summary-grid">
          <Card className="pp-agent-setup-card">
            <div className="pp-agent-setup-metric">DMA</div>
            <div className="pp-agent-setup-label">Default candidate preloaded</div>
          </Card>
          <Card className="pp-agent-setup-card">
            <div className="pp-agent-setup-metric">{readinessSummary.ready}/4</div>
            <div className="pp-agent-setup-label">Mandatory stages ready</div>
          </Card>
          <Card className="pp-agent-setup-card">
            <div className="pp-agent-setup-metric">{humanizeStatus(currentDraft?.status || 'draft')}</div>
            <div className="pp-agent-setup-label">Current contract status</div>
          </Card>
        </div>
      </div>

      {!!error && <ApiErrorPanel title="Base contract workflow error" error={error} />}

      {(isLoadingDraft || isLoadingOptions) && (
        <div style={{ marginBottom: 16 }}>
          <Spinner label={isLoadingDraft ? 'Loading draft...' : 'Loading authoring options...'} />
        </div>
      )}

      <Card style={{ marginBottom: 16 }}>
        <CardHeader header={<Text weight="semibold">Workflow stages</Text>} />
        <div className="pp-agent-stage-grid" style={{ padding: 16 }}>
          {WORKFLOW_STAGES.map(stage => (
            <div key={stage.key} className="pp-agent-stage-card">
              <div className="pp-agent-stage-header">
                <Text weight="semibold">{stage.title}</Text>
                <span className={`pp-agent-status-pill pp-agent-status-pill--${sectionStates[stage.key]}`}>
                  {labelForState(sectionStates[stage.key])}
                </span>
              </div>
              <Text size={200}>{stage.guidance}</Text>
              <Text size={100} style={{ opacity: 0.75, marginTop: 6 }}>
                {stage.required ? 'Mandatory before review submission' : 'Optional'}
              </Text>
            </div>
          ))}
        </div>
      </Card>

      <Card style={{ marginBottom: 16 }}>
        <CardHeader header={<Text weight="semibold">Readiness summary</Text>} />
        <div className="pp-agent-readiness-grid" style={{ padding: 16 }}>
          <div className="pp-agent-readiness-item">
            <Text weight="semibold">{readinessSummary.ready}</Text>
            <Text size={200}>Ready</Text>
          </div>
          <div className="pp-agent-readiness-item">
            <Text weight="semibold">{readinessSummary.needsReview}</Text>
            <Text size={200}>Needs review</Text>
          </div>
          <div className="pp-agent-readiness-item">
            <Text weight="semibold">{readinessSummary.missing}</Text>
            <Text size={200}>Blocking submission</Text>
          </div>
          <div className="pp-agent-readiness-item pp-agent-readiness-item--wide">
            <Text size={200} weight="semibold">Next step</Text>
            <Text size={200}>
              {submitBlocked
                ? 'Finish every mandatory stage before sending this contract to review.'
                : 'All mandatory stages are complete. Save and send the contract for review when ready.'}
            </Text>
          </div>
        </div>
      </Card>

      <div className="pp-agent-save-banner" style={{ marginBottom: 16, borderColor: saveBannerTone, color: saveBannerTone }}>
        <Text weight="semibold">{saveBannerText}</Text>
        <Text size={200}>Status: {humanizeStatus(currentDraft?.status || 'draft')}</Text>
      </div>

      {reviewerComments.length > 0 && (
        <Card style={{ marginBottom: 16 }}>
          <CardHeader header={<Text weight="semibold">Reviewer feedback</Text>} />
          <div style={{ padding: 16, display: 'grid', gap: 10 }}>
            {reviewerComments.map(comment => (
              <div key={`${comment.section_key}-${comment.comment}`} className="pp-agent-review-comment">
                <Text weight="semibold">{comment.section_key.replace(/_/g, ' ')}</Text>
                <Text size={200}>{comment.comment}</Text>
              </div>
            ))}
            <Text size={200} style={{ opacity: 0.8 }}>
              Return path: update the highlighted sections, save your changes, and resubmit the draft from this page.
            </Text>
          </div>
        </Card>
      )}

      <Card style={{ marginBottom: 16 }}>
        <CardHeader header={<Text weight="semibold">1. Define agent</Text>} />
        <div style={{ padding: 16, display: 'flex', flexDirection: 'column', gap: 12, maxWidth: 600 }}>
          <Text size={200} style={{ opacity: 0.8 }}>Name the agent, explain who it serves, and make the promise obvious before anyone reviews release readiness.</Text>
          <Field
            label="Agent type"
            required
            validationMessage={validationErrors.agent_type}
            validationState={validationErrors.agent_type ? 'error' : 'none'}
          >
            <Input
              value={form.agent_type}
              onChange={(_, d) => setField('agent_type', d.value)}
              placeholder="e.g. marketing_content_v1"
            />
          </Field>

          <Field
            label="Display name"
            required
            validationMessage={validationErrors.display_name}
            validationState={validationErrors.display_name ? 'error' : 'none'}
          >
            <Input
              value={form.display_name}
              onChange={(_, d) => setField('display_name', d.value)}
              placeholder="e.g. Content Marketing Agent"
            />
          </Field>

          <Field
            label="Contract summary"
            required
            validationMessage={validationErrors.description}
            validationState={validationErrors.description ? 'error' : 'none'}
          >
            <Textarea
              value={form.description}
              onChange={(_, d) => setField('description', d.value)}
              rows={3}
              placeholder="Explain what this Digital Marketing Agent does and why a business would trust it."
            />
          </Field>

          <Field label="Industry">
            <select
              value={form.industry}
              onChange={e => setField('industry', e.target.value)}
              style={{
                padding: '6px 10px',
                borderRadius: 4,
                background: '#18181b',
                color: '#fff',
                border: '1px solid rgba(255,255,255,0.2)',
                width: '100%',
              }}
            >
              {INDUSTRY_OPTIONS.map(o => (
                <option key={o.value} value={o.value}>
                  {o.label}
                </option>
              ))}
            </select>
          </Field>

          <Field
            label="Target customer"
            required
            validationMessage={validationErrors.target_customer}
            validationState={validationErrors.target_customer ? 'error' : 'none'}
          >
            <Textarea
              value={form.target_customer}
              onChange={(_, d) => setField('target_customer', d.value)}
              rows={2}
              placeholder="Describe the business profile this base contract is designed for."
            />
          </Field>
        </div>
      </Card>

      <Card style={{ marginBottom: 16 }}>
        <CardHeader header={<Text weight="semibold">2. Set operating contract</Text>} />
        <div style={{ padding: 16, display: 'flex', flexDirection: 'column', gap: 12, maxWidth: 600 }}>
          <Text size={200} style={{ opacity: 0.8 }}>Capture the runtime expectations and safety defaults that must hold before catalog preparation can begin.</Text>
          <div>
            <Text size={200} style={{ display: 'block', marginBottom: 8, opacity: 0.85 }}>
              Approval mode
            </Text>
            <div style={{ display: 'flex', gap: 8 }}>
              <Button
                appearance={form.approval_mode === 'manual' ? 'primary' : 'secondary'}
                size="small"
                onClick={() => setField('approval_mode', 'manual')}
                aria-label="Manual approval mode"
              >
                Manual
              </Button>
              <Button
                appearance={form.approval_mode === 'auto' ? 'primary' : 'secondary'}
                size="small"
                onClick={() => setField('approval_mode', 'auto')}
                aria-label="Auto approval mode"
              >
                Auto
              </Button>
            </div>
          </div>

          <Field label="Max tasks per day (0 = unlimited)">
            <Input
              type="number"
              value={String(form.max_tasks_per_day)}
              onChange={(_, d) => setField('max_tasks_per_day', Number(d.value) || 0)}
            />
          </Field>

          <Field label="Trial task limit">
            <Input
              type="number"
              value={String(form.trial_task_limit)}
              onChange={(_, d) => setField('trial_task_limit', Number(d.value) || 10)}
            />
          </Field>

          <Field
            label="Processor class"
            required
            validationMessage={validationErrors.processor_class}
            validationState={validationErrors.processor_class ? 'error' : 'none'}
          >
            <select
              value={form.processor_class}
              onChange={e => setField('processor_class', e.target.value)}
              style={{
                padding: '6px 10px',
                borderRadius: 4,
                background: '#18181b',
                color: '#fff',
                border: '1px solid rgba(255,255,255,0.2)',
                width: '100%',
              }}
            >
              <option value="">— Select processor class —</option>
              {processorOptions.length > 0
                ? processorOptions.map(o => (
                    <option key={o.value} value={o.value}>
                      {o.label}
                    </option>
                  ))
                : (
                    <option value={form.processor_class || 'ContentProcessor'}>
                      {form.processor_class || 'ContentProcessor'}
                    </option>
                  )}
            </select>
          </Field>

          <Field
            label="Pump class"
            required
            validationMessage={validationErrors.pump_class}
            validationState={validationErrors.pump_class ? 'error' : 'none'}
          >
            <select
              value={form.pump_class}
              onChange={e => setField('pump_class', e.target.value)}
              style={{
                padding: '6px 10px',
                borderRadius: 4,
                background: '#18181b',
                color: '#fff',
                border: '1px solid rgba(255,255,255,0.2)',
                width: '100%',
              }}
            >
              <option value="">— Select pump class —</option>
              {pumpOptions.length > 0
                ? pumpOptions.map(o => (
                    <option key={o.value} value={o.value}>
                      {o.label}
                    </option>
                  ))
                : (
                    <option value={form.pump_class || 'SocialMediaPump'}>
                      {form.pump_class || 'SocialMediaPump'}
                    </option>
                  )}
            </select>
          </Field>

          <Field label="Connector class (optional)">
            <Input
              value={form.connector_class}
              onChange={(_, d) => setField('connector_class', d.value)}
              placeholder="None"
            />
          </Field>

          <Field label="Publisher class (optional)">
            <Input
              value={form.publisher_class}
              onChange={(_, d) => setField('publisher_class', d.value)}
              placeholder="None"
            />
          </Field>

          {showPositionSizeField && (
            <Field label="Max position size (INR, 0 = unlimited)">
              <Input
                type="number"
                value={String(form.max_position_size_inr)}
                onChange={(_, d) => setField('max_position_size_inr', Number(d.value) || 0)}
              />
            </Field>
          )}
        </div>
      </Card>

      <Card style={{ marginBottom: 16 }}>
        <CardHeader header={<Text weight="semibold">3. Review deliverables</Text>} />
        <div style={{ padding: 16, display: 'flex', flexDirection: 'column', gap: 12, maxWidth: 600 }}>
          <Text size={200} style={{ opacity: 0.8 }}>Describe what the reviewer should expect the customer to receive during trial and what the operator should check before release.</Text>
          <Field
            label="Primary outcomes"
            required
            validationMessage={validationErrors.primary_outcomes}
            validationState={validationErrors.primary_outcomes ? 'error' : 'none'}
          >
            <Textarea
              value={form.primary_outcomes}
              onChange={(_, d) => setField('primary_outcomes', d.value)}
              rows={3}
              placeholder="Summarize the core outcomes this base contract should produce."
            />
          </Field>

          <Field
            label="Deliverable commitments"
            required
            validationMessage={validationErrors.deliverable_commitments}
            validationState={validationErrors.deliverable_commitments ? 'error' : 'none'}
          >
            <Textarea
              value={form.deliverable_commitments}
              onChange={(_, d) => setField('deliverable_commitments', d.value)}
              rows={3}
              placeholder="List the deliverables or review artifacts the operator should expect."
            />
          </Field>

          <Field label="Optional extensions">
            <Textarea
              value={form.optional_extensions}
              onChange={(_, d) => setField('optional_extensions', d.value)}
              rows={2}
              placeholder="Capture useful but non-blocking extensions or future hooks."
            />
          </Field>
        </div>
      </Card>

      <Card style={{ marginBottom: 16 }}>
        <CardHeader header={<Text weight="semibold">4. Governance and handoff</Text>} />
        <div style={{ padding: 16, display: 'flex', flexDirection: 'column', gap: 12 }}>
          <Text size={200} style={{ opacity: 0.8 }}>Hooks and launch notes are not implementation trivia. They are the reviewer context that keeps approval decisions recoverable and explicit.</Text>
          <Field
            label="Handoff notes"
            required
            validationMessage={validationErrors.handoff_notes}
            validationState={validationErrors.handoff_notes ? 'error' : 'none'}
          >
            <Textarea
              value={form.handoff_notes}
              onChange={(_, d) => setField('handoff_notes', d.value)}
              rows={3}
              placeholder="Explain what the next reviewer or catalog owner should check after approval."
            />
          </Field>

          {HOOK_LIST.map(hook => (
            <div key={hook.key} style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
              <Checkbox
                label={hook.label}
                checked={form.hooks[hook.key] ?? false}
                disabled={hook.key === 'AuditHook'}
                onChange={(_, d) => {
                  if (hook.key === 'AuditHook') return
                  clearError()
                  setForm(prev => ({
                    ...prev,
                    hooks: { ...prev.hooks, [hook.key]: !!d.checked },
                  }))
                  setIsDirty(true)
                  setSaveState('unsaved')
                }}
              />
              <Text size={200} style={{ paddingLeft: 32, opacity: 0.7 }}>
                {hook.description}
              </Text>
            </div>
          ))}
        </div>
      </Card>

      <div style={{ display: 'flex', gap: 12, marginBottom: 32 }}>
        <Button
          appearance="secondary"
          onClick={() => void handleSave()}
          disabled={isSubmitting}
        >
          {isSubmitting && saveState === 'saving' ? 'Saving…' : 'Save draft'}
        </Button>
        <Button
          appearance="primary"
          onClick={() => void handleSubmitForReview()}
          disabled={isSubmitting || submitBlocked}
        >
          Submit for review
        </Button>
        <Button appearance="secondary" onClick={handleReset}>
          Reset
        </Button>
      </div>

      <div className="pp-agent-setup-footer-grid">
        <Card className="pp-agent-setup-card">
          <Text weight="semibold">Best contributor outcome</Text>
          <Text size={200}>A contract can be reopened, edited, and resubmitted without reconstructing state from scattered notes.</Text>
        </Card>
        <Card className="pp-agent-setup-card">
          <Text weight="semibold">Best customer outcome</Text>
          <Text size={200}>The customer later hires a clear, trustworthy, well-governed agent instead of a mystery bundle of settings.</Text>
        </Card>
      </div>
    </div>
  )
}
