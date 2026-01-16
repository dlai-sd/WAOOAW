import { Button, Badge } from '@fluentui/react-components'
import { Star20Filled, ArrowRight20Regular, Briefcase20Regular } from '@fluentui/react-icons'
import type { Agent } from '../types/plant.types'

interface AgentCardProps {
  agent: Agent & { 
    job_role?: { name: string }
    rating?: number 
    price?: number 
  }
  onTryAgent?: (agentId: string) => void
}

export default function AgentCard({ agent, onTryAgent }: AgentCardProps) {
  const getStatusBadge = () => {
    switch (agent.status) {
      case 'active':
        return <Badge appearance="filled" color="success" size="small">Available</Badge>
      case 'inactive':
        return <Badge appearance="ghost" size="small">Inactive</Badge>
      case 'suspended':
        return <Badge appearance="filled" color="danger" size="small">Unavailable</Badge>
      default:
        return <Badge appearance="ghost" size="small">Unknown</Badge>
    }
  }

  // Get initials for avatar (fallback)
  const getInitials = (name: string) => {
    return name.split(' ').map(w => w[0]).join('').substring(0, 2).toUpperCase()
  }

  const handleTryClick = () => {
    if (onTryAgent) {
      onTryAgent(agent.id)
    }
  }

  return (
    <div className="agent-card">
      <div className="agent-avatar-large">
        {getInitials(agent.name)}
      </div>
      <div className="agent-info">
        <h3>{agent.name}</h3>
        <div className="agent-meta">
          {agent.rating && (
            <span className="agent-rating">
              <Star20Filled style={{ marginRight: '4px', color: '#f59e0b' }} /> 
              {agent.rating.toFixed(1)}
            </span>
          )}
          {getStatusBadge()}
        </div>
        <p className="agent-industry">
          <Briefcase20Regular style={{ marginRight: '4px' }} />
          {agent.industry.charAt(0).toUpperCase() + agent.industry.slice(1)}
        </p>
        {agent.job_role && (
          <p className="agent-specialty">{agent.job_role.name}</p>
        )}
        <p className="agent-description">{agent.description}</p>
        <div className="agent-footer">
          {agent.price ? (
            <span className="agent-price">₹{agent.price.toLocaleString()}/mo</span>
          ) : (
            <span className="agent-price">Contact for pricing</span>
          )}
          <Button 
            appearance="primary" 
            size="small" 
            icon={<ArrowRight20Regular />} 
            iconPosition="after"
            onClick={handleTryClick}
            disabled={agent.status !== 'active'}
          >
            {agent.status === 'active' ? 'Try Free 7 Days' : 'Unavailable'}
          </Button>
        </div>
      </div>
    </div>
  )
}
