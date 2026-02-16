/**
 * Agent Detail Page - Detailed view of a single agent
 * Shows job role, skills, description, and booking options
 */

import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { 
  Button, 
  Spinner, 
  Badge,
  Card
} from '@fluentui/react-components'
import { 
  ArrowLeft20Regular, 
  Star20Filled,
  Briefcase20Regular,
  CheckmarkCircle20Filled,
} from '@fluentui/react-icons'
import { plantAPIService } from '../services/plant.service'
import type { Agent, JobRole, Skill } from '../types/plant.types'
import BookingModal from '../components/BookingModal'

export default function AgentDetail() {
  const { agentId } = useParams<{ agentId: string }>()
  const navigate = useNavigate()
  
  const [agent, setAgent] = useState<Agent | null>(null)
  const [jobRole, setJobRole] = useState<JobRole | null>(null)
  const [skills, setSkills] = useState<Skill[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [bookingModalOpen, setBookingModalOpen] = useState(false)

  const trialDays = agent?.trial_days ?? 7
  const monthlyPrice = agent?.price

  useEffect(() => {
    if (agentId) {
      loadAgentDetails(agentId)
    }
  }, [agentId])

  const loadAgentDetails = async (id: string) => {
    setLoading(true)
    setError(null)

    try {
      // Fetch agent with job role
      const agentData = await plantAPIService.getAgentWithJobRole(id)
      setAgent(agentData)
      setJobRole(agentData.job_role)

      // Fetch skills for the job role
      if (agentData.job_role) {
        const skillsData = await plantAPIService.getJobRoleSkills(agentData.job_role.id)
        setSkills(skillsData)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load agent details')
      console.error('Failed to load agent:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleStartTrial = () => {
    setBookingModalOpen(true)
  }

  const handleBookingSuccess = (result: { order_id: string; subscription_id?: string | null }) => {
    setBookingModalOpen(false)

    if (result.subscription_id) {
      navigate(
        `/hire/receipt/${encodeURIComponent(result.order_id)}?subscriptionId=${encodeURIComponent(result.subscription_id)}&agentId=${encodeURIComponent(agent?.id || '')}`
      )
      return
    }

    // Fallback: if subscription_id isn't available, return to portal.
    navigate('/portal')
  }

  const getStatusBadge = () => {
    if (!agent) return null
    
    switch (agent.status) {
      case 'active':
        return <Badge appearance="filled" color="success" size="large">Available</Badge>
      case 'inactive':
        return <Badge appearance="ghost" size="large">Inactive</Badge>
      case 'suspended':
        return <Badge appearance="filled" color="danger" size="large">Unavailable</Badge>
      default:
        return null
    }
  }

  const getInitials = (name: string) => {
    return name.split(' ').map(w => w[0]).join('').substring(0, 2).toUpperCase()
  }

  if (loading) {
    return (
      <div className="page-state page-state--loading">
        <Spinner size="large" label="Loading agent details..." />
      </div>
    )
  }

  if (error || !agent) {
    return (
      <div className="agent-detail-page agent-detail-page--narrow">
        <Card className="page-state page-state--error">
          <h3 className="page-state-title page-state-title--error">Failed to Load Agent</h3>
          <p className="page-state-body">{error || 'Agent not found'}</p>
          <Button appearance="primary" onClick={() => navigate('/discover')} className="page-state-action">
            Back to Discovery
          </Button>
        </Card>
      </div>
    )
  }

  return (
    <div className="agent-detail-page">
      {/* Back Button */}
      <Button 
        appearance="subtle" 
        icon={<ArrowLeft20Regular />}
        onClick={() => navigate('/discover')}
        className="agent-detail-back"
      >
        Back to Discovery
      </Button>

      {/* Agent Header */}
      <Card className="agent-detail-header">
        <div className="agent-detail-header-row">
          {/* Avatar */}
          <div
            className="agent-detail-avatar"
          >
            {getInitials(agent.name)}
          </div>

          {/* Info */}
          <div className="agent-detail-info">
            <div className="agent-detail-title-row">
              <h1 className="agent-detail-title">
                {agent.name}
              </h1>
              {getStatusBadge()}
            </div>

            <div className="agent-detail-meta-row">
              <span className="agent-detail-meta">
                <Briefcase20Regular />
                {agent.industry.charAt(0).toUpperCase() + agent.industry.slice(1)}
              </span>
              {/* Placeholder rating - TODO: Get from backend */}
              <span className="agent-detail-meta">
                <Star20Filled className="agent-detail-rating-icon" />
                4.8 (Coming soon)
              </span>
            </div>

            <p className="agent-detail-description">
              {agent.description || jobRole?.description || ''}
            </p>

            {/* CTA Buttons */}
            <div className="agent-detail-cta-row">
              <Button 
                appearance="primary" 
                size="large"
                onClick={handleStartTrial}
                disabled={agent.status !== 'active'}
              >
                {agent.status === 'active' ? `Start ${trialDays}-Day Free Trial` : 'Currently Unavailable'}
              </Button>
              <div className="agent-detail-price">
                {monthlyPrice ? `₹${monthlyPrice.toLocaleString()}/month after trial` : 'Pricing coming soon'}
              </div>
            </div>
          </div>
        </div>
      </Card>

      {/* Job Role & Skills */}
      <div className="agent-detail-grid">
        {/* Job Role */}
        {jobRole && (
          <Card className="agent-detail-card">
            <h2 className="agent-detail-section-title">
              Job Role
            </h2>
            <h3 className="agent-detail-subtitle">
              {jobRole.name}
            </h3>
            <Badge appearance="outline" className="agent-detail-badge">
              {jobRole.seniority_level.charAt(0).toUpperCase() + jobRole.seniority_level.slice(1)} Level
            </Badge>
            <p className="agent-detail-body">
              {jobRole.description}
            </p>
          </Card>
        )}

        {/* Skills */}
        {skills.length > 0 && (
          <Card className="agent-detail-card">
            <h2 className="agent-detail-section-title">
              Required Skills ({skills.length})
            </h2>
            <div className="agent-detail-skill-list">
              {skills.map((skill) => (
                <div
                  key={skill.id}
                  className="agent-detail-skill"
                >
                  <CheckmarkCircle20Filled className="agent-detail-skill-icon" />
                  <div>
                    <div className="agent-detail-skill-name">{skill.name}</div>
                    <div className="agent-detail-skill-meta">
                      {skill.category}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        )}
      </div>

      {/* What You Get */}
      <Card className="agent-detail-card agent-detail-card--spacious">
        <h2 className="agent-detail-section-title">
          What You Get with 7-Day Trial
        </h2>
        <div className="agent-detail-trial-grid">
          <div>
            <h3 className="agent-detail-trial-title">✓ Full Access</h3>
            <p className="agent-detail-body">Complete access to all agent capabilities</p>
          </div>
          <div>
            <h3 className="agent-detail-trial-title">✓ Keep Deliverables</h3>
            <p className="agent-detail-body">Keep everything the agent creates, even if you cancel</p>
          </div>
          <div>
            <h3 className="agent-detail-trial-title">✓ No Credit Card</h3>
            <p className="agent-detail-body">Try first, decide later. No payment info required</p>
          </div>
          <div>
            <h3 className="agent-detail-trial-title">✓ Cancel Anytime</h3>
            <p className="agent-detail-body">Zero commitment. Cancel within 7 days, pay nothing</p>
          </div>
        </div>
      </Card>

      {/* Booking Modal */}
      {agent && (
        <BookingModal
          agent={agent}
          isOpen={bookingModalOpen}
          onClose={() => setBookingModalOpen(false)}
          onSuccess={handleBookingSuccess}
        />
      )}
    </div>
  )
}
