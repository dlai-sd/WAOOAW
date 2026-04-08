import { Badge, Button, Card, Spinner, Text, Input, Textarea } from '@fluentui/react-components'
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
  { id: 'connect',   title: 'Channel Ready',        description: 'Anchor this hire to the exact YouTube identity it should work through.' },
  { id: 'theme',     title: 'Brief Chat',           description: 'Brief the DMA like a strategist and approve the direction it extracts.' },
  { id: 'schedule',  title: 'Plan',                 description: 'Confirm the publishing rhythm once the strategy feels right.' },
  { id: 'activate',  title: 'Review & Activate',    description: 'Review the brief, channel state, and activation blockers in one place.' },
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

function buildDmaIntroduction(options: {
  brandName: string
  businessLabel: string
  location: string
  customerProfile: string
  goal: string
}): string {
  const brandName = String(options.brandName || '').trim()
  const businessLabel = String(options.businessLabel || '').trim() || brandName || 'your business'
  const location = String(options.location || '').trim()
  const customerProfile = String(options.customerProfile || '').trim()
  const goal = String(options.goal || '').trim()

  const businessDescriptor = brandName && businessLabel !== brandName
    ? `${businessLabel} for ${brandName}`
    : businessLabel
  const locationDescriptor = location ? `, located in ${location}` : ''
  const audienceDescriptor = customerProfile ? `, serving ${customerProfile}` : ''
  const goalDescriptor = goal
    ? ` My working objective is to turn that into content that supports ${goal}.`
    : ' My working objective is to turn that into content your customers trust, engage with, and act on.'

  return `Let me introduce myself quickly. I am your Digital Marketing Agent from WAOOAW. Based on what I know so far, I understand your business is ${businessDescriptor}${locationDescriptor}${audienceDescriptor}.${goalDescriptor} I will tighten the brief with you, connect the right channel, and only move to drafts after you approve the direction.`
}

