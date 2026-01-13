import { Card, CardHeader, Text, Body1, Button, Badge } from '@fluentui/react-components'
import { Checkmark24Regular, Dismiss24Regular } from '@fluentui/react-icons'

export default function GovernorConsole() {
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
    </div>
  )
}
