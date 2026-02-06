import { useMemo, useState } from 'react'
import { Body1, Button, Card, CardHeader, Field, Input, Text, Textarea } from '@fluentui/react-components'
import ApiErrorPanel from '../components/ApiErrorPanel'
import { gatewayApiClient } from '../services/gatewayApiClient'

function parseChannels(raw: string): string[] {
  return raw
    .split(',')
    .map(s => s.trim())
    .filter(Boolean)
}

export default function AgentSetup() {
  const [customerId, setCustomerId] = useState('CUST-001')
  const [agentId, setAgentId] = useState('AGT-MKT-HEALTH-001')
  const [channelsRaw, setChannelsRaw] = useState('linkedin,instagram')
  const [postingIdentity, setPostingIdentity] = useState('')
  const [credentialRefsRaw, setCredentialRefsRaw] = useState('{"linkedin":"credref-link-1","instagram":"credref-ig-1"}')

  const [isBusy, setIsBusy] = useState(false)
  const [error, setError] = useState<unknown>(null)
  const [lastSavedAt, setLastSavedAt] = useState<string | null>(null)

  const channels = useMemo(() => parseChannels(channelsRaw), [channelsRaw])

  async function handleLoad() {
    setIsBusy(true)
    setError(null)
    setLastSavedAt(null)
    try {
      const data = await gatewayApiClient.listAgentSetups({ customer_id: customerId, agent_id: agentId, limit: 1 })
      const first = (data?.setups || [])[0]
      if (!first) return

      setChannelsRaw((first.channels || []).join(','))
      setPostingIdentity(first.posting_identity || '')
      setCredentialRefsRaw(JSON.stringify(first.credential_refs || {}, null, 0))
      setLastSavedAt(first.updated_at || null)
    } catch (e: any) {
      setError(e)
    } finally {
      setIsBusy(false)
    }
  }

  async function handleSave() {
    setIsBusy(true)
    setError(null)
    setLastSavedAt(null)

    try {
      const parsedRefs = JSON.parse(credentialRefsRaw || '{}')
      const data = await gatewayApiClient.upsertAgentSetup({
        customer_id: customerId,
        agent_id: agentId,
        channels,
        posting_identity: postingIdentity || null,
        credential_refs: parsedRefs
      })
      setLastSavedAt(data?.updated_at || null)
    } catch (e: any) {
      setError(e)
    } finally {
      setIsBusy(false)
    }
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <Text as="h1" size={900} weight="semibold">Agent Setup</Text>
        <Body1>Post-hire configuration (channels + credential refs)</Body1>
      </div>

      {!!error && <ApiErrorPanel title="AgentSetup error" error={error} />}

      <Card>
        <CardHeader header={<Text weight="semibold">Setup</Text>} />
        <div style={{ padding: 16, display: 'flex', flexDirection: 'column', gap: 12, maxWidth: 900 }}>
          <Field label="Customer ID">
            <Input value={customerId} onChange={(_, data) => setCustomerId(data.value)} />
          </Field>

          <Field label="Agent ID">
            <Input value={agentId} onChange={(_, data) => setAgentId(data.value)} />
          </Field>

          <Field label="Allowed channels (comma-separated)">
            <Input value={channelsRaw} onChange={(_, data) => setChannelsRaw(data.value)} />
          </Field>

          <Field label="Posting identity (optional)">
            <Input value={postingIdentity} onChange={(_, data) => setPostingIdentity(data.value)} />
          </Field>

          <Field label="Credential refs (JSON: channel -> credential_ref)">
            <Textarea value={credentialRefsRaw} onChange={(_, data) => setCredentialRefsRaw(data.value)} rows={5} />
          </Field>

          <div style={{ display: 'flex', gap: 12 }}>
            <Button appearance="secondary" onClick={handleLoad} disabled={isBusy}>Load</Button>
            <Button appearance="primary" onClick={handleSave} disabled={isBusy}>Save</Button>
          </div>

          {lastSavedAt && (
            <Text size={200} style={{ opacity: 0.85 }}>Saved at: {String(lastSavedAt)}</Text>
          )}
        </div>
      </Card>
    </div>
  )
}
