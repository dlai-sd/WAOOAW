import { Badge, Button, Card, CardHeader, Spinner, Text, Input, Textarea } from '@fluentui/react-components'
import { useEffect, useMemo, useRef, useState } from 'react'

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
  type DigitalMarketingStrategyWorkshop,
  type DigitalMarketingStrategyWorkshopSummary,
  type UpsertDigitalMarketingActivationInput,
} from '../services/digitalMarketingActivation.service'
import {
  createDraftBatch,
  executeDraftPost,
  approveDraftPost,
  rejectDraftPost,
  scheduleDraftPost,
  type DraftBatch,
  type DraftPost,
} from '../services/marketingReview.service'
import {
  startYouTubeConnection,
  attachYouTubeConnection,
  listYouTubeConnections,
  validateYouTubeConnection,
  type ValidateYouTubeConnectionResponse,
  type YouTubeConnection,
} from '../services/youtubeConnections.service'
import {
  findPlatformConnection,
  listPlatformConnections,
  type PlatformConnection,
} from '../services/platformConnections.service'
import {
  getBrandVoice,
  updateBrandVoice,
} from '../services/brandVoice.service'
import { getProfile, updateProfile, type ProfileData } from '../services/profile.service'
import { redirectTo } from '../utils/browserNavigation'
import {
  beginYouTubeOAuthFlow,
  clearYouTubeOAuthResult,
  getYouTubeOAuthCallbackUri,
  readYouTubeOAuthResult,
} from '../utils/youtubeOAuthFlow'

const DIGITAL_MARKETING_AGENT_TYPE_ID = 'marketing.digital_marketing.v1'

const DMA_STEPS = [
  { id: 'connect',   title: 'Channel Ready',        description: 'Connect or confirm the YouTube channel.' },
  { id: 'theme',     title: 'Brief Chat',           description: 'Guide the customer to a usable YouTube direction.' },
  { id: 'schedule',  title: 'Plan',                 description: 'Confirm posting rhythm only after the brief is coherent.' },
  { id: 'activate',  title: 'Review & Activate',    description: 'Show exactly what is ready and what is blocked.' },
] as const

const PLATFORM_OPTIONS = [
  { key: 'youtube', label: 'YouTube', description: 'Channel uploads and video publishing approvals.' },
  { key: 'instagram', label: 'Instagram', description: 'Reels, posts, and story publishing workflows.' },
  { key: 'facebook', label: 'Facebook', description: 'Page posting and distribution.' },
  { key: 'linkedin', label: 'LinkedIn', description: 'Thought leadership and company-page posts.' },
  { key: 'whatsapp', label: 'WhatsApp', description: 'Outbound campaign and customer follow-up content.' },
  { key: 'x', label: 'X', description: 'Short-form social publishing and promotion.' },
]

const SUPPORTED_PLATFORM_OPTIONS = PLATFORM_OPTIONS.filter((platform) => platform.key === 'youtube')


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

function buildEmptyStrategyWorkshop(): DigitalMarketingStrategyWorkshop {
  return {
    status: 'not_started',
    assistant_message: '',
    checkpoint_summary: '',
    current_focus_question: '',
    next_step_options: [],
    time_saving_note: '',
    follow_up_questions: [],
    messages: [],
    summary: {
      profession_name: '',
      location_focus: '',
      customer_profile: '',
      service_focus: '',
      signature_differentiator: '',
      business_goal: '',
      first_content_direction: '',
      business_focus: '',
      audience: '',
      positioning: '',
      tone: '',
      content_pillars: [],
      youtube_angle: '',
      cta: '',
    },
    approved_at: null,
  }
}

function normalizeStrategyWorkshop(workshop: unknown): DigitalMarketingStrategyWorkshop {
  const raw = workshop && typeof workshop === 'object' ? workshop as DigitalMarketingStrategyWorkshop : {}
  const rawSummary = raw.summary && typeof raw.summary === 'object' ? raw.summary : {}
  const status = raw.status === 'discovery' || raw.status === 'approval_ready' || raw.status === 'approved'
    ? raw.status
    : 'not_started'

  return {
    status,
    assistant_message: String(raw.assistant_message || ''),
    checkpoint_summary: String(raw.checkpoint_summary || ''),
    current_focus_question: String(raw.current_focus_question || raw.follow_up_questions?.[0] || ''),
    next_step_options: Array.isArray(raw.next_step_options)
      ? raw.next_step_options.map((item) => String(item || '').trim()).filter(Boolean)
      : [],
    time_saving_note: String(raw.time_saving_note || ''),
    follow_up_questions: Array.isArray(raw.follow_up_questions)
      ? raw.follow_up_questions.map((item) => String(item || '').trim()).filter(Boolean)
      : [],
    messages: Array.isArray(raw.messages)
      ? raw.messages
          .map((item) => {
            const role = item?.role === 'user' ? 'user' : item?.role === 'assistant' ? 'assistant' : null
            const content = String(item?.content || '').trim()
            return role && content ? { role, content } : null
          })
          .filter(Boolean) as NonNullable<DigitalMarketingStrategyWorkshop['messages']>
      : [],
    summary: {
      profession_name: String(rawSummary.profession_name || ''),
      location_focus: String(rawSummary.location_focus || ''),
      customer_profile: String(rawSummary.customer_profile || ''),
      service_focus: String(rawSummary.service_focus || ''),
      signature_differentiator: String(rawSummary.signature_differentiator || ''),
      business_goal: String(rawSummary.business_goal || ''),
      first_content_direction: String(rawSummary.first_content_direction || ''),
      business_focus: String(rawSummary.business_focus || ''),
      audience: String(rawSummary.audience || ''),
      positioning: String(rawSummary.positioning || ''),
      tone: String(rawSummary.tone || ''),
      content_pillars: Array.isArray(rawSummary.content_pillars)
        ? rawSummary.content_pillars.map((item) => String(item || '').trim()).filter(Boolean)
        : [],
      youtube_angle: String(rawSummary.youtube_angle || ''),
      cta: String(rawSummary.cta || ''),
    },
    approved_at: raw.approved_at ? String(raw.approved_at) : null,
  }
}

