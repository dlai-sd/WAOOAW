/**
 * Trial Dashboard - Manage active and past trials
 * Shows trial countdown, deliverables, and conversion options
 */

import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Button,
  Card,
  Badge,
  Spinner,
  Tab,
  TabList
} from '@fluentui/react-components'
import {
  Calendar20Regular,
  Document20Regular,
  CheckmarkCircle20Filled,
  Warning20Filled
} from '@fluentui/react-icons'
import type { Agent } from '../types/plant.types'

interface Trial {
  id: string
  agent_id: string
  agent: Agent & { job_role?: { name: string } }
  customer_name: string
  customer_email: string
  company: string
  start_date: string
  end_date: string
  status: 'active' | 'converted' | 'cancelled' | 'expired'
  deliverables_count: number
  days_remaining: number
}

export default function TrialDashboard() {
  const navigate = useNavigate()
  const [trials, setTrials] = useState<Trial[]>([])
  const [activeTab, setActiveTab] = useState<'active' | 'history'>('active')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadTrials()
  }, [])

  const loadTrials = async () => {
    setLoading(true)
    setError(null)

    try {
      // TODO: Call backend API to fetch trials
      // const response = await fetch('/api/v1/trials')
      // if (!response.ok) throw new Error('Failed to load trials')
      // const data = await response.json()
      // setTrials(data)

      // Mock data for now
      await new Promise(resolve => setTimeout(resolve, 1000))
      
      const mockTrials: Trial[] = [
        {
          id: '1',
          agent_id: 'agent-1',
          agent: {
            id: 'agent-1',
            name: 'Marketing Maven',
            description: 'Expert in content marketing and SEO',
            industry: 'marketing',
            job_role_id: 'role-1',
            job_role: { name: 'Content Marketing Specialist' },
            status: 'active',
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString()
          },
          customer_name: 'John Doe',
          customer_email: 'john@example.com',
          company: 'Example Corp',
          start_date: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
          end_date: new Date(Date.now() + 5 * 24 * 60 * 60 * 1000).toISOString(),
          status: 'active',
          deliverables_count: 8,
          days_remaining: 5
        }
      ]

      setTrials(mockTrials)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load trials')
      console.error('Failed to load trials:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleKeepAgent = async (trialId: string) => {
    // TODO: Call backend API to convert trial to paid subscription
    alert('Converting to paid subscription!\n\nPayment integration coming soon...')
  }

  const handleCancelTrial = async (trialId: string) => {
    if (!confirm('Are you sure you want to cancel this trial? You will keep all deliverables.')) {
      return
    }

    try {
      // TODO: Call backend API to cancel trial
      alert('Trial cancelled. You can still access all deliverables.')
      loadTrials()
    } catch (err) {
      alert('Failed to cancel trial. Please try again.')
    }
  }

  const handleViewAgent = (agentId: string) => {
    navigate(`/agent/${agentId}`)
  }

  const getStatusBadge = (status: Trial['status']) => {
    switch (status) {
      case 'active':
        return <Badge appearance="filled" color="success">Active Trial</Badge>
      case 'converted':
        return <Badge appearance="filled" color="brand">Subscribed</Badge>
      case 'cancelled':
        return <Badge appearance="ghost">Cancelled</Badge>
      case 'expired':
        return <Badge appearance="filled" color="warning">Expired</Badge>
      default:
        return null
    }
  }

  const getDaysRemainingBadge = (daysRemaining: number) => {
    if (daysRemaining <= 0) {
      return (
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#ef4444' }}>
          <Warning20Filled />
          <span style={{ fontWeight: 600 }}>Trial Ended</span>
        </div>
      )
    } else if (daysRemaining <= 2) {
      return (
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#f59e0b' }}>
          <Warning20Filled />
          <span style={{ fontWeight: 600 }}>{daysRemaining} day{daysRemaining !== 1 ? 's' : ''} left</span>
        </div>
      )
    } else {
      return (
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#10b981' }}>
          <CheckmarkCircle20Filled />
          <span style={{ fontWeight: 600 }}>{daysRemaining} days left</span>
        </div>
      )
    }
  }

  const activeTrials = trials.filter(t => t.status === 'active')
  const historyTrials = trials.filter(t => t.status !== 'active')

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '3rem' }}>
        <Spinner size="large" label="Loading trials..." />
      </div>
    )
  }

  if (error) {
    return (
      <div style={{ padding: '2rem', maxWidth: '800px', margin: '0 auto' }}>
        <Card style={{ padding: '2rem', textAlign: 'center', backgroundColor: '#fee' }}>
          <h3 style={{ color: '#c00' }}>Failed to Load Trials</h3>
          <p>{error}</p>
          <Button appearance="primary" onClick={loadTrials} style={{ marginTop: '1rem' }}>
            Retry
          </Button>
        </Card>
      </div>
    )
  }

  const currentTrials = activeTab === 'active' ? activeTrials : historyTrials

  return (
    <div style={{ padding: '2rem', maxWidth: '1400px', margin: '0 auto' }}>
      {/* Header */}
      <div style={{ marginBottom: '2rem' }}>
        <h1 style={{ fontSize: '2.5rem', fontWeight: 700, marginBottom: '0.5rem' }}>
          Trial Dashboard
        </h1>
        <p style={{ fontSize: '1.1rem', color: '#666' }}>
          Manage your AI agent trials and subscriptions
        </p>
      </div>

      {/* Tabs */}
      <TabList
        selectedValue={activeTab}
        onTabSelect={(_, data) => setActiveTab(data.value as 'active' | 'history')}
        style={{ marginBottom: '2rem' }}
      >
        <Tab value="active">
          Active Trials ({activeTrials.length})
        </Tab>
        <Tab value="history">
          History ({historyTrials.length})
        </Tab>
      </TabList>

      {/* Empty State */}
      {currentTrials.length === 0 && (
        <Card style={{ padding: '3rem', textAlign: 'center' }}>
          <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>
            {activeTab === 'active' ? '🎯' : '📋'}
          </div>
          <h3 style={{ marginBottom: '0.5rem' }}>
            {activeTab === 'active' ? 'No Active Trials' : 'No Trial History'}
          </h3>
          <p style={{ color: '#666', marginBottom: '1.5rem' }}>
            {activeTab === 'active' 
              ? 'Start a 7-day trial with an AI agent to get started'
              : 'Your completed trials will appear here'
            }
          </p>
          {activeTab === 'active' && (
            <Button appearance="primary" onClick={() => navigate('/discover')}>
              Discover Agents
            </Button>
          )}
        </Card>
      )}

      {/* Trial Cards */}
      <div style={{ display: 'grid', gap: '1.5rem' }}>
        {currentTrials.map((trial) => (
          <Card key={trial.id} style={{ padding: '1.5rem' }}>
            <div style={{ display: 'flex', gap: '1.5rem', alignItems: 'start', flexWrap: 'wrap' }}>
              {/* Agent Avatar */}
              <div
                style={{
                  width: '80px',
                  height: '80px',
                  borderRadius: '1rem',
                  background: 'linear-gradient(135deg, #00f2fe, #667eea)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '2rem',
                  fontWeight: 700,
                  color: 'white',
                  flexShrink: 0
                }}
              >
                {trial.agent.name.split(' ').map(w => w[0]).join('').substring(0, 2).toUpperCase()}
              </div>

              {/* Info */}
              <div style={{ flex: 1, minWidth: '300px' }}>
                <div style={{ display: 'flex', gap: '1rem', alignItems: 'center', marginBottom: '0.5rem', flexWrap: 'wrap' }}>
                  <h3 style={{ fontSize: '1.5rem', fontWeight: 600, margin: 0 }}>
                    {trial.agent.name}
                  </h3>
                  {getStatusBadge(trial.status)}
                </div>

                <p style={{ color: '#666', marginBottom: '1rem' }}>
                  {trial.agent.job_role?.name || 'AI Agent'} · {trial.agent.industry.charAt(0).toUpperCase() + trial.agent.industry.slice(1)}
                </p>

                <div style={{ display: 'flex', gap: '2rem', flexWrap: 'wrap' }}>
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#666', marginBottom: '0.25rem' }}>
                      <Calendar20Regular />
                      <span style={{ fontSize: '0.9rem' }}>Started</span>
                    </div>
                    <div style={{ fontWeight: 600 }}>
                      {new Date(trial.start_date).toLocaleDateString()}
                    </div>
                  </div>

                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#666', marginBottom: '0.25rem' }}>
                      <Document20Regular />
                      <span style={{ fontSize: '0.9rem' }}>Deliverables</span>
                    </div>
                    <div style={{ fontWeight: 600 }}>
                      {trial.deliverables_count} items
                    </div>
                  </div>

                  {trial.status === 'active' && (
                    <div>
                      <div style={{ fontSize: '0.9rem', color: '#666', marginBottom: '0.25rem' }}>
                        Time Remaining
                      </div>
                      <div>
                        {getDaysRemainingBadge(trial.days_remaining)}
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* Actions */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', minWidth: '180px' }}>
                {trial.status === 'active' && (
                  <>
                    <Button 
                      appearance="primary"
                      onClick={() => handleKeepAgent(trial.id)}
                    >
                      Keep Agent (₹12k/mo)
                    </Button>
                    <Button 
                      appearance="subtle"
                      onClick={() => handleViewAgent(trial.agent_id)}
                    >
                      View Agent
                    </Button>
                    <Button 
                      appearance="subtle"
                      onClick={() => handleCancelTrial(trial.id)}
                    >
                      Cancel Trial
                    </Button>
                  </>
                )}

                {trial.status === 'converted' && (
                  <Button appearance="subtle" onClick={() => handleViewAgent(trial.agent_id)}>
                    Manage Subscription
                  </Button>
                )}

                {(trial.status === 'cancelled' || trial.status === 'expired') && (
                  <Button appearance="subtle" onClick={() => handleViewAgent(trial.agent_id)}>
                    View Agent
                  </Button>
                )}
              </div>
            </div>
          </Card>
        ))}
      </div>

      {/* Info Card */}
      {activeTrials.length > 0 && activeTab === 'active' && (
        <Card style={{ padding: '1.5rem', marginTop: '2rem', backgroundColor: '#f0f9ff' }}>
          <h3 style={{ fontSize: '1.1rem', fontWeight: 600, marginBottom: '0.5rem' }}>
            💡 Trial Tips
          </h3>
          <ul style={{ margin: 0, paddingLeft: '1.5rem', color: '#666' }}>
            <li>Keep all deliverables even if you cancel</li>
            <li>Convert to paid before trial ends to avoid interruption</li>
            <li>Cancel anytime - no questions asked</li>
            <li>Access deliverables from your dashboard 24/7</li>
          </ul>
        </Card>
      )}
    </div>
  )
}
