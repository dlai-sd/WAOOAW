import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { FluentProvider } from '@fluentui/react-components'
import { waooawLightTheme } from '../theme'
import { TradingReadinessCard } from '../components/TradingReadinessCard'
import type { TradingSetupReadiness } from '../services/tradingSetup.service'

const makeReadiness = (overrides: Partial<TradingSetupReadiness> = {}): TradingSetupReadiness => ({
  configured: false,
  step: 'welcome',
  has_credentials: false,
  credentials_valid: false,
  has_instrument: false,
  has_rsi_period: false,
  has_risk_limits: false,
  ...overrides,
})

const renderCard = (readiness: TradingSetupReadiness, onConfigureCta?: () => void) =>
  render(
    <FluentProvider theme={waooawLightTheme}>
      <TradingReadinessCard readiness={readiness} onConfigureCta={onConfigureCta} />
    </FluentProvider>
  )

describe('TradingReadinessCard', () => {
  it('T3: all 5 readiness badges render with correct ✓/✗ state', () => {
    const readiness = makeReadiness({
      has_credentials: true,
      credentials_valid: false,
      has_instrument: true,
      has_rsi_period: false,
      has_risk_limits: true,
    })
    renderCard(readiness)

    const credsEntered = screen.getByTestId('readiness-has_credentials')
    expect(credsEntered).toBeInTheDocument()
    expect(credsEntered.textContent).toContain('✓')

    const credsValid = screen.getByTestId('readiness-credentials_valid')
    expect(credsValid.textContent).toContain('✗')

    const instrument = screen.getByTestId('readiness-has_instrument')
    expect(instrument.textContent).toContain('✓')

    const rsi = screen.getByTestId('readiness-has_rsi_period')
    expect(rsi.textContent).toContain('✗')

    const risk = screen.getByTestId('readiness-has_risk_limits')
    expect(risk.textContent).toContain('✓')
  })

  it('T4: "Complete setup →" CTA hidden when configured === true', () => {
    const readiness = makeReadiness({ configured: true })
    renderCard(readiness)

    expect(screen.queryByText('Complete setup →')).not.toBeInTheDocument()
    expect(screen.getByText(/Ready to trade/)).toBeInTheDocument()
  })

  it('shows "Complete setup →" CTA when configured === false', () => {
    const ctaFn = vi.fn()
    renderCard(makeReadiness(), ctaFn)

    const cta = screen.getByText('Complete setup →')
    expect(cta).toBeInTheDocument()
    fireEvent.click(cta)
    expect(ctaFn).toHaveBeenCalledTimes(1)
  })

  it('shows green banner text when all readiness checks pass', () => {
    const readiness = makeReadiness({ configured: true })
    renderCard(readiness)

    expect(screen.getByText(/Ready to trade/)).toBeInTheDocument()
  })
})
