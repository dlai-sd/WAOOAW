import React from 'react'
import { act, fireEvent, render, screen, waitFor } from '@testing-library/react-native'

import { MyAgentsScreen } from '../MyAgentsScreen'

jest.mock('@/hooks/useHiredAgents', () => ({
  useHiredAgents: jest.fn(),
  useAgentsInTrial: jest.fn(),
}))

jest.mock('@/hooks/useTheme', () => ({
  useTheme: () => ({
    colors: {
      black: '#000000',
      textPrimary: '#ffffff',
      textSecondary: '#cccccc',
      neonCyan: '#00f2fe',
      success: '#10b981',
      warning: '#f59e0b',
      error: '#ef4444',
      border: '#333333',
      card: '#1a1a1a',
    },
    spacing: {
      xs: 4,
      sm: 8,
      md: 16,
      lg: 24,
      xl: 32,
      screenPadding: { horizontal: 16, vertical: 12 },
    },
    typography: {
      fontFamily: {
        display: 'SpaceGrotesk-Bold',
        body: 'Inter-Regular',
        bodyBold: 'Inter-Bold',
      },
    },
  }),
}))

jest.mock('@/components/LoadingSpinner', () => ({
  LoadingSpinner: ({ message }: { message: string }) => <>{message}</>,
}))

jest.mock('@/components/ErrorView', () => ({
  ErrorView: ({ message }: { message: string }) => <>{message}</>,
}))

jest.mock('@/components/voice/VoiceControl', () => ({
  VoiceControl: (props: any) => {
    (global as any).__myAgentsVoiceControlProps = props;
    return null;
  },
}))

jest.mock('@/components/voice/VoiceHelpModal', () => ({
  VoiceHelpModal: () => null,
}))

jest.mock('@/hooks/usePerformanceMonitoring', () => ({
  usePerformanceMonitoring: jest.fn(),
}))

const { useHiredAgents, useAgentsInTrial } = jest.requireMock('@/hooks/useHiredAgents') as {
  useHiredAgents: jest.Mock
  useAgentsInTrial: jest.Mock
}

const mockNavigate = jest.fn()
const mockParentNavigate = jest.fn()

const navigation = {
  navigate: mockNavigate,
  getParent: () => ({ navigate: mockParentNavigate }),
} as any

