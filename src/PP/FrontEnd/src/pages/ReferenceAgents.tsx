import { useEffect, useState } from 'react'
import { Card, CardHeader, Text, Body1, Spinner, Button, Input, Checkbox } from '@fluentui/react-components'
import ApiErrorPanel from '../components/ApiErrorPanel'
import { gatewayApiClient } from '../services/gatewayApiClient'

export type PlantReferenceAgent = {
  agent_id: string
  display_name: string
  agent_type: string
  spec: Record<string, unknown>
}

type RunReferenceAgentResponse = {
  agent_id: string
  agent_type: string
  status: string
  review?: Record<string, unknown> | null
  draft: Record<string, unknown>
  published: boolean
}

function parseOptionalNumber(raw: string): number | undefined {
  const trimmed = raw.trim()
  if (!trimmed) return undefined
  const value = Number(trimmed)
  return Number.isFinite(value) ? value : undefined
}

function AgentRunner({ agent }: { agent: PlantReferenceAgent }) {
  const [customerId, setCustomerId] = useState('CUST-1')
  const [planId, setPlanId] = useState('plan_starter')
  const [trialMode, setTrialMode] = useState(false)
  const [purpose, setPurpose] = useState('pp_reference_agent_demo')

  const [language, setLanguage] = useState('')
  const [theme, setTheme] = useState('')
  const [topic, setTopic] = useState('')

  const [exchangeAccountId, setExchangeAccountId] = useState('')
  const [coin, setCoin] = useState('BTC')
  const [units, setUnits] = useState('1')
  const [side, setSide] = useState<'long' | 'short'>('long')
  const [tradeIntent, setTradeIntent] = useState<'enter' | 'exit'>('enter')
  const [market, setMarket] = useState(true)
  const [limitPrice, setLimitPrice] = useState('')
  const [intentAction, setIntentAction] = useState<'place_order' | 'close_position' | ''>('')
  const [approvalId, setApprovalId] = useState('')

  // Metering is required for budgeted plans; seed safe defaults.
  const [estimatedCostUsd, setEstimatedCostUsd] = useState('0.10')
  const [tokensIn, setTokensIn] = useState('11')
  const [tokensOut, setTokensOut] = useState('22')
  const [model, setModel] = useState('')

  const [isRunning, setIsRunning] = useState(false)
  const [runError, setRunError] = useState<unknown>(null)
  const [runResult, setRunResult] = useState<RunReferenceAgentResponse | null>(null)

  const runDraft = async () => {
    setIsRunning(true)
    setRunError(null)
    setRunResult(null)

    try {
      const payload: Record<string, unknown> = {
        customer_id: customerId.trim() || undefined,
        plan_id: planId.trim() || undefined,
        trial_mode: trialMode,
        purpose: purpose.trim() || undefined,
        // Story 1.2 scope: run draft only.
        do_publish: false,
        estimated_cost_usd: parseOptionalNumber(estimatedCostUsd) ?? 0,
        meter_tokens_in: parseOptionalNumber(tokensIn) ?? 0,
        meter_tokens_out: parseOptionalNumber(tokensOut) ?? 0,
        meter_model: model.trim() || undefined,
      }

      if (language.trim()) payload.language = language.trim()
      if (agent.agent_type === 'marketing' && theme.trim()) payload.theme = theme.trim()
      if (agent.agent_type === 'tutor' && topic.trim()) payload.topic = topic.trim()
      if (agent.agent_type === 'trading') {
        if (exchangeAccountId.trim()) payload.exchange_account_id = exchangeAccountId.trim()
        if (coin.trim()) payload.coin = coin.trim()

        const parsedUnits = parseOptionalNumber(units)
        if (parsedUnits !== undefined) payload.units = parsedUnits

        payload.side = side
        payload.action = tradeIntent
        payload.market = market

        const parsedLimitPrice = parseOptionalNumber(limitPrice)
        if (parsedLimitPrice !== undefined) payload.limit_price = parsedLimitPrice

        if (intentAction) payload.intent_action = intentAction
        if (approvalId.trim()) payload.approval_id = approvalId.trim()
      }

      const data = (await gatewayApiClient.runReferenceAgent(agent.agent_id, payload)) as RunReferenceAgentResponse
      setRunResult(data)
    } catch (e) {
      setRunError(e)
    } finally {
      setIsRunning(false)
    }
  }

  return (
    <Card appearance="outline">
      <div style={{ padding: 12, display: 'flex', flexDirection: 'column', gap: 12 }}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
          <div>
            <Text size={200} style={{ display: 'block', marginBottom: 6, opacity: 0.85 }}>Customer ID</Text>
            <Input value={customerId} onChange={(_, data) => setCustomerId(data.value)} placeholder="CUST-123" />
          </div>
          <div>
            <Text size={200} style={{ display: 'block', marginBottom: 6, opacity: 0.85 }}>Plan ID (optional)</Text>
            <Input value={planId} onChange={(_, data) => setPlanId(data.value)} placeholder="plan_starter" />
          </div>

          <div>
            <Text size={200} style={{ display: 'block', marginBottom: 6, opacity: 0.85 }}>Purpose (optional)</Text>
            <Input value={purpose} onChange={(_, data) => setPurpose(data.value)} placeholder="pp_reference_agent_demo" />
          </div>
          <div>
            <Text size={200} style={{ display: 'block', marginBottom: 6, opacity: 0.85 }}>Language (optional)</Text>
            <Input value={language} onChange={(_, data) => setLanguage(data.value)} placeholder="en" />
          </div>

          {agent.agent_type === 'marketing' && (
            <div style={{ gridColumn: '1 / -1' }}>
              <Text size={200} style={{ display: 'block', marginBottom: 6, opacity: 0.85 }}>Theme (optional)</Text>
              <Input value={theme} onChange={(_, data) => setTheme(data.value)} placeholder="Valentine campaign" />
            </div>
          )}

          {agent.agent_type === 'tutor' && (
            <div style={{ gridColumn: '1 / -1' }}>
              <Text size={200} style={{ display: 'block', marginBottom: 6, opacity: 0.85 }}>Topic (optional)</Text>
              <Input value={topic} onChange={(_, data) => setTopic(data.value)} placeholder="Triangles" />
            </div>
          )}

          {agent.agent_type === 'trading' && (
            <>
              <div style={{ gridColumn: '1 / -1' }}>
                <Text size={200} style={{ display: 'block', marginBottom: 6, opacity: 0.85 }}>Exchange account ID</Text>
                <Input value={exchangeAccountId} onChange={(_, data) => setExchangeAccountId(data.value)} placeholder="EXCH-..." />
              </div>

              <div>
                <Text size={200} style={{ display: 'block', marginBottom: 6, opacity: 0.85 }}>Coin</Text>
                <Input value={coin} onChange={(_, data) => setCoin(data.value)} placeholder="BTC" />
              </div>
              <div>
                <Text size={200} style={{ display: 'block', marginBottom: 6, opacity: 0.85 }}>Units</Text>
                <Input value={units} onChange={(_, data) => setUnits(data.value)} placeholder="1" />
              </div>

              <div>
                <Text size={200} style={{ display: 'block', marginBottom: 6, opacity: 0.85 }}>Side</Text>
                <Input value={side} onChange={(_, data) => setSide((data.value as any) || 'long')} placeholder="long" />
              </div>
              <div>
                <Text size={200} style={{ display: 'block', marginBottom: 6, opacity: 0.85 }}>Action</Text>
                <Input value={tradeIntent} onChange={(_, data) => setTradeIntent((data.value as any) || 'enter')} placeholder="enter" />
              </div>

              <div>
                <Text size={200} style={{ display: 'block', marginBottom: 6, opacity: 0.85 }}>Intent action (optional; required for execution)</Text>
                <Input value={intentAction} onChange={(_, data) => setIntentAction((data.value as any) || '')} placeholder="place_order" />
              </div>
              <div>
                <Text size={200} style={{ display: 'block', marginBottom: 6, opacity: 0.85 }}>Approval ID (optional)</Text>
                <Input value={approvalId} onChange={(_, data) => setApprovalId(data.value)} placeholder="APR-..." />
              </div>

              <div>
                <Text size={200} style={{ display: 'block', marginBottom: 6, opacity: 0.85 }}>Limit price (optional)</Text>
                <Input value={limitPrice} onChange={(_, data) => setLimitPrice(data.value)} placeholder="" />
              </div>

              <div style={{ display: 'flex', alignItems: 'flex-end' }}>
                <Checkbox label="Market order" checked={market} onChange={(_, data) => setMarket(!!data.checked)} />
              </div>
            </>
          )}
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 1fr', gap: 12 }}>
          <div>
            <Text size={200} style={{ display: 'block', marginBottom: 6, opacity: 0.85 }}>Estimated Cost USD</Text>
            <Input value={estimatedCostUsd} onChange={(_, data) => setEstimatedCostUsd(data.value)} placeholder="0.10" />
          </div>
          <div>
            <Text size={200} style={{ display: 'block', marginBottom: 6, opacity: 0.85 }}>Tokens In</Text>
            <Input value={tokensIn} onChange={(_, data) => setTokensIn(data.value)} placeholder="11" />
          </div>
          <div>
            <Text size={200} style={{ display: 'block', marginBottom: 6, opacity: 0.85 }}>Tokens Out</Text>
            <Input value={tokensOut} onChange={(_, data) => setTokensOut(data.value)} placeholder="22" />
          </div>
          <div>
            <Text size={200} style={{ display: 'block', marginBottom: 6, opacity: 0.85 }}>Model (optional)</Text>
            <Input value={model} onChange={(_, data) => setModel(data.value)} placeholder="gpt-4o-mini" />
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12 }}>
          <Checkbox label="Trial mode" checked={trialMode} onChange={(_, data) => setTrialMode(!!data.checked)} />
          <Button appearance="primary" onClick={() => void runDraft()} disabled={isRunning}>
            {isRunning ? 'Running…' : 'Run Draft'}
          </Button>
        </div>

        {!!runError && <ApiErrorPanel title="Run error" error={runError} />}

        {runResult && (
          <div>
            <Text weight="semibold">Run Result</Text>
            <Text size={200} style={{ display: 'block', marginTop: 4, opacity: 0.85 }}>
              Status: {runResult.status} • Published: {String(runResult.published)}
            </Text>
            <pre
              style={{
                marginTop: 8,
                padding: 12,
                background: 'rgba(255,255,255,0.04)',
                border: '1px solid rgba(255,255,255,0.08)',
                borderRadius: 8,
                overflowX: 'auto'
              }}
            >
              {JSON.stringify(runResult.draft, null, 2)}
            </pre>
          </div>
        )}
      </div>
    </Card>
  )
}

