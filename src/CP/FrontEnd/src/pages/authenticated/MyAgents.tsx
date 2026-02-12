import { Card, Button, Badge, Dialog, DialogBody, DialogContent, DialogSurface, DialogTitle, Select, Input, Textarea, Checkbox } from '@fluentui/react-components'
import { Star20Filled } from '@fluentui/react-icons'
import { useNavigate } from 'react-router-dom'
import { useEffect, useMemo, useState } from 'react'

import { AgentSelector } from '../../components/AgentSelector'
import { LoadingIndicator, SaveIndicator, FeedbackMessage, ValidationFeedback } from '../../components/FeedbackIndicators'
import { ListItemSkeleton, PageSkeleton } from '../../components/SkeletonLoaders'
import { cancelSubscription } from '../../services/subscriptions.service'
import { getMyAgentsSummary, type MyAgentInstanceSummary } from '../../services/myAgentsSummary.service'
import { getAgentTypeDefinition, type AgentTypeDefinition, type GoalTemplateDefinition, type SchemaFieldDefinition } from '../../services/agentTypes.service'
import { getHiredAgentBySubscription, upsertHiredAgentDraft, type HiredAgentInstance } from '../../services/hiredAgents.service'
import { upsertPlatformCredential } from '../../services/platformCredentials.service'
import { upsertExchangeSetup } from '../../services/exchangeSetup.service'
import { deleteHiredAgentGoal, listHiredAgentGoals, upsertHiredAgentGoal, type GoalInstance } from '../../services/hiredAgentGoals.service'
import { listHiredAgentDeliverables, reviewHiredAgentDeliverable, type Deliverable } from '../../services/hiredAgentDeliverables.service'

type JsonObject = Record<string, unknown>

function agentTypeIdFromAgentId(agentId: string): string | null {
  const normalized = String(agentId || '').trim().toUpperCase()
  if (normalized.startsWith('AGT-TRD-')) return 'trading.delta_futures.v1'
  if (normalized.startsWith('AGT-MKT-')) return 'marketing.healthcare.v1'
  return null
}

function normalizeString(value: unknown): string {
  return String(value ?? '')
}

function parseListText(value: string): string[] {
  return String(value || '')
    .split(/\n|,/g)
    .map((x) => x.trim())
    .filter(Boolean)
}

function stableJsonStringify(value: unknown): string {
  try {
    return JSON.stringify(value ?? {}, null, 2)
  } catch {
    return '{\n}'
  }
}

function getSchemaField(schema: AgentTypeDefinition | null, key: string): SchemaFieldDefinition | null {
  const fields = schema?.config_schema?.fields || []
  return fields.find((f) => f.key === key) || null
}

function requiredLabel(label: string, required?: boolean): string {
  return required ? `${label} *` : label
}

function isPlainObject(value: unknown): value is JsonObject {
  return Boolean(value) && typeof value === 'object' && !Array.isArray(value)
}

function validateRequiredField(field: SchemaFieldDefinition, value: unknown): string | null {
  if (!field.required) return null

  if (field.type === 'text' || field.type === 'enum') {
    if (!String(value || '').trim()) {
      return field.type === 'enum' 
        ? `Please select a ${field.label.toLowerCase()} from the dropdown`
        : `${field.label} is required and cannot be empty`
    }
    return null
  }

  if (field.type === 'number') {
    const n = typeof value === 'number' ? value : Number(String(value || ''))
    if (!Number.isFinite(n)) {
      return `${field.label} must be a valid number`
    }
    return null
  }

  if (field.type === 'boolean') {
    return typeof value === 'boolean' ? null : `${field.label} must be set to true or false`
  }

  if (field.type === 'list') {
    if (!Array.isArray(value) || value.length === 0) {
      return `${field.label} requires at least one item`
    }
    return null
  }

  if (field.type === 'object') {
    if (!isPlainObject(value)) {
      return `${field.label} must be a valid JSON object`
    }
    return null
  }

  return null
}

function getGoalTemplate(definition: AgentTypeDefinition | null, goalTemplateId: string): GoalTemplateDefinition | null {
  const templates = definition?.goal_templates || []
  return templates.find((t) => t.goal_template_id === goalTemplateId) || null
}

function renderFrequencyLabel(freq: string): string {
  const key = String(freq || '').trim().toLowerCase()
  if (!key) return '—'
  if (key === 'on_demand') return 'On demand'
  return key[0].toUpperCase() + key.slice(1)
}

function JsonObjectTextarea(props: {
  value: unknown
  disabled: boolean
  onChangeObject: (value: JsonObject) => void
}) {
  const text = stableJsonStringify(props.value ?? {})
  const [localText, setLocalText] = useState(text)

  useEffect(() => {
    setLocalText(text)
  }, [text])

  const parseAndSet = (raw: string) => {
    setLocalText(raw)
    try {
      const parsed = JSON.parse(raw || '{}')
      if (isPlainObject(parsed)) {
        props.onChangeObject(parsed)
      }
    } catch {
      // keep raw; validation happens on save.
    }
  }

  return <Textarea value={localText} disabled={props.disabled} onChange={(_, data) => parseAndSet(String(data.value || ''))} />
}

