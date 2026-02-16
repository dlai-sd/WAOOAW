import AgentCard from '../components/AgentCard'
import { mockAgents } from '../lib/mockData'

export default function MarketplaceSection() {
  return (
    <section className="marketplace-section" id="agents">
      <div className="container">
        <div className="marketplace-header">
          <h2 className="marketplace-title">Top agents, ready to work</h2>
          <p className="marketplace-subtitle">Browse specialists with real outcomes, fast response, and clear pricing.</p>
        </div>
        <div className="agents-grid">
          {mockAgents.slice(0, 6).map((agent) => (
            <AgentCard key={agent.id} agent={agent as any} />
          ))}
        </div>
      </div>
    </section>
  )
}
