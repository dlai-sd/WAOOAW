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
  credential_ref: string
  posting_identity?: string | null
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
  const [marketingPlatform, setMarketingPlatform] = useState('instagram')
  const [marketingPostingIdentity, setMarketingPostingIdentity] = useState('')
  const [marketingAccessToken, setMarketingAccessToken] = useState('')
  const [marketingRefreshToken, setMarketingRefreshToken] = useState('')

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
    const lifecycleLabel = resolvedLifecycleState ? ` · ${resolvedLifecycleState.replaceAll('_', ' ')}` : ''
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
      const hasPending = Boolean(marketingAccessToken.trim())
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
    marketingAccessToken
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
                const postingIdentity = String((p as any).posting_identity || '').trim()
                if (platform && credentialRef) {
                  platforms.push({
                    platform,
                    credential_ref: credentialRef,
                    ...(postingIdentity ? { posting_identity: postingIdentity } : {})
                  })
                }
              }
            }
          }
          setMarketingPlatforms(platforms)
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
        credential_ref: String(p.credential_ref || '').trim(),
        ...(p.posting_identity ? { posting_identity: p.posting_identity } : {})
      }))
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
        if (hasPending) {
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
            ? `${marketingPlatforms.length} platform${marketingPlatforms.length === 1 ? '' : 's'} connected`
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
                  <Select value={marketingPlatform} onChange={(_, data) => setMarketingPlatform(String(data.value || 'instagram'))} data-testid="cp-hire-setup-platform">
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

                {marketingPlatforms.length > 0 && (
                  <div style={{ marginTop: '0.75rem' }}>
                    <div style={{ fontWeight: 600, marginBottom: '0.25rem' }}>Connected platforms</div>
                    <ul style={{ margin: 0, paddingLeft: '1.25rem' }}>
                      {marketingPlatforms.map((p) => (
                        <li key={`${p.platform}:${p.credential_ref}`}>
                          {p.platform}
                          {p.posting_identity ? ` — ${p.posting_identity}` : ''} (ref: {p.credential_ref})
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
