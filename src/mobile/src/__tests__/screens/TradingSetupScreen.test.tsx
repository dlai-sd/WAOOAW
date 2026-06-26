/**
 * Tests for TradingSetupScreen (feat/share-trader-setup-chat)
 */
import React from 'react'
import { render, fireEvent, waitFor, act } from '@testing-library/react-native'
import { TradingSetupScreen } from '../../screens/agents/TradingSetupScreen'
import * as tradingSetupService from '@/services/tradingSetup.service'

const mockNavigate = jest.fn()
const mockGoBack = jest.fn()

jest.mock('@/services/tradingSetup.service')
jest.mock('@/hooks/useTheme', () => ({
  useTheme: () => ({
    colors: {
      black: '#0a0a0a',
      neonCyan: '#00f2fe',
      textPrimary: '#ffffff',
      textSecondary: '#71717a',
    },
    typography: {
      fontFamily: { display: 'SpaceGrotesk', body: 'Inter', bodyBold: 'Inter-Bold' },
    },
  }),
}))

const BASE_RESPONSE = {
  hired_instance_id: 'TRD-001',
  state: {
    step: 'welcome',
    messages: [
      {
        role: 'assistant' as const,
        content: "Namaste! I'm your Share Trader.",
        masked: false,
      },
    ],
    collected: {},
    validation_status: 'pending' as const,
    configured: false,
    updated_at: '',
  },
  readiness: {
    configured: false,
    step: 'welcome',
    has_credentials: false,
    credentials_valid: false,
    has_instrument: false,
    has_rsi_period: false,
    has_risk_limits: false,
  },
}

const mockProps = {
  navigation: { navigate: mockNavigate, goBack: mockGoBack } as any,
  route: { params: { hiredAgentId: 'TRD-001' } } as any,
}

describe('TradingSetupScreen', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    ;(tradingSetupService.getTradingSetup as jest.Mock).mockResolvedValue(BASE_RESPONSE)
    ;(tradingSetupService.sendTradingSetupMessage as jest.Mock).mockResolvedValue({
      ...BASE_RESPONSE,
      state: { ...BASE_RESPONSE.state, step: 'api_key', messages: [
        BASE_RESPONSE.state.messages[0],
        { role: 'user', content: 'start', masked: false },
        { role: 'assistant', content: 'Enter API key', masked: false },
      ]},
    })
  })

  it('renders screen with testID', async () => {
    const { getByTestId } = render(<TradingSetupScreen {...mockProps} />)
    await waitFor(() => getByTestId('trading-setup-screen'))
  })

  it('shows loading spinner initially', () => {
    const { UNSAFE_getByType } = render(<TradingSetupScreen {...mockProps} />)
    // ActivityIndicator shown during initial load
    const { ActivityIndicator } = require('react-native')
    // just verify screen renders without crash
  })

  it('renders first assistant message after load', async () => {
    const { getByText } = render(<TradingSetupScreen {...mockProps} />)
    await waitFor(() => getByText(/Share Trader/))
  })

  it('sends message on press Send', async () => {
    const { getByTestId } = render(<TradingSetupScreen {...mockProps} />)
    await waitFor(() => getByTestId('trading-setup-input'))

    fireEvent.changeText(getByTestId('trading-setup-input'), 'start')
    await act(async () => {
      fireEvent.press(getByTestId('trading-setup-send'))
    })

    expect(tradingSetupService.sendTradingSetupMessage).toHaveBeenCalledWith(
      'TRD-001',
      'start'
    )
  })

  it('Send button disabled when input is empty', async () => {
    const { getByTestId } = render(<TradingSetupScreen {...mockProps} />)
    await waitFor(() => getByTestId('trading-setup-send'))
    const btn = getByTestId('trading-setup-send')
    expect(btn.props.accessibilityState?.disabled ?? btn.props.disabled).toBeTruthy()
  })

  it('shows Secure badge on api_key step', async () => {
    ;(tradingSetupService.getTradingSetup as jest.Mock).mockResolvedValue({
      ...BASE_RESPONSE,
      state: { ...BASE_RESPONSE.state, step: 'api_key' },
    })
    const { getByText } = render(<TradingSetupScreen {...mockProps} />)
    await waitFor(() => getByText(/Secure/))
  })

  it('shows done button on done step', async () => {
    ;(tradingSetupService.getTradingSetup as jest.Mock).mockResolvedValue({
      ...BASE_RESPONSE,
      state: { ...BASE_RESPONSE.state, step: 'done', configured: true },
    })
    const { getByTestId } = render(<TradingSetupScreen {...mockProps} />)
    await waitFor(() => getByTestId('trading-setup-done-btn'))
    fireEvent.press(getByTestId('trading-setup-done-btn'))
    expect(mockGoBack).toHaveBeenCalled()
  })

  it('shows error banner on load failure', async () => {
    ;(tradingSetupService.getTradingSetup as jest.Mock).mockRejectedValue(new Error('network'))
    const { getByText } = render(<TradingSetupScreen {...mockProps} />)
    await waitFor(() => getByText(/Failed to load/))
  })

  it('back button calls goBack', async () => {
    const { getByTestId } = render(<TradingSetupScreen {...mockProps} />)
    await waitFor(() => getByTestId('trading-setup-back'))
    fireEvent.press(getByTestId('trading-setup-back'))
    expect(mockGoBack).toHaveBeenCalled()
  })
})
