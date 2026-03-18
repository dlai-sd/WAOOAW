import { FluentProvider } from '@fluentui/react-components'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { describe, expect, it, vi, beforeEach } from 'vitest'

import { DigitalMarketingActivationWizard } from '../components/DigitalMarketingActivationWizard'
import { waooawLightTheme } from '../theme'

vi.mock('../services/digitalMarketingActivation.service', () => ({
  getDigitalMarketingActivationWorkspace: vi.fn(),
  patchDigitalMarketingActivationWorkspace: vi.fn(),
  generateDigitalMarketingThemePlan: vi.fn(),
  patchDigitalMarketingThemePlan: vi.fn(),
  getNextPendingPlatform: (selectedPlatforms: string[], platformSteps: Array<{ platform_key: string; complete: boolean }>) => {
    const completed = new Map(platformSteps.map((step) => [step.platform_key, step.complete]))
    return selectedPlatforms.find((platform) => !completed.get(platform)) || null
  },
}))

vi.mock('../services/platformConnections.service', () => ({
  listPlatformConnections: vi.fn().mockResolvedValue([]),
}))

const defaultWorkspace = {
  hired_instance_id: 'HAI-1',
  help_visible: false,
  activation_complete: false,
  induction: {
    nickname: 'Growth Copilot',
    theme: 'dark',
    primary_language: 'en',
    timezone: 'Asia/Kolkata',
    brand_name: 'WAOOAW',
    offerings_services: ['Activation'],
    location: 'Pune',
    target_audience: 'Founders',
    notes: '',
  },
  prepare_agent: {
    selected_platforms: [],
    platform_steps: [],
    all_selected_platforms_completed: false,
  },
  campaign_setup: {
    campaign_id: 'CAM-1',
    master_theme: '',
    derived_themes: [],
    schedule: {
      start_date: '',
      posts_per_week: 0,
      preferred_days: [],
      preferred_hours_utc: [],
    },
  },
  updated_at: '2026-03-18T09:00:00Z',
}

function renderWizard() {
  return render(
    <FluentProvider theme={waooawLightTheme}>
      <DigitalMarketingActivationWizard
        selectedInstance={{
          subscription_id: 'SUB-1',
          agent_id: 'AGT-MKT-DMA-001',
          agent_type_id: 'marketing.digital_marketing.v1',
          duration: 'monthly',
          status: 'active',
          current_period_start: '2026-03-01T00:00:00Z',
          current_period_end: '2026-04-01T00:00:00Z',
          cancel_at_period_end: false,
          hired_instance_id: 'HAI-1',
          nickname: 'Growth Copilot',
        }}
        readOnly={false}
      />
    </FluentProvider>
  )
}

