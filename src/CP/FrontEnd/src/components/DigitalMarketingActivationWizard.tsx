import { Badge, Button, Card, Checkbox, Input, Textarea } from '@fluentui/react-components'
import { useNavigate } from 'react-router-dom'
import { useEffect, useMemo, useState } from 'react'

import { FeedbackMessage, LoadingIndicator, ProgressIndicator, SaveIndicator } from './FeedbackIndicators'
import { PlatformConnectionsPanel } from './PlatformConnectionsPanel'
import { getHiredAgentBySubscription, upsertHiredAgentDraft, type HiredAgentInstance } from '../services/hiredAgents.service'
import type { MyAgentInstanceSummary } from '../services/myAgentsSummary.service'
import {
  buildMarketingPlatformBindings,
  getActivationMilestoneCount,
  getDigitalMarketingActivationWorkspace,
  getSelectedMarketingPlatforms,
  upsertDigitalMarketingActivationWorkspace,
  type DigitalMarketingActivationResponse,
} from '../services/digitalMarketingActivation.service'

const DIGITAL_MARKETING_AGENT_TYPE_ID = 'marketing.digital_marketing.v1'

const PLATFORM_OPTIONS = [
  { key: 'youtube', label: 'YouTube', description: 'Channel uploads and video publishing approvals.' },
  { key: 'instagram', label: 'Instagram', description: 'Reels, posts, and story publishing workflows.' },
  { key: 'facebook', label: 'Facebook', description: 'Page posting and distribution.' },
  { key: 'linkedin', label: 'LinkedIn', description: 'Thought leadership and company-page posts.' },
  { key: 'whatsapp', label: 'WhatsApp', description: 'Outbound campaign and customer follow-up content.' },
  { key: 'x', label: 'X', description: 'Short-form social publishing and promotion.' },
]

const WIZARD_STEPS = [
  {
    id: 'induct',
    title: 'Induct Agent',
    description: 'Set the identity this customer will see and preserve the draft-backed configured state.',
  },
  {
    id: 'brief',
    title: 'Capture business brief',
    description: 'Add the business context the backend materializes into the hired-agent config.',
  },
  {
    id: 'channels',
    title: 'Prepare agent channels',
    description: 'Choose the live channels and connect what the agent needs before runtime handoff.',
  },
] as const

type DigitalMarketingActivationWizardProps = {
  instance: MyAgentInstanceSummary
  readOnly: boolean
  onSaved: (updated: HiredAgentInstance) => void
}

function normalizeText(value: unknown): string {
  return String(value ?? '')
}

function formatListForTextarea(value: unknown): string {
  if (!Array.isArray(value)) return ''
  return value
    .map((entry) => String(entry || '').trim())
    .filter(Boolean)
    .join('\n')
}

function parseListTextarea(value: string): string[] {
  return String(value || '')
    .split(/\n|,/g)
    .map((entry) => entry.trim())
    .filter(Boolean)
}

function buildFallbackDraft(instance: MyAgentInstanceSummary): HiredAgentInstance {
  return {
    subscription_id: instance.subscription_id,
    hired_instance_id: String(instance.hired_instance_id || '').trim(),
    agent_id: instance.agent_id,
    agent_type_id: instance.agent_type_id,
    nickname: instance.nickname || '',
    theme: '',
    config: {},
    configured: Boolean(instance.configured),
    goals_completed: Boolean(instance.goals_completed),
  }
}

