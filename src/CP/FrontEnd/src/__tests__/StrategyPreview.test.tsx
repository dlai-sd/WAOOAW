import { describe, it, expect, vi, beforeEach } from 'vitest'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'

import { DigitalMarketingActivationWizard } from '../components/DigitalMarketingActivationWizard'

vi.mock('../services/hiredAgents.service', () => ({
  getHiredAgentBySubscription: vi.fn(async () => ({
    subscription_id: 'sub-1',
    hired_instance_id: 'hire-1',
    agent_id: 'AGT-MKT-DMA-001',
    agent_type_id: 'marketing.digital_marketing.v1',
    nickname: 'Growth Copilot',
    theme: 'default',
    config: {},
    configured: false,
    goals_completed: false,
  })),
  upsertHiredAgentDraft: vi.fn(async (payload) => ({
    ...payload,
    hired_instance_id: 'hire-1',
    configured: false,
    goals_completed: false,
  })),
}))

vi.mock('../services/digitalMarketingActivation.service', () => ({
  buildMarketingPlatformBindings: vi.fn(() => ({})),
  generateDigitalMarketingThemePlan: vi.fn(),
  getActivationMilestoneCount: vi.fn(() => 0),
  getDigitalMarketingActivationWorkspace: vi.fn(),
  getSelectedMarketingPlatforms: vi.fn(() => ['youtube']),
  patchDigitalMarketingThemePlan: vi.fn(),
  upsertDigitalMarketingActivationWorkspace: vi.fn(async (id, payload) => ({
    hired_instance_id: id,
    customer_id: 'cust-1',
    agent_type_id: 'marketing.digital_marketing.v1',
    workspace: {
      ...(payload.workspace || {}),
      platform_bindings: {},
      campaign_setup: payload.workspace?.campaign_setup || {
        master_theme: '',
        derived_themes: [],
        strategy_workshop: {
          status: 'not_started',
          assistant_message: '',
          checkpoint_summary: '',
          current_focus_question: '',
          next_step_options: [],
          time_saving_note: '',
          follow_up_questions: [],
          messages: [],
          summary: {},
        },
      },
    },
    readiness: {
      brief_complete: false,
      youtube_selected: true,
      youtube_connection_ready: false,
      configured: false,
      can_finalize: false,
      missing_requirements: [],
    },
    updated_at: new Date().toISOString(),
  })),
}))

vi.mock('../services/marketingReview.service', () => ({
  createDraftBatch: vi.fn(),
  executeDraftPost: vi.fn(),
  approveDraftPost: vi.fn(),
  rejectDraftPost: vi.fn(),
  scheduleDraftPost: vi.fn(),
}))

vi.mock('../services/youtubeConnections.service', () => ({
  startYouTubeConnection: vi.fn(),
  attachYouTubeConnection: vi.fn(),
  listYouTubeConnections: vi.fn(async () => []),
}))

vi.mock('../services/platformConnections.service', () => ({
  findPlatformConnection: vi.fn(() => null),
  listPlatformConnections: vi.fn(async () => []),
}))

vi.mock('../utils/browserNavigation', () => ({
  redirectTo: vi.fn(),
}))

vi.mock('../utils/youtubeOAuthFlow', () => ({
  beginYouTubeOAuthFlow: vi.fn(),
  clearYouTubeOAuthResult: vi.fn(),
  getYouTubeOAuthCallbackUri: vi.fn(() => 'http://localhost/callback'),
  readYouTubeOAuthResult: vi.fn(() => null),
}))

vi.mock('../services/brandVoice.service', () => ({
  getBrandVoice: vi.fn(async () => ({
    tone_keywords: [],
    vocabulary_preferences: [],
    messaging_patterns: [],
    example_phrases: [],
    voice_description: '',
  })),
  updateBrandVoice: vi.fn(async (payload) => payload),
}))

const instance = {
  subscription_id: 'sub-1',
  hired_instance_id: 'hire-1',
  agent_id: 'AGT-MKT-DMA-001',
  agent_type_id: 'marketing.digital_marketing.v1',
  configured: false,
  goals_completed: false,
}

async function moveToThemeStep() {
  for (let index = 0; index < 3; index += 1) {
    fireEvent.click(await screen.findByRole('button', { name: 'Continue' }))
  }
  await screen.findByTestId('dma-step-panel-theme')
}

