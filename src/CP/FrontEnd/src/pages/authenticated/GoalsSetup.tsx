import { Badge, Button, Card, Select } from '@fluentui/react-components'
import { useEffect, useMemo, useState } from 'react'

import { DigitalMarketingBriefStepCard } from '../../components/DigitalMarketingBriefStepCard'
import { DigitalMarketingBriefSummaryCard } from '../../components/DigitalMarketingBriefSummaryCard'
import { FeedbackMessage, LoadingIndicator } from '../../components/FeedbackIndicators'
import {
  getThemeDiscoverySkill,
  isDigitalMarketingAgent,
  listHiredAgentSkills,
  saveGoalConfig,
  type GoalSchemaField,
} from '../../services/agentSkills.service'
import { getMyAgentsSummary, type MyAgentInstanceSummary } from '../../services/myAgentsSummary.service'

type BriefStepDefinition = {
  key: string
  title: string
  description: string
  prompt: string
  fieldKeys: string[]
}

const BRIEF_STEP_DEFINITIONS: BriefStepDefinition[] = [
  {
    key: 'context',
    title: 'Map the business context',
    description: 'Give the agent enough context to sound like your business instead of generic marketing copy.',
    prompt: 'What business is this agent speaking for, which market are you in, and what locality should shape the examples, language, and proof points?',
    fieldKeys: ['business_background', 'industry', 'locality'],
  },
  {
    key: 'audience',
    title: 'Define the audience and promise',
    description: 'Clarify who this content is for and what offer should move them to act.',
    prompt: 'Who exactly are you trying to reach, what persona should the agent keep in mind, and what offer or promise should the content keep reinforcing?',
    fieldKeys: ['target_audience', 'persona', 'offer'],
  },
  {
    key: 'channel',
    title: 'Shape the YouTube angle',
    description: 'Translate the business goal into a channel-specific operating brief for YouTube.',
    prompt: 'What outcome should YouTube drive, what does success look like there, and how often should the agent aim to publish?',
    fieldKeys: ['objective', 'channel_intent', 'posting_cadence'],
  },
  {
    key: 'voice',
    title: 'Lock the voice and proof signal',
    description: 'Finish with how the work should sound and what signal tells you the brief is working.',
    prompt: 'What tone should the agent protect in every draft, and which business signals should tell you the content is doing its job?',
    fieldKeys: ['tone', 'success_metrics'],
  },
]

function hasValue(value: unknown): boolean {
  if (Array.isArray(value)) return value.length > 0
  if (value && typeof value === 'object') return Object.keys(value as Record<string, unknown>).length > 0
  return String(value ?? '').trim().length > 0
}

function isFieldVisible(field: GoalSchemaField, values: Record<string, unknown>): boolean {
  if (!field.show_if) return true
  return values[field.show_if.key] === field.show_if.value
}

function isFieldComplete(field: GoalSchemaField, values: Record<string, unknown>): boolean {
  if (!isFieldVisible(field, values)) return true
  if (!field.required) return true
  return hasValue(values[field.key])
}

function buildBriefSteps(fields: GoalSchemaField[]) {
  const usedKeys = new Set<string>()
  const steps = BRIEF_STEP_DEFINITIONS.map((step) => {
    const stepFields = step.fieldKeys
      .map((key) => fields.find((field) => field.key === key))
      .filter((field): field is GoalSchemaField => Boolean(field))

    stepFields.forEach((field) => usedKeys.add(field.key))

    return {
      ...step,
      fields: stepFields,
    }
  }).filter((step) => step.fields.length > 0)

  const extraFields = fields.filter((field) => !usedKeys.has(field.key))
  if (extraFields.length > 0) {
    if (steps.length > 0) {
      steps[steps.length - 1] = {
        ...steps[steps.length - 1],
        fields: [...steps[steps.length - 1].fields, ...extraFields],
      }
    } else {
      steps.push({
        key: 'brief',
        title: 'Capture the brief',
        description: 'Capture the core operating details the agent needs before it can draft.',
        prompt: 'Complete the structured brief so the agent can create specific, credible content instead of guessing.',
        fieldKeys: extraFields.map((field) => field.key),
        fields: extraFields,
      })
    }
  }

  return steps
}

function getDigitalMarketingInstances(instances: MyAgentInstanceSummary[]): MyAgentInstanceSummary[] {
  return instances.filter(
    (instance) =>
      Boolean(String(instance.hired_instance_id || '').trim()) &&
      isDigitalMarketingAgent(instance.agent_id, instance.agent_type_id)
  )
}

