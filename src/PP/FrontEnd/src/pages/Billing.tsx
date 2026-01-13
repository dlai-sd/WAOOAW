import { Card, CardHeader, Text, Body1 } from '@fluentui/react-components'

export default function Billing() {
  return (
    <div className="page-container">
      <div className="page-header">
        <Text as="h1" size={900} weight="semibold">Billing & Revenue</Text>
        <Body1>MRR, churn, invoices, and financial metrics</Body1>
      </div>

      <div className="dashboard-grid">
        <Card className="metric-card">
          <CardHeader header={<Text weight="semibold">Monthly Recurring Revenue</Text>} />
          <Text size={700}>₹2,400,000</Text>
          <Text size={200} style={{ color: '#10b981' }}>+12.4% MoM</Text>
        </Card>

        <Card className="metric-card">
          <CardHeader header={<Text weight="semibold">Churn Rate</Text>} />
          <Text size={700}>2.3%</Text>
          <Text size={200}>Better than 5.1% avg</Text>
        </Card>

        <Card className="metric-card">
          <CardHeader header={<Text weight="semibold">ARPU</Text>} />
          <Text size={700}>₹1,945</Text>
          <Text size={200}>Average Revenue Per User</Text>
        </Card>

        <Card className="metric-card">
          <CardHeader header={<Text weight="semibold">Outstanding Invoices</Text>} />
          <Text size={700}>12</Text>
          <Text size={200}>₹1.2M total</Text>
        </Card>
      </div>

      <Card style={{ marginTop: '24px' }}>
        <CardHeader header={<Text weight="semibold">Revenue Breakdown</Text>} />
        <div style={{ padding: '16px' }}>
          <Text>Marketing Agents: ₹1.2M (50%)</Text><br />
          <Text>Education Agents: ₹800K (33%)</Text><br />
          <Text>Sales Agents: ₹400K (17%)</Text>
        </div>
      </Card>
    </div>
  )
}
