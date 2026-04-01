import { beforeEach, describe, expect, it, vi } from 'vitest'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'

import { DigitalMarketingActivationWizard } from '../components/DigitalMarketingActivationWizard'

const { getBrandVoiceMock, updateBrandVoiceMock } = vi.hoisted(() => ({
  getBrandVoiceMock: vi.fn(async () => ({
    tone_keywords: ['warm', 'credible'],
    vocabulary_preferences: [],
    messaging_patterns: [],
    example_phrases: ['We explain every step.'],
    voice_description: 'Warm and credible.',
  })),
  updateBrandVoiceMock: vi.fn(async () => ({
    tone_keywords: ['warm', 'credible'],
    vocabulary_preferences: [],
    messaging_patterns: [],
    example_phrases: ['We explain every step.'],
    voice_description: 'Warm and credible.',
  })),
}))

vi.mock('../services/brandVoice.service', () => ({
  getBrandVoice: getBrandVoiceMock,
  updateBrandVoice: updateBrandVoiceMock,
}))

vi.mock('../services/hiredAgents.service', () => ({
  getHiredAgentBySubscription: vi.fn(async () => ({
    hired_instance_id: 'hire_1',
    subscription_id: 'sub_1',
    agent_id: 'AGT-MKT-DMA-001',
    agent_type_id: 'marketing.digital_marketing.v1',
    nickname: 'Growth Copilot',
    theme: 'default',
    config: {},
    configured: false,
    goals_completed: false,
  })),
  upsertHiredAgentDraft: vi.fn(async () => ({
    hired_instance_id: 'hire_1',
    subscription_id: 'sub_1',
    agent_id: 'AGT-MKT-DMA-001',
    agent_type_id: 'marketing.digital_marketing.v1',
    nickname: 'Growth Copilot',
    theme: 'default',
    config: {},
    configured: true,
    goals_completed: false,
  })),
}))

vi.mock('../services/digitalMarketingActivation.service', () => ({
  buildMarketingPlatformBindings: vi.fn((_platforms, existing) => existing || {}),
  generateDigitalMarketingThemePlan: vi.fn(async () => ({ workspace: { campaign_setup: { strategy_workshop: { status: 'discovery', messages: [] } } } })),
  getActivationMilestoneCount: vi.fn(() => 1),
  getDigitalMarketingActivationWorkspace: vi.fn(async () => ({
    hired_instance_id: 'hire_1',
    customer_id: 'user-1',
    agent_type_id: 'marketing.digital_marketing.v1',
    workspace: {
      brand_name: 'WAOOAW',
      location: 'Mumbai',
      primary_language: 'English',
      timezone: 'Asia/Kolkata',
      business_context: '',
      offerings_services: [],
      platforms_enabled: ['youtube'],
      platform_bindings: {},
      campaign_setup: {
        strategy_workshop: {
          status: 'discovery',
          assistant_message: '',
          checkpoint_summary: '',
          current_focus_question: '',
          next_step_options: [],
          time_saving_note: '',
          follow_up_questions: [],
          messages: [],
          summary: {},
          approved_at: null,
        },
      },
    },
    readiness: {
      brief_complete: true,
      youtube_selected: true,
      youtube_connection_ready: false,
      configured: true,
      can_finalize: false,
      missing_requirements: [],
    },
    updated_at: '2026-04-01T00:00:00Z',
  })),
  getSelectedMarketingPlatforms: vi.fn((workspace) => workspace?.platforms_enabled || []),
  patchDigitalMarketingThemePlan: vi.fn(async () => ({ workspace: {} })),
  upsertDigitalMarketingActivationWorkspace: vi.fn(async () => ({
    hired_instance_id: 'hire_1',
    customer_id: 'user-1',
    agent_type_id: 'marketing.digital_marketing.v1',
    workspace: {
      brand_name: 'WAOOAW',
      location: 'Mumbai',
      primary_language: 'English',
      timezone: 'Asia/Kolkata',
      business_context: '',
      offerings_services: [],
      platforms_enabled: ['youtube'],
      platform_bindings: {},
      campaign_setup: { strategy_workshop: { status: 'discovery', messages: [], summary: {} } },
    },
    readiness: {
      brief_complete: true,
      youtube_selected: true,
      youtube_connection_ready: false,
      configured: true,
      can_finalize: false,
      missing_requirements: [],
    },
    updated_at: '2026-04-01T00:00:00Z',
  })),
}))

