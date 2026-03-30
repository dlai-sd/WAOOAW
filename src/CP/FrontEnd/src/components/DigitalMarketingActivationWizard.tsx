import { Badge, Button, Card, CardHeader, Spinner, Text, Input, Textarea } from '@fluentui/react-components'
import { useNavigate } from 'react-router-dom'
import { useEffect, useMemo, useState } from 'react'

import { FeedbackMessage, LoadingIndicator, SaveIndicator } from './FeedbackIndicators'
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
  type UpsertDigitalMarketingActivationInput,
} from '../services/digitalMarketingActivation.service'
import {
  startYouTubeConnection,
  finalizeYouTubeConnection,
  attachYouTubeConnection,
  listYouTubeConnections,
  type YouTubeConnection,
} from '../services/youtubeConnections.service'
import { redirectTo } from '../utils/browserNavigation'

const DIGITAL_MARKETING_AGENT_TYPE_ID = 'marketing.digital_marketing.v1'

const DMA_STEPS = [
  { id: 'select',    title: 'Select Agent',         description: 'Choose which hired agent to configure.' },
  { id: 'induct',    title: 'Induct Agent',          description: 'Set the agent nickname and brand identity.' },
  { id: 'platforms', title: 'Choose Platforms',      description: 'Select which social channels this agent will manage.' },
  { id: 'connect',   title: 'Connect Platforms',     description: 'Authorise each selected platform channel.' },
  { id: 'theme',     title: 'Build Master Theme',    description: 'Define brand brief and generate an AI content strategy.' },
  { id: 'schedule',  title: 'Confirm Schedule',      description: 'Set posting frequency and preferred days.' },
  { id: 'activate',  title: 'Review & Activate',     description: 'Check readiness then activate the agent.' },
] as const

const PLATFORM_OPTIONS = [
  { key: 'youtube', label: 'YouTube', description: 'Channel uploads and video publishing approvals.' },
  { key: 'instagram', label: 'Instagram', description: 'Reels, posts, and story publishing workflows.' },
  { key: 'facebook', label: 'Facebook', description: 'Page posting and distribution.' },
  { key: 'linkedin', label: 'LinkedIn', description: 'Thought leadership and company-page posts.' },
  { key: 'whatsapp', label: 'WhatsApp', description: 'Outbound campaign and customer follow-up content.' },
  { key: 'x', label: 'X', description: 'Short-form social publishing and promotion.' },
]


function isNotFoundError(error: unknown): error is { status: number } {
  return Boolean(error) && typeof error === 'object' && Number((error as { status?: number }).status) === 404
}