describe('MyAgentsScreen', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('auto-switches to hired agents when no trials exist but hires do', async () => {
    useHiredAgents.mockReturnValue({
      data: [
        {
          subscription_id: 'sub-1',
          agent_id: 'AGT-OPS-1',
          status: 'active',
          duration: 'monthly',
          current_period_start: '2026-03-01T00:00:00Z',
          current_period_end: '2026-04-01T00:00:00Z',
          cancel_at_period_end: false,
          hired_instance_id: 'hire-1',
          nickname: 'Ops Agent',
          trial_status: null,
        },
      ],
      isLoading: false,
      isFetching: false,
      error: null,
      refetch: jest.fn(),
    })
    useAgentsInTrial.mockReturnValue({
      data: [],
      isLoading: false,
      isFetching: false,
      error: null,
      refetch: jest.fn(),
    })

    render(<MyAgentsScreen navigation={navigation} route={{ key: 'my-agents', name: 'MyAgents' } as any} />)

    await waitFor(() => {
      expect(screen.getByText('AGT-OPS-1')).toBeTruthy()
    })

    expect(screen.getByText('Needs attention')).toBeTruthy()
    expect(screen.queryByText('No Active Trials')).toBeNull()
  })

  it('routes hired agents into the operations hub when runtime id is present', async () => {
    useHiredAgents.mockReturnValue({
      data: [
        {
          subscription_id: 'sub-1',
          agent_id: 'AGT-OPS-1',
          status: 'active',
          duration: 'monthly',
          current_period_start: '2026-03-01T00:00:00Z',
          current_period_end: '2026-04-01T00:00:00Z',
          cancel_at_period_end: false,
          hired_instance_id: 'hire-1',
          nickname: 'Ops Agent',
          trial_status: null,
        },
      ],
      isLoading: false,
      isFetching: false,
      error: null,
      refetch: jest.fn(),
    })
    useAgentsInTrial.mockReturnValue({
      data: [],
      isLoading: false,
      isFetching: false,
      error: null,
      refetch: jest.fn(),
    })

    render(<MyAgentsScreen navigation={navigation} route={{ key: 'my-agents', name: 'MyAgents' } as any} />)

    await waitFor(() => {
      expect(screen.getByText('AGT-OPS-1')).toBeTruthy()
    })

    fireEvent.press(screen.getByTestId('agent-card-sub-1'))

    expect(mockNavigate).toHaveBeenCalledWith('AgentOperations', {
      hiredAgentId: 'hire-1',
    })
  })

  it('derives the attention summary from supported runtime fields only', async () => {
    useHiredAgents.mockReturnValue({
      data: [
        {
          subscription_id: 'sub-1',
          agent_id: 'AGT-OPS-1',
          status: 'active',
          duration: 'monthly',
          current_period_start: '2026-03-01T00:00:00Z',
          current_period_end: '2026-04-01T00:00:00Z',
          cancel_at_period_end: false,
          hired_instance_id: 'hire-1',
          configured: true,
          goals_completed: true,
          nickname: 'Ops Agent',
          trial_status: null,
        },
        {
          subscription_id: 'sub-2',
          agent_id: 'AGT-OPS-2',
          status: 'active',
          duration: 'monthly',
          current_period_start: '2026-03-01T00:00:00Z',
          current_period_end: '2026-04-01T00:00:00Z',
          cancel_at_period_end: true,
          hired_instance_id: 'hire-2',
          configured: false,
          goals_completed: false,
          nickname: 'Needs Setup',
          trial_status: null,
        },
      ],
      isLoading: false,
      isFetching: false,
      error: null,
      refetch: jest.fn(),
    })
    useAgentsInTrial.mockReturnValue({
      data: [],
      isLoading: false,
      isFetching: false,
      error: null,
      refetch: jest.fn(),
    })

    render(<MyAgentsScreen navigation={navigation} route={{ key: 'my-agents', name: 'MyAgents' } as any} />)

    await waitFor(() => {
      expect(screen.getByText('1 need attention')).toBeTruthy()
    })

    expect(screen.getByText('Subscription ending soon')).toBeTruthy()
    expect(screen.getByText('Subscription ending soon • Runtime configuration incomplete • Goals need review')).toBeTruthy()
  })

  it('provides a RefreshControl for pull-to-refresh', () => {
    useHiredAgents.mockReturnValue({
      data: [],
      isLoading: false,
      isFetching: false,
      error: null,
      refetch: jest.fn(),
    })
    useAgentsInTrial.mockReturnValue({
      data: [],
      isLoading: false,
      isFetching: false,
      error: null,
      refetch: jest.fn(),
    })

    const rendered = render(
      <MyAgentsScreen navigation={navigation} route={{ key: 'my-agents', name: 'MyAgents' } as any} />
    )

    expect(rendered.UNSAFE_getByType('ScrollView').props.refreshControl).toBeTruthy()
  })

  it('voice callbacks: navigate, action, help handlers exercise branches', async () => {
    const mockRefetch = jest.fn()
    useHiredAgents.mockReturnValue({
      data: [],
      isLoading: false,
      isFetching: false,
      error: null,
      refetch: mockRefetch,
    })
    useAgentsInTrial.mockReturnValue({
      data: [],
      isLoading: false,
      isFetching: false,
      error: null,
      refetch: mockRefetch,
    })

    render(
      <MyAgentsScreen navigation={navigation} route={{ key: 'my-agents', name: 'MyAgents' } as any} />
    )

    const callbacks = (global as any).__myAgentsVoiceControlProps?.callbacks
    expect(callbacks).toBeTruthy()

    // Trigger all voices branches
    act(() => {
      callbacks?.onNavigate?.('Home')
      callbacks?.onNavigate?.('Discover')
      callbacks?.onNavigate?.('Profile')
      callbacks?.onNavigate?.('UnknownScreen')
      callbacks?.onAction?.('refresh')
      callbacks?.onAction?.('showHelp')
      callbacks?.onAction?.('switchTab')
      callbacks?.onAction?.('unknown')
      callbacks?.onHelp?.()
    })

    expect(mockRefetch).toHaveBeenCalled()
  })
})