describe('StrategyPreview', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders the strategy preview summary and messages before approval', async () => {
    const activation = await import('../services/digitalMarketingActivation.service')
    vi.mocked(activation.getDigitalMarketingActivationWorkspace).mockResolvedValueOnce({
      hired_instance_id: 'hire-1',
      customer_id: 'cust-1',
      agent_type_id: 'marketing.digital_marketing.v1',
      workspace: {
        brand_name: 'WAOOAW',
        location: 'Pune',
        primary_language: 'English',
        timezone: 'Asia/Kolkata',
        business_context: '',
        offerings_services: ['Strategy'],
        platforms_enabled: ['youtube'],
        platform_bindings: {},
        campaign_setup: {
          master_theme: 'Video growth',
          derived_themes: [],
          strategy_workshop: {
            status: 'approval_ready',
            assistant_message: 'Focus on video content.',
            checkpoint_summary: 'Focus on video content and consistent posting.',
            current_focus_question: '',
            next_step_options: [],
            time_saving_note: '',
            follow_up_questions: [],
            messages: [{ role: 'assistant', content: 'Focus on video content.' }],
            summary: {},
          },
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
      updated_at: new Date().toISOString(),
    })

    render(<DigitalMarketingActivationWizard instance={instance as any} instances={[instance as any]} readOnly={false} />)
    await moveToThemeStep()

    await waitFor(() => {
      expect(screen.getByText('Review your content strategy before approving')).toBeTruthy()
    })
    expect(screen.getByText('Focus on video content and consistent posting.')).toBeTruthy()
    expect(screen.getAllByText('Focus on video content.').length).toBeGreaterThan(0)
  })

  it('renders the empty placeholder when no strategy exists yet', async () => {
    const activation = await import('../services/digitalMarketingActivation.service')
    vi.mocked(activation.getDigitalMarketingActivationWorkspace).mockResolvedValueOnce({
      hired_instance_id: 'hire-1',
      customer_id: 'cust-1',
      agent_type_id: 'marketing.digital_marketing.v1',
      workspace: {
        brand_name: 'WAOOAW',
        location: 'Pune',
        primary_language: 'English',
        timezone: 'Asia/Kolkata',
        business_context: '',
        offerings_services: ['Strategy'],
        platforms_enabled: ['youtube'],
        platform_bindings: {},
        campaign_setup: {
          master_theme: '',
          derived_themes: [],
          strategy_workshop: {
            status: 'not_started',
            assistant_message: '',
            checkpoint_summary: '',
            current_focus_question: '',
            next_step_options: [],
            time_saving_note: '',
            follow_up_questions: [],
            messages: [],
            summary: {},
          },
        },
      },
      readiness: {
        brief_complete: false,
        youtube_selected: true,
        youtube_connection_ready: false,
        configured: false,
        can_finalize: false,
        missing_requirements: [],
      },
      updated_at: new Date().toISOString(),
    })

    render(<DigitalMarketingActivationWizard instance={instance as any} instances={[instance as any]} readOnly={false} />)
    await moveToThemeStep()

    await waitFor(() => {
      expect(screen.getByText(/No strategy generated yet/i)).toBeTruthy()
    })
  })

  it('does not render the preview once the strategy is approved', async () => {
    const activation = await import('../services/digitalMarketingActivation.service')
    vi.mocked(activation.getDigitalMarketingActivationWorkspace).mockResolvedValueOnce({
      hired_instance_id: 'hire-1',
      customer_id: 'cust-1',
      agent_type_id: 'marketing.digital_marketing.v1',
      workspace: {
        brand_name: 'WAOOAW',
        location: 'Pune',
        primary_language: 'English',
        timezone: 'Asia/Kolkata',
        business_context: '',
        offerings_services: ['Strategy'],
        platforms_enabled: ['youtube'],
        platform_bindings: {},
        campaign_setup: {
          master_theme: 'Video growth',
          derived_themes: [],
          strategy_workshop: {
            status: 'approved',
            assistant_message: 'Approved strategy',
            checkpoint_summary: 'Approved strategy',
            current_focus_question: '',
            next_step_options: [],
            time_saving_note: '',
            follow_up_questions: [],
            messages: [{ role: 'assistant', content: 'Approved strategy' }],
            summary: {},
          },
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
      updated_at: new Date().toISOString(),
    })

    render(<DigitalMarketingActivationWizard instance={instance as any} instances={[instance as any]} readOnly={false} />)
    await moveToThemeStep()

    await waitFor(() => {
      expect(screen.queryByText('Review your content strategy before approving')).toBeNull()
    })
  })
})
