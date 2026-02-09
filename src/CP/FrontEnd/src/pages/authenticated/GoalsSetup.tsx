import { Card, Button, Textarea, Input } from '@fluentui/react-components'
import { useEffect, useRef, useState } from 'react'
import { listPlatformCredentials, upsertPlatformCredential, type PlatformCredential } from '../../services/platformCredentials.service'
import { listExchangeSetups, upsertExchangeSetup, type ExchangeSetup } from '../../services/exchangeSetup.service'
import { listTradingStrategyConfigs, upsertTradingStrategyConfig, type TradingStrategyConfig } from '../../services/tradingStrategy.service'

export default function GoalsSetup() {
  const isMountedRef = useRef(true)

  useEffect(() => {
    return () => {
      isMountedRef.current = false
    }
  }, [])

  const [platform, setPlatform] = useState('instagram')
  const [postingIdentity, setPostingIdentity] = useState('')
  const [accessToken, setAccessToken] = useState('')
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [connections, setConnections] = useState<PlatformCredential[]>([])

  const [exchangeProvider, setExchangeProvider] = useState('delta_exchange_india')
  const [exchangeApiKey, setExchangeApiKey] = useState('')
  const [exchangeApiSecret, setExchangeApiSecret] = useState('')
  const [defaultCoin, setDefaultCoin] = useState('BTC')
  const [allowedCoins, setAllowedCoins] = useState('BTC,ETH')
  const [maxUnitsPerOrder, setMaxUnitsPerOrder] = useState('1')
  const [maxNotionalInr, setMaxNotionalInr] = useState('')
  const [isSavingExchange, setIsSavingExchange] = useState(false)
  const [exchangeError, setExchangeError] = useState<string | null>(null)
  const [exchangeSetups, setExchangeSetups] = useState<ExchangeSetup[]>([])

  const [strategyAgentId, setStrategyAgentId] = useState('AGT-TRD-DELTA-001')
  const [intervalSeconds, setIntervalSeconds] = useState('300')
  const [windowStart, setWindowStart] = useState('09:15')
  const [windowEnd, setWindowEnd] = useState('15:30')
  const [strategyParamsJson, setStrategyParamsJson] = useState('')
  const [isSavingStrategy, setIsSavingStrategy] = useState(false)
  const [strategyError, setStrategyError] = useState<string | null>(null)
  const [strategyConfigs, setStrategyConfigs] = useState<TradingStrategyConfig[]>([])

  const refreshConnections = async () => {
    try {
      const rows = await listPlatformCredentials()
      if (!isMountedRef.current) return
      setConnections(rows)
    } catch (e: any) {
      if (!isMountedRef.current) return
      setError(e?.message || 'Failed to load platform connections')
    }
  }

  const refreshExchangeSetups = async () => {
    try {
      const rows = await listExchangeSetups()
      if (!isMountedRef.current) return
      setExchangeSetups(rows)
    } catch (e: any) {
      if (!isMountedRef.current) return
      setExchangeError(e?.message || 'Failed to load exchange setup')
    }
  }

  const refreshStrategyConfigs = async () => {
    try {
      const rows = await listTradingStrategyConfigs(strategyAgentId)
      if (!isMountedRef.current) return
      setStrategyConfigs(rows)
    } catch (e: any) {
      if (!isMountedRef.current) return
      setStrategyError(e?.message || 'Failed to load trading strategy config')
    }
  }

  useEffect(() => {
    refreshConnections()
    refreshExchangeSetups()
    refreshStrategyConfigs()
  }, [])

  const onConnect = async () => {
    setError(null)
    setIsSaving(true)
    try {
      await upsertPlatformCredential({
        platform,
        posting_identity: postingIdentity || undefined,
        access_token: accessToken
      })
      setAccessToken('')
      setPostingIdentity('')
      await refreshConnections()
    } catch (e: any) {
      setError(e?.message || 'Failed to connect platform')
    } finally {
      setIsSaving(false)
    }
  }

  const onSaveExchangeSetup = async () => {
    setExchangeError(null)
    setIsSavingExchange(true)
    try {
      const allowed = allowedCoins
        .split(',')
        .map((s) => s.trim().toUpperCase())
        .filter(Boolean)

      await upsertExchangeSetup({
        exchange_provider: exchangeProvider,
        api_key: exchangeApiKey,
        api_secret: exchangeApiSecret,
        default_coin: defaultCoin.trim().toUpperCase(),
        allowed_coins: allowed.length ? allowed : undefined,
        max_units_per_order: Number(maxUnitsPerOrder || '0'),
        ...(maxNotionalInr.trim() ? { max_notional_inr: Number(maxNotionalInr) } : {})
      })

      setExchangeApiKey('')
      setExchangeApiSecret('')
      await refreshExchangeSetups()
    } catch (e: any) {
      setExchangeError(e?.message || 'Failed to save exchange setup')
    } finally {
      setIsSavingExchange(false)
    }
  }

  const onSaveStrategyConfig = async () => {
    setStrategyError(null)
    setIsSavingStrategy(true)
    try {
      const interval = intervalSeconds.trim() ? Number(intervalSeconds) : undefined

      let strategyParams: Record<string, unknown> | undefined = undefined
      if (strategyParamsJson.trim()) {
        try {
          const parsed = JSON.parse(strategyParamsJson)
          if (parsed && typeof parsed === 'object' && !Array.isArray(parsed)) {
            strategyParams = parsed
          } else {
            throw new Error('strategy params must be a JSON object')
          }
        } catch (e: any) {
          setStrategyError(e?.message || 'Invalid strategy params JSON')
          return
        }
      }

      await upsertTradingStrategyConfig({
        agent_id: strategyAgentId,
        ...(interval ? { interval_seconds: interval } : {}),
        ...(windowStart.trim() && windowEnd.trim()
          ? { active_window_start: windowStart.trim(), active_window_end: windowEnd.trim() }
          : {})
        ,
        ...(strategyParams ? { strategy_params: strategyParams } : {})
      })

      await refreshStrategyConfigs()
    } catch (e: any) {
      setStrategyError(e?.message || 'Failed to save trading strategy config')
    } finally {
      setIsSavingStrategy(false)
    }
  }

  return (
    <div className="goals-setup-page">
      <div className="page-header">
        <h1>Configure Goals for: Content Marketing Agent</h1>
        <div>
          <Button appearance="outline">Save Draft</Button>
          <Button appearance="primary">Submit for Genesis Validation</Button>
        </div>
      </div>

      <Card className="wizard-card">
        <h2>Connect Platforms (Customer Setup)</h2>

        <div className="form-group">
          <label>Platform *</label>
          <select value={platform} onChange={(e) => setPlatform(e.target.value)} className="filter-select">
            <option value="youtube">YouTube</option>
            <option value="instagram">Instagram</option>
            <option value="facebook">Facebook</option>
            <option value="linkedin">LinkedIn</option>
            <option value="whatsapp">WhatsApp</option>
          </select>
        </div>

        <div className="form-group">
          <label>Posting identity (page/channel/account)</label>
          <Input value={postingIdentity} onChange={(_, data) => setPostingIdentity(data.value)} placeholder="e.g., DrSharmaClinic" />
        </div>

        <div className="form-group">
          <label>Access token *</label>
          <Input value={accessToken} onChange={(_, data) => setAccessToken(data.value)} placeholder="Paste token (stored server-side)" type="password" />
        </div>

        {error && <div style={{ color: '#ef4444' }}>{error}</div>}

        <div className="wizard-nav">
          <Button appearance="primary" onClick={onConnect} disabled={!accessToken || isSaving}>
            {isSaving ? 'Saving…' : 'Save Connection'}
          </Button>
        </div>

        <h3 style={{ marginTop: '1rem' }}>Existing connections ({connections.length})</h3>
        <ul>
          {connections.map((c) => (
            <li key={c.credential_ref}>
              {c.platform} {c.posting_identity ? `— ${c.posting_identity}` : ''} (ref: {c.credential_ref})
            </li>
          ))}
        </ul>
      </Card>

      <Card className="wizard-card">
        <h2>Connect Exchange (Trading Setup)</h2>

        <div className="form-group">
          <label>Exchange provider *</label>
          <select value={exchangeProvider} onChange={(e) => setExchangeProvider(e.target.value)} className="filter-select">
            <option value="delta_exchange_india">Delta Exchange India</option>
          </select>
        </div>

        <div className="form-group">
          <label>API key *</label>
          <Input value={exchangeApiKey} onChange={(_, data) => setExchangeApiKey(data.value)} placeholder="Stored server-side" type="password" />
        </div>

        <div className="form-group">
          <label>API secret *</label>
          <Input value={exchangeApiSecret} onChange={(_, data) => setExchangeApiSecret(data.value)} placeholder="Stored server-side" type="password" />
        </div>

        <div className="form-group">
          <label>Default coin *</label>
          <Input value={defaultCoin} onChange={(_, data) => setDefaultCoin(data.value)} placeholder="BTC" />
        </div>

        <div className="form-group">
          <label>Allowed coins (comma-separated)</label>
          <Input value={allowedCoins} onChange={(_, data) => setAllowedCoins(data.value)} placeholder="BTC,ETH" />
        </div>

        <div className="form-group">
          <label>Max units per order *</label>
          <Input value={maxUnitsPerOrder} onChange={(_, data) => setMaxUnitsPerOrder(data.value)} placeholder="1" />
        </div>

        <div className="form-group">
          <label>Max notional (INR) (optional)</label>
          <Input value={maxNotionalInr} onChange={(_, data) => setMaxNotionalInr(data.value)} placeholder="e.g., 100000" />
        </div>

        {exchangeError && <div style={{ color: '#ef4444' }}>{exchangeError}</div>}

        <div className="wizard-nav">
          <Button
            appearance="primary"
            onClick={onSaveExchangeSetup}
            disabled={!exchangeApiKey || !exchangeApiSecret || !defaultCoin || isSavingExchange}
          >
            {isSavingExchange ? 'Saving…' : 'Save Exchange Setup'}
          </Button>
        </div>

        <h3 style={{ marginTop: '1rem' }}>Saved exchange setups ({exchangeSetups.length})</h3>
        <ul>
          {exchangeSetups.map((s) => (
            <li key={s.credential_ref}>
              {s.exchange_provider} — default {s.default_coin} — allowed [{(s.allowed_coins || []).join(', ')}] — max units {s.risk_limits?.max_units_per_order}
              {s.risk_limits?.max_notional_inr ? ` — max notional ₹${s.risk_limits.max_notional_inr}` : ''} (ref: {s.credential_ref})
            </li>
          ))}
        </ul>
      </Card>

      <Card className="wizard-card">
        <h2>Trading Strategy (Interval Setup)</h2>

        <div className="form-group">
          <label>Agent ID</label>
          <Input value={strategyAgentId} onChange={(_, data) => setStrategyAgentId(data.value)} />
        </div>

        <div className="form-group">
          <label>Interval seconds (optional)</label>
          <Input value={intervalSeconds} onChange={(_, data) => setIntervalSeconds(data.value)} placeholder="300" />
        </div>

        <div className="form-group">
          <label>Active window start (optional)</label>
          <Input value={windowStart} onChange={(_, data) => setWindowStart(data.value)} placeholder="09:15" />
        </div>

        <div className="form-group">
          <label>Active window end (optional)</label>
          <Input value={windowEnd} onChange={(_, data) => setWindowEnd(data.value)} placeholder="15:30" />
        </div>

        <div className="form-group">
          <label>Strategy params (optional JSON)</label>
          <Textarea
            value={strategyParamsJson}
            onChange={(_, data) => setStrategyParamsJson(String(data.value || ''))}
            placeholder='e.g., {"mode":"paper","max_trades_per_day":2}'
          />
        </div>

        {strategyError && <div style={{ color: '#ef4444' }}>{strategyError}</div>}

        <div className="wizard-nav">
          <Button appearance="primary" onClick={onSaveStrategyConfig} disabled={isSavingStrategy}>
            {isSavingStrategy ? 'Saving…' : 'Save Strategy Config'}
          </Button>
        </div>

        <h3 style={{ marginTop: '1rem' }}>Saved strategy configs ({strategyConfigs.length})</h3>
        <ul>
          {strategyConfigs.map((c) => (
            <li key={c.config_ref}>
              {c.agent_id} — interval {c.interval_seconds ?? '—'}s — window {c.active_window ? `${c.active_window.start}–${c.active_window.end}` : '—'} (ref: {c.config_ref})
            </li>
          ))}
        </ul>
      </Card>

      <Card className="wizard-card">
        <h2>Wizard: Step 1/5 - Goal Statement</h2>
        
        <div className="form-group">
          <label>Primary Goal *</label>
          <Textarea 
            placeholder="Publish 5 HIPAA-compliant blog posts per week about diabetes management"
            rows={4}
          />
          <div className="character-count">Character count: 85/500</div>
        </div>

        <div className="form-group">
          <label>Use Template:</label>
          <div className="template-buttons">
            <Button appearance="outline">Healthcare Content</Button>
            <Button appearance="outline">Marketing Campaign</Button>
            <Button appearance="outline">Sales</Button>
          </div>
        </div>

        <div className="form-group">
          <label>Priority Level:</label>
          <div className="radio-group">
            <label><input type="radio" name="priority" /> P0 Critical</label>
            <label><input type="radio" name="priority" defaultChecked /> P1 High</label>
            <label><input type="radio" name="priority" /> P2 Medium</label>
            <label><input type="radio" name="priority" /> P3 Low</label>
          </div>
        </div>

        <div className="form-group">
          <label>Timeline:</label>
          <div className="radio-group">
            <label><input type="radio" name="timeline" /> Immediate</label>
            <label><input type="radio" name="timeline" defaultChecked /> Weekly</label>
            <label><input type="radio" name="timeline" /> Monthly</label>
          </div>
        </div>

        <div className="wizard-nav">
          <Button appearance="outline">← Back</Button>
          <Button appearance="primary">Next: Criteria →</Button>
        </div>
      </Card>

      <section className="existing-goals">
        <h2>Existing Goals (3)</h2>
        <Card className="goal-item">
          <div className="goal-header">
            <span>✅ Goal 1: Publish 5 blog posts/week</span>
            <span>[P1] [Active]</span>
          </div>
          <div className="goal-status">
            Status: 3/5 complete this week (60%)
          </div>
          <Button appearance="subtle">Edit</Button>
        </Card>
      </section>
    </div>
  )
}

