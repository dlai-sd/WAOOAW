import { useEffect, useState } from 'react'
import { Card, CardHeader, Text, Body1, Button, Spinner, Table, TableHeader, TableRow, TableHeaderCell, TableBody, TableCell } from '@fluentui/react-components'
import { Add24Regular } from '@fluentui/react-icons'

import config from '../config/oauth.config'

type PPAgent = {
  id: string
  name?: string
  description?: string
  job_role_id?: string
  industry?: string
  status?: string
  team_id?: string | null
  created_at?: string
}

export default function AgentManagement() {
  const [agents, setAgents] = useState<PPAgent[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const loadAgents = async () => {
    setLoading(true)
    setError(null)

    try {
      const resp = await fetch(`${config.apiBaseUrl}/pp/agents`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
      })

      if (!resp.ok) {
        const text = await resp.text()
        throw new Error(text || `Request failed (${resp.status})`)
      }

      const data = (await resp.json()) as PPAgent[]
      setAgents(Array.isArray(data) ? data : [])
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load agents')
      setAgents([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadAgents()
  }, [])

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

        {loading && (
          <div style={{ padding: '1rem' }}>
            <Spinner label="Loading agents..." />
          </div>
        )}

        {error && !loading && (
          <div style={{ padding: '1rem' }}>
            <Text as="p" style={{ color: '#ef4444' }}>{error}</Text>
            <Button appearance="secondary" onClick={loadAgents}>Retry</Button>
          </div>
        )}

        {!loading && !error && agents.length === 0 && (
          <div style={{ padding: '1rem' }}>
            <Text as="p">No agents found.</Text>
          </div>
        )}

        <Table>
          <TableHeader>
            <TableRow>
              <TableHeaderCell>Name</TableHeaderCell>
              <TableHeaderCell>Industry</TableHeaderCell>
              <TableHeaderCell>Status</TableHeaderCell>
              <TableHeaderCell>Created</TableHeaderCell>
              <TableHeaderCell>Actions</TableHeaderCell>
            </TableRow>
          </TableHeader>
          <TableBody>
            {agents.map(agent => (
              <TableRow key={agent.id}>
                <TableCell>{agent.name || agent.id}</TableCell>
                <TableCell>{agent.industry || '-'}</TableCell>
                <TableCell>{agent.status || '-'}</TableCell>
                <TableCell>{agent.created_at ? new Date(agent.created_at).toLocaleString() : '-'}</TableCell>
                <TableCell>
                  <Button size="small" appearance="subtle">Manage</Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Card>
    </div>
  )
}