function formatBusinessSnapshot(value: string, fallback: string): string {
  return String(value || '').trim() || fallback
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
  const [activeStepIndex, setActiveStepIndex] = useState(1)
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
  const chatScrollRef = useRef<HTMLDivElement | null>(null)
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
    if (!activeInstance?.subscription_id) return
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
  const offeringsList = useMemo(() => parseListTextarea(offeringsText), [offeringsText])
  const businessLabel = useMemo(() => {
    return formatBusinessSnapshot(
      String(strategySummary.profession_name || strategySummary.service_focus || strategySummary.business_focus || brandName).trim(),
      'Waiting for business type',
    )
  }, [brandName, strategySummary.business_focus, strategySummary.profession_name, strategySummary.service_focus])
  const locationLabel = useMemo(() => {
    return formatBusinessSnapshot(
      String(strategySummary.location_focus || location).trim(),
      'Waiting for service area',
    )
  }, [location, strategySummary.location_focus])
  const audienceLabel = useMemo(() => {
    return formatBusinessSnapshot(
      String(strategySummary.customer_profile || strategySummary.audience).trim(),
      'Waiting for target customers',
    )
  }, [strategySummary.audience, strategySummary.customer_profile])
  const serviceFocusLabel = useMemo(() => {
    return formatBusinessSnapshot(
      String(strategySummary.service_focus || strategySummary.business_focus || offeringsList[0] || '').trim(),
      'Waiting for core offer',
    )
  }, [offeringsList, strategySummary.business_focus, strategySummary.service_focus])
  const differentiatorLabel = useMemo(() => {
    return formatBusinessSnapshot(
      String(strategySummary.signature_differentiator || strategySummary.positioning).trim(),
      'Waiting for differentiation',
    )
  }, [strategySummary.positioning, strategySummary.signature_differentiator])
  const goalLabel = useMemo(() => {
    return formatBusinessSnapshot(
      String(strategySummary.business_goal || businessContext).trim(),
      'Waiting for the business goal',
    )
  }, [businessContext, strategySummary.business_goal])
  const firstDirectionLabel = useMemo(() => {
    return formatBusinessSnapshot(
      String(strategySummary.first_content_direction || strategySummary.youtube_angle || masterTheme).trim(),
      'Waiting for the first content direction',
    )
  }, [masterTheme, strategySummary.first_content_direction, strategySummary.youtube_angle])
  const dmaIntroduction = useMemo(() => {
    return buildDmaIntroduction({
      brandName,
      businessLabel,
      location: String(strategySummary.location_focus || location || '').trim(),
      customerProfile: String(strategySummary.customer_profile || strategySummary.audience || '').trim(),
      goal: String(strategySummary.business_goal || businessContext || '').trim(),
    })
  }, [brandName, businessContext, businessLabel, location, strategySummary.audience, strategySummary.business_goal, strategySummary.customer_profile, strategySummary.location_focus])
  const conversationHistory = useMemo(
    () => (strategyWorkshop.messages || []).slice(-10),
    [strategyWorkshop.messages],
  )
  const isFirstConversation = conversationHistory.length === 0
    && !String(strategyWorkshop.assistant_message || '').trim()
    && !String(strategyWorkshop.checkpoint_summary || '').trim()
  const openingAssistantMessage = useMemo(() => {
    if (isFirstConversation) {
      return `Tell me what your business does, who you most want to reach, and the first result you want this content to drive. I will tighten the brief with you here and keep this moving without turning it into setup busywork.`
    }
    if (strategyWorkshop.assistant_message) return strategyWorkshop.assistant_message
    return `I have picked the conversation back up and I am ready to tighten the brief, unblock the next decision, and move this toward approved publishing.`
  }, [isFirstConversation, strategyWorkshop.assistant_message])
  const chatMessages = useMemo(() => {
    const messages = conversationHistory
      .map((message) => ({
        role: message.role === 'assistant' ? 'assistant' : 'user',
        content: String(message.content || '').trim(),
      }))
      .filter((message) => message.content)

    if (messages.length === 0) {
      return [{ role: 'assistant' as const, content: openingAssistantMessage }]
    }

    const latestAssistantMessage = String(strategyWorkshop.assistant_message || '').trim()
    const lastMessage = messages[messages.length - 1]
    if (
      latestAssistantMessage
      && (lastMessage?.role !== 'assistant' || lastMessage.content !== latestAssistantMessage)
    ) {
      messages.push({ role: 'assistant', content: latestAssistantMessage })
    }

    return messages
  }, [conversationHistory, openingAssistantMessage, strategyWorkshop.assistant_message])

  useEffect(() => {
    const chatScrollElement = chatScrollRef.current
    if (!chatScrollElement) return
    chatScrollElement.scrollTop = chatScrollElement.scrollHeight
  }, [chatMessages.length, themePlanLoading])

  const canSendStrategyReply = Boolean(strategyReply.trim()) && !readOnly && !themePlanLoading
  const operatingChecklist = useMemo(() => ([
    {
      label: 'YouTube identity attached',
      ok: !selectedPlatforms.includes('youtube') || isYouTubeAttached,
    },
    {
      label: 'Business brief understood',
      ok: readiness.brief_complete || missingProfileFields.length === 0,
    },
    {
      label: 'Strategy approved',
      ok: isThemeApproved,
    },
    {
      label: 'Publishing plan confirmed',
      ok: Boolean(scheduleStartDate.trim()),
    },
  ]), [isThemeApproved, isYouTubeAttached, missingProfileFields.length, readiness.brief_complete, scheduleStartDate, selectedPlatforms])
  const nextActionCopy = useMemo(() => {
    if (currentStep.id === 'connect') {
      return isYouTubeAttached
        ? 'The channel identity is attached. Continue into the brief so I can shape the first content direction.'
        : 'Connect and test the YouTube channel you want me to operate so I can work on the correct publishing identity.'
    }
    if (currentStep.id === 'theme') {
      return isThemeApproved
        ? 'The strategic direction is approved. Move to planning so we can lock the publishing rhythm.'
        : 'Give me the sharpest possible answer to the next question. I will turn that into a tighter business brief and first content direction.'
    }
    if (currentStep.id === 'schedule') {
      return scheduleStartDate.trim()
        ? 'The schedule is set. Review activation readiness before turning this hire fully on.'
        : 'Choose when the first publishing cycle should start and how often this hire should post.'
    }
    if (readiness.can_finalize) {
      return 'Everything required for activation is in place. Review the brief on the right, then activate the DMA.'
    }
    if (readiness.missing_requirements?.length) {
      return `Resolve these blockers before activation: ${readiness.missing_requirements.join(', ')}.`
    }
    return 'Review the brief and readiness checks, then activate when the business direction feels correct.'
  }, [currentStep.id, isThemeApproved, isYouTubeAttached, readiness.can_finalize, readiness.missing_requirements, scheduleStartDate])
  const stageStateLabel = useMemo(() => {
    if (currentStep.id === 'connect') return isYouTubeAttached ? 'Channel attached' : 'Waiting for channel'
    if (currentStep.id === 'theme') return isThemeApproved ? 'Strategy approved' : 'Conversation in progress'
    if (currentStep.id === 'schedule') return scheduleStartDate.trim() ? 'Cadence set' : 'Cadence needed'
    return readiness.can_finalize ? 'Ready to activate' : 'Review blockers'
  }, [currentStep.id, isThemeApproved, isYouTubeAttached, readiness.can_finalize, scheduleStartDate])

  useEffect(() => {
    if (currentStep.id === 'connect') {
      setActiveMilestone('prepare')
      return
    }
    if (currentStep.id === 'theme') {
      setActiveMilestone('theme')
      return
    }
    if (currentStep.id === 'schedule') {
      setActiveMilestone('schedule')
      return
    }
    setActiveMilestone('induct')
  }, [currentStep.id])

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

  const buildActivationWorkspacePayload = (): UpsertDigitalMarketingActivationInput => {
    const offeringsServices = parseListTextarea(offeringsText)
    const platformBindings = buildMarketingPlatformBindings(
      selectedPlatforms,
      activation?.workspace.platform_bindings,
      'default'
    )

    return {
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
  }

  const persistWorkspaceSnapshot = async ({ updateIndicators = true }: { updateIndicators?: boolean } = {}): Promise<boolean> => {
    if (readOnly) return true

    if (updateIndicators) {
      setSaveStatus('saving')
      setSaveError(null)
    }

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

      const { activation: savedActivation, draft: recoveredDraft } = await saveActivationWorkspaceWithRecovery(
        savedDraft.hired_instance_id,
        buildActivationWorkspacePayload(),
      )

      const refreshedDraft = await getHiredAgentBySubscription(activeInstance.subscription_id).catch(() => ({
        ...savedDraft,
        ...(recoveredDraft || {}),
        configured: savedActivation.readiness.configured,
      }))

      setDraft(refreshedDraft)
      setActivation(savedActivation)
      if (updateIndicators) {
        setSaveStatus('saved')
      }
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
      const message = isNotFoundError(e)
        ? 'This hire is no longer available. Please select another agent.'
        : e?.message || 'Failed to save activation workspace'

      setSaveError(message)
      setSaveStatus('error')

      if (isNotFoundError(e)) {
        await onStaleReference?.({
          subscriptionId: activeInstance?.subscription_id || '',
          hiredInstanceId,
        })
      }
      return false
    }
  }

  const saveWorkspace = async (): Promise<boolean> => {
    return persistWorkspaceSnapshot({ updateIndicators: true })
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
  }

  const generateThemePlan = async (overrideReply?: string) => {
    if (!hiredInstanceId) return
    setThemePlanLoading(true)
    setThemePlanError(null)
    try {
      const pendingInput = String(overrideReply ?? strategyReply).trim()
      const response = await generateDigitalMarketingThemePlan(hiredInstanceId, {
        ...buildActivationWorkspacePayload(),
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
      void persistWorkspaceSnapshot({ updateIndicators: false })
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
                  style={{ padding: '0.85rem', border: '1px solid var(--colorNeutralStroke2)', borderRadius: '10px', background: 'color-mix(in srgb, var(--colorNeutralBackground3) 76%, transparent)' }}
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
                      <a href={receiptUrl} target="_blank" rel="noopener noreferrer" style={{ color: 'var(--colorBrandForegroundLink)' }} data-testid={`publish-receipt-${post.post_id}`}>
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

  const renderYouTubeControlRail = () => (
    <details open={!isYouTubeAttached} data-testid="dma-step-panel-connect">
      <summary style={{ cursor: 'pointer', fontWeight: 600 }}>YouTube connection</summary>
      <div style={{ display: 'grid', gap: '0.85rem', marginTop: '0.9rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', gap: '0.75rem', alignItems: 'center', flexWrap: 'wrap' }}>
          <div>
            <div style={{ fontWeight: 600 }}>Publishing identity</div>
            <div style={{ opacity: 0.75, fontSize: '0.9rem' }}>
              Connect the YouTube channel this DMA should grow and publish through.
            </div>
          </div>
          <Badge appearance="outline" color={isYouTubeAttached ? 'success' : 'warning'}>
            {isYouTubeAttached ? 'Connected' : 'Needs connection'}
          </Badge>
        </div>

        {savedYouTubeConnection?.display_name ? (
          <div style={{ fontSize: '0.9rem' }}>
            Channel: <strong>{savedYouTubeConnection.display_name}</strong>
          </div>
        ) : null}

        <div style={{ display: 'flex', gap: '0.65rem', flexWrap: 'wrap' }}>
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
              {youtubePersistLoading ? 'Saving…' : 'Save for DMA'}
            </Button>
          ) : null}
        </div>

        {youtubeValidationResult ? (
          <div
            data-testid="youtube-validation-metrics"
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(8rem, 1fr))',
              gap: '0.75rem',
              padding: '0.9rem 1rem',
              border: '1px solid color-mix(in srgb, var(--colorBrandStroke1) 45%, var(--colorNeutralStroke2))',
              borderRadius: '0.9rem',
              background: 'color-mix(in srgb, var(--colorBrandBackground2) 12%, var(--colorNeutralBackground3))',
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
              border: '1px solid var(--colorNeutralStroke2)',
              borderRadius: '0.9rem',
              background: 'color-mix(in srgb, var(--colorNeutralBackground3) 74%, transparent)',
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
                    background: 'color-mix(in srgb, var(--colorBrandBackground2) 12%, var(--colorNeutralBackground3))',
                    border: '1px solid color-mix(in srgb, var(--colorBrandStroke1) 38%, var(--colorNeutralStroke2))',
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
              border: '1px solid color-mix(in srgb, var(--colorPaletteDarkOrangeBorder2) 70%, transparent)',
              background: 'color-mix(in srgb, var(--colorPaletteDarkOrangeBackground2) 55%, transparent)',
              color: 'var(--colorPaletteDarkOrangeForeground1)',
              fontSize: '0.95rem',
            }}
          >
            {getYouTubeNextActionCopy(youtubeValidationResult?.next_action_hint)}
          </div>
        ) : null}

        {oauthMessage && <div className="dma-wizard-oauth-success">{oauthMessage}</div>}
        {youtubeValidationError && <div className="dma-wizard-oauth-error">{youtubeValidationError}</div>}
        {oauthError && <div className="dma-wizard-oauth-error">{oauthError}</div>}
      </div>
    </details>
  )

  const renderBusinessContextRail = () => (
    <details open={!brandName.trim() || !location.trim()} data-testid="dma-step-panel-business">
      <summary style={{ cursor: 'pointer', fontWeight: 600 }}>Business details</summary>
      <div style={{ display: 'grid', gap: '0.9rem', marginTop: '0.9rem' }}>
        <div style={{ opacity: 0.75, fontSize: '0.9rem' }}>
          Use this only when you want to pin details directly instead of saying them in chat.
        </div>
        <div className="dma-wizard-form-grid">
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
        <label style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
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
        <details>
          <summary style={{ cursor: 'pointer', fontWeight: 600 }}>Brand voice</summary>
          <div style={{ display: 'grid', gap: '0.85rem', marginTop: '0.8rem' }}>
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
  )

  const renderStrategyControlRail = () => (
    <details open={!isThemeApproved} data-testid="dma-step-panel-theme">
      <summary style={{ cursor: 'pointer', fontWeight: 600 }}>Strategy controls</summary>
      <div style={{ display: 'grid', gap: '1rem', marginTop: '0.9rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', gap: '0.75rem', alignItems: 'center', flexWrap: 'wrap' }}>
          <div>
            <div style={{ fontWeight: 600 }}>Direction and approvals</div>
            <div style={{ opacity: 0.75, fontSize: '0.9rem' }}>
              I will keep turning the conversation into a sharper brief and an approval-ready content direction.
            </div>
          </div>
          <Badge
            appearance="outline"
            color={isThemeApproved ? 'success' : strategyWorkshop.status === 'approval_ready' ? 'informative' : 'warning'}
            data-testid="strategy-workshop-status"
          >
            {isThemeApproved ? 'Approved' : strategyWorkshop.status === 'approval_ready' ? 'Ready for approval' : 'Discovery in progress'}
          </Badge>
        </div>

        <StrategyPreviewPanel
          isThemeApproved={isThemeApproved}
          masterTheme={masterTheme}
          derivedThemes={derivedThemes}
          strategySummary={strategySummary}
          fallbackSummary={strategyWorkshop.checkpoint_summary || strategyWorkshop.assistant_message || ''}
          messages={strategyPreviewMessages}
        />

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
            <span style={{ color: 'var(--colorPaletteGreenForeground1)', fontSize: '0.85rem' }}>Draft generation is now unlocked.</span>
          ) : (
            <span style={{ opacity: 0.7, fontSize: '0.85rem' }}>Approve when the positioning and content lanes feel commercially right.</span>
          )}
        </div>

        {renderDraftGenerationPanel()}
      </div>
    </details>
  )

  const renderScheduleControlRail = () => (
    <details open={isThemeApproved && !scheduleStartDate.trim()} data-testid="dma-step-panel-schedule">
      <summary style={{ cursor: 'pointer', fontWeight: 600 }}>Publishing cadence</summary>
      <div style={{ display: 'grid', gap: '1rem', marginTop: '0.9rem' }}>
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
                    border: `1px solid ${isSelected ? 'color-mix(in srgb, var(--colorBrandStroke1) 70%, transparent)' : 'var(--colorNeutralStroke2)'}`,
                    background: isSelected
                      ? 'color-mix(in srgb, var(--colorBrandBackground2) 18%, var(--colorNeutralBackground3))'
                      : 'color-mix(in srgb, var(--colorNeutralBackground3) 76%, transparent)',
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
            Schedule set: {postsPerWeek || '3'}x/week from {scheduleStartDate}
          </Badge>
        ) : (
          <div style={{ opacity: 0.6, fontSize: '0.9rem' }}>Set the first publishing date to lock the cadence.</div>
        )}
      </div>
    </details>
  )

  const renderActivationControlRail = () => (
    <details open={!readiness.can_finalize} data-testid="dma-step-panel-activate">
      <summary style={{ cursor: 'pointer', fontWeight: 600 }}>Activation controls</summary>
      <div style={{ display: 'grid', gap: '1rem', marginTop: '0.9rem' }}>
        <div style={{ border: '1px solid var(--colorNeutralStroke2)', borderRadius: '14px', overflow: 'hidden' }}>
          {[
            { label: 'Agent identity configured', ok: readiness.configured },
            { label: 'Business brief complete', ok: readiness.brief_complete },
            { label: 'Platform connections ready', ok: !readiness.youtube_selected || readiness.youtube_connection_ready },
            { label: 'Campaign theme generated', ok: Boolean(masterTheme) },
          ].map(({ label, ok }) => (
            <div key={label} className="dma-wizard-review-row" style={{ padding: '0.85rem 1rem' }}>
              <span>{label}</span>
              <Badge appearance="outline" color={ok ? 'success' : 'warning'}>
                {ok ? 'Ready' : 'Incomplete'}
              </Badge>
            </div>
          ))}
        </div>

        {readiness.missing_requirements?.length > 0 ? (
          <FeedbackMessage
            intent="warning"
            title="Complete these before activating"
            message={readiness.missing_requirements.join(' · ')}
          />
        ) : null}

        {finishStatus === 'success' || activation?.workspace.activation_complete ? (
          <FeedbackMessage intent="success" title="Setup complete" message="This hire now has channels, theme plan, and schedule confirmed." />
        ) : null}

        {finishError ? <FeedbackMessage intent="error" title="Activation failed" message={finishError} /> : null}

        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center', flexWrap: 'wrap' }}>
          <Button
            appearance="primary"
            onClick={() => void finishActivation()}
            disabled={readOnly || finishStatus === 'saving' || !readiness.can_finalize}
          >
            {finishStatus === 'saving' ? 'Activating…' : 'Activate Agent'}
          </Button>
          <Button
            appearance="secondary"
            onClick={() => {
              void saveWorkspace()
              void saveProfile()
              void saveBrandVoice()
            }}
            disabled={readOnly || saveStatus === 'saving'}
          >
            {saveStatus === 'saving' ? 'Saving…' : 'Save progress'}
          </Button>
        </div>
      </div>
    </details>
  )

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

  const handleStrategySubmit = () => {
    if (!canSendStrategyReply) return
    void generateThemePlan()
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
        <section className="dma-wizard-main">
          <Card className="dma-wizard-main-card">
            <div className="dma-chat-shell" data-testid="dma-conversation-hero">
              <div className="dma-chat-header">
                <div>
                  <div className="dma-wizard-section-label">Digital Marketing Agent</div>
                  <Text as="h2" size={600} weight="semibold">Chat with your DMA</Text>
                </div>
                <div className="dma-chat-header-badges">
                  <Badge appearance="outline" color={isThemeApproved ? 'success' : 'informative'}>{stageStateLabel}</Badge>
                  <Badge appearance="outline" color={readiness.can_finalize ? 'success' : 'warning'}>{completedMilestones}/5 signals locked</Badge>
                </div>
              </div>
            </div>

            <div className="dma-wizard-main-body">
              <div className="dma-wizard-canvas-body">
                <div className="dma-wizard-step-content" data-testid="dma-chat-primary-panel">
                  <div className="dma-chat-thread" data-testid="dma-chat-thread">
                    <div className="dma-chat-scroll-region" ref={chatScrollRef} data-testid="dma-chat-scroll-region">
                      <div className="dma-chat-message-stack" data-testid="dma-chat-message-stack">
                        {chatMessages.map((message, index) => (
                          <div
                            key={`${message.role}-${index}-${message.content.slice(0, 24)}`}
                            className={`dma-wizard-theme-workshop-message${message.role === 'assistant' ? ' dma-wizard-theme-workshop-message--assistant' : ' dma-wizard-theme-workshop-message--user'}`}
                            data-testid={message.role === 'assistant' && index === chatMessages.length - 1 ? 'strategy-assistant-message' : undefined}
                          >
                            <div>{message.content}</div>
                          </div>
                        ))}

                        {themePlanLoading ? (
                          <div
                            className="dma-wizard-theme-workshop-message dma-wizard-theme-workshop-message--assistant dma-wizard-theme-workshop-message--pending"
                            data-testid="strategy-thinking-indicator"
                          >
                            <div>Thinking through the brief and tightening the next decision...</div>
                          </div>
                        ) : null}
                      </div>

                      {strategyWorkshop.checkpoint_summary ? (
                        <div className="dma-chat-insight-card" data-testid="strategy-checkpoint-summary">
                          <div className="dma-chat-insight-label">What I have already understood</div>
                          <div>{strategyWorkshop.checkpoint_summary}</div>
                        </div>
                      ) : null}

                      {strategyWorkshop.current_focus_question ? (
                        <div className="dma-chat-focus-card" data-testid="strategy-current-focus-question">
                          <div className="dma-chat-insight-label">Best next answer</div>
                          <div>{strategyWorkshop.current_focus_question}</div>
                        </div>
                      ) : null}

                      {(strategyWorkshop.next_step_options || []).length > 0 ? (
                        <div className="dma-chat-quick-replies">
                          <div style={{ fontWeight: 600, marginBottom: '0.45rem' }}>Quick replies</div>
                          <div className="dma-wizard-theme-option-list">
                            {(strategyWorkshop.next_step_options || []).map((option, index) => (
                              <Button
                                key={`${option}-${index}`}
                                type="button"
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
                    </div>

                    <div className="dma-chat-composer" data-testid="dma-chat-composer">
                      <div className="dma-chat-composer-header">
                        <div style={{ fontWeight: 600 }}>Keep feeding the brief</div>
                        <div className="dma-chat-composer-hint">Press Enter to send. Use Shift+Enter for a new line.</div>
                      </div>
                      <div className="dma-chat-composer-body">
                        <label className="dma-chat-composer-field">
                          <span style={{ fontWeight: 600 }}>Message your DMA</span>
                          <Textarea
                            aria-label="Strategy workshop reply"
                            value={strategyReply}
                            onChange={(_, data) => setStrategyReply(data.value)}
                            onKeyDown={(event) => {
                              if (event.key === 'Enter' && !event.shiftKey) {
                                event.preventDefault()
                                handleStrategySubmit()
                              }
                            }}
                            disabled={readOnly || themePlanLoading}
                            resize="vertical"
                            rows={4}
                            placeholder="Tell me more about your business, customers, offer, objections, proof, and the exact result you want this content to create."
                          />
                        </label>

                        <div className="dma-chat-composer-actions">
                          <Button
                            type="button"
                            appearance="primary"
                            onClick={handleStrategySubmit}
                            disabled={!canSendStrategyReply}
                            data-testid="start-theme-workshop-btn"
                          >
                            Send
                          </Button>
                          {!strategyReply.trim() ? (
                            <span className="dma-chat-composer-empty-state">
                              Share more context and I will keep sharpening the brief without forcing you through setup fields.
                            </span>
                          ) : null}
                        </div>
                      </div>
                      {themePlanError ? (
                        <FeedbackMessage intent="error" title="DMA reply failed" message={themePlanError} />
                      ) : null}
                    </div>

                    <SaveIndicator status={saveStatus} errorMessage={saveError || undefined} />
                  </div>
                </div>
 
            </div>
            </div>
          </Card>
        </section>

        <aside className="dma-wizard-brief-panel">
          <Card className="dma-wizard-brief-card">
            <div className="dma-wizard-brief-card-header">
              <div>
                <div className="dma-wizard-section-label">Live business brief</div>
                <Text as="h3" size={500} weight="semibold">What the DMA understands so far</Text>
              </div>
              <Badge appearance="outline" color={readiness.can_finalize ? 'success' : 'warning'}>
                {readiness.can_finalize ? 'Activation ready' : 'Still shaping'}
              </Badge>
            </div>

            <div className="dma-wizard-brief-summary" data-testid="dma-live-brief">
              <div className="dma-wizard-brief-summary-card"><span>Business</span><strong>{businessLabel}</strong></div>
              <div className="dma-wizard-brief-summary-card"><span>Location</span><strong>{locationLabel}</strong></div>
              <div className="dma-wizard-brief-summary-card"><span>Target customers</span><strong>{audienceLabel}</strong></div>
              <div className="dma-wizard-brief-summary-card"><span>Core offer</span><strong>{serviceFocusLabel}</strong></div>
              <div className="dma-wizard-brief-summary-card"><span>Differentiator</span><strong>{differentiatorLabel}</strong></div>
              <div className="dma-wizard-brief-summary-card"><span>First content direction</span><strong>{firstDirectionLabel}</strong></div>
            </div>
          </Card>

          <Card className="dma-wizard-brief-card">
            <div className="dma-wizard-section-label">Business objective</div>
            <Text as="p" size={300}>{goalLabel}</Text>
            {(strategySummary.content_pillars || []).length > 0 ? (
              <div className="dma-wizard-pill-list">
                {(strategySummary.content_pillars || []).map((pillar, index) => (
                  <Badge key={`${pillar}-${index}`} appearance="filled" color="informative">{pillar}</Badge>
                ))}
              </div>
            ) : null}
          </Card>

          <Card className="dma-wizard-brief-card">
            <div className="dma-wizard-section-label">Operating status</div>
            <div className="dma-wizard-status-list">
              {operatingChecklist.map((item) => (
                <div key={item.label} className={`dma-wizard-status-item${item.ok ? ' is-done' : ''}`}>
                  <span className="dma-wizard-status-item-label">{item.label}</span>
                  <Badge appearance="outline" color={item.ok ? 'success' : 'warning'}>
                    {item.ok ? 'Ready' : 'Pending'}
                  </Badge>
                </div>
              ))}
            </div>
          </Card>

          <Card className="dma-wizard-brief-card">
            <div className="dma-wizard-section-label">Next action</div>
            <Text as="p" size={300} data-testid="dma-next-action-copy">{nextActionCopy}</Text>
            {missingProfileFields.length > 0 ? (
              <div className="dma-wizard-copy-card dma-wizard-copy-card--compact">
                Missing brief details: {missingProfileFields.join(', ')}.
              </div>
            ) : null}
          </Card>

          <Card className="dma-wizard-brief-card">
            <div className="dma-wizard-section-label">Setup controls</div>
            <div style={{ display: 'grid', gap: '1rem' }}>
              {renderBusinessContextRail()}
              {renderYouTubeControlRail()}
              {renderStrategyControlRail()}
              {renderScheduleControlRail()}
              {renderActivationControlRail()}
            </div>
          </Card>
        </aside>
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
    if (!summary) {
      return (
        <Card style={{ padding: '1rem', marginBottom: '1rem', background: 'var(--colorNeutralBackground3)' }}>
          <div style={{ fontSize: '0.8rem', textTransform: 'uppercase', letterSpacing: '0.06em', opacity: 0.7, marginBottom: '0.5rem' }}>
            Strategy Preview
          </div>
          <div>No strategy generated yet.</div>
        </Card>
      )
    }

    return (
      <div style={{ marginBottom: '1rem', padding: '1rem', border: '1px solid var(--colorNeutralStroke2)', borderRadius: '0.75rem', background: 'var(--colorNeutralBackground3)' }}>
        <h4 style={{ margin: '0 0 0.5rem', color: 'var(--colorBrandForeground1)' }}>Review your content strategy before approving</h4>
        <blockquote style={{ borderLeft: '3px solid var(--colorBrandStroke1)', paddingLeft: '1rem', margin: '0.5rem 0', color: 'var(--colorNeutralForeground2)' }}>
          {summary}
        </blockquote>
        {thread.map((msg, index) => (
          <div key={`${msg.role}-${index}`} style={{ margin: '0.25rem 0', color: msg.role === 'assistant' ? 'var(--colorBrandForeground1)' : 'var(--colorNeutralForeground2)' }}>
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
        <div key={`${msg.role}-${index}`} style={{ margin: '0.25rem 0', color: msg.role === 'assistant' ? 'var(--colorBrandForeground1)' : 'var(--colorNeutralForeground2)' }}>
          <strong>{msg.role === 'assistant' ? 'Agent' : 'You'}:</strong> {msg.content}
        </div>
      ))}
    </Card>
  )
}

export default DigitalMarketingActivationWizard