vi.mock('../services/marketingReview.service', () => ({
  createDraftBatch: vi.fn(async () => ({ posts: [] })),
  executeDraftPost: vi.fn(async () => ({})),
  approveDraftPost: vi.fn(async () => ({ approval_id: 'APR-1' })),
  rejectDraftPost: vi.fn(async () => ({})),
  scheduleDraftPost: vi.fn(async () => ({})),
}))

vi.mock('../services/youtubeConnections.service', () => ({
  startYouTubeConnection: vi.fn(async () => ({ state: 'state', authorization_url: 'https://example.com' })),
  attachYouTubeConnection: vi.fn(async () => ({})),
  listYouTubeConnections: vi.fn(async () => []),
}))

vi.mock('../services/platformConnections.service', () => ({
  findPlatformConnection: vi.fn(() => null),
  listPlatformConnections: vi.fn(async () => []),
}))

vi.mock('../utils/browserNavigation', () => ({ redirectTo: vi.fn() }))
vi.mock('../utils/youtubeOAuthFlow', () => ({
  beginYouTubeOAuthFlow: vi.fn(),
  clearYouTubeOAuthResult: vi.fn(),
  getYouTubeOAuthCallbackUri: vi.fn(() => 'https://example.com/callback'),
  readYouTubeOAuthResult: vi.fn(() => null),
}))

describe('Brand voice section', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  async function renderThemeStep() {
    const activeInstance = {
      subscription_id: 'sub_1',
      agent_id: 'AGT-MKT-DMA-001',
      agent_type_id: 'marketing.digital_marketing.v1',
      hired_instance_id: 'hire_1',
      nickname: 'Growth Copilot',
      duration: 'monthly',
      status: 'active',
      current_period_start: '',
      current_period_end: '',
      cancel_at_period_end: false,
      configured: false,
      goals_completed: false,
    }

    render(
      <DigitalMarketingActivationWizard
        instance={activeInstance}
        instances={[activeInstance]}
        readOnly={false}
      />
    )

    fireEvent.click(await screen.findByRole('button', { name: /Build Master Theme/i }))

    await waitFor(() => {
      expect(screen.getByText('Brand Voice')).toBeInTheDocument()
    })
  }

  it('loads brand voice into the step 5 fields', async () => {
    await renderThemeStep()

    await waitFor(() => {
      expect(screen.getByLabelText('Voice description')).toHaveValue('Warm and credible.')
    })
    expect(screen.getByLabelText('Tone keywords')).toHaveValue('warm, credible')
  })

  it('keeps fields empty when brand voice is missing', async () => {
    getBrandVoiceMock.mockRejectedValueOnce(new Error('404'))
    await renderThemeStep()

    await waitFor(() => {
      expect(screen.getByText('Brand Voice')).toBeInTheDocument()
    })
    expect(screen.getByLabelText('Voice description')).toHaveValue('')
  })

  it('saves parsed brand voice arrays on continue', async () => {
    await renderThemeStep()

    fireEvent.change(screen.getByLabelText('Voice description'), { target: { value: 'Helpful and direct' } })
    fireEvent.change(screen.getByLabelText('Tone keywords'), { target: { value: 'helpful, direct' } })
    fireEvent.change(screen.getByLabelText('Example phrases'), { target: { value: 'Line one\nLine two' } })
    fireEvent.click(screen.getByRole('button', { name: /Continue/i }))

    await waitFor(() => {
      expect(updateBrandVoiceMock).toHaveBeenCalledWith(
        expect.objectContaining({
          voice_description: 'Helpful and direct',
          tone_keywords: ['helpful', 'direct'],
          example_phrases: ['Line one', 'Line two'],
        })
      )
    })
  })
})
