import { useEffect, useMemo, useState } from 'react'
import { useNavigate, useParams, useSearchParams } from 'react-router-dom'
import { Button, Card, Checkbox, Input, Select, Spinner, Textarea } from '@fluentui/react-components'
import {
  finalizeHireWizard,
  getHireWizardDraftBySubscription,
  upsertHireWizardDraft,
  type HireWizardDraft
} from '../services/hireWizard.service'
import { plantAPIService } from '../services/plant.service'
import { upsertExchangeSetup } from '../services/exchangeSetup.service'
import { upsertTradingStrategyConfig } from '../services/tradingStrategy.service'
import { upsertPlatformCredential } from '../services/platformCredentials.service'
import {
  attachYouTubeConnection,
  finalizeYouTubeConnection,
  listYouTubeConnections,
  startYouTubeConnection,
  type YouTubeConnection,
} from '../services/youtubeConnections.service'

type Step = 1 | 2 | 3 | 4

const THEME_OPTIONS = [
  { value: 'default', label: 'Default' },
  { value: 'dark', label: 'Dark' },
  { value: 'light', label: 'Light' }
]

const MARKETING_PLATFORM_OPTIONS = [
  { value: 'youtube', label: 'YouTube' },
  { value: 'instagram', label: 'Instagram' },
  { value: 'facebook', label: 'Facebook' },
  { value: 'x', label: 'X (Twitter)' },
  { value: 'linkedin', label: 'LinkedIn' },
  { value: 'whatsapp', label: 'WhatsApp' }
]

type MarketingPlatformConfig = {
  platform: string
  credential_ref?: string
  customer_platform_credential_id?: string
  display_name?: string | null
  posting_identity?: string | null
}

function buildRedirectUri(searchParams: URLSearchParams): string {
  if (typeof window === 'undefined') return ''
  const nextParams = new URLSearchParams(searchParams)
  nextParams.delete('code')
  nextParams.delete('state')
  nextParams.delete('scope')
  nextParams.delete('error')
  const query = nextParams.toString()
  return `${window.location.origin}${window.location.pathname}${query ? `?${query}` : ''}`
}

function getMarketingSkillId(): string {
  return 'default'
}

function resolveAgentTypeId(agentTypeId?: string | null, agentId?: string): string {
  const explicit = String(agentTypeId || '').trim()
  if (explicit) return explicit

  const normalized = String(agentId || '').trim().toUpperCase()
  if (normalized.startsWith('AGT-TRD-')) return 'trading.share_trader.v1'
  if (normalized.startsWith('AGT-MKT-')) return 'marketing.digital_marketing.v1'
  return ''
}

function inferAgentTypeId(agentTypeId?: string | null, agentId?: string): string {
  const resolved = resolveAgentTypeId(agentTypeId, agentId)
  if (resolved) return resolved
  return 'marketing.digital_marketing.v1'
}

function isTradingAgentType(agentTypeId?: string | null): boolean {
  return String(agentTypeId || '').trim().startsWith('trading.')
}

function isMarketingAgentType(agentTypeId?: string | null): boolean {
  return String(agentTypeId || '').trim().startsWith('marketing.')
}