function buildEmptyActivationResponse(
  hiredInstanceId: string,
  agentTypeId: string,
): DigitalMarketingActivationResponse {
  return {
    hired_instance_id: hiredInstanceId,
    customer_id: null,
    agent_type_id: agentTypeId,
    workspace: {
      help_visible: false,
      activation_complete: false,
      brand_name: '',
      location: '',
      primary_language: '',
      timezone: '',
      business_context: '',
      offerings_services: [],
      platforms_enabled: [],
      platform_bindings: {},
      campaign_setup: {
        campaign_id: null,
        master_theme: '',
        derived_themes: [],
        schedule: {
          start_date: '',
          posts_per_week: 0,
          preferred_days: [],
          preferred_hours_utc: [],
        },
      },
    },
    readiness: {
      brief_complete: false,
      youtube_selected: false,
      youtube_connection_ready: false,
      configured: false,
      can_finalize: false,
      missing_requirements: [],
    },
    updated_at: new Date().toISOString(),
  }
}
type DigitalMarketingActivationWizardProps = {
  instances?: MyAgentInstanceSummary[]
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
  onStaleReference?: (details: { subscriptionId: string; hiredInstanceId?: string | null }) => void | Promise<void>
  onSelectedInstanceChange?: (subscriptionId: string) => void
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

function parseHourList(value: string): number[] {
  return String(value || '')
    .split(/\n|,/g)
    .map((entry) => Number(entry.trim()))
    .filter((entry) => Number.isFinite(entry) && entry >= 0 && entry <= 23)
}

function formatHours(value: unknown): string {
  return Array.isArray(value) ? value.map((entry) => String(entry)).join(', ') : ''
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

export function DigitalMarketingActivationWizard({
  instances = [],
  instance,
  selectedInstance,
  readOnly,
  onSaved,
  onSavedInstance,
  onStaleReference,
  onSelectedInstanceChange,
}: DigitalMarketingActivationWizardProps) {
  const navigate = useNavigate()
  const activeInstance = instance ?? selectedInstance ?? null

  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [saveError, setSaveError] = useState<string | null>(null)
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle')
  const [showHelp, setShowHelp] = useState(false)
  const [activeMilestone, setActiveMilestone] = useState<'induct' | 'prepare' | 'theme' | 'schedule'>('induct')
  const [activeStepIndex, setActiveStepIndex] = useState(0)
  const currentStep = DMA_STEPS[activeStepIndex]

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
  const [scheduleStartDate, setScheduleStartDate] = useState('')
  const [postsPerWeek, setPostsPerWeek] = useState('')
  const [preferredDaysText, setPreferredDaysText] = useState('')
  const [preferredHoursText, setPreferredHoursText] = useState('')
  const [finishStatus, setFinishStatus] = useState<'idle' | 'saving' | 'success' | 'error'>('idle')
  const [finishError, setFinishError] = useState<string | null>(null)
  const [youtubeConnected, setYoutubeConnected] = useState(false)
  const [savedYouTubeConnection, setSavedYouTubeConnection] = useState<YouTubeConnection | null>(null)
  const [oauthLoading, setOauthLoading] = useState(false)
  const [oauthError, setOauthError] = useState<string | null>(null)
  const [oauthMessage, setOauthMessage] = useState<string | null>(null)

  const hiredInstanceId = useMemo(
    () => String(draft?.hired_instance_id || activeInstance?.hired_instance_id || '').trim(),
    [draft?.hired_instance_id, activeInstance?.hired_instance_id]
  )

  const youtubeSkillId = useMemo(() => {
    const binding = activation?.workspace?.platform_bindings?.youtube
    return String(binding?.skill_id || 'default').trim() || 'default'
  }, [activation?.workspace?.platform_bindings])

  function pickReusableYouTubeConnection(connections: YouTubeConnection[]): YouTubeConnection | null {
    const now = Date.now()
    for (const connection of connections) {
      if (String(connection.platform_key || '').toLowerCase() !== 'youtube') continue
      if (String(connection.connection_status || '').toLowerCase() !== 'connected') continue
      const tokenExpiry = connection.token_expires_at ? Date.parse(connection.token_expires_at) : Number.NaN
      if (Number.isFinite(tokenExpiry) && tokenExpiry <= now) continue
      return connection
    }
    return null
  }

  function markYouTubeConnected(connection: YouTubeConnection | null, successMessage: string) {
    setSavedYouTubeConnection(connection)
    setYoutubeConnected(true)
    setOauthMessage(successMessage)
    setOauthError(null)
    setActivation((current) => {
      if (!current) return current
      return {
        ...current,
        workspace: {
          ...current.workspace,
          platform_bindings: {
            ...(current.workspace.platform_bindings || {}),
            youtube: {
              ...(current.workspace.platform_bindings?.youtube || {}),
              skill_id: youtubeSkillId,
              customer_platform_credential_id: connection?.id,
              credential_id: connection?.id,
              connected: true,
            },
          },
        },
        readiness: {
          ...current.readiness,
          youtube_connection_ready: true,
        },
      }
    })
  }

  // Auto-select + advance if only one instance and we are on step 0
  useEffect(() => {
    if (activeStepIndex === 0 && instances.length === 1) {
      onSelectedInstanceChange?.(instances[0].subscription_id)
      setActiveStepIndex(1)
    }
  }, [instances, activeStepIndex, onSelectedInstanceChange])

  // OAuth callback — detect ?code&state on mount and finalize connection
  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const code = params.get('code')
    const state = params.get('state')
    if (!code || !state) return

    const storedState = sessionStorage.getItem('yt_oauth_state')
    if (!storedState || storedState !== state) {
      // State mismatch — do not process (CSRF protection)
      return
    }

    const redirectUri = window.location.origin + window.location.pathname
    const hiredInstanceIdForOauth = String(activeInstance?.hired_instance_id || hiredInstanceId || '').trim()
    if (!hiredInstanceIdForOauth) return

    ;(async () => {
      try {
        setOauthLoading(true)
        setOauthMessage(null)
        const connection = await finalizeYouTubeConnection({ state, code, redirect_uri: redirectUri })
        await attachYouTubeConnection(connection.id, {
          hired_instance_id: hiredInstanceIdForOauth,
          skill_id: youtubeSkillId,
        })
        sessionStorage.removeItem('yt_oauth_state')
        window.history.replaceState({}, '', window.location.pathname)
        markYouTubeConnected(connection, 'YouTube connected successfully.')
        setActiveStepIndex(DMA_STEPS.findIndex((s) => s.id === 'connect'))
      } catch (err) {
        setOauthError('YouTube connection failed. Please try again.')
      } finally {
        setOauthLoading(false)
      }
    })()
  }, [activeInstance?.hired_instance_id, hiredInstanceId, youtubeSkillId])

  // Load existing saved YouTube connections for this customer
  useEffect(() => {
    listYouTubeConnections()
      .then((connections) => {
        setSavedYouTubeConnection(pickReusableYouTubeConnection(connections))
      })
      .catch(() => {
        setSavedYouTubeConnection(null)
      })
  }, [])

  useEffect(() => {
    setYoutubeConnected(Boolean(activation?.readiness?.youtube_connection_ready))
  }, [activation?.readiness?.youtube_connection_ready])

  const campaignSetup = activation?.workspace.campaign_setup || {}
  const schedule = campaignSetup.schedule || {}

  const normalizedSchedule: DigitalMarketingCampaignSchedule = {
    start_date: scheduleStartDate.trim(),
    posts_per_week: Math.max(Number(postsPerWeek || 0), 0),
    preferred_days: parseListTextarea(preferredDaysText),
    preferred_hours_utc: parseHourList(preferredHoursText),
  }

  const applyThemePlanState = (workspace: DigitalMarketingActivationResponse['workspace'] | Record<string, unknown> | null | undefined) => {
    const resolvedWorkspace = (workspace || {}) as DigitalMarketingActivationResponse['workspace']
    const nextCampaignSetup = resolvedWorkspace.campaign_setup || {}
    const nextSchedule = nextCampaignSetup.schedule || {}
    setMasterTheme(String(nextCampaignSetup.master_theme || ''))
    setDerivedThemes(Array.isArray(nextCampaignSetup.derived_themes) ? nextCampaignSetup.derived_themes : [])
    setScheduleStartDate(String(nextSchedule.start_date || ''))
    setPostsPerWeek(String(nextSchedule.posts_per_week || ''))
    setPreferredDaysText(Array.isArray(nextSchedule.preferred_days) ? nextSchedule.preferred_days.join(', ') : '')
    setPreferredHoursText(formatHours(nextSchedule.preferred_hours_utc))
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
      const resolvedAgentTypeId = String(nextDraft.agent_type_id || activeInstance?.agent_type_id || DIGITAL_MARKETING_AGENT_TYPE_ID).trim() || DIGITAL_MARKETING_AGENT_TYPE_ID
      let nextActivation: DigitalMarketingActivationResponse | null = buildEmptyActivationResponse(nextHiredInstanceId, resolvedAgentTypeId)
      if (nextHiredInstanceId) {
        try {
          nextActivation = await getDigitalMarketingActivationWorkspace(nextHiredInstanceId)
        } catch (activationError: any) {
          if (!isNotFoundError(activationError)) throw activationError
          nextActivation = buildEmptyActivationResponse(nextHiredInstanceId, resolvedAgentTypeId)
        }
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
      setFinishStatus('idle')
      setFinishError(null)
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
  const canFinish = Boolean(masterTheme.trim()) && Boolean(scheduleStartDate.trim()) && Boolean(readiness.can_finalize)
  const missingProfileFields = useMemo(() => {
    const items: string[] = []
    if (!brandName.trim()) items.push('brand name')
    if (!location.trim()) items.push('location')
    if (!primaryLanguage.trim()) items.push('primary language')
    if (!timezone.trim()) items.push('timezone')
    if (parseListTextarea(offeringsText).length === 0) items.push('offerings and services')
    return items
  }, [brandName, location, offeringsText, primaryLanguage, timezone])

  const saveActivationWorkspaceWithRecovery = async (
    initialHiredInstanceId: string,
    payload: UpsertDigitalMarketingActivationInput,
  ): Promise<{ activation: DigitalMarketingActivationResponse; draft: HiredAgentInstance | null }> => {
    try {
      const savedActivation = await upsertDigitalMarketingActivationWorkspace(initialHiredInstanceId, payload)
      return { activation: savedActivation, draft: null }
    } catch (error: any) {
      if (!isNotFoundError(error) || !activeInstance?.subscription_id) {
        throw error
      }

      const refreshedDraft = await getHiredAgentBySubscription(activeInstance.subscription_id)
      const refreshedHiredInstanceId = String(refreshedDraft?.hired_instance_id || '').trim()
      if (!refreshedHiredInstanceId || refreshedHiredInstanceId === initialHiredInstanceId) {
        throw error
      }

      const savedActivation = await upsertDigitalMarketingActivationWorkspace(refreshedHiredInstanceId, payload)
      return { activation: savedActivation, draft: refreshedDraft }
    }
  }

  const saveWorkspace = async (): Promise<boolean> => {
    if (readOnly) return true

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

      const activationPayload: UpsertDigitalMarketingActivationInput = {
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
      }

      const { activation: savedActivation, draft: recoveredDraft } = await saveActivationWorkspaceWithRecovery(
        savedDraft.hired_instance_id,
        activationPayload,
      )

      const refreshedDraft = await getHiredAgentBySubscription(activeInstance.subscription_id).catch(() => ({
        ...savedDraft,
        ...(recoveredDraft || {}),
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
      return true
    } catch (e: any) {
      if (isNotFoundError(e)) {
        const message = 'This hire is no longer available. Please select another agent.'
        setSaveError(message)
        setSaveStatus('error')
        await onStaleReference?.({
          subscriptionId: activeInstance?.subscription_id || '',
          hiredInstanceId,
        })
        return false
      }
      setSaveError(e?.message || 'Failed to save activation workspace')
      setSaveStatus('error')
      return false
    }
  }

  async function handleContinue() {
    if (currentStep.id !== 'select') {
      const saved = await saveWorkspace()
      if (!saved) return
    }
    setActiveStepIndex(i => Math.min(DMA_STEPS.length - 1, i + 1))
  }

  async function handleConnectYouTube() {
    setOauthLoading(true)
    setOauthError(null)
    setOauthMessage(null)
    try {
      if (!hiredInstanceId) {
        setOauthError('This agent is not ready yet. Please reload the page and try again.')
        return
      }

      const knownConnection = savedYouTubeConnection || pickReusableYouTubeConnection(await listYouTubeConnections())
      if (knownConnection) {
        try {
          await attachYouTubeConnection(knownConnection.id, {
            hired_instance_id: hiredInstanceId,
            skill_id: youtubeSkillId,
          })
          markYouTubeConnected(knownConnection, 'Saved YouTube connection linked successfully.')
          return
        } catch {
          setSavedYouTubeConnection(null)
        }
      }

      const redirectUri = window.location.origin + window.location.pathname
      const { state, authorization_url } = await startYouTubeConnection(redirectUri)
      sessionStorage.setItem('yt_oauth_state', state)
      redirectTo(authorization_url)
    } catch (err) {
      setOauthError('Could not start YouTube connection. Please try again.')
    } finally {
      setOauthLoading(false)
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
          schedule: normalizedSchedule,
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
          schedule: normalizedSchedule,
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

  const finishActivation = async () => {
    if (!hiredInstanceId || readOnly) return
    setFinishStatus('saving')
    setFinishError(null)
    try {
      const activationPayload: UpsertDigitalMarketingActivationInput = {
        workspace: {
          ...(activation?.workspace || {}),
          help_visible: showHelp,
          activation_complete: true,
          platforms_enabled: selectedPlatforms,
          campaign_setup: {
            campaign_id: campaignSetup.campaign_id,
            master_theme: masterTheme.trim(),
            derived_themes: derivedThemes,
            schedule: normalizedSchedule,
          },
        },
      }

      const { activation: savedActivation, draft: recoveredDraft } = await saveActivationWorkspaceWithRecovery(
        hiredInstanceId,
        activationPayload,
      )

      setActivation(savedActivation)
      applyThemePlanState(savedActivation.workspace)
      setFinishStatus('success')

      const resolvedDraft = recoveredDraft || draft
      const updatedDraft = resolvedDraft
        ? {
            ...resolvedDraft,
            configured: true,
            goals_completed: true,
            hired_instance_id: savedActivation.hired_instance_id,
          }
        : null

      if (updatedDraft) {
        setDraft(updatedDraft)
        onSaved?.(updatedDraft)
      }
      onSavedInstance?.({
        configured: true,
        goals_completed: true,
        hired_instance_id: savedActivation.hired_instance_id,
        agent_type_id: activeInstance?.agent_type_id || DIGITAL_MARKETING_AGENT_TYPE_ID,
      })
      setActiveMilestone('schedule')
    } catch (e: any) {
      if (isNotFoundError(e)) {
        const message = 'This hire is no longer available. Please select another agent.'
        setFinishStatus('error')
        setFinishError(message)
        await onStaleReference?.({
          subscriptionId: activeInstance?.subscription_id || '',
          hiredInstanceId,
        })
        return
      }
      setFinishStatus('error')
      setFinishError(e?.message || 'Failed to finish activation.')
    }
  }

  if (!activeInstance && (currentStep.id !== 'select' || instances.length === 0)) {
    return <FeedbackMessage intent="warning" title="Activation unavailable" message="Select a hired agent before opening the digital marketing activation workspace." />
  }

  if (loading && currentStep.id !== 'select') {
    return <LoadingIndicator message="Loading digital marketing activation..." size="medium" />
  }

  if (error && currentStep.id !== 'select') {
    return <FeedbackMessage intent="error" title="Activation unavailable" message={error} action={{ label: 'Retry', onClick: () => void loadState() }} />
  }

  return (
    <div className="dma-wizard-page">
      <div className="dma-wizard-shell">
        {/* LEFT RAIL */}
        <aside className="dma-wizard-rail">
          <Card className="dma-wizard-rail-card">
            <Text as="h2" size={500} weight="semibold">Activation steps</Text>
            <div className="dma-wizard-step-list">
              {DMA_STEPS.map((step, index) => {
                const isActive = index === activeStepIndex
                const isDone = index < activeStepIndex
                return (
                  <button
                    key={step.id}
                    type="button"
                    className={`dma-wizard-step-button${isActive ? ' is-active' : ''}${isDone ? ' is-done' : ''}`}
                    onClick={() => setActiveStepIndex(index)}
                  >
                    <span className="dma-wizard-step-index">0{index + 1}</span>
                    <span className="dma-wizard-step-copy">
                      <span className="dma-wizard-step-title">{step.title}</span>
                      <span className="dma-wizard-step-description">{step.description}</span>
                    </span>
                    {isDone ? <span className="dma-wizard-step-state dma-wizard-step-state--done">Done</span> : null}
                    {isActive ? <span className="dma-wizard-step-state dma-wizard-step-state--active">Now</span> : null}
                  </button>
                )
              })}
            </div>
          </Card>
        </aside>

        {/* CANVAS */}
        <section className="dma-wizard-canvas">
          <Card className="dma-wizard-canvas-card">
            {/* STICKY HEADER */}
            <div className="dma-wizard-canvas-header">
              <CardHeader
                className="dma-wizard-canvas-header-card"
                header={
                  <div>
                    <Text as="h2" size={600} weight="semibold">{currentStep.title}</Text>
                    <Text as="p" size={300}>{currentStep.description}</Text>
                  </div>
                }
              />
            </div>

            {/* SCROLLABLE BODY */}
            <div className="dma-wizard-canvas-body">

              {/* STEP 0 — Select Agent */}
              {currentStep.id === 'select' && (
                <div data-testid="dma-step-panel-select" className="dma-wizard-canvas-body-inner">
                  {instances.length === 0 ? (
                    <div>No agents found.</div>
                  ) : (
                    <div className="dma-wizard-agent-select-grid">
                      {instances.map((inst) => (
                        <button
                          key={inst.subscription_id}
                          type="button"
                          className={`dma-wizard-agent-card${inst.subscription_id === activeInstance?.subscription_id ? ' is-selected' : ''}`}
                          onClick={() => {
                            onSelectedInstanceChange?.(inst.subscription_id)
                            setActiveStepIndex(1)
                          }}
                        >
                          <div className="dma-wizard-agent-card-name">
                            {inst.nickname || inst.agent_id}
                          </div>
                          <div className="dma-wizard-agent-card-meta">
                            {inst.status}
                          </div>
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* STEP 1 — Induct Agent */}
              {currentStep.id === 'induct' && (
                <div className="dma-wizard-step-content" data-testid="dma-step-panel-induct">
                  <div style={{ display: 'grid', gap: '1.25rem' }}>
                    <div>
                      <div className="dma-wizard-section-label">Agent identity</div>
                      <div className="dma-wizard-form-grid">
                        <label style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                          <span>Nickname</span>
                          <Input
                            aria-label="Nickname"
                            value={nickname}
                            onChange={(_, data) => setNickname(data.value)}
                            disabled={readOnly}
                            placeholder="e.g. Growth Copilot"
                          />
                        </label>
                        <label style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                          <span>Theme</span>
                          <Input
                            aria-label="Theme"
                            value={theme}
                            onChange={(_, data) => setTheme(data.value)}
                            disabled={readOnly}
                            placeholder="e.g. dark"
                          />
                        </label>
                      </div>
                    </div>
                    <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap', alignItems: 'center' }}>
                      <Badge appearance="outline" color={readiness.configured ? 'success' : 'warning'}>
                        {readiness.configured ? 'Identity configured ✓' : 'Nickname and theme required'}
                      </Badge>
                      {hiredInstanceId ? (
                        <span style={{ opacity: 0.65, fontSize: '0.85rem' }}>
                          Hire ID: {hiredInstanceId}
                        </span>
                      ) : null}
                    </div>
                  </div>
                </div>
              )}

              {/* STEP 2 — Choose Platforms */}
              {currentStep.id === 'platforms' && (
                <div className="dma-wizard-step-content" data-testid="dma-step-panel-platforms">
                  <div style={{ display: 'grid', gap: '1.25rem' }}>
                    <div>
                      <div className="dma-wizard-section-label">Select the channels for this agent to manage</div>
                      <div className="dma-wizard-platform-grid">
                        {[
                          { key: 'youtube',   label: 'YouTube' },
                          { key: 'instagram', label: 'Instagram' },
                          { key: 'facebook',  label: 'Facebook' },
                          { key: 'linkedin',  label: 'LinkedIn' },
                          { key: 'whatsapp',  label: 'WhatsApp' },
                          { key: 'x',        label: 'X (Twitter)' },
                        ].map(({ key, label }) => {
                          const isSelected = selectedPlatforms.includes(key)
                          return (
                            <button
                              key={key}
                              type="button"
                              className={`dma-wizard-platform-card${isSelected ? ' is-selected' : ''}`}
                              onClick={() => {
                                if (readOnly) return
                                setSelectedPlatforms(prev =>
                                  isSelected ? prev.filter(p => p !== key) : [...prev, key]
                                )
                              }}
                              disabled={readOnly}
                              aria-pressed={isSelected}
                              data-testid={`platform-toggle-${key}`}
                            >
                              <span style={{ fontWeight: 600 }}>{label}</span>
                              {isSelected ? <span style={{ color: '#00f2fe', marginLeft: 'auto' }}>✓</span> : null}
                            </button>
                          )
                        })}
                      </div>
                    </div>
                    {selectedPlatforms.length > 0 ? (
                      <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                        {selectedPlatforms.map(p => (
                          <Badge key={p} appearance="outline" color="informative">{p}</Badge>
                        ))}
                      </div>
                    ) : (
                      <div style={{ opacity: 0.6, fontSize: '0.9rem' }}>Select at least one platform to continue.</div>
                    )}
                  </div>
                </div>
              )}

              {/* STEP 3 — Connect Platforms */}
              {currentStep.id === 'connect' && (
                <div data-testid="dma-step-panel-connect" className="dma-wizard-canvas-body-inner">
                  <div className="dma-wizard-platform-connect-list">

                    {/* YouTube */}
                    <div className="dma-wizard-platform-connect-row">
                      <div className="dma-wizard-platform-connect-info">
                        <span className="dma-wizard-platform-connect-name">YouTube</span>
                        <span className="dma-wizard-platform-connect-desc">
                          Connect your YouTube channel to allow the agent to manage uploads and publishing.
                        </span>
                      </div>
                      <div className="dma-wizard-platform-connect-action">
                        {youtubeConnected ? (
                          <span className="dma-wizard-connected-badge">✓ Connected</span>
                        ) : (
                          <Button
                            appearance="primary"
                            disabled={oauthLoading || readOnly}
                            onClick={() => void handleConnectYouTube()}
                          >
                            {oauthLoading
                              ? 'Connecting…'
                              : savedYouTubeConnection
                                ? 'Use saved YouTube connection'
                                : 'Connect with Google'}
                          </Button>
                        )}
                      </div>
                    </div>

                    {oauthMessage && (
                      <div className="dma-wizard-oauth-success">{oauthMessage}</div>
                    )}

                    {oauthError && (
                      <div className="dma-wizard-oauth-error">{oauthError}</div>
                    )}

                    {/* Other platforms */}
                    {(['Instagram', 'Facebook', 'LinkedIn', 'WhatsApp', 'X'] as const).map((name) => (
                      <div key={name} className="dma-wizard-platform-connect-row dma-wizard-platform-connect-row--disabled">
                        <div className="dma-wizard-platform-connect-info">
                          <span className="dma-wizard-platform-connect-name">{name}</span>
                        </div>
                        <div className="dma-wizard-platform-connect-action">
                          <span className="dma-wizard-coming-soon-badge">Unavailable</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* STEP 4 — Build Master Theme */}
              {currentStep.id === 'theme' && (
                <div className="dma-wizard-step-content" data-testid="dma-step-panel-theme">
                  <div style={{ display: 'grid', gap: '1.75rem' }}>
                    {/* Business brief */}
                    <div>
                      <div className="dma-wizard-section-label">Business brief</div>
                      <div className="dma-wizard-form-grid" style={{ marginBottom: '0.85rem' }}>
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
                          <Input aria-label="Timezone" value={timezone} onChange={(_, data) => setTimezone(data.value)} disabled={readOnly} placeholder="e.g. Asia/Kolkata" />
                        </label>
                      </div>
                      <label style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem', marginBottom: '0.85rem' }}>
                        <span>Offerings and services</span>
                        <Textarea
                          aria-label="Offerings and services"
                          value={offeringsText}
                          onChange={(_, data) => setOfferingsText(data.value)}
                          disabled={readOnly}
                          resize="vertical"
                          rows={3}
                          placeholder="Comma-separated list of what you sell or offer"
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
                          rows={3}
                          placeholder="Describe your business, target audience, key differentiators"
                        />
                      </label>
                    </div>

                    {/* AI theme generation */}
                    <div>
                      <div className="dma-wizard-section-label">AI-generated content strategy</div>
                      <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center', marginBottom: '1rem' }}>
                        <Button
                          appearance="primary"
                          onClick={() => void generateThemePlan()}
                          disabled={readOnly || themePlanLoading || !brandName.trim()}
                        >
                          {themePlanLoading ? 'Generating…' : 'Generate with AI'}
                        </Button>
                        {themePlanLoading ? <Spinner size="tiny" /> : null}
                        {!brandName.trim() ? <span style={{ opacity: 0.6, fontSize: '0.85rem' }}>Enter brand name first</span> : null}
                      </div>
                      {masterTheme ? (
                        <div style={{ display: 'grid', gap: '1rem' }}>
                          <label style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                            <span style={{ fontWeight: 600 }}>Master theme</span>
                            <Input
                              aria-label="Master theme"
                              value={masterTheme}
                              onChange={(_, data) => setMasterTheme(data.value)}
                              disabled={readOnly}
                            />
                          </label>
                          {derivedThemes.length > 0 ? (
                            <div>
                              <div style={{ fontWeight: 600, marginBottom: '0.5rem' }}>Derived themes ({derivedThemes.length})</div>
                              <div style={{ display: 'grid', gap: '0.6rem' }}>
                                {derivedThemes.map((dt, idx) => (
                                  <div key={idx} style={{ padding: '0.75rem', border: '1px solid var(--colorNeutralStroke2)', borderRadius: '10px', background: 'rgba(255,255,255,0.03)' }}>
                                    <div style={{ fontWeight: 600 }}>{dt.title}</div>
                                    {dt.description ? <div style={{ opacity: 0.75, fontSize: '0.85rem', marginTop: '0.2rem' }}>{dt.description}</div> : null}
                                    {dt.frequency ? <div style={{ opacity: 0.5, fontSize: '0.78rem', marginTop: '0.2rem' }}>Frequency: {dt.frequency}</div> : null}
                                  </div>
                                ))}
                              </div>
                            </div>
                          ) : null}
                        </div>
                      ) : (
                        <div style={{ opacity: 0.6, fontSize: '0.9rem' }}>
                          Fill in the brief above then click &ldquo;Generate with AI&rdquo; to create a tailored content strategy.
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )}

              {/* STEP 5 — Confirm Schedule */}
              {currentStep.id === 'schedule' && (
                <div className="dma-wizard-step-content" data-testid="dma-step-panel-schedule">
                  <div style={{ display: 'grid', gap: '1.25rem' }}>
                    <div>
                      <div className="dma-wizard-section-label">Posting schedule</div>
                      <div className="dma-wizard-form-grid">
                        <label style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                          <span>Start date</span>
                          <Input
                            type="date"
                            aria-label="Start date"
                            value={scheduleStartDate}
                            onChange={(_, data) => setScheduleStartDate(data.value)}
                            disabled={readOnly}
                          />
                        </label>
                        <label style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                          <span>Posts per week</span>
                          <Input
                            type="number"
                            aria-label="Posts per week"
                            value={postsPerWeek}
                            onChange={(_, data) => setPostsPerWeek(data.value)}
                            disabled={readOnly}
                            min="1"
                            max="21"
                          />
                        </label>
                      </div>
                    </div>
                    <div>
                      <div className="dma-wizard-section-label">Preferred days</div>
                      <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                        {['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].map((day) => {
                          const selectedDays = parseListTextarea(preferredDaysText)
                          const isSelected = selectedDays.includes(day)
                          return (
                            <button
                              key={day}
                              type="button"
                              style={{
                                padding: '0.4rem 0.9rem',
                                borderRadius: '999px',
                                border: `1px solid ${isSelected ? 'rgba(0,242,254,0.5)' : 'var(--colorNeutralStroke2)'}`,
                                background: isSelected ? 'rgba(0,242,254,0.1)' : 'rgba(255,255,255,0.03)',
                                color: 'inherit',
                                cursor: readOnly ? 'default' : 'pointer',
                                fontWeight: isSelected ? 700 : 400,
                              }}
                              onClick={() => {
                                if (readOnly) return
                                const current = parseListTextarea(preferredDaysText)
                                const next = isSelected ? current.filter(d => d !== day) : [...current, day]
                                setPreferredDaysText(next.join(', '))
                              }}
                              aria-pressed={isSelected}
                            >
                              {day}
                            </button>
                          )
                        })}
                      </div>
                    </div>
                    {scheduleStartDate ? (
                      <Badge appearance="outline" color="success">
                        Schedule set: {postsPerWeek || '3'}×/week from {scheduleStartDate}
                      </Badge>
                    ) : (
                      <div style={{ opacity: 0.6, fontSize: '0.9rem' }}>Set a start date to confirm the schedule.</div>
                    )}
                  </div>
                </div>
              )}

              {/* STEP 6 — Review & Activate */}
              {currentStep.id === 'activate' && (
                <div className="dma-wizard-step-content" data-testid="dma-step-panel-activate">
                  <div style={{ display: 'grid', gap: '1.5rem' }}>
                    {/* Readiness checklist */}
                    <div>
                      <div className="dma-wizard-section-label">Activation readiness</div>
                      <div style={{ border: '1px solid var(--colorNeutralStroke2)', borderRadius: '14px', overflow: 'hidden' }}>
                        {[
                          { label: 'Agent identity configured',   ok: readiness.configured },
                          { label: 'Business brief complete',      ok: readiness.brief_complete },
                          { label: 'Platform connections ready',   ok: !readiness.youtube_selected || readiness.youtube_connection_ready },
                          { label: 'Campaign theme generated',     ok: Boolean(masterTheme) },
                        ].map(({ label, ok }) => (
                          <div key={label} className="dma-wizard-review-row" style={{ padding: '0.85rem 1rem' }}>
                            <span>{label}</span>
                            <Badge appearance="outline" color={ok ? 'success' : 'warning'}>
                              {ok ? '✓ Ready' : 'Incomplete'}
                            </Badge>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Missing requirements */}
                    {readiness.missing_requirements?.length > 0 ? (
                      <FeedbackMessage
                        intent="warning"
                        title="Complete these before activating"
                        message={readiness.missing_requirements.join(' · ')}
                      />
                    ) : null}

                    {/* Activation status */}
                    {readiness.can_finalize ? (
                      <div style={{ display: 'grid', gap: '0.6rem' }}>
                        <div style={{ color: '#10b981', fontWeight: 600 }}>
                          ✓ Agent is ready to activate
                        </div>
                        {readOnly ? (
                          <Badge appearance="outline" color="informative">This hire has ended — activation workspace is read-only.</Badge>
                        ) : null}
                      </div>
                    ) : (
                      <div style={{ opacity: 0.7, fontSize: '0.9rem' }}>
                        Complete the missing items above, then return to this step to activate.
                      </div>
                    )}

                    {saveError ? <FeedbackMessage intent="error" title="Save failed" message={saveError} /> : null}
                    {finishError ? <FeedbackMessage intent="error" title="Activation failed" message={finishError} /> : null}
                    {finishStatus === 'success' || activation?.workspace.activation_complete ? (
                      <FeedbackMessage intent="success" title="Setup complete" message="This hire now has channels, theme plan, and schedule confirmed." />
                    ) : null}
                  </div>
                </div>
              )}

            </div>

            {/* STICKY FOOTER — Back / Continue / Activate */}
            <div className="dma-wizard-action-bar">
              <div className="dma-wizard-action-bar-left">
                <SaveIndicator status={saveStatus} errorMessage={saveError || undefined} />
              </div>
              <div className="dma-wizard-action-bar-right">
                <Button
                  appearance="subtle"
                  onClick={() => setActiveStepIndex(i => Math.max(0, i - 1))}
                  disabled={activeStepIndex === 0}
                >
                  Back
                </Button>
                {activeStepIndex < DMA_STEPS.length - 1 ? (
                  <Button
                    appearance="primary"
                    onClick={() => void handleContinue()}
                    disabled={saveStatus === 'saving'}
                  >
                    {saveStatus === 'saving' ? 'Saving…' : 'Continue'}
                  </Button>
                ) : (
                  <Button
                    appearance="primary"
                    onClick={() => void finishActivation()}
                    disabled={readOnly || finishStatus === 'saving' || !readiness.can_finalize}
                  >
                    {finishStatus === 'saving' ? 'Activating…' : 'Activate Agent'}
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

export default DigitalMarketingActivationWizard
