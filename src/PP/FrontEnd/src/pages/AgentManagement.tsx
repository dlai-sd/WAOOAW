import { Card, CardHeader, Text, Body1, Button, Table, TableHeader, TableRow, TableHeaderCell, TableBody, TableCell } from '@fluentui/react-components'
import { Add24Regular } from '@fluentui/react-icons'

export default function AgentManagement() {
  const agents = [
    { id: 1, name: 'Marketing Agent Alpha', industry: 'Marketing', status: 'Active', customers: 23 },
    { id: 2, name: 'Education Tutor Beta', industry: 'Education', status: 'Active', customers: 45 },
    { id: 3, name: 'Sales SDR Gamma', industry: 'Sales', status: 'Pending', customers: 0 },
  ]

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
        <Table>
          <TableHeader>
            <TableRow>
              <TableHeaderCell>Name</TableHeaderCell>
              <TableHeaderCell>Industry</TableHeaderCell>
              <TableHeaderCell>Status</TableHeaderCell>
              <TableHeaderCell>Customers</TableHeaderCell>
              <TableHeaderCell>Actions</TableHeaderCell>
            </TableRow>
          </TableHeader>
          <TableBody>
            {agents.map(agent => (
              <TableRow key={agent.id}>
                <TableCell>{agent.name}</TableCell>
                <TableCell>{agent.industry}</TableCell>
                <TableCell>{agent.status}</TableCell>
                <TableCell>{agent.customers}</TableCell>
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
