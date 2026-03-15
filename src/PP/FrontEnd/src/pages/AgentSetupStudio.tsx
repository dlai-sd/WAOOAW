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
import { gatewayApiClient, type AgentAuthoringDraft as GatewayAgentAuthoringDraft } from '../services/gatewayApiClient'

const INDUSTRY_OPTIONS = [
  { value: 'marketing', label: 'Marketing' },
  { value: 'education', label: 'Education' },
  { value: 'sales', label: 'Sales' },
]

const BLANK_AGENT_SETUP_FORM: AgentTypeSetupFormData = {
  ...DEFAULT_AGENT_TYPE_SETUP_FORM,
  agent_type: '',
  display_name: '',
  description: '',
  target_customer: '',
  primary_outcomes: '',
  deliverable_commitments: '',
  optional_extensions: '',
  handoff_notes: '',
  hooks: { ...DEFAULT_AGENT_TYPE_SETUP_FORM.hooks },
}

const TEMPLATES = [
  {
    id: 'digital-marketing',
    title: 'Digital Marketing Agent',
    subtitle: 'Campaign planning, content production, governed publishing',
    description: 'A strong default template for a customer-facing marketing operator.',
    form: { ...DEFAULT_AGENT_TYPE_SETUP_FORM, hooks: { ...DEFAULT_AGENT_TYPE_SETUP_FORM.hooks } },
  },
  {
    id: 'sales-outreach',
    title: 'Sales Outreach Agent',
    subtitle: 'Prospecting, follow-up, and reviewable messaging',
    description: 'A reusable base for sales teams that want structure before scale.',
    form: {
      ...DEFAULT_AGENT_TYPE_SETUP_FORM,
      agent_type: 'sales.outreach_agent',
      display_name: 'Sales Outreach Agent',
      description: 'Runs structured outbound sales work with clear review controls.',
      industry: 'sales',
      target_customer: 'Revenue teams that need dependable outbound execution.',
      hooks: { ...DEFAULT_AGENT_TYPE_SETUP_FORM.hooks },
    },
  },
  {
    id: 'blank',
    title: 'Start from scratch',
    subtitle: 'Build a new reusable blueprint',
    description: 'Begin with a blank authoring canvas and define the blueprint yourself.',
    form: { ...BLANK_AGENT_SETUP_FORM, hooks: { ...BLANK_AGENT_SETUP_FORM.hooks } },
  },
]

const STEPS = [
  { id: 'starter', title: 'Choose a starting point', description: 'Start from a template or a blank blueprint.' },
  { id: 'identity', title: 'Define the agent', description: 'Name it, explain the promise, and define the customer.' },
  { id: 'value', title: 'Shape customer value', description: 'Describe outcomes and deliverables in plain language.' },
  { id: 'operations', title: 'Set operating rules', description: 'Choose approval style, limits, and optional advanced settings.' },
  { id: 'review', title: 'Prepare for review', description: 'Capture handoff notes and safety defaults for the reviewer.' },
] as const

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

function cloneForm(form: AgentTypeSetupFormData): AgentTypeSetupFormData {
  return { ...form, hooks: { ...form.hooks } }
}

function validate(form: AgentTypeSetupFormData): ValidationErrors {
  const errors: ValidationErrors = {}
  if (!form.agent_type.trim()) errors.agent_type = 'Internal blueprint key is required'
  if (!form.display_name.trim()) errors.display_name = 'Display name is required'
  if (!form.description.trim()) errors.description = 'Agent promise is required'
  if (!form.target_customer.trim()) errors.target_customer = 'Target customer is required'
  if (!form.processor_class.trim()) errors.processor_class = 'Processor class is required'
  if (!form.pump_class.trim()) errors.pump_class = 'Pump class is required'
  if (!form.primary_outcomes.trim()) errors.primary_outcomes = 'Primary outcomes are required'
  if (!form.deliverable_commitments.trim()) errors.deliverable_commitments = 'Deliverable commitments are required'
  if (!form.handoff_notes.trim()) errors.handoff_notes = 'Review handoff notes are required'
  return errors
}

