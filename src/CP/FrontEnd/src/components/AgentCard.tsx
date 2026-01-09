import { Button, Badge } from '@fluentui/react-components'
import { Star20Filled, ArrowRight20Regular } from '@fluentui/react-icons'

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

interface AgentCardProps {
  agent: Agent
}

export default function AgentCard({ agent }: AgentCardProps) {
  const getStatusBadge = () => {
    switch (agent.status) {
      case 'available':
        return <Badge appearance="filled" color="success" size="small">Available</Badge>
      case 'working':
        return <Badge appearance="filled" color="warning" size="small">Working</Badge>
      case 'offline':
        return <Badge appearance="ghost" size="small">Offline</Badge>
    }
  }

  return (
    <div className="agent-card">
      <div className="agent-info">
        <h3>{agent.name}</h3>
        <div className="agent-meta">
          <span className="agent-rating">
            <Star20Filled style={{ marginRight: '4px', color: '#f59e0b' }} /> {agent.rating}
          </span>
          {getStatusBadge()}
        </div>
        <p className="agent-industry">{agent.industry}</p>
        <p className="agent-specialty">{agent.specialty}</p>
        <div className="agent-footer">
          <span className="agent-price">₹{agent.price.toLocaleString()}/mo</span>
          <Button appearance="primary" size="small" icon={<ArrowRight20Regular />} iconPosition="after">
            Try Free
          </Button>
        </div>
      </div>
    </div>
  )
}