export default function ReferenceAgents() {
  const [agents, setAgents] = useState<PlantReferenceAgent[] | null>(null)
  const [error, setError] = useState<unknown>(null)

  useEffect(() => {
    let cancelled = false

    async function load() {
      try {
        setError(null)
        const data = (await gatewayApiClient.listReferenceAgents()) as PlantReferenceAgent[]
        if (!cancelled) setAgents(data)
      } catch (e) {
        if (!cancelled) setError(e)
      }
    }

    void load()
    return () => {
      cancelled = true
    }
  }, [])

  return (
    <div className="page-container">
      <div className="page-header">
        <Text as="h1" size={900} weight="semibold">Reference Agents</Text>
        <Body1>Demo agents manufactured from AgentSpecs (Plant)</Body1>
      </div>

      {!!error && <ApiErrorPanel title="Failed to load reference agents" error={error} />}

      {!error && agents === null ? (
        <Card style={{ padding: 16 }}>
          <Spinner label="Loading reference agents..." />
        </Card>
      ) : null}

      {agents && (
        <Card>
          <CardHeader header={<Text weight="semibold">Available Agents ({agents.length})</Text>} />
          <div style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {agents.map((agent) => (
              <Card key={agent.agent_id} appearance="outline">
                <div style={{ padding: 12, display: 'flex', flexDirection: 'column', gap: 12 }}>
                  <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', gap: 12 }}>
                    <Text weight="semibold">{agent.display_name}</Text>
                    <Text size={200} style={{ opacity: 0.85 }}>{agent.agent_type}</Text>
                  </div>
                  <Text size={200} style={{ opacity: 0.9 }}>ID: {agent.agent_id}</Text>
                  <pre style={{ margin: 0, whiteSpace: 'pre-wrap', fontSize: 12, opacity: 0.9 }}>
                    {JSON.stringify(agent.spec, null, 2)}
                  </pre>

                  <AgentRunner agent={agent} />
                </div>
              </Card>
            ))}
          </div>
        </Card>
      )}
    </div>
  )
}