export default function HireSetupWizard() {
  const navigate = useNavigate()
  const params = useParams()
  const [searchParams] = useSearchParams()

  const subscriptionId = params.subscriptionId
  const agentId = searchParams.get('agentId') || ''
  const requestedAgentTypeId = searchParams.get('agentTypeId') || ''
  const requestedCatalogVersion = searchParams.get('catalogVersion') || ''
  const requestedLifecycleState = searchParams.get('lifecycleState') || ''
  const requestedAgentName = searchParams.get('agentName') || ''

  const [step, setStep] = useState<Step>(1)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [draft, setDraft] = useState<HireWizardDraft | null>(null)
  const [resolvedAgentTypeId, setResolvedAgentTypeId] = useState(() => resolveAgentTypeId(requestedAgentTypeId, agentId))
  const [resolvedCatalogVersion, setResolvedCatalogVersion] = useState(requestedCatalogVersion)
  const [resolvedLifecycleState, setResolvedLifecycleState] = useState(requestedLifecycleState)
  const [resolvedAgentName, setResolvedAgentName] = useState(requestedAgentName)

  const [nickname, setNickname] = useState('')
  const [theme, setTheme] = useState('default')
  const [configJson, setConfigJson] = useState('{}')
  const [goalsCompleted, setGoalsCompleted] = useState(false)

  const isTradingAgent = useMemo(() => {
    return isTradingAgentType(resolvedAgentTypeId)
  }, [resolvedAgentTypeId])

  const isMarketingAgent = useMemo(() => {
    return isMarketingAgentType(resolvedAgentTypeId)
  }, [resolvedAgentTypeId])

  const [exchangeProvider, setExchangeProvider] = useState('delta_exchange_india')
  const [coinsRaw, setCoinsRaw] = useState('')
  const [intervalSeconds, setIntervalSeconds] = useState('300')
  const [apiKey, setApiKey] = useState('')
  const [apiSecret, setApiSecret] = useState('')

  const [exchangeCredentialRef, setExchangeCredentialRef] = useState<string | null>(null)

  const [marketingPlatforms, setMarketingPlatforms] = useState<MarketingPlatformConfig[]>([])
  const [marketingPlatform, setMarketingPlatform] = useState('youtube')
  const [marketingPostingIdentity, setMarketingPostingIdentity] = useState('')
  const [marketingAccessToken, setMarketingAccessToken] = useState('')
  const [marketingRefreshToken, setMarketingRefreshToken] = useState('')
  const [youtubeConnections, setYouTubeConnections] = useState<YouTubeConnection[]>([])
  const [selectedYouTubeConnectionId, setSelectedYouTubeConnectionId] = useState('')
  const [youtubeConnectBusy, setYouTubeConnectBusy] = useState(false)
  const [youtubeConnectStatus, setYouTubeConnectStatus] = useState<string | null>(null)

  const stepCopy: Record<Step, { title: string; body: string }> = {
    1: {
      title: 'Name the role you are hiring for',
      body: 'Give the agent a business-facing identity so it feels like part of your operating team, not a generic tool.',
    },
    2: {
      title: 'Choose the working style',
      body: 'Theme and working defaults shape how the agent presents itself in your runtime and customer surfaces.',
    },
    3: {
      title: 'Connect the systems it needs',
      body: 'This is where trust is won or lost. Make setup expectations clear and keep credentials server-side.',
    },
    4: {
      title: 'Review before activation',
      body: 'Customers should understand what they just configured, what happens next, and when the trial starts.',
    },
  }

  const selectedAgentSummary = useMemo(() => {
    if (!agentId) return 'Agent not identified'
    const base = resolvedAgentName || agentId
    const versionLabel = resolvedCatalogVersion ? ` · ${resolvedCatalogVersion}` : ''
    const lifecycleLabel = resolvedLifecycleState ? ` · ${resolvedLifecycleState.replace(/_/g, ' ')}` : ''
    return `${base}${versionLabel}${lifecycleLabel}`
  }, [agentId, resolvedAgentName, resolvedCatalogVersion, resolvedLifecycleState])

  const canNext = useMemo(() => {
    if (step === 1) return Boolean(nickname.trim())
    if (step === 2) return Boolean(theme.trim())
    if (step === 3 && isTradingAgent) {
      const hasCoins = Boolean(coinsRaw.trim())
      const hasInterval = Number(intervalSeconds) > 0
      const hasProvider = Boolean(exchangeProvider.trim())
      const hasExistingCred = Boolean(exchangeCredentialRef && exchangeCredentialRef.trim())
      const hasNewCred = Boolean(apiKey.trim() && apiSecret.trim())
      return hasProvider && hasCoins && hasInterval && (hasExistingCred || hasNewCred)
    }
    if (step === 3 && isMarketingAgent) {
      const hasExisting = marketingPlatforms.length > 0
      const hasSelectedYouTube = Boolean(selectedYouTubeConnectionId.trim())
      const hasPending = marketingPlatform !== 'youtube' && Boolean(marketingAccessToken.trim())
      if (marketingPlatform === 'youtube') return hasExisting || hasSelectedYouTube
      return hasExisting || hasPending
    }
    return true
  }, [
    step,
    nickname,
    theme,
    isTradingAgent,
    coinsRaw,
    intervalSeconds,
    exchangeProvider,
    apiKey,
    apiSecret,
    exchangeCredentialRef,
    isMarketingAgent,
    marketingPlatforms,
    marketingAccessToken,
    marketingPlatform,
    selectedYouTubeConnectionId
  ])

  const inferInitialStep = (existing: HireWizardDraft): Step => {
    const hasNickname = Boolean(String(existing.nickname || '').trim())
    const hasTheme = Boolean(String(existing.theme || '').trim())
    const alreadyAtReview = Boolean(existing.goals_completed) || existing.trial_status === 'active'

    if (!hasNickname) return 1
    if (!hasTheme) return 2
    if (alreadyAtReview) return 4
    return 3
  }

  useEffect(() => {
    let cancelled = false

    const load = async () => {
      setError(null)
      if (!subscriptionId) {
        setError('Missing subscription id')
        setLoading(false)
        return
      }
      if (!agentId) {
        setError('Missing agent id')
        setLoading(false)
        return
      }
      try {
        if (!requestedAgentTypeId || !requestedCatalogVersion || !requestedLifecycleState || !requestedAgentName) {
          const catalogAgent = await plantAPIService.getCatalogAgent(agentId)
          if (!cancelled && catalogAgent) {
            setResolvedAgentTypeId(resolveAgentTypeId(catalogAgent.agent_type_id, agentId))
            setResolvedCatalogVersion(String(catalogAgent.external_catalog_version || ''))
            setResolvedLifecycleState(String(catalogAgent.lifecycle_state || ''))
            setResolvedAgentName(String(catalogAgent.public_name || ''))
          }
        }

        const existing = await getHireWizardDraftBySubscription(subscriptionId)
        if (cancelled) return
        setDraft(existing)
        setResolvedAgentTypeId(resolveAgentTypeId(existing.agent_type_id || requestedAgentTypeId, existing.agent_id || agentId))
        setNickname(String(existing.nickname || ''))
        setTheme(String(existing.theme || 'default'))
        setGoalsCompleted(Boolean(existing.goals_completed))
        setConfigJson(JSON.stringify(existing.config || {}, null, 2))

        if (!requestedCatalogVersion && existing.external_catalog_version) {
          setResolvedCatalogVersion(String(existing.external_catalog_version))
        }
        if (!requestedLifecycleState && existing.catalog_status_at_hire) {
          setResolvedLifecycleState(String(existing.catalog_status_at_hire))
        }

        const cfg = (existing.config || {}) as Record<string, any>
        const existingAgentTypeId = resolveAgentTypeId(existing.agent_type_id || requestedAgentTypeId, existing.agent_id || agentId)
        if (isTradingAgentType(existingAgentTypeId)) {
          setExchangeProvider(String(cfg.exchange_provider || 'delta_exchange_india'))
          const allowed = Array.isArray(cfg.allowed_coins) ? cfg.allowed_coins : []
          setCoinsRaw(allowed.length ? allowed.join(', ') : '')
          setIntervalSeconds(String(cfg.interval_seconds || '300'))
          setExchangeCredentialRef(cfg.exchange_credential_ref ? String(cfg.exchange_credential_ref) : null)
          setApiKey('')
          setApiSecret('')
        } else if (isMarketingAgentType(existingAgentTypeId)) {
          const platformsRaw = cfg.platforms
          const platforms: MarketingPlatformConfig[] = []
          if (Array.isArray(platformsRaw)) {
            for (const p of platformsRaw) {
              if (p && typeof p === 'object') {
                const platform = String((p as any).platform || '').trim()
                const credentialRef = String((p as any).credential_ref || '').trim()
                const customerPlatformCredentialId = String((p as any).customer_platform_credential_id || '').trim()
                const postingIdentity = String((p as any).posting_identity || '').trim()
                if (platform && (credentialRef || customerPlatformCredentialId)) {
                  platforms.push({
                    platform,
                    ...(credentialRef ? { credential_ref: credentialRef } : {}),
                    ...(customerPlatformCredentialId ? { customer_platform_credential_id: customerPlatformCredentialId } : {}),
                    ...((p as any).display_name ? { display_name: String((p as any).display_name) } : {}),
                    ...(postingIdentity ? { posting_identity: postingIdentity } : {})
                  })
                }
              }
            }
          }
          setMarketingPlatforms(platforms)
          const existingYouTube = platforms.find((p) => p.platform === 'youtube' && p.customer_platform_credential_id)
          setSelectedYouTubeConnectionId(existingYouTube?.customer_platform_credential_id || '')
          setMarketingAccessToken('')
          setMarketingRefreshToken('')
          setMarketingPostingIdentity('')
        }
        setStep(inferInitialStep(existing))
      } catch (e: any) {
        // 404 is fine: user hasn't saved draft yet.
        if (e?.status && Number(e.status) === 404) {
          setDraft(null)
        } else {
          setError(e?.message || 'Failed to load wizard draft')
        }
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    load()
    return () => {
      cancelled = true
    }
  }, [subscriptionId, agentId, requestedAgentTypeId, requestedCatalogVersion, requestedLifecycleState])

  useEffect(() => {
    if (!isMarketingAgent) return
    let cancelled = false

    const loadConnections = async () => {
      try {
        const rows = await listYouTubeConnections()
        if (cancelled) return
        setYouTubeConnections(rows)
        if (!selectedYouTubeConnectionId) {
          const connected = rows.find((row) => row.connection_status === 'connected')
          if (connected) setSelectedYouTubeConnectionId(connected.id)
        }
      } catch {
        if (!cancelled) setYouTubeConnections([])
      }
    }

    loadConnections()
    return () => {
      cancelled = true
    }
  }, [isMarketingAgent, selectedYouTubeConnectionId])

  useEffect(() => {
    if (!isMarketingAgent) return
    const code = searchParams.get('code') || ''
    const stateParam = searchParams.get('state') || ''
    if (!code || !stateParam) return

    let cancelled = false

    const finalizeConnection = async () => {
      setYouTubeConnectBusy(true)
      setYouTubeConnectStatus('Finalizing YouTube connection…')
      setError(null)
      try {
        const redirectUri = buildRedirectUri(searchParams)
        const credential = await finalizeYouTubeConnection({
          state: stateParam,
          code,
          redirect_uri: redirectUri,
        })
        if (cancelled) return
        const nextConnections = await listYouTubeConnections()
        if (cancelled) return
        setYouTubeConnections(nextConnections)
        setSelectedYouTubeConnectionId(credential.id)
        setMarketingPlatform('youtube')
        setMarketingPlatforms((prev) => {
          const remaining = prev.filter((item) => item.platform !== 'youtube')
          return [
            ...remaining,
            {
              platform: 'youtube',
              customer_platform_credential_id: credential.id,
              display_name: credential.display_name || 'YouTube Channel',
              posting_identity: credential.display_name || null,
            },
          ]
        })
        setYouTubeConnectStatus(`Connected ${credential.display_name || 'YouTube channel'}`)
        const nextSearch = new URLSearchParams(searchParams)
        nextSearch.delete('code')
        nextSearch.delete('state')
        nextSearch.delete('scope')
        nextSearch.delete('error')
        navigate(
          {
            pathname: `/hire/setup/${encodeURIComponent(subscriptionId || '')}`,
            search: nextSearch.toString() ? `?${nextSearch.toString()}` : '',
          },
          { replace: true }
        )
      } catch (e: any) {
        if (!cancelled) {
          setError(e?.message || 'Failed to finalize YouTube connection')
          setYouTubeConnectStatus(null)
        }
      } finally {
        if (!cancelled) setYouTubeConnectBusy(false)
      }
    }

    finalizeConnection()
    return () => {
      cancelled = true
    }
  }, [isMarketingAgent, navigate, searchParams, subscriptionId])

  const parseConfig = (): Record<string, unknown> => {
    if (isTradingAgent) {
      const coins = (coinsRaw || '')
        .split(',')
        .map((c) => c.trim().toUpperCase())
        .filter(Boolean)
      const interval = Number(intervalSeconds)
      if (!exchangeProvider.trim()) throw new Error('Exchange is required')
      if (!coins.length) throw new Error('At least one coin is required')
      if (!interval || interval <= 0) throw new Error('Interval is required')

      const cfg: Record<string, unknown> = {
        exchange_provider: exchangeProvider.trim(),
        allowed_coins: coins,
        interval_seconds: interval
      }
      if (exchangeCredentialRef) {
        cfg.exchange_credential_ref = exchangeCredentialRef
      }
      return cfg
    }

    if (isMarketingAgent) {
      const platforms = (marketingPlatforms || []).map((p) => ({
        platform: String(p.platform || '').trim(),
        ...(p.credential_ref ? { credential_ref: String(p.credential_ref).trim() } : {}),
        ...(p.customer_platform_credential_id
          ? { customer_platform_credential_id: String(p.customer_platform_credential_id).trim() }
          : {}),
        ...(p.display_name ? { display_name: p.display_name } : {}),
        ...(p.posting_identity ? { posting_identity: p.posting_identity } : {})
      })).filter((p) => Boolean(p.platform) && Boolean((p as any).credential_ref || (p as any).customer_platform_credential_id))
      return { platforms }
    }

    const raw = configJson.trim() || '{}'
    const parsed = JSON.parse(raw)
    if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) {
      throw new Error('Config must be a JSON object')
    }
    return parsed as Record<string, unknown>
  }

  const saveDraft = async (): Promise<HireWizardDraft> => {
    if (!subscriptionId) throw new Error('Missing subscription id')
    if (!agentId) throw new Error('Missing agent id')

    setSaving(true)
    setError(null)
    try {
      let cfg = parseConfig()

      if (isTradingAgent) {
        const hasExistingCred = Boolean(exchangeCredentialRef && exchangeCredentialRef.trim())
        const hasNewCred = Boolean(apiKey.trim() && apiSecret.trim())
        if (!hasExistingCred && !hasNewCred) {
          throw new Error('API key/secret required (or keep existing credential)')
        }

        // Store secrets in CP (encrypted). Never persist secrets in the hired-agent config.
        if (hasNewCred) {
          const coins = Array.isArray((cfg as any).allowed_coins) ? ((cfg as any).allowed_coins as string[]) : []
          const defaultCoin = coins[0]
          const exchange = await upsertExchangeSetup({
            exchange_provider: String((cfg as any).exchange_provider || 'delta_exchange_india'),
            api_key: apiKey.trim(),
            api_secret: apiSecret.trim(),
            default_coin: defaultCoin,
            allowed_coins: coins,
            // Not part of the wizard UX; keep a conservative baseline.
            max_units_per_order: 1
          })
          setExchangeCredentialRef(exchange.credential_ref)
          cfg = {
            ...(cfg as any),
            exchange_credential_ref: exchange.credential_ref
          }
        }

        await upsertTradingStrategyConfig({
          agent_id: agentId,
          interval_seconds: Number((cfg as any).interval_seconds)
        })
      }

      if (isMarketingAgent) {
        const hasPending = Boolean(marketingAccessToken.trim())
        const isYouTubeFlow = marketingPlatform === 'youtube'
        if (isYouTubeFlow) {
          if (!selectedYouTubeConnectionId.trim()) {
            throw new Error('Connect YouTube before continuing')
          }

          const selectedConnection = youtubeConnections.find((row) => row.id === selectedYouTubeConnectionId)
          const nextPlatforms = [
            ...marketingPlatforms.filter((p) => p.platform !== 'youtube'),
            {
              platform: 'youtube',
              customer_platform_credential_id: selectedYouTubeConnectionId,
              display_name: selectedConnection?.display_name || 'YouTube Channel',
              posting_identity: selectedConnection?.display_name || undefined,
            },
          ]
          setMarketingPlatforms(nextPlatforms)
          cfg = { platforms: nextPlatforms }
        } else if (hasPending) {
          const saved = await upsertPlatformCredential({
            platform: marketingPlatform,
            posting_identity: marketingPostingIdentity.trim() || undefined,
            access_token: marketingAccessToken.trim(),
            refresh_token: marketingRefreshToken.trim() || undefined
          })

          const nextPlatforms = [...marketingPlatforms]
          const idx = nextPlatforms.findIndex((p) => String(p.platform || '').trim() === marketingPlatform)
          const entry: MarketingPlatformConfig = {
            platform: marketingPlatform,
            credential_ref: saved.credential_ref,
            ...(marketingPostingIdentity.trim() ? { posting_identity: marketingPostingIdentity.trim() } : {})
          }
          if (idx >= 0) nextPlatforms[idx] = entry
          else nextPlatforms.push(entry)

          setMarketingPlatforms(nextPlatforms)
          setMarketingAccessToken('')
          setMarketingRefreshToken('')
          setMarketingPostingIdentity('')

          cfg = { platforms: nextPlatforms }
        }
      }

      const next = await upsertHireWizardDraft({
        subscription_id: subscriptionId,
        agent_id: agentId,
        agent_type_id: inferAgentTypeId(resolvedAgentTypeId, agentId),
        nickname: nickname.trim() || undefined,
        theme: theme.trim() || undefined,
        config: cfg
      })
      setDraft(next)

      if (isMarketingAgent && selectedYouTubeConnectionId.trim()) {
        await attachYouTubeConnection(selectedYouTubeConnectionId, {
          hired_instance_id: next.hired_instance_id,
          skill_id: getMarketingSkillId(),
          platform_key: 'youtube',
        })
      }

      return next
    } finally {
      setSaving(false)
    }
  }

  const onBack = () => {
    setError(null)
    if (step === 1) return
    setStep((step - 1) as Step)
  }

  const onNext = async () => {
    setError(null)
    if (!canNext) return

    try {
      await saveDraft()
      if (step < 4) setStep((step + 1) as Step)
    } catch (e: any) {
      setError(e?.message || 'Failed to save draft')
    }
  }

  const onActivate = async () => {
    setError(null)
    try {
      const saved = await saveDraft()
      const finalized = await finalizeHireWizard({
        hired_instance_id: saved.hired_instance_id,
        agent_type_id: inferAgentTypeId(resolvedAgentTypeId, agentId),
        goals_completed: Boolean(goalsCompleted)
      })
      setDraft(finalized)

      navigate('/portal', {
        state: {
          portalEntry: {
            page: 'my-agents',
            agentId,
            agentName: resolvedAgentName || undefined,
            catalogVersion: finalized.external_catalog_version || resolvedCatalogVersion || undefined,
            lifecycleState: finalized.catalog_status_at_hire || resolvedLifecycleState || undefined,
            source: 'trial-activated',
            subscriptionId,
          },
        },
      })
    } catch (e: any) {
      setError(e?.message || 'Failed to activate trial')
    }
  }

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', padding: '3rem 1rem' }}>
        <Spinner size="large" />
      </div>
    )
  }

  const reviewSummary = [
    { label: 'Selected agent', value: selectedAgentSummary },
    { label: 'Agent nickname', value: nickname || 'Not set' },
    { label: 'Theme', value: theme || 'Default' },
    {
      label: 'Connected systems',
      value: isTradingAgent
        ? `${exchangeProvider || 'Exchange not selected'}${exchangeCredentialRef ? ' · credential ready' : apiKey.trim() ? ' · credential staged' : ''}`
        : isMarketingAgent
          ? marketingPlatforms.length
            ? marketingPlatforms
                .map((platform) => platform.display_name || platform.posting_identity || platform.platform)
                .join(', ')
            : marketingPlatform === 'youtube'
              ? 'No YouTube channel connected yet'
              : marketingAccessToken.trim()
                ? `${marketingPlatform} token staged`
                : 'No platform connected yet'
          : 'Custom config provided',
    },
    { label: 'Activation readiness', value: goalsCompleted ? 'Goals confirmed' : 'Waiting for goal confirmation' },
  ]

  return (
    <div className="hire-wizard-page" style={{ maxWidth: 920, margin: '0 auto', padding: '2rem 1rem' }} data-testid="cp-hire-setup-page">
      <div className="hire-wizard-hero">
        <div>
          <div className="hire-wizard-kicker">Hire Activation</div>
          <h1 style={{ fontSize: '1.95rem', fontWeight: 700, marginBottom: '0.6rem' }}>Setup & Activate Trial</h1>
          <p style={{ marginBottom: 0, color: 'var(--colorNeutralForeground2)', maxWidth: '58ch' }}>
            Trial starts only after setup is completed. The flow should make clear what this agent needs, how it works,
            and what you will be able to monitor after activation.
          </p>
        </div>
        <div className="hire-wizard-proof-grid">
          <div className="hire-wizard-proof-card">
            <div className="hire-wizard-proof-value">Agent</div>
            <div className="hire-wizard-proof-label">{selectedAgentSummary}</div>
          </div>
          <div className="hire-wizard-proof-card">
            <div className="hire-wizard-proof-value">4</div>
            <div className="hire-wizard-proof-label">Simple steps</div>
          </div>
          <div className="hire-wizard-proof-card">
            <div className="hire-wizard-proof-value">0</div>
            <div className="hire-wizard-proof-label">Secret leakage to Plant</div>
          </div>
          <div className="hire-wizard-proof-card">
            <div className="hire-wizard-proof-value">1</div>
            <div className="hire-wizard-proof-label">Clear activation moment</div>
          </div>
        </div>
      </div>

      <Card style={{ padding: '1.5rem' }}>
        <div className="hire-wizard-step-header" data-testid={`cp-hire-setup-step-${step}`}>
          <div>
            <div style={{ marginBottom: '0.35rem', fontWeight: 600 }}>Step {step} of 4</div>
            <div className="hire-wizard-step-title">{stepCopy[step].title}</div>
            <div className="hire-wizard-step-body">{stepCopy[step].body}</div>
          </div>
          <div className="hire-wizard-step-pills">
            {[1, 2, 3, 4].map((item) => (
              <span key={item} className={`hire-wizard-step-pill ${step >= item ? 'active' : ''}`}>0{item}</span>
            ))}
          </div>
        </div>

        {step === 1 && (
          <div className="form-group">
            <label>Agent nickname *</label>
            <Input value={nickname} onChange={(_, data) => setNickname(data.value)} placeholder="e.g. Growth Copilot" data-testid="cp-hire-setup-nickname" />
          </div>
        )}

        {step === 2 && (
          <div className="form-group">
            <label>Theme *</label>
            <Select value={theme} onChange={(_, data) => setTheme(String(data.value || 'default'))} data-testid="cp-hire-setup-theme">
              {THEME_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </Select>
          </div>
        )}

        {step === 3 && (
          <>
            {isTradingAgent ? (
              <>
                <div className="hire-wizard-inline-note">Connect the exchange once, then manage trading behaviour from the runtime view later.</div>
                <div className="form-group">
                  <label>Exchange *</label>
                  <Select value={exchangeProvider} onChange={(_, data) => setExchangeProvider(String(data.value || 'delta_exchange_india'))} data-testid="cp-hire-setup-exchange-provider">
                    <option value="delta_exchange_india">Delta India</option>
                  </Select>
                </div>

                <div className="form-group">
                  <label>Coins (comma-separated) *</label>
                  <Input value={coinsRaw} onChange={(_, data) => setCoinsRaw(data.value)} placeholder="e.g. BTC, ETH" data-testid="cp-hire-setup-coins" />
                </div>

                <div className="form-group">
                  <label>Interval *</label>
                  <Select value={intervalSeconds} onChange={(_, data) => setIntervalSeconds(String(data.value || '300'))} data-testid="cp-hire-setup-interval">
                    <option value="60">1 minute</option>
                    <option value="300">5 minutes</option>
                    <option value="900">15 minutes</option>
                    <option value="3600">1 hour</option>
                  </Select>
                </div>

                <div className="form-group">
                  <label>{exchangeCredentialRef ? 'API key (optional to keep existing)' : 'API key *'}</label>
                  <Input value={apiKey} onChange={(_, data) => setApiKey(data.value)} placeholder="Enter your exchange API key" data-testid="cp-hire-setup-api-key" />
                </div>

                <div className="form-group">
                  <label>{exchangeCredentialRef ? 'API secret (optional to keep existing)' : 'API secret *'}</label>
                  <Input
                    type="password"
                    value={apiSecret}
                    onChange={(_, data) => setApiSecret(data.value)}
                    placeholder="Enter your exchange API secret"
                    data-testid="cp-hire-setup-api-secret"
                  />
                </div>
              </>
            ) : isMarketingAgent ? (
              <>
                <div className="hire-wizard-inline-note" style={{ marginBottom: '0.75rem' }}>
                  Connect your marketing platforms. Tokens are stored securely in CP; Plant receives only credential references.
                </div>

                <div className="form-group">
                  <label>Platform *</label>
                  <Select value={marketingPlatform} onChange={(_, data) => setMarketingPlatform(String(data.value || 'youtube'))} data-testid="cp-hire-setup-platform">
                    {MARKETING_PLATFORM_OPTIONS.map((opt) => (
                      <option key={opt.value} value={opt.value}>
                        {opt.label}
                      </option>
                    ))}
                  </Select>
                </div>

                <div className="form-group">
                  <label>Posting identity (page/channel/account)</label>
                  <Input
                    value={marketingPostingIdentity}
                    onChange={(_, data) => setMarketingPostingIdentity(data.value)}
                    placeholder="e.g., DrSharmaClinic"
                    data-testid="cp-hire-setup-posting-identity"
                  />
                </div>

                {marketingPlatform === 'youtube' ? (
                  <div className="hire-wizard-youtube-connect" data-testid="cp-hire-setup-youtube-connect">
                    <div className="hire-wizard-inline-note" style={{ marginBottom: '0.75rem' }}>
                      Connect YouTube once with Google, then choose the verified channel you want this agent to use.
                    </div>

                    {youtubeConnectStatus && (
                      <div style={{ marginBottom: '0.75rem', color: 'var(--colorBrandForeground1)' }}>{youtubeConnectStatus}</div>
                    )}

                    <div style={{ display: 'flex', gap: '0.75rem', marginBottom: '1rem', flexWrap: 'wrap' }}>
                      <Button
                        appearance="primary"
                        disabled={youtubeConnectBusy}
                        data-testid="cp-hire-setup-youtube-connect-button"
                        onClick={async () => {
                          setError(null)
                          setYouTubeConnectBusy(true)
                          setYouTubeConnectStatus(null)
                          try {
                            const redirectUri = buildRedirectUri(searchParams)
                            const start = await startYouTubeConnection(redirectUri)
                            if (typeof window !== 'undefined') {
                              window.location.assign(start.authorization_url)
                            }
                          } catch (e: any) {
                            setError(e?.message || 'Failed to start YouTube connection')
                            setYouTubeConnectBusy(false)
                          }
                        }}
                      >
                        {youtubeConnections.length > 0 ? 'Reconnect YouTube' : 'Connect YouTube'}
                      </Button>

                      {selectedYouTubeConnectionId && (
                        <Button
                          appearance="outline"
                          disabled={youtubeConnectBusy}
                          onClick={() => setSelectedYouTubeConnectionId('')}
                          data-testid="cp-hire-setup-youtube-clear-selection"
                        >
                          Clear selection
                        </Button>
                      )}
                    </div>

                    {youtubeConnections.length > 0 ? (
                      <div style={{ display: 'grid', gap: '0.75rem' }}>
                        <div style={{ fontWeight: 600 }}>Available YouTube channels</div>
                        {youtubeConnections.map((connection) => {
                          const selected = selectedYouTubeConnectionId === connection.id
                          return (
                            <button
                              key={connection.id}
                              type="button"
                              onClick={() => {
                                setSelectedYouTubeConnectionId(connection.id)
                                setMarketingPlatforms((prev) => {
                                  const rest = prev.filter((item) => item.platform !== 'youtube')
                                  return [
                                    ...rest,
                                    {
                                      platform: 'youtube',
                                      customer_platform_credential_id: connection.id,
                                      display_name: connection.display_name || 'YouTube Channel',
                                      posting_identity: connection.display_name || undefined,
                                    },
                                  ]
                                })
                              }}
                              data-testid={`cp-hire-setup-youtube-option-${connection.id}`}
                              style={{
                                textAlign: 'left',
                                padding: '0.9rem 1rem',
                                borderRadius: 12,
                                border: selected ? '2px solid var(--colorBrandStroke1)' : '1px solid var(--colorNeutralStroke2)',
                                background: selected ? 'var(--colorNeutralBackground1Selected)' : 'var(--colorNeutralBackground1)',
                                cursor: 'pointer',
                              }}
                            >
                              <div style={{ fontWeight: 600 }}>{connection.display_name || 'YouTube Channel'}</div>
                              <div style={{ fontSize: '0.9rem', color: 'var(--colorNeutralForeground2)' }}>
                                {connection.connection_status} · {connection.verification_status}
                                {connection.last_verified_at ? ` · verified ${new Date(connection.last_verified_at).toLocaleString()}` : ''}
                              </div>
                            </button>
                          )
                        })}
                      </div>
                    ) : (
                      <div style={{ color: 'var(--colorNeutralForeground2)' }}>
                        No YouTube channel connected yet.
                      </div>
                    )}
                  </div>
                ) : (
                  <>
                    <div className="form-group">
                      <label>Access token *</label>
                      <Input
                        type="password"
                        value={marketingAccessToken}
                        onChange={(_, data) => setMarketingAccessToken(data.value)}
                        placeholder="Paste token (stored server-side)"
                        data-testid="cp-hire-setup-access-token"
                      />
                    </div>

                    <div className="form-group">
                      <label>Refresh token (optional)</label>
                      <Input
                        type="password"
                        value={marketingRefreshToken}
                        onChange={(_, data) => setMarketingRefreshToken(data.value)}
                        placeholder="Optional"
                        data-testid="cp-hire-setup-refresh-token"
                      />
                    </div>
                  </>
                )}

                {marketingPlatforms.length > 0 && (
                  <div style={{ marginTop: '0.75rem' }}>
                    <div style={{ fontWeight: 600, marginBottom: '0.25rem' }}>Connected platforms</div>
                    <ul style={{ margin: 0, paddingLeft: '1.25rem' }}>
                      {marketingPlatforms.map((p) => (
                        <li key={`${p.platform}:${p.customer_platform_credential_id || p.credential_ref || 'pending'}`}>
                          {p.display_name || p.platform}
                          {p.posting_identity ? ` — ${p.posting_identity}` : ''}
                          {p.customer_platform_credential_id
                            ? ` (connection: ${p.customer_platform_credential_id})`
                            : p.credential_ref
                              ? ` (ref: ${p.credential_ref})`
                              : ''}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </>
            ) : (
              <div className="form-group">
                <label>Agent-specific configuration (JSON)</label>
                <Textarea
                  value={configJson}
                  onChange={(_, data) => setConfigJson(data.value)}
                  resize="vertical"
                  rows={10}
                  data-testid="cp-hire-setup-config-json"
                />
              </div>
            )}
          </>
        )}

        {step === 4 && (
          <>
            <div className="hire-wizard-inline-note" style={{ marginBottom: '1rem' }}>
              Review your setup and activate trial.
            </div>

            <div className="hire-wizard-review-grid">
              {reviewSummary.map((item) => (
                <div key={item.label} className="hire-wizard-review-card">
                  <div className="hire-wizard-review-label">{item.label}</div>
                  <div className="hire-wizard-review-value">{item.value}</div>
                </div>
              ))}
            </div>

            <Checkbox
              checked={goalsCompleted}
              onChange={(_, data) => setGoalsCompleted(Boolean(data.checked))}
              label="I have completed the goal setting step"
              data-testid="cp-hire-setup-goals-completed"
            />

            {draft?.trial_status === 'active' && (
              <div style={{ marginTop: '1rem' }}>
                Trial is active{draft.trial_end_at ? ` until ${draft.trial_end_at}` : ''}.
              </div>
            )}
          </>
        )}

        {error && <div style={{ marginTop: '1rem', color: 'var(--colorPaletteRedForeground1)' }}>{error}</div>}

        <div style={{ display: 'flex', gap: '0.75rem', marginTop: '1.5rem' }}>
          <Button appearance="outline" onClick={onBack} disabled={saving || step === 1} data-testid="cp-hire-setup-back">
            Back
          </Button>

          {step < 4 ? (
            <Button appearance="primary" onClick={onNext} disabled={saving || !canNext} data-testid="cp-hire-setup-next">
              {saving ? 'Saving…' : 'Save & Continue'}
            </Button>
          ) : (
            <Button appearance="primary" onClick={onActivate} disabled={saving || !goalsCompleted} data-testid="cp-hire-setup-activate">
              {saving ? 'Saving…' : 'Activate trial'}
            </Button>
          )}

          <Button
            appearance="subtle"
            onClick={() =>
              navigate(agentId ? `/agent/${encodeURIComponent(agentId)}` : '/portal')
            }
            disabled={saving}
          >
            Exit
          </Button>
        </div>
      </Card>

      <div className="hire-wizard-bottom-grid">
        <Card className="hire-wizard-bottom-card">
          <div className="hire-wizard-bottom-title">What the customer should know next</div>
          <p>After activation, WAOOAW should route them cleanly to hiring runtime, approvals, spend, and results.</p>
        </Card>
        <Card className="hire-wizard-bottom-card">
          <div className="hire-wizard-bottom-title">What the system should guarantee</div>
          <p>Credentials stay protected, setup feels finite, and activation does not feel like a hidden background side effect.</p>
        </Card>
      </div>
    </div>
  )
}
