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

const mockGetWorkspace = jest.fn()
const mockPatchWorkspace = jest.fn()

jest.mock('@/services/digitalMarketingActivation.service', () => ({
  getDigitalMarketingActivationWorkspace: (...args: unknown[]) => mockGetWorkspace(...args),
  patchDigitalMarketingActivationWorkspace: (...args: unknown[]) => mockPatchWorkspace(...args),
}))

const mockToggle = jest.fn()
jest.mock('@/hooks/useAgentVoiceOverlay', () => ({
  useAgentVoiceOverlay: jest.fn(() => ({
    isListening: false,
    toggle: mockToggle,
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

jest.mock('@/components/ArtifactRenderer', () => ({
  ArtifactRenderer: () => null,
}))

const mockNavigate = jest.fn()
const mockGoBack = jest.fn()

const makeNavigation = () => ({ navigate: mockNavigate, goBack: mockGoBack } as any)
const makeRoute = (hiredAgentId = 'ha-1') => ({
  params: { hiredAgentId },
  key: 'DMAConversation-1',
  name: 'DMAConversation',
} as any)

const makeWorkspaceResp = (messages: { role: string; content: string }[] = []) => ({
  hired_instance_id: 'ha-1',
  agent_type_id: 'marketing.digital_marketing.v1',
  workspace: {
    campaign_setup: {
      strategy_workshop: { messages },
    },
  },
  readiness: { brief_complete: false, youtube_selected: false, youtube_connection_ready: false, configured: false, can_finalize: false, missing_requirements: [] },
  updated_at: '2026-01-01T00:00:00Z',
})

import { DMAConversationScreen } from '@/screens/agents/DMAConversationScreen'
import { useAgentVoiceOverlay } from '@/hooks/useAgentVoiceOverlay'

// ─── Tests ────────────────────────────────────────────────────────────────────

describe('DMAConversationScreen', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    ;(useAgentVoiceOverlay as jest.Mock).mockReturnValue({
      isListening: false,
      toggle: mockToggle,
      lastCommand: null,
      isAvailable: false,
    })
  })

  it('E2-S1-T1: shows both message bubbles when workspace has 2 messages', async () => {
    mockGetWorkspace.mockResolvedValueOnce(
      makeWorkspaceResp([
        { role: 'assistant', content: 'Hello, tell me about your business.' },
        { role: 'user', content: 'We sell dental services.' },
      ])
    )
    const { getByText } = render(
      <DMAConversationScreen navigation={makeNavigation()} route={makeRoute()} />
    )
    await waitFor(() => {
      expect(getByText('Hello, tell me about your business.')).toBeTruthy()
      expect(getByText('We sell dental services.')).toBeTruthy()
    })
  })

  it('E2-S1-T2: shows error banner when workspace load throws', async () => {
    mockGetWorkspace.mockRejectedValueOnce(new Error('network error'))
    const { getByText } = render(
      <DMAConversationScreen navigation={makeNavigation()} route={makeRoute()} />
    )
    await waitFor(() => {
      expect(getByText('Failed to load conversation. Please try again.')).toBeTruthy()
    })
  })

  it('E2-S1-T3: calls patch with user message when Send is pressed', async () => {
    mockGetWorkspace.mockResolvedValueOnce(makeWorkspaceResp([]))
    mockPatchWorkspace.mockResolvedValueOnce(makeWorkspaceResp([{ role: 'user', content: 'hello' }]))

    const { getByTestId } = render(
      <DMAConversationScreen navigation={makeNavigation()} route={makeRoute()} />
    )
    await waitFor(() => {
      expect(getByTestId('dma-chat-input')).toBeTruthy()
    })

    fireEvent.changeText(getByTestId('dma-chat-input'), 'hello')
    fireEvent.press(getByTestId('dma-chat-send'))

    await waitFor(() => {
      expect(mockPatchWorkspace).toHaveBeenCalled()
      const patchArgs = mockPatchWorkspace.mock.calls[0]
      const messages = patchArgs[1]?.campaign_setup?.strategy_workshop?.messages
      expect(Array.isArray(messages)).toBe(true)
      expect(messages.some((m: any) => m.role === 'user' && m.content === 'hello')).toBe(true)
    })
  })

  it('E2-S1-T4: shows empty-state hint when messages is empty', async () => {
    mockGetWorkspace.mockResolvedValueOnce(makeWorkspaceResp([]))
    const { getByText } = render(
      <DMAConversationScreen navigation={makeNavigation()} route={makeRoute()} />
    )
    await waitFor(() => {
      expect(
        getByText('Start the strategy workshop — describe your business, audience, and goals.')
      ).toBeTruthy()
    })
  })

  it('E2-S1-T5: shows ActivityIndicator while workspace promise is pending', () => {
    // Never-resolving promise
    mockGetWorkspace.mockReturnValueOnce(new Promise(() => {}))
    const { UNSAFE_getAllByType } = render(
      <DMAConversationScreen navigation={makeNavigation()} route={makeRoute()} />
    )
    const { ActivityIndicator } = require('react-native')
    const indicators = UNSAFE_getAllByType(ActivityIndicator)
    expect(indicators.length).toBeGreaterThan(0)
  })

  it('E3-S1-T1: renders voice-fab-dma when useAgentVoiceOverlay returns isAvailable true', async () => {
    ;(useAgentVoiceOverlay as jest.Mock).mockReturnValue({
      isListening: false,
      toggle: mockToggle,
      lastCommand: null,
      isAvailable: true,
    })
    mockGetWorkspace.mockResolvedValueOnce(makeWorkspaceResp([]))
    const { getByTestId } = render(
      <DMAConversationScreen navigation={makeNavigation()} route={makeRoute()} />
    )
    await waitFor(() => {
      expect(getByTestId('voice-fab-dma')).toBeTruthy()
    })
  })

  it('E3-S1-T2: does not render voice-fab-dma and still shows input when isAvailable false', async () => {
    ;(useAgentVoiceOverlay as jest.Mock).mockReturnValue({
      isListening: false,
      toggle: jest.fn(),
      lastCommand: null,
      isAvailable: false,
    })
    mockGetWorkspace.mockResolvedValueOnce(makeWorkspaceResp([]))
    const { queryByTestId, getByTestId } = render(
      <DMAConversationScreen navigation={makeNavigation()} route={makeRoute()} />
    )
    await waitFor(() => {
      expect(queryByTestId('voice-fab-dma')).toBeNull()
      expect(getByTestId('dma-chat-input')).toBeTruthy()
    })
  })

  it('E3-S1-T3: voice "send message" command calls patch (handleSend executes)', async () => {
    let capturedCommands: any = null
    ;(useAgentVoiceOverlay as jest.Mock).mockImplementation((commands: any) => {
      capturedCommands = commands
      return { isListening: false, toggle: jest.fn(), lastCommand: null, isAvailable: true }
    })
    mockGetWorkspace.mockResolvedValueOnce(makeWorkspaceResp([]))
    mockPatchWorkspace.mockResolvedValue(makeWorkspaceResp([]))

    const { getByTestId } = render(
      <DMAConversationScreen navigation={makeNavigation()} route={makeRoute()} />
    )
    await waitFor(() => {
      expect(getByTestId('dma-chat-input')).toBeTruthy()
    })

    // Give the input some text so handleSend will not early-exit on empty
    fireEvent.changeText(getByTestId('dma-chat-input'), 'voice triggered')

    // Re-render captures the latest capturedCommands via closure
    expect(capturedCommands).not.toBeNull()
    expect(typeof capturedCommands['send message']).toBe('function')

    await capturedCommands['send message']('')
    expect(mockPatchWorkspace).toHaveBeenCalled()
  })
})
