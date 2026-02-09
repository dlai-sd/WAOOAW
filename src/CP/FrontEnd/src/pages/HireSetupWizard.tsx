import { useEffect, useMemo, useState } from 'react'
import { useNavigate, useParams, useSearchParams } from 'react-router-dom'
import { Button, Card, Checkbox, Field, Input, Select, Spinner, Textarea } from '@fluentui/react-components'
import {
  finalizeHireWizard,
  getHireWizardDraftBySubscription,
  upsertHireWizardDraft,
  type HireWizardDraft
} from '../services/hireWizard.service'
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

export default function HireSetupWizard() {
  const navigate = useNavigate()
  const params = useParams()
  const [searchParams] = useSearchParams()

  const subscriptionId = params.subscriptionId
  const agentId = searchParams.get('agentId') || ''

  const [step, setStep] = useState<Step>(1)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [draft, setDraft] = useState<HireWizardDraft | null>(null)

  const [nickname, setNickname] = useState('')
  const [theme, setTheme] = useState('default')
  const [configJson, setConfigJson] = useState('{}')
  const [goalsCompleted, setGoalsCompleted] = useState(false)

  const isTradingAgent = useMemo(() => {
    return String(agentId || '').toUpperCase().startsWith('AGT-TRD-')
  }, [agentId])

  const isMarketingAgent = useMemo(() => {
    return String(agentId || '').toUpperCase().startsWith('AGT-MKT-')
  }, [agentId])

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
        const existing = await getHireWizardDraftBySubscription(subscriptionId)
        if (cancelled) return
        setDraft(existing)
        setNickname(String(existing.nickname || ''))
        setTheme(String(existing.theme || 'default'))
        setGoalsCompleted(Boolean(existing.goals_completed))
        setConfigJson(JSON.stringify(existing.config || {}, null, 2))

        const cfg = (existing.config || {}) as Record<string, any>
        if (String(existing.agent_id || '').toUpperCase().startsWith('AGT-TRD-')) {
          setExchangeProvider(String(cfg.exchange_provider || 'delta_exchange_india'))
          const allowed = Array.isArray(cfg.allowed_coins) ? cfg.allowed_coins : []
          setCoinsRaw(allowed.length ? allowed.join(', ') : '')
          setIntervalSeconds(String(cfg.interval_seconds || '300'))
          setExchangeCredentialRef(cfg.exchange_credential_ref ? String(cfg.exchange_credential_ref) : null)
          setApiKey('')
          setApiSecret('')
        } else if (String(existing.agent_id || '').toUpperCase().startsWith('AGT-MKT-')) {
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
  }, [subscriptionId, agentId])

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
        goals_completed: Boolean(goalsCompleted)
      })
      setDraft(finalized)

      navigate('/portal')
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

  return (
    <div style={{ maxWidth: 720, margin: '0 auto', padding: '2rem 1rem' }}>
      <h1 style={{ fontSize: '1.75rem', fontWeight: 700, marginBottom: '0.5rem' }}>Setup & Activate Trial</h1>
      <p style={{ marginBottom: '1.5rem' }}>
        Trial starts only after setup is completed.
      </p>

      <Card style={{ padding: '1.5rem' }}>
        <div style={{ marginBottom: '1rem', fontWeight: 600 }}>Step {step} of 4</div>

        {step === 1 && (
          <Field label="Agent nickname" required>
            <Input value={nickname} onChange={(_, data) => setNickname(data.value)} placeholder="e.g. Growth Copilot" />
          </Field>
        )}

        {step === 2 && (
          <Field label="Theme" required>
            <Select value={theme} onChange={(_, data) => setTheme(String(data.value || 'default'))}>
              {THEME_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </Select>
          </Field>
        )}

        {step === 3 && (
          <>
            {isTradingAgent ? (
              <>
                <Field label="Exchange" required>
                  <Select value={exchangeProvider} onChange={(_, data) => setExchangeProvider(String(data.value || 'delta_exchange_india'))}>
                    <option value="delta_exchange_india">Delta India</option>
                  </Select>
                </Field>

                <Field label="Coins (comma-separated)" required>
                  <Input value={coinsRaw} onChange={(_, data) => setCoinsRaw(data.value)} placeholder="e.g. BTC, ETH" />
                </Field>

                <Field label="Interval" required>
                  <Select value={intervalSeconds} onChange={(_, data) => setIntervalSeconds(String(data.value || '300'))}>
                    <option value="60">1 minute</option>
                    <option value="300">5 minutes</option>
                    <option value="900">15 minutes</option>
                    <option value="3600">1 hour</option>
                  </Select>
                </Field>

                <Field label={exchangeCredentialRef ? 'API key (optional to keep existing)' : 'API key'} required={!exchangeCredentialRef}>
                  <Input value={apiKey} onChange={(_, data) => setApiKey(data.value)} placeholder="Enter your exchange API key" />
                </Field>

                <Field label={exchangeCredentialRef ? 'API secret (optional to keep existing)' : 'API secret'} required={!exchangeCredentialRef}>
                  <Input
                    type="password"
                    value={apiSecret}
                    onChange={(_, data) => setApiSecret(data.value)}
                    placeholder="Enter your exchange API secret"
                  />
                </Field>
              </>
            ) : isMarketingAgent ? (
              <>
                <div style={{ marginBottom: '0.75rem' }}>
                  Connect your marketing platforms. Tokens are stored securely in CP; Plant receives only credential references.
                </div>

                <Field label="Platform" required>
                  <Select value={marketingPlatform} onChange={(_, data) => setMarketingPlatform(String(data.value || 'instagram'))}>
                    {MARKETING_PLATFORM_OPTIONS.map((opt) => (
                      <option key={opt.value} value={opt.value}>
                        {opt.label}
                      </option>
                    ))}
                  </Select>
                </Field>

                <Field label="Posting identity (page/channel/account)">
                  <Input
                    value={marketingPostingIdentity}
                    onChange={(_, data) => setMarketingPostingIdentity(data.value)}
                    placeholder="e.g., DrSharmaClinic"
                  />
                </Field>

                <Field label="Access token" required>
                  <Input
                    type="password"
                    value={marketingAccessToken}
                    onChange={(_, data) => setMarketingAccessToken(data.value)}
                    placeholder="Paste token (stored server-side)"
                  />
                </Field>

                <Field label="Refresh token (optional)">
                  <Input
                    type="password"
                    value={marketingRefreshToken}
                    onChange={(_, data) => setMarketingRefreshToken(data.value)}
                    placeholder="Optional"
                  />
                </Field>

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
              <Field label="Agent-specific configuration (JSON)">
                <Textarea
                  value={configJson}
                  onChange={(_, data) => setConfigJson(data.value)}
                  resize="vertical"
                  rows={10}
                />
              </Field>
            )}
          </>
        )}

        {step === 4 && (
          <>
            <div style={{ marginBottom: '1rem' }}>
              Review your setup and activate trial.
            </div>
            <Checkbox
              checked={goalsCompleted}
              onChange={(_, data) => setGoalsCompleted(Boolean(data.checked))}
              label="I have completed the goal setting step"
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
          <Button appearance="outline" onClick={onBack} disabled={saving || step === 1}>
            Back
          </Button>

          {step < 4 ? (
            <Button appearance="primary" onClick={onNext} disabled={saving || !canNext}>
              {saving ? 'Saving…' : 'Save & Continue'}
            </Button>
          ) : (
            <Button appearance="primary" onClick={onActivate} disabled={saving || !goalsCompleted}>
              {saving ? 'Saving…' : 'Activate trial'}
            </Button>
          )}

          <Button appearance="subtle" onClick={() => navigate('/portal')} disabled={saving}>
            Exit
          </Button>
        </div>
      </Card>
    </div>
  )
}
