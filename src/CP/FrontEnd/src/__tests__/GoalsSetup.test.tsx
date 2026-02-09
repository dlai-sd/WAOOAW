import { describe, it, expect, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import GoalsSetup from '../pages/authenticated/GoalsSetup'

vi.mock('../../services/platformCredentials.service', () => ({
  listPlatformCredentials: vi.fn(async () => []),
  upsertPlatformCredential: vi.fn(async () => ({ credential_ref: 'CRED-1' })),
}))

vi.mock('../../services/exchangeSetup.service', () => ({
  listExchangeSetups: vi.fn(async () => []),
  upsertExchangeSetup: vi.fn(async () => ({ exchange_setup_ref: 'EX-1' })),
}))

vi.mock('../../services/tradingStrategy.service', () => ({
  listTradingStrategyConfigs: vi.fn(async () => []),
  upsertTradingStrategyConfig: vi.fn(async () => ({ strategy_config_ref: 'TS-1' })),
}))

describe('GoalsSetup', () => {
  it('renders without crashing', async () => {
    const { container } = render(<GoalsSetup />)
    expect(container).toBeTruthy()

    // Let initial async effects settle so we don't get post-teardown updates.
    await waitFor(() => {
      expect(screen.getByText(/Connect Exchange \(Trading Setup\)/i)).toBeInTheDocument()
    })
  })

  it('renders component content', async () => {
    const { container } = render(<GoalsSetup />)
    expect(container.firstChild).toBeTruthy()

    await waitFor(() => {
      expect(screen.getByText(/Connect Platforms \(Customer Setup\)/i)).toBeInTheDocument()
    })
  })

  it('renders exchange setup section', async () => {
    render(<GoalsSetup />)

    await waitFor(() => {
      expect(screen.getByText('Connect Exchange (Trading Setup)')).toBeInTheDocument()
    })
  })
})
