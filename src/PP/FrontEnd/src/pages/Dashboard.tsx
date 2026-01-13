import { Card, CardHeader, Text, Body1 } from '@fluentui/react-components'

export default function Dashboard() {
  return (
    <div className="page-container">
      <div className="page-header">
        <Text as="h1" size={900} weight="semibold">Dashboard</Text>
        <Body1>Platform overview and key metrics</Body1>
      </div>

      <div className="dashboard-grid">
        <Card className="metric-card">
          <CardHeader header={<Text weight="semibold">MRR</Text>} />
          <Text size={700}>₹2.4M</Text>
          <Text size={200} style={{ color: '#10b981' }}>+12% vs last month</Text>
        </Card>

        <Card className="metric-card">
          <CardHeader header={<Text weight="semibold">Active Agents</Text>} />
          <Text size={700}>47</Text>
          <Text size={200}>Across 3 industries</Text>
        </Card>

        <Card className="metric-card">
          <CardHeader header={<Text weight="semibold">Customers</Text>} />
          <Text size={700}>1,234</Text>
          <Text size={200} style={{ color: '#10b981' }}>+89 this month</Text>
        </Card>

        <Card className="metric-card">
          <CardHeader header={<Text weight="semibold">Churn Rate</Text>} />
          <Text size={700}>2.3%</Text>
          <Text size={200}>Industry avg: 5.1%</Text>
        </Card>
      </div>
    </div>
  )
}
