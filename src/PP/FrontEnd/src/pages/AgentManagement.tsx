import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { Card, CardHeader, Text, Body1, Button, Table, TableHeader, TableRow, TableHeaderCell, TableBody, TableCell, Field, Textarea } from '@fluentui/react-components'
import ApiErrorPanel from '../components/ApiErrorPanel'
import { gatewayApiClient } from '../services/gatewayApiClient'

type PlantAgent = {
  id: string
  name?: string
  industry?: string
  industry_id?: string
  status?: string
  team_id?: string | null
  team_name?: string | null
  created_at?: string
}

export default function AgentManagement() {
  const [agents, setAgents] = useState<PlantAgent[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<unknown>(null)

  const [agentTypes, setAgentTypes] = useState<any[]>([])
  const [agentTypesLoading, setAgentTypesLoading] = useState(true)
  const [agentTypesError, setAgentTypesError] = useState<unknown>(null)
  const [editorId, setEditorId] = useState<string>('')
  const [editorRaw, setEditorRaw] = useState<string>('')
  const [publishBusy, setPublishBusy] = useState(false)

  useEffect(() => {
    const abortController = new AbortController()

    async function loadAgents() {
      setIsLoading(true)
      setError(null)
      try {
        const data = (await gatewayApiClient.listAgents()) as PlantAgent[]
        setAgents(Array.isArray(data) ? data : [])
      } catch (e: any) {
        if (e?.name === 'AbortError') return
        setError(e)
        setAgents([])
      } finally {
        setIsLoading(false)
      }
    }

    void loadAgents()
    return () => abortController.abort()
  }, [])

  useEffect(() => {
    let cancelled = false

    async function loadAgentTypes() {
      setAgentTypesLoading(true)
      setAgentTypesError(null)
      try {
        const data = (await gatewayApiClient.listAgentTypeDefinitions()) as any[]
        if (cancelled) return
        setAgentTypes(Array.isArray(data) ? data : [])
      } catch (e: any) {
        if (cancelled) return
        setAgentTypesError(e)
        setAgentTypes([])
      } finally {
        if (!cancelled) setAgentTypesLoading(false)
      }
    }

    void loadAgentTypes()
    return () => {
      cancelled = true
    }
  }, [])

  const editorJsonError = useMemo(() => {
    if (!editorRaw.trim()) return null
    try {
      JSON.parse(editorRaw)
      return null
    } catch (e: any) {
      return String(e?.message || 'Invalid JSON')
    }
  }, [editorRaw])

  const editorSkillKeysError = useMemo(() => {
    if (!editorRaw.trim()) return null
    if (editorJsonError) return null
    try {
      const parsed = JSON.parse(editorRaw)
      const keys = parsed?.required_skill_keys
      if (!Array.isArray(keys)) return 'required_skill_keys must be a string[]'
      if (keys.length === 0) return 'required_skill_keys must include at least one skill_key'
      const bad = keys.filter((k: any) => typeof k !== 'string' || !String(k).trim())
      if (bad.length > 0) return 'required_skill_keys must contain only non-empty strings'
      return null
    } catch {
      return null
    }
  }, [editorRaw, editorJsonError])

  async function handleEditAgentType(agentTypeId: string) {
    setAgentTypesError(null)
    try {
      const data = await gatewayApiClient.getAgentTypeDefinition(agentTypeId)
      setEditorId(agentTypeId)
      setEditorRaw(JSON.stringify(data, null, 2))
    } catch (e: any) {
      setAgentTypesError(e)
    }
  }

  async function handlePublish() {
    if (!editorId.trim()) return
    if (editorJsonError) return
    if (editorSkillKeysError) return

    setPublishBusy(true)
    setAgentTypesError(null)
    try {
      const parsed = JSON.parse(editorRaw)
      const saved = await gatewayApiClient.publishAgentTypeDefinition(editorId, parsed)
      setEditorRaw(JSON.stringify(saved, null, 2))
      const refreshed = (await gatewayApiClient.listAgentTypeDefinitions()) as any[]
      setAgentTypes(Array.isArray(refreshed) ? refreshed : [])
    } catch (e: any) {
      setAgentTypesError(e)
    } finally {
      setPublishBusy(false)
    }
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <Text as="h1" size={900} weight="semibold">Agent Management</Text>
        <Body1>Create, certify, and deploy AI agents</Body1>
      </div>

      <div style={{ display: 'flex', gap: 12, marginBottom: 16 }}>
        <Link to="/agents" style={{ textDecoration: 'none' }}>
          <Button appearance="primary">Agents</Button>
        </Link>
        <Link to="/agents/data" style={{ textDecoration: 'none' }}>
          <Button appearance="secondary">Agent Data</Button>
        </Link>
      </div>

      <Card>
        <CardHeader header={<Text weight="semibold">All Agents</Text>} />
        {isLoading && (
          <div style={{ padding: 16 }}>
            <Text>Loading from Plant…</Text>
          </div>
        )}

        {!!error && <ApiErrorPanel title="Plant error" error={error} />}

        <Table>
          <TableHeader>
            <TableRow>
              <TableHeaderCell>Name</TableHeaderCell>
              <TableHeaderCell>Industry</TableHeaderCell>
              <TableHeaderCell>Status</TableHeaderCell>
              <TableHeaderCell>Team</TableHeaderCell>
              <TableHeaderCell>Actions</TableHeaderCell>
            </TableRow>
          </TableHeader>
          <TableBody>
            {agents.map(agent => (
              <TableRow key={agent.id}>
                <TableCell>{agent.name || agent.id}</TableCell>
                <TableCell>{agent.industry || agent.industry_id || '-'}</TableCell>
                <TableCell>{agent.status || '-'}</TableCell>
                <TableCell>{agent.team_name || agent.team_id || '-'}</TableCell>
                <TableCell>
                  <Button size="small" appearance="subtle">Manage</Button>
                </TableCell>
              </TableRow>
            ))}

            {!isLoading && !error && agents.length === 0 && (
              <TableRow>
                <TableCell colSpan={5}>
                  <Text>No agents returned from Plant.</Text>
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </Card>

      <div style={{ height: 16 }} />

      <Card>
        <CardHeader header={<Text weight="semibold">Agent Type Definitions</Text>} />

        {agentTypesLoading && (
          <div style={{ padding: 16 }}>
            <Text>Loading agent types…</Text>
          </div>
        )}

        {!!agentTypesError && <ApiErrorPanel title="AgentTypes error" error={agentTypesError} />}

        <Table>
          <TableHeader>
            <TableRow>
              <TableHeaderCell>Agent type</TableHeaderCell>
              <TableHeaderCell>Version</TableHeaderCell>
              <TableHeaderCell>Actions</TableHeaderCell>
            </TableRow>
          </TableHeader>
          <TableBody>
            {agentTypes.map((t) => (
              <TableRow key={String(t?.agent_type_id || '')}>
                <TableCell>{String(t?.agent_type_id || '-')}</TableCell>
                <TableCell>{String(t?.version || '-')}</TableCell>
                <TableCell>
                  <Button size="small" appearance="subtle" onClick={() => handleEditAgentType(String(t?.agent_type_id || ''))}>
                    Edit
                  </Button>
                </TableCell>
              </TableRow>
            ))}

            {!agentTypesLoading && !agentTypesError && agentTypes.length === 0 && (
              <TableRow>
                <TableCell colSpan={3}>
                  <Text>No agent types returned from Plant.</Text>
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>

        <div style={{ padding: 16, display: 'flex', flexDirection: 'column', gap: 12, maxWidth: 900 }}>
          <Field label="Selected agent_type_id">
            <Textarea value={editorId} readOnly rows={1} />
          </Field>

          <Field label={editorJsonError ? `Definition JSON (error: ${editorJsonError})` : 'Definition JSON'}>
            <Textarea value={editorRaw} onChange={(_: unknown, data: any) => setEditorRaw(data.value)} rows={12} />
          </Field>

          <div>
            <Text size={200} style={{ display: 'block', opacity: 0.85 }}>
              Required field: <code>required_skill_keys</code> (string[] of certified skill_key values).
            </Text>
            {!!editorSkillKeysError && (
              <Text size={200} style={{ display: 'block', marginTop: 6, color: 'var(--colorPaletteRedForeground1)' }}>
                {editorSkillKeysError}
              </Text>
            )}
          </div>

          <div style={{ display: 'flex', gap: 12 }}>
            <Button appearance="primary" onClick={handlePublish} disabled={publishBusy || !editorId.trim() || !!editorJsonError || !!editorSkillKeysError}>
              Publish
            </Button>
          </div>
        </div>
      </Card>
    </div>
  )
}