function buildStrategyWorkshopPayload(
  workshop: DigitalMarketingStrategyWorkshop,
  summary: DigitalMarketingStrategyWorkshopSummary,
  statusOverride?: DigitalMarketingStrategyWorkshop['status'],
): DigitalMarketingStrategyWorkshop {
  return {
    ...normalizeStrategyWorkshop(workshop),
    status: statusOverride || workshop.status || 'not_started',
    summary: {
      profession_name: String(summary.profession_name || '').trim(),
      location_focus: String(summary.location_focus || '').trim(),
      customer_profile: String(summary.customer_profile || '').trim(),
      service_focus: String(summary.service_focus || '').trim(),
      signature_differentiator: String(summary.signature_differentiator || '').trim(),
      business_goal: String(summary.business_goal || '').trim(),
      first_content_direction: String(summary.first_content_direction || '').trim(),
      business_focus: String(summary.business_focus || '').trim(),
      audience: String(summary.audience || '').trim(),
      positioning: String(summary.positioning || '').trim(),
      tone: String(summary.tone || '').trim(),
      content_pillars: Array.isArray(summary.content_pillars)
        ? summary.content_pillars.map((item) => String(item || '').trim()).filter(Boolean)
        : [],
      youtube_angle: String(summary.youtube_angle || '').trim(),
      cta: String(summary.cta || '').trim(),
    },
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

function formatDurationLabel(totalSeconds: number): string {
  const safeSeconds = Math.max(0, Math.trunc(totalSeconds || 0))
  const minutes = Math.floor(safeSeconds / 60)
  const seconds = safeSeconds % 60
  return `${minutes}:${String(seconds).padStart(2, '0')}`
}

function formatPublishedDateLabel(value: string | null | undefined): string {
  if (!value) return 'Unknown publish date'
  const parsed = new Date(value)
  if (Number.isNaN(parsed.getTime())) return 'Unknown publish date'
  return parsed.toLocaleDateString()
}

function getYouTubeNextActionCopy(nextActionHint: string | null | undefined): string | null {
  if (nextActionHint === 'reconnect_required') {
    return 'Token expired — reconnect with Google to restore access'
  }
  if (nextActionHint === 'token_expiring_soon') {
    return 'Token expires soon — consider reconnecting to avoid disruption'
  }
  if (nextActionHint === 'connected_ready') {
    return 'Connected and ready — your DMA can access this channel'
  }
  return null
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
  const [voiceDescription, setVoiceDescription] = useState('')
  const [toneKeywords, setToneKeywords] = useState('')
  const [examplePhrases, setExamplePhrases] = useState('')
  const [brandVoiceLoading, setBrandVoiceLoading] = useState(false)
  const [selectedPlatforms, setSelectedPlatforms] = useState<string[]>([])
  const [masterTheme, setMasterTheme] = useState('')
  const [derivedThemes, setDerivedThemes] = useState<DigitalMarketingDerivedTheme[]>([])
  const [strategyWorkshop, setStrategyWorkshop] = useState<DigitalMarketingStrategyWorkshop>(buildEmptyStrategyWorkshop())
  const [strategySummary, setStrategySummary] = useState<DigitalMarketingStrategyWorkshopSummary>(buildEmptyStrategyWorkshop().summary || {})
  const [strategyReply, setStrategyReply] = useState('')
  const [strategyDetailsEditable, setStrategyDetailsEditable] = useState(false)
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
  const [attachedYouTubeConnection, setAttachedYouTubeConnection] = useState<PlatformConnection | null>(null)
  const [oauthLoading, setOauthLoading] = useState(false)
  const [oauthError, setOauthError] = useState<string | null>(null)
  const [oauthMessage, setOauthMessage] = useState<string | null>(null)
  const [youtubeValidationLoading, setYoutubeValidationLoading] = useState(false)
  const [youtubePersistLoading, setYoutubePersistLoading] = useState(false)
  const [youtubeValidationError, setYoutubeValidationError] = useState<string | null>(null)
  const [youtubeValidationResult, setYoutubeValidationResult] = useState<ValidateYouTubeConnectionResponse | null>(null)

  const [generatedBatch, setGeneratedBatch] = useState<DraftBatch | null>(null)
  const [draftPosts, setDraftPosts] = useState<DraftPost[]>([])
  const [draftGenerating, setDraftGenerating] = useState(false)
  const [draftGenerateError, setDraftGenerateError] = useState<string | null>(null)
  const [postActionStatus, setPostActionStatus] = useState<Record<string, 'idle' | 'loading' | 'done' | 'error'>>({})
  const [postPublishReceipts, setPostPublishReceipts] = useState<Record<string, string>>({})
  const [queueDateTime, setQueueDateTime] = useState<Record<string, string>>({})
  const profileRef = useRef<ProfileData | null>(null)

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
    setYoutubeConnected(Boolean(connection))
    setOauthMessage(successMessage)
    setOauthError(null)
    setYoutubeValidationError(null)
    setYoutubeValidationResult(null)
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
              connected: Boolean(connection),
            },
          },
        },
      }
    })
  }

  function markYouTubeAttached(connection: PlatformConnection, successMessage: string) {
    setAttachedYouTubeConnection(connection)
    setYoutubeConnected(true)
    setOauthMessage(successMessage)
    setOauthError(null)
    setActivation((current) => {
      if (!current) return current
      return {
        ...current,
        readiness: {
          ...current.readiness,
          youtube_connection_ready: true,
        },
      }
    })
  }

  async function refreshAttachedYouTubeConnection(nextHiredInstanceId: string): Promise<PlatformConnection | null> {
    if (!nextHiredInstanceId) {
      setAttachedYouTubeConnection(null)
      return null
    }

    try {
      const connections = await listPlatformConnections(nextHiredInstanceId)
      const connection = findPlatformConnection(connections, 'youtube')
      setAttachedYouTubeConnection(connection)
      return connection
    } catch {
      setAttachedYouTubeConnection(null)
      return null
    }
  }

  const isYouTubeAttached = useMemo(() => {
    const status = String(attachedYouTubeConnection?.status || '').trim().toLowerCase()
    return Boolean(attachedYouTubeConnection && (status === 'connected' || status === 'active'))
  }, [attachedYouTubeConnection])

  // OAuth callback — detect ?code&state on mount and finalize connection
  useEffect(() => {
    const result = readYouTubeOAuthResult()
    if (!result || result.source !== 'activation-wizard') return
    if (result.hiredInstanceId && hiredInstanceId && result.hiredInstanceId !== hiredInstanceId) return

    clearYouTubeOAuthResult()
    markYouTubeConnected(result.connection, result.message)
    setActiveStepIndex(DMA_STEPS.findIndex((s) => s.id === 'connect'))
  }, [hiredInstanceId])

  // Load existing saved YouTube connections for this customer
  useEffect(() => {
    listYouTubeConnections()
      .then((connections) => {
        const reusableConnection = pickReusableYouTubeConnection(connections)
        setSavedYouTubeConnection(reusableConnection)
        setYoutubeConnected(Boolean(reusableConnection))
      })
      .catch(() => {
        setSavedYouTubeConnection(null)
        setYoutubeConnected(false)
      })
  }, [])

  useEffect(() => {
    void refreshAttachedYouTubeConnection(hiredInstanceId)
  }, [hiredInstanceId])

  const campaignSetup = activation?.workspace.campaign_setup || {}
  const schedule = campaignSetup.schedule || {}
  const isThemeApproved = strategyWorkshop.status === 'approved'
  const latestCustomerNote = useMemo(() => {
    const messages = strategyWorkshop.messages || []
    for (let index = messages.length - 1; index >= 0; index -= 1) {
      if (messages[index]?.role === 'user') return messages[index].content
    }
    return ''
  }, [strategyWorkshop.messages])

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
    const nextWorkshop = normalizeStrategyWorkshop(nextCampaignSetup.strategy_workshop)
    setMasterTheme(String(nextCampaignSetup.master_theme || ''))
    setDerivedThemes(Array.isArray(nextCampaignSetup.derived_themes) ? nextCampaignSetup.derived_themes : [])
    setStrategyWorkshop(nextWorkshop)
    setStrategySummary(nextWorkshop.summary || {})
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

      let profile = profileRef.current
      const workspaceBrandName = normalizeText(nextActivation?.workspace.brand_name)
      if (!workspaceBrandName && !profile) {
        try {
          profile = await getProfile()
          profileRef.current = profile
        } catch {
          profile = profileRef.current
        }
      }
      setDraft(nextDraft)
      setActivation(nextActivation)
      setNickname(normalizeText(nextDraft.nickname))
      setTheme(normalizeText(nextDraft.theme))
      setBrandName(workspaceBrandName || normalizeText(profile?.business_name))
      setLocation(normalizeText(nextActivation?.workspace.location) || normalizeText(profile?.location))
      setPrimaryLanguage(normalizeText(nextActivation?.workspace.primary_language) || normalizeText(profile?.primary_language))
      setTimezone(normalizeText(nextActivation?.workspace.timezone) || normalizeText(profile?.timezone))
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

  useEffect(() => {
    if (currentStep.id !== 'theme') return
    let cancelled = false
    setBrandVoiceLoading(true)
    getBrandVoice()
      .then((brandVoice) => {
        if (cancelled) return
        setVoiceDescription(brandVoice.voice_description || '')
        setToneKeywords((brandVoice.tone_keywords || []).join(', '))
        setExamplePhrases((brandVoice.example_phrases || []).join('\n'))
      })
      .catch(() => {
        if (cancelled) return
        setVoiceDescription('')
        setToneKeywords('')
        setExamplePhrases('')
      })
      .finally(() => {
        if (!cancelled) setBrandVoiceLoading(false)
      })
    return () => { cancelled = true }
  }, [currentStep.id])

  const readiness = activation?.readiness || {
    brief_complete: false,
    youtube_selected: selectedPlatforms.includes('youtube'),
    youtube_connection_ready: false,
    configured: Boolean(nickname.trim() && theme.trim()),
    can_finalize: false,
    missing_requirements: [],
  }

  const milestoneCount = getActivationMilestoneCount(readiness)
  const completedMilestones = milestoneCount + (isThemeApproved ? 1 : 0)
  const canFinish = Boolean(masterTheme.trim()) && isThemeApproved && Boolean(scheduleStartDate.trim()) && Boolean(readiness.can_finalize)
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

  const saveBrandVoice = async (): Promise<boolean> => {
    if (readOnly) return true
    try {
      await updateBrandVoice({
        voice_description: voiceDescription.trim(),
        tone_keywords: parseListTextarea(toneKeywords),
        example_phrases: parseListTextarea(examplePhrases),
      })
      return true
    } catch (e: any) {
      setSaveError(e?.message || 'Failed to save brand voice')
      setSaveStatus('error')
      return false
    }
  }

  const saveProfile = async (): Promise<boolean> => {
    if (readOnly) return true

    const payload = {
      business_name: brandName.trim(),
      location: location.trim(),
      timezone: timezone.trim(),
      primary_language: primaryLanguage.trim(),
    }
    const currentProfile = profileRef.current
    const hasChanges = !currentProfile || (
      normalizeText(currentProfile.business_name).trim() !== payload.business_name ||
      normalizeText(currentProfile.location).trim() !== payload.location ||
      normalizeText(currentProfile.timezone).trim() !== payload.timezone ||
      normalizeText(currentProfile.primary_language).trim() !== payload.primary_language
    )
    const hasAnyValue = Object.values(payload).some((value) => value.trim())

    if (!hasChanges || (!hasAnyValue && !currentProfile)) {
      return true
    }

    try {
      profileRef.current = await updateProfile(payload)
      return true
    } catch (e: any) {
      setSaveError(e?.message || 'Failed to sync profile details')
      setSaveStatus('error')
      return false
    }
  }

  async function handleContinue() {
    const saved = await saveWorkspace()
    if (!saved) return
    if (currentStep.id === 'theme') {
      const savedProfile = await saveProfile()
      if (!savedProfile) return
      const savedBrandVoice = await saveBrandVoice()
      if (!savedBrandVoice) return
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

      const redirectUri = getYouTubeOAuthCallbackUri()
      const { state, authorization_url } = await startYouTubeConnection(redirectUri)
      beginYouTubeOAuthFlow({
        state,
        source: 'activation-wizard',
        returnTo: '/my-agents',
        redirectUri,
        hiredInstanceId,
        skillId: youtubeSkillId,
      })
      redirectTo(authorization_url)
    } catch (err) {
      setOauthError('Could not start YouTube connection. Please try again.')
    } finally {
      setOauthLoading(false)
    }
  }

  async function handleTestYouTubeConnection() {
    if (!savedYouTubeConnection?.id) {
      setYoutubeValidationError('Connect a YouTube channel first.')
      return
    }

    setYoutubeValidationLoading(true)
    setYoutubeValidationError(null)
    setOauthError(null)
    try {
      const result = await validateYouTubeConnection(savedYouTubeConnection.id)
      setYoutubeValidationResult(result)
      setSavedYouTubeConnection((current) => {
        if (!current) return current
        return {
          ...current,
          display_name: result.display_name,
          provider_account_id: result.provider_account_id,
          verification_status: result.verification_status,
          connection_status: result.connection_status,
          token_expires_at: result.token_expires_at,
          last_verified_at: result.last_verified_at,
        }
      })
      setYoutubeConnected(true)
      setOauthMessage(`Connection test succeeded for ${result.display_name || 'your YouTube channel'}.`)
    } catch (caughtError: any) {
      setYoutubeValidationResult(null)
      setYoutubeValidationError(caughtError?.message || 'The YouTube connection test failed. Please try again.')
    } finally {
      setYoutubeValidationLoading(false)
    }
  }

  async function handlePersistYouTubeConnection() {
    if (!savedYouTubeConnection?.id) {
      setOauthError('Connect and test a YouTube channel before saving it for the agent.')
      return
    }
    if (!youtubeValidationResult || youtubeValidationResult.id !== savedYouTubeConnection.id) {
      setOauthError('Run a successful connection test before saving it for the agent.')
      return
    }
    if (!hiredInstanceId) {
      setOauthError('This agent is not ready yet. Please reload the page and try again.')
      return
    }

    setYoutubePersistLoading(true)
    setOauthError(null)
    try {
      const attachedConnection = await attachYouTubeConnection(savedYouTubeConnection.id, {
        hired_instance_id: hiredInstanceId,
        skill_id: youtubeSkillId,
      })
      markYouTubeAttached(attachedConnection, 'YouTube connection saved for future agent use.')
    } catch (caughtError: any) {
      setOauthError(caughtError?.message || 'Could not save the YouTube connection for the agent.')
    } finally {
      setYoutubePersistLoading(false)
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
    const nextWorkshop = normalizeStrategyWorkshop(nextWorkspace.campaign_setup?.strategy_workshop)
    setStrategyWorkshop(nextWorkshop)
    setStrategySummary(nextWorkshop.summary || {})
    setStrategyReply('')
    setStrategyDetailsEditable(false)
  }

  const generateThemePlan = async (overrideReply?: string) => {
    if (!hiredInstanceId) return
    setThemePlanLoading(true)
    setThemePlanError(null)
    try {
      const saved = await saveWorkspace()
      if (!saved) return
      const pendingInput = String(overrideReply ?? strategyReply).trim()
      const response = await generateDigitalMarketingThemePlan(hiredInstanceId, {
        campaign_setup: {
          schedule: normalizedSchedule,
          strategy_workshop: {
            ...buildStrategyWorkshopPayload(
              strategyWorkshop,
              strategySummary,
              strategyWorkshop.status === 'approved' ? 'approval_ready' : strategyWorkshop.status,
            ),
            pending_input: pendingInput,
          },
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

  const youtubeCredentialRef: string | null = useMemo(() => {
    const binding = activation?.workspace?.platform_bindings?.youtube
    return String(
      attachedYouTubeConnection?.customer_platform_credential_id
      || binding?.credential_ref
      || binding?.customer_platform_credential_id
      || ''
    ).trim() || null
  }, [activation?.workspace?.platform_bindings, attachedYouTubeConnection?.customer_platform_credential_id])

  const canGenerateYouTubeDraft = useMemo(() => {
    const ytSelected = selectedPlatforms.includes('youtube')
    const ytReady = isYouTubeAttached
    const briefReady = Boolean(brandName.trim())
    return ytSelected && ytReady && briefReady && isThemeApproved && !draftGenerating
  }, [selectedPlatforms, isYouTubeAttached, brandName, isThemeApproved, draftGenerating])

  const handleGenerateYouTubeDraft = async () => {
    if (!canGenerateYouTubeDraft || !hiredInstanceId) return
    setDraftGenerating(true)
    setDraftGenerateError(null)
    try {
      const agentId = String(draft?.agent_id || activeInstance?.agent_id || '').trim()
      const campaignId = activation?.workspace?.campaign_setup?.campaign_id || undefined
      const batch = await createDraftBatch({
        agent_id: agentId,
        hired_instance_id: hiredInstanceId,
        campaign_id: campaignId ?? null,
        theme: masterTheme.trim() || brandName.trim(),
        brand_name: brandName.trim(),
        brief_summary: businessContext.trim() || undefined,
        location: location.trim() || undefined,
        audience: undefined,
        tone: undefined,
        language: primaryLanguage.trim() || undefined,
        youtube_credential_ref: youtubeCredentialRef,
        youtube_visibility: 'private',
        public_release_requested: false,
        channels: ['youtube'],
      })
      setGeneratedBatch(batch)
      setDraftPosts(batch.posts.filter((p) => p.channel === 'youtube'))
      setPostActionStatus({})
      setPostPublishReceipts({})
    } catch (e: any) {
      setDraftGenerateError(e?.message || 'Failed to generate YouTube draft.')
    } finally {
      setDraftGenerating(false)
    }
  }

  const handleApprovePost = async (postId: string) => {
    setPostActionStatus((s) => ({ ...s, [postId]: 'loading' }))
    try {
      const approval = await approveDraftPost(postId)
      setDraftPosts((posts) =>
        posts.map((p) => (
          p.post_id === postId
            ? {
                ...p,
                review_status: 'approved',
                approval_id: approval.approval_id || p.approval_id || null,
              }
            : p
        ))
      )
      setPostActionStatus((s) => ({ ...s, [postId]: 'done' }))
    } catch {
      setPostActionStatus((s) => ({ ...s, [postId]: 'error' }))
    }
  }

  const handleRejectPost = async (postId: string) => {
    setPostActionStatus((s) => ({ ...s, [postId]: 'loading' }))
    try {
      await rejectDraftPost(postId)
      setDraftPosts((posts) =>
        posts.map((p) => (p.post_id === postId ? { ...p, review_status: 'rejected' } : p))
      )
      setPostActionStatus((s) => ({ ...s, [postId]: 'done' }))
    } catch {
      setPostActionStatus((s) => ({ ...s, [postId]: 'error' }))
    }
  }

  const handlePublishNow = async (post: DraftPost) => {
    if (!generatedBatch) return
    const agentId = String(draft?.agent_id || activeInstance?.agent_id || '').trim()
    setPostActionStatus((s) => ({ ...s, [post.post_id]: 'loading' }))
    try {
      const result = await executeDraftPost({
        post_id: post.post_id,
        agent_id: agentId,
        approval_id: post.approval_id ?? undefined,
        intent_action: 'publish',
      })
      if (result.provider_post_url) {
        setPostPublishReceipts((r) => ({ ...r, [post.post_id]: result.provider_post_url! }))
      }
      setDraftPosts((posts) =>
        posts.map((p) =>
          p.post_id === post.post_id
            ? { ...p, execution_status: result.execution_status ?? 'posted', provider_post_url: result.provider_post_url ?? null }
            : p
        )
      )
      setPostActionStatus((s) => ({ ...s, [post.post_id]: 'done' }))
    } catch {
      setPostActionStatus((s) => ({ ...s, [post.post_id]: 'error' }))
    }
  }

  const handleQueuePost = async (post: DraftPost) => {
    const scheduledAt = queueDateTime[post.post_id]
    if (!scheduledAt) return
    setPostActionStatus((s) => ({ ...s, [post.post_id]: 'loading' }))
    try {
      await scheduleDraftPost(post.post_id, scheduledAt, post.approval_id ?? undefined)
      setDraftPosts((posts) =>
        posts.map((p) =>
          p.post_id === post.post_id
            ? { ...p, execution_status: 'scheduled', scheduled_at: scheduledAt }
            : p
        )
      )
      setPostActionStatus((s) => ({ ...s, [post.post_id]: 'done' }))
    } catch {
      setPostActionStatus((s) => ({ ...s, [post.post_id]: 'error' }))
    }
  }

  const renderDraftGenerationPanel = () => {
    if (!selectedPlatforms.includes('youtube')) return null

    return (
      <div className="dma-wizard-theme-draft-panel" data-testid="theme-draft-panel">
        <div style={{ fontWeight: 600, marginBottom: '0.5rem' }}>Generate YouTube draft</div>
        <div style={{ opacity: 0.7, fontSize: '0.85rem', marginBottom: '0.75rem' }}>
          Once you approve the strategy, the agent can turn it into a YouTube draft for review.
        </div>
        {!isYouTubeAttached ? (
          <div style={{ opacity: 0.7, fontSize: '0.85rem' }}>Connect and attach YouTube in the previous step first.</div>
        ) : !isThemeApproved ? (
          <div style={{ opacity: 0.75, fontSize: '0.85rem' }} data-testid="generate-youtube-draft-next-step-hint">
            Approve the master theme strategy below before generating a YouTube draft.
          </div>
        ) : (
          <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
            <Button
              appearance="primary"
              onClick={() => void handleGenerateYouTubeDraft()}
              disabled={!canGenerateYouTubeDraft || readOnly}
              data-testid="generate-youtube-draft-btn"
            >
              {draftGenerating ? 'Generating…' : 'Generate YouTube Draft'}
            </Button>
            {draftGenerating ? <Spinner size="tiny" /> : null}
          </div>
        )}
        {draftGenerateError ? (
          <FeedbackMessage intent="error" title="Draft generation failed" message={draftGenerateError} />
        ) : null}

        {draftPosts.length > 0 && (
          <div style={{ marginTop: '1rem', display: 'grid', gap: '1rem' }}>
            <div style={{ fontWeight: 600, fontSize: '0.95rem' }}>Draft posts ({draftPosts.length})</div>
            {draftPosts.map((post) => {
              const status = postActionStatus[post.post_id] || 'idle'
              const isApproved = post.review_status === 'approved'
              const isRejected = post.review_status === 'rejected'
              const isPosted = post.execution_status === 'posted'
              const isScheduled = post.execution_status === 'scheduled'
              const receiptUrl = postPublishReceipts[post.post_id] || post.provider_post_url
              const ytAttached = isYouTubeAttached
              return (
                <div
                  key={post.post_id}
                  data-testid={`draft-post-card-${post.post_id}`}
                  style={{ padding: '0.85rem', border: '1px solid var(--colorNeutralStroke2)', borderRadius: '10px', background: 'rgba(255,255,255,0.03)' }}
                >
                  <div style={{ fontSize: '0.85rem', opacity: 0.65, marginBottom: '0.4rem' }}>YouTube draft</div>
                  <div style={{ marginBottom: '0.75rem', lineHeight: 1.5 }}>{post.text}</div>
                  <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', alignItems: 'center' }}>
                    <Badge appearance="outline" color={isApproved ? 'success' : isRejected ? 'danger' : 'warning'}>
                      {post.review_status}
                    </Badge>
                    {isPosted ? (
                      <Badge appearance="outline" color="success">Published</Badge>
                    ) : isScheduled ? (
                      <Badge appearance="outline" color="informative">Queued</Badge>
                    ) : null}
                  </div>
                  {receiptUrl ? (
                    <div style={{ marginTop: '0.5rem', fontSize: '0.82rem' }}>
                      <span style={{ opacity: 0.6 }}>Published: </span>
                      <a href={receiptUrl} target="_blank" rel="noopener noreferrer" style={{ color: '#00f2fe' }} data-testid={`publish-receipt-${post.post_id}`}>
                        {receiptUrl}
                      </a>
                    </div>
                  ) : null}
                  {!isRejected && !isPosted && !isScheduled ? (
                    <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.75rem', flexWrap: 'wrap' }}>
                      {!isApproved ? (
                        <>
                          <Button
                            size="small"
                            appearance="primary"
                            disabled={status === 'loading' || readOnly}
                            onClick={() => void handleApprovePost(post.post_id)}
                            data-testid={`approve-post-btn-${post.post_id}`}
                          >
                            Approve
                          </Button>
                          <Button
                            size="small"
                            appearance="subtle"
                            disabled={status === 'loading' || readOnly}
                            onClick={() => void handleRejectPost(post.post_id)}
                            data-testid={`reject-post-btn-${post.post_id}`}
                          >
                            Reject
                          </Button>
                        </>
                      ) : null}
                      {isApproved ? (
                        <>
                          <Button
                            size="small"
                            appearance="primary"
                            disabled={status === 'loading' || !ytAttached || readOnly}
                            onClick={() => void handlePublishNow(post)}
                            data-testid={`publish-now-btn-${post.post_id}`}
                            title={!ytAttached ? 'YouTube must be connected and attached' : undefined}
                          >
                            Publish now
                          </Button>
                          <div style={{ display: 'flex', gap: '0.4rem', alignItems: 'center' }}>
                            <Input
                              type="datetime-local"
                              size="small"
                              aria-label="Queue date and time"
                              value={queueDateTime[post.post_id] || ''}
                              onChange={(_, d) => setQueueDateTime((q) => ({ ...q, [post.post_id]: d.value }))}
                              style={{ fontSize: '0.82rem' }}
                            />
                            <Button
                              size="small"
                              appearance="outline"
                              disabled={status === 'loading' || !queueDateTime[post.post_id] || readOnly}
                              onClick={() => void handleQueuePost(post)}
                              data-testid={`queue-post-btn-${post.post_id}`}
                            >
                              Queue for later
                            </Button>
                          </div>
                        </>
                      ) : null}
                      {status === 'loading' ? <Spinner size="tiny" /> : null}
                      {status === 'error' ? <span style={{ color: '#ef4444', fontSize: '0.82rem' }}>Action failed</span> : null}
                    </div>
                  ) : null}
                </div>
              )
            })}
          </div>
        )}
      </div>
    )
  }

  const strategyPreviewMessages = (strategyWorkshop.messages || []).slice(-5)

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
          strategy_workshop: buildStrategyWorkshopPayload(strategyWorkshop, strategySummary),
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

  const updateStrategySummaryField = (field: keyof DigitalMarketingStrategyWorkshopSummary, value: string | string[]) => {
    setStrategySummary((current) => ({
      ...current,
      [field]: value,
    }))
  }

  const handleStrategyOption = (option: string) => {
    if (themePlanLoading || readOnly) return
    const normalizedOption = String(option || '').trim()
    if (!normalizedOption) return
    setStrategyReply(normalizedOption)
    void generateThemePlan(normalizedOption)
  }

  const approveThemeStrategy = async () => {
    if (!hiredInstanceId || !masterTheme.trim()) return
    setThemePlanSaving(true)
    setThemePlanError(null)
    try {
      const response = await patchDigitalMarketingThemePlan(hiredInstanceId, {
        master_theme: masterTheme.trim(),
        derived_themes: derivedThemes,
        campaign_setup: {
          campaign_id: campaignSetup.campaign_id,
          schedule: normalizedSchedule,
          strategy_workshop: {
            ...buildStrategyWorkshopPayload(strategyWorkshop, strategySummary, 'approved'),
            approved_at: new Date().toISOString(),
          },
        },
      })
      applyThemePlanResponse(response)
    } catch (e: any) {
      setThemePlanError(e?.message || 'Failed to approve theme strategy.')
    } finally {
      setThemePlanSaving(false)
    }
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
            strategy_workshop: buildStrategyWorkshopPayload(strategyWorkshop, strategySummary),
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

              {/* STEP 1 — Channel Ready */}
              {currentStep.id === 'connect' && (
                <div className="dma-wizard-step-content" data-testid="dma-step-panel-connect">
                  <div className="dma-wizard-platform-connect-list">

                    {/* YouTube */}
                    <div className="dma-wizard-platform-connect-row">
                      <div className="dma-wizard-platform-connect-info">
                        <span className="dma-wizard-platform-connect-name">YouTube</span>
                        <span className="dma-wizard-platform-connect-desc">
                          Connect your YouTube channel to allow the agent to manage uploads and publishing.
                        </span>
                        {savedYouTubeConnection?.display_name ? (
                          <span
                            data-testid="youtube-linked-channel-name"
                            style={{ fontSize: '0.85rem', color: '#10b981', marginTop: '0.2rem', display: 'block' }}
                          >
                            Channel: {savedYouTubeConnection.display_name}
                          </span>
                        ) : null}
                        {savedYouTubeConnection && savedYouTubeConnection.verification_status !== 'verified' ? (
                          <span style={{ fontSize: '0.8rem', color: '#f59e0b', display: 'block' }}>
                            Verification pending. Run Test connection to verify this channel.
                          </span>
                        ) : null}
                        {youtubeValidationResult && !isYouTubeAttached ? (
                          <span style={{ fontSize: '0.8rem', color: '#f59e0b', display: 'block' }}>
                            Connection tested successfully. Save it for the agent when ready.
                          </span>
                        ) : null}
                      </div>
                      <div className="dma-wizard-platform-connect-action" style={{ display: 'grid', gap: '0.6rem', justifyItems: 'end' }}>
                        {isYouTubeAttached ? (
                          <span className="dma-wizard-connected-badge" data-testid="youtube-connected-badge">✓ Connected</span>
                        ) : null}
                        <Button
                          appearance="primary"
                          disabled={oauthLoading || readOnly}
                          onClick={() => void handleConnectYouTube()}
                        >
                          {oauthLoading
                            ? 'Connecting…'
                            : savedYouTubeConnection
                              ? 'Reconnect with Google'
                              : 'Connect with Google'}
                        </Button>
                        <Button
                          appearance="secondary"
                          disabled={!savedYouTubeConnection || youtubeValidationLoading || readOnly}
                          onClick={() => void handleTestYouTubeConnection()}
                        >
                          {youtubeValidationLoading ? 'Testing…' : 'Test connection'}
                        </Button>
                        {!isYouTubeAttached && youtubeValidationResult && youtubeValidationResult.id === savedYouTubeConnection?.id ? (
                          <Button
                            appearance="outline"
                            disabled={youtubePersistLoading || readOnly}
                            onClick={() => void handlePersistYouTubeConnection()}
                          >
                            {youtubePersistLoading ? 'Saving…' : 'Persist connection for future use by Agent'}
                          </Button>
                        ) : null}
                      </div>
                    </div>

                    {youtubeValidationResult ? (
                      <div
                        data-testid="youtube-validation-metrics"
                        style={{
                          display: 'grid',
                          gridTemplateColumns: 'repeat(auto-fit, minmax(8rem, 1fr))',
                          gap: '0.75rem',
                          padding: '0.9rem 1rem',
                          border: '1px solid rgba(0, 242, 254, 0.18)',
                          borderRadius: '0.9rem',
                          background: 'rgba(0, 242, 254, 0.05)',
                        }}
                      >
                        <div><strong>Channels</strong><div>{youtubeValidationResult.channel_count}</div></div>
                        <div><strong>Videos</strong><div>{youtubeValidationResult.total_video_count}</div></div>
                        <div><strong>Shorts</strong><div>{youtubeValidationResult.recent_short_count}</div></div>
                        <div><strong>Long videos</strong><div>{youtubeValidationResult.recent_long_video_count}</div></div>
                        <div><strong>Subscribers</strong><div>{youtubeValidationResult.subscriber_count}</div></div>
                        <div><strong>Views</strong><div>{youtubeValidationResult.view_count}</div></div>
                      </div>
                    ) : null}

                    {youtubeValidationResult?.recent_uploads?.length ? (
                      <div
                        data-testid="youtube-recent-uploads"
                        style={{
                          display: 'grid',
                          gap: '0.6rem',
                          padding: '0.9rem 1rem',
                          border: '1px solid rgba(255, 255, 255, 0.08)',
                          borderRadius: '0.9rem',
                          background: 'rgba(255, 255, 255, 0.02)',
                        }}
                      >
                        <div style={{ fontWeight: 700 }}>Recent uploads (proof)</div>
                        <div style={{ display: 'grid', gap: '0.5rem' }}>
                          {youtubeValidationResult.recent_uploads.map((upload) => (
                            <div
                              key={upload.video_id}
                              style={{
                                padding: '0.75rem 0.85rem',
                                borderRadius: '0.75rem',
                                background: 'rgba(0, 242, 254, 0.05)',
                                border: '1px solid rgba(0, 242, 254, 0.12)',
                              }}
                            >
                              <div style={{ fontWeight: 600 }}>{upload.title}</div>
                              <div style={{ fontSize: '0.85rem', opacity: 0.78 }}>
                                {formatPublishedDateLabel(upload.published_at)} · {formatDurationLabel(upload.duration_seconds)}
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    ) : null}

                    {getYouTubeNextActionCopy(youtubeValidationResult?.next_action_hint) ? (
                      <div
                        data-testid="youtube-next-action-hint"
                        style={{
                          padding: '0.9rem 1rem',
                          borderRadius: '0.9rem',
                          border: '1px solid rgba(245, 158, 11, 0.28)',
                          background: 'rgba(245, 158, 11, 0.08)',
                          color: '#fcd34d',
                          fontSize: '0.95rem',
                        }}
                      >
                        {getYouTubeNextActionCopy(youtubeValidationResult?.next_action_hint)}
                      </div>
                    ) : null}

                    {oauthMessage && (
                      <div className="dma-wizard-oauth-success">{oauthMessage}</div>
                    )}

                    {youtubeValidationError && (
                      <div className="dma-wizard-oauth-error">{youtubeValidationError}</div>
                    )}

                    {oauthError && (
                      <div className="dma-wizard-oauth-error">{oauthError}</div>
                    )}

                    {selectedPlatforms.includes('youtube') ? (
                      <div className="dma-wizard-connect-next-step" data-testid="generate-youtube-draft-next-step-hint">
                        Build Master Theme is next. The AI strategist will workshop your positioning, ask follow-up questions, and only unlock draft generation after you approve the final theme.
                      </div>
                    ) : null}
                  </div>
                </div>
              )}

              {/* STEP 2 — Build Master Theme */}
              {currentStep.id === 'theme' && (
                <div className="dma-wizard-step-content" data-testid="dma-step-panel-theme">
                  <div style={{ display: 'grid', gap: '1.75rem' }}>

                    {/* PRIMARY: AI Strategy Workshop - Consultative chat-like interface */}
                    <div className="dma-wizard-theme-workshop-card">
                      <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between' }}>
                        <div>
                          <div className="dma-wizard-section-label">Brief your DMA hire</div>
                          <div style={{ fontWeight: 600, marginTop: '0.25rem' }}>The assistant will ask only what it needs to build your first YouTube theme</div>
                        </div>
                        <Badge
                          appearance="outline"
                          color={isThemeApproved ? 'success' : strategyWorkshop.status === 'approval_ready' ? 'informative' : 'warning'}
                          data-testid="strategy-workshop-status"
                        >
                          {isThemeApproved ? 'Approved' : strategyWorkshop.status === 'approval_ready' ? 'Ready for approval' : 'Discovery in progress'}
                        </Badge>
                      </div>

                      <div className="dma-wizard-theme-workshop-thread" data-testid="strategy-workshop-thread">
                        <div className="dma-wizard-theme-workshop-message dma-wizard-theme-workshop-message--assistant" data-testid="strategy-assistant-message">
                          <div className="dma-wizard-theme-workshop-message-role">Marketing Strategist</div>
                          <div>
                            {strategyWorkshop.assistant_message || 'Start the workshop and the strategist will quickly lock the strongest direction, not run a long intake interview.'}
                          </div>
                        </div>

                        {strategyWorkshop.checkpoint_summary ? (
                          <div className="dma-wizard-theme-workshop-insights">
                            <div className="dma-wizard-theme-insight-card" data-testid="strategy-checkpoint-summary">
                              <div className="dma-wizard-theme-insight-label">What we've locked</div>
                              <div>{strategyWorkshop.checkpoint_summary}</div>
                            </div>
                          </div>
                        ) : null}

                        {latestCustomerNote ? (
                          <div className="dma-wizard-theme-latest-note">
                            <div className="dma-wizard-theme-workshop-message-role">Latest customer note</div>
                            <div>{latestCustomerNote}</div>
                          </div>
                        ) : null}
                      </div>

                      {strategyWorkshop.current_focus_question ? (
                        <div>
                          <div style={{ fontWeight: 600, marginBottom: '0.45rem' }}>Next question</div>
                          <div className="dma-wizard-theme-follow-up-question" data-testid="strategy-current-focus-question">{strategyWorkshop.current_focus_question}</div>
                        </div>
                      ) : null}

                      {(strategyWorkshop.next_step_options || []).length > 0 ? (
                        <div>
                          <div style={{ fontWeight: 600, marginBottom: '0.45rem' }}>Quick answers</div>
                          <div className="dma-wizard-theme-option-list">
                            {(strategyWorkshop.next_step_options || []).map((option, index) => (
                              <Button
                                key={`${option}-${index}`}
                                appearance="secondary"
                                size="small"
                                onClick={() => handleStrategyOption(option)}
                                disabled={readOnly || themePlanLoading}
                                data-testid={`strategy-option-${index}`}
                              >
                                {option}
                              </Button>
                            ))}
                          </div>
                        </div>
                      ) : null}

                      <label style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                        <span style={{ fontWeight: 600 }}>Your answer or instruction</span>
                        <Textarea
                          aria-label="Strategy workshop reply"
                          value={strategyReply}
                          onChange={(_, data) => setStrategyReply(data.value)}
                          disabled={readOnly}
                          resize="vertical"
                          rows={3}
                          placeholder="Tell the strategist about your ideal customer, business goals, positioning, or anything the strategy must respect."
                        />
                      </label>

                      <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center', flexWrap: 'wrap' }}>
                        <Button
                          appearance="primary"
                          onClick={() => void generateThemePlan()}
                          disabled={readOnly || themePlanLoading || !brandName.trim()}
                          data-testid="start-theme-workshop-btn"
                        >
                          {themePlanLoading
                            ? 'Strategist is thinking…'
                            : latestCustomerNote || strategyWorkshop.assistant_message
                              ? 'Send to strategist'
                              : 'Start AI workshop'}
                        </Button>
                        {themePlanLoading ? <Spinner size="tiny" /> : null}
                        {!brandName.trim() ? <span style={{ opacity: 0.6, fontSize: '0.85rem' }}>Enter brand name first</span> : null}
                      </div>

                      <div>
                        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap' }}>
                          <div className="dma-wizard-section-label">Extracted business brief</div>
                          <Button
                            appearance="subtle"
                            size="small"
                            onClick={() => setStrategyDetailsEditable((current) => !current)}
                            disabled={readOnly}
                            data-testid="toggle-strategy-details-edit"
                          >
                            {strategyDetailsEditable ? 'Hide edit fields' : 'Edit extracted details'}
                          </Button>
                        </div>

                        <div className="dma-wizard-theme-summary-grid" data-testid="strategy-summary-grid">
                          <div className="dma-wizard-theme-summary-card"><span>Profession</span><strong>{strategySummary.profession_name || 'Waiting for strategist to infer'}</strong></div>
                          <div className="dma-wizard-theme-summary-card"><span>Location focus</span><strong>{strategySummary.location_focus || location || 'Waiting for locality focus'}</strong></div>
                          <div className="dma-wizard-theme-summary-card"><span>Customer profile</span><strong>{strategySummary.customer_profile || strategySummary.audience || 'Waiting for audience clarity'}</strong></div>
                          <div className="dma-wizard-theme-summary-card"><span>Service focus</span><strong>{strategySummary.service_focus || strategySummary.business_focus || 'Waiting for service focus'}</strong></div>
                          <div className="dma-wizard-theme-summary-card"><span>Differentiator</span><strong>{strategySummary.signature_differentiator || strategySummary.positioning || 'Waiting for differentiation'}</strong></div>
                          <div className="dma-wizard-theme-summary-card"><span>First content direction</span><strong>{strategySummary.first_content_direction || strategySummary.youtube_angle || 'Waiting for first content direction'}</strong></div>
                        </div>

                        {strategyDetailsEditable ? (
                          <div className="dma-wizard-form-grid" style={{ marginTop: '0.85rem' }}>
                            <label style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                              <span>Profession</span>
                              <Input aria-label="Profession" value={String(strategySummary.profession_name || '')} onChange={(_, data) => updateStrategySummaryField('profession_name', data.value)} disabled={readOnly} />
                            </label>
                            <label style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                              <span>Location focus</span>
                              <Input aria-label="Location focus" value={String(strategySummary.location_focus || '')} onChange={(_, data) => updateStrategySummaryField('location_focus', data.value)} disabled={readOnly} />
                            </label>
                            <label style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                              <span>Customer profile</span>
                              <Textarea aria-label="Customer profile" value={String(strategySummary.customer_profile || '')} onChange={(_, data) => updateStrategySummaryField('customer_profile', data.value)} disabled={readOnly} resize="vertical" rows={3} />
                            </label>
                            <label style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                              <span>Service focus</span>
                              <Textarea aria-label="Service focus" value={String(strategySummary.service_focus || '')} onChange={(_, data) => updateStrategySummaryField('service_focus', data.value)} disabled={readOnly} resize="vertical" rows={3} />
                            </label>
                            <label style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                              <span>Differentiator</span>
                              <Textarea aria-label="Differentiator" value={String(strategySummary.signature_differentiator || '')} onChange={(_, data) => updateStrategySummaryField('signature_differentiator', data.value)} disabled={readOnly} resize="vertical" rows={3} />
                            </label>
                            <label style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                              <span>Business goal</span>
                              <Textarea aria-label="Business goal" value={String(strategySummary.business_goal || '')} onChange={(_, data) => updateStrategySummaryField('business_goal', data.value)} disabled={readOnly} resize="vertical" rows={3} />
                            </label>
                            <label style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                              <span>First content direction</span>
                              <Textarea aria-label="First content direction" value={String(strategySummary.first_content_direction || '')} onChange={(_, data) => updateStrategySummaryField('first_content_direction', data.value)} disabled={readOnly} resize="vertical" rows={3} />
                            </label>
                            <label style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                              <span>Tone</span>
                              <Input aria-label="Tone" value={String(strategySummary.tone || '')} onChange={(_, data) => updateStrategySummaryField('tone', data.value)} disabled={readOnly} />
                            </label>
                            <label style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                              <span>Content pillars</span>
                              <Textarea aria-label="Content pillars" value={formatListForTextarea(strategySummary.content_pillars)} onChange={(_, data) => updateStrategySummaryField('content_pillars', parseListTextarea(data.value))} disabled={readOnly} resize="vertical" rows={3} />
                            </label>
                            <label style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                              <span>Call to action</span>
                              <Textarea aria-label="Call to action" value={String(strategySummary.cta || '')} onChange={(_, data) => updateStrategySummaryField('cta', data.value)} disabled={readOnly} resize="vertical" rows={3} />
                            </label>
                          </div>
                        ) : null}
                      </div>

                      <DigitalMarketingThemePlanCard
                        masterTheme={masterTheme}
                        derivedThemes={derivedThemes}
                        editable
                        saving={themePlanSaving}
                        loading={themePlanLoading}
                        error={themePlanError}
                        onMasterThemeChange={setMasterTheme}
                        onDerivedThemeChange={updateDerivedTheme}
                        onAddDerivedTheme={addDerivedTheme}
                        onSave={() => void saveThemePlan()}
                      />

                      <StrategyPreviewPanel
                        isThemeApproved={isThemeApproved}
                        masterTheme={masterTheme}
                        derivedThemes={derivedThemes}
                        strategySummary={strategySummary}
                        fallbackSummary={strategyWorkshop.checkpoint_summary || strategyWorkshop.assistant_message || ''}
                        messages={strategyPreviewMessages}
                      />
                      <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center', flexWrap: 'wrap' }}>
                        <Button
                          appearance="primary"
                          disabled={readOnly || themePlanSaving || !masterTheme.trim()}
                          onClick={() => void approveThemeStrategy()}
                          data-testid="approve-theme-strategy-btn"
                        >
                          {isThemeApproved ? 'Strategy approved' : 'Approve strategy'}
                        </Button>
                        {isThemeApproved ? (
                          <span style={{ color: '#10b981', fontSize: '0.85rem' }}>Draft generation is now unlocked.</span>
                        ) : (
                          <span style={{ opacity: 0.7, fontSize: '0.85rem' }}>Approve only when the positioning and content lanes feel final.</span>
                        )}
                      </div>

                      {renderDraftGenerationPanel()}
                    </div>

                    {/* SECONDARY: Optional structured business fields (collapsed by default) */}
                    <details style={{ marginTop: '1rem' }}>
                      <summary style={{ cursor: 'pointer', fontWeight: 600, padding: '0.75rem', background: 'var(--colorNeutralBackground3)', borderRadius: '8px' }}>
                        Optional business context fields
                      </summary>
                      <div style={{ marginTop: '1rem', padding: '1rem', border: '1px solid var(--colorNeutralStroke2)', borderRadius: '8px' }}>
                        <div className="dma-wizard-section-label" style={{ marginBottom: '0.75rem' }}>Direct input fields</div>
                        <div style={{ opacity: 0.75, fontSize: '0.85rem', marginBottom: '1rem' }}>
                          The assistant will ask for most of this progressively. Use these only if you already know the exact inputs.
                        </div>
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
                        <details style={{ marginTop: '1rem' }}>
                          <summary style={{ cursor: 'pointer', fontWeight: 600, marginBottom: '0.75rem' }}>Brand Voice</summary>
                          <div style={{ display: 'grid', gap: '0.85rem', marginTop: '0.75rem' }}>
                            {brandVoiceLoading ? <Spinner size="tiny" /> : null}
                            <label style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                              <span>Voice description</span>
                              <Textarea
                                aria-label="Voice description"
                                value={voiceDescription}
                                onChange={(_, data) => setVoiceDescription(data.value)}
                                disabled={readOnly}
                                resize="vertical"
                                rows={3}
                                placeholder="Describe how your brand should sound."
                              />
                            </label>
                            <label style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                              <span>Tone keywords</span>
                              <Input
                                aria-label="Tone keywords"
                                value={toneKeywords}
                                onChange={(_, data) => setToneKeywords(data.value)}
                                disabled={readOnly}
                                placeholder="e.g. warm, credible, direct"
                              />
                            </label>
                            <label style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                              <span>Example phrases</span>
                              <Textarea
                                aria-label="Example phrases"
                                value={examplePhrases}
                                onChange={(_, data) => setExamplePhrases(data.value)}
                                disabled={readOnly}
                                resize="vertical"
                                rows={4}
                                placeholder="One phrase per line"
                              />
                            </label>
                          </div>
                        </details>
                      </div>
                    </details>
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

export function StrategyPreviewPanel({
  isThemeApproved,
  masterTheme,
  derivedThemes,
  strategySummary,
  fallbackSummary = '',
  messages,
}: {
  isThemeApproved: boolean
  masterTheme?: string
  derivedThemes?: DigitalMarketingDerivedTheme[]
  strategySummary: DigitalMarketingStrategyWorkshopSummary | string
  fallbackSummary?: string
  messages: Array<{ role: 'assistant' | 'user'; content: string }>
}) {
  if (isThemeApproved) return null

  const strictPreviewMode = masterTheme !== undefined || derivedThemes !== undefined
  const resolvedMasterTheme = masterTheme || ''
  const resolvedDerivedThemes = derivedThemes || []
  const hasPreview = Boolean(resolvedMasterTheme.trim()) || resolvedDerivedThemes.length > 0
  const thread = messages.slice(-5)
  const summary = typeof strategySummary === 'string'
    ? strategySummary
    : strategySummary.first_content_direction
      || strategySummary.business_goal
      || strategySummary.positioning
      || fallbackSummary

  if (!hasPreview) {
    if (strictPreviewMode) return null
    if (!summary) return null

    return (
      <div style={{ marginBottom: '1rem', padding: '1rem', border: '1px solid #333', borderRadius: '0.75rem', background: '#1a1a1a' }}>
        <h4 style={{ margin: '0 0 0.5rem', color: '#00f2fe' }}>Review your content strategy before approving</h4>
        <blockquote style={{ borderLeft: '3px solid #667eea', paddingLeft: '1rem', margin: '0.5rem 0', color: '#ccc' }}>
          {summary}
        </blockquote>
        {thread.map((msg, index) => (
          <div key={`${msg.role}-${index}`} style={{ margin: '0.25rem 0', color: msg.role === 'assistant' ? '#00f2fe' : '#ccc' }}>
            <strong>{msg.role === 'assistant' ? 'Agent' : 'You'}:</strong> {msg.content}
          </div>
        ))}
      </div>
    )
  }

  return (
    <Card style={{ padding: '1rem', marginBottom: '1rem', background: 'var(--colorNeutralBackground3)' }}>
      <div style={{ fontSize: '0.8rem', textTransform: 'uppercase', letterSpacing: '0.06em', opacity: 0.7, marginBottom: '0.5rem' }}>
        Strategy Preview — review before approving
      </div>
      {resolvedMasterTheme ? (
        <div style={{ fontWeight: 600, fontSize: '1.05rem', marginBottom: '0.5rem' }}>
          Master Theme: {resolvedMasterTheme}
        </div>
      ) : null}
      {resolvedDerivedThemes.length > 0 ? (
        <div style={{ marginBottom: '0.75rem' }}>
          <div style={{ fontWeight: 500, marginBottom: '0.25rem' }}>Derived Themes:</div>
          <ul style={{ margin: 0, paddingLeft: '1.25rem' }}>
            {resolvedDerivedThemes.map((theme, index) => (
              <li key={`${theme.title}-${index}`} style={{ marginBottom: '0.25rem' }}>
                <strong>{theme.title}</strong>
                {theme.description ? ` — ${theme.description}` : ''}
              </li>
            ))}
          </ul>
        </div>
      ) : null}
      {typeof strategySummary !== 'string' ? (
        <div style={{ display: 'grid', gap: '0.25rem', marginBottom: thread.length ? '0.75rem' : 0 }}>
          {strategySummary.business_goal ? <div><strong>Business goal:</strong> {strategySummary.business_goal}</div> : null}
          {strategySummary.positioning ? <div><strong>Positioning:</strong> {strategySummary.positioning}</div> : null}
          {strategySummary.first_content_direction ? <div><strong>First content direction:</strong> {strategySummary.first_content_direction}</div> : null}
        </div>
      ) : summary ? (
        <div style={{ marginBottom: thread.length ? '0.75rem' : 0 }}>{summary}</div>
      ) : null}
      {thread.map((msg, index) => (
        <div key={`${msg.role}-${index}`} style={{ margin: '0.25rem 0', color: msg.role === 'assistant' ? '#00f2fe' : '#ccc' }}>
          <strong>{msg.role === 'assistant' ? 'Agent' : 'You'}:</strong> {msg.content}
        </div>
      ))}
    </Card>
  )
}

export default DigitalMarketingActivationWizard
