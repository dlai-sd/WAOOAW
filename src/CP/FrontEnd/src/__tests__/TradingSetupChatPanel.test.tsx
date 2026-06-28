import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { FluentProvider } from '@fluentui/react-components'
import { waooawLightTheme } from '../theme'
import { TradingSetupChatPanel } from '../components/TradingSetupChatPanel'

const makeMockSetup = (step: string, messages = [{ role: 'assistant' as const, content: 'Welcome!', masked: false }]) => ({
  hired_instance_id: 'HIRED-1',
  state: {
    step,
    messages,
    collected: {},
    validation_status: 'pending' as const,
    configured: false,
  },
  readiness: {
    configured: false,
    step,
    has_credentials: false,
    credentials_valid: false,
    has_instrument: false,
    has_rsi_period: false,
    has_risk_limits: false,
  },
})

vi.mock('../services/tradingSetup.service', () => ({
  getTradingSetup: vi.fn(),
  sendTradingSetupMessage: vi.fn(),
  emergencyStop: vi.fn(),
}))

const renderComponent = (hiredInstanceId = 'HIRED-1') =>
  render(
    <FluentProvider theme={waooawLightTheme}>
      <TradingSetupChatPanel hiredInstanceId={hiredInstanceId} />
    </FluentProvider>
  )

describe('TradingSetupChatPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('T1: renders message list from loaded state', async () => {
    const { getTradingSetup } = await import('../services/tradingSetup.service')
    vi.mocked(getTradingSetup).mockResolvedValue(
      makeMockSetup('welcome', [
        { role: 'assistant', content: 'Welcome to Share Trader!', masked: false },
        { role: 'user', content: 'Hello', masked: false },
      ])
    )

    renderComponent()

    await waitFor(() => {
      expect(screen.getByText('Welcome to Share Trader!')).toBeInTheDocument()
    })
    expect(screen.getByText('Hello')).toBeInTheDocument()
  })

  it('T2: api_key step shows password input and secure badge', async () => {
    const { getTradingSetup } = await import('../services/tradingSetup.service')
    vi.mocked(getTradingSetup).mockResolvedValue(makeMockSetup('api_key'))

    renderComponent()

    await waitFor(() => {
      const input = screen.getByTestId('trading-chat-input')
      expect(input).toHaveAttribute('type', 'password')
    })
    expect(screen.getByText('🔒 Secure Input')).toBeInTheDocument()
  })

  it('T3: Send button calls sendTradingSetupMessage with input text', async () => {
    const { getTradingSetup, sendTradingSetupMessage } = await import('../services/tradingSetup.service')
    vi.mocked(getTradingSetup).mockResolvedValue(makeMockSetup('welcome'))
    vi.mocked(sendTradingSetupMessage).mockResolvedValue(
      makeMockSetup('api_key', [
        { role: 'assistant', content: 'Welcome!', masked: false },
        { role: 'user', content: 'start', masked: false },
      ])
    )

    renderComponent()

    await waitFor(() => {
      expect(screen.getByTestId('trading-chat-input')).toBeInTheDocument()
    })

    const input = screen.getByTestId('trading-chat-input')
    fireEvent.change(input, { target: { value: 'start' } })
    fireEvent.click(screen.getByTestId('trading-chat-send'))

    await waitFor(() => {
      expect(sendTradingSetupMessage).toHaveBeenCalledWith('HIRED-1', 'start')
    })
  })

  it('T4: Done step hides input bar and shows emergency stop button', async () => {
    const { getTradingSetup } = await import('../services/tradingSetup.service')
    vi.mocked(getTradingSetup).mockResolvedValue(makeMockSetup('done'))

    renderComponent()

    await waitFor(() => {
      expect(screen.getByTestId('emergency-stop-btn')).toBeInTheDocument()
    })
    expect(screen.queryByTestId('trading-chat-input')).not.toBeInTheDocument()
  })

  it('T5: Emergency stop confirm button calls emergencyStop()', async () => {
    const { getTradingSetup, emergencyStop } = await import('../services/tradingSetup.service')
    vi.mocked(getTradingSetup).mockResolvedValue(makeMockSetup('done'))
    vi.mocked(emergencyStop).mockResolvedValue({ status: 'stopped', stopped_at: '2026-01-01T00:00:00Z' })

    renderComponent()

    await waitFor(() => {
      expect(screen.getByTestId('emergency-stop-btn')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByTestId('emergency-stop-btn'))

    await waitFor(() => {
      expect(screen.getByTestId('emergency-stop-confirm')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByTestId('emergency-stop-confirm'))

    await waitFor(() => {
      expect(emergencyStop).toHaveBeenCalledWith('HIRED-1')
    })
  })

  it('T6: BDD — normal step shows text input, done step shows emergency stop', async () => {
    const { getTradingSetup, sendTradingSetupMessage } = await import('../services/tradingSetup.service')
    vi.mocked(getTradingSetup).mockResolvedValue(makeMockSetup('welcome'))
    vi.mocked(sendTradingSetupMessage).mockResolvedValue(makeMockSetup('done'))

    renderComponent()

    await waitFor(() => {
      expect(screen.getByTestId('trading-chat-input')).toBeInTheDocument()
    })

    const input = screen.getByTestId('trading-chat-input')
    fireEvent.change(input, { target: { value: 'start' } })
    fireEvent.click(screen.getByTestId('trading-chat-send'))

    await waitFor(() => {
      expect(screen.getByTestId('emergency-stop-btn')).toBeInTheDocument()
    })
    expect(screen.queryByTestId('trading-chat-input')).not.toBeInTheDocument()
  })

  it('shows error when API call fails', async () => {
    const { getTradingSetup } = await import('../services/tradingSetup.service')
    vi.mocked(getTradingSetup).mockRejectedValue(new Error('Network error'))

    renderComponent()

    await waitFor(() => {
      expect(screen.getByText('Failed to load trading setup.')).toBeInTheDocument()
    })
  })
})