describe('MyAgents Digital Marketing wizard', () => {
  beforeEach(async () => {
    vi.clearAllMocks()
    const serviceModule = await import('../services/digitalMarketingActivation.service')
    vi.mocked(serviceModule.getDigitalMarketingActivationWorkspace).mockResolvedValue(structuredClone(defaultWorkspace) as any)
    vi.mocked(serviceModule.patchDigitalMarketingActivationWorkspace).mockImplementation(async (_id, patch: any) => ({
      ...structuredClone(defaultWorkspace),
      ...patch,
      induction: { ...structuredClone(defaultWorkspace).induction, ...(patch.induction || {}) },
      prepare_agent: {
        ...structuredClone(defaultWorkspace).prepare_agent,
        ...(patch.prepare_agent || {}),
        all_selected_platforms_completed: Boolean(
          (patch.prepare_agent?.platform_steps || structuredClone(defaultWorkspace).prepare_agent.platform_steps).length
        ) && (patch.prepare_agent?.platform_steps || structuredClone(defaultWorkspace).prepare_agent.platform_steps).every((step: any) => step.complete),
      },
      campaign_setup: {
        ...structuredClone(defaultWorkspace).campaign_setup,
        ...(patch.campaign_setup || {}),
      },
    }) as any)
    vi.mocked(serviceModule.generateDigitalMarketingThemePlan).mockResolvedValue({
      campaign_id: 'CAM-1',
      master_theme: 'Trust-first growth',
      derived_themes: [
        { title: 'Proof', description: 'Show results', frequency: 'weekly' },
        { title: 'Education', description: 'Teach the market', frequency: 'weekly' },
      ],
      workspace: {
        ...structuredClone(defaultWorkspace),
        campaign_setup: {
          ...structuredClone(defaultWorkspace).campaign_setup,
          master_theme: 'Trust-first growth',
          derived_themes: [
            { title: 'Proof', description: 'Show results', frequency: 'weekly' },
            { title: 'Education', description: 'Teach the market', frequency: 'weekly' },
          ],
        },
      },
    } as any)
    vi.mocked(serviceModule.patchDigitalMarketingThemePlan).mockImplementation(async (_id, patch: any) => ({
      campaign_id: 'CAM-1',
      master_theme: patch.master_theme,
      derived_themes: patch.derived_themes || [],
      workspace: {
        ...structuredClone(defaultWorkspace),
        campaign_setup: {
          ...structuredClone(defaultWorkspace).campaign_setup,
          master_theme: patch.master_theme,
          derived_themes: patch.derived_themes || [],
          schedule: patch.schedule || structuredClone(defaultWorkspace).campaign_setup.schedule,
        },
      },
    }) as any)
  })

  it('toggles both help panels on and off', async () => {
    renderWizard()

    fireEvent.click(await screen.findByRole('button', { name: 'Show Help' }))

    await waitFor(() => {
      expect(screen.getByTestId('dma-help-panel-primary')).toBeInTheDocument()
      expect(screen.getByTestId('dma-help-panel-secondary')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByRole('button', { name: 'Hide Help' }))

    await waitFor(() => {
      expect(screen.queryByTestId('dma-help-panel-primary')).not.toBeInTheDocument()
      expect(screen.queryByTestId('dma-help-panel-secondary')).not.toBeInTheDocument()
    })
  })

  it('hydrates saved induction field values from the workspace API', async () => {
    renderWizard()

    expect(await screen.findByDisplayValue('Growth Copilot')).toBeInTheDocument()
    expect(screen.getByDisplayValue('WAOOAW')).toBeInTheDocument()
    expect(screen.getByDisplayValue('Pune')).toBeInTheDocument()
  })

  it('renders the exact milestone header labels', async () => {
    renderWizard()

    expect(await screen.findByText('Induct Agent')).toBeInTheDocument()
    expect(screen.getByText('Prepare Agent')).toBeInTheDocument()
    expect(screen.getByText('Master Theme')).toBeInTheDocument()
    expect(screen.getByText('Confirm Schedule')).toBeInTheDocument()
  })

  it('renders only the selected platform steps and advances to the next incomplete one', async () => {
    const serviceModule = await import('../services/digitalMarketingActivation.service')
    vi.mocked(serviceModule.getDigitalMarketingActivationWorkspace).mockResolvedValueOnce({
      ...structuredClone(defaultWorkspace),
      prepare_agent: {
        selected_platforms: ['youtube', 'instagram'],
        platform_steps: [
          { platform_key: 'youtube', complete: false, status: 'pending' },
          { platform_key: 'instagram', complete: false, status: 'pending' },
        ],
        all_selected_platforms_completed: false,
      },
    } as any)

    renderWizard()
    fireEvent.click(await screen.findByText('Prepare Agent'))

    expect(await screen.findByText('youtube')).toBeInTheDocument()
    expect(screen.getByText('instagram')).toBeInTheDocument()

    fireEvent.click(screen.getAllByRole('button', { name: 'Mark prepared' })[0])

    await waitFor(() => {
      expect(screen.getByText('This is the next platform to prepare.')).toBeInTheDocument()
    })
  })

  it('generates and then saves the master theme plan', async () => {
    renderWizard()
    fireEvent.click(await screen.findByText('Master Theme'))
    fireEvent.click(screen.getByRole('button', { name: 'Generate theme plan' }))

    await waitFor(() => {
      expect(screen.getByDisplayValue('Trust-first growth')).toBeInTheDocument()
      expect(screen.getByText('Proof')).toBeInTheDocument()
      expect(screen.getByText('Education')).toBeInTheDocument()
    })

    fireEvent.change(screen.getByLabelText('Master theme'), { target: { value: 'Trust-first growth updated' } })
    fireEvent.click(screen.getByRole('button', { name: 'Save theme plan' }))

    await waitFor(() => {
      expect(screen.getByDisplayValue('Trust-first growth updated')).toBeInTheDocument()
    })
  })

  it('keeps finish disabled until schedule and prior setup are complete, then enables it', async () => {
    const serviceModule = await import('../services/digitalMarketingActivation.service')
    vi.mocked(serviceModule.getDigitalMarketingActivationWorkspace).mockResolvedValueOnce({
      ...structuredClone(defaultWorkspace),
      campaign_setup: {
        ...structuredClone(defaultWorkspace).campaign_setup,
        master_theme: 'Trust-first growth',
      },
      prepare_agent: {
        ...structuredClone(defaultWorkspace).prepare_agent,
        platform_steps: [
          { platform_key: 'youtube', complete: true, status: 'complete' },
          { platform_key: 'instagram', complete: true, status: 'complete' },
        ],
        all_selected_platforms_completed: true,
      },
    } as any)

    renderWizard()
    fireEvent.click(await screen.findByText('Confirm Schedule'))

    const finishButton = await screen.findByRole('button', { name: 'Finish activation' })
    expect(finishButton).toBeDisabled()

    fireEvent.change(screen.getByLabelText('Start date'), { target: { value: '2026-03-22' } })
    fireEvent.change(screen.getByLabelText('Posts per week'), { target: { value: '3' } })

    await waitFor(() => {
      expect(finishButton).not.toBeDisabled()
    })
  })
})
