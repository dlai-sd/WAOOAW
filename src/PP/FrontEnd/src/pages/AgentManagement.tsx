import { useEffect, useMemo, useState } from 'react'
import { Card, CardHeader, Text, Body1, Button, Table, TableHeader, TableRow, TableHeaderCell, TableBody, TableCell } from '@fluentui/react-components'
import { Add24Regular } from '@fluentui/react-icons'
import config from '../config/oauth.config'

type PlantAgent = {
  id: string
  name?: string
  industry?: string
  status?: string
  team_id?: string | null
  created_at?: string
}

export default function AgentManagement() {
  const [agents, setAgents] = useState<PlantAgent[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const agentsUrl = useMemo(() => `${config.apiBaseUrl}/v1/agents`, [])

  useEffect(() => {
    const abortController = new AbortController()

    async function loadAgents() {
      setIsLoading(true)
      setError(null)
      try {
        const res = await fetch(agentsUrl, {
          method: 'GET',
          signal: abortController.signal
        })

        if (!res.ok) {
          const bodyText = await res.text()
          let detail = bodyText
          try {
            const parsed = JSON.parse(bodyText)
            detail = parsed?.detail || parsed?.message || bodyText
          } catch {
            // non-json response
          }
          throw new Error(`${res.status} ${res.statusText}: ${detail}`)
        }

        const data = (await res.json()) as PlantAgent[]
        setAgents(Array.isArray(data) ? data : [])
      } catch (e: any) {
        if (e?.name === 'AbortError') return
        setError(e?.message || 'Failed to load agents')
        setAgents([])
      } finally {
        setIsLoading(false)
      }
    }

    void loadAgents()
    return () => abortController.abort()
  }, [agentsUrl])

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <Text as="h1" size={900} weight="semibold">Agent Management</Text>
          <Body1>Create, certify, and deploy AI agents</Body1>
        </div>
        <Button appearance="primary" icon={<Add24Regular />}>Create Agent</Button>
      </div>

      <Card>
        <CardHeader header={<Text weight="semibold">All Agents</Text>} />
        {isLoading && (
          <div style={{ padding: 16 }}>
            <Text>Loading from Plant…</Text>
          </div>
        )}

        {error && (
          <div style={{ padding: 16 }}>
            <Text weight="semibold">Plant error</Text>
            <div style={{ marginTop: 8 }}>
              <Text>{error}</Text>
            </div>
          </div>
        )}

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
                <TableCell>{agent.industry || '-'}</TableCell>
                <TableCell>{agent.status || '-'}</TableCell>
                <TableCell>{agent.team_id || '-'}</TableCell>
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
    </div>
  )
}
