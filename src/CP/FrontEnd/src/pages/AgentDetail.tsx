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
  Card,
  Dialog,
  DialogSurface,
  DialogTitle,
  DialogBody,
  DialogContent
} from '@fluentui/react-components'
import { 
  ArrowLeft20Regular, 
  Star20Filled,
  Briefcase20Regular,
  CheckmarkCircle20Filled,
  Checkmark24Filled
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
      <div style={{ textAlign: 'center', padding: '3rem' }}>
        <Spinner size="large" label="Loading agent details..." />
      </div>
    )
  }

  if (error || !agent) {
    return (
      <div style={{ padding: '2rem', maxWidth: '800px', margin: '0 auto' }}>
        <Card style={{ padding: '2rem', textAlign: 'center', backgroundColor: '#fee' }}>
          <h3 style={{ color: '#c00' }}>Failed to Load Agent</h3>
          <p>{error || 'Agent not found'}</p>
          <Button appearance="primary" onClick={() => navigate('/discover')} style={{ marginTop: '1rem' }}>
            Back to Discovery
          </Button>
        </Card>
      </div>
    )
  }

  return (
    <div style={{ padding: '2rem', maxWidth: '1200px', margin: '0 auto' }}>
      {/* Back Button */}
      <Button 
        appearance="subtle" 
        icon={<ArrowLeft20Regular />}
        onClick={() => navigate('/discover')}
        style={{ marginBottom: '1.5rem' }}
      >
        Back to Discovery
      </Button>

      {/* Agent Header */}
      <Card style={{ padding: '2rem', marginBottom: '2rem' }}>
        <div style={{ display: 'flex', gap: '2rem', alignItems: 'start', flexWrap: 'wrap' }}>
          {/* Avatar */}
          <div
            style={{
              width: '120px',
              height: '120px',
              borderRadius: '1.5rem',
              background: 'linear-gradient(135deg, #00f2fe, #667eea)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '3rem',
              fontWeight: 700,
              color: 'white'
            }}
          >
            {getInitials(agent.name)}
          </div>

          {/* Info */}
          <div style={{ flex: 1 }}>
            <div style={{ display: 'flex', gap: '1rem', alignItems: 'center', marginBottom: '0.5rem', flexWrap: 'wrap' }}>
              <h1 style={{ fontSize: '2rem', fontWeight: 700, margin: 0 }}>
                {agent.name}
              </h1>
              {getStatusBadge()}
            </div>

            <div style={{ display: 'flex', gap: '1.5rem', marginBottom: '1rem', flexWrap: 'wrap' }}>
              <span style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Briefcase20Regular />
                {agent.industry.charAt(0).toUpperCase() + agent.industry.slice(1)}
              </span>
              {/* Placeholder rating - TODO: Get from backend */}
              <span style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Star20Filled style={{ color: '#f59e0b' }} />
                4.8 (Coming soon)
              </span>
            </div>

            <p style={{ fontSize: '1.1rem', color: '#666', marginBottom: '1.5rem' }}>
              {agent.description || jobRole?.description || ''}
            </p>

            {/* CTA Buttons */}
            <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
              <Button 
                appearance="primary" 
                size="large"
                onClick={handleStartTrial}
                disabled={agent.status !== 'active'}
              >
                {agent.status === 'active' ? `Start ${trialDays}-Day Free Trial` : 'Currently Unavailable'}
              </Button>
              <div style={{ display: 'flex', alignItems: 'center', fontSize: '1.2rem', fontWeight: 600 }}>
                {monthlyPrice ? `₹${monthlyPrice.toLocaleString()}/month after trial` : 'Pricing coming soon'}
              </div>
            </div>
          </div>
        </div>
      </Card>

      {/* Job Role & Skills */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '2rem' }}>
        {/* Job Role */}
        {jobRole && (
          <Card style={{ padding: '1.5rem' }}>
            <h2 style={{ fontSize: '1.5rem', fontWeight: 700, marginBottom: '1rem' }}>
              Job Role
            </h2>
            <h3 style={{ fontSize: '1.2rem', fontWeight: 600, marginBottom: '0.5rem' }}>
              {jobRole.name}
            </h3>
            <Badge appearance="outline" style={{ marginBottom: '1rem' }}>
              {jobRole.seniority_level.charAt(0).toUpperCase() + jobRole.seniority_level.slice(1)} Level
            </Badge>
            <p style={{ color: '#666', lineHeight: 1.6 }}>
              {jobRole.description}
            </p>
          </Card>
        )}

        {/* Skills */}
        {skills.length > 0 && (
          <Card style={{ padding: '1.5rem' }}>
            <h2 style={{ fontSize: '1.5rem', fontWeight: 700, marginBottom: '1rem' }}>
              Required Skills ({skills.length})
            </h2>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {skills.map((skill) => (
                <div
                  key={skill.id}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.75rem',
                    padding: '0.75rem',
                    backgroundColor: '#f5f5f5',
                    borderRadius: '0.5rem'
                  }}
                >
                  <CheckmarkCircle20Filled style={{ color: '#10b981' }} />
                  <div>
                    <div style={{ fontWeight: 600 }}>{skill.name}</div>
                    <div style={{ fontSize: '0.85rem', color: '#666' }}>
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
      <Card style={{ padding: '2rem', marginTop: '2rem' }}>
        <h2 style={{ fontSize: '1.5rem', fontWeight: 700, marginBottom: '1rem' }}>
          What You Get with 7-Day Trial
        </h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '1.5rem' }}>
          <div>
            <h3 style={{ fontWeight: 600, marginBottom: '0.5rem' }}>✓ Full Access</h3>
            <p style={{ color: '#666' }}>Complete access to all agent capabilities</p>
          </div>
          <div>
            <h3 style={{ fontWeight: 600, marginBottom: '0.5rem' }}>✓ Keep Deliverables</h3>
            <p style={{ color: '#666' }}>Keep everything the agent creates, even if you cancel</p>
          </div>
          <div>
            <h3 style={{ fontWeight: 600, marginBottom: '0.5rem' }}>✓ No Credit Card</h3>
            <p style={{ color: '#666' }}>Try first, decide later. No payment info required</p>
          </div>
          <div>
            <h3 style={{ fontWeight: 600, marginBottom: '0.5rem' }}>✓ Cancel Anytime</h3>
            <p style={{ color: '#666' }}>Zero commitment. Cancel within 7 days, pay nothing</p>
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
