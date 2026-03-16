import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import AgentDetail from '../pages/AgentDetail'
import { PlantAPIError, type Agent, type CatalogAgent, type JobRole, type Skill } from '../types/plant.types'

const plantServiceMocks = vi.hoisted(() => ({
  getAgentWithJobRole: vi.fn(),
  getCatalogAgent: vi.fn(),
  getJobRoleSkills: vi.fn(),
}))

vi.mock('../services/plant.service', () => ({
  plantAPIService: {
    getAgentWithJobRole: plantServiceMocks.getAgentWithJobRole,
    getCatalogAgent: plantServiceMocks.getCatalogAgent,
    getJobRoleSkills: plantServiceMocks.getJobRoleSkills,
  }
}))

vi.mock('../components/BookingModal', () => ({
  default: ({ agent, isOpen }: { agent: Agent; isOpen: boolean }) => (
    isOpen ? <div data-testid="booking-modal">{agent.id}::{agent.name}</div> : null
  )
}))

function renderAgentDetail(initialEntry: string) {
  return render(
    <MemoryRouter initialEntries={[initialEntry]}>
      <Routes>
        <Route path="/agent/:agentId" element={<AgentDetail />} />
      </Routes>
    </MemoryRouter>
  )
}

describe('AgentDetail', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('falls back to catalog agents after UUID validation errors', async () => {
    const catalogAgent: CatalogAgent = {
      release_id: 'release_1',
      id: 'AGT-MKT-DMA-001',
      public_name: 'Digital Marketing Agent',
      short_description: 'Launches and optimizes acquisition campaigns.',
      industry_name: 'marketing',
      job_role_label: 'Demand Generation Specialist',
      monthly_price_inr: 12000,
      trial_days: 7,
      allowed_durations: ['monthly'],
      supported_channels: ['youtube'],
      approval_mode: 'instant',
      agent_type_id: 'marketing.digital_marketing.v1',
      external_catalog_version: '2026.03',
      lifecycle_state: 'live_on_cp',
      approved_for_new_hire: true,
    }

    plantServiceMocks.getAgentWithJobRole.mockRejectedValueOnce(new PlantAPIError({
      type: 'about:blank',
      title: 'Request Validation Error',
      status: 422,
      detail: 'agent_id must be a valid UUID'
    }))
    plantServiceMocks.getCatalogAgent.mockResolvedValueOnce(catalogAgent)

    renderAgentDetail('/agent/AGT-MKT-DMA-001')

    expect(await screen.findByRole('heading', { name: 'Digital Marketing Agent' })).toBeInTheDocument()
    expect(screen.getByText('Demand Generation Specialist')).toBeInTheDocument()
    expect(screen.getByText(/₹12,000\/month after trial/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /start 7-day free trial/i })).toBeEnabled()
    expect(plantServiceMocks.getJobRoleSkills).not.toHaveBeenCalled()

    fireEvent.click(screen.getByRole('button', { name: /start 7-day free trial/i }))

    expect(await screen.findByTestId('booking-modal')).toHaveTextContent('AGT-MKT-DMA-001::Digital Marketing Agent')
  })

  it('keeps the UUID agent flow and loads skills', async () => {
    const jobRole: JobRole = {
      id: 'job-role-1',
      name: 'Growth Marketer',
      description: 'Owns campaign planning and execution.',
      required_skills: ['skill-1'],
      seniority_level: 'senior',
      entity_type: 'job_role',
      status: 'certified',
      created_at: '2026-01-01T00:00:00Z',
    }

    const agent: Agent & { job_role: JobRole } = {
      id: '0f6d8ed4-0fd1-4c71-b6fc-334ba184e50b',
      name: 'Runtime Agent',
      description: 'Handles active customer work.',
      job_role_id: 'job-role-1',
      industry: 'marketing',
      entity_type: 'agent',
      status: 'active',
      created_at: '2026-01-01T00:00:00Z',
      price: 15000,
      trial_days: 7,
      allowed_durations: ['monthly'],
      job_role: jobRole,
    }

    const skills: Skill[] = [
      {
        id: 'skill-1',
        name: 'Paid Social',
        description: 'Manages paid social campaigns.',
        category: 'technical',
        entity_type: 'skill',
        status: 'certified',
        created_at: '2026-01-01T00:00:00Z',
      }
    ]

    plantServiceMocks.getAgentWithJobRole.mockResolvedValueOnce(agent)
    plantServiceMocks.getJobRoleSkills.mockResolvedValueOnce(skills)

    renderAgentDetail('/agent/0f6d8ed4-0fd1-4c71-b6fc-334ba184e50b')

    expect(await screen.findByRole('heading', { name: 'Runtime Agent' })).toBeInTheDocument()
    expect(screen.getByText('Growth Marketer')).toBeInTheDocument()
    expect(screen.getByText('Paid Social')).toBeInTheDocument()

    await waitFor(() => {
      expect(plantServiceMocks.getCatalogAgent).not.toHaveBeenCalled()
      expect(plantServiceMocks.getJobRoleSkills).toHaveBeenCalledWith('job-role-1')
    })
  })
})