import { FluentProvider } from '@fluentui/react-components'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { describe, expect, it, vi, beforeEach } from 'vitest'
import { MemoryRouter } from 'react-router-dom'

import { DigitalMarketingActivationWizard } from '../components/DigitalMarketingActivationWizard'
import { waooawLightTheme } from '../theme'

vi.mock('../services/digitalMarketingActivation.service', () => ({
  getDigitalMarketingActivationWorkspace: vi.fn(),
  upsertDigitalMarketingActivationWorkspace: vi.fn(),
  generateDigitalMarketingThemePlan: vi.fn(),
  patchDigitalMarketingThemePlan: vi.fn(),
  buildMarketingPlatformBindings: vi.fn(() => ({})),
  getActivationMilestoneCount: vi.fn(() => 2),
  getSelectedMarketingPlatforms: vi.fn((workspace: any) => workspace?.platforms_enabled || []),
  getNextPendingPlatform: (selectedPlatforms: string[], platformSteps: Array<{ platform_key: string; complete: boolean }>) => {
    const completed = new Map(platformSteps.map((step) => [step.platform_key, step.complete]))
    return selectedPlatforms.find((platform) => !completed.get(platform)) || null
  },
}))

vi.mock('../services/hiredAgents.service', () => ({
  getHiredAgentBySubscription: vi.fn().mockResolvedValue({
    subscription_id: 'SUB-1',
    hired_instance_id: 'HAI-1',
    agent_id: 'AGT-MKT-DMA-001',
    agent_type_id: 'marketing.digital_marketing.v1',
    nickname: 'Growth Copilot',
    theme: 'dark',
    config: {},
    configured: false,
    goals_completed: false,
  }),
  upsertHiredAgentDraft: vi.fn(),
}))

