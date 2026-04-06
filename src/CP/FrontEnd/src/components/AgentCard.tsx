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
    specialty?: string
    bestFor?: string
    proofMetric?: string
    responseTime?: string
  }) | (CatalogAgent & {
    status?: AgentStatus | 'available' | 'working' | 'offline'
    avatar?: string
    rating?: number
    specialty?: string
    bestFor?: string
    proofMetric?: string
    responseTime?: string
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
  const specialtyLabel = isCatalogAgent ? agent.job_role_label : agent.specialty || agent.specialization || agent.job_role?.name
  const price = isCatalogAgent ? agent.monthly_price_inr : agent.price
  const lifecycleState = isCatalogAgent ? agent.lifecycle_state : null
  const catalogVersion = isCatalogAgent ? agent.external_catalog_version : null
  const bestFor = agent.bestFor
  const proofMetric = agent.proofMetric
  const responseTime = agent.responseTime

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
    return <Badge appearance="ghost" size="small">{state.replace(/_/g, ' ')}</Badge>
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
      <div className="agent-card-head">
        <div className="agent-avatar-large">
          {getAvatar()}
        </div>
        <div className="agent-identity">
          <div className="agent-name-row">
            <h3>{displayName}</h3>
            {getStatusBadge()}
          </div>
          {specialtyLabel && (
            <p className="agent-specialty agent-specialty--lead">{specialtyLabel}</p>
          )}
          <div className="agent-meta">
            {'rating' in agent && agent.rating && (
              <span className="agent-rating">
                <Star20Filled className="agent-rating-icon" />
                {agent.rating.toFixed(1)}
              </span>
            )}
            {getLifecycleBadge(lifecycleState)}
            {catalogVersion ? <Badge appearance="outline" size="small">{catalogVersion}</Badge> : null}
          </div>
        </div>
      </div>

      <div className="agent-info">
        <div className="agent-pill-row">
          <span className="agent-industry-pill">
            <Briefcase20Regular className="agent-industry-icon" />
            {industryLabel}
          </span>
          {responseTime ? <span className="agent-speed-pill">{responseTime}</span> : null}
        </div>

        {bestFor ? (
          <p className="agent-best-for">
            <span className="agent-best-for-label">Best for</span>
            {bestFor}
          </p>
        ) : null}

        <p className="agent-description">{description}</p>

        {proofMetric || jobRoleName ? (
          <div className="agent-proof-row">
            {proofMetric ? <div className="agent-proof-card">{proofMetric}</div> : null}
            {jobRoleName ? <div className="agent-proof-card agent-proof-card--secondary">{jobRoleName}</div> : null}
          </div>
        ) : null}

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
