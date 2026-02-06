import { useCallback, useEffect, useState } from 'react'
import { Card, CardHeader, Text, Body1, Button, Badge, Input, Spinner } from '@fluentui/react-components'
import { Checkmark24Regular, Dismiss24Regular } from '@fluentui/react-icons'
import ApiErrorPanel from '../components/ApiErrorPanel'
import { gatewayApiClient } from '../services/gatewayApiClient'

type PlantReferenceAgent = {
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

export default function GovernorConsole() {
  const [agents, setAgents] = useState<PlantReferenceAgent[]>([])
  const [agentsLoading, setAgentsLoading] = useState(true)
  const [agentsError, setAgentsError] = useState<unknown>(null)

  const [agentId, setAgentId] = useState('')
  const [customerId, setCustomerId] = useState('CUST-1')
  const [planId, setPlanId] = useState('plan_starter')
  const [approvalId, setApprovalId] = useState('')
  const [purpose, setPurpose] = useState('pp_publish_approval_sim')
  const [estimatedCostUsd, setEstimatedCostUsd] = useState('0.10')
  const [tokensIn, setTokensIn] = useState('11')
  const [tokensOut, setTokensOut] = useState('22')

  const [isPublishing, setIsPublishing] = useState(false)
  const [publishError, setPublishError] = useState<unknown>(null)
  const [publishResult, setPublishResult] = useState<RunReferenceAgentResponse | null>(null)

  const loadReferenceAgents = useCallback(async (signal?: AbortSignal) => {
    setAgentsLoading(true)
    setAgentsError(null)
    try {
      const data = (await gatewayApiClient.listReferenceAgents()) as PlantReferenceAgent[]
      setAgents(Array.isArray(data) ? data : [])
      if (!agentId && Array.isArray(data) && data.length > 0) {
        setAgentId(data[0].agent_id)
      }
    } catch (e: any) {
      if (e?.name === 'AbortError' || signal?.aborted) return
      setAgentsError(e)
      setAgents([])
    } finally {
      setAgentsLoading(false)
    }
  }, [agentId])

  useEffect(() => {
    const abortController = new AbortController()
    void loadReferenceAgents(abortController.signal)
    return () => abortController.abort()
  }, [loadReferenceAgents])

  const attemptPublish = async () => {
    setIsPublishing(true)
    setPublishError(null)
    setPublishResult(null)

    try {
      const payload: Record<string, unknown> = {
        customer_id: customerId.trim() || undefined,
        plan_id: planId.trim() || undefined,
        do_publish: true,
        approval_id: approvalId.trim() || undefined,
        purpose: purpose.trim() || undefined,
        estimated_cost_usd: parseOptionalNumber(estimatedCostUsd) ?? 0,
        meter_tokens_in: parseOptionalNumber(tokensIn) ?? 0,
        meter_tokens_out: parseOptionalNumber(tokensOut) ?? 0,
      }

      const data = (await gatewayApiClient.runReferenceAgent(agentId.trim(), payload)) as RunReferenceAgentResponse
      setPublishResult(data)
    } catch (e) {
      setPublishError(e)
    } finally {
      setIsPublishing(false)
    }
  }

  const pendingApprovals = [
    { id: 1, type: 'Agent Deployment', agent: 'Marketing Agent Delta', requestedBy: 'admin@waooaw.com', priority: 'High' },
    { id: 2, type: 'Customer Refund', customer: 'Acme Corp', amount: '₹15,000', priority: 'Medium' },
    { id: 3, type: 'Feature Flag', feature: 'Advanced Analytics', environment: 'Production', priority: 'Low' },
  ]

  return (
    <div className="page-container">
      <div className="page-header">
        <Text as="h1" size={900} weight="semibold">Governor Console</Text>
        <Body1>Approval queue and operational decisions</Body1>
      </div>

      <Card>
        <CardHeader header={<Text weight="semibold">Pending Approvals ({pendingApprovals.length})</Text>} />
        <div style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {pendingApprovals.map(item => (
            <Card key={item.id} appearance="outline">
              <div style={{ padding: '12px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <div>
                  <div style={{ display: 'flex', gap: '8px', alignItems: 'center', marginBottom: '4px' }}>
                    <Text weight="semibold">{item.type}</Text>
                    <Badge appearance="filled" color={item.priority === 'High' ? 'danger' : item.priority === 'Medium' ? 'warning' : 'informative'}>
                      {item.priority}
                    </Badge>
                  </div>
                  <Text size={200}>
                    {'agent' in item && `Agent: ${item.agent} • `}
                    {'customer' in item && `Customer: ${item.customer} • Amount: ${item.amount} • `}
                    {'feature' in item && `Feature: ${item.feature} • ${item.environment} • `}
                    Requested by: {item.requestedBy || 'System'}
                  </Text>
                </div>
                <div style={{ display: 'flex', gap: '8px' }}>
                  <Button appearance="primary" icon={<Checkmark24Regular />} size="small">Approve</Button>
                  <Button appearance="subtle" icon={<Dismiss24Regular />} size="small">Reject</Button>
                </div>
              </div>
            </Card>
          ))}
        </div>
      </Card>

      <Card style={{ marginTop: 24 }}>
        <CardHeader
          header={<Text weight="semibold">Approval-assisted publish (Plant)</Text>}
          description={<Text size={200}>Simulates Plant publish gate via reference agent run</Text>}
          action={
            <Button appearance="subtle" size="small" onClick={() => void loadReferenceAgents()} disabled={agentsLoading}>
              Refresh Agents
            </Button>
          }
        />

        {agentsError && <div style={{ padding: 16 }}><ApiErrorPanel title="Failed to load reference agents" error={agentsError} /></div>}

        <div style={{ padding: 16, display: 'grid', gap: 12, gridTemplateColumns: '1fr 1fr' }}>
          <div style={{ gridColumn: '1 / -1' }}>
            <Text size={200} style={{ display: 'block', marginBottom: 6, opacity: 0.85 }}>Reference Agent</Text>
            {agentsLoading ? (
              <Spinner label="Loading agents..." />
            ) : (
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginBottom: 8 }}>
                {agents.map((a) => (
                  <Button
                    key={a.agent_id}
                    size="small"
                    appearance={a.agent_id === agentId ? 'primary' : 'subtle'}
                    onClick={() => setAgentId(a.agent_id)}
                  >
                    {a.display_name}
                  </Button>
                ))}
              </div>
            )}
            <Input value={agentId} onChange={(_, data) => setAgentId(data.value)} placeholder="AGT-MKT-CAKE-001" />
          </div>

          <div>
            <Text size={200} style={{ display: 'block', marginBottom: 6, opacity: 0.85 }}>Customer ID</Text>
            <Input value={customerId} onChange={(_, data) => setCustomerId(data.value)} placeholder="CUST-1" />
          </div>
          <div>
            <Text size={200} style={{ display: 'block', marginBottom: 6, opacity: 0.85 }}>Plan ID (optional)</Text>
            <Input value={planId} onChange={(_, data) => setPlanId(data.value)} placeholder="plan_starter" />
          </div>

          <div>
            <Text size={200} style={{ display: 'block', marginBottom: 6, opacity: 0.85 }}>Approval ID</Text>
            <Input value={approvalId} onChange={(_, data) => setApprovalId(data.value)} placeholder="APR-123" />
          </div>
          <div>
            <Text size={200} style={{ display: 'block', marginBottom: 6, opacity: 0.85 }}>Purpose (optional)</Text>
            <Input value={purpose} onChange={(_, data) => setPurpose(data.value)} placeholder="pp_publish_approval_sim" />
          </div>

          <div>
            <Text size={200} style={{ display: 'block', marginBottom: 6, opacity: 0.85 }}>Estimated Cost USD</Text>
            <Input value={estimatedCostUsd} onChange={(_, data) => setEstimatedCostUsd(data.value)} placeholder="0.10" />
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
            <div>
              <Text size={200} style={{ display: 'block', marginBottom: 6, opacity: 0.85 }}>Tokens In</Text>
              <Input value={tokensIn} onChange={(_, data) => setTokensIn(data.value)} placeholder="11" />
            </div>
            <div>
              <Text size={200} style={{ display: 'block', marginBottom: 6, opacity: 0.85 }}>Tokens Out</Text>
              <Input value={tokensOut} onChange={(_, data) => setTokensOut(data.value)} placeholder="22" />
            </div>
          </div>
        </div>

        <div style={{ padding: 16, display: 'flex', justifyContent: 'flex-end' }}>
          <Button appearance="primary" onClick={() => void attemptPublish()} disabled={isPublishing || !agentId.trim()}>
            {isPublishing ? 'Attempting…' : 'Attempt Publish'}
          </Button>
        </div>

        {publishError && <div style={{ padding: 16 }}><ApiErrorPanel title="Publish denied" error={publishError} /></div>}

        {publishResult && (
          <div style={{ padding: 16 }}>
            <Text weight="semibold">Publish Result</Text>
            <Text size={200} style={{ display: 'block', marginTop: 4, opacity: 0.85 }}>
              Status: {publishResult.status} • Published: {String(publishResult.published)}
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
              {JSON.stringify(publishResult.draft, null, 2)}
            </pre>
          </div>
        )}
      </Card>
    </div>
  )
}