function stateTone(state: SectionState): 'ready' | 'needs_review' | 'missing' {
  return state === 'ready' ? 'ready' : state === 'needs_review' ? 'needs_review' : 'missing'
}

function humanizeStatus(status?: string): string {
  return (status || 'draft').replace(/_/g, ' ')
}

function mapStepToSection(stepId: string): string | null {
  if (stepId === 'identity') return 'define_agent'
  if (stepId === 'value') return 'deliverables'
  if (stepId === 'operations') return 'operating_contract'
  if (stepId === 'review') return 'governance'
  return null
}

interface AgentSetupStudioProps {
  agentSetupId?: string
}

export default function AgentSetupStudio({ agentSetupId }: AgentSetupStudioProps) {
  const draftIdFromQuery = useMemo(() => {
    if (typeof window === 'undefined') return undefined
    return new URLSearchParams(window.location.search).get('draft_id') || undefined
  }, [])
  const activeDraftId = agentSetupId || draftIdFromQuery

  const [form, setForm] = useState<AgentTypeSetupFormData>(cloneForm(DEFAULT_AGENT_TYPE_SETUP_FORM))
  const [validationErrors, setValidationErrors] = useState<ValidationErrors>({})
  const [draftId, setDraftId] = useState<string | undefined>(activeDraftId)
  const [isDirty, setIsDirty] = useState(false)
  const [saveState, setSaveState] = useState<'idle' | 'unsaved' | 'saving' | 'saved' | 'error' | 'submitted'>('idle')
  const [selectedTemplateId, setSelectedTemplateId] = useState(activeDraftId ? 'blank' : 'digital-marketing')
  const [activeStepIndex, setActiveStepIndex] = useState(activeDraftId ? 1 : 0)
  const [showAdvancedRuntime, setShowAdvancedRuntime] = useState(false)
  const [starterMode, setStarterMode] = useState<'existing' | 'new'>(activeDraftId ? 'existing' : 'new')
  const [recentDrafts, setRecentDrafts] = useState<GatewayAgentAuthoringDraft[]>([])
  const [isLoadingDraftList, setIsLoadingDraftList] = useState(false)

  const {
    isSubmitting,
    isLoadingDraft,
    error,
    savedAt,
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
  const submitBlocked = Object.values(sectionStates).some(value => value === 'missing')
  const unresolvedItems = useMemo(() => {
    const items: string[] = []
    if (sectionStates.define_agent !== 'ready') items.push('Define the agent clearly for reviewers.')
    if (sectionStates.deliverables !== 'ready') items.push('Describe customer outcomes and deliverables.')
    if (sectionStates.operating_contract !== 'ready') items.push('Confirm operating rules and runtime defaults.')
    if (sectionStates.governance !== 'ready') items.push('Add handoff notes and safety defaults.')
    return items
  }, [sectionStates])

  useEffect(() => {
    void loadClassOptions()
  }, [loadClassOptions])

  useEffect(() => {
    let cancelled = false
    async function loadRecentDrafts() {
      setIsLoadingDraftList(true)
      try {
        const drafts = await gatewayApiClient.listAgentAuthoringDrafts()
        if (cancelled) return
        setRecentDrafts(drafts)
      } catch {
        if (cancelled) return
        setRecentDrafts([])
      } finally {
        if (!cancelled) setIsLoadingDraftList(false)
      }
    }
    void loadRecentDrafts()
    return () => { cancelled = true }
  }, [])

  useEffect(() => {
    if (!activeDraftId) return
    const draftIdToLoad: string = activeDraftId
    let cancelled = false
    async function hydrateDraft() {
      try {
        const loadedForm = await loadDraft(draftIdToLoad)
        if (cancelled) return
        setForm(cloneForm(loadedForm))
        setDraftId(draftIdToLoad)
        setSaveState('saved')
        setIsDirty(false)
        setSelectedTemplateId('blank')
      } catch {
        return
      }
    }
    void hydrateDraft()
    return () => { cancelled = true }
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

  function applyTemplate(templateId: string) {
    const template = TEMPLATES.find(item => item.id === templateId)
    if (!template) return
    setSelectedTemplateId(templateId)
    setForm(cloneForm(template.form))
    setValidationErrors({})
    setIsDirty(true)
    setSaveState('unsaved')
    setActiveStepIndex(1)
    setStarterMode('new')
  }

  async function handleSelectExistingDraft(selectedDraft: GatewayAgentAuthoringDraft) {
    clearError()
    setSaveState('saving')
    try {
      const loadedForm = await loadDraft(selectedDraft.draft_id)
      setForm(cloneForm(loadedForm))
      setDraftId(selectedDraft.draft_id)
      setValidationErrors({})
      setIsDirty(false)
      setSaveState('saved')
      setStarterMode('existing')
      setSelectedTemplateId('blank')
      setActiveStepIndex(1)
    } catch {
      setSaveState('error')
    }
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
      await submitForReview(savedDraft.draft_id)
      setValidationErrors({})
      setIsDirty(false)
      setSaveState('submitted')
    } catch {
      setSaveState('error')
    }
  }

  const saveBannerText = saveState === 'saving' || isSubmitting
    ? 'Saving draft...'
    : saveState === 'submitted'
      ? 'Draft sent for review. The reviewer can now inspect completeness and next steps.'
      : saveState === 'saved' && savedAt
        ? `Draft saved at ${new Date(savedAt).toLocaleString()}`
        : saveState === 'error'
          ? 'Save failed. Your draft stays on screen. Check the connection and try again.'
          : saveState === 'unsaved' || isDirty
            ? 'Unsaved changes'
            : 'No unsaved changes'

  const currentStep = STEPS[activeStepIndex]
  const currentSection = mapStepToSection(currentStep.id)
  const canContinue = currentStep.id === 'starter' || !currentSection || sectionStates[currentSection] === 'ready'

  return (
    <div className="page-container pp-agent-studio-page">
      <div className="page-header">
        <div>
          <Text as="h1" size={800} weight="semibold">
            Agent Setup Studio
          </Text>
          <Text as="p" size={300} className="page-subtitle">
            Build a reusable WAOOAW agent blueprint with business context first, then operating detail.
          </Text>
        </div>
      </div>

      {error ? <ApiErrorPanel title="Agent setup error" error={error} /> : null}

      {(isLoadingDraft || isLoadingOptions) ? (
        <Card>
          <Spinner label={isLoadingDraft ? 'Loading draft...' : 'Loading studio options...'} />
        </Card>
      ) : null}

      <div className="pp-agent-studio-shell">
        <aside className="pp-agent-studio-rail">
          <Card className="pp-agent-studio-rail-card">
            <Text as="h2" size={500} weight="semibold">
              Progress
            </Text>
            <div className="pp-agent-studio-step-list">
              {STEPS.map((step, index) => {
                const sectionKey = mapStepToSection(step.id)
                const stepState = sectionKey ? sectionStates[sectionKey] : selectedTemplateId ? 'ready' : 'missing'
                const isActive = index === activeStepIndex
                return (
                  <button
                    key={step.id}
                    type="button"
                    className={`pp-agent-studio-step-button${isActive ? ' is-active' : ''}`}
                    onClick={() => setActiveStepIndex(index)}
                  >
                    <span className="pp-agent-studio-step-index">0{index + 1}</span>
                    <span className="pp-agent-studio-step-copy">
                      <span className="pp-agent-studio-step-title">{step.title}</span>
                      <span className="pp-agent-studio-step-description">{step.description}</span>
                    </span>
                    <span className={`pp-agent-studio-step-state pp-agent-studio-step-state--${stateTone(stepState as SectionState)}`}>
                      {stepState === 'ready' ? 'Ready' : stepState === 'needs_review' ? 'Review' : 'Missing'}
                    </span>
                  </button>
                )
              })}
            </div>
          </Card>
        </aside>

        <section className="pp-agent-studio-canvas">
          <Card className="pp-agent-studio-canvas-card">
            <div className="pp-agent-studio-canvas-header">
            <CardHeader
              className="pp-agent-studio-canvas-header-card"
              header={
                <div>
                  <Text as="h2" size={600} weight="semibold">{currentStep.title}</Text>
                  <Text as="p" size={300}>{currentStep.description}</Text>
                </div>
              }
            />
            </div>

            <div className="pp-agent-studio-canvas-body">

            {currentStep.id === 'starter' ? (
              <div className="pp-agent-studio-starter-layout">
                <div className="pp-agent-studio-starter-mode-grid">
                  <button
                    type="button"
                    className={`pp-agent-studio-template-card${starterMode === 'existing' ? ' is-selected' : ''}`}
                    onClick={() => setStarterMode('existing')}
                  >
                    <Text as="span" size={500} weight="semibold">Open existing blueprint</Text>
                    <Text as="span" size={200} className="pp-agent-studio-template-subtitle">Resume a saved draft and continue the wizard.</Text>
                    <Body1>Use this when an agent blueprint already exists and needs further authoring or review prep.</Body1>
                  </button>
                  <button
                    type="button"
                    className={`pp-agent-studio-template-card${starterMode === 'new' ? ' is-selected' : ''}`}
                    onClick={() => setStarterMode('new')}
                  >
                    <Text as="span" size={500} weight="semibold">Create new blueprint</Text>
                    <Text as="span" size={200} className="pp-agent-studio-template-subtitle">Start a new reusable agent definition from a template or blank canvas.</Text>
                    <Body1>Use this when you are designing a fresh agent type for the marketplace or internal catalog.</Body1>
                  </button>
                </div>

                {starterMode === 'existing' ? (
                  <div className="pp-agent-studio-existing-list">
                    <Text as="h3" size={500} weight="semibold">Existing blueprints</Text>
                    {isLoadingDraftList ? (
                      <Card className="pp-agent-studio-preview-card">
                        <Spinner label="Loading blueprints..." />
                      </Card>
                    ) : recentDrafts.length > 0 ? (
                      recentDrafts.map(existingDraft => (
                        <button
                          key={existingDraft.draft_id}
                          type="button"
                          className={`pp-agent-studio-existing-card${draftId === existingDraft.draft_id ? ' is-selected' : ''}`}
                          onClick={() => void handleSelectExistingDraft(existingDraft)}
                        >
                          <div className="pp-agent-studio-existing-card-header">
                            <Text as="span" size={400} weight="semibold">{existingDraft.candidate_agent_label || existingDraft.candidate_agent_type_id}</Text>
                            <span className={`pp-agent-studio-step-state pp-agent-studio-step-state--${stateTone(existingDraft.section_states.governance || 'missing')}`}>
                              {humanizeStatus(existingDraft.status)}
                            </span>
                          </div>
                          <Text as="p" size={200}>Draft ID: {existingDraft.draft_id}</Text>
                          <Text as="p" size={200}>Updated: {new Date(existingDraft.updated_at).toLocaleString()}</Text>
                        </button>
                      ))
                    ) : (
                      <Card className="pp-agent-studio-preview-card">
                        <Text as="p" size={300}>No saved blueprints are available in this session. Start a new one.</Text>
                      </Card>
                    )}
                  </div>
                ) : (
                  <div className="pp-agent-studio-template-grid">
                    {TEMPLATES.map(template => (
                      <button
                        key={template.id}
                        type="button"
                        className={`pp-agent-studio-template-card${selectedTemplateId === template.id ? ' is-selected' : ''}`}
                        onClick={() => applyTemplate(template.id)}
                      >
                        <Text as="span" size={500} weight="semibold">{template.title}</Text>
                        <Text as="span" size={200} className="pp-agent-studio-template-subtitle">{template.subtitle}</Text>
                        <Body1>{template.description}</Body1>
                      </button>
                    ))}
                  </div>
                )}
              </div>
            ) : null}

            {currentStep.id === 'identity' ? (
              <div className="pp-agent-studio-form-grid">
                <Field label="Agent display name" validationMessage={validationErrors.display_name}>
                  <Input value={form.display_name} onChange={(_, data) => setField('display_name', data.value)} />
                </Field>
                <Field label="Internal blueprint key" validationMessage={validationErrors.agent_type}>
                  <Input value={form.agent_type} onChange={(_, data) => setField('agent_type', data.value)} />
                </Field>
                <Field label="Primary industry">
                  <div className="pp-agent-studio-choice-grid">
                    {INDUSTRY_OPTIONS.map(option => (
                      <button
                        key={option.value}
                        type="button"
                        className={`pp-agent-studio-choice-card${form.industry === option.value ? ' is-selected' : ''}`}
                        onClick={() => setField('industry', option.value)}
                      >
                        <Text as="span" size={400} weight="semibold">{option.label}</Text>
                      </button>
                    ))}
                  </div>
                </Field>
                <Field label="What promise does this agent make?" validationMessage={validationErrors.description}>
                  <Textarea rows={4} value={form.description} onChange={(_, data) => setField('description', data.value)} />
                </Field>
                <Field label="Who is the target customer?" validationMessage={validationErrors.target_customer}>
                  <Textarea rows={4} value={form.target_customer} onChange={(_, data) => setField('target_customer', data.value)} />
                </Field>
              </div>
            ) : null}

            {currentStep.id === 'value' ? (
              <div className="pp-agent-studio-form-grid">
                <Field label="Primary customer outcomes" validationMessage={validationErrors.primary_outcomes}>
                  <Textarea rows={5} value={form.primary_outcomes} onChange={(_, data) => setField('primary_outcomes', data.value)} />
                </Field>
                <Field label="Deliverables this agent commits to" validationMessage={validationErrors.deliverable_commitments}>
                  <Textarea rows={5} value={form.deliverable_commitments} onChange={(_, data) => setField('deliverable_commitments', data.value)} />
                </Field>
                <Field label="Optional extensions and upgrade paths">
                  <Textarea rows={4} value={form.optional_extensions} onChange={(_, data) => setField('optional_extensions', data.value)} />
                </Field>
                <Card className="pp-agent-studio-preview-card">
                  <Text as="h3" size={500} weight="semibold">
                    Reviewer preview
                  </Text>
                  <Body1>
                    {form.display_name || 'This agent'} helps {form.target_customer || 'a defined customer segment'} by delivering {form.primary_outcomes || 'clear business outcomes'}.
                  </Body1>
                  <Text as="p" size={200}>
                    Deliverables: {form.deliverable_commitments || 'Add concrete deliverables so the reviewer knows what success looks like.'}
                  </Text>
                </Card>
              </div>
            ) : null}

            {currentStep.id === 'operations' ? (
              <div className="pp-agent-studio-form-grid">
                <Field label="Approval mode">
                  <div className="pp-agent-studio-choice-grid">
                    {[
                      { value: 'manual', label: 'Human in the loop', description: 'A person approves material before external action.' },
                      { value: 'auto', label: 'Guarded autopilot', description: 'The agent can act within defined safety limits.' },
                    ].map(option => (
                      <button
                        key={option.value}
                        type="button"
                        className={`pp-agent-studio-choice-card${form.approval_mode === option.value ? ' is-selected' : ''}`}
                        onClick={() => setField('approval_mode', option.value as AgentTypeSetupFormData['approval_mode'])}
                      >
                        <Text as="span" size={400} weight="semibold">{option.label}</Text>
                        <Text as="span" size={200}>{option.description}</Text>
                      </button>
                    ))}
                  </div>
                </Field>

                <div className="pp-agent-studio-choice-grid">
                  <Card className="pp-agent-studio-preview-card">
                    <Text as="h3" size={400} weight="semibold">Daily task cap</Text>
                    <Text as="p" size={200}>{form.max_tasks_per_day} tasks per day</Text>
                  </Card>
                  <Card className="pp-agent-studio-preview-card">
                    <Text as="h3" size={400} weight="semibold">Trial limit</Text>
                    <Text as="p" size={200}>{form.trial_task_limit} tasks in trial mode</Text>
                  </Card>
                  <Card className="pp-agent-studio-preview-card">
                    <Text as="h3" size={400} weight="semibold">Budget limit</Text>
                    <Text as="p" size={200}>₹{form.max_position_size_inr.toLocaleString('en-IN')} max position size</Text>
                  </Card>
                </div>

                <Field label="Enable advanced runtime mapping">
                  <Checkbox
                    checked={showAdvancedRuntime}
                    onChange={(_, data) => setShowAdvancedRuntime(Boolean(data.checked))}
                    label="Show processor, pump, and integration classes"
                  />
                </Field>

                {showAdvancedRuntime ? (
                  <div className="pp-agent-studio-form-grid pp-agent-studio-form-grid--nested">
                    <Field label="Processor class" validationMessage={validationErrors.processor_class}>
                      <Input value={form.processor_class} onChange={(_, data) => setField('processor_class', data.value)} list="processor-options" />
                    </Field>
                    <Field label="Pump class" validationMessage={validationErrors.pump_class}>
                      <Input value={form.pump_class} onChange={(_, data) => setField('pump_class', data.value)} list="pump-options" />
                    </Field>
                    <Field label="Connector class">
                      <Input value={form.connector_class} onChange={(_, data) => setField('connector_class', data.value)} />
                    </Field>
                    <Field label="Publisher class">
                      <Input value={form.publisher_class} onChange={(_, data) => setField('publisher_class', data.value)} />
                    </Field>
                    <datalist id="processor-options">
                      {processorOptions.map(option => <option key={option.value} value={option.value}>{option.label}</option>)}
                    </datalist>
                    <datalist id="pump-options">
                      {pumpOptions.map(option => <option key={option.value} value={option.value}>{option.label}</option>)}
                    </datalist>
                  </div>
                ) : null}

                <Field label="Success hooks">
                  <div className="pp-agent-studio-hook-grid">
                    {HOOK_LIST.map(hook => (
                      <Checkbox
                        key={hook.key}
                        checked={form.hooks[hook.key]}
                        label={hook.label}
                        onChange={(_, data) => {
                          setForm(prev => ({
                            ...prev,
                            hooks: {
                              ...prev.hooks,
                              [hook.key]: Boolean(data.checked),
                            },
                          }))
                          setIsDirty(true)
                          setSaveState('unsaved')
                        }}
                      />
                    ))}
                  </div>
                </Field>
              </div>
            ) : null}

            {currentStep.id === 'review' ? (
              <div className="pp-agent-studio-form-grid">
                <Field label="Reviewer handoff notes" validationMessage={validationErrors.handoff_notes}>
                  <Textarea rows={6} value={form.handoff_notes} onChange={(_, data) => setField('handoff_notes', data.value)} />
                </Field>
                <Card className="pp-agent-studio-preview-card">
                  <Text as="h3" size={500} weight="semibold">
                    Submission checklist
                  </Text>
                  <div className="pp-agent-studio-unresolved-list">
                    {unresolvedItems.length > 0 ? unresolvedItems.map(item => (
                      <Text as="p" size={200} key={item}>{item}</Text>
                    )) : <Text as="p" size={200}>This blueprint is ready for reviewer inspection.</Text>}
                  </div>
                </Card>
              </div>
            ) : null}
            </div>

            <div className="pp-agent-studio-action-bar">
              <div className="pp-agent-studio-action-bar-left">
                <Button appearance="secondary" onClick={handleSave} disabled={isSubmitting || isLoadingDraft}>
                  Save draft
                </Button>
                <Text as="span" size={200}>{saveBannerText}</Text>
              </div>
              <div className="pp-agent-studio-action-bar-right">
                <Button
                  appearance="subtle"
                  onClick={() => setActiveStepIndex(index => Math.max(0, index - 1))}
                  disabled={activeStepIndex === 0}
                >
                  Back
                </Button>
                {activeStepIndex < STEPS.length - 1 ? (
                  <Button appearance="primary" onClick={() => setActiveStepIndex(index => index + 1)} disabled={!canContinue}>
                    Continue
                  </Button>
                ) : (
                  <Button appearance="primary" onClick={handleSubmitForReview} disabled={isSubmitting || submitBlocked}>
                    Submit for review
                  </Button>
                )}
              </div>
            </div>
          </Card>
        </section>
      </div>
    </div>
  )
}