export function DigitalMarketingActivationWizard({ instance, readOnly, onSaved }: DigitalMarketingActivationWizardProps) {
  const navigate = useNavigate()

  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [saveError, setSaveError] = useState<string | null>(null)
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle')
  const [activeStepIndex, setActiveStepIndex] = useState(0)

  const [draft, setDraft] = useState<HiredAgentInstance | null>(null)
  const [activation, setActivation] = useState<DigitalMarketingActivationResponse | null>(null)

  const [nickname, setNickname] = useState('')
  const [theme, setTheme] = useState('')
  const [brandName, setBrandName] = useState('')
  const [location, setLocation] = useState('')
  const [primaryLanguage, setPrimaryLanguage] = useState('')
  const [timezone, setTimezone] = useState('')
  const [businessContext, setBusinessContext] = useState('')
  const [offeringsText, setOfferingsText] = useState('')
  const [selectedPlatforms, setSelectedPlatforms] = useState<string[]>([])

  const hiredInstanceId = useMemo(
    () => String(draft?.hired_instance_id || instance.hired_instance_id || '').trim(),
    [draft?.hired_instance_id, instance.hired_instance_id]
  )

  const loadState = async () => {
    setLoading(true)
    setError(null)
    try {
      let nextDraft: HiredAgentInstance
      try {
        nextDraft = await getHiredAgentBySubscription(instance.subscription_id)
      } catch (draftError: any) {
        if (draftError?.status !== 404) throw draftError
        nextDraft = buildFallbackDraft(instance)
      }

      const nextHiredInstanceId = String(nextDraft.hired_instance_id || instance.hired_instance_id || '').trim()
      let nextActivation: DigitalMarketingActivationResponse | null = null
      if (nextHiredInstanceId) {
        nextActivation = await getDigitalMarketingActivationWorkspace(nextHiredInstanceId)
      }

      setDraft(nextDraft)
      setActivation(nextActivation)
      setNickname(normalizeText(nextDraft.nickname))
      setTheme(normalizeText(nextDraft.theme))
      setBrandName(normalizeText(nextActivation?.workspace.brand_name))
      setLocation(normalizeText(nextActivation?.workspace.location))
      setPrimaryLanguage(normalizeText(nextActivation?.workspace.primary_language))
      setTimezone(normalizeText(nextActivation?.workspace.timezone))
      setBusinessContext(normalizeText(nextActivation?.workspace.business_context))
      setOfferingsText(formatListForTextarea(nextActivation?.workspace.offerings_services))
      setSelectedPlatforms(getSelectedMarketingPlatforms(nextActivation?.workspace))
      setSaveStatus('idle')
      setSaveError(null)
    } catch (e: any) {
      setError(e?.message || 'Failed to load activation workspace')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void loadState()
  }, [instance.subscription_id])

  useEffect(() => {
    setActiveStepIndex(0)
  }, [instance.subscription_id])

  const readiness = activation?.readiness || {
    brief_complete: false,
    youtube_selected: selectedPlatforms.includes('youtube'),
    youtube_connection_ready: false,
    configured: Boolean(nickname.trim() && theme.trim()),
    can_finalize: false,
    missing_requirements: [],
  }

  const milestoneCount = getActivationMilestoneCount(readiness)
  const activeStep = WIZARD_STEPS[activeStepIndex]
  const isFinalStep = activeStepIndex === WIZARD_STEPS.length - 1
  const missingProfileFields = useMemo(() => {
    const items: string[] = []
    if (!brandName.trim()) items.push('brand name')
    if (!location.trim()) items.push('location')
    if (!primaryLanguage.trim()) items.push('primary language')
    if (!timezone.trim()) items.push('timezone')
    if (parseListTextarea(offeringsText).length === 0) items.push('offerings and services')
    return items
  }, [brandName, location, offeringsText, primaryLanguage, timezone])

  const saveWorkspace = async () => {
    if (readOnly) return

    setSaveStatus('saving')
    setSaveError(null)

    try {
      const resolvedAgentTypeId = String(instance.agent_type_id || draft?.agent_type_id || DIGITAL_MARKETING_AGENT_TYPE_ID).trim() || DIGITAL_MARKETING_AGENT_TYPE_ID
      const savedDraft = await upsertHiredAgentDraft({
        subscription_id: instance.subscription_id,
        agent_id: instance.agent_id,
        agent_type_id: resolvedAgentTypeId,
        nickname: nickname.trim(),
        theme: theme.trim(),
        config: draft?.config || {},
      })

      const offeringsServices = parseListTextarea(offeringsText)
      const platformBindings = buildMarketingPlatformBindings(
        selectedPlatforms,
        activation?.workspace.platform_bindings,
        'default'
      )

      const savedActivation = await upsertDigitalMarketingActivationWorkspace(savedDraft.hired_instance_id, {
        workspace: {
          brand_name: brandName.trim(),
          location: location.trim(),
          primary_language: primaryLanguage.trim(),
          timezone: timezone.trim(),
          business_context: businessContext.trim(),
          offerings_services: offeringsServices,
          platforms_enabled: selectedPlatforms,
          platform_bindings: platformBindings,
        },
      })

      const refreshedDraft = await getHiredAgentBySubscription(instance.subscription_id).catch(() => ({
        ...savedDraft,
        configured: savedActivation.readiness.configured,
      }))

      setDraft(refreshedDraft)
      setActivation(savedActivation)
      setSaveStatus('saved')
      onSaved({
        ...refreshedDraft,
        hired_instance_id: savedActivation.hired_instance_id,
        configured: savedActivation.readiness.configured,
      })
    } catch (e: any) {
      setSaveError(e?.message || 'Failed to save activation workspace')
      setSaveStatus('error')
    }
  }

  const togglePlatform = (platformKey: string, checked: boolean) => {
    setSelectedPlatforms((prev) => {
      const next = new Set(prev)
      if (checked) next.add(platformKey)
      else next.delete(platformKey)
      return Array.from(next)
    })
  }

  const goToStep = (nextStepIndex: number) => {
    setActiveStepIndex(Math.max(0, Math.min(nextStepIndex, WIZARD_STEPS.length - 1)))
  }

  if (loading) {
    return <LoadingIndicator message="Loading digital marketing activation..." size="medium" />
  }

  if (error) {
    return <FeedbackMessage intent="error" title="Activation unavailable" message={error} action={{ label: 'Retry', onClick: () => void loadState() }} />
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', marginTop: '1rem' }}>
      <Card style={{ padding: '1.25rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', gap: '1rem', flexWrap: 'wrap', alignItems: 'flex-start' }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
            <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', alignItems: 'center' }}>
              <h3 style={{ margin: 0 }}>Digital Marketing activation</h3>
              <Badge appearance="tint" color={readiness.can_finalize ? 'success' : 'informative'}>
                {readiness.can_finalize ? 'Ready to run' : 'In setup'}
              </Badge>
            </div>
            <div style={{ opacity: 0.8, maxWidth: '60ch', lineHeight: 1.5 }}>
              Induct the agent, capture the business brief, and attach live channels without sending this hire back through the older setup flow.
            </div>
          </div>

          <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap', alignItems: 'center' }}>
            <SaveIndicator status={saveStatus} errorMessage={saveError || undefined} />
            <Button appearance="secondary" onClick={() => void loadState()}>
              Refresh status
            </Button>
            <Button appearance="primary" onClick={() => void saveWorkspace()} disabled={readOnly || saveStatus === 'saving'}>
              {saveStatus === 'saving' ? 'Saving draft...' : 'Save draft'}
            </Button>
          </div>
        </div>

        <ProgressIndicator current={milestoneCount} total={3} label="Activation milestones" />

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '0.75rem' }}>
          {WIZARD_STEPS.map((step, index) => {
            const selected = index === activeStepIndex
            const completed = index < activeStepIndex
            return (
              <Button
                key={step.id}
                appearance={selected ? 'primary' : 'secondary'}
                onClick={() => goToStep(index)}
                style={{
                  minHeight: '88px',
                  justifyContent: 'flex-start',
                  alignItems: 'flex-start',
                  textAlign: 'left',
                  border: selected ? undefined : '1px solid var(--colorNeutralStroke2)',
                  background: completed && !selected ? 'var(--colorNeutralBackground2)' : undefined,
                }}
              >
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.3rem' }}>
                  <span style={{ fontSize: '0.78rem', opacity: 0.78 }}>
                    {completed ? `Step ${index + 1} completed` : `Step ${index + 1}`}
                  </span>
                  <span style={{ fontWeight: 600 }}>{step.title}</span>
                </div>
              </Button>
            )
          })}
        </div>

        {saveError ? <FeedbackMessage intent="error" title="Activation save failed" message={saveError} /> : null}

        {readOnly ? (
          <FeedbackMessage intent="warning" title="Read-only access" message="This hire has ended, so the activation workspace can be viewed but not edited." />
        ) : null}
      </Card>

      <Card style={{ padding: '1.25rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        <div>
          <div style={{ fontSize: '0.8rem', textTransform: 'uppercase', letterSpacing: '0.08em', opacity: 0.7 }}>
            Step {activeStepIndex + 1} of {WIZARD_STEPS.length}
          </div>
          <h4 style={{ margin: '0.35rem 0 0' }}>{activeStep.title}</h4>
          <div style={{ marginTop: '0.35rem', opacity: 0.8 }}>{activeStep.description}</div>
        </div>

        {activeStep.id === 'induct' ? (
          <>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '0.9rem' }}>
              <label style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                <span>Nickname</span>
                <Input aria-label="Nickname" value={nickname} onChange={(_, data) => setNickname(data.value)} disabled={readOnly} />
              </label>
              <label style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                <span>Theme</span>
                <Input aria-label="Theme" value={theme} onChange={(_, data) => setTheme(data.value)} disabled={readOnly} />
              </label>
            </div>

            <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', alignItems: 'center' }}>
              <Badge appearance="outline" color={readiness.configured ? 'success' : 'warning'}>
                {readiness.configured ? 'Agent identity configured' : 'Nickname and theme still required'}
              </Badge>
              {hiredInstanceId ? <span style={{ opacity: 0.72, fontSize: '0.9rem' }}>Hire instance: {hiredInstanceId}</span> : null}
            </div>
          </>
        ) : null}

        {activeStep.id === 'brief' ? (
          <>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '0.9rem' }}>
              <label style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                <span>Brand name</span>
                <Input aria-label="Brand name" value={brandName} onChange={(_, data) => setBrandName(data.value)} disabled={readOnly} />
              </label>
              <label style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                <span>Location</span>
                <Input aria-label="Location" value={location} onChange={(_, data) => setLocation(data.value)} disabled={readOnly} />
              </label>
              <label style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                <span>Primary language</span>
                <Input aria-label="Primary language" value={primaryLanguage} onChange={(_, data) => setPrimaryLanguage(data.value)} disabled={readOnly} />
              </label>
              <label style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                <span>Timezone</span>
                <Input aria-label="Timezone" value={timezone} onChange={(_, data) => setTimezone(data.value)} disabled={readOnly} />
              </label>
            </div>

            <label style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
              <span>Offerings and services</span>
              <Textarea
                aria-label="Offerings and services"
                value={offeringsText}
                onChange={(_, data) => setOfferingsText(data.value)}
                disabled={readOnly}
                resize="vertical"
                rows={4}
              />
            </label>

            <label style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
              <span>Business context</span>
              <Textarea
                aria-label="Business context"
                value={businessContext}
                onChange={(_, data) => setBusinessContext(data.value)}
                disabled={readOnly}
                resize="vertical"
                rows={4}
              />
            </label>

            {missingProfileFields.length > 0 ? (
              <div style={{ border: '1px solid var(--colorPaletteYellowBorder2)', borderRadius: '12px', padding: '0.85rem 1rem', background: 'var(--colorPaletteYellowBackground1)' }}>
                Add the remaining business details before the hire can be treated as fully briefed: {missingProfileFields.join(', ')}.
              </div>
            ) : (
              <Badge appearance="filled" color="success">Business brief complete</Badge>
            )}
          </>
        ) : null}

        {activeStep.id === 'channels' ? (
          <>
            <div style={{ display: 'grid', gap: '0.75rem' }}>
              {PLATFORM_OPTIONS.map((platform) => {
                const checked = selectedPlatforms.includes(platform.key)
                return (
                  <div key={platform.key} style={{ border: '1px solid var(--colorNeutralStroke2)', borderRadius: '12px', padding: '0.9rem 1rem' }}>
                    <Checkbox
                      label={platform.label}
                      checked={checked}
                      disabled={readOnly}
                      onChange={(_, data) => togglePlatform(platform.key, Boolean(data.checked))}
                    />
                    <div style={{ marginTop: '0.35rem', opacity: 0.78, paddingLeft: '1.8rem' }}>{platform.description}</div>
                  </div>
                )
              })}
            </div>

            {selectedPlatforms.includes('youtube') ? (
              <div style={{ border: '1px solid var(--colorNeutralStroke2)', borderRadius: '12px', padding: '1rem', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', gap: '1rem', flexWrap: 'wrap', alignItems: 'center' }}>
                  <div>
                    <div style={{ fontWeight: 600 }}>YouTube readiness</div>
                    <div style={{ marginTop: '0.25rem', opacity: 0.8 }}>
                      {readiness.youtube_connection_ready
                        ? 'This hire has a verified YouTube attachment.'
                        : 'This hire still needs a verified YouTube attachment before uploads can run.'}
                    </div>
                  </div>
                  <Badge appearance={readiness.youtube_connection_ready ? 'filled' : 'tint'} color={readiness.youtube_connection_ready ? 'success' : 'warning'}>
                    {readiness.youtube_connection_ready ? 'Connected' : 'Needs setup'}
                  </Badge>
                </div>

                <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
                  <Button
                    appearance="primary"
                    onClick={() => navigate(`/hire/setup/${encodeURIComponent(instance.subscription_id)}?agentId=${encodeURIComponent(instance.agent_id)}&agentTypeId=${encodeURIComponent(String(instance.agent_type_id || DIGITAL_MARKETING_AGENT_TYPE_ID))}&step=3&focus=youtube`)}
                  >
                    Open YouTube setup
                  </Button>
                  <Button appearance="secondary" onClick={() => void loadState()}>
                    I connected YouTube
                  </Button>
                </div>
              </div>
            ) : null}

            {hiredInstanceId ? (
              <div>
                <div style={{ fontWeight: 600, marginBottom: '0.4rem' }}>Platform connections</div>
                <div style={{ marginBottom: '0.65rem', opacity: 0.78 }}>
                  Use the shared platform-connection controls for any channel that needs a credential or reconnection.
                </div>
                <PlatformConnectionsPanel hiredInstanceId={hiredInstanceId} readOnly={readOnly} />
              </div>
            ) : null}
          </>
        ) : null}

        <div style={{ display: 'flex', justifyContent: 'space-between', gap: '0.75rem', flexWrap: 'wrap', paddingTop: '0.5rem' }}>
          <Button appearance="secondary" onClick={() => goToStep(activeStepIndex - 1)} disabled={activeStepIndex === 0}>
            Back
          </Button>
          {isFinalStep ? (
            <Button appearance="primary" onClick={() => void saveWorkspace()} disabled={readOnly || saveStatus === 'saving'}>
              {saveStatus === 'saving' ? 'Saving activation...' : 'Save activation'}
            </Button>
          ) : (
            <Button appearance="primary" onClick={() => goToStep(activeStepIndex + 1)}>
              Continue
            </Button>
          )}
        </div>
      </Card>

      <Card style={{ padding: '1.25rem', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', gap: '1rem', flexWrap: 'wrap', alignItems: 'center' }}>
          <div>
            <h4 style={{ margin: 0 }}>Activation readiness</h4>
            <div style={{ marginTop: '0.3rem', opacity: 0.8 }}>This comes directly from the backend readiness contract.</div>
          </div>
          <Badge appearance={readiness.can_finalize ? 'filled' : 'outline'} color={readiness.can_finalize ? 'success' : 'warning'}>
            {readiness.can_finalize ? 'Ready for runtime handoff' : 'More setup required'}
          </Badge>
        </div>

        {readiness.missing_requirements.length > 0 ? (
          <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
            {readiness.missing_requirements.map((requirement) => (
              <Badge key={requirement} appearance="tint" color="warning">
                {requirement.replace(/_/g, ' ')}
              </Badge>
            ))}
          </div>
        ) : (
          <Badge appearance="filled" color="success">All activation checks satisfied</Badge>
        )}
      </Card>
    </div>
  )
}

export default DigitalMarketingActivationWizard