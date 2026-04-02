import { beforeEach, describe, expect, it, vi } from 'vitest'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'

import { DigitalMarketingActivationWizard } from '../components/DigitalMarketingActivationWizard'

vi.mock('../services/profile.service', () => ({
  getProfile: vi.fn(async () => ({ id: 'user-1', email: 'test@example.com' })),
  updateProfile: vi.fn(async () => ({ id: 'user-1', email: 'test@example.com' })),
}))

vi.mock('../services/brandVoice.service', () => ({
  getBrandVoice: vi.fn(async () => ({
    tone_keywords: [],
    vocabulary_preferences: [],
    messaging_patterns: [],
    example_phrases: [],
    voice_description: '',
  })),
  updateBrandVoice: vi.fn(async () => ({
    tone_keywords: [],
    vocabulary_preferences: [],
    messaging_patterns: [],
    example_phrases: [],
    voice_description: '',
  })),
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
      brand_name: '',
      location: '',
      primary_language: '',
      timezone: '',
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
  getSelectedMarketingPlatforms: vi.fn((workspace) => workspace?.platforms_enabled || []),
  patchDigitalMarketingThemePlan: vi.fn(async () => ({ workspace: {} })),
  upsertDigitalMarketingActivationWorkspace: vi.fn(async () => ({
    hired_instance_id: 'hire_1',
    customer_id: 'user-1',
    agent_type_id: 'marketing.digital_marketing.v1',
    workspace: {
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

async function renderWizard() {
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

  await waitFor(() => {
    expect(screen.getByRole('button', { name: /Choose Platforms/i })).toBeInTheDocument()
  })
}

describe('Wizard platforms', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('shows only the supported YouTube platform card', async () => {
    await renderWizard()
    fireEvent.click(screen.getByRole('button', { name: /Choose Platforms/i }))

    await waitFor(() => {
      expect(screen.getByText('YouTube')).toBeInTheDocument()
    })
    expect(screen.queryByText('Instagram')).not.toBeInTheDocument()
    expect(screen.queryByText('Unavailable')).not.toBeInTheDocument()
  })

  it('does not show unavailable badges in the connect step', async () => {
    await renderWizard()
    fireEvent.click(screen.getByRole('button', { name: /Connect Platforms/i }))

    await waitFor(() => {
      expect(screen.getByText(/Connect your YouTube channel/i)).toBeInTheDocument()
    })
    expect(screen.queryByText('Instagram')).not.toBeInTheDocument()
    expect(screen.queryByText('Unavailable')).not.toBeInTheDocument()
  })
})