vi.mock('../components/PlatformConnectionsPanel', () => ({
  PlatformConnectionsPanel: () => <div>Platform connections panel</div>,
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
    <MemoryRouter>
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
    </MemoryRouter>
  )
}

describe('MyAgents Digital Marketing wizard', () => {
  beforeEach(async () => {
    vi.clearAllMocks()
    const serviceModule = await import('../services/digitalMarketingActivation.service')
    vi.mocked(serviceModule.getDigitalMarketingActivationWorkspace).mockResolvedValue({
      hired_instance_id: 'HAI-1',
      customer_id: 'CUST-1',
      agent_type_id: 'marketing.digital_marketing.v1',
      workspace: {
        brand_name: 'WAOOAW',
        location: 'Pune',
        primary_language: 'en',
        timezone: 'Asia/Kolkata',
        business_context: '',
        offerings_services: ['Activation'],
        platforms_enabled: ['youtube'],
        campaign_setup: structuredClone(defaultWorkspace).campaign_setup,
      },
      readiness: {
        brief_complete: true,
        youtube_selected: true,
        youtube_connection_ready: true,
        configured: true,
        can_finalize: false,
        missing_requirements: [],
      },
      updated_at: '2026-03-18T09:00:00Z',
    } as any)
    vi.mocked(serviceModule.upsertDigitalMarketingActivationWorkspace).mockResolvedValue({
      hired_instance_id: 'HAI-1',
      customer_id: 'CUST-1',
      agent_type_id: 'marketing.digital_marketing.v1',
      workspace: {
        brand_name: 'WAOOAW',
        location: 'Pune',
        primary_language: 'en',
        timezone: 'Asia/Kolkata',
        business_context: '',
        offerings_services: ['Activation'],
        platforms_enabled: ['youtube'],
      },
      readiness: {
        brief_complete: true,
        youtube_selected: true,
        youtube_connection_ready: true,
        configured: true,
        can_finalize: false,
        missing_requirements: [],
      },
      updated_at: '2026-03-18T09:00:00Z',
    } as any)
    vi.mocked(serviceModule.generateDigitalMarketingThemePlan).mockResolvedValue({
      campaign_id: 'CAM-1',
      master_theme: 'Trust-first growth',
      derived_themes: [
        { title: 'Proof', description: 'Show results', frequency: 'weekly' },
        { title: 'Education', description: 'Teach the market', frequency: 'weekly' },
      ],
      workspace: {
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
        campaign_setup: {
          ...structuredClone(defaultWorkspace).campaign_setup,
          master_theme: patch.master_theme,
          derived_themes: patch.derived_themes || [],
          schedule: patch.campaign_setup?.schedule || structuredClone(defaultWorkspace).campaign_setup.schedule,
        },
      },
    }) as any)
  })

  it('generates and renders the master theme plus derived themes', async () => {
    renderWizard()

    fireEvent.click(await screen.findByRole('button', { name: 'Master Theme' }))
    fireEvent.click(screen.getByRole('button', { name: 'Generate theme plan' }))

    await waitFor(() => {
      expect(screen.getByDisplayValue('Trust-first growth')).toBeInTheDocument()
      expect(screen.getByDisplayValue('Proof')).toBeInTheDocument()
      expect(screen.getByDisplayValue('Education')).toBeInTheDocument()
    })
  })

  it('reloads the edited theme back from the backend after refresh', async () => {
    const serviceModule = await import('../services/digitalMarketingActivation.service')
    vi.mocked(serviceModule.getDigitalMarketingActivationWorkspace)
      .mockResolvedValueOnce({
        hired_instance_id: 'HAI-1',
        customer_id: 'CUST-1',
        agent_type_id: 'marketing.digital_marketing.v1',
        workspace: {
          brand_name: 'WAOOAW',
          location: 'Pune',
          primary_language: 'en',
          timezone: 'Asia/Kolkata',
          business_context: '',
          offerings_services: ['Activation'],
          platforms_enabled: ['youtube'],
          campaign_setup: structuredClone(defaultWorkspace).campaign_setup,
        },
        readiness: {
          brief_complete: true,
          youtube_selected: true,
          youtube_connection_ready: true,
          configured: true,
          can_finalize: false,
          missing_requirements: [],
        },
        updated_at: '2026-03-18T09:00:00Z',
      } as any)
      .mockResolvedValueOnce({
        hired_instance_id: 'HAI-1',
        customer_id: 'CUST-1',
        agent_type_id: 'marketing.digital_marketing.v1',
        workspace: {
          brand_name: 'WAOOAW',
          location: 'Pune',
          primary_language: 'en',
          timezone: 'Asia/Kolkata',
          business_context: '',
          offerings_services: ['Activation'],
          platforms_enabled: ['youtube'],
          campaign_setup: {
            ...structuredClone(defaultWorkspace).campaign_setup,
            master_theme: 'Trust-first growth updated',
            derived_themes: [
              { title: 'Proof', description: 'Show results', frequency: 'weekly' },
              { title: 'Education', description: 'Teach the market', frequency: 'weekly' },
            ],
          },
        },
        readiness: {
          brief_complete: true,
          youtube_selected: true,
          youtube_connection_ready: true,
          configured: true,
          can_finalize: false,
          missing_requirements: [],
        },
        updated_at: '2026-03-18T09:00:00Z',
      } as any)

    renderWizard()
    fireEvent.click(await screen.findByRole('button', { name: 'Master Theme' }))
    fireEvent.click(screen.getByRole('button', { name: 'Generate theme plan' }))

    await waitFor(() => {
      expect(screen.getByDisplayValue('Trust-first growth')).toBeInTheDocument()
    })

    fireEvent.change(screen.getByLabelText('Master theme'), { target: { value: 'Trust-first growth updated' } })
    fireEvent.click(screen.getByRole('button', { name: 'Save theme plan' }))
    fireEvent.click(screen.getByRole('button', { name: 'Refresh status' }))

    await waitFor(() => {
      expect(screen.getByDisplayValue('Trust-first growth updated')).toBeInTheDocument()
    })
  })

  it('toggles both help panels on and off in the master theme step', async () => {
    renderWizard()
    fireEvent.click(await screen.findByRole('button', { name: 'Master Theme' }))

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
})
