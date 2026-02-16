import AgentCard from '../components/AgentCard'
import { mockAgents } from '../lib/mockData'

export default function MarketplaceSection() {
  return (
    <section className="marketplace-section">
      <div className="container">
        <div className="agents-grid">
          {mockAgents.slice(0, 6).map((agent) => (
            <AgentCard key={agent.id} agent={agent as any} />
          ))}
        </div>
      </div>
    </section>
  )
}
