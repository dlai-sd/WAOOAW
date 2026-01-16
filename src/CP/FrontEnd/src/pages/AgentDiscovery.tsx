/**
 * Agent Discovery Page - Marketplace for browsing AI agents
 * Integrates with Plant API for real agent data
 */

import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { 
  Input, 
  Button, 
  Spinner, 
  Select,
  Card
} from '@fluentui/react-components'
import { Search20Regular, Filter20Regular } from '@fluentui/react-icons'
import AgentCard from '../components/AgentCard'
import { plantAPIService } from '../services/plant.service'
import type { Agent, Industry, AgentStatus } from '../types/plant.types'

export default function AgentDiscovery() {
  const navigate = useNavigate()
  const [agents, setAgents] = useState<Array<Agent & { job_role?: { name: string } }>>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [industryFilter, setIndustryFilter] = useState<Industry | ''>('')
  const [statusFilter, setStatusFilter] = useState<AgentStatus | ''>('')

  // Fetch agents on mount and when filters change
  useEffect(() => {
    loadAgents()
  }, [industryFilter, statusFilter])

  const loadAgents = async () => {
    setLoading(true)
    setError(null)
    
    try {
      const params: any = { limit: 50 }
      if (industryFilter) params.industry = industryFilter
      if (statusFilter) params.status = statusFilter

      // Fetch agents with job role details
      const data = await plantAPIService.listAgentsWithJobRoles(params)
      setAgents(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load agents')
      console.error('Failed to load agents:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      loadAgents()
      return
    }

    setLoading(true)
    try {
      const params: any = {}
      if (industryFilter) params.industry = industryFilter
      if (statusFilter) params.status = statusFilter

      const results = await plantAPIService.searchAgents(searchQuery, params)
      
      // Enrich with job roles
      const enriched = await Promise.all(
        results.map(async (agent) => {
          try {
            const jobRole = await plantAPIService.getJobRole(agent.job_role_id)
            return { ...agent, job_role: jobRole }
          } catch {
            return agent
          }
        })
      )
      
      setAgents(enriched)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Search failed')
    } finally {
      setLoading(false)
    }
  }

  const handleTryAgent = (agentId: string) => {
    // Navigate to agent detail page
    console.log('Try agent:', agentId)
    navigate(`/agent/${agentId}`)
  }

  const filteredAgents = agents

  return (
    <div style={{ padding: '2rem', maxWidth: '1400px', margin: '0 auto' }}>
      {/* Header */}
      <div style={{ marginBottom: '2rem' }}>
        <h1 style={{ fontSize: '2.5rem', fontWeight: 700, marginBottom: '0.5rem' }}>
          Discover AI Agents
        </h1>
        <p style={{ fontSize: '1.1rem', color: '#666' }}>
          Browse our marketplace of specialized AI agents. Try any agent free for 7 days.
        </p>
      </div>

      {/* Search & Filters */}
      <Card style={{ padding: '1.5rem', marginBottom: '2rem' }}>
        <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', alignItems: 'end' }}>
          <div style={{ flex: '1', minWidth: '300px' }}>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600 }}>
              Search Agents
            </label>
            <Input
              placeholder="Search by name or description..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
              contentBefore={<Search20Regular />}
              style={{ width: '100%' }}
            />
          </div>

          <div style={{ minWidth: '180px' }}>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600 }}>
              Industry
            </label>
            <Select
              value={industryFilter}
              onChange={(e, data) => setIndustryFilter(data.value as Industry | '')}
              style={{ width: '100%' }}
            >
              <option value="">All Industries</option>
              <option value="marketing">Marketing</option>
              <option value="education">Education</option>
              <option value="sales">Sales</option>
              <option value="healthcare">Healthcare</option>
              <option value="finance">Finance</option>
              <option value="general">General</option>
            </Select>
          </div>

          <div style={{ minWidth: '150px' }}>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600 }}>
              Status
            </label>
            <Select
              value={statusFilter}
              onChange={(e, data) => setStatusFilter(data.value as AgentStatus | '')}
              style={{ width: '100%' }}
            >
              <option value="">All Statuses</option>
              <option value="active">Available</option>
              <option value="inactive">Inactive</option>
            </Select>
          </div>

          <Button 
            appearance="primary" 
            icon={<Search20Regular />}
            onClick={handleSearch}
          >
            Search
          </Button>

          {(searchQuery || industryFilter || statusFilter) && (
            <Button 
              appearance="subtle"
              onClick={() => {
                setSearchQuery('')
                setIndustryFilter('')
                setStatusFilter('')
                loadAgents()
              }}
            >
              Clear Filters
            </Button>
          )}
        </div>
      </Card>

      {/* Results Count */}
      {!loading && (
        <div style={{ marginBottom: '1rem', color: '#666' }}>
          Found {filteredAgents.length} agent{filteredAgents.length !== 1 ? 's' : ''}
          {industryFilter && ` in ${industryFilter}`}
          {statusFilter && ` (${statusFilter})`}
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div style={{ textAlign: 'center', padding: '3rem' }}>
          <Spinner size="large" label="Loading agents..." />
        </div>
      )}

      {/* Error State */}
      {error && !loading && (
        <Card style={{ padding: '2rem', textAlign: 'center', backgroundColor: '#fee' }}>
          <h3 style={{ color: '#c00' }}>Failed to Load Agents</h3>
          <p>{error}</p>
          <Button appearance="primary" onClick={loadAgents} style={{ marginTop: '1rem' }}>
            Retry
          </Button>
        </Card>
      )}

      {/* Empty State */}
      {!loading && !error && filteredAgents.length === 0 && (
        <Card style={{ padding: '3rem', textAlign: 'center' }}>
          <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>🔍</div>
          <h3>No Agents Found</h3>
          <p style={{ color: '#666' }}>
            {searchQuery || industryFilter || statusFilter
              ? 'Try adjusting your search or filters'
              : 'No agents available at the moment'}
          </p>
        </Card>
      )}

      {/* Agent Grid */}
      {!loading && !error && filteredAgents.length > 0 && (
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(350px, 1fr))',
            gap: '1.5rem'
          }}
        >
          {filteredAgents.map((agent) => (
            <AgentCard 
              key={agent.id} 
              agent={agent} 
              onTryAgent={handleTryAgent}
            />
          ))}
        </div>
      )}
    </div>
  )
}