export default function GoalsSetup() {
  const [instances, setInstances] = useState<MyAgentInstanceSummary[]>([])
  const [instancesLoading, setInstancesLoading] = useState(true)
  const [instancesError, setInstancesError] = useState<string | null>(null)
  const [selectedHiredInstanceId, setSelectedHiredInstanceId] = useState('')
  const [skillsLoading, setSkillsLoading] = useState(false)
  const [skillsError, setSkillsError] = useState<string | null>(null)
  const [themeDiscoveryFields, setThemeDiscoveryFields] = useState<GoalSchemaField[]>([])
  const [themeDiscoverySkillId, setThemeDiscoverySkillId] = useState('')
  const [values, setValues] = useState<Record<string, unknown>>({})
  const [currentStepIndex, setCurrentStepIndex] = useState(0)
  const [isSaving, setIsSaving] = useState(false)
  const [saveError, setSaveError] = useState<string | null>(null)
  const [saveSuccess, setSaveSuccess] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false

    const loadInstances = async () => {
      setInstancesLoading(true)
      setInstancesError(null)
      try {
        const response = await getMyAgentsSummary()
        if (cancelled) return
        const nextInstances = getDigitalMarketingInstances(response?.instances || [])
        setInstances(nextInstances)
        setSelectedHiredInstanceId((current) => current || String(nextInstances[0]?.hired_instance_id || ''))
      } catch (error: unknown) {
        if (!cancelled) {
          setInstancesError(error instanceof Error ? error.message : 'Failed to load your hired agents')
        }
      } finally {
        if (!cancelled) setInstancesLoading(false)
      }
    }

    void loadInstances()
    return () => {
      cancelled = true
    }
  }, [])

  useEffect(() => {
    let cancelled = false
    const hiredInstanceId = String(selectedHiredInstanceId || '').trim()

    if (!hiredInstanceId) {
      setThemeDiscoveryFields([])
      setThemeDiscoverySkillId('')
      setValues({})
      setCurrentStepIndex(0)
      return
    }

    const loadSkills = async () => {
      setSkillsLoading(true)
      setSkillsError(null)
      setSaveError(null)
      setSaveSuccess(null)

      try {
        const skills = await listHiredAgentSkills(hiredInstanceId)
        if (cancelled) return

        const skill = getThemeDiscoverySkill(skills)
        if (!skill) {
          setThemeDiscoveryFields([])
          setThemeDiscoverySkillId('')
          setValues({})
          setSkillsError('This hired agent does not expose the Theme Discovery skill yet.')
          return
        }

        setThemeDiscoveryFields(skill.goal_schema?.fields || [])
        setThemeDiscoverySkillId(skill.skill_id)
        setValues(skill.goal_config || {})
        setCurrentStepIndex(0)
      } catch (error: unknown) {
        if (!cancelled) {
          setThemeDiscoveryFields([])
          setThemeDiscoverySkillId('')
          setValues({})
          setSkillsError(error instanceof Error ? error.message : 'Failed to load Theme Discovery')
        }
      } finally {
        if (!cancelled) setSkillsLoading(false)
      }
    }

    void loadSkills()
    return () => {
      cancelled = true
    }
  }, [selectedHiredInstanceId])

  const selectedInstance = useMemo(
    () => instances.find((instance) => String(instance.hired_instance_id || '') === selectedHiredInstanceId) || null,
    [instances, selectedHiredInstanceId]
  )

  const steps = useMemo(() => buildBriefSteps(themeDiscoveryFields), [themeDiscoveryFields])
  const currentStep = steps[currentStepIndex] || null
  const visibleFields = useMemo(
    () => themeDiscoveryFields.filter((field) => isFieldVisible(field, values)),
    [themeDiscoveryFields, values]
  )

  const missingFieldLabels = useMemo(() => {
    if (!currentStep) return []
    return currentStep.fields
      .filter((field) => !isFieldComplete(field, values))
      .map((field) => field.label)
  }, [currentStep, values])

  const canContinue = missingFieldLabels.length === 0

  const setField = (key: string, value: unknown) => {
    setSaveError(null)
    setSaveSuccess(null)
    setValues((current) => ({ ...current, [key]: value }))
  }

  const onSave = async () => {
    if (!selectedHiredInstanceId || !themeDiscoverySkillId) return

    setIsSaving(true)
    setSaveError(null)
    setSaveSuccess(null)
    try {
      const updatedSkill = await saveGoalConfig(selectedHiredInstanceId, themeDiscoverySkillId, values)
      setValues(updatedSkill.goal_config || values)
      setSaveSuccess('Theme Discovery brief saved. Content Creation will use this structured brief.')
    } catch (error: unknown) {
      setSaveError(error instanceof Error ? error.message : 'Failed to save Theme Discovery brief')
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <div className="goals-setup-page">
      <div className="page-header">
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', flexWrap: 'wrap' }}>
            <Badge appearance="filled" color="informative">Digital Marketing Agent</Badge>
            <Badge appearance="tint">Theme Discovery</Badge>
          </div>
          <h1 style={{ marginBottom: '0.5rem' }}>Build a brief the agent can actually use</h1>
          <div style={{ opacity: 0.82, maxWidth: '760px', lineHeight: 1.6 }}>
            This guided conversation captures business context, audience, offer, YouTube intent, cadence, and success signals so the agent can create precise drafts instead of guessing from a one-line prompt.
          </div>
        </div>
      </div>

      {instancesLoading ? <LoadingIndicator message="Loading your Digital Marketing Agent brief..." size="medium" /> : null}
      {instancesError ? (
        <FeedbackMessage intent="error" title="We could not load your hired agents" message={instancesError} />
      ) : null}

      {!instancesLoading && !instancesError && instances.length === 0 ? (
        <Card style={{ padding: '1.25rem' }}>
          <h2 style={{ marginTop: 0 }}>No Digital Marketing Agent found yet</h2>
          <div style={{ opacity: 0.82, lineHeight: 1.6 }}>
            Hire the Digital Marketing Agent first. Once the hire exists, Theme Discovery will save directly into its runtime brief.
          </div>
        </Card>
      ) : null}

      {!instancesLoading && !instancesError && instances.length > 0 ? (
        <div style={{ display: 'grid', gap: '1rem' }}>
          <Card style={{ padding: '1rem 1.25rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', gap: '1rem', flexWrap: 'wrap', alignItems: 'flex-end' }}>
              <div>
                <div style={{ fontSize: '0.8rem', textTransform: 'uppercase', letterSpacing: '0.06em', opacity: 0.7 }}>
                  Active hire
                </div>
                <div style={{ marginTop: '0.35rem', fontSize: '1.05rem', fontWeight: 600 }}>
                  {selectedInstance?.nickname || selectedInstance?.agent_id || 'Digital Marketing Agent'}
                </div>
                <div style={{ marginTop: '0.3rem', opacity: 0.78 }}>
                  The brief you save here becomes the structured context for content generation and YouTube readiness.
                </div>
              </div>
              {instances.length > 1 ? (
                <div style={{ minWidth: '260px' }}>
                  <label htmlFor="digital-marketing-agent-select" style={{ display: 'block', marginBottom: '0.35rem' }}>
                    Choose hired agent
                  </label>
                  <Select
                    id="digital-marketing-agent-select"
                    value={selectedHiredInstanceId}
                    onChange={(_, data) => setSelectedHiredInstanceId(data.value)}
                  >
                    {instances.map((instance) => (
                      <option key={String(instance.hired_instance_id)} value={String(instance.hired_instance_id)}>
                        {instance.nickname || instance.agent_id}
                      </option>
                    ))}
                  </Select>
                </div>
              ) : null}
            </div>
          </Card>

          {skillsLoading ? <LoadingIndicator message="Loading Theme Discovery fields..." size="medium" /> : null}
          {skillsError ? (
            <FeedbackMessage intent="error" title="Theme Discovery is not ready" message={skillsError} />
          ) : null}

          {!skillsLoading && !skillsError && currentStep ? (
            <div
              style={{
                display: 'grid',
                gap: '1rem',
                gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
                alignItems: 'start',
              }}
            >
              <div style={{ display: 'grid', gap: '1rem' }}>
                <DigitalMarketingBriefStepCard
                  title={currentStep.title}
                  description={currentStep.description}
                  prompt={currentStep.prompt}
                  fields={currentStep.fields}
                  values={values}
                  stepIndex={currentStepIndex}
                  stepCount={steps.length}
                  canGoBack={currentStepIndex > 0}
                  canContinue={canContinue}
                  isSaving={isSaving}
                  isLastStep={currentStepIndex === steps.length - 1}
                  missingFieldLabels={missingFieldLabels}
                  onChange={setField}
                  onBack={() => setCurrentStepIndex((index) => Math.max(0, index - 1))}
                  onNext={() => setCurrentStepIndex((index) => Math.min(steps.length - 1, index + 1))}
                  onSave={onSave}
                />

                {(saveSuccess || saveError) && (
                  <FeedbackMessage
                    intent={saveError ? 'error' : 'success'}
                    title={saveError ? 'Theme Discovery was not saved' : 'Theme Discovery saved'}
                    message={saveError || saveSuccess || ''}
                  />
                )}
              </div>

              <div style={{ display: 'grid', gap: '1rem' }}>
                <DigitalMarketingBriefSummaryCard
                  title="Structured brief summary"
                  subtitle="This is the exact brief the agent will carry forward into draft creation."
                  fields={visibleFields}
                  values={values}
                />

                <Card style={{ padding: '1rem 1.1rem' }}>
                  <div style={{ fontWeight: 600 }}>Why this matters</div>
                  <div style={{ marginTop: '0.5rem', opacity: 0.82, lineHeight: 1.6 }}>
                    Theme Discovery is the customer-approved source of truth for the Digital Marketing Agent. Better brief quality here reduces generic drafts and false-positive publish readiness later.
                  </div>
                </Card>
              </div>
            </div>
          ) : null}
        </div>
      ) : null}
    </div>
  )
}

