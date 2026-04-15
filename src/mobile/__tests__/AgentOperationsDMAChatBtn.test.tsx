/**
 * AgentOperationsScreen DMA Chat Button Test (MOB-DMA-1 E2-S1-T6)
 *
 * Verifies that the "Chat with Agent" button navigates to DMAConversation
 * when isDigitalMarketing is true.
 */

import React from 'react'
import { render, fireEvent, waitFor } from '@testing-library/react-native'

// ─── Mocks ────────────────────────────────────────────────────────────────────

jest.mock('@/hooks/useTheme', () => ({
  useTheme: () => ({
    colors: {
      black: '#0a0a0a',
      neonCyan: '#00f2fe',
      textPrimary: '#ffffff',
      textSecondary: '#a1a1aa',
      card: '#18181b',
      error: '#ef4444',
      success: '#10b981',
      warning: '#f59e0b',
      border: '#374151',
    },
    spacing: { xs: 4, sm: 8, md: 16, lg: 24, xl: 32, screenPadding: { horizontal: 16, vertical: 20 } },
    typography: {
      fontFamily: { display: 'SpaceGrotesk_700Bold', body: 'Inter_400Regular', bodyBold: 'Inter_600SemiBold' },
    },
  }),
}))

jest.mock('@/hooks/useHiredAgents', () => ({
  useHiredAgentById: jest.fn(() => ({
    data: {
      agent_id: 'AGT-MKT-DMA-001',
      agent_type_id: 'marketing.digital_marketing.v1',
      nickname: 'My DMA Agent',
      hired_instance_id: 'hi-dma-1',
    },
    isLoading: false,
    error: null,
  })),
}))

jest.mock('@/hooks/useApprovalQueue', () => ({
  useApprovalQueue: jest.fn(() => ({
    deliverables: [],
    isLoading: false,
    error: null,
    approve: jest.fn(),
    reject: jest.fn(),
  })),
}))

const mockCpGet = jest.fn()
const mockCpPatch = jest.fn()
const mockCpPost = jest.fn(() => Promise.resolve({ data: {} }))

jest.mock('@/lib/cpApiClient', () => ({
  __esModule: true,
  default: {
    get: (...args: unknown[]) => mockCpGet(...args),
    patch: (...args: unknown[]) => mockCpPatch(...args),
    post: (...args: unknown[]) => mockCpPost(...args),
  },
}))

jest.mock('@/hooks/useAgentVoiceOverlay', () => ({
  useAgentVoiceOverlay: jest.fn(() => ({
    isListening: false,
    toggle: jest.fn(),
    lastCommand: null,
    isAvailable: false,
  })),
}))

jest.mock('@/components/voice/VoiceFAB', () => {
  const React = require('react')
  const { View } = require('react-native')
  return {
    VoiceFAB: (props: any) => React.createElement(View, { testID: props.testID }),
  }
})

const mockNavigate = jest.fn()
const mockGoBack = jest.fn()
const mockNavigation = { navigate: mockNavigate, goBack: mockGoBack } as any

const mockRoute = {
  params: { hiredAgentId: 'hi-dma-1', focusSection: 'goals' },
  key: 'AgentOperations-dma',
  name: 'AgentOperations',
} as any

import { AgentOperationsScreen } from '@/screens/agents/AgentOperationsScreen'

// ─── Tests ────────────────────────────────────────────────────────────────────

describe('AgentOperationsScreen — DMA chat button', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    // Return the Theme Discovery skill so goals section shows the DMA UI
    mockCpGet.mockResolvedValue({
      data: [
        {
          skill_id: 'skill-theme-discovery',
          name: 'theme_discovery',
          display_name: 'Theme Discovery',
          goal_schema: {
            fields: [
              { key: 'business_background', label: 'Business Background', type: 'text', required: true },
              { key: 'industry', label: 'Industry', type: 'text', required: true },
              { key: 'locality', label: 'Locality', type: 'text', required: true },
            ],
          },
          goal_config: {},
        },
      ],
    })
    mockCpPatch.mockResolvedValue({ data: { goal_config: {} } })
  })

  it('E2-S1-T6: tapping chat-with-agent-btn navigates to DMAConversation', async () => {
    const { getByTestId } = render(
      <AgentOperationsScreen navigation={mockNavigation} route={mockRoute} />
    )
    await waitFor(() => {
      expect(getByTestId('chat-with-agent-btn')).toBeTruthy()
    })
    fireEvent.press(getByTestId('chat-with-agent-btn'))
    expect(mockNavigate).toHaveBeenCalledWith('DMAConversation', { hiredAgentId: expect.any(String) })
  })
})
