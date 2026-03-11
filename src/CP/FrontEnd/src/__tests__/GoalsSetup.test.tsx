import { describe, it, expect, vi, beforeEach } from 'vitest'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import GoalsSetup from '../pages/authenticated/GoalsSetup'

const { listHiredAgentSkillsMock, saveGoalConfigMock } = vi.hoisted(() => ({
  listHiredAgentSkillsMock: vi.fn(async () => [
    {
      skill_id: 'skill-theme-discovery',
      name: 'theme_discovery',
      display_name: 'Theme Discovery',
      goal_schema: {
        fields: [
          { key: 'business_background', label: 'Business Background', type: 'text', required: true },
          { key: 'industry', label: 'Industry', type: 'text', required: true },
          { key: 'locality', label: 'Locality', type: 'text', required: true },
          { key: 'target_audience', label: 'Target Audience', type: 'text', required: true },
          { key: 'persona', label: 'Persona', type: 'text', required: true },
          { key: 'offer', label: 'Offer', type: 'text', required: true },
          { key: 'objective', label: 'Objective', type: 'text', required: true },
          { key: 'channel_intent', label: 'YouTube Intent', type: 'text', required: true },
          { key: 'posting_cadence', label: 'Posting Cadence', type: 'text', required: true },
          { key: 'tone', label: 'Tone', type: 'text', required: true },
          { key: 'success_metrics', label: 'Success Metrics', type: 'text', required: true },
        ],
      },
      goal_config: {},
    },
  ]),
  saveGoalConfigMock: vi.fn(async (_hiredInstanceId, _skillId, goalConfig) => ({
    skill_id: 'skill-theme-discovery',
    name: 'theme_discovery',
    display_name: 'Theme Discovery',
    goal_schema: { fields: [] },
    goal_config: goalConfig,
  })),
}))

vi.mock('../services/myAgentsSummary.service', () => ({
  getMyAgentsSummary: vi.fn(async () => ({
    instances: [
      {
        subscription_id: 'SUB-1',
        agent_id: 'AGT-MKT-DMA-001',
        hired_instance_id: 'HIRED-DMA-1',
        nickname: 'YouTube Growth Agent',
        duration: 'monthly',
        status: 'active',
        current_period_start: '2026-03-01T00:00:00Z',
        current_period_end: '2026-04-01T00:00:00Z',
        cancel_at_period_end: false,
      },
    ],
  })),
}))

vi.mock('../services/agentSkills.service', () => ({
  DIGITAL_MARKETING_AGENT_ID: 'AGT-MKT-DMA-001',
  isDigitalMarketingAgent: (agentId?: string | null, agentTypeId?: string | null) =>
    String(agentId || '').trim().toUpperCase() === 'AGT-MKT-DMA-001' ||
    String(agentTypeId || '').trim() === 'marketing.digital_marketing.v1',
  getThemeDiscoverySkill: (skills: Array<{ skill_id: string; name?: string; display_name?: string }>) =>
    skills.find((skill) => ['theme discovery', 'theme_discovery'].includes(String(skill.display_name || skill.name || '').trim().toLowerCase())) || null,
  listHiredAgentSkills: listHiredAgentSkillsMock,
  saveGoalConfig: saveGoalConfigMock,
}))

describe('GoalsSetup', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders the Theme Discovery workflow shell', async () => {
    const { container } = render(<GoalsSetup />)
    expect(container.firstChild).toBeTruthy()

    await waitFor(() => {
      expect(screen.getByText(/Build a brief the agent can actually use/i)).toBeInTheDocument()
      expect(screen.getByText(/Theme Discovery step 1 of 4/i)).toBeInTheDocument()
    })
  })

  it('completes and saves a Theme Discovery happy path', async () => {
    render(<GoalsSetup />)

    await waitFor(() => {
      expect(screen.getByText('Map the business context')).toBeInTheDocument()
    })

    fireEvent.change(screen.getByLabelText('Business Background *'), { target: { value: 'Dental clinic with two branches' } })
    fireEvent.change(screen.getByLabelText('Industry *'), { target: { value: 'Healthcare' } })
    fireEvent.change(screen.getByLabelText('Locality *'), { target: { value: 'Bengaluru' } })
    fireEvent.click(screen.getByRole('button', { name: 'Continue' }))

    await waitFor(() => {
      expect(screen.getByText('Define the audience and promise')).toBeInTheDocument()
    })

    fireEvent.change(screen.getByLabelText('Target Audience *'), { target: { value: 'Working parents' } })
    fireEvent.change(screen.getByLabelText('Persona *'), { target: { value: 'Care-seeking parent' } })
    fireEvent.change(screen.getByLabelText('Offer *'), { target: { value: 'Free first consultation' } })
    fireEvent.click(screen.getByRole('button', { name: 'Continue' }))

    await waitFor(() => {
      expect(screen.getByText('Shape the YouTube angle')).toBeInTheDocument()
    })

    fireEvent.change(screen.getByLabelText('Objective *'), { target: { value: 'Drive qualified appointment requests' } })
    fireEvent.change(screen.getByLabelText('YouTube Intent *'), { target: { value: 'Educational shorts and explainers' } })
    fireEvent.change(screen.getByLabelText('Posting Cadence *'), { target: { value: 'Three videos per week' } })
    fireEvent.click(screen.getByRole('button', { name: 'Continue' }))

    await waitFor(() => {
      expect(screen.getByText('Lock the voice and proof signal')).toBeInTheDocument()
    })

    fireEvent.change(screen.getByLabelText('Tone *'), { target: { value: 'Clear and reassuring' } })
    fireEvent.change(screen.getByLabelText('Success Metrics *'), { target: { value: 'Consult bookings and watch-through rate' } })
    fireEvent.click(screen.getByRole('button', { name: 'Save Theme Discovery brief' }))

    await waitFor(() => {
      expect(saveGoalConfigMock).toHaveBeenCalledWith(
        'HIRED-DMA-1',
        'skill-theme-discovery',
        expect.objectContaining({
          business_background: 'Dental clinic with two branches',
          objective: 'Drive qualified appointment requests',
          success_metrics: 'Consult bookings and watch-through rate',
        })
      )
    })

    await waitFor(() => {
      expect(screen.getByText(/Theme Discovery saved/i)).toBeInTheDocument()
      expect(screen.getByText('Dental clinic with two branches')).toBeInTheDocument()
    })
  })
})
