import { Badge, Button, Card, Checkbox, Input, Textarea } from '@fluentui/react-components'
import { useNavigate } from 'react-router-dom'
import { useEffect, useMemo, useState } from 'react'

import { FeedbackMessage, LoadingIndicator, ProgressIndicator, SaveIndicator } from './FeedbackIndicators'
import { PlatformConnectionsPanel } from './PlatformConnectionsPanel'
import { DigitalMarketingThemePlanCard } from './DigitalMarketingThemePlanCard'
import { getHiredAgentBySubscription, upsertHiredAgentDraft, type HiredAgentInstance } from '../services/hiredAgents.service'
import type { MyAgentInstanceSummary } from '../services/myAgentsSummary.service'
import {
  buildMarketingPlatformBindings,
  generateDigitalMarketingThemePlan,
  getActivationMilestoneCount,
  getDigitalMarketingActivationWorkspace,
  getSelectedMarketingPlatforms,
  patchDigitalMarketingThemePlan,
  upsertDigitalMarketingActivationWorkspace,
  type DigitalMarketingCampaignSchedule,
  type DigitalMarketingDerivedTheme,
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

type DigitalMarketingActivationWizardProps = {
  instance?: MyAgentInstanceSummary | null
  selectedInstance?: MyAgentInstanceSummary | null
  readOnly: boolean
  onSaved?: (updated: HiredAgentInstance) => void
  onSavedInstance?: (patch: {
    nickname?: string | null
    configured?: boolean
    goals_completed?: boolean
    hired_instance_id?: string | null
    agent_type_id?: string | null
  }) => void
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

export function DigitalMarketingActivationWizard({ instance, selectedInstance, readOnly, onSaved, onSavedInstance }: DigitalMarketingActivationWizardProps) {
  const navigate = useNavigate()
  const activeInstance = instance ?? selectedInstance ?? null

  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [saveError, setSaveError] = useState<string | null>(null)
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle')
  const [showHelp, setShowHelp] = useState(false)
  const [activeMilestone, setActiveMilestone] = useState<'induct' | 'prepare' | 'theme' | 'schedule'>('induct')

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
  const [masterTheme, setMasterTheme] = useState('')
  const [derivedThemes, setDerivedThemes] = useState<DigitalMarketingDerivedTheme[]>([])
  const [themePlanLoading, setThemePlanLoading] = useState(false)
  const [themePlanSaving, setThemePlanSaving] = useState(false)
  const [themePlanError, setThemePlanError] = useState<string | null>(null)

  const hiredInstanceId = useMemo(
    () => String(draft?.hired_instance_id || activeInstance?.hired_instance_id || '').trim(),
    [draft?.hired_instance_id, activeInstance?.hired_instance_id]
  )

  const campaignSetup = activation?.workspace.campaign_setup || {}
  const schedule = campaignSetup.schedule || {}

  const applyThemePlanState = (workspace: DigitalMarketingActivationResponse['workspace'] | Record<string, unknown> | null | undefined) => {
    const resolvedWorkspace = (workspace || {}) as DigitalMarketingActivationResponse['workspace']
    const nextCampaignSetup = resolvedWorkspace.campaign_setup || {}
    setMasterTheme(String(nextCampaignSetup.master_theme || ''))
    setDerivedThemes(Array.isArray(nextCampaignSetup.derived_themes) ? nextCampaignSetup.derived_themes : [])
  }

  const loadState = async () => {
    setLoading(true)
    setError(null)
    try {
      let nextDraft: HiredAgentInstance
      try {
        if (!activeInstance?.subscription_id) {
          throw new Error('Missing subscription context for digital marketing activation.')
        }
        nextDraft = await getHiredAgentBySubscription(activeInstance.subscription_id)
      } catch (draftError: any) {
        if (draftError?.status !== 404) throw draftError
        if (!activeInstance) {
          throw new Error('Missing hired agent context for digital marketing activation.')
        }
        nextDraft = buildFallbackDraft(activeInstance)
      }

      const nextHiredInstanceId = String(nextDraft.hired_instance_id || activeInstance?.hired_instance_id || '').trim()
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
      applyThemePlanState(nextActivation?.workspace)
      setSaveStatus('idle')
      setSaveError(null)
      setThemePlanError(null)
    } catch (e: any) {
      setError(e?.message || 'Failed to load activation workspace')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (!activeInstance?.subscription_id) {
      setDraft(null)
      setActivation(null)
      setLoading(false)
      return
    }
    void loadState()
  }, [activeInstance?.subscription_id])

  const readiness = activation?.readiness || {
    brief_complete: false,
    youtube_selected: selectedPlatforms.includes('youtube'),
    youtube_connection_ready: false,
    configured: Boolean(nickname.trim() && theme.trim()),
    can_finalize: false,
    missing_requirements: [],
  }

  const milestoneCount = getActivationMilestoneCount(readiness)
  const completedMilestones = milestoneCount + (masterTheme.trim() ? 1 : 0)
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
      if (!activeInstance?.subscription_id || !activeInstance?.agent_id) {
        throw new Error('Missing hired agent context for digital marketing activation.')
      }
      const resolvedAgentTypeId = String(activeInstance.agent_type_id || draft?.agent_type_id || DIGITAL_MARKETING_AGENT_TYPE_ID).trim() || DIGITAL_MARKETING_AGENT_TYPE_ID
      const savedDraft = await upsertHiredAgentDraft({
        subscription_id: activeInstance.subscription_id,
        agent_id: activeInstance.agent_id,
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

      const refreshedDraft = await getHiredAgentBySubscription(activeInstance.subscription_id).catch(() => ({
        ...savedDraft,
        configured: savedActivation.readiness.configured,
      }))

      setDraft(refreshedDraft)
      setActivation(savedActivation)
      setSaveStatus('saved')
      onSaved?.({
        ...refreshedDraft,
        hired_instance_id: savedActivation.hired_instance_id,
        configured: savedActivation.readiness.configured,
      })
      onSavedInstance?.({
        nickname: refreshedDraft.nickname,
        configured: savedActivation.readiness.configured,
        goals_completed: refreshedDraft.goals_completed,
        hired_instance_id: savedActivation.hired_instance_id,
        agent_type_id: refreshedDraft.agent_type_id,
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

  const applyThemePlanResponse = (response: { workspace?: unknown; master_theme?: string; derived_themes?: DigitalMarketingDerivedTheme[] }) => {
    const responseWorkspace = ((response.workspace as any)?.workspace || response.workspace || {}) as DigitalMarketingActivationResponse['workspace']
    const nextWorkspace = {
      ...(activation?.workspace || {}),
      ...responseWorkspace,
      campaign_setup: {
        ...(activation?.workspace.campaign_setup || {}),
        ...(responseWorkspace?.campaign_setup || {}),
      },
    }
    setActivation((current) => {
      if (!current) return current
      return {
        ...current,
        workspace: nextWorkspace,
      }
    })
    setMasterTheme(String(response.master_theme || nextWorkspace.campaign_setup?.master_theme || ''))
    setDerivedThemes(Array.isArray(response.derived_themes) ? response.derived_themes : nextWorkspace.campaign_setup?.derived_themes || [])
  }

  const generateThemePlan = async () => {
    if (!hiredInstanceId) return
    setThemePlanLoading(true)
    setThemePlanError(null)
    try {
      const response = await generateDigitalMarketingThemePlan(hiredInstanceId, {
        campaign_setup: {
          schedule,
        },
      })
      applyThemePlanResponse(response)
      setActiveMilestone('theme')
    } catch (e: any) {
      setThemePlanError(e?.message || 'Failed to generate theme plan.')
    } finally {
      setThemePlanLoading(false)
    }
  }

  const saveThemePlan = async () => {
    if (!hiredInstanceId) return
    setThemePlanSaving(true)
    setThemePlanError(null)
    try {
      const response = await patchDigitalMarketingThemePlan(hiredInstanceId, {
        master_theme: masterTheme.trim(),
        derived_themes: derivedThemes,
        campaign_setup: {
          campaign_id: campaignSetup.campaign_id,
          schedule,
        },
      })
      applyThemePlanResponse(response)
    } catch (e: any) {
      setThemePlanError(e?.message || 'Failed to save theme plan.')
    } finally {
      setThemePlanSaving(false)
    }
  }

  const updateDerivedTheme = (index: number, field: keyof DigitalMarketingDerivedTheme, value: string) => {
    setDerivedThemes((current) =>
      current.map((theme, themeIndex) => (themeIndex === index ? { ...theme, [field]: value } : theme))
    )
  }

  const addDerivedTheme = () => {
    setDerivedThemes((current) => [...current, { title: `Derived theme ${current.length + 1}`, description: '', frequency: 'weekly' }])
  }

  if (!activeInstance) {
    return <FeedbackMessage intent="warning" title="Activation unavailable" message="Select a hired agent before opening the digital marketing activation workspace." />
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
            <Button appearance="subtle" onClick={() => setShowHelp((value) => !value)}>
              {showHelp ? 'Hide Help' : 'Show Help'}
            </Button>
            <Button appearance="secondary" onClick={() => void loadState()}>
              Refresh status
            </Button>
            <Button appearance="primary" onClick={() => void saveWorkspace()} disabled={readOnly || saveStatus === 'saving'}>
              {saveStatus === 'saving' ? 'Saving activation...' : 'Save activation'}
            </Button>
          </div>
        </div>

        <ProgressIndicator current={completedMilestones} total={4} label="Activation milestones" />

        <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
          {[
            ['induct', 'Induct Agent'],
            ['prepare', 'Prepare Agent'],
            ['theme', 'Master Theme'],
            ['schedule', 'Confirm Schedule'],
          ].map(([key, label]) => (
            <Button
              key={key}
              appearance={activeMilestone === key ? 'primary' : 'secondary'}
              onClick={() => setActiveMilestone(key as 'induct' | 'prepare' | 'theme' | 'schedule')}
            >
              {label}
            </Button>
          ))}
        </div>

        {showHelp ? (
          <div data-testid="dma-help-panel-primary" style={{ border: '1px solid var(--colorNeutralStroke2)', borderRadius: '12px', padding: '0.9rem 1rem', lineHeight: 1.6, background: 'var(--colorNeutralBackground2)' }}>
            Save this workspace whenever you update the business brief or channel choices. If YouTube is selected, use the setup shortcut below once and then refresh this page so the backend can verify the channel attachment for this hire.
          </div>
        ) : null}

        {saveError ? <FeedbackMessage intent="error" title="Activation save failed" message={saveError} /> : null}

        {readOnly ? (
          <FeedbackMessage intent="warning" title="Read-only access" message="This hire has ended, so the activation workspace can be viewed but not edited." />
        ) : null}
      </Card>

      <Card style={{ padding: '1.25rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        <div>
          <div style={{ fontSize: '0.8rem', textTransform: 'uppercase', letterSpacing: '0.08em', opacity: 0.7 }}>Step 1</div>
          <h4 style={{ margin: '0.35rem 0 0' }}>Induct Agent</h4>
          <div style={{ marginTop: '0.35rem', opacity: 0.8 }}>Set the identity this customer will see and preserve the draft-backed configured state.</div>
        </div>

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
      </Card>

      <Card style={{ padding: '1.25rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        <div>
          <div style={{ fontSize: '0.8rem', textTransform: 'uppercase', letterSpacing: '0.08em', opacity: 0.7 }}>Step 2</div>
          <h4 style={{ margin: '0.35rem 0 0' }}>Capture business brief</h4>
          <div style={{ marginTop: '0.35rem', opacity: 0.8 }}>These fields feed the marketing brief that the backend materializes into the hired-agent config.</div>
        </div>

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
      </Card>

      <Card style={{ padding: '1.25rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        <div>
          <div style={{ fontSize: '0.8rem', textTransform: 'uppercase', letterSpacing: '0.08em', opacity: 0.7 }}>Step 3</div>
          <h4 style={{ margin: '0.35rem 0 0' }}>Prepare agent channels</h4>
          <div style={{ marginTop: '0.35rem', opacity: 0.8 }}>Choose where the agent will work, then attach the channel credentials the backend needs to verify.</div>
        </div>

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
                onClick={() => navigate(`/hire/setup/${encodeURIComponent(activeInstance.subscription_id)}?agentId=${encodeURIComponent(activeInstance.agent_id)}&agentTypeId=${encodeURIComponent(String(activeInstance.agent_type_id || DIGITAL_MARKETING_AGENT_TYPE_ID))}&step=3&focus=youtube`)}
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
      </Card>

      <Card style={{ padding: '1.25rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        <div>
          <div style={{ fontSize: '0.8rem', textTransform: 'uppercase', letterSpacing: '0.08em', opacity: 0.7 }}>Step 4</div>
          <h4 style={{ margin: '0.35rem 0 0' }}>Master Theme</h4>
          <div style={{ marginTop: '0.35rem', opacity: 0.8 }}>Generate a persisted campaign theme plan, review the derived themes, and save manual revisions back through the activation API.</div>
        </div>

        {showHelp ? (
          <div data-testid="dma-help-panel-secondary" style={{ border: '1px solid var(--colorNeutralStroke2)', borderRadius: '12px', padding: '0.9rem 1rem', lineHeight: 1.6, background: 'var(--colorNeutralBackground2)' }}>
            Generate a first draft from the saved induction brief, then edit the master theme or derived themes before saving. Use Refresh status after saving to confirm the persisted plan reloads from the backend.
          </div>
        ) : null}

        {themePlanLoading ? <LoadingIndicator message="Generating theme plan..." size="small" /> : null}
        {!themePlanLoading && themePlanError ? <FeedbackMessage intent="error" title="Theme plan unavailable" message={themePlanError} /> : null}

        {!themePlanLoading ? (
          <DigitalMarketingThemePlanCard
            masterTheme={masterTheme}
            derivedThemes={derivedThemes}
            editable={!readOnly}
            saving={themePlanSaving}
            error={themePlanError}
            onMasterThemeChange={setMasterTheme}
            onDerivedThemeChange={updateDerivedTheme}
            onAddDerivedTheme={addDerivedTheme}
            onGenerate={() => void generateThemePlan()}
            onRegenerate={masterTheme.trim() || derivedThemes.length > 0 ? () => void generateThemePlan() : undefined}
            onSave={() => void saveThemePlan()}
          />
        ) : null}
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