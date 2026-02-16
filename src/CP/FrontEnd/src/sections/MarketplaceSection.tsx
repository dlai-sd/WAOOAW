import { Card, Text } from '@fluentui/react-components'
import { mockAgents } from '../lib/mockData'

export default function MarketplaceSection() {
  return (
    <section className="marketplace-section">
      <div className="container">
        <div className="agents-grid">
          {mockAgents.map((agent) => (
            <Card key={agent.id}>
              <div style={{ padding: '1rem' }}>
                <Text weight="semibold">
                  {agent.avatar} {agent.name}
                </Text>
                <div style={{ marginTop: '0.25rem' }}>
                  <Text size={200}>{agent.industry}</Text>
                </div>
                <div style={{ marginTop: '0.25rem' }}>
                  <Text size={200}>{agent.specialty}</Text>
                </div>
              </div>
            </Card>
          ))}
        </div>
      </div>
    </section>
  )
}
