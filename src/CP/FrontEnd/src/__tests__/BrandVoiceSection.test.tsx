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
  getDigitalMarketingActivationWorkspace: vi.fn(async () => ({
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
  })),
  getSelectedMarketingPlatforms: vi.fn(() => ['youtube']),
  patchDigitalMarketingThemePlan: vi.fn(),
  upsertDigitalMarketingActivationWorkspace: vi.fn(async (id, payload) => ({
    hired_instance_id: id,
    customer_id: 'cust-1',
    agent_type_id: 'marketing.digital_marketing.v1',
    workspace: {
      ...(payload.workspace || {}),
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
  getBrandVoice: vi.fn(),
  updateBrandVoice: vi.fn(async (payload) => ({
    tone_keywords: payload.tone_keywords || [],
    vocabulary_preferences: payload.vocabulary_preferences || [],
    messaging_patterns: payload.messaging_patterns || [],
    example_phrases: payload.example_phrases || [],
    voice_description: payload.voice_description || '',
  })),
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

describe('BrandVoiceSection', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('loads existing brand voice into the theme step', async () => {
    const brandVoice = await import('../services/brandVoice.service')
    vi.mocked(brandVoice.getBrandVoice).mockResolvedValueOnce({
      tone_keywords: ['confident', 'warm'],
      vocabulary_preferences: [],
      messaging_patterns: [],
      example_phrases: ['Let us grow together'],
      voice_description: 'Confident and warm',
    })

    render(<DigitalMarketingActivationWizard instance={instance as any} instances={[instance as any]} readOnly={false} />)
    await moveToThemeStep()

    await waitFor(() => {
      expect(screen.getByDisplayValue('Confident and warm')).toBeTruthy()
    })
    expect(screen.getByDisplayValue('confident, warm')).toBeTruthy()
  })

  it('keeps brand voice fields empty when none exists yet', async () => {
    const brandVoice = await import('../services/brandVoice.service')
    vi.mocked(brandVoice.getBrandVoice).mockRejectedValueOnce(new Error('404'))

    render(<DigitalMarketingActivationWizard instance={instance as any} instances={[instance as any]} readOnly={false} />)
    await moveToThemeStep()

    await waitFor(() => {
      expect(screen.getByLabelText('Voice description')).toBeTruthy()
    })
    expect((screen.getByLabelText('Voice description') as HTMLTextAreaElement).value).toBe('')
  })

  it('updates brand voice when continuing from the theme step', async () => {
    const brandVoice = await import('../services/brandVoice.service')
    vi.mocked(brandVoice.getBrandVoice).mockResolvedValueOnce({
      tone_keywords: [],
      vocabulary_preferences: [],
      messaging_patterns: [],
      example_phrases: [],
      voice_description: '',
    })

    render(<DigitalMarketingActivationWizard instance={instance as any} instances={[instance as any]} readOnly={false} />)
    await moveToThemeStep()

    fireEvent.change(screen.getByLabelText('Voice description'), { target: { value: 'Bold and expert' } })
    fireEvent.change(screen.getByLabelText('Tone keywords'), { target: { value: 'bold, expert' } })
    fireEvent.change(screen.getByLabelText('Example phrases'), { target: { value: 'We make growth simple' } })
    fireEvent.click(screen.getByRole('button', { name: 'Continue' }))

    await waitFor(() => {
      expect(brandVoice.updateBrandVoice).toHaveBeenCalledWith(expect.objectContaining({
        tone_keywords: ['bold', 'expert'],
        example_phrases: ['We make growth simple'],
        voice_description: 'Bold and expert',
      }))
    })
  })
})
