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

describe('DMA Activation Wizard — step navigation', () => {
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
        can_finalize: true,
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
        activation_complete: false,
        campaign_setup: structuredClone(defaultWorkspace).campaign_setup,
      },
      readiness: {
        brief_complete: true,
        youtube_selected: true,
        youtube_connection_ready: true,
        configured: true,
        can_finalize: true,
        missing_requirements: [],
      },
      updated_at: '2026-03-18T09:00:00Z',
    } as any)

    const hiredAgentsModule = await import('../services/hiredAgents.service')
    vi.mocked(hiredAgentsModule.upsertHiredAgentDraft).mockResolvedValue({
      subscription_id: 'SUB-1',
      hired_instance_id: 'HAI-1',
      agent_id: 'AGT-MKT-DMA-001',
      agent_type_id: 'marketing.digital_marketing.v1',
      nickname: 'Growth Copilot',
      theme: 'dark',
      config: {},
      configured: true,
      goals_completed: false,
    })
  })

  it('renders wizard shell with 6 step buttons', async () => {
    renderWizard()
    await waitFor(() => {
      expect(screen.getByTestId('dma-step-panel-induct')).toBeInTheDocument()
    })
    const stepTitles = ['Induct Agent', 'Choose Platforms', 'Connect Platforms', 'Build Master Theme', 'Confirm Schedule', 'Review & Activate']
    for (const title of stepTitles) {
      expect(screen.getByText(title)).toBeInTheDocument()
    }
    expect(screen.getByText('Now')).toBeInTheDocument()
  })

  it('starts on step 1 — Induct Agent panel visible', async () => {
    renderWizard()
    await waitFor(() => {
      expect(screen.getByTestId('dma-step-panel-induct')).toBeInTheDocument()
    })
    expect(screen.getByLabelText('Nickname')).toBeInTheDocument()
  })

  it('Continue button advances to step 2', async () => {
    renderWizard()
    await waitFor(() => {
      expect(screen.getByTestId('dma-step-panel-induct')).toBeInTheDocument()
    })
    fireEvent.click(screen.getByRole('button', { name: 'Continue' }))
    await waitFor(() => {
      expect(screen.getByTestId('dma-step-panel-platforms')).toBeInTheDocument()
    })
  })

  it('Back button goes back from step 2 to step 1', async () => {
    renderWizard()
    await waitFor(() => {
      expect(screen.getByTestId('dma-step-panel-induct')).toBeInTheDocument()
    })
    fireEvent.click(screen.getByRole('button', { name: 'Continue' }))
    await waitFor(() => {
      expect(screen.getByTestId('dma-step-panel-platforms')).toBeInTheDocument()
    })
    fireEvent.click(screen.getByRole('button', { name: 'Back' }))
    await waitFor(() => {
      expect(screen.getByTestId('dma-step-panel-induct')).toBeInTheDocument()
    })
  })

  it('Back button disabled on step 1', async () => {
    renderWizard()
    await waitFor(() => {
      expect(screen.getByTestId('dma-step-panel-induct')).toBeInTheDocument()
    })
    expect(screen.getByRole('button', { name: 'Back' })).toBeDisabled()
  })

  it('Activate Agent button visible on step 6', async () => {
    renderWizard()
    await waitFor(() => {
      expect(screen.getByTestId('dma-step-panel-induct')).toBeInTheDocument()
    })
    const reviewActivateBtn = screen.getByText('Review & Activate').closest('button')
    expect(reviewActivateBtn).not.toBeNull()
    fireEvent.click(reviewActivateBtn!)
    await waitFor(() => {
      expect(screen.getByTestId('dma-step-panel-activate')).toBeInTheDocument()
    })
    expect(screen.getByRole('button', { name: 'Activate Agent' })).toBeInTheDocument()
  })
})

