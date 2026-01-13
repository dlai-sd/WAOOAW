import { Card, CardHeader, Text, Body1, Table, TableHeader, TableRow, TableHeaderCell, TableBody, TableCell, Button } from '@fluentui/react-components'

export default function CustomerManagement() {
  const customers = [
    { id: 1, name: 'Acme Corp', email: 'contact@acme.com', agents: 3, mrr: '₹45,000' },
    { id: 2, name: 'Beta Industries', email: 'info@beta.com', agents: 2, mrr: '₹30,000' },
    { id: 3, name: 'Gamma Solutions', email: 'hello@gamma.com', agents: 5, mrr: '₹75,000' },
  ]

  return (
    <div className="page-container">
      <div className="page-header">
        <Text as="h1" size={900} weight="semibold">Customer Management</Text>
        <Body1>View customers, subscriptions, and usage</Body1>
      </div>

      <Card>
        <CardHeader header={<Text weight="semibold">All Customers</Text>} />
        <Table>
          <TableHeader>
            <TableRow>
              <TableHeaderCell>Company</TableHeaderCell>
              <TableHeaderCell>Email</TableHeaderCell>
              <TableHeaderCell>Agents</TableHeaderCell>
              <TableHeaderCell>MRR</TableHeaderCell>
              <TableHeaderCell>Actions</TableHeaderCell>
            </TableRow>
          </TableHeader>
          <TableBody>
            {customers.map(customer => (
              <TableRow key={customer.id}>
                <TableCell>{customer.name}</TableCell>
                <TableCell>{customer.email}</TableCell>
                <TableCell>{customer.agents}</TableCell>
                <TableCell>{customer.mrr}</TableCell>
                <TableCell>
                  <Button size="small" appearance="subtle">View Details</Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Card>
    </div>
  )
}
