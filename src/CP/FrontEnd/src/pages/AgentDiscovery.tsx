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
import { Search20Regular } from '@fluentui/react-icons'
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
      const params: any = { q: searchQuery.trim() }
      if (industryFilter) params.industry = industryFilter
      if (statusFilter) params.status = statusFilter

      const results = await plantAPIService.listAgentsWithJobRoles(params)
      setAgents(results)
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
    <div className="discover-page">
      {/* Header */}
      <div className="discover-header">
        <h1 className="discover-title">
          Discover AI Agents
        </h1>
        <p className="discover-subtitle">
          Browse our marketplace of specialized AI agents. Try any agent free for 7 days.
        </p>
      </div>

      {/* Search & Filters */}
      <Card className="discover-filters">
        <div className="discover-filters-row">
          <div className="discover-search">
            <label className="discover-label">
              Search Agents
            </label>
            <Input
              placeholder="Search by name or description..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              contentBefore={<Search20Regular />}
              className="discover-control"
            />
          </div>

          <div className="discover-select discover-select--industry">
            <label className="discover-label">
              Industry
            </label>
            <Select
              value={industryFilter}
              onChange={(e, data) => setIndustryFilter(data.value as Industry | '')}
              className="discover-control"
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

          <div className="discover-select discover-select--status">
            <label className="discover-label">
              Status
            </label>
            <Select
              value={statusFilter}
              onChange={(e, data) => setStatusFilter(data.value as AgentStatus | '')}
              className="discover-control"
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
            className="discover-action"
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
              className="discover-action"
            >
              Clear Filters
            </Button>
          )}
        </div>
      </Card>

      {/* Results Count */}
      {!loading && (
        <div className="discover-count">
          Found {filteredAgents.length} agent{filteredAgents.length !== 1 ? 's' : ''}
          {industryFilter && ` in ${industryFilter}`}
          {statusFilter && ` (${statusFilter})`}
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="page-state page-state--loading">
          <Spinner size="large" label="Loading agents..." />
        </div>
      )}

      {/* Error State */}
      {error && !loading && (
        <Card className="page-state page-state--error">
          <h3 className="page-state-title page-state-title--error">Failed to Load Agents</h3>
          <p className="page-state-body">{error}</p>
          <Button appearance="primary" onClick={loadAgents} className="page-state-action">
            Retry
          </Button>
        </Card>
      )}

      {/* Empty State */}
      {!loading && !error && filteredAgents.length === 0 && (
        <Card className="page-state page-state--empty">
          <div className="page-state-icon" aria-hidden>
            🔍
          </div>
          <h3 className="page-state-title">No Agents Found</h3>
          <p className="page-state-body">
            {searchQuery || industryFilter || statusFilter
              ? 'Try adjusting your search or filters'
              : 'No agents available at the moment'}
          </p>
        </Card>
      )}

      {/* Agent Grid */}
      {!loading && !error && filteredAgents.length > 0 && (
        <div className="discover-grid">
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
