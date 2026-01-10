import { SearchBox, Dropdown, Option } from '@fluentui/react-components'
import AgentCard from '../components/AgentCard'
import { mockAgents } from '../lib/mockData'

interface Agent {
  id: string
  name: string
  avatar: string
  rating: number
  industry: string
  specialty: string
  price: number
  status: 'available' | 'working' | 'offline'
}

export default function MarketplaceSection() {
  return (
    <section className="marketplace-section">
      <div className="container">
        <div className="search-bar">
          <SearchBox placeholder="Search agents..." className="search-box" />
          <Dropdown placeholder="All Industries" className="filter-select">
            <Option>All Industries</Option>
            <Option>Marketing</Option>
            <Option>Sales</Option>
            <Option>Education</Option>
          </Dropdown>
          <Dropdown placeholder="All Ratings" className="filter-select">
            <Option>All Ratings</Option>
            <Option>4.5+ Stars</Option>
            <Option>4.0+ Stars</Option>
          </Dropdown>
        </div>
        <div className="agents-grid">
          {mockAgents.map((agent: Agent) => (
            <AgentCard key={agent.id} agent={agent} />
          ))}
        </div>
      </div>
    </section>
  )
}
