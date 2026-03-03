// CP-SKILLS-2 regression: SkillsPanel component tests
// Covers: loading state, error state, empty state, skill list render,
// GoalConfigForm save success, GoalConfigForm save error.

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { SkillsPanel } from '../components/SkillsPanel'

// ── Service mocks ─────────────────────────────────────────────────────────────

vi.mock('../services/agentSkills.service', () => ({
  listHiredAgentSkills: vi.fn(),
  saveGoalConfig: vi.fn(),
}))

vi.mock('../services/platformConnections.service', () => ({
  listPlatformConnections: vi.fn(async () => []),
  createPlatformConnection: vi.fn(async () => ({})),
  deletePlatformConnection: vi.fn(async () => ({})),
}))

// ── Helpers ───────────────────────────────────────────────────────────────────

async function importSkillsSvc() {
  return import('../services/agentSkills.service')
}

const MOCK_SKILL_NO_SCHEMA = {
  skill_id: 'skill-1',
  name: 'monitoring',
  display_name: 'Performance Monitoring',
  description: 'Monitors agent KPIs',
}

const MOCK_SKILL_WITH_SCHEMA = {
  skill_id: 'skill-2',
  name: 'content_posting',
  display_name: 'Content Posting',
  goal_schema: {
    fields: [
      {
        key: 'frequency',
        label: 'Posting Frequency',
        type: 'enum' as const,
        required: true,
        options: ['daily', 'weekly', 'monthly'],
      },
      {
        key: 'tone',
        label: 'Tone',
        type: 'text' as const,
        required: false,
      },
    ],
  },
  goal_config: { frequency: 'weekly', tone: 'professional' },
}

// ── Tests ─────────────────────────────────────────────────────────────────────

describe('SkillsPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('shows loading indicator while fetching skills', async () => {
    const svc = await importSkillsSvc()

    // Never resolves during this test
    vi.mocked(svc.listHiredAgentSkills).mockReturnValue(new Promise(() => {}))

    render(<SkillsPanel hiredInstanceId="hire-abc" readOnly={false} />)

    expect(screen.getByText(/Loading skills/i)).toBeTruthy()
  })

  it('shows error message when skill fetch fails', async () => {
    const svc = await importSkillsSvc()
    vi.mocked(svc.listHiredAgentSkills).mockRejectedValue(
      new Error('Gateway timeout')
    )

    render(<SkillsPanel hiredInstanceId="hire-abc" readOnly={false} />)

    await waitFor(() => {
      expect(screen.getByText(/Failed to load skills/i)).toBeTruthy()
    })
  })

  it('shows empty state when no skills are configured', async () => {
    const svc = await importSkillsSvc()
    vi.mocked(svc.listHiredAgentSkills).mockResolvedValue([])

    render(<SkillsPanel hiredInstanceId="hire-abc" readOnly={false} />)

    await waitFor(() => {
      expect(screen.getByText(/No skills configured/i)).toBeTruthy()
    })
  })

  it('shows placeholder when hiredInstanceId is empty', () => {
    render(<SkillsPanel hiredInstanceId="" readOnly={false} />)
    expect(screen.getByText(/No hired agent selected/i)).toBeTruthy()
  })

  it('renders skill display names after successful fetch', async () => {
    const svc = await importSkillsSvc()
    vi.mocked(svc.listHiredAgentSkills).mockResolvedValue([
      MOCK_SKILL_NO_SCHEMA,
      MOCK_SKILL_WITH_SCHEMA,
    ])

    render(<SkillsPanel hiredInstanceId="hire-abc" readOnly={false} />)

    await waitFor(() => {
      expect(screen.getByText('Performance Monitoring')).toBeTruthy()
      expect(screen.getByText('Content Posting')).toBeTruthy()
    })
  })

  it('saves goal config and shows success feedback', async () => {
    const svc = await importSkillsSvc()
    vi.mocked(svc.listHiredAgentSkills).mockResolvedValue([MOCK_SKILL_WITH_SCHEMA])
    vi.mocked(svc.saveGoalConfig).mockResolvedValue({
      ...MOCK_SKILL_WITH_SCHEMA,
      goal_config: { frequency: 'daily', tone: 'professional' },
    })

    render(<SkillsPanel hiredInstanceId="hire-abc" readOnly={false} />)

    // Wait for skill to load and expand button to appear
    await waitFor(() => {
      expect(screen.getByText('Content Posting')).toBeTruthy()
    })

    // Click the skill header to expand the GoalConfigForm
    fireEvent.click(screen.getByText('Content Posting'))

    // Save button appears when form is expanded
    await waitFor(() => {
      expect(screen.getByText(/Save/i)).toBeTruthy()
    })

    fireEvent.click(screen.getByText(/Save/i))

    await waitFor(() => {
      expect(svc.saveGoalConfig).toHaveBeenCalledWith(
        'hire-abc',
        'skill-2',
        expect.any(Object)
      )
    })

    await waitFor(() => {
      expect(screen.getByText(/Saved/i)).toBeTruthy()
    })
  })

  it('shows save error feedback when saveGoalConfig rejects', async () => {
    const svc = await importSkillsSvc()
    vi.mocked(svc.listHiredAgentSkills).mockResolvedValue([MOCK_SKILL_WITH_SCHEMA])
    vi.mocked(svc.saveGoalConfig).mockRejectedValue(new Error('Plant 503'))

    render(<SkillsPanel hiredInstanceId="hire-abc" readOnly={false} />)

    await waitFor(() => {
      expect(screen.getByText('Content Posting')).toBeTruthy()
    })

    fireEvent.click(screen.getByText('Content Posting'))

    await waitFor(() => {
      expect(screen.getByText(/Save/i)).toBeTruthy()
    })

    fireEvent.click(screen.getByText(/Save/i))

    await waitFor(() => {
      expect(screen.getByText(/Plant 503|Failed to save|error/i)).toBeTruthy()
    })
  })

  it('does not render save button in readOnly mode', async () => {
    const svc = await importSkillsSvc()
    vi.mocked(svc.listHiredAgentSkills).mockResolvedValue([MOCK_SKILL_WITH_SCHEMA])

    render(<SkillsPanel hiredInstanceId="hire-abc" readOnly={true} />)

    await waitFor(() => {
      expect(screen.getByText('Content Posting')).toBeTruthy()
    })

    fireEvent.click(screen.getByText('Content Posting'))

    await waitFor(() => {
      expect(screen.queryByText(/^Save$/)).toBeNull()
    })
  })
})