function ConfigureAgentPanel(props: {
  instance: MyAgentInstanceSummary
  readOnly: boolean
  onSaved: (updated: HiredAgentInstance) => void
}) {
  const { instance, readOnly, onSaved } = props

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [draft, setDraft] = useState<HiredAgentInstance | null>(null)
  const [definition, setDefinition] = useState<AgentTypeDefinition | null>(null)

  const [nickname, setNickname] = useState('')
  const [theme, setTheme] = useState('default')
  const [config, setConfig] = useState<JsonObject>({})

  const [constraintsJson, setConstraintsJson] = useState('')
  const [saving, setSaving] = useState(false)
  const [savedAt, setSavedAt] = useState<number | null>(null)
  const [touchedFields, setTouchedFields] = useState<Record<string, boolean>>({})

  const [platformTokenDrafts, setPlatformTokenDrafts] = useState<Record<string, { access: string; refresh: string; posting: string }>>({})
  const [connectingPlatform, setConnectingPlatform] = useState<string | null>(null)

  const [exchangeApiKey, setExchangeApiKey] = useState('')
  const [exchangeApiSecret, setExchangeApiSecret] = useState('')
  const [exchangeDefaultCoin, setExchangeDefaultCoin] = useState('BTC')
  const [exchangeAllowedCoinsText, setExchangeAllowedCoinsText] = useState('BTC')
  const [exchangeMaxUnitsPerOrder, setExchangeMaxUnitsPerOrder] = useState('1')
  const [exchangeMaxNotionalInr, setExchangeMaxNotionalInr] = useState('')
  const [connectingExchange, setConnectingExchange] = useState(false)

  useEffect(() => {
    let cancelled = false

    const load = async () => {
      setLoading(true)
      setError(null)
      setSavedAt(null)

      try {
        let draftResp: HiredAgentInstance | null = null
        try {
          draftResp = await getHiredAgentBySubscription(instance.subscription_id)
        } catch (e: any) {
          // No draft yet is okay.
          if (e?.status !== 404 && e?.problem?.status !== 404) {
            throw e
          }
        }
        if (cancelled) return
        setDraft(draftResp)

        const agentTypeId =
          String(draftResp?.agent_type_id || '').trim() ||
          String(instance.agent_type_id || '').trim() ||
          agentTypeIdFromAgentId(instance.agent_id) ||
          null

        if (agentTypeId) {
          const def = await getAgentTypeDefinition(agentTypeId)
          if (cancelled) return
          setDefinition(def)
        } else {
          setDefinition(null)
        }

        const initialNickname = String(draftResp?.nickname || instance.nickname || '').trim()
        const initialTheme = String(draftResp?.theme || '').trim() || 'default'
        const initialConfig = (draftResp?.config && typeof draftResp.config === 'object' ? draftResp.config : {}) as JsonObject

        setNickname(initialNickname)
        setTheme(initialTheme)
        setConfig(initialConfig)

        setConstraintsJson(stableJsonStringify((initialConfig as any)?.constraints ?? {}))

        // Pre-fill exchange fields from config when present
        const exchangeProvider = normalizeString((initialConfig as any)?.exchange_provider || 'delta_exchange_india')
        setConfig((prev) => ({ ...prev, exchange_provider: exchangeProvider }))

        const allowedCoins = Array.isArray((initialConfig as any)?.allowed_coins) ? ((initialConfig as any).allowed_coins as unknown[]) : []
        const allowedCoinsText = allowedCoins.length ? allowedCoins.map((x) => String(x || '').trim()).filter(Boolean).join('\n') : 'BTC'
        setExchangeAllowedCoinsText(allowedCoinsText)

        const defaultCoin = String((initialConfig as any)?.default_coin || 'BTC').trim() || 'BTC'
        setExchangeDefaultCoin(defaultCoin)

        const riskLimits = (initialConfig as any)?.risk_limits
        if (riskLimits && typeof riskLimits === 'object') {
          const maxUnits = (riskLimits as any).max_units_per_order
          const maxNotional = (riskLimits as any).max_notional_inr
          if (maxUnits !== undefined && maxUnits !== null) setExchangeMaxUnitsPerOrder(String(maxUnits))
          if (maxNotional !== undefined && maxNotional !== null) setExchangeMaxNotionalInr(String(maxNotional))
        }
      } catch (e: any) {
        if (!cancelled) setError(e?.message || 'Failed to load configuration')
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    load()
    return () => {
      cancelled = true
    }
  }, [instance.subscription_id, instance.agent_id, instance.agent_type_id, instance.nickname])

  const schemaFields = definition?.config_schema?.fields || []

  const requiredErrors = useMemo(() => {
    const errors: Record<string, string> = {}
    for (const field of schemaFields) {
      if (!field?.required) continue

      if (field.key === 'nickname') {
        if (!String(nickname || '').trim()) errors[field.key] = 'Required'
        continue
      }
      if (field.key === 'theme') {
        if (!String(theme || '').trim()) errors[field.key] = 'Required'
        continue
      }
      if (field.key === 'constraints') {
        try {
          const parsed = JSON.parse(constraintsJson || '{}')
          if (!isPlainObject(parsed)) errors[field.key] = 'Required'
        } catch {
          errors[field.key] = 'Invalid JSON'
        }
        continue
      }

      const val = (config as any)[field.key]
      const err = validateRequiredField(field, val)
      if (err) errors[field.key] = err
    }
    return errors
  }, [schemaFields, nickname, theme, config, constraintsJson])

  const canSave = !readOnly && !saving && Object.keys(requiredErrors).length === 0

  const setConfigKey = (key: string, value: unknown) => {
    setConfig((prev) => ({ ...prev, [key]: value }))
  }

  const renderListField = (field: SchemaFieldDefinition, value: unknown) => {
    const listValue = Array.isArray(value) ? (value as unknown[]) : []
    const itemType = field.item_type

    if (itemType === 'enum' && Array.isArray(field.options) && field.options.length) {
      const selected = new Set(listValue.map((x) => String(x || '').toLowerCase()))
      return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
          {field.options.map((opt) => {
            const key = String(opt)
            const checked = selected.has(key.toLowerCase())
            return (
              <Checkbox
                key={key}
                label={key}
                checked={checked}
                disabled={readOnly}
                onChange={(_, data) => {
                  const next = new Set(selected)
                  if (data.checked) next.add(key.toLowerCase())
                  else next.delete(key.toLowerCase())
                  setConfigKey(field.key, Array.from(next))
                }}
              />
            )
          })}
        </div>
      )
    }

    const text = listValue.map((x) => String(x ?? '')).join('\n')
    return (
      <Textarea
        value={text}
        disabled={readOnly}
        onChange={(_, data) => setConfigKey(field.key, parseListText(String(data.value || '')))}
        placeholder="One per line"
      />
    )
  }

  const renderObjectField = (field: SchemaFieldDefinition, value: unknown) => {
    return (
      <JsonObjectTextarea
        value={value ?? {}}
        disabled={readOnly}
        onChangeObject={(obj) => setConfigKey(field.key, obj)}
      />
    )
  }

  const connectPlatform = async (platform: string) => {
    const key = String(platform || '').toLowerCase()
    const draftRow = platformTokenDrafts[key] || { access: '', refresh: '', posting: '' }
    if (!draftRow.access.trim()) {
      setError('Access token is required to connect platform')
      return
    }

    setConnectingPlatform(key)
    setError(null)
    try {
      const resp = await upsertPlatformCredential({
        platform: key,
        access_token: draftRow.access,
        refresh_token: draftRow.refresh || undefined,
        posting_identity: draftRow.posting || undefined
      })

      setConfig((prev) => {
        const existing = (prev as any).platform_credentials
        const nextCreds: JsonObject = isPlainObject(existing) ? { ...existing } : {}
        nextCreds[key] = resp.credential_ref
        return { ...prev, platform_credentials: nextCreds }
      })

      setPlatformTokenDrafts((prev) => ({ ...prev, [key]: { access: '', refresh: '', posting: '' } }))
    } catch (e: any) {
      setError(e?.message || 'Failed to connect platform')
    } finally {
      setConnectingPlatform(null)
    }
  }

  const connectExchange = async () => {
    const exchangeProvider = normalizeString((config as any)?.exchange_provider || 'delta_exchange_india')
    if (!exchangeApiKey.trim() || !exchangeApiSecret.trim()) {
      setError('API key and secret are required to connect exchange')
      return
    }

    const allowed = parseListText(exchangeAllowedCoinsText).map((c) => c.toUpperCase())
    const defaultCoin = String(exchangeDefaultCoin || '').trim().toUpperCase() || 'BTC'

    const maxUnits = Number(exchangeMaxUnitsPerOrder)
    const maxNotional = exchangeMaxNotionalInr.trim() ? Number(exchangeMaxNotionalInr) : undefined
    if (!Number.isFinite(maxUnits) || maxUnits <= 0) {
      setError('Max units per order must be a positive number')
      return
    }
    if (maxNotional !== undefined && (!Number.isFinite(maxNotional) || maxNotional <= 0)) {
      setError('Max notional INR must be a positive number')
      return
    }

    setConnectingExchange(true)
    setError(null)
    try {
      const resp = await upsertExchangeSetup({
        exchange_provider: exchangeProvider,
        api_key: exchangeApiKey,
        api_secret: exchangeApiSecret,
        default_coin: defaultCoin,
        allowed_coins: allowed,
        max_units_per_order: maxUnits,
        ...(maxNotional !== undefined ? { max_notional_inr: maxNotional } : {})
      })

      setConfig((prev) => ({
        ...prev,
        exchange_provider: resp.exchange_provider,
        exchange_credential_ref: resp.credential_ref,
        allowed_coins: resp.allowed_coins,
        default_coin: resp.default_coin,
        risk_limits: resp.risk_limits
      }))

      // Clear secrets from UI after successful connect.
      setExchangeApiKey('')
      setExchangeApiSecret('')
    } catch (e: any) {
      setError(e?.message || 'Failed to connect exchange')
    } finally {
      setConnectingExchange(false)
    }
  }

  const onSaveDraft = async () => {
    setSaving(true)
    setError(null)
    try {
      let constraintsObj: JsonObject | undefined = undefined
      if (getSchemaField(definition, 'constraints')) {
        try {
          const parsed = JSON.parse(constraintsJson || '{}')
          if (isPlainObject(parsed)) constraintsObj = parsed
        } catch {
          // ignore; validation already flags
        }
      }

      const payloadConfig: JsonObject = { ...config }
      if (constraintsObj) payloadConfig.constraints = constraintsObj

      const updated = await upsertHiredAgentDraft({
        subscription_id: instance.subscription_id,
        agent_id: instance.agent_id,
        nickname: nickname || undefined,
        theme: theme || undefined,
        config: payloadConfig
      })
      setDraft(updated)
      setSavedAt(Date.now())
      onSaved(updated)
    } catch (e: any) {
      setError(e?.message || 'Failed to save configuration')
    } finally {
      setSaving(false)
    }
  }

  const renderField = (field: SchemaFieldDefinition) => {
    const key = field.key
    const err = requiredErrors[key]
    const touched = touchedFields[key]

    const markTouched = () => setTouchedFields(prev => ({ ...prev, [key]: true }))

    if (key === 'nickname') {
      return (
        <div>
          <div style={{ fontWeight: 600 }}>{requiredLabel(field.label, field.required)}</div>
          <Input 
            value={nickname} 
            disabled={readOnly} 
            onChange={(_, data) => setNickname(String(data.value || ''))}
            onBlur={markTouched}
          />
          <ValidationFeedback field={field.label} error={err} touched={touched} showSuccess={touched && !err} />
        </div>
      )
    }

    if (key === 'theme') {
      const options = field.options || ['default', 'dark', 'light']
      return (
        <div>
          <div style={{ fontWeight: 600 }}>{requiredLabel(field.label, field.required)}</div>
          <Select 
            value={theme} 
            disabled={readOnly} 
            onChange={(_, data) => {
              setTheme(String(data.value || ''))
              markTouched()
            }}
          >
            {options.map((opt) => (
              <option key={opt} value={opt}>
                {opt}
              </option>
            ))}
          </Select>
          <ValidationFeedback field={field.label} error={err} touched={touched} showSuccess={touched && !err} />
        </div>
      )
    }

    if (key === 'platform_credentials') {
      const enabled = Array.isArray((config as any)?.platforms_enabled) ? ((config as any).platforms_enabled as unknown[]) : []
      const enabledPlatforms = enabled.map((x) => String(x || '').toLowerCase()).filter(Boolean)
      const credsRaw = (config as any)?.platform_credentials
      const creds = isPlainObject(credsRaw) ? (credsRaw as JsonObject) : {}

      return (
        <div>
          <div style={{ fontWeight: 600 }}>{requiredLabel(field.label, field.required)}</div>
          <div style={{ marginTop: '0.25rem', opacity: 0.85 }}>{field.description || 'Connect platforms; CP stores secrets and Plant receives only refs.'}</div>
          {enabledPlatforms.length === 0 ? (
            <div style={{ marginTop: '0.5rem', opacity: 0.85 }}>Select at least one platform above, then connect it here.</div>
          ) : (
            <div style={{ marginTop: '0.75rem', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {enabledPlatforms.map((platform) => {
                const currentRef = normalizeString((creds as any)[platform] || '')
                const row = platformTokenDrafts[platform] || { access: '', refresh: '', posting: '' }

                return (
                  <div key={platform} style={{ padding: '0.75rem', borderRadius: '10px', border: '1px solid var(--colorNeutralStroke2)' }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '0.75rem', flexWrap: 'wrap' }}>
                      <div style={{ fontWeight: 600 }}>{platform}</div>
                      <div style={{ opacity: 0.85 }}>{currentRef ? `Connected (${currentRef})` : 'Not connected'}</div>
                    </div>

                    <div style={{ marginTop: '0.5rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                      <Input
                        value={row.posting}
                        disabled={readOnly}
                        onChange={(_, data) =>
                          setPlatformTokenDrafts((prev) => ({
                            ...prev,
                            [platform]: { ...row, posting: String(data.value || '') }
                          }))
                        }
                        placeholder="Posting identity (optional)"
                      />
                      <Input
                        value={row.access}
                        disabled={readOnly}
                        onChange={(_, data) =>
                          setPlatformTokenDrafts((prev) => ({
                            ...prev,
                            [platform]: { ...row, access: String(data.value || '') }
                          }))
                        }
                        placeholder="Access token"
                      />
                      <Input
                        value={row.refresh}
                        disabled={readOnly}
                        onChange={(_, data) =>
                          setPlatformTokenDrafts((prev) => ({
                            ...prev,
                            [platform]: { ...row, refresh: String(data.value || '') }
                          }))
                        }
                        placeholder="Refresh token (optional)"
                      />
                      <Button
                        appearance="primary"
                        disabled={readOnly || connectingPlatform === platform}
                        onClick={() => connectPlatform(platform)}
                      >
                        {connectingPlatform === platform ? 'Connecting…' : 'Connect'}
                      </Button>
                    </div>
                  </div>
                )
              })}
            </div>
          )}
          <ValidationFeedback field={field.label} error={err} touched={touched} showSuccess={touched && !err} />
        </div>
      )
    }

    if (key === 'exchange_credential_ref') {
      const currentRef = normalizeString((config as any)?.exchange_credential_ref || '')
      return (
        <div>
          <div style={{ fontWeight: 600 }}>{requiredLabel(field.label, field.required)}</div>
          <div style={{ marginTop: '0.25rem', opacity: 0.85 }}>{field.description || 'Connect exchange; CP stores secrets and Plant receives only refs.'}</div>
          <div style={{ marginTop: '0.5rem', opacity: 0.9 }}>{currentRef ? `Connected (${currentRef})` : 'Not connected yet'}</div>

          <div style={{ marginTop: '0.75rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            <Input value={exchangeApiKey} disabled={readOnly} onChange={(_, data) => setExchangeApiKey(String(data.value || ''))} placeholder="API key" />
            <Input value={exchangeApiSecret} disabled={readOnly} onChange={(_, data) => setExchangeApiSecret(String(data.value || ''))} placeholder="API secret" />
            <Input value={exchangeDefaultCoin} disabled={readOnly} onChange={(_, data) => setExchangeDefaultCoin(String(data.value || ''))} placeholder="Default coin (e.g., BTC)" />
            <Textarea value={exchangeAllowedCoinsText} disabled={readOnly} onChange={(_, data) => setExchangeAllowedCoinsText(String(data.value || ''))} placeholder="Allowed coins (one per line)" />
            <Input value={exchangeMaxUnitsPerOrder} disabled={readOnly} onChange={(_, data) => setExchangeMaxUnitsPerOrder(String(data.value || ''))} placeholder="Max units per order" />
            <Input value={exchangeMaxNotionalInr} disabled={readOnly} onChange={(_, data) => setExchangeMaxNotionalInr(String(data.value || ''))} placeholder="Max notional INR (optional)" />
            <Button appearance="primary" disabled={readOnly || connectingExchange} onClick={connectExchange}>
              {connectingExchange ? 'Connecting…' : 'Connect exchange'}
            </Button>
          </div>

          <ValidationFeedback field={field.label} error={err} touched={touched} showSuccess={touched && !err} />
        </div>
      )
    }

    if (key === 'risk_limits') {
      const risk = (config as any)?.risk_limits
      const maxUnits = risk && typeof risk === 'object' ? String((risk as any).max_units_per_order ?? '') : ''
      const maxNotional = risk && typeof risk === 'object' ? String((risk as any).max_notional_inr ?? '') : ''

      return (
        <div>
          <div style={{ fontWeight: 600 }}>{requiredLabel(field.label, field.required)}</div>
          <div style={{ marginTop: '0.5rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            <Input
              value={maxUnits}
              disabled={readOnly}
              onChange={(_, data) => {
                const next = { ...(isPlainObject(risk) ? (risk as JsonObject) : {}) }
                ;(next as any).max_units_per_order = data.value
                setConfigKey('risk_limits', next)
              }}
              placeholder="max_units_per_order"
            />
            <Input
              value={maxNotional}
              disabled={readOnly}
              onChange={(_, data) => {
                const next = { ...(isPlainObject(risk) ? (risk as JsonObject) : {}) }
                ;(next as any).max_notional_inr = data.value
                setConfigKey('risk_limits', next)
              }}
              placeholder="max_notional_inr (optional)"
            />
          </div>
          <ValidationFeedback field={field.label} error={err} touched={touched} showSuccess={touched && !err} />
        </div>
      )
    }

    if (key === 'constraints') {
      return (
        <div>
          <div style={{ fontWeight: 600 }}>{requiredLabel(field.label, field.required)}</div>
          <Textarea value={constraintsJson} disabled={readOnly} onChange={(_, data) => setConstraintsJson(String(data.value || ''))} />
          <ValidationFeedback field={field.label} error={err} touched={touched} showSuccess={touched && !err} />
        </div>
      )
    }

    const value = (config as any)[key]
    if (field.type === 'text') {
      return (
        <div>
          <div style={{ fontWeight: 600 }}>{requiredLabel(field.label, field.required)}</div>
          <Input value={normalizeString(value)} disabled={readOnly} onChange={(_, data) => setConfigKey(key, String(data.value || ''))} />
          <ValidationFeedback field={field.label} error={err} touched={touched} showSuccess={touched && !err} />
        </div>
      )
    }
    if (field.type === 'enum') {
      const options = field.options || []
      return (
        <div>
          <div style={{ fontWeight: 600 }}>{requiredLabel(field.label, field.required)}</div>
          <Select value={normalizeString(value)} disabled={readOnly} onChange={(_, data) => setConfigKey(key, String(data.value || ''))}>
            <option value="">Select…</option>
            {options.map((opt) => (
              <option key={opt} value={opt}>
                {opt}
              </option>
            ))}
          </Select>
          <ValidationFeedback field={field.label} error={err} touched={touched} showSuccess={touched && !err} />
        </div>
      )
    }
    if (field.type === 'number') {
      return (
        <div>
          <div style={{ fontWeight: 600 }}>{requiredLabel(field.label, field.required)}</div>
          <Input value={normalizeString(value)} disabled={readOnly} onChange={(_, data) => setConfigKey(key, data.value)} />
          <ValidationFeedback field={field.label} error={err} touched={touched} showSuccess={touched && !err} />
        </div>
      )
    }
    if (field.type === 'boolean') {
      const checked = Boolean(value)
      return (
        <div>
          <Checkbox
            label={requiredLabel(field.label, field.required)}
            checked={checked}
            disabled={readOnly}
            onChange={(_, data) => setConfigKey(key, Boolean(data.checked))}
          />
          <ValidationFeedback field={field.label} error={err} touched={touched} showSuccess={touched && !err} />
        </div>
      )
    }
    if (field.type === 'list') {
      return (
        <div>
          <div style={{ fontWeight: 600 }}>{requiredLabel(field.label, field.required)}</div>
          {renderListField(field, value)}
          <ValidationFeedback field={field.label} error={err} touched={touched} showSuccess={touched && !err} />
        </div>
      )
    }
    if (field.type === 'object') {
      return (
        <div>
          <div style={{ fontWeight: 600 }}>{requiredLabel(field.label, field.required)}</div>
          {renderObjectField(field, value)}
          <ValidationFeedback field={field.label} error={err} touched={touched} showSuccess={touched && !err} />
        </div>
      )
    }

    return null
  }

  return (
    <div style={{ marginTop: '0.75rem' }}>
      {loading ? (
        <div style={{ marginTop: '1rem' }}>
          <PageSkeleton variant="form" />
        </div>
      ) : null}
      {error ? <FeedbackMessage intent="error" message={error} /> : null}

      {!loading && definition ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div style={{ opacity: 0.85 }}>
            Schema: {definition.agent_type_id} (v{definition.version})
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.9rem' }}>
            {schemaFields.map((f) => (
              <div key={f.key}>{renderField(f)}</div>
            ))}
          </div>

          <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center', flexWrap: 'wrap' }}>
            <Button appearance="primary" onClick={onSaveDraft} disabled={!canSave}>
              {readOnly ? 'Read-only' : 'Save configuration'}
            </Button>
            <SaveIndicator status={saving ? 'saving' : savedAt ? 'saved' : 'idle'} />
            {Object.keys(requiredErrors).length > 0 ? (
              <div style={{ opacity: 0.85 }}>Fill required fields to save.</div>
            ) : null}
            {draft?.configured ? <Badge appearance="filled" color="success" size="small">Configured</Badge> : null}
          </div>
        </div>
      ) : (
        <div style={{ opacity: 0.85 }}>No configuration schema available yet for this agent.</div>
      )}
    </div>
  )
}

function GoalSettingPanel(props: { instance: MyAgentInstanceSummary; readOnly: boolean }) {
  const { instance, readOnly } = props

  const hiredInstanceId = String(instance.hired_instance_id || '').trim()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [definition, setDefinition] = useState<AgentTypeDefinition | null>(null)
  const [goals, setGoals] = useState<GoalInstance[]>([])

  const [editingGoalId, setEditingGoalId] = useState<string | null>(null)
  const [goalTemplateId, setGoalTemplateId] = useState('')
  const [frequency, setFrequency] = useState('weekly')
  const [settings, setSettings] = useState<JsonObject>({})

  const [saving, setSaving] = useState(false)
  const [savedAt, setSavedAt] = useState<number | null>(null)
  const [touchedFields, setTouchedFields] = useState<Record<string, boolean>>({})

  const [deliverablesLoading, setDeliverablesLoading] = useState(false)
  const [deliverablesError, setDeliverablesError] = useState<string | null>(null)
  const [deliverables, setDeliverables] = useState<Deliverable[]>([])
  const [activeDeliverableId, setActiveDeliverableId] = useState<string | null>(null)
  const [reviewNotes, setReviewNotes] = useState('')
  const [reviewing, setReviewing] = useState(false)
  const [reviewSavedAt, setReviewSavedAt] = useState<number | null>(null)

  const agentTypeId = useMemo(() => {
    const fromInstance = String(instance.agent_type_id || '').trim()
    return fromInstance || agentTypeIdFromAgentId(instance.agent_id) || null
  }, [instance.agent_type_id, instance.agent_id])

  const activeTemplate = useMemo(() => {
    if (!definition) return null
    if (!goalTemplateId) return null
    return getGoalTemplate(definition, goalTemplateId)
  }, [definition, goalTemplateId])

  const settingsFields = activeTemplate?.settings_schema?.fields || []

  useEffect(() => {
    let cancelled = false

    const load = async () => {
      setLoading(true)
      setError(null)
      setSavedAt(null)

      try {
        if (!hiredInstanceId) {
          setDefinition(null)
          setGoals([])
          setDeliverables([])
          return
        }

        if (!agentTypeId) {
          setDefinition(null)
          setGoals([])
          setDeliverables([])
          return
        }

        const [defResp, goalsResp] = await Promise.all([
          getAgentTypeDefinition(agentTypeId),
          listHiredAgentGoals(hiredInstanceId)
        ])
        if (cancelled) return

        setDefinition(defResp)
        setGoals((goalsResp?.goals || []).slice())

        const templates = defResp?.goal_templates || []
        if (!goalTemplateId && templates.length) {
          setGoalTemplateId(templates[0].goal_template_id)
          setFrequency(String(templates[0].default_frequency || 'weekly'))
          setSettings({})
        }
      } catch (e: any) {
        if (!cancelled) setError(e?.message || 'Failed to load goals')
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    load()
    return () => {
      cancelled = true
    }
    // Intentionally not depending on goalTemplateId to avoid resetting form during edits.
  }, [hiredInstanceId, agentTypeId])

  useEffect(() => {
    let cancelled = false

    const loadDeliverables = async () => {
      setDeliverablesLoading(true)
      setDeliverablesError(null)
      setReviewSavedAt(null)

      try {
        if (!hiredInstanceId) {
          setDeliverables([])
          setActiveDeliverableId(null)
          setReviewNotes('')
          return
        }

        const resp = await listHiredAgentDeliverables(hiredInstanceId)
        if (cancelled) return
        const next = (resp?.deliverables || []).slice()
        setDeliverables(next)

        const currentId = String(activeDeliverableId || '').trim()
        if (currentId && !next.some((d) => d.deliverable_id === currentId)) {
          setActiveDeliverableId(null)
          setReviewNotes('')
        }
      } catch (e: any) {
        if (!cancelled) setDeliverablesError(e?.message || 'Failed to load drafts')
      } finally {
        if (!cancelled) setDeliverablesLoading(false)
      }
    }

    loadDeliverables()
    return () => {
      cancelled = true
    }
  }, [hiredInstanceId])

  const activeDeliverable = useMemo(() => {
    if (!activeDeliverableId) return null
    return deliverables.find((d) => d.deliverable_id === activeDeliverableId) || null
  }, [deliverables, activeDeliverableId])

  const onReviewDeliverable = async (decision: 'approved' | 'rejected') => {
    if (readOnly) return
    if (!activeDeliverable) return

    setReviewing(true)
    setDeliverablesError(null)
    try {
      const resp = await reviewHiredAgentDeliverable(activeDeliverable.deliverable_id, {
        decision,
        notes: String(reviewNotes || '').trim() || null
      })

      setDeliverables((prev) =>
        prev.map((d) =>
          d.deliverable_id === resp.deliverable_id
            ? {
                ...d,
                review_status: resp.review_status,
                approval_id: resp.approval_id ?? d.approval_id,
                review_notes: String(reviewNotes || '').trim() || null,
                updated_at: resp.updated_at ?? d.updated_at
              }
            : d
        )
      )
      setReviewSavedAt(Date.now())
    } catch (e: any) {
      setDeliverablesError(e?.message || 'Failed to submit review')
    } finally {
      setReviewing(false)
    }
  }

  useEffect(() => {
    if (!activeTemplate) return
    if (editingGoalId) return
    setFrequency(String(activeTemplate.default_frequency || 'weekly'))
    setSettings({})
  }, [activeTemplate?.goal_template_id])

  const requiredErrors = useMemo(() => {
    const errors: Record<string, string> = {}
    if (!goalTemplateId) errors.goal_template_id = 'Required'
    if (!String(frequency || '').trim()) errors.frequency = 'Required'

    for (const field of settingsFields) {
      if (!field?.required) continue
      const val = (settings as any)[field.key]
      const err = validateRequiredField(field, val)
      if (err) errors[field.key] = err
    }
    return errors
  }, [goalTemplateId, frequency, settingsFields, settings])

  const canSave = hiredInstanceId && !readOnly && !saving && Object.keys(requiredErrors).length === 0

  const setSettingKey = (key: string, value: unknown) => {
    setSettings((prev) => ({ ...(prev as any), [key]: value }))
  }

  const renderListField = (field: SchemaFieldDefinition, value: unknown) => {
    const listValue = Array.isArray(value) ? (value as unknown[]) : []
    const itemType = field.item_type

    if (itemType === 'enum' && Array.isArray(field.options) && field.options.length) {
      const selected = new Set(listValue.map((x) => String(x || '').toLowerCase()))
      return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
          {field.options.map((opt) => {
            const key = String(opt)
            const checked = selected.has(key.toLowerCase())
            return (
              <Checkbox
                key={key}
                label={key}
                checked={checked}
                disabled={readOnly}
                onChange={(_, data) => {
                  const next = new Set(selected)
                  if (data.checked) next.add(key.toLowerCase())
                  else next.delete(key.toLowerCase())
                  setSettingKey(field.key, Array.from(next))
                }}
              />
            )
          })}
        </div>
      )
    }

    const text = listValue.map((x) => String(x ?? '')).join('\n')
    return (
      <Textarea
        value={text}
        disabled={readOnly}
        onChange={(_, data) => setSettingKey(field.key, parseListText(String(data.value || '')))}
        placeholder="One per line"
      />
    )
  }

  const renderObjectField = (field: SchemaFieldDefinition, value: unknown) => {
    return (
      <JsonObjectTextarea
        value={value ?? {}}
        disabled={readOnly}
        onChangeObject={(obj) => setSettingKey(field.key, obj)}
      />
    )
  }

  const renderSettingsField = (field: SchemaFieldDefinition) => {
    const key = field.key
    const value = (settings as any)[key]
    const err = requiredErrors[key]
    const touched = touchedFields[key]

    const markTouched = () => setTouchedFields(prev => ({ ...prev, [key]: true }))

    if (field.type === 'text') {
      return (
        <div>
          <div style={{ fontWeight: 600 }}>{requiredLabel(field.label, field.required)}</div>
          <Input
            aria-label={field.label}
            value={String(value ?? '')}
            disabled={readOnly}
            onChange={(_, data) => setSettingKey(key, String(data.value || ''))}
            onBlur={markTouched}
          />
          <ValidationFeedback field={field.label} error={err} touched={touched} showSuccess={touched && !err} />
        </div>
      )
    }

    if (field.type === 'enum') {
      const opts = field.options || []
      return (
        <div>
          <div style={{ fontWeight: 600 }}>{requiredLabel(field.label, field.required)}</div>
          <Select
            aria-label={field.label}
            value={String(value ?? '')}
            disabled={readOnly}
            onChange={(_, data) => {
              setSettingKey(key, String(data.value || ''))
              markTouched()
            }}
          >
            <option value="">Select…</option>
            {opts.map((opt) => (
              <option key={opt} value={opt}>
                {opt}
              </option>
            ))}
          </Select>
          <ValidationFeedback field={field.label} error={err} touched={touched} showSuccess={touched && !err} />
        </div>
      )
    }

    if (field.type === 'number') {
      return (
        <div>
          <div style={{ fontWeight: 600 }}>{requiredLabel(field.label, field.required)}</div>
          <Input
            aria-label={field.label}
            value={value === undefined || value === null ? '' : String(value)}
            disabled={readOnly}
            inputMode="decimal"
            onChange={(_, data) => {
              const raw = String(data.value || '')
              if (!raw.trim()) {
                setSettingKey(key, undefined)
                return
              }
              const parsed = Number(raw)
              setSettingKey(key, Number.isFinite(parsed) ? parsed : raw)
            }}
            onBlur={markTouched}
          />
          <ValidationFeedback field={field.label} error={err} touched={touched} showSuccess={touched && !err} />
        </div>
      )
    }

    if (field.type === 'boolean') {
      const checked = typeof value === 'boolean' ? value : false
      return (
        <div>
          <Checkbox
            label={requiredLabel(field.label, field.required)}
            checked={checked}
            disabled={readOnly}
            onChange={(_, data) => {
              setSettingKey(key, Boolean(data.checked))
              markTouched()
            }}
          />
          <ValidationFeedback field={field.label} error={err} touched={touched} showSuccess={touched && !err} />
        </div>
      )
    }

    if (field.type === 'list') {
      return (
        <div>
          <div style={{ fontWeight: 600 }}>{requiredLabel(field.label, field.required)}</div>
          {renderListField(field, value)}
          <ValidationFeedback field={field.label} error={err} touched={touched} showSuccess={touched && !err} />
        </div>
      )
    }

    if (field.type === 'object') {
      return (
        <div>
          <div style={{ fontWeight: 600 }}>{requiredLabel(field.label, field.required)}</div>
          {renderObjectField(field, value)}
          <ValidationFeedback field={field.label} error={err} touched={touched} showSuccess={touched && !err} />
        </div>
      )
    }

    return null
  }

  const startNewGoal = () => {
    setEditingGoalId(null)
    const templates = definition?.goal_templates || []
    const first = templates[0]
    if (first) {
      setGoalTemplateId(first.goal_template_id)
      setFrequency(String(first.default_frequency || 'weekly'))
    }
    setSettings({})
    setSavedAt(null)
    setError(null)
  }

  const onEditGoal = (g: GoalInstance) => {
    setEditingGoalId(g.goal_instance_id)
    setGoalTemplateId(g.goal_template_id)
    setFrequency(g.frequency)
    setSettings(isPlainObject(g.settings) ? (g.settings as JsonObject) : {})
    setSavedAt(null)
    setError(null)
  }

  const onSaveGoal = async () => {
    if (!hiredInstanceId) return
    if (!goalTemplateId) return

    setSaving(true)
    setError(null)
    try {
      const updated = await upsertHiredAgentGoal(hiredInstanceId, {
        goal_instance_id: editingGoalId,
        goal_template_id: goalTemplateId,
        frequency: frequency,
        settings: settings
      })

      setGoals((prev) => {
        const idx = prev.findIndex((x) => x.goal_instance_id === updated.goal_instance_id)
        if (idx >= 0) {
          const next = prev.slice()
          next[idx] = updated
          return next
        }
        return [updated, ...prev]
      })

      setSavedAt(Date.now())
      setEditingGoalId(null)
    } catch (e: any) {
      setError(e?.message || 'Failed to save goal')
    } finally {
      setSaving(false)
    }
  }

  const onDeleteGoal = async (goalInstanceId: string) => {
    if (!hiredInstanceId) return
    if (readOnly) return

    setError(null)
    try {
      await deleteHiredAgentGoal(hiredInstanceId, goalInstanceId)
      setGoals((prev) => prev.filter((x) => x.goal_instance_id !== goalInstanceId))
      if (editingGoalId === goalInstanceId) {
        startNewGoal()
      }
    } catch (e: any) {
      setError(e?.message || 'Failed to delete goal')
    }
  }

  if (!hiredInstanceId) {
    return <div style={{ marginTop: '0.75rem', opacity: 0.85 }}>Save configuration first to enable Goal Setting.</div>
  }

  if (!agentTypeId) {
    return <div style={{ marginTop: '0.75rem', opacity: 0.85 }}>No goal templates available yet for this agent.</div>
  }

  const templates = definition?.goal_templates || []

  return (
    <div style={{ marginTop: '0.75rem' }}>
      {loading ? (
        <div style={{ marginTop: '1rem' }}>
          <ListItemSkeleton count={3} />
        </div>
      ) : null}
      {error ? <FeedbackMessage intent="error" message={error} /> : null}

      {!loading && templates.length ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div style={{ opacity: 0.85 }}>Templates: {templates.length} available</div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            <div style={{ fontWeight: 600 }}>Your goals ({goals.length})</div>
            {goals.length === 0 ? <div style={{ opacity: 0.85 }}>No goals yet.</div> : null}
            {goals.length ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                {goals.map((g) => {
                  const t = getGoalTemplate(definition, g.goal_template_id)
                  const title = t ? t.name : g.goal_template_id
                  return (
                    <div
                      key={g.goal_instance_id}
                      style={{ padding: '0.75rem', borderRadius: '10px', border: '1px solid var(--colorNeutralStroke2)' }}
                    >
                      <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap' }}>
                        <div>
                          <div style={{ fontWeight: 600 }}>{title}</div>
                          <div style={{ opacity: 0.85 }}>Frequency: {renderFrequencyLabel(g.frequency)}</div>
                        </div>
                        <div style={{ display: 'flex', gap: '0.5rem' }}>
                          <Button appearance="outline" onClick={() => onEditGoal(g)} disabled={readOnly}>
                            Edit
                          </Button>
                          <Button appearance="subtle" onClick={() => onDeleteGoal(g.goal_instance_id)} disabled={readOnly}>
                            Delete
                          </Button>
                        </div>
                      </div>
                    </div>
                  )
                })}
              </div>
            ) : null}
          </div>

          <div style={{ paddingTop: '0.25rem', borderTop: '1px solid var(--colorNeutralStroke2)' }}>
            <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap' }}>
              <div style={{ fontWeight: 600 }}>{editingGoalId ? 'Edit goal' : 'Add goal'}</div>
              <Button appearance="outline" onClick={startNewGoal} disabled={readOnly}>
                New
              </Button>
            </div>

            <div style={{ marginTop: '0.75rem', display: 'flex', flexDirection: 'column', gap: '0.9rem' }}>
              <div>
                <div style={{ fontWeight: 600 }}>Goal template</div>
                <Select
                  value={goalTemplateId}
                  disabled={readOnly}
                  onChange={(_, data) => {
                    setGoalTemplateId(String(data.value || ''))
                    setTouchedFields(prev => ({ ...prev, goal_template_id: true }))
                  }}
                  aria-label="Goal template"
                >
                  {templates.map((t) => (
                    <option key={t.goal_template_id} value={t.goal_template_id}>
                      {t.name}
                    </option>
                  ))}
                </Select>
                <ValidationFeedback 
                  field="Goal template" 
                  error={requiredErrors.goal_template_id} 
                  touched={touchedFields.goal_template_id} 
                  showSuccess={touchedFields.goal_template_id && !requiredErrors.goal_template_id} 
                />
              </div>

              <div>
                <div style={{ fontWeight: 600 }}>Frequency</div>
                <Select
                  value={frequency}
                  disabled={readOnly}
                  onChange={(_, data) => {
                    setFrequency(String(data.value || ''))
                    setTouchedFields(prev => ({ ...prev, frequency: true }))
                  }}
                  aria-label="Goal frequency"
                >
                  {['daily', 'weekly', 'monthly', 'on_demand'].map((opt) => (
                    <option key={opt} value={opt}>
                      {renderFrequencyLabel(opt)}
                    </option>
                  ))}
                </Select>
                <ValidationFeedback 
                  field="Frequency" 
                  error={requiredErrors.frequency} 
                  touched={touchedFields.frequency} 
                  showSuccess={touchedFields.frequency && !requiredErrors.frequency} 
                />
              </div>

              {settingsFields.length ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.9rem' }}>
                  {settingsFields.map((f) => (
                    <div key={f.key}>{renderSettingsField(f)}</div>
                  ))}
                </div>
              ) : (
                <div style={{ opacity: 0.85 }}>No settings required for this goal.</div>
              )}

              <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center', flexWrap: 'wrap' }}>
                <Button appearance="primary" onClick={onSaveGoal} disabled={!canSave}>
                  {readOnly ? 'Read-only' : 'Save goal'}
                </Button>
                <SaveIndicator status={saving ? 'saving' : savedAt ? 'saved' : 'idle'} />
                {Object.keys(requiredErrors).length > 0 ? <div style={{ opacity: 0.85 }}>Fill required fields to save.</div> : null}
              </div>
            </div>
          </div>

          <div style={{ paddingTop: '0.75rem', borderTop: '1px solid var(--colorNeutralStroke2)' }}>
            <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap' }}>
              <div style={{ fontWeight: 600 }}>Drafts ({deliverables.length})</div>
              <Button
                appearance="outline"
                onClick={() => {
                  if (!hiredInstanceId) return
                  setDeliverablesLoading(true)
                  setDeliverablesError(null)
                  listHiredAgentDeliverables(hiredInstanceId)
                    .then((resp) => setDeliverables((resp?.deliverables || []).slice()))
                    .catch((e: any) => setDeliverablesError(e?.message || 'Failed to load drafts'))
                    .finally(() => setDeliverablesLoading(false))
                }}
                disabled={!hiredInstanceId || deliverablesLoading}
              >
                Refresh
              </Button>
            </div>

            {deliverablesLoading ? (
              <div style={{ marginTop: '1rem' }}>
                <ListItemSkeleton count={3} />
              </div>
            ) : null}
            {deliverablesError ? <FeedbackMessage intent="error" message={deliverablesError} /> : null}

            {!deliverablesLoading && deliverables.length === 0 ? <div style={{ marginTop: '0.5rem', opacity: 0.85 }}>No drafts yet.</div> : null}

            {deliverables.length ? (
              <div style={{ marginTop: '0.5rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                {deliverables.map((d) => {
                  const isActive = d.deliverable_id === activeDeliverableId
                  const status = String(d.review_status || '').trim() || 'pending_review'
                  return (
                    <div key={d.deliverable_id} style={{ padding: '0.75rem', borderRadius: '10px', border: '1px solid var(--colorNeutralStroke2)' }}>
                      <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap' }}>
                        <div>
                          <div style={{ fontWeight: 600 }}>{d.title || d.deliverable_id}</div>
                          <div style={{ opacity: 0.85 }}>Status: {status.replace(/_/g, ' ')}</div>
                          {d.approval_id ? <div style={{ opacity: 0.85 }}>Approval: {d.approval_id}</div> : null}
                        </div>
                        <div style={{ display: 'flex', gap: '0.5rem' }}>
                          <Button
                            appearance={isActive ? 'primary' : 'outline'}
                            onClick={() => {
                              setActiveDeliverableId(d.deliverable_id)
                              setReviewNotes(String(d.review_notes || ''))
                              setReviewSavedAt(null)
                            }}
                          >
                            Review
                          </Button>
                        </div>
                      </div>

                      {isActive ? (
                        <div style={{ marginTop: '0.75rem', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                          <div>
                            <div style={{ fontWeight: 600 }}>Draft payload</div>
                            <Textarea value={stableJsonStringify(d.payload || {})} readOnly />
                          </div>

                          <div>
                            <div style={{ fontWeight: 600 }}>Review notes</div>
                            <Textarea
                              aria-label="Review notes"
                              value={reviewNotes}
                              disabled={readOnly || reviewing}
                              onChange={(_, data) => setReviewNotes(String(data.value || ''))}
                              placeholder="Optional notes"
                            />
                          </div>

                          <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center', flexWrap: 'wrap' }}>
                            <Button appearance="primary" disabled={readOnly || reviewing} onClick={() => onReviewDeliverable('approved')}>
                              Approve
                            </Button>
                            <Button appearance="outline" disabled={readOnly || reviewing} onClick={() => onReviewDeliverable('rejected')}>
                              Reject
                            </Button>
                            <SaveIndicator status={reviewing ? 'saving' : reviewSavedAt ? 'saved' : 'idle'} />
                          </div>
                        </div>
                      ) : null}
                    </div>
                  )
                })}
              </div>
            ) : null}
          </div>
        </div>
      ) : (
        <div style={{ opacity: 0.85 }}>No goal templates available yet for this agent.</div>
      )}
    </div>
  )
}

export default function MyAgents() {
  const navigate = useNavigate()

  const RETENTION_DAYS_AFTER_END = 30
  const SELECTED_SUBSCRIPTION_STORAGE_KEY = 'cp_my_agents_selected_subscription_id'

  const [instances, setInstances] = useState<MyAgentInstanceSummary[]>([])
  const [selectedSubscriptionId, setSelectedSubscriptionId] = useState<string>('')
  const [activeSection, setActiveSection] = useState<'configure' | 'goals'>('configure')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [nowMs, setNowMs] = useState(() => Date.now())

  const [confirmOpen, setConfirmOpen] = useState(false)
  const [selected, setSelected] = useState<MyAgentInstanceSummary | null>(null)
  const [cancelling, setCancelling] = useState(false)

  const activeCount = useMemo(() => instances.length, [instances])

  useEffect(() => {
    const timer = setInterval(() => setNowMs(Date.now()), 60_000)
    return () => clearInterval(timer)
  }, [])

  useEffect(() => {
    let cancelled = false

    const load = async () => {
      setLoading(true)
      setError(null)
      try {
        const summary = await getMyAgentsSummary()
        if (cancelled) return
        const nextInstances = summary?.instances || []
        setInstances(nextInstances)

        const persisted = (() => {
          try {
            return String(localStorage.getItem(SELECTED_SUBSCRIPTION_STORAGE_KEY) || '').trim()
          } catch {
            return ''
          }
        })()

        const initial =
          (persisted && nextInstances.some((x) => x.subscription_id === persisted) ? persisted : '') ||
          (nextInstances[0]?.subscription_id || '')

        setSelectedSubscriptionId(initial)
      } catch (e: any) {
        if (!cancelled) setError(e?.message || 'Failed to load subscriptions')
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    load()
    return () => {
      cancelled = true
    }
  }, [])

  useEffect(() => {
    if (!selectedSubscriptionId) return
    try {
      localStorage.setItem(SELECTED_SUBSCRIPTION_STORAGE_KEY, selectedSubscriptionId)
    } catch {
      // ignore
    }
  }, [selectedSubscriptionId])

  const selectedInstance = useMemo(() => {
    if (!selectedSubscriptionId) return null
    return instances.find((x) => x.subscription_id === selectedSubscriptionId) || null
  }, [instances, selectedSubscriptionId])

  const getStatusBadge = (status: string) => {
    const statusMap = {
      active: { appearance: 'filled' as const, color: 'success' as const, label: 'Active' },
      canceled: { appearance: 'ghost' as const, color: undefined, label: 'Canceled' }
    }
    const config = statusMap[status as keyof typeof statusMap] || statusMap.active
    return <Badge appearance={config.appearance} color={config.color} size="small">{config.label}</Badge>
  }

  const formatDate = (iso: string) => {
    try {
      return new Date(iso).toLocaleDateString()
    } catch {
      return iso
    }
  }

  const formatRemaining = (untilIso: string): string => {
    const untilMs = new Date(untilIso).getTime()
    if (!Number.isFinite(untilMs)) return '—'

    const diffMs = Math.max(0, untilMs - nowMs)
    const totalMinutes = Math.floor(diffMs / 60_000)
    const days = Math.floor(totalMinutes / (60 * 24))
    const hours = Math.floor((totalMinutes - days * 60 * 24) / 60)

    if (days > 0) return `${days}d ${hours}h`
    return `${hours}h`
  }

  const renderTrialBanner = (instance: MyAgentInstanceSummary) => {
    const configured = Boolean(instance.configured)
    const status = String(instance.trial_status || '').toLowerCase()

    if (!configured) {
      return (
        <div style={{ marginTop: '0.75rem', padding: '0.75rem', borderRadius: '10px', border: '1px solid var(--colorNeutralStroke2)' }}>
          <div style={{ fontWeight: 600 }}>Trial will start after setup</div>
          <div style={{ marginTop: '0.25rem', opacity: 0.85 }}>
            Finish your configuration to activate the trial.
          </div>
        </div>
      )
    }

    if (status === 'active' && instance.trial_end_at) {
      return (
        <div style={{ marginTop: '0.75rem', padding: '0.75rem', borderRadius: '10px', border: '1px solid var(--colorNeutralStroke2)' }}>
          <div style={{ fontWeight: 600 }}>Trial ends in {formatRemaining(instance.trial_end_at)}</div>
        </div>
      )
    }

    return null
  }

  const onOpenCancel = (instance: MyAgentInstanceSummary) => {
    setSelected(instance)
    setConfirmOpen(true)
  }

  const onConfirmCancel = async () => {
    if (!selected) return
    setCancelling(true)
    setError(null)
    try {
      const updated = await cancelSubscription(selected.subscription_id)
      setInstances((prev) =>
        prev.map((x) =>
          x.subscription_id === updated.subscription_id
            ? {
                ...x,
                duration: updated.duration,
                status: updated.status,
                current_period_start: updated.current_period_start,
                current_period_end: updated.current_period_end,
                cancel_at_period_end: updated.cancel_at_period_end
              }
            : x
        )
      )
      setConfirmOpen(false)
      setSelected(null)
    } catch (e: any) {
      setError(e?.message || 'Failed to schedule cancellation')
    } finally {
      setCancelling(false)
    }
  }

  const selectedReadOnlyExpired = useMemo(() => {
    if (!selectedInstance) return false

    const retentionExpiresAtMs = selectedInstance.retention_expires_at
      ? new Date(selectedInstance.retention_expires_at).getTime()
      : NaN
    if (Number.isFinite(retentionExpiresAtMs)) {
      return nowMs > retentionExpiresAtMs
    }

    const endMs = new Date(selectedInstance.current_period_end).getTime()
    if (!Number.isFinite(endMs)) return false
    if (String(selectedInstance.status || '').toLowerCase() !== 'canceled') return false
    return nowMs > endMs + RETENTION_DAYS_AFTER_END * 24 * 60 * 60 * 1000
  }, [selectedInstance, nowMs])

  const selectedInReadOnlyRetention = useMemo(() => {
    if (!selectedInstance) return false
    if (selectedReadOnlyExpired) return false

    const status = String(selectedInstance.status || '').toLowerCase()
    if (status !== 'canceled') return false

    const endMs = new Date(selectedInstance.current_period_end).getTime()
    if (!Number.isFinite(endMs)) return false
    return nowMs <= endMs + RETENTION_DAYS_AFTER_END * 24 * 60 * 60 * 1000
  }, [selectedInstance, selectedReadOnlyExpired, nowMs])

  return (
    <div className="my-agents-page">
      <div className="page-header">
        <h1>My Agents ({activeCount})</h1>
        <Button appearance="primary" onClick={() => navigate('/discover')}>+ Hire New Agent</Button>
      </div>

      {loading && <LoadingIndicator message="Loading your agents..." size="medium" />}
      {error && <FeedbackMessage intent="error" title="Error" message={error} />}

      {instances.length > 0 ? (
        <Card className="agent-detail-card" style={{ marginTop: '1rem' }}>
          <div style={{ display: 'flex', gap: '1rem', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap' }}>
            <div style={{ minWidth: '300px', maxWidth: '500px', flex: '1' }}>
              <AgentSelector
                agents={instances}
                selectedId={selectedSubscriptionId}
                onChange={setSelectedSubscriptionId}
                loading={loading}
                disabled={selectedReadOnlyExpired}
                label="Selected Agent"
                helperText={selectedReadOnlyExpired ? "This agent's trial has ended" : "View and manage your hired agents"}
              />
            </div>
            <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', flexWrap: 'wrap' }}>
              <Button
                appearance={activeSection === 'configure' ? 'primary' : 'outline'}
                onClick={() => setActiveSection('configure')}
                disabled={selectedReadOnlyExpired}
              >
                Configure
              </Button>
              <Button
                appearance={activeSection === 'goals' ? 'primary' : 'outline'}
                onClick={() => setActiveSection('goals')}
                disabled={selectedReadOnlyExpired}
              >
                Goal Setting
              </Button>
            </div>
          </div>

          {selectedInstance ? (
            <div style={{ marginTop: '1rem' }}>
              <div className="agent-header">
                <div className="agent-title">
                  <h2>{selectedInstance.nickname || selectedInstance.agent_id}</h2>
                  {getStatusBadge(selectedInstance.status)}
                </div>
                <div className="agent-meta">
                  <span className="agent-rating">
                    <Star20Filled style={{ color: '#f59e0b' }} />
                  </span>
                  <span> | Plan: {selectedInstance.duration} | Next billing: {formatDate(selectedInstance.current_period_end)}</span>
                </div>
              </div>

              <div className="agent-goals">
                <h3>Subscription:</h3>
                <div className="goal-progress">
                  <span style={{ opacity: 0.8 }}>ID: {selectedInstance.subscription_id}</span>
                </div>
              </div>

              {selectedReadOnlyExpired && (
                <div style={{ marginTop: '0.75rem', padding: '0.75rem', borderRadius: '10px', border: '1px solid var(--colorNeutralStroke2)' }}>
                  <div style={{ fontWeight: 600 }}>Read-only access expired</div>
                  <div style={{ marginTop: '0.25rem', opacity: 0.85 }}>
                    This hire ended more than {RETENTION_DAYS_AFTER_END} days ago.
                  </div>
                </div>
              )}

              {selectedInReadOnlyRetention && (
                <div style={{ marginTop: '0.75rem', opacity: 0.85 }}>
                  This hire has ended.
                  <div style={{ marginTop: '0.35rem', opacity: 0.9 }}>
                    You keep read-only access to deliverables and configuration for {RETENTION_DAYS_AFTER_END} days, and can export your work.
                  </div>
                </div>
              )}

              <div style={{ marginTop: '0.75rem', display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
                <Button appearance="outline" disabled={selectedReadOnlyExpired}>View Dashboard</Button>
                <Button appearance="outline" disabled={selectedReadOnlyExpired}>Settings</Button>
                <Button
                  appearance="subtle"
                  onClick={() => onOpenCancel(selectedInstance)}
                  disabled={selectedInstance.cancel_at_period_end || String(selectedInstance.status || '').toLowerCase() !== 'active'}
                >
                  End Hire
                </Button>
              </div>

              {renderTrialBanner(selectedInstance)}

              {selectedInstance.cancel_at_period_end && (
                <div style={{ marginTop: '0.75rem', opacity: 0.85 }}>
                  Scheduled to end on {formatDate(selectedInstance.current_period_end)}.
                  <div style={{ marginTop: '0.35rem', opacity: 0.9 }}>
                    After it ends: you keep read-only access to deliverables and configuration for {RETENTION_DAYS_AFTER_END} days, and can export your work.
                  </div>
                </div>
              )}

              <div style={{ marginTop: '1rem', padding: '0.75rem', borderRadius: '10px', border: '1px solid var(--colorNeutralStroke2)' }}>
                {activeSection === 'configure' ? (
                  <>
                    <div style={{ fontWeight: 600 }}>Configure</div>
                    <div style={{ marginTop: '0.25rem', opacity: 0.85 }}>
                      Update this agent’s configuration and connected accounts.
                    </div>

                    <ConfigureAgentPanel
                      instance={selectedInstance}
                      readOnly={selectedReadOnlyExpired || selectedInReadOnlyRetention}
                      onSaved={(updated) => {
                        setInstances((prev) =>
                          prev.map((x) =>
                            x.subscription_id === selectedInstance.subscription_id
                              ? {
                                  ...x,
                                  nickname: updated.nickname ?? x.nickname,
                                  configured: updated.configured ?? x.configured,
                                  goals_completed: updated.goals_completed ?? x.goals_completed,
                                  hired_instance_id: updated.hired_instance_id ?? x.hired_instance_id,
                                  agent_type_id: updated.agent_type_id ?? x.agent_type_id
                                }
                              : x
                          )
                        )
                      }}
                    />
                  </>
                ) : (
                  <>
                    <div style={{ fontWeight: 600 }}>Goal Setting</div>
                    <div style={{ marginTop: '0.25rem', opacity: 0.85 }}>
                      Create and manage goals for this agent. Drafts require approval before any external action.
                    </div>

                    <GoalSettingPanel instance={selectedInstance} readOnly={selectedReadOnlyExpired || selectedInReadOnlyRetention} />
                  </>
                )}
              </div>
            </div>
          ) : null}
        </Card>
      ) : null}

      <Dialog open={confirmOpen} onOpenChange={(_, data) => setConfirmOpen(Boolean(data.open))}>
        <DialogSurface style={{ maxWidth: '520px' }}>
          <DialogBody>
            <DialogTitle>End hire at next billing date?</DialogTitle>
            <DialogContent>
              {selected ? (
                <div>
                  <div style={{ marginBottom: '0.75rem' }}>
                    Plan: <strong>{selected.duration}</strong>
                    <br />
                    Next billing date: <strong>{formatDate(selected.current_period_end)}</strong>
                  </div>
                  <div style={{ opacity: 0.9 }}>
                    Your agent stays active until the billing boundary, then billing stops.
                  </div>

                  <div style={{ marginTop: '1rem' }}>
                    <div style={{ fontWeight: 600, marginBottom: '0.35rem' }}>After your hire ends</div>
                    <div style={{ opacity: 0.9 }}>
                      You keep access to your work — but the agent stops running.
                    </div>
                    <ul style={{ margin: '0.5rem 0 0', paddingLeft: '1.25rem', opacity: 0.9 }}>
                      <li>Deliverables and configuration remain available in read-only.</li>
                      <li>Read-only access remains for {RETENTION_DAYS_AFTER_END} days after the end date.</li>
                      <li>You can export/download your work.</li>
                      <li>No new changes will be made after the end date.</li>
                    </ul>
                  </div>
                </div>
              ) : null}

              <div style={{ display: 'flex', gap: '0.75rem', marginTop: '1.25rem' }}>
                <Button appearance="primary" onClick={onConfirmCancel} disabled={cancelling || !selected}>
                  {cancelling ? 'Scheduling…' : 'Confirm end hire'}
                </Button>
                <Button appearance="outline" onClick={() => setConfirmOpen(false)} disabled={cancelling}>
                  Keep subscription
                </Button>
              </div>
            </DialogContent>
          </DialogBody>
        </DialogSurface>
      </Dialog>
    </div>
  )
}
