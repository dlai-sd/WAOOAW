import { Button, Badge } from '@fluentui/react-components'
import { Star20Filled, ArrowRight20Regular, Briefcase20Regular } from '@fluentui/react-icons'
import type { Agent, AgentStatus, CatalogAgent, CatalogLifecycleState } from '../types/plant.types'

interface AgentCardProps {
  agent: (Omit<Agent, 'status'> & {
    status: AgentStatus | 'available' | 'working' | 'offline'
    avatar?: string
    job_role?: { name: string }
    rating?: number
    price?: number
  }) | (CatalogAgent & {
    status?: AgentStatus | 'available' | 'working' | 'offline'
    avatar?: string
    rating?: number
  })
  onTryAgent?: (agentId: string) => void
}

export default function AgentCard({ agent, onTryAgent }: AgentCardProps) {
  const isCatalogAgent = 'public_name' in agent
  const resolvedStatus = isCatalogAgent
    ? ((agent.lifecycle_state === 'live_on_cp' && agent.approved_for_new_hire) ? 'available' : 'offline')
    : agent.status
  const isTryEnabled = resolvedStatus === 'active' || resolvedStatus === 'available'

  const displayName = isCatalogAgent ? agent.public_name : agent.name
  const industryLabel = isCatalogAgent
    ? agent.industry_name
    : `${agent.industry.charAt(0).toUpperCase()}${agent.industry.slice(1)}`
  const description = isCatalogAgent ? agent.short_description : agent.description
  const jobRoleName = isCatalogAgent ? agent.job_role_label : agent.job_role?.name
  const price = isCatalogAgent ? agent.monthly_price_inr : agent.price
  const lifecycleState = isCatalogAgent ? agent.lifecycle_state : null
  const catalogVersion = isCatalogAgent ? agent.external_catalog_version : null

  const getStatusBadge = () => {
    switch (resolvedStatus) {
      // Legacy/mock status values
      case 'available':
        return <Badge appearance="filled" color="success" size="small">Available</Badge>
      case 'working':
        return <Badge appearance="filled" color="warning" size="small">Working</Badge>
      case 'offline':
        return <Badge appearance="ghost" size="small">Offline</Badge>
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

  const getLifecycleBadge = (state: CatalogLifecycleState | null) => {
    if (!state) return null
    if (state === 'live_on_cp') return <Badge appearance="tint" color="success" size="small">Live on CP</Badge>
    if (state === 'servicing_only') return <Badge appearance="tint" color="warning" size="small">Servicing only</Badge>
    if (state === 'retired_from_catalog') return <Badge appearance="ghost" size="small">Retired</Badge>
    return <Badge appearance="ghost" size="small">{state.replaceAll('_', ' ')}</Badge>
  }

  const getAvatar = () => {
    const rawAvatar = agent.avatar
    if (typeof rawAvatar === 'string' && rawAvatar.trim()) return rawAvatar.trim()
    return '🤖'
  }

  const handleTryClick = () => {
    if (onTryAgent) {
      onTryAgent(agent.id)
    }
  }

  return (
    <div className="agent-card" data-testid={`cp-agent-card-${agent.id}`}>
      <div className="agent-avatar-large">
        {getAvatar()}
      </div>
      <div className="agent-info">
        <h3>{displayName}</h3>
        <div className="agent-meta">
          {'rating' in agent && agent.rating && (
            <span className="agent-rating">
              <Star20Filled className="agent-rating-icon" />
              {agent.rating.toFixed(1)}
            </span>
          )}
          {getStatusBadge()}
          {getLifecycleBadge(lifecycleState)}
          {catalogVersion ? <Badge appearance="outline" size="small">{catalogVersion}</Badge> : null}
        </div>
        <p className="agent-industry">
          <Briefcase20Regular className="agent-industry-icon" />
          {industryLabel}
        </p>
        {jobRoleName && (
          <p className="agent-specialty">{jobRoleName}</p>
        )}
        <p className="agent-description">{description}</p>
        <div className="agent-footer">
          {price ? (
            <span className="agent-price">₹{price.toLocaleString()}/mo</span>
          ) : (
            <span className="agent-price">Contact for pricing</span>
          )}
          <Button 
            appearance="primary" 
            size="small" 
            icon={<ArrowRight20Regular />} 
            iconPosition="after"
            onClick={handleTryClick}
            disabled={!isTryEnabled}
            data-testid={`cp-agent-card-cta-${agent.id}`}
          >
            {isTryEnabled ? 'Try Free 7 Days' : 'Unavailable'}
          </Button>
        </div>
      </div>
    </div>
  )
}
