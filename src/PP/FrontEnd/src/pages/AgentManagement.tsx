import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Card, CardHeader, Text, Body1, Button, Table, TableHeader, TableRow, TableHeaderCell, TableBody, TableCell } from '@fluentui/react-components'
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

        {error && <ApiErrorPanel title="Plant error" error={error} />}

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
    </div>
  )
}
